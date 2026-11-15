import asyncio
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

from bson import ObjectId

from models.remediations import RemediationProposal
from security_engine.executor import ExecutionError
from security_engine.remediation_pipeline import RemediationPipeline
from security_engine.scanners.base import ScannerResult
from security_engine.verification import compare_semgrep


def scan(*items):
    now = datetime.now(timezone.utc)
    return ScannerResult(scanner='semgrep', scanner_version='1.test', configuration='test',
                         started_at=now, completed_at=now, exit_code=0,
                         results=list(items), errors=[], metadata={})


def finding_item(rule='rule.eval', path='app.py', line=3, severity='ERROR'):
    return {'check_id': rule, 'path': path, 'start': {'line': line}, 'end': {'line': line},
            'extra': {'severity': severity, 'message': 'Finding'}}


def finding():
    return {'severity': 'high', 'location': 'app.py:3-3',
            'evidence': {'rule_id': 'rule.eval', 'path': 'app.py', 'start_line': 3}}


def test_comparison_verifies_removed_finding_without_equal_or_higher_regression():
    remediation_id = str(ObjectId())
    result = compare_semgrep(remediation_id, finding(), scan(finding_item()),
                             scan(finding_item('rule.low', 'other.py', 1, 'WARNING')))
    assert result.status == 'verified' and result.original_finding_present is False
    assert result.new_findings_count == 1 and result.new_equal_or_higher_findings_count == 0
    assert result.before_severity_counts['high'] == 1
    assert result.after_severity_counts['medium'] == 1


def test_comparison_fails_when_original_remains():
    result = compare_semgrep(str(ObjectId()), finding(), scan(finding_item()), scan(finding_item()))
    assert result.status == 'failed' and result.original_finding_present is True


def test_comparison_fails_on_new_equal_severity_finding():
    after = scan(finding_item('new.rule', 'other.py', 8, 'ERROR'))
    result = compare_semgrep(str(ObjectId()), finding(), scan(finding_item()), after)
    assert result.status == 'failed' and result.original_finding_present is False
    assert result.new_equal_or_higher_findings_count == 1


def test_line_shift_does_not_turn_existing_finding_into_regression():
    existing = finding_item('existing.rule', 'other.py', 10, 'ERROR')
    shifted = finding_item('existing.rule', 'other.py', 12, 'ERROR')
    result = compare_semgrep(str(ObjectId()), finding(),
                             scan(finding_item(), existing), scan(shifted))
    assert result.status == 'verified'
    assert result.new_findings_count == result.new_equal_or_higher_findings_count == 0


class Workspace:
    def __init__(self, root):
        self.paths = SimpleNamespace(root=root, original=root / 'original', patched=root / 'patched',
                                     artifacts=root / 'artifacts')
        self.exited = False

    def __enter__(self):
        self.paths.root.mkdir(); self.paths.artifacts.mkdir()
        return self

    def create_patched_copy(self):
        self.paths.patched.mkdir()
        return self.paths.patched

    def __exit__(self, *_):
        self.exited = True


def proposal():
    return RemediationProposal(summary='Fix', explanation='Fix', affected_files=['app.py'],
        patch='--- a/app.py\n+++ b/app.py\n@@ -1 +1 @@\n-a\n+b\n',
        expected_security_effect='Fix', confidence=.9)


def pipeline(tmp_path, *, scanner_error=None):
    remediation = {'_id': ObjectId(), 'organization_id': 'a' * 24, 'project_id': 'b' * 24,
                   'asset_id': 'c' * 24, 'finding_id': 'd' * 24,
                   'source_commit': 'e' * 40, 'verification_status': 'testing'}
    repository = AsyncMock()
    repository.load_remediation_context.return_value = (
        SimpleNamespace(), finding(), proposal(), scan(finding_item()))
    checkout = AsyncMock()
    checkout.checkout_revision.return_value = SimpleNamespace(commit_sha='e' * 40)
    scanner = AsyncMock()
    scanner.scan.side_effect = scanner_error
    if scanner_error is None:
        scanner.scan.return_value = scan()
    patcher = AsyncMock()
    holder = {}
    def factory(_):
        holder['workspace'] = Workspace(tmp_path / 'workspace')
        return holder['workspace']
    engine = RemediationPipeline(repository, checkout, scanner, patcher, factory, {},
                                 timeout=30, patch_max_bytes=1000, patch_max_files=1)
    return engine, remediation, repository, holder


def test_pipeline_scans_only_patched_tree_and_persists_verified_result(tmp_path):
    engine, remediation, repository, holder = pipeline(tmp_path)
    assert asyncio.run(engine.process(remediation)) == 'verified'
    assert holder['workspace'].exited
    assert engine.scanner.scan.await_args.args[0].repository == holder['workspace'].paths.patched
    saved = repository.complete_remediation.await_args.args[1]
    assert saved.status == 'verified' and saved.original_finding_present is False
    repository.fail_remediation.assert_not_awaited()


def test_pipeline_scanner_failure_is_inconclusive_and_cleans_workspace(tmp_path):
    engine, remediation, repository, holder = pipeline(tmp_path, scanner_error=ExecutionError('private'))
    assert asyncio.run(engine.process(remediation)) == 'inconclusive'
    assert holder['workspace'].exited
    repository.complete_remediation.assert_not_awaited()
    assert repository.fail_remediation.await_args.args[1:] == (
        'inconclusive', 'Static remediation verification could not be completed')


def test_pipeline_generates_and_freezes_missing_proposal_with_same_agent(tmp_path):
    engine, remediation, repository, holder = pipeline(tmp_path)
    context = list(repository.load_remediation_context.return_value)
    context[2] = None
    repository.load_remediation_context.return_value = tuple(context)
    agent = AsyncMock()
    agent.max_context_chars = 1000
    agent.propose_remediation.return_value = (proposal(), {'total_tokens': 12})
    engine.agent = agent
    repository.save_remediation_proposal.return_value = proposal()

    async def checkout(snapshot, destination, artifacts, commit):
        destination.mkdir()
        (destination / 'app.py').write_text('\n\nresult = eval(value)\n', encoding='utf-8')
        return SimpleNamespace(commit_sha=commit)

    engine.checkout.checkout_revision.side_effect = checkout
    assert asyncio.run(engine.process(remediation)) == 'verified'
    assert holder['workspace'].exited
    assert 'eval(value)' in agent.propose_remediation.await_args.args[1]
    metadata = repository.save_remediation_proposal.await_args.args[2]
    assert metadata == {'analysis_mode': 'agent_generated', 'usage': {'total_tokens': 12}}


def test_pipeline_reports_agent_unavailable_without_fabricating_patch(tmp_path):
    engine, remediation, repository, holder = pipeline(tmp_path)
    context = list(repository.load_remediation_context.return_value)
    context[2] = None
    repository.load_remediation_context.return_value = tuple(context)

    async def checkout(snapshot, destination, artifacts, commit):
        destination.mkdir()
        return SimpleNamespace(commit_sha=commit)

    engine.checkout.checkout_revision.side_effect = checkout
    assert asyncio.run(engine.process(remediation)) == 'failed'
    assert holder['workspace'].exited
    repository.save_remediation_proposal.assert_not_awaited()
    assert repository.fail_remediation.await_args.args[1:] == (
        'failed', 'Automated remediation proposal generation is unavailable')
