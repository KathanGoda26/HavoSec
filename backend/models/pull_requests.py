from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field
from models.remediations import VerificationResult


class PullRequestStatus(str, Enum):
    QUEUED = 'queued'
    CREATING = 'creating'
    OPEN = 'open'
    CLOSED = 'closed'
    MERGED = 'merged'
    FAILED = 'failed'


class PullRequestResponse(BaseModel):
    id: str
    organization_id: str
    project_id: str
    asset_id: str
    finding_id: str
    remediation_id: str
    provider: str = Field(pattern=r'^github$')
    repository_id: int
    repository_full_name: str
    installation_id: int
    branch: str
    base_branch: str
    expected_source_commit: str = Field(pattern=r'^[a-f0-9]{40}$')
    verified_patch_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    commit_sha: str | None = Field(default=None, pattern=r'^[a-f0-9]{40}$')
    pr_number: int | None = None
    pr_url: str | None = None
    status: PullRequestStatus
    checks_status: str
    checks: dict[str, str] = Field(default_factory=dict)
    reverification_status: str
    reverification_result: VerificationResult | None = None
    readiness_status: str = 'waiting'
    error: str | None = None
    requested_by: str
    created_at: datetime
    updated_at: datetime
