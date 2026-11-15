import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

from bson import ObjectId

from security_engine.pr_reverification_pipeline import PullRequestReverificationPipeline
from security_engine.scanners.base import ScannerResult
from security_engine.workspace import RunWorkspace


def scan(results):
    now = datetime.now(timezone.utc)
    return ScannerResult(scanner='semgrep', scanner_version='1', configuration='test',
                         started_at=now, completed_at=now, exit_code=0,
                         results=results, errors=[], metadata={})


def test_exact_remote_commit_is_materialized_scanned_and_persisted(tmp_path):
    record = {'_id': ObjectId(), 'repository_full_name': 'owner/repo',
              'branch': 'havosec/remediation-test', 'commit_sha': '1' * 40,
              'remediation_id': 'e' * 24}
    finding = {'severity': 'medium', 'location': 'app.py:1-1',
               'evidence': {'rule_id': 'unsafe-eval', 'path': 'app.py', 'start_line': 1}}
    before = scan([{'check_id': 'unsafe-eval', 'path': 'app.py', 'start': {'line': 1},
                    'extra': {'severity': 'WARNING'}}])
    storage = AsyncMock()
    storage.load_pull_request_reverification_context.return_value = (
        {}, finding, {'installation_id': 1}, {}, before)
    client = AsyncMock()
    client.get_branch_head.return_value = '1' * 40
    client.get_commit.return_value = {'tree': {'sha': '2' * 40}}
    client.get_tree.return_value = {'app.py': {'type': 'blob', 'mode': '100644', 'sha': '3' * 40}}
    client.get_blob.return_value = b"print('safe')\n"
    scanner = AsyncMock()
    scanner.scan.return_value = scan([])
    pipeline = PullRequestReverificationPipeline(
        storage, lambda _: client, scanner,
        lambda identity: RunWorkspace(identity, parent=tmp_path))

    assert asyncio.run(pipeline.process(record)) == 'verified'
    persisted = storage.complete_pull_request_reverification.await_args.args[1]
    assert persisted.status == 'verified'
    assert persisted.original_finding_present is False
    assert persisted.new_equal_or_higher_findings_count == 0


def test_remote_branch_change_fails_before_scan(tmp_path):
    record = {'_id': ObjectId(), 'repository_full_name': 'owner/repo',
              'branch': 'havosec/remediation-test', 'commit_sha': '1' * 40,
              'remediation_id': 'e' * 24}
    storage, client, scanner = AsyncMock(), AsyncMock(), AsyncMock()
    storage.load_pull_request_reverification_context.return_value = (
        {}, {}, {'installation_id': 1}, {}, scan([]))
    client.get_branch_head.return_value = '9' * 40
    pipeline = PullRequestReverificationPipeline(
        storage, lambda _: client, scanner,
        lambda identity: RunWorkspace(identity, parent=tmp_path))
    assert asyncio.run(pipeline.process(record)) == 'inconclusive'
    scanner.scan.assert_not_awaited()
    storage.fail_pull_request_reverification.assert_awaited_once()
