"""Scan a fixed Git fixture without granting access to repository contents or credentials."""
import os
import re
import shutil
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

from security_engine.executor import DependencyUnavailable, ExecutionError, controlled_environment, execute
from security_engine.normalization.semgrep import normalize_semgrep, safe_path
from security_engine.scanners.semgrep import SemgrepScanner
from security_engine.workspace import RunWorkspace


SOURCE_REPO = Path(__file__).resolve().parents[2]
FIXTURE_DIR = 'backend/tests/fixtures/vulnerable-repository'
FIXTURE_FILES = ('app.py', 'clean.py')
RULE_PATH = 'backend/security_engine/rules/semgrep-v1.yml'
SCANNER_VERSION = '1.176.0'
SCANNER_IMAGE = f'semgrep/semgrep:{SCANNER_VERSION}'


async def git_blob(commit, relative_path, workspace):
    git = shutil.which('git')
    if not git:
        raise DependencyUnavailable('Git is required to read the fixture commit')
    prefix = str(workspace.artifacts / 'git')
    options = {'cwd': SOURCE_REPO, 'timeout': 4, 'max_output_bytes': 64 * 1024,
               'environment': controlled_environment(), 'artifact_prefix': prefix}
    listing = await execute([git, 'ls-tree', commit, '--', relative_path], **options)
    entries = listing.stdout.splitlines()
    if listing.exit_code or len(entries) != 1 or not entries[0].startswith(b'100644 blob '):
        raise ExecutionError('Fixture commit does not contain the expected regular file')
    result = await execute([git, 'cat-file', 'blob', f'{commit}:{relative_path}'], **options)
    if result.exit_code:
        raise ExecutionError('Fixture blob is unavailable')
    return result.stdout


class IsolatedFixtureScanner(SemgrepScanner):
    async def _run(self, workspace):
        docker = shutil.which('docker')
        if not docker or os.name != 'posix':
            raise DependencyUnavailable('The fixture scanner requires a local Linux Docker engine')
        name = f'havosec-fixture-{uuid4().hex}'
        host = [docker, '--host', 'unix:///var/run/docker.sock']
        options = {'cwd': workspace.repository, 'environment': controlled_environment()}
        try:
            return await execute([
                *host, 'run', '--name', name, '--rm', '--pull', 'never',
                '--network', 'none', '--read-only', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
                '--user', '65534:65534', '--pids-limit', '64', '--memory', '768m', '--cpus', '1',
                '--tmpfs', '/tmp:rw,nosuid,nodev,size=64m,mode=1777', '--env', 'HOME=/tmp',
                '--env', 'SEMGREP_SEND_METRICS=off', '--entrypoint', 'semgrep',
                '--volume', f'{workspace.repository}:/src:ro',
                '--volume', f'{workspace.artifacts / "rules.yml"}:/rules.yml:ro',
                '--workdir', '/src', SCANNER_IMAGE, *self.arguments('/rules.yml', *FIXTURE_FILES),
            ], **options, timeout=self.timeout, max_output_bytes=self.max_output_bytes,
                artifact_prefix=str(workspace.artifacts / 'semgrep'))
        finally:
            try:
                await execute([*host, 'rm', '-f', name], **options, timeout=5, max_output_bytes=8192,
                              artifact_prefix=str(workspace.artifacts / 'cleanup'))
            except (OSError, ExecutionError):
                # The container uses --rm. Preserve the original scan error or cancellation.
                pass


async def assess_fixture(mission, scanner=None):
    commit = mission.get('fixture_commit')
    report = {
        'status': 'incomplete', 'commit_sha': commit, 'scanner': 'semgrep', 'scanner_version': SCANNER_VERSION,
        'rules_sha256': None, 'coverage': {'expected': list(FIXTURE_FILES), 'scanned': [], 'missing': list(FIXTURE_FILES)},
        'observations': [], 'gaps': [], 'captured_at': datetime.now(timezone.utc),
    }
    if not isinstance(commit, str) or not re.fullmatch('[0-9a-f]{40}', commit):
        report['gaps'].append('invalid_fixture_commit')
        return report
    if scanner is None:
        scanner = IsolatedFixtureScanner(timeout=40, max_output_bytes=512_000, max_findings=50)
    try:
        files = {}
        with RunWorkspace(mission['_id']) as workspace:
            workspace.repository.mkdir()
            for name in FIXTURE_FILES:
                data = await git_blob(commit, f'{FIXTURE_DIR}/{name}', workspace)
                files[name] = data.splitlines(keepends=True)
                (workspace.repository / name).write_bytes(data)
            rules = await git_blob(commit, RULE_PATH, workspace)
            (workspace.artifacts / 'rules.yml').write_bytes(rules)
            report['rules_sha256'] = sha256(rules).hexdigest()
            result = await scanner.scan(workspace)
        if result.scanner_version != SCANNER_VERSION:
            raise ExecutionError('Unexpected Semgrep version')
        scanned = {safe_path(path) for path in result.metadata['scanned_paths']}
        if not scanned <= set(FIXTURE_FILES):
            raise ValueError('Unexpected coverage path')
        missing = sorted(set(FIXTURE_FILES) - scanned)
        report['coverage'].update(scanned=sorted(scanned), missing=missing)
        if missing:
            report['gaps'].append('fixture_files_missing_from_scan')
        if result.errors:
            report['gaps'].append('scanner_reported_errors')
        context = SimpleNamespace(repository='HavoSec fixture', branch=None, commit_sha=commit,
                                  organization_id=mission['organization_id'], project_id=mission['project_id'],
                                  asset_id=mission['asset_id'], security_run_id=str(mission['_id']))
        candidates = normalize_semgrep(result, context)
        observations = []
        for candidate in candidates:
            path = candidate.file_path
            if path not in scanned or candidate.end_line > len(files[path]):
                raise ValueError('Observation is outside the reported scan coverage')
            evidence = b''.join(files[path][candidate.start_line - 1:candidate.end_line])
            observations.append({
                'rule_id': candidate.rule_id, 'severity': candidate.severity.value, 'path': path,
                'start_line': candidate.start_line, 'end_line': candidate.end_line,
                'evidence_sha256': sha256(evidence).hexdigest(),
            })
        report['observations'] = observations
        report['captured_at'] = result.completed_at
        if not report['gaps']:
            report['status'] = 'complete'
    except (ExecutionError, OSError, ValueError, KeyError):
        report['gaps'].append('fixture_scan_failed')
    return report
