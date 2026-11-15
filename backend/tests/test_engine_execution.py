import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
import pytest

from security_engine.executor import execute, ExecutionError, ExecutionTimeout, OutputLimitExceeded
from security_engine.workspace import RunWorkspace
from security_engine.repository import GitRepository
from security_engine.scanners.base import ScannerResult
from security_engine.scanners.semgrep import SemgrepScanner, RULES
from security_engine.normalization.semgrep import normalize_semgrep, safe_path, SEVERITY
from models.findings import Severity


FIXTURE = Path(__file__).parent / 'fixtures' / 'vulnerable-repository'


def paths(tmp_path):
    root = tmp_path / 'work'; root.mkdir()
    repo, artifacts = root / 'repo', root / 'artifacts'
    repo.mkdir(); artifacts.mkdir()
    return SimpleNamespace(root=root, repository=repo, artifacts=artifacts)


def test_workspace_is_unique_and_cleans_on_success_and_error(tmp_path):
    roots = []
    for error in [False, True]:
        with pytest.raises(RuntimeError) if error else __import__('contextlib').nullcontext():
            with RunWorkspace('not-used-in-path', parent=tmp_path) as workspace:
                roots.append(workspace.root)
                (workspace.repository).mkdir()
                (workspace.repository / 'data').write_text('fixture')
                if error:
                    raise RuntimeError('test')
        assert not roots[-1].exists()
    assert roots[0] != roots[1] and all(root.name.startswith('havosec-run-') for root in roots)


def test_workspace_preserve_is_explicit(tmp_path):
    with RunWorkspace('run', parent=tmp_path, keep=True) as workspace:
        root = workspace.root
    assert root.exists()
    import shutil
    shutil.rmtree(root)


def test_executor_output_and_limits(tmp_path):
    async def exercise():
        env = {'SYSTEMROOT': __import__('os').environ.get('SYSTEMROOT', '')}
        result = await execute([__import__('sys').executable, '-c', 'print("ok")'], cwd=tmp_path,
                               timeout=5, max_output_bytes=100, environment=env,
                               artifact_prefix=str(tmp_path / 'one'))
        assert result.stdout.strip() == b'ok' and result.exit_code == 0
        with pytest.raises(OutputLimitExceeded):
            await execute([__import__('sys').executable, '-c', 'print("x"*200)'], cwd=tmp_path,
                          timeout=5, max_output_bytes=10, environment=env,
                          artifact_prefix=str(tmp_path / 'two'))
        with pytest.raises(ExecutionTimeout):
            await execute([__import__('sys').executable, '-c', 'import time; time.sleep(5)'], cwd=tmp_path,
                          timeout=.05, max_output_bytes=100, environment=env,
                          artifact_prefix=str(tmp_path / 'three'))
    asyncio.run(exercise())


def test_git_adapter_uses_argument_arrays_and_verifies_sha(tmp_path):
    workspace = paths(tmp_path)
    snapshot = SimpleNamespace(repository='https://github.com/a/b', branch='main')
    calls = []
    async def fake(args, **kwargs):
        calls.append((args, kwargs))
        output = b'' if len(calls) == 1 else b'a' * 40 + b'\n'
        return SimpleNamespace(exit_code=0, stdout=output, stderr=b'')
    with patch('security_engine.repository.shutil.which', return_value='C:/git.exe'), patch('security_engine.repository.execute', fake):
        result = asyncio.run(GitRepository(20, 500).checkout(snapshot, workspace))
    assert result.commit_sha == 'a' * 40
    assert calls[0][0][-3:] == ['--', snapshot.repository, str(workspace.repository)]
    assert '--branch' in calls[0][0] and calls[0][1]['environment']['GIT_TERMINAL_PROMPT'] == '0'
    assert all(call[1].get('shell') is None for call in calls)


def test_git_adapter_checks_out_and_verifies_exact_finding_revision(tmp_path):
    destination, artifacts = tmp_path / 'source', tmp_path / 'artifacts'
    artifacts.mkdir()
    commit = 'a' * 40
    snapshot = SimpleNamespace(repository='https://github.com/a/b')
    calls = []

    async def fake(args, **kwargs):
        calls.append((args, kwargs))
        output = (commit + '\n').encode() if args[-3:] == ['rev-parse', '--verify', 'HEAD'] else b''
        return SimpleNamespace(exit_code=0, stdout=output, stderr=b'')

    with patch('security_engine.repository.shutil.which', return_value='C:/git.exe'), \
         patch('security_engine.repository.execute', fake):
        result = asyncio.run(GitRepository(20, 500).checkout_revision(
            snapshot, destination, artifacts, commit,
        ))
    assert result.commit_sha == commit and result.branch is None
    assert calls[2][0][-2:] == ['origin', commit]
    assert calls[3][0][-2:] == ['--detach', 'FETCH_HEAD']
    assert calls[2][1]['environment']['GIT_TERMINAL_PROMPT'] == '0'


def test_exact_revision_rejects_invalid_or_mismatched_commit(tmp_path):
    repository = GitRepository(20, 500)
    snapshot = SimpleNamespace(repository='https://github.com/a/b')
    with patch('security_engine.repository.execute', new=AsyncMock()) as execute:
        with pytest.raises(ExecutionError, match='invalid'):
            asyncio.run(repository.checkout_revision(snapshot, tmp_path / 'one', tmp_path, 'main'))
        execute.assert_not_awaited()

    success = SimpleNamespace(exit_code=0, stdout=b'', stderr=b'')
    mismatch = SimpleNamespace(exit_code=0, stdout=b'b' * 40 + b'\n', stderr=b'')
    with patch('security_engine.repository.shutil.which', return_value='git'), \
         patch('security_engine.repository.execute', new=AsyncMock(side_effect=[success] * 4 + [mismatch])):
        with pytest.raises(ExecutionError, match='does not match'):
            asyncio.run(repository.checkout_revision(snapshot, tmp_path / 'two', tmp_path, 'a' * 40))


def semgrep_payload(path='app.py'):
    return {'version': '1.test', 'errors': [], 'results': [{
        'check_id': 'test.rule', 'path': path, 'start': {'line': 3}, 'end': {'line': 3},
        'extra': {'message': 'Unsafe evaluation', 'severity': 'ERROR', 'lines': 'eval(value)'}}]}


def test_scanner_fixed_command_and_json(tmp_path):
    workspace = paths(tmp_path)
    result = SimpleNamespace(exit_code=0, stdout=json.dumps(semgrep_payload()).encode(), stderr=b'')
    with patch('security_engine.scanners.semgrep.shutil.which', return_value='semgrep'), \
         patch('security_engine.scanners.semgrep.execute', new=AsyncMock(return_value=result)) as process:
        parsed = asyncio.run(SemgrepScanner(30, 10000, 10).scan(workspace))
    args = process.await_args.args[0]
    assert args == ['semgrep', 'scan', '--json', '--metrics=off', '--disable-version-check', '--config', str(RULES), '--', '.']
    assert process.await_args.kwargs['cwd'] == workspace.repository
    assert parsed.scanner_version == '1.test' and len(parsed.results) == 1


@pytest.mark.parametrize('exit_code,payload,error', [(2, semgrep_payload(), 'failed'), (0, b'not json', 'invalid'),
    (0, {'errors': [], 'results': 'bad'}, 'invalid')])
def test_scanner_failures_are_controlled(tmp_path, exit_code, payload, error):
    workspace = paths(tmp_path)
    stdout = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
    result = SimpleNamespace(exit_code=exit_code, stdout=stdout, stderr=b'sensitive path')
    with patch('security_engine.scanners.semgrep.shutil.which', return_value='semgrep'), \
         patch('security_engine.scanners.semgrep.execute', new=AsyncMock(return_value=result)):
        with pytest.raises(Exception, match=error):
            asyncio.run(SemgrepScanner(30, 10000, 10).scan(workspace))


def test_normalization_relative_path_mapping_and_fingerprint():
    now = datetime.now(timezone.utc)
    scanner = ScannerResult(scanner='semgrep', scanner_version='1.2', configuration='test',
                            started_at=now, completed_at=now, exit_code=0,
                            results=semgrep_payload()['results'])
    context = SimpleNamespace(organization_id='o', project_id='p', asset_id='a', security_run_id='r',
                              repository='https://github.com/a/b', branch='main', commit_sha='f' * 40)
    first = normalize_semgrep(scanner, context)[0]
    second = normalize_semgrep(scanner, context)[0]
    assert first.fingerprint == second.fingerprint and len(first.fingerprint) == 64
    assert first.file_path == 'app.py' and first.severity == Severity.HIGH
    assert first.evidence['snippet_sha256'] and 'eval(value)' not in first.evidence.values()
    changed = scanner.model_copy(update={'results': semgrep_payload('src/other.py')['results']})
    assert normalize_semgrep(changed, context)[0].fingerprint != first.fingerprint


def test_severity_mapping_is_central_and_complete():
    assert SEVERITY == {'ERROR': Severity.HIGH, 'WARNING': Severity.MEDIUM, 'INFO': Severity.LOW,
                        'INVENTORY': Severity.INFO, 'EXPERIMENT': Severity.INFO}


@pytest.mark.parametrize('value', ['/tmp/run/repo/app.py', 'C:\\tmp\\repo\\app.py', '../app.py',
                                   'src/../app.py', '', None])
def test_absolute_and_escaping_paths_rejected(value):
    with pytest.raises(ValueError):
        safe_path(value)


def test_fixture_is_small_and_never_imported():
    files = [path for path in FIXTURE.rglob('*') if path.is_file()]
    assert set(files) == {FIXTURE / 'app.py', FIXTURE / 'known-good-eval-fix.diff'}
    assert all(path.stat().st_size < 1000 for path in files)
    assert 'subprocess.run' in (FIXTURE / 'app.py').read_text()
