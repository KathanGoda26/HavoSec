"""Independently verify the bundled proposal against the pinned fixture."""
import logging
from datetime import datetime, timezone
from hashlib import sha256
from types import SimpleNamespace

from mission_orchestration.fixture_assessment import (
    FIXTURE_DIR, FIXTURE_FILES, RULE_PATH, SCANNER_VERSION, IsolatedSemgrepScanner, git_blob,
)
from models.remediations import RemediationProposal
from security_engine.executor import ExecutionError
from security_engine.normalization.semgrep import safe_path
from security_engine.patch_integrity import patch_sha256
from security_engine.remediation_workspace import PatchApplicator, RemediationWorkspace
from security_engine.verification import compare_semgrep


log = logging.getLogger(__name__)
PATCH_PATH = f'{FIXTURE_DIR}/known-good-eval-fix.diff'
TARGET_PATH = 'app.py'
TARGET_RULE = 'havosec.python.eval'


async def covered_scan(scanner, workspace, repository):
    scan = await scanner.scan(SimpleNamespace(repository=repository, artifacts=workspace.paths.artifacts))
    scanned = {safe_path(path) for path in scan.metadata['scanned_paths']}
    if scan.errors or scanned != set(FIXTURE_FILES) or scan.scanner_version != SCANNER_VERSION:
        raise ExecutionError('The verification scan did not cover the pinned fixture')
    return scan


async def verify_fixture_remediation(mission):
    commit = mission.get('fixture_commit')
    baseline = mission.get('assessment_report') or {}
    record = {
        'status': 'inconclusive', 'source_commit': commit, 'rules_sha256': baseline.get('rules_sha256'),
        'scanner_version': SCANNER_VERSION, 'proposal': None, 'patch_sha256': None,
        'finding': None, 'comparison': None, 'skipped_checks': ['Repository code and tests were not executed.'],
        'publication_status': 'fixture_only', 'summary': 'A completed assessment of the pinned fixture is required.',
    }
    if baseline.get('status') != 'complete' or baseline.get('commit_sha') != commit:
        return record
    finding = next((item for item in baseline['observations'] if item['path'] == TARGET_PATH
                    and item['rule_id'].endswith(TARGET_RULE)), None)
    if finding is None:
        record['summary'] = 'The known eval finding was absent from the assessment.'
        return record
    record['finding'] = finding
    try:
        with RemediationWorkspace(mission['_id'], max_bytes=1_000_000) as workspace:
            paths = workspace.paths
            paths.original.mkdir()
            for name in FIXTURE_FILES:
                source = await git_blob(commit, f'{FIXTURE_DIR}/{name}', paths)
                (paths.original / name).write_bytes(source)
            rules = await git_blob(commit, RULE_PATH, paths)
            if sha256(rules).hexdigest() != baseline['rules_sha256']:
                raise ExecutionError('The verification rules do not match the assessment')
            (paths.artifacts / 'rules.yml').write_bytes(rules)
            patch = (await git_blob(commit, PATCH_PATH, paths)).decode('utf-8')
            proposal = RemediationProposal(
                summary='Replace eval with Python literal parsing',
                explanation='Interpret supported literal values without executing the input as Python code.',
                affected_files=[TARGET_PATH], patch=patch,
                expected_security_effect='Removes arbitrary Python evaluation at the target location.',
                potential_side_effects=['Inputs must use Python literal syntax.'],
                recommended_tests=['Review the accepted input formats.'], confidence=1,
            )
            record.update(proposal=proposal.model_dump(), patch_sha256=patch_sha256(patch))
            scanner = IsolatedSemgrepScanner(timeout=40, max_output_bytes=512_000, max_findings=50)
            before = await covered_scan(scanner, workspace, paths.original)
            exact_match = any(item['check_id'] == finding['rule_id'] and item['path'] == TARGET_PATH
                              and item['start']['line'] == finding['start_line'] for item in before.results)
            if not exact_match:
                raise ExecutionError('The target finding could not be reproduced')
            workspace.create_patched_copy()
            await PatchApplicator().apply(proposal, workspace, max_bytes=65_536, max_files=1, timeout=8)
            after = await covered_scan(scanner, workspace, paths.patched)
            result = compare_semgrep(str(mission['_id']), {'severity': finding['severity'], 'evidence': finding},
                                     before, after)
            target_still_matches = any(item['check_id'] == finding['rule_id'] and item['path'] == TARGET_PATH
                                       for item in after.results)
            if target_still_matches:
                record.update(status='failed', summary='The target rule still matches in the patched file.')
            else:
                record.update(status=result.status, summary=result.summary)
            comparison = result.model_dump()
            comparison.update(status=record['status'], summary=record['summary'],
                              original_finding_present=target_still_matches)
            record['comparison'] = comparison
    except (ExecutionError, OSError, ValueError, KeyError) as error:
        log.warning('Fixture remediation verification could not complete (%s)', type(error).__name__)
        record['status'] = 'inconclusive'
        record['summary'] = 'The pinned patch or one of its verification scans could not be completed.'
    record['checked_at'] = datetime.now(timezone.utc)
    return record
