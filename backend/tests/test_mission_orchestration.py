import asyncio
import json
import os
from dataclasses import replace
from pathlib import Path
from uuid import uuid4

import pytest
from bson import ObjectId
from fastapi import HTTPException

from core.database import DatabaseSettings, create_database_client
from core.domain_indexes import ensure_domain_indexes
from core.ownership import OrganizationScope
from mission_orchestration.governance import ATTEMPT_BUSY, POLICY_DENIED, FixtureGateway, FixtureRejected
from mission_orchestration.plan import (
    APPROVAL_REQUIRED, ASSESSMENT_V1, FIXTURE_REMEDIATION_MISSION, FIXTURE_SCAN_MISSION, GITHUB_SCAN_MISSION,
    FixtureAttempt, MissionRef, ProgressEvent, TaskResult, validate_plan,
)
from mission_orchestration.storage import OrchestrationStore, utc_now
from repositories.missions import MissionRepository


def test_plan_orders_dependencies_and_rejects_cycles_or_inputs_outside_scope():
    prepare, assess, summarize = ASSESSMENT_V1
    assert validate_plan((summarize, assess, prepare)) == ASSESSMENT_V1
    with pytest.raises(ValueError, match='cycle'):
        validate_plan((replace(prepare, dependencies=('summarize',)), assess, summarize))
    with pytest.raises(ValueError, match='Invalid input'):
        validate_plan((prepare, replace(assess, inputs=('arbitrary_repository',)), summarize))
    with pytest.raises(ValueError, match='Invalid dependencies'):
        validate_plan((prepare, replace(assess, dependencies=('missing',)), summarize))


async def seed_mission_scope(db, organization_id):
    project_id, asset_id, user_id = ObjectId(), ObjectId(), ObjectId()
    await db.client_companies.update_one(
        {'_id': ObjectId(organization_id)}, {'$setOnInsert': {'status': 'active'}}, upsert=True)
    await db.users.insert_one({'_id': user_id, 'organizationId': organization_id, 'role': 'admin'})
    await db.projects.insert_one({'_id': project_id, 'organization_id': organization_id, 'status': 'active'})
    await db.assets.insert_one({'_id': asset_id, 'organization_id': organization_id, 'status': 'active',
                                'project_id': str(project_id), 'type': 'repository', 'target': 'fixture://test'})
    return project_id, asset_id, user_id


async def seed_mission(db, organization_id):
    mission = MissionRef(organization_id, str(ObjectId()))
    project_id, asset_id, user_id = await seed_mission_scope(db, organization_id)
    now = utc_now()
    await db.missions.insert_one({
        '_id': ObjectId(mission.mission_id), 'organization_id': organization_id,
        'request_key': uuid4().hex, 'status': 'queued', 'created_at': now, 'updated_at': now,
        'mission_type': 'repository_assessment', 'requested_by': str(user_id),
        'project_id': str(project_id), 'asset_id': str(asset_id),
    })
    await db.mission_outbox.insert_one({
        '_id': ObjectId(mission.mission_id), 'organization_id': organization_id,
        'mission_id': mission.mission_id, 'type': 'start_mission', 'status': 'pending', 'created_at': now,
    })
    return mission


async def with_test_database(check):
    uri = os.environ.get('MISSION_TEST_MONGO_URL')
    if not uri:
        pytest.skip('Set MISSION_TEST_MONGO_URL to an isolated MongoDB replica set')
    settings = DatabaseSettings(uri, 'havosec_mission_test_' + uuid4().hex)
    client = create_database_client(settings)
    try:
        db = client[settings.database_name]
        await ensure_domain_indexes(db)
        await check(db, OrchestrationStore(db))
    finally:
        try:
            await client.drop_database(settings.database_name)
        finally:
            client.close()


def test_mongo_retries_projection_slot_and_cancellation():
    async def check(db, store):
        await store.check_indexes()
        organization = str(ObjectId())
        first = await seed_mission(db, organization)
        command = await store.claim_command()
        await db.mission_outbox.update_one({'_id': command['_id']}, {'$set': {'available_at': utc_now()}})
        replacement = await store.claim_command()
        assert replacement['_id'] == command['_id'] and replacement['attempts'] == 2
        await store.deliver_command(command, first.workflow_id)
        assert (await db.mission_outbox.find_one({'_id': command['_id']}))['status'] == 'pending'
        await store.deliver_command(replacement, first.workflow_id)
        assert (await db.mission_outbox.find_one({'_id': command['_id']}))['status'] == 'delivered'

        second = await seed_mission(db, organization)
        other = await seed_mission(db, str(ObjectId()))
        for mission in (first, second, other):
            assert (await store.project(ProgressEvent(mission, 1, 'queued', 3))).status == 'queued'
        slots = await asyncio.gather(store.acquire_slot(first), store.acquire_slot(second))
        assert sum(state.acquired_slot for state in slots) == 1
        owner, waiting = (first, second) if slots[0].acquired_slot else (second, first)
        assert (await store.acquire_slot(other)).acquired_slot
        running = ProgressEvent(owner, 2, 'running', 3, 'prepare')
        await store.project(running)
        await store.project(running)

        repository = MissionRepository(db)
        document = await store.get_mission(owner)
        scope = OrganizationScope(organization)
        cancellations = await asyncio.gather(*(repository.request_cancellation(scope, document) for _ in range(3)))
        assert len({result['cancel_requested_at'] for result in cancellations}) == 1
        assert await db.mission_outbox.count_documents({'type': 'cancel_mission'}) == 1
        result = TaskResult('prepare', 'fixture_scope', 1, 'fixture/prepare/1')
        assert (await store.project(ProgressEvent(owner, 3, 'completed', 3, completed=[result]))).status == 'cancelled'
        assert (await store.project(running)).status == 'cancelled'
        finished = await store.get_mission(owner)
        assert finished['orchestration']['version'] == 3
        assert finished['orchestration']['completed'][0]['task_id'] == 'prepare'
        assert (await store.acquire_slot(waiting)).acquired_slot

    asyncio.run(with_test_database(check))


def test_temporal_runs_isolated_semgrep_and_reports_gaps(monkeypatch):
    address = os.environ.get('MISSION_TEST_TEMPORAL_ADDRESS')
    commit = os.environ.get('MISSION_TEST_FIXTURE_COMMIT')
    if not address or not commit:
        pytest.skip('Set the Temporal address and fixture commit, and load the pinned Semgrep image')
    pytest.importorskip('temporalio')
    from temporalio.client import Client
    from temporalio.worker import Worker

    from mission_orchestration.activities import MissionActivities
    from mission_orchestration.dispatcher import MissionDispatcher
    from mission_orchestration.fixture_assessment import SCANNER_VERSION
    from mission_orchestration import fixture_remediation
    from mission_orchestration.workflow import RepositoryAssessment
    from security_engine.patch_integrity import patch_sha256

    async def check(db, store):
        client = await Client.connect(address)
        queue = 'havosec-fixture-' + uuid4().hex
        dispatcher = MissionDispatcher(store, client, queue)
        activities = MissionActivities(store)
        async with Worker(client, task_queue=queue, workflows=[RepositoryAssessment], activities=[
            activities.acquire_mission_slot, activities.project_mission_progress, activities.run_mission_fixture,
        ]):
            async def run(snapshot, expected, mission_type=FIXTURE_SCAN_MISSION):
                ref = await seed_mission(db, str(ObjectId()))
                await db.missions.update_one(store.mission_query(ref), {'$set': {
                    'mission_type': mission_type, 'fixture_commit': snapshot,
                }})
                assert await dispatcher.dispatch_one()
                assert await asyncio.wait_for(client.get_workflow_handle(ref.workflow_id).result(), 100) == expected
                return await store.get_mission(ref)

            report = (await run(commit, 'completed'))['assessment_report']
            assert report['status'] == 'complete'
            assert report['commit_sha'] == commit and report['scanner_version'] == SCANNER_VERSION
            assert len(report['rules_sha256']) == 64
            rules_digest = report['rules_sha256']
            assert report['coverage']['scanned'] == ['app.py', 'clean.py']
            assert not report['gaps']
            assert report['observations']
            assert all(item['path'] == 'app.py' and len(item['evidence_sha256']) == 64
                       for item in report['observations'])
            assert any(item['rule_id'].endswith('havosec.python.eval') for item in report['observations'])

            report = (await run('0' * 40, 'partial'))['assessment_report']
            assert report['status'] == 'incomplete' and report['gaps'] and not report['observations']

            verified = (await run(commit, 'completed', FIXTURE_REMEDIATION_MISSION))['remediation_verification']
            assert verified['status'] == 'verified', verified['summary']
            assert verified['source_commit'] == commit
            assert verified['rules_sha256'] == rules_digest
            assert verified['patch_sha256'] == patch_sha256(verified['proposal']['patch'])
            assert verified['comparison']['before_finding_count'] == 2
            assert verified['comparison']['after_finding_count'] == 1
            assert verified['publication_status'] == 'fixture_only'

            original_git_blob = fixture_remediation.git_blob

            async def shifted_eval(snapshot, name, workspace):
                if name == fixture_remediation.PATCH_PATH:
                    return (b'--- a/app.py\n+++ b/app.py\n@@ -2,5 +2,6 @@\n \n \n'
                            b' def unsafe(user_input):\n+    # A comment does not fix eval.\n'
                            b'     return eval(user_input)\n \n')
                return await original_git_blob(snapshot, name, workspace)

            monkeypatch.setattr(fixture_remediation, 'git_blob', shifted_eval)
            failed = (await run(commit, 'partial', FIXTURE_REMEDIATION_MISSION))['remediation_verification']
            assert failed['status'] == 'failed', failed['summary']
            assert failed['comparison']['original_finding_present'] is True

    asyncio.run(with_test_database(check))


def test_temporal_scans_authorized_github_snapshot(monkeypatch):
    address = os.environ.get('MISSION_TEST_TEMPORAL_ADDRESS')
    pilot = os.environ.get('MISSION_TEST_GITHUB_PILOT')
    use_app = os.environ.get('MISSION_TEST_USE_GITHUB_APP') == '1'
    if not address or not pilot:
        if use_app:
            pytest.fail('The authenticated check requires a test Temporal address and pilot repository')
        pytest.skip('Set a Temporal address and a public pilot snapshot')
    name, repo_id, *pin = pilot.split(',')
    repository_id = int(repo_id)
    if use_app:
        from urllib.parse import urlsplit

        mongo = urlsplit(os.environ.get('MISSION_TEST_MONGO_URL', ''))
        assert mongo.scheme == 'mongodb' and mongo.hostname in ('localhost', '127.0.0.1', '::1'), (
            'The authenticated check requires a local test MongoDB instance')
        assert mongo.username is None and ',' not in mongo.netloc
    else:
        assert len(pin) == 1, 'The public pilot requires a pinned commit'
    pytest.importorskip('temporalio')
    from fastapi import FastAPI
    from httpx import ASGITransport, AsyncClient
    from temporalio.client import Client
    from temporalio.worker import Worker

    from core.database import get_database, load_backend_environment
    from integrations.github.client import GitHubAppClient, download_repository_archive
    from integrations.github.config import GitHubAppSettings
    from mission_orchestration.activities import MissionActivities
    from mission_orchestration.dispatcher import MissionDispatcher
    from mission_orchestration.workflow import RepositoryAssessment
    from routes.missions import router
    from services import missions
    from utils.auth import get_current_user

    class PublicGitHubArchive:
        async def download_readonly_archive(self, repository, requested_id, revision, destination, limit):
            assert (repository, requested_id, revision) == (name, repository_id, pin[0])
            await download_repository_archive('https://api.github.com', repository, revision, destination, limit)

    async def pinned_public_commit(github):
        assert github['repository'] == name and github['repository_id'] == repository_id
        return pin[0]

    if not use_app:
        monkeypatch.setattr(missions, 'resolve_github_commit', pinned_public_commit)

    async def check(db, store):
        organization = str(ObjectId())
        project, asset, actor = await seed_mission_scope(db, organization)
        if use_app:
            load_backend_environment()
            settings = GitHubAppSettings.from_environment(require_installation=True)
            installed = await GitHubAppClient(settings).get_installation()
        else:
            installed = {'installation_id': 42, 'permissions': {'contents': 'read'}}
        integration = ObjectId()
        scope = {'organization_id': organization}
        await db.client_companies.update_one({'_id': ObjectId(organization)}, {
            '$set': {'mission_policy.github_assessment': 'require_approval'},
        })
        await db.github_integrations.insert_one({
            **scope, '_id': integration, 'installation_id': installed['installation_id'], 'status': 'active',
            'permissions': installed['permissions'],
        })
        await db.github_repositories.insert_one({
            **scope, 'integration_id': str(integration), 'repository_id': repository_id, 'full_name': name,
            'default_branch': 'main', 'authorized': True, 'connection_status': 'active',
        })
        await db.assets.update_one({**scope, '_id': asset}, {'$set': {
            'target': 'https://github.com/' + name,
            'source_control': {'provider': 'github', 'integration_id': str(integration),
                               'repository_id': repository_id, 'repository_full_name': name,
                               'default_branch': 'main', 'connection_status': 'active'},
        }})
        app = FastAPI()
        app.include_router(router, prefix='/api/missions')
        app.dependency_overrides[get_database] = lambda: db
        app.dependency_overrides[get_current_user] = lambda: {
            'id': str(actor), 'organizationId': organization, 'role': 'admin',
        }
        client = await Client.connect(address)
        queue = 'havosec-real-pilot-' + uuid4().hex
        factory = None if use_app else lambda _: PublicGitHubArchive()
        activities = MissionActivities(store, github_client_factory=factory)
        async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as api:
            response = await api.post('/api/missions', headers={'Idempotency-Key': uuid4().hex}, json={
                'project_id': str(project), 'asset_id': str(asset), 'objective': 'Read-only GitHub pilot',
                'mission_type': GITHUB_SCAN_MISSION,
            })
            assert response.status_code == 201, response.text
            queued = response.json()
            commit = queued['source_commit']
            assert isinstance(commit, str) and len(commit) == 40
            assert not pin or commit == pin[0]
            ref = MissionRef(organization, queued['id'], GITHUB_SCAN_MISSION)
            path = '/api/missions/' + ref.mission_id
            async with Worker(client, task_queue=queue, workflows=[RepositoryAssessment], activities=[
                activities.acquire_mission_slot, activities.project_mission_progress, activities.run_mission_fixture,
            ]):
                assert await MissionDispatcher(store, client, queue).dispatch_one()
                async with asyncio.timeout(40):
                    while True:
                        actions = (await api.get(path + '/actions')).json()
                        pending = next((a for a in actions if a['operation'] == 'assess'
                                        and a['decision']['outcome'] == 'require_approval'), None)
                        if pending is not None:
                            assert not pending['attempts']
                            break
                        await asyncio.sleep(.1)
                approval = await api.post(path + '/actions/assess/approve',
                                          json={'action_digest': pending['digest']})
                assert approval.status_code == 200, approval.text
                status = await asyncio.wait_for(client.get_workflow_handle(ref.workflow_id).result(), timeout=160)
            report_response = await api.get(path + '/report')
            assert report_response.status_code == 200, report_response.text
            report = report_response.json()
        report_path = os.environ.get('MISSION_TEST_GITHUB_REPORT')
        if report_path:
            Path(report_path).write_text(json.dumps(report, default=str, indent=2) + '\n', encoding='utf-8')
        assert report['commit_sha'] == commit and report['repository'] == name
        assert report['coverage']['scanned'], report['gaps']
        assert status == ('completed' if not report['gaps'] else 'partial')
        print('Pilot scan:', json.dumps({'repository': name, 'commit': commit,
                                        'files': len(report['coverage']['scanned']),
                                        'excluded': report['coverage']['excluded'],
                                        'observations': len(report['observations']), 'gaps': report['gaps']}))

    asyncio.run(with_test_database(check))


def test_fixture_gateway_policy_approval_and_retry():
    from datetime import timedelta

    async def check(db, store):
        organization = str(ObjectId())
        mission = await seed_mission(db, organization)
        identity = store.mission_query(mission)
        await db.client_companies.update_one({'_id': ObjectId(organization)}, {
            '$set': {'mission_policy.fixture': 'require_approval'},
        })
        actor = (await store.get_mission(mission))['requested_by']
        await store.project(ProgressEvent(mission, 1, 'queued', 3))
        await store.acquire_slot(mission)
        await store.project(ProgressEvent(mission, 2, 'running', 3, 'prepare'))
        gateway = FixtureGateway(db)
        request = FixtureAttempt(mission, 'prepare')
        foreign = FixtureAttempt(MissionRef(str(ObjectId()), mission.mission_id), 'prepare')
        with pytest.raises(FixtureRejected, match=POLICY_DENIED):
            await gateway.begin(foreign, 'foreign', 1)
        with pytest.raises(FixtureRejected, match=APPROVAL_REQUIRED):
            await gateway.begin(request, 'pending', 1)
        await store.project(ProgressEvent(mission, 3, 'awaiting_approval', 3, 'prepare'))
        action = (await store.get_mission(mission))['fixture_actions']['prepare']
        assert action['attempts'] == []
        digest = action['digest']
        with pytest.raises(HTTPException) as altered:
            await gateway.change_approval(mission, 'prepare', actor, '0' * 64)
        assert altered.value.status_code == 409
        granted = await gateway.change_approval(mission, 'prepare', actor, digest)
        await gateway.change_approval(mission, 'prepare', actor, digest, revoke_id=granted['id'])
        with pytest.raises(FixtureRejected, match=APPROVAL_REQUIRED):
            await gateway.begin(request, 'revoked', 1)
        await gateway.change_approval(mission, 'prepare', actor, digest)
        await db.missions.update_one(identity, {'$set': {
            'fixture_actions.prepare.approval.expires_at': utc_now() - timedelta(seconds=1),
        }})
        with pytest.raises(FixtureRejected, match=APPROVAL_REQUIRED):
            await gateway.begin(request, 'expired', 1)
        granted = await gateway.change_approval(mission, 'prepare', actor, digest)
        await db.users.update_one({'_id': ObjectId(actor)}, {'$set': {'role': 'user'}})
        with pytest.raises(FixtureRejected, match=POLICY_DENIED):
            await gateway.begin(request, 'membership_changed', 1)
        await db.users.update_one({'_id': ObjectId(actor)}, {'$set': {'role': 'admin'}})
        assert await gateway.begin(request, 'first', 1) is None
        with pytest.raises(FixtureRejected, match=ATTEMPT_BUSY):
            await gateway.begin(request, 'contender', 2)
        await gateway.finish(request, 'first', 'failed')
        assert await gateway.begin(request, 'retry', 2) is None
        result = TaskResult('prepare', 'fixture_scope', 2, 'retry')
        await gateway.finish(request, 'retry', 'completed', result)
        assert await gateway.begin(request, 'replay', 3) == result
        action = (await store.get_mission(mission))['fixture_actions']['prepare']
        assert action['approval']['id'] == granted['id']
        assert action['approval']['consumed_for'] == digest
        assert [attempt['state'] for attempt in action['attempts']] == ['failed', 'completed']
        assert await db.mission_execution_events.count_documents({
            'organization_id': organization, 'mission_id': mission.mission_id, 'type': 'approval_revoked',
        }) == 1

        await store.project(ProgressEvent(mission, 4, 'running', 3, 'assess', [result]))
        asset_id = (await store.get_mission(mission))['asset_id']
        await db.assets.update_one({'_id': ObjectId(asset_id)}, {'$set': {'target': 'fixture://changed'}})
        with pytest.raises(FixtureRejected, match=POLICY_DENIED):
            await gateway.begin(FixtureAttempt(mission, 'assess'), 'changed_target', 1)
        action = (await store.get_mission(mission))['fixture_actions']['assess']
        assert action['decision']['reason'] == 'target_changed' and action['attempts'] == []

    asyncio.run(with_test_database(check))


def test_temporal_dispatch_restart_activity_retry_and_cancellation():
    address = os.environ.get('MISSION_TEST_TEMPORAL_ADDRESS')
    if not address:
        pytest.skip('Set MISSION_TEST_TEMPORAL_ADDRESS to an isolated Temporal development server')
    pytest.importorskip('temporalio')
    from temporalio import activity
    from temporalio.client import Client
    from temporalio.exceptions import ApplicationError
    from temporalio.worker import Worker

    from mission_orchestration.activities import MissionActivities
    from mission_orchestration.dispatcher import MissionDispatcher
    from mission_orchestration.workflow import RepositoryAssessment

    async def check(db, store):
        client = await Client.connect(address)
        queue = 'havosec-test-' + uuid4().hex
        organization = str(ObjectId())
        recovered = await seed_mission(db, organization)
        dispatcher = MissionDispatcher(store, client, queue)

        class InterruptedStore(OrchestrationStore):
            async def deliver_command(self, command, workflow_id):
                raise RuntimeError('simulated dispatcher crash after Temporal accepted the start')

        with pytest.raises(RuntimeError, match='simulated dispatcher crash'):
            await MissionDispatcher(InterruptedStore(db), client, queue).dispatch_one()
        handle = client.get_workflow_handle(recovered.workflow_id)
        original_run = (await handle.describe()).run_id
        await db.mission_outbox.update_one(
            {'_id': ObjectId(recovered.mission_id)}, {'$set': {'available_at': utc_now()}})
        assert await dispatcher.dispatch_one()
        assert (await handle.describe()).run_id == original_run

        interrupted = asyncio.Event()
        started_for_cancellation = asyncio.Event()
        cancelled = await seed_mission(db, organization)
        failed = await seed_mission(db, organization)
        attempts = []
        class TestActivities(MissionActivities):
            async def execute_fixture(self, request, task, attempt, attempt_id):
                if request.mission == recovered and task.id == 'assess' and attempt == 1:
                    interrupted.set()
                    raise ApplicationError('fixture failed on its first attempt')
                if request.mission == cancelled:
                    assert task.id == 'prepare'
                    started_for_cancellation.set()
                    while True:
                        activity.heartbeat()
                        await asyncio.sleep(0.2)
                if request.mission == failed:
                    attempts.append(attempt)
                    raise ApplicationError('fixture fails on every attempt')
                return await super().execute_fixture(request, task, attempt, attempt_id)

        activities = TestActivities(store)

        def worker():
            return Worker(client, task_queue=queue, workflows=[RepositoryAssessment], activities=[
                activities.acquire_mission_slot, activities.project_mission_progress, activities.run_mission_fixture,
            ])

        async def wait_for_action(mission, task_id, predicate):
            async with asyncio.timeout(30):
                while True:
                    document = await store.get_mission(mission)
                    action = document.get('fixture_actions', {}).get(task_id)
                    if action and predicate(document, action):
                        return document, action
                    await asyncio.sleep(0.1)

        async with worker():
            await asyncio.wait_for(interrupted.wait(), timeout=25)
            await wait_for_action(recovered, 'assess', lambda _, action: action['attempts'][0]['state'] == 'failed')
        async with worker():
            assert await asyncio.wait_for(handle.result(), timeout=30) == 'completed'
            progress = (await store.get_mission(recovered))['orchestration']
            assert [task['attempt'] for task in progress['completed']] == [1, 2, 1]
            action = (await store.get_mission(recovered))['fixture_actions']['assess']
            assert [attempt['state'] for attempt in action['attempts']] == ['failed', 'completed']
            assert await dispatcher.dispatch_one()
            assert await dispatcher.dispatch_one()
            await asyncio.wait_for(started_for_cancellation.wait(), timeout=25)
            await MissionRepository(db).request_cancellation(
                OrganizationScope(organization), await store.get_mission(cancelled))
            assert await dispatcher.dispatch_one()
            assert await asyncio.wait_for(
                client.get_workflow_handle(cancelled.workflow_id).result(), timeout=25) == 'cancelled'
            cancelled_record = await store.get_mission(cancelled)
            assert cancelled_record['orchestration']['completed'] == []
            assert cancelled_record['fixture_actions']['prepare']['attempts'][0]['state'] == 'interrupted'
            assert await asyncio.wait_for(
                client.get_workflow_handle(failed.workflow_id).result(), timeout=40) == 'failed'
            assert attempts == [1, 2, 3]

            approval_org = str(ObjectId())
            governed = await seed_mission(db, approval_org)
            await db.client_companies.update_one({'_id': ObjectId(approval_org)}, {
                '$set': {'mission_policy.fixture': 'require_approval'},
            })
            assert await dispatcher.dispatch_one()
            gateway = FixtureGateway(db)
            for task in ASSESSMENT_V1:
                document, action = await wait_for_action(
                    governed, task.id, lambda doc, entry: doc['status'] == 'awaiting_approval'
                    and doc['orchestration']['current_task'] == task.id and not entry['attempts'],
                )
                await gateway.change_approval(governed, task.id, document['requested_by'], action['digest'])
            assert await asyncio.wait_for(
                client.get_workflow_handle(governed.workflow_id).result(), timeout=25) == 'completed'
            governed_actions = (await store.get_mission(governed))['fixture_actions']
            assert all(len(action['attempts']) == 1 and action['approval']['consumed_for'] == action['digest']
                       for action in governed_actions.values())

    asyncio.run(with_test_database(check))
