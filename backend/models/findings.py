"""Finding record contract for trusted future ingestion; no HTTP creation schema."""
import json
from datetime import datetime
from enum import Enum
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, JsonValue, field_validator


class Severity(str, Enum):
    CRITICAL = 'critical'
    HIGH = 'high'
    MEDIUM = 'medium'
    LOW = 'low'
    INFO = 'info'


class FindingStatus(str, Enum):
    NEW = 'new'
    TRIAGED = 'triaged'
    CONFIRMED = 'confirmed'
    REMEDIATING = 'remediating'
    RESOLVED = 'resolved'


class FindingUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    status: FindingStatus


class ValidationStatus(str, Enum):
    CONFIRMED = 'confirmed'
    LIKELY = 'likely'
    NEEDS_REVIEW = 'needs_review'
    REJECTED = 'rejected'


class ValidationResult(BaseModel):
    model_config = ConfigDict(extra='forbid')
    finding_id: str = Field(pattern=r'^[a-fA-F0-9]{24}$')
    security_run_id: str | None = Field(default=None, pattern=r'^[a-fA-F0-9]{24}$')
    status: ValidationStatus
    confidence: float = Field(ge=0, le=1, allow_inf_nan=False)
    reasoning_summary: str = Field(min_length=1, max_length=2000)
    evidence_summary: str = Field(min_length=1, max_length=2000)
    supporting_factors: list[str] = Field(default_factory=list, max_length=20)
    uncertainties: list[str] = Field(default_factory=list, max_length=20)
    validated_at: datetime
    validation_method: Literal['deterministic', 'agent_assisted']
    requested_by: str = Field(min_length=1, max_length=200)

    @field_validator('supporting_factors', 'uncertainties')
    @classmethod
    def bounded_summaries(cls, value):
        if any(not item or len(item) > 500 for item in value):
            raise ValueError('Validation factor exceeds its allowed size')
        return value


class FindingResponse(BaseModel):
    id: str
    organization_id: str
    project_id: str
    asset_id: str | None = None
    security_run_id: str | None = None
    security_run_ids: list[str] = Field(default_factory=list, max_length=1000)
    title: str = Field(min_length=1, max_length=300)
    description: str = Field(default='', max_length=16000)
    category: str | None = Field(default=None, max_length=200)
    severity: Severity
    cvss: float | None = Field(default=None, ge=0, le=10, allow_inf_nan=False)
    confidence: float | None = Field(default=None, ge=0, le=1, allow_inf_nan=False)
    status: FindingStatus = FindingStatus.NEW
    affected_component: str | None = Field(default=None, max_length=2000)
    location: str | None = Field(default=None, max_length=4000)
    evidence: dict[str, JsonValue] = Field(default_factory=dict)
    references: list[str] = Field(default_factory=list, max_length=100)
    source: str = Field(min_length=1, max_length=200)
    source_metadata: dict[str, JsonValue] = Field(default_factory=dict)
    first_detected_at: datetime
    last_detected_at: datetime
    created_at: datetime
    updated_at: datetime
    fingerprint: str | None = Field(default=None, pattern=r'^[a-f0-9]{64}$')
    last_security_run_id: str | None = None
    validation: ValidationResult | None = None

    @field_validator('evidence', 'source_metadata')
    @classmethod
    def bounded_json(cls, value):
        if len(json.dumps(value, allow_nan=False).encode('utf-8')) > 65536:
            raise ValueError('Evidence/source metadata exceeds 64 KiB')
        return value

    @field_validator('references')
    @classmethod
    def bounded_references(cls, value):
        if any(len(item) > 2048 for item in value):
            raise ValueError('Reference exceeds 2048 characters')
        return value


class FindingPage(BaseModel):
    items: list[FindingResponse]
    total: int
    limit: int
    offset: int
