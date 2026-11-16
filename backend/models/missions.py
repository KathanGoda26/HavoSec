from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from mission_orchestration.plan import FIXTURE_SCAN_MISSION, GITHUB_SCAN_MISSION


class MissionStatus(str, Enum):
    QUEUED = 'queued'
    RUNNING = 'running'
    AWAITING_APPROVAL = 'awaiting_approval'
    COMPLETED = 'completed'
    PARTIAL = 'partial'
    FAILED = 'failed'
    CANCELLED = 'cancelled'
    NEEDS_REVIEW = 'needs_review'


class MissionCreate(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)

    project_id: str = Field(pattern=r'^[0-9a-fA-F]{24}$')
    asset_id: str = Field(pattern=r'^[0-9a-fA-F]{24}$')
    objective: str = Field(min_length=1, max_length=1000)
    mission_type: Literal['repository_assessment', FIXTURE_SCAN_MISSION, GITHUB_SCAN_MISSION] = 'repository_assessment'


class MissionTaskResult(BaseModel):
    task_id: str
    output: str
    attempt: int
    attempt_id: str


class MissionProgress(BaseModel):
    version: int
    total_tasks: int
    current_task: str | None
    completed: list[MissionTaskResult]


class MissionResponse(BaseModel):
    id: str
    organization_id: str
    project_id: str
    asset_id: str
    objective: str
    mission_type: str
    requested_by: str
    status: MissionStatus
    created_at: datetime
    updated_at: datetime
    cancel_requested_at: datetime | None = None
    orchestration: MissionProgress | None = None
    source_commit: str | None = None


class MissionPage(BaseModel):
    items: list[MissionResponse]
    total: int
    limit: int
    offset: int


class FixtureApprovalRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')

    action_digest: str = Field(pattern=r'^[0-9a-f]{64}$')
