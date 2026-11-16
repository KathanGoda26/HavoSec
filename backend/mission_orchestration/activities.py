import asyncio

from temporalio import activity
from temporalio.exceptions import ApplicationError

from mission_orchestration.governance import ATTEMPT_BUSY, FixtureGateway, FixtureRejected
from mission_orchestration.plan import (
    ASSESSMENT_V1, FixtureAttempt, MissionRef, ProgressEvent, ProgressState, TaskResult,
)


class MissionActivities:
    def __init__(self, store):
        self.store = store
        self.gateway = FixtureGateway(store.db)
        self.tasks = {task.id: task for task in ASSESSMENT_V1}

    @activity.defn
    async def project_mission_progress(self, event: ProgressEvent) -> ProgressState:
        return await self.store.project(event)

    @activity.defn
    async def acquire_mission_slot(self, mission: MissionRef) -> ProgressState:
        return await self.store.acquire_slot(mission)

    @activity.defn
    async def run_mission_fixture(self, request: FixtureAttempt) -> TaskResult:
        task = self.tasks.get(request.task_id)
        if task is None:
            raise ApplicationError('Unknown fixture task', non_retryable=True)
        info = activity.info()
        if info.workflow_id != request.mission.workflow_id:
            raise ApplicationError('Unexpected fixture workflow', non_retryable=True)
        attempt_id = f'{info.workflow_run_id}/{info.activity_id}/{info.attempt}'
        try:
            cached = await self.gateway.begin(request, attempt_id, info.attempt)
            if cached is not None:
                return cached
            try:
                result = await self.execute_fixture(request, task, info.attempt, attempt_id)
                await self.gateway.finish(request, attempt_id, 'completed', result)
            except asyncio.CancelledError:
                await self.gateway.finish(request, attempt_id, 'interrupted')
                raise
            except Exception:
                await self.gateway.finish(request, attempt_id, 'failed')
                raise
            return result
        except FixtureRejected as exc:
            raise ApplicationError('Fixture was not admitted', type=exc.code,
                                   non_retryable=exc.code != ATTEMPT_BUSY) from exc

    async def execute_fixture(self, request, task, attempt, attempt_id):
        # The only adapter has fixed outputs and performs no filesystem, subprocess or network work.
        for _ in range(5):
            mission = await self.store.get_mission(request.mission)
            if not self.gateway.ready(mission, request.mission, task.id):
                raise ApplicationError('Mission cannot run this task', non_retryable=True)
            activity.heartbeat()
            await asyncio.sleep(0.2)
        return TaskResult(task.id, task.output, attempt, attempt_id)
