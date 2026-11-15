from datetime import datetime
from enum import Enum
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class RemediationProposal(BaseModel):
    model_config = ConfigDict(extra='forbid')
    summary: str = Field(min_length=1, max_length=2000)
    explanation: str = Field(min_length=1, max_length=4000)
    affected_files: list[str] = Field(min_length=1, max_length=50)
    patch: str = Field(min_length=1, max_length=1_000_000)
    expected_security_effect: str = Field(min_length=1, max_length=4000)
    potential_side_effects: list[str] = Field(default_factory=list, max_length=20)
    recommended_tests: list[str] = Field(default_factory=list, max_length=20)
    confidence: float = Field(ge=0, le=1, allow_inf_nan=False)

    @field_validator('affected_files')
    @classmethod
    def unique_files(cls, value):
        if len(value) != len(set(value)):
            raise ValueError('Affected files must be unique')
        return value

    @field_validator('potential_side_effects', 'recommended_tests')
    @classmethod
    def bounded_items(cls, value):
        if any(not item or len(item) > 1000 for item in value):
            raise ValueError('Proposal list item exceeds its allowed size')
        return value


class RemediationStatus(str, Enum):
    PENDING = 'pending'
    IN_PROGRESS = 'in_progress'
    AWAITING_APPROVAL = 'awaiting_approval'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    RESOLVED = 'resolved'
    FAILED = 'failed'


class VerificationStatus(str, Enum):
    NOT_STARTED = 'not_started'
    QUEUED = 'queued'
    TESTING = 'testing'
    VERIFIED = 'verified'
    FAILED = 'failed'
    INCONCLUSIVE = 'inconclusive'


class VerificationResult(BaseModel):
    model_config = ConfigDict(extra='forbid')
    remediation_id: str = Field(pattern=r'^[a-fA-F0-9]{24}$')
    status: Literal['verified', 'failed', 'inconclusive']
    original_finding_present: bool | None
    new_findings_count: int = Field(ge=0, le=2000)
    new_equal_or_higher_findings_count: int = Field(ge=0, le=2000)
    before_finding_count: int = Field(ge=0, le=2000)
    after_finding_count: int = Field(ge=0, le=2000)
    before_severity_counts: dict[str, int]
    after_severity_counts: dict[str, int]
    scanner: str = Field(min_length=1, max_length=100)
    scanner_version: str = Field(min_length=1, max_length=100)
    summary: str = Field(min_length=1, max_length=2000)
    verified_at: datetime


class RemediationCreate(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    finding_id: str = Field(pattern=r'^[a-fA-F0-9]{24}$')
    summary: str = Field(min_length=1, max_length=2000)
    recommendation: str = Field(default='', max_length=16000)
    proposed_fix: str = Field(default='', max_length=32000)
    acknowledge_likely: bool = False


class RemediationUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    summary: str | None = Field(default=None, min_length=1, max_length=2000)
    recommendation: str | None = Field(default=None, max_length=16000)
    proposed_fix: str | None = Field(default=None, max_length=32000)
    status: RemediationStatus | None = None

    @model_validator(mode='after')
    def nonempty(self):
        if not self.model_fields_set or any(getattr(self, key) is None for key in self.model_fields_set):
            raise ValueError('Provide at least one non-null field')
        return self


class RemediationResponse(BaseModel):
    id: str
    organization_id: str
    project_id: str
    finding_id: str
    status: RemediationStatus
    summary: str
    recommendation: str
    proposed_fix: str
    created_by: str
    approved_by: str | None
    created_at: datetime
    updated_at: datetime
    asset_id: str | None = None
    source_security_run_id: str | None = None
    source_commit: str | None = Field(default=None, pattern=r'^[a-f0-9]{40}$')
    verified_source_commit: str | None = Field(default=None, pattern=r'^[a-f0-9]{40}$')
    verified_patch_sha256: str | None = Field(default=None, pattern=r'^[a-f0-9]{64}$')
    verified_affected_files: list[str] = Field(default_factory=list, max_length=50)
    verified_at: datetime | None = None
    source_integrity_status: Literal['verified', 'stale', 'unknown'] | None = None
    proposal: RemediationProposal | None = None
    patch_format: str | None = None
    validation_status: str | None = None
    verification_status: VerificationStatus = VerificationStatus.NOT_STARTED
    verification_result: VerificationResult | None = None
    verification_attempts: int = Field(default=0, ge=0, le=2)
    proposal_agent_metadata: dict = Field(default_factory=dict)


class PullRequestEligibility(BaseModel):
    eligible: bool
    reasons: list[str]
    source_integrity_status: Literal['verified', 'stale', 'unknown']
    requires_remote_source_check: bool


class RemediationPage(BaseModel):
    items: list[RemediationResponse]
    total: int
    limit: int
    offset: int
