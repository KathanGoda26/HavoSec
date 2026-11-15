import asyncio
from copy import deepcopy
from datetime import datetime, timezone, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock
from bson import ObjectId
import pytest

from security_engine.pipeline import SecurityPipeline, safe_reason
from security_engine.executor import DependencyUnavailable, ExecutionTimeout, OutputLimitExceeded
from security_engine.storage import WorkerRepository, RunChanged, candidate_to_document
from security_engine.policy import RepositorySnapshot, RepositoryPolicyError
from security_engine.scanners.base import ScannerResult
from security_engine.normalization.semgrep import normalize_semgrep
from models.remediations import VerificationResult


def run_record():
    return {'_id': ObjectId(), 'organization_id': 'a' * 24, 'project_id': 'b' * 24,
            'asset_ids': ['c' * 24], 'requested_by': 'd' * 24, 'status': 'running', 'progress': 5}


def scanner_result():
    now = datetime.now(timezone.utc)
    return ScannerResult(scanner='semgrep', scanner_version='1.test', configuration='test',
        started_at=now, completed_at=now, exit_code=0, errors=[], results=[{
            'check_id': 'test.eval', 'path': 'src/app.py', 'start': {'line': 4}, 'end': {'line': 4},
            'extra': {'message': 'Unsafe eval', 'severity': 'WARNING', 'lines': 'eval(value)'}}])


class Workspace:
    def __init__(self, root):
        root.mkdir(parents=True)
        self.value = SimpleNamespace(root=root, repository=root / 'repo', artifacts=root / 'artifacts')
        self.value.repository.mkdir(); self.value.artifacts.mkdir()
        self.exited = False
    def __enter__(self): return self.value
    def __exit__(self, *_): self.exited = True


def pipeline(tmp_path, *, cancelled=None, scan_error=None, agent=None):
    storage = AsyncMock()
    snapshot = RepositorySnapshot(organization_id='a' * 24, project_id='b' * 24,
        asset_id='c' * 24, repository='https://github.com/a/b', branch='main')
    storage.load_authorized_context.return_value = (None, None, None, snapshot)
    storage.is_cancelled.side_effect = cancelled or [False, False, False, False, False]
    checkout = AsyncMock(); checkout.checkout.return_value = SimpleNamespace(commit_sha='e' * 40)
    scanner = AsyncMock()
    scanner.scan.side_effect = scan_error
    if scan_error is None: scanner.scan.return_value = scanner_result()
    holder = {}
    def factory(_):
        holder['workspace'] = Workspace(tmp_path / 'workspace')
        return holder['workspace']
    return SecurityPipeline(storage, checkout, scanner, factory, {}, agent), storage, holder


def test_success_stages_summary_and_cleanup(tmp_path):
    engine, storage, holder = pipeline(tmp_path)
    result = asyncio.run(engine.process(run_record()))
    assert result == 'completed' and holder['workspace'].exited
    assert [call.args[1] for call in storage.heartbeat.await_args_list] == [15, 30, 60, 70, 80, 95]
    candidates, summary = storage.complete.await_args.args[2:]
    assert len(candidates) == summary['scanner_findings'] == summary['normalized_findings'] == 1
    assert summary['medium'] == 1 and summary['agent_enriched'] == 0
    assert summary['analysis_mode'] == 'deterministic_only' and summary['agent_usage'] == {}
    assert summary['commit_sha'] == 'e' * 40 and summary['files_analyzed'] is None
    storage.fail.assert_not_awaited()


@pytest.mark.parametrize('cancelled,heartbeat_count', [([True], 1), ([False, True], 2),
    ([False, False, True], 4), ([False, False, False, True], 5),
    ([False, False, False, False, True], 6)])
def test_cancellation_between_major_stages(tmp_path, cancelled, heartbeat_count):
    engine, storage, holder = pipeline(tmp_path, cancelled=cancelled)
    assert asyncio.run(engine.process(run_record())) == 'cancelled'
    assert storage.heartbeat.await_count == heartbeat_count
    storage.complete.assert_not_awaited(); storage.fail.assert_not_awaited()
    assert holder['workspace'].exited


@pytest.mark.parametrize('error,reason', [(DependencyUnavailable('path'), 'Required security tool is unavailable'),
    (ExecutionTimeout('sensitive path'), 'Security analysis timed out'),
    (OutputLimitExceeded('data'), 'Security tool output exceeded its limit'),
    (RepositoryPolicyError('secret repo'), 'Repository is not authorized for analysis')])
def test_failures_are_safe_and_cleanup(tmp_path, error, reason):
    engine, storage, holder = pipeline(tmp_path, scan_error=error)
    assert asyncio.run(engine.process(run_record())) == 'failed'
    storage.fail.assert_awaited_once()
    assert storage.fail.await_args.args[1] == reason
    assert 'sensitive' not in reason and 'secret' not in reason
    assert holder['workspace'].exited


def test_changed_run_does_not_overwrite_state(tmp_path):
    engine, storage, _ = pipeline(tmp_path)
    storage.heartbeat.side_effect = RunChanged('cancelled')
    assert asyncio.run(engine.process(run_record())) == 'cancelled_or_changed'
    storage.fail.assert_not_awaited(); storage.complete.assert_not_awaited()


def test_pipeline_records_agent_enrichment_without_changing_scanner_count(tmp_path):
    agent = AsyncMock()
    agent.enrich.side_effect = lambda candidates, _: (
        [candidates[0].model_copy(update={'title': 'Reviewed', 'analysis': {'priority': 'high'}})],
        1, {'total_tokens': 42})
    engine, storage, _ = pipeline(tmp_path, agent=agent)
    assert asyncio.run(engine.process(run_record())) == 'completed'
    candidates, summary = storage.complete.await_args.args[2:]
    assert candidates[0].title == 'Reviewed'
    assert summary['scanner_findings'] == summary['normalized_findings'] == summary['agent_enriched'] == 1
    assert summary['analysis_mode'] == 'agent_enriched'
    assert summary['agent_usage'] == {'total_tokens': 42}


def test_candidate_conversion_is_valid_and_has_no_snippet():
    context = SimpleNamespace(organization_id='a' * 24, project_id='b' * 24, asset_id='c' * 24,
        security_run_id='d' * 24, repository='https://github.com/a/b', branch='main', commit_sha='e' * 40)
    candidate = normalize_semgrep(scanner_result(), context)[0]
    document = candidate_to_document(candidate, datetime.now(timezone.utc))
    assert document['source'] == 'semgrep' and document['status'] == 'new'
    assert document['security_run_id'] == document['last_security_run_id'] == 'd' * 24
    assert document['security_run_ids'] == ['d' * 24]
    assert document['location'] == 'src/app.py:4-4'
    assert 'eval(value)' not in str(document)


class Transaction:
    async def __aenter__(self): return self
    async def __aexit__(self, *_): return False
    async def with_transaction(self, callback): return await callback(self)


def db_mock():
    db = SimpleNamespace()
    db.client = SimpleNamespace(start_session=AsyncMock(return_value=Transaction()))
    for name in ['security_runs', 'activity_events', 'projects', 'assets', 'users', 'findings', 'remediations', 'scanner_results']:
        setattr(db, name, AsyncMock())
    return db


def test_atomic_claim_and_started_event():
    db, run = db_mock(), run_record()
    run['status'] = 'running'
    db.security_runs.find_one_and_update.return_value = run
    storage = WorkerRepository(db, 'worker-one', 60)
    assert asyncio.run(storage.claim()) == run
    query, update = db.security_runs.find_one_and_update.await_args.args[:2]
    assert query == {'status': 'queued'} and update['$set']['worker_id'] == 'worker-one'
    assert db.security_runs.find_one_and_update.await_args.kwargs['session'] is not None
    event = db.activity_events.insert_one.await_args.args[0]
    assert event['event_type'] == 'security_run_started' and event['actor_id'] == 'security-worker'


def test_only_one_atomic_claim_receives_run():
    db, run = db_mock(), run_record()
    db.security_runs.find_one_and_update.side_effect = [run, None]
    first, second = WorkerRepository(db, 'one', 60), WorkerRepository(db, 'two', 60)
    assert asyncio.run(first.claim()) == run and asyncio.run(second.claim()) is None
    assert db.activity_events.insert_one.await_count == 1


def test_operator_verification_can_claim_only_its_created_run():
    db, run = db_mock(), run_record()
    db.security_runs.find_one_and_update.return_value = run
    storage = WorkerRepository(db, 'verification', 60)
    assert asyncio.run(storage.claim(str(run['_id']))) == run
    assert db.security_runs.find_one_and_update.await_args.args[0] == {
        'status': 'queued', '_id': run['_id']}


def test_remediation_verification_claim_is_atomic_and_audited():
    db, remediation = db_mock(), {
        '_id': ObjectId(), 'organization_id': 'a' * 24, 'project_id': 'b' * 24,
        'verification_status': 'testing'}
    db.remediations.find_one_and_update.return_value = remediation
    storage = WorkerRepository(db, 'worker-one', 60)
    assert asyncio.run(storage.claim_remediation()) == remediation
    query, update = db.remediations.find_one_and_update.await_args.args[:2]
    assert query == {'verification_status': 'queued'}
    assert update['$set']['verification_status'] == 'testing'
    assert update['$set']['worker_id'] == 'worker-one'
    event = db.activity_events.insert_one.await_args.args[0]
    assert event['event_type'] == 'remediation_verification_started'
    assert event['entity_type'] == 'remediation'


def authorized_records(run):
    project = {'_id': ObjectId(run['project_id']), 'organization_id': run['organization_id'],
               'status': 'active'}
    asset = {'_id': ObjectId(run['asset_ids'][0]), 'organization_id': run['organization_id'],
             'project_id': run['project_id'], 'status': 'active', 'type': 'repository',
             'target': 'https://github.com/a/b', 'metadata': {}}
    user = {'_id': ObjectId(run['requested_by']), 'organizationId': run['organization_id'],
            'role': 'admin', 'status': 'active'}
    return project, asset, user


def test_worker_rechecks_requester_and_repository_authorization():
    db, run = db_mock(), run_record()
    project, asset, user = authorized_records(run)
    db.projects.find_one.return_value = project
    db.assets.find_one.return_value = asset
    db.users.find_one.return_value = user
    storage = WorkerRepository(db, 'worker', 60)
    _, _, _, snapshot = asyncio.run(storage.load_authorized_context(
        run, {run['organization_id']: {'https://github.com/a/b'}}))
    assert snapshot.organization_id == run['organization_id']
    assert snapshot.asset_id == run['asset_ids'][0]


@pytest.mark.parametrize('change', [
    {'status': 'disabled'},
    {'role': 'user'},
    {'organizationId': 'f' * 24},
])
def test_worker_rejects_requester_changes_after_queue(change):
    db, run = db_mock(), run_record()
    project, asset, user = authorized_records(run)
    user.update(change)
    db.projects.find_one.return_value = project
    db.assets.find_one.return_value = asset
    db.users.find_one.return_value = user
    storage = WorkerRepository(db, 'worker', 60)
    with pytest.raises(ValueError, match='no longer authorized'):
        asyncio.run(storage.load_authorized_context(
            run, {run['organization_id']: {'https://github.com/a/b'}}))


def test_worker_rejects_asset_removed_after_queue():
    db, run = db_mock(), run_record()
    project, _, user = authorized_records(run)
    db.projects.find_one.return_value = project
    db.assets.find_one.return_value = None
    db.users.find_one.return_value = user
    with pytest.raises(ValueError, match='asset is unavailable'):
        asyncio.run(WorkerRepository(db, 'worker', 60).load_authorized_context(
            run, {run['organization_id']: {'https://github.com/a/b'}}))


def test_heartbeat_fails_closed_and_expired_claim_recovery():
    db, run = db_mock(), run_record()
    db.security_runs.update_one.return_value.modified_count = 0
    storage = WorkerRepository(db, 'worker', 60)
    with pytest.raises(RunChanged): asyncio.run(storage.heartbeat(run, 30))
    failed_one, failed_two = deepcopy(run), deepcopy(run)
    failed_one['status'] = failed_two['status'] = 'failed'
    db.security_runs.find_one_and_update.side_effect = [failed_one, failed_two, None]
    assert asyncio.run(storage.fail_expired_claims()) == 2
    query, update = db.security_runs.find_one_and_update.await_args_list[0].args
    assert query['status'] == 'running' and '$lt' in query['claim_expires_at']
    assert update['$set']['status'] == 'failed' and 'worker_id' in update['$unset']
    assert db.activity_events.insert_one.await_count == 2
    assert db.activity_events.insert_one.await_args.args[0]['event_type'] == 'security_run_failed'


def test_transactional_completion_uses_upsert_and_conditional_run():
    db, run = db_mock(), run_record()
    db.security_runs.update_one.return_value.modified_count = 1
    storage = WorkerRepository(db, 'worker', 60)
    context = SimpleNamespace(organization_id=run['organization_id'], project_id=run['project_id'],
        asset_id=run['asset_ids'][0], security_run_id=str(run['_id']), repository='https://github.com/a/b',
        branch='main', commit_sha='e' * 40)
    candidates = normalize_semgrep(scanner_result(), context)
    summary = {'commit_sha': 'e' * 40}
    asyncio.run(storage.complete(run, scanner_result(), candidates, summary))
    assert db.findings.update_one.await_args.kwargs['upsert'] is True
    query = db.findings.update_one.await_args.args[0]
    assert query == {'organization_id': run['organization_id'], 'fingerprint': candidates[0].fingerprint}
    finding_update = db.findings.update_one.await_args.args[1]
    assert finding_update['$addToSet']['security_run_ids'] == str(run['_id'])
    run_query = db.security_runs.update_one.await_args.args[0]
    assert run_query['status'] == 'running' and run_query['worker_id'] == 'worker'
    assert db.activity_events.insert_many.await_args.args[0][1]['event_type'] == 'security_run_completed'


def test_completion_aborts_when_cancelled():
    db, run = db_mock(), run_record()
    db.security_runs.update_one.return_value.modified_count = 0
    storage = WorkerRepository(db, 'worker', 60)
    with pytest.raises(RunChanged):
        asyncio.run(storage.complete(run, scanner_result(), [], {'commit_sha': 'e' * 40}))


def test_remediation_verification_completion_is_transactional_and_approval_ready():
    db = db_mock()
    remediation = {'_id': ObjectId(), 'organization_id': 'a' * 24, 'project_id': 'b' * 24,
                   'asset_id': 'c' * 24, 'verification_status': 'testing'}
    db.remediations.update_one.return_value.modified_count = 1
    result = VerificationResult(
        remediation_id=str(remediation['_id']), status='verified',
        original_finding_present=False, new_findings_count=0,
        new_equal_or_higher_findings_count=0, before_finding_count=1,
        after_finding_count=0, before_severity_counts={'high': 1},
        after_severity_counts={}, scanner='semgrep', scanner_version='1.test',
        summary='Removed', verified_at=datetime.now(timezone.utc))
    asyncio.run(WorkerRepository(db, 'worker', 60).complete_remediation(
        remediation, result, scanner_result().model_copy(update={'results': []})))
    update = db.remediations.update_one.await_args.args[1]['$set']
    assert update['verification_status'] == 'verified'
    assert update['status'] == 'awaiting_approval'
    raw = db.scanner_results.insert_one.await_args.args[0]
    assert raw['remediation_id'] == str(remediation['_id']) and raw['phase'] == 'after_patch'
    event = db.activity_events.insert_one.await_args.args[0]
    assert event['event_type'] == 'remediation_verified'
