import asyncio
import os
from dataclasses import replace
from uuid import uuid4

import pytest
from bson import ObjectId

from core.database import DatabaseSettings, create_database_client
from core.domain_indexes import ensure_domain_indexes
from core.ownership import OrganizationScope
from mission_orchestration.plan import ASSESSMENT_V1, MissionRef, ProgressEvent, TaskResult, validate_plan
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
    now = utc_now()
    await db.missions.insert_one({
        '_id': ObjectId(mission.mission_id), 'organization_id': organization_id,
        'request_key': uuid4().hex, 'status': 'queued', 'created_at': now, 'updated_at': now,
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
    from mission_orchestration.plan import FixtureAttempt, TaskResult
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
        activities = MissionActivities(store)

        @activity.defn(name='run_mission_fixture')
        async def inject_failure(request: FixtureAttempt) -> TaskResult:
            attempt = activity.info().attempt
            if request.mission == recovered and request.task_id == 'assess' and attempt == 1:
                interrupted.set()
                raise ApplicationError('fixture failed on its first attempt')
            if request.mission == cancelled:
                assert request.task_id == 'prepare'
                started_for_cancellation.set()
                while True:
                    activity.heartbeat()
                    await asyncio.sleep(0.2)
            if request.mission == failed:
                attempts.append(attempt)
                raise ApplicationError('fixture fails on every attempt')
            return await activities.run_mission_fixture(request)

        def worker():
            return Worker(client, task_queue=queue, workflows=[RepositoryAssessment], activities=[
                activities.acquire_mission_slot, activities.project_mission_progress, inject_failure,
            ])

        async with worker():
            await asyncio.wait_for(interrupted.wait(), timeout=25)
        async with worker():
            assert await asyncio.wait_for(handle.result(), timeout=30) == 'completed'
            progress = (await store.get_mission(recovered))['orchestration']
            assert [task['attempt'] for task in progress['completed']] == [1, 2, 1]
            assert await dispatcher.dispatch_one()
            assert await dispatcher.dispatch_one()
            await asyncio.wait_for(started_for_cancellation.wait(), timeout=25)
            await MissionRepository(db).request_cancellation(
                OrganizationScope(organization), await store.get_mission(cancelled))
            assert await dispatcher.dispatch_one()
            assert await asyncio.wait_for(
                client.get_workflow_handle(cancelled.workflow_id).result(), timeout=25) == 'cancelled'
            assert (await store.get_mission(cancelled))['orchestration']['completed'] == []
            assert await asyncio.wait_for(
                client.get_workflow_handle(failed.workflow_id).result(), timeout=40) == 'failed'
            assert attempts == [1, 2, 3]

    asyncio.run(with_test_database(check))
