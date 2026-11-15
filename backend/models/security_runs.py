from datetime import datetime
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field, field_validator


class RunType(str, Enum):
    QUICK = 'quick'
    STANDARD = 'standard'
    FULL = 'full'


class RunStatus(str, Enum):
    QUEUED = 'queued'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'


class SecurityRunCreate(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    project_id: str = Field(pattern=r'^[a-fA-F0-9]{24}$')
    asset_ids: list[str] = Field(min_length=1, max_length=100)
    type: RunType = RunType.STANDARD

    @field_validator('asset_ids')
    @classmethod
    def valid_unique_ids(cls, values):
        from bson import ObjectId
        if any(not ObjectId.is_valid(value) for value in values):
            raise ValueError('Invalid asset ID')
        canonical = [str(ObjectId(value)) for value in values]
        if len(set(canonical)) != len(canonical):
            raise ValueError('Duplicate assets are not permitted')
        return canonical


class SecurityRunResponse(BaseModel):
    id: str
    organization_id: str
    project_id: str
    asset_ids: list[str]
    type: RunType
    status: RunStatus
    requested_by: str
    started_at: datetime | None
    completed_at: datetime | None
    progress: int
    summary: dict | None
    error: str | None
    created_at: datetime
    updated_at: datetime
    commit_sha: str | None = None
    scanner: str | None = None
    scanner_version: str | None = None
    analysis_mode: str | None = None


class SecurityRunPage(BaseModel):
    items: list[SecurityRunResponse]
    total: int
    limit: int
    offset: int
