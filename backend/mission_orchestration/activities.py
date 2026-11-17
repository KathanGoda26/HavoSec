import asyncio

from temporalio import activity
from temporalio.exceptions import ApplicationError

from mission_orchestration.fixture_assessment import assess_fixture
from mission_orchestration.fixture_remediation import verify_fixture_remediation
from mission_orchestration.github_assessment import assess_github_repository
from mission_orchestration.governance import ATTEMPT_BUSY, FixtureGateway, FixtureRejected
from mission_orchestration.plan import (
    ASSESSMENT_V1, FIXTURE_REMEDIATION_MISSION, FIXTURE_SCAN_MISSION, GITHUB_SCAN_MISSION, INCOMPLETE_SCAN,
    UNVERIFIED_PATCH, FixtureAttempt, MissionRef, ProgressEvent, ProgressState, TaskResult,
)


class MissionActivities:
    def __init__(self, store, github_client_factory=None):
        self.store = store
        self.github_client_factory = github_client_factory
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
                report = None
                verification = None
                mission_type = request.mission.mission_type
                if mission_type in (FIXTURE_SCAN_MISSION, FIXTURE_REMEDIATION_MISSION,
                                    GITHUB_SCAN_MISSION) and task.id == 'assess':
                    operation = self.assess_github if mission_type == GITHUB_SCAN_MISSION else assess_fixture
                    report = await self.run_with_heartbeat(request, attempt_id, operation)
                    output = task.output if report['status'] == 'complete' else INCOMPLETE_SCAN
                    result = TaskResult(task.id, output, info.attempt, attempt_id)
                elif mission_type == FIXTURE_REMEDIATION_MISSION and task.id == 'summarize':
                    verification = await self.run_with_heartbeat(request, attempt_id, verify_fixture_remediation)
                    output = 'fixture_patch_verified' if verification['status'] == 'verified' else UNVERIFIED_PATCH
                    result = TaskResult(task.id, output, info.attempt, attempt_id)
                else:
                    result = await self.execute_fixture(request, task, info.attempt, attempt_id)
                await self.gateway.finish(request, attempt_id, 'completed', result, report, verification=verification)
            except asyncio.CancelledError:
                await self.gateway.finish(request, attempt_id, 'interrupted')
                raise
            except Exception:
                await self.gateway.finish(request, attempt_id, 'failed')
                raise
            return result
        except FixtureRejected as exc:
            raise ApplicationError('Mission action was not admitted', type=exc.code,
                                   non_retryable=exc.code != ATTEMPT_BUSY) from exc

    async def execute_fixture(self, request, task, attempt, attempt_id):
        # Simulation and orchestration-only steps have fixed outputs.
        for _ in range(5):
            mission = await self.store.get_mission(request.mission)
            if not self.gateway.ready(mission, request.mission, task.id):
                raise ApplicationError('Mission cannot run this task', non_retryable=True)
            activity.heartbeat()
            await asyncio.sleep(0.2)
        return TaskResult(task.id, task.output, attempt, attempt_id)

    async def assess_github(self, mission):
        return await assess_github_repository(mission, self.github_client_factory)

    async def run_with_heartbeat(self, request, attempt_id, operation):
        mission = await self.store.get_mission(request.mission)
        await self.gateway.keep_alive(request, attempt_id)
        activity.heartbeat()
        scan = asyncio.create_task(operation(mission))
        try:
            while not scan.done():
                await asyncio.wait({scan}, timeout=0.5)
                if not scan.done():
                    await self.gateway.keep_alive(request, attempt_id)
                    activity.heartbeat()
            return await scan
        finally:
            if not scan.done():
                scan.cancel()
                await asyncio.gather(scan, return_exceptions=True)
