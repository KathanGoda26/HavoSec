import asyncio

from temporalio import activity
from temporalio.exceptions import ApplicationError

from mission_orchestration.plan import (
    ASSESSMENT_V1, FixtureAttempt, MissionRef, ProgressEvent, ProgressState, TaskResult,
)


class MissionActivities:
    def __init__(self, store):
        self.store = store
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
        for _ in range(5):
            mission = await self.store.get_mission(request.mission)
            state = self.store.state(mission)
            if (state.cancellation_requested or state.status != 'running' or not state.acquired_slot
                    or mission['orchestration']['current_task'] != task.id):
                raise ApplicationError('Mission cannot run this task', non_retryable=True)
            activity.heartbeat()
            await asyncio.sleep(0.2)
        info = activity.info()
        return TaskResult(task.id, task.output, info.attempt,
                          f'{info.workflow_run_id}/{info.activity_id}/{info.attempt}')
