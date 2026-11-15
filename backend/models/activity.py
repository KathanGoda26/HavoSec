from datetime import datetime
from enum import Enum
from pydantic import BaseModel


class ActivityType(str, Enum):
    PROJECT_CREATED = 'project_created'
    PROJECT_UPDATED = 'project_updated'
    PROJECT_ARCHIVED = 'project_archived'
    ASSET_CREATED = 'asset_created'
    ASSET_UPDATED = 'asset_updated'
    ASSET_ARCHIVED = 'asset_archived'
    SECURITY_RUN_CREATED = 'security_run_created'
    SECURITY_RUN_CANCELLED = 'security_run_cancelled'
    SECURITY_RUN_STARTED = 'security_run_started'
    SECURITY_RUN_COMPLETED = 'security_run_completed'
    SECURITY_RUN_FAILED = 'security_run_failed'
    FINDINGS_CREATED = 'findings_created'
    FINDING_CREATED = 'finding_created'
    FINDING_UPDATED = 'finding_updated'
    FINDING_VALIDATED = 'finding_validated'
    REMEDIATION_CREATED = 'remediation_created'
    REMEDIATION_UPDATED = 'remediation_updated'
    REMEDIATION_VERIFICATION_QUEUED = 'remediation_verification_queued'
    REMEDIATION_VERIFICATION_STARTED = 'remediation_verification_started'
    REMEDIATION_VERIFIED = 'remediation_verified'
    REMEDIATION_FAILED = 'remediation_failed'
    PULL_REQUEST_CREATION_STARTED = 'pull_request_creation_started'
    PULL_REQUEST_CREATED = 'pull_request_created'
    PULL_REQUEST_FAILED = 'pull_request_failed'
    PULL_REQUEST_STATUS_UPDATED = 'pull_request_status_updated'
    PULL_REQUEST_CHECKS_UPDATED = 'pull_request_checks_updated'
    REMEDIATION_REVERIFICATION_STARTED = 'remediation_reverification_started'
    REMEDIATION_REVERIFICATION_PASSED = 'remediation_reverification_passed'
    REMEDIATION_REVERIFICATION_FAILED = 'remediation_reverification_failed'


class ActivityResponse(BaseModel):
    id: str
    organization_id: str
    project_id: str
    actor_id: str
    event_type: str
    entity_type: str
    entity_id: str
    message: str
    metadata: dict
    created_at: datetime


class ActivityPage(BaseModel):
    items: list[ActivityResponse]
    total: int
    limit: int
    offset: int
