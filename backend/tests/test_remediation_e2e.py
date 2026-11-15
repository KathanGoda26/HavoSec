"""Real Semgrep proof over a tiny HavoSec-owned fixture; fixture code is never run."""
import asyncio
import os
import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest
from bson import ObjectId

from models.remediations import RemediationProposal
from security_engine.executor import controlled_environment, execute
from security_engine.remediation_workspace import PatchApplicator, RemediationWorkspace
from security_engine.repository import GitRepository
from security_engine.scanners.semgrep import SemgrepScanner
from security_engine.verification import compare_semgrep


FIXTURE = Path(__file__).parent / 'fixtures' / 'vulnerable-repository'
SEMGREP_BIN = Path(__file__).resolve().parents[1] / '.tools' / 'semgrep-venv' / 'Scripts'
TARGET_RULE_SUFFIX = 'havosec.python.eval'


async def git(args, cwd, artifacts, index):
    binary = shutil.which('git')
    assert binary
    result = await execute([binary, *args], cwd=cwd, timeout=20, max_output_bytes=100_000,
                           environment=controlled_environment(),
                           artifact_prefix=str(artifacts / f'fixture-git-{index}'))
    assert result.exit_code == 0
    return result


def target(scan):
    return next(item for item in scan.results if item['check_id'].endswith(TARGET_RULE_SUFFIX))


def test_known_good_patch_completes_real_isolated_semgrep_loop(tmp_path, monkeypatch):
    scanner_binary = SEMGREP_BIN / ('semgrep.exe' if os.name == 'nt' else 'semgrep')
    if not scanner_binary.is_file():
        pytest.skip('Install requirements-worker.txt to run the real Semgrep proof')
    monkeypatch.setenv('PATH', str(SEMGREP_BIN) + os.pathsep + os.environ.get('PATH', ''))
    source, setup_artifacts = tmp_path / 'source', tmp_path / 'setup-artifacts'
    source.mkdir(); setup_artifacts.mkdir()
    shutil.copy2(FIXTURE / 'app.py', source / 'app.py')

    async def exercise():
        await git(['init', '--quiet', '--', str(source)], tmp_path, setup_artifacts, 0)
        await git(['-C', str(source), 'config', 'user.name', 'HavoSec Test'], tmp_path, setup_artifacts, 1)
        await git(['-C', str(source), 'config', 'user.email', 'fixture@invalid.local'], tmp_path, setup_artifacts, 2)
        await git(['-C', str(source), 'add', '--', 'app.py'], tmp_path, setup_artifacts, 3)
        await git(['-C', str(source), 'commit', '--quiet', '-m', 'fixture'], tmp_path, setup_artifacts, 4)
        revision = await git(['-C', str(source), 'rev-parse', '--verify', 'HEAD'], tmp_path, setup_artifacts, 5)
        commit = revision.stdout.decode('ascii').strip().lower()
        scanner = SemgrepScanner(120, 4_000_000, 20)
        before_artifacts = tmp_path / 'before-artifacts'; before_artifacts.mkdir()
        before = await scanner.scan(SimpleNamespace(repository=source, artifacts=before_artifacts))
        original = (source / 'app.py').read_text(encoding='utf-8')
        remediation_id = str(ObjectId())
        workspace_root = None
        with RemediationWorkspace(remediation_id, parent=tmp_path, max_bytes=10_000_000) as workspace:
            workspace_root = workspace.paths.root
            snapshot = SimpleNamespace(repository=str(source))
            checked_out = await GitRepository(30, 500_000).checkout_revision(
                snapshot, workspace.paths.original, workspace.paths.artifacts, commit)
            assert checked_out.commit_sha == commit
            workspace.create_patched_copy()
            patch_text = (FIXTURE / 'known-good-eval-fix.diff').read_text(encoding='utf-8')
            proposal = RemediationProposal(
                summary='Replace eval with safe literal parsing',
                explanation='Parse supported Python literals without executing input.',
                affected_files=['app.py'], patch=patch_text,
                expected_security_effect='Removes arbitrary Python evaluation.',
                potential_side_effects=['Only Python literal syntax remains accepted.'],
                recommended_tests=['Review accepted input formats.'], confidence=1.0)
            safe = await PatchApplicator().apply(
                proposal, workspace, max_bytes=65_536, max_files=1, timeout=30)
            after_artifacts = workspace.paths.artifacts / 'after'; after_artifacts.mkdir()
            after = await scanner.scan(SimpleNamespace(
                repository=workspace.paths.patched, artifacts=after_artifacts))
            item = target(before)
            canonical_rule = item['check_id']
            finding = {'severity': 'medium', 'location': f"app.py:{item['start']['line']}-{item['end']['line']}",
                       'evidence': {'rule_id': canonical_rule, 'path': 'app.py',
                                    'start_line': item['start']['line']}}
            result = compare_semgrep(remediation_id, finding, before, after)
            assert len(before.results) == 2 and len(after.results) == 1
            assert target(before) and all(item['check_id'] != canonical_rule for item in after.results)
            assert result.status == 'verified' and result.original_finding_present is False
            assert result.new_findings_count == result.new_equal_or_higher_findings_count == 0
            assert safe.files == ('app.py',) and safe.size_bytes == len(patch_text.encode('utf-8'))
            assert (source / 'app.py').read_text(encoding='utf-8') == original
            assert (workspace.paths.original / 'app.py').read_text(encoding='utf-8') == original
            assert 'ast.literal_eval' in (workspace.paths.patched / 'app.py').read_text(encoding='utf-8')
        assert workspace_root is not None and not workspace_root.exists()

    asyncio.run(exercise())
