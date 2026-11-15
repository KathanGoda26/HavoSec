import asyncio
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy
from temporalio.exceptions import ActivityError

from mission_orchestration.plan import (
    ASSESSMENT_V1, CANCEL_SIGNAL, TERMINAL_STATUSES, WORKFLOW_TYPE, FixtureAttempt, MissionRef, ProgressEvent,
    ProgressState, TaskResult, validate_plan,
)


PROJECTION_RETRY = RetryPolicy(
    maximum_interval=timedelta(seconds=30), non_retryable_error_types=['ValueError'],
)


@workflow.defn(name=WORKFLOW_TYPE)
class RepositoryAssessment:
    def __init__(self):
        self.cancel_requested = False
        self.active_task = None
        self.version = 0
        self.completed = []

    @workflow.signal(name=CANCEL_SIGNAL)
    def request_cancellation(self):
        if not self.cancel_requested:
            self.cancel_requested = True
            if self.active_task is not None:
                self.active_task.cancel()

    @workflow.run
    async def run(self, mission: MissionRef) -> str:
        self.mission = mission
        plan = validate_plan(ASSESSMENT_V1)
        self.total_tasks = len(plan)
        initial = await self.project('queued')
        if initial.status in TERMINAL_STATUSES:
            return initial.status
        try:
            await self.wait_for_slot()
            status = await self.run_tasks(plan)
        except asyncio.CancelledError:
            self.cancel_requested = True
            status = 'cancelled'
        if self.cancel_requested:
            status = 'cancelled'
        return (await self.project(status)).status

    async def wait_for_slot(self):
        delay = 1
        while not self.cancel_requested:
            state = await workflow.execute_activity(
                'acquire_mission_slot', self.mission, result_type=ProgressState,
                start_to_close_timeout=timedelta(seconds=15), retry_policy=PROJECTION_RETRY,
            )
            self.cancel_requested |= state.cancellation_requested
            if state.acquired_slot or self.cancel_requested:
                return
            try:
                await workflow.wait_condition(lambda: self.cancel_requested, timeout=delay)
            except TimeoutError:
                delay = min(delay * 2, 30)

    async def run_tasks(self, plan):
        for task in plan:
            if self.cancel_requested:
                break
            await self.project('running', task.id)
            if self.cancel_requested:
                break
            self.active_task = workflow.start_activity(
                'run_mission_fixture', FixtureAttempt(self.mission, task.id), result_type=TaskResult,
                activity_id=task.id, start_to_close_timeout=timedelta(seconds=task.deadline_seconds),
                heartbeat_timeout=timedelta(seconds=3),
                retry_policy=RetryPolicy(maximum_attempts=task.max_attempts, maximum_interval=timedelta(seconds=5)),
                cancellation_type=workflow.ActivityCancellationType.WAIT_CANCELLATION_COMPLETED,
            )
            try:
                self.completed.append(await self.active_task)
            except ActivityError:
                return 'partial' if self.completed else 'failed'
            finally:
                self.active_task = None
        return 'completed'

    async def project(self, status, current_task=None):
        self.version += 1
        handle = workflow.start_activity(
            'project_mission_progress',
            ProgressEvent(self.mission, self.version, status, self.total_tasks, current_task, list(self.completed)),
            result_type=ProgressState, start_to_close_timeout=timedelta(seconds=15), retry_policy=PROJECTION_RETRY,
        )
        try:
            state = await asyncio.shield(handle)
        except asyncio.CancelledError:
            self.cancel_requested = True
            state = await handle
        self.cancel_requested |= state.cancellation_requested
        return state
