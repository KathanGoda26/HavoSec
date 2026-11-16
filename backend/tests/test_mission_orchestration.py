import asyncio
import os
from dataclasses import replace
from uuid import uuid4

import pytest
from bson import ObjectId
from fastapi import HTTPException

from core.database import DatabaseSettings, create_database_client
from core.domain_indexes import ensure_domain_indexes
from core.ownership import OrganizationScope
from mission_orchestration.governance import ATTEMPT_BUSY, POLICY_DENIED, FixtureGateway, FixtureRejected
from mission_orchestration.plan import (
    APPROVAL_REQUIRED, ASSESSMENT_V1, FIXTURE_SCAN_MISSION, FixtureAttempt, MissionRef, ProgressEvent, TaskResult,
    validate_plan,
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


async def seed_mission(db, organization_id):
    mission = MissionRef(organization_id, str(ObjectId()))
    project_id, asset_id, user_id = ObjectId(), ObjectId(), ObjectId()
    await db.client_companies.update_one(
        {'_id': ObjectId(organization_id)}, {'$setOnInsert': {'status': 'active'}}, upsert=True)
    await db.users.insert_one({'_id': user_id, 'organizationId': organization_id, 'role': 'admin'})
    await db.projects.insert_one({'_id': project_id, 'organization_id': organization_id, 'status': 'active'})
    await db.assets.insert_one({'_id': asset_id, 'organization_id': organization_id, 'status': 'active',
                                'project_id': str(project_id), 'type': 'repository', 'target': 'fixture://test'})
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


def test_temporal_runs_isolated_semgrep_and_reports_gaps():
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
    from mission_orchestration.workflow import RepositoryAssessment

    async def check(db, store):
        client = await Client.connect(address)
        queue = 'havosec-fixture-' + uuid4().hex
        dispatcher = MissionDispatcher(store, client, queue)
        activities = MissionActivities(store)
        async with Worker(client, task_queue=queue, workflows=[RepositoryAssessment], activities=[
            activities.acquire_mission_slot, activities.project_mission_progress, activities.run_mission_fixture,
        ]):
            async def run(snapshot, expected):
                ref = await seed_mission(db, str(ObjectId()))
                await db.missions.update_one(store.mission_query(ref), {'$set': {
                    'mission_type': FIXTURE_SCAN_MISSION, 'fixture_commit': snapshot,
                }})
                assert await dispatcher.dispatch_one()
                assert await asyncio.wait_for(client.get_workflow_handle(ref.workflow_id).result(), 100) == expected
                return (await store.get_mission(ref))['assessment_report']

            report = await run(commit, 'completed')
            assert report['status'] == 'complete'
            assert report['commit_sha'] == commit and report['scanner_version'] == SCANNER_VERSION
            assert len(report['rules_sha256']) == 64
            assert report['coverage']['scanned'] == ['app.py', 'clean.py']
            assert not report['gaps']
            assert report['observations']
            assert all(item['path'] == 'app.py' and len(item['evidence_sha256']) == 64
                       for item in report['observations'])
            assert any(item['rule_id'].endswith('havosec.python.eval') for item in report['observations'])

            report = await run('0' * 40, 'partial')
            assert report['status'] == 'incomplete' and report['gaps'] and not report['observations']

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
