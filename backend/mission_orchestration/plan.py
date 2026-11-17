from dataclasses import dataclass, field


WORKFLOW_TYPE = 'RepositoryAssessmentV1'
PLAN_VERSION = 1
APPROVAL_REQUIRED = 'FixtureApprovalRequired'
FIXTURE_SCAN_MISSION = 'fixture_repository_assessment'
FIXTURE_REMEDIATION_MISSION = 'fixture_remediation_verification'
GITHUB_SCAN_MISSION = 'github_repository_assessment'
INCOMPLETE_SCAN = 'fixture_scan_incomplete'
UNVERIFIED_PATCH = 'fixture_patch_unverified'
CANCEL_SIGNAL = 'request_cancellation'
TERMINAL_STATUSES = frozenset({'completed', 'partial', 'failed', 'cancelled', 'needs_review'})


@dataclass(frozen=True)
class MissionRef:
    organization_id: str
    mission_id: str
    mission_type: str = 'repository_assessment'

    @property
    def workflow_id(self):
        return f'mission/{self.organization_id}/{self.mission_id}'


@dataclass(frozen=True)
class TaskSpec:
    id: str
    objective: str
    inputs: tuple[str, ...]
    output: str
    dependencies: tuple[str, ...]
    capability: str
    deadline_seconds: int
    max_attempts: int


@dataclass(frozen=True)
class FixtureAttempt:
    mission: MissionRef
    task_id: str


@dataclass(frozen=True)
class TaskResult:
    task_id: str
    output: str
    attempt: int
    attempt_id: str


@dataclass(frozen=True)
class ProgressEvent:
    mission: MissionRef
    version: int
    status: str
    total_tasks: int
    current_task: str | None = None
    completed: list[TaskResult] = field(default_factory=list)


@dataclass(frozen=True)
class ProgressState:
    status: str
    cancellation_requested: bool = False
    acquired_slot: bool = False


ASSESSMENT_V1 = (
    TaskSpec('prepare', 'Prepare the fixture repository scope', ('mission',), 'fixture_scope',
             (), 'fixture', 15, 3),
    TaskSpec('assess', 'Assess the fixture repository', ('fixture_scope',), 'fixture_observations',
             ('prepare',), 'fixture', 15, 3),
    TaskSpec('summarize', 'Summarize the fixture observations', ('fixture_observations',), 'fixture_summary',
             ('assess',), 'fixture', 15, 3),
)


def validate_plan(plan):
    by_id = {task.id: task for task in plan}
    outputs = {task.output for task in plan}
    if not plan or len(by_id) != len(plan) or len(outputs) != len(plan) or 'mission' in outputs:
        raise ValueError('A plan needs unique tasks and output references')
    for task in plan:
        if (not task.id or not task.objective or not task.output or task.capability != 'fixture'
                or not 1 <= task.deadline_seconds <= 60 or not 1 <= task.max_attempts <= 5):
            raise ValueError(f'Invalid fixture task {task.id}')
        if not set(task.dependencies).issubset(by_id) or len(set(task.dependencies)) != len(task.dependencies):
            raise ValueError(f'Invalid dependencies for {task.id}')
        allowed_inputs = {'mission'} | {by_id[parent].output for parent in task.dependencies}
        if not task.inputs or not set(task.inputs).issubset(allowed_inputs):
            raise ValueError(f'Invalid input references for {task.id}')

    ordered = []
    completed = set()
    while len(ordered) < len(plan):
        ready = [task for task in plan if task.id not in completed and set(task.dependencies) <= completed]
        if not ready:
            raise ValueError('Task graph contains a cycle')
        ordered.extend(ready)
        completed.update(task.id for task in ready)
    return tuple(ordered)
