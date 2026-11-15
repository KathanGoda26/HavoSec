import json
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field, JsonValue, field_validator, model_validator


class AssetType(str, Enum):
    REPOSITORY = 'repository'
    APPLICATION = 'application'
    DOMAIN = 'domain'
    API = 'api'
    HOST = 'host'


class AssetStatus(str, Enum):
    ACTIVE = 'active'
    ARCHIVED = 'archived'


class AssetUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    name: str | None = Field(default=None, min_length=1, max_length=200)
    target: str | None = Field(default=None, min_length=1, max_length=2048)
    metadata: dict[str, JsonValue] | None = None

    @field_validator('metadata')
    @classmethod
    def bounded_metadata(cls, value):
        if value is not None:
            try:
                encoded = json.dumps(value, allow_nan=False).encode('utf-8')
            except (ValueError, TypeError) as exc:
                raise ValueError('Metadata must be valid JSON') from exc
            if len(encoded) > 16384:
                raise ValueError('Metadata exceeds 16 KiB')
        return value

    @model_validator(mode='after')
    def require_changes(self):
        if not self.model_fields_set or any(getattr(self, key) is None for key in self.model_fields_set):
            raise ValueError('Provide non-null fields')
        return self


class AssetCreate(AssetUpdate):
    project_id: str = Field(pattern=r'^[a-fA-F0-9]{24}$')
    name: str = Field(min_length=1, max_length=200)
    type: AssetType
    target: str = Field(min_length=1, max_length=2048)
    metadata: dict[str, JsonValue] = Field(default_factory=dict)


class SourceControlLink(BaseModel):
    provider: str = Field(pattern=r'^github$')
    integration_id: str = Field(pattern=r'^[a-fA-F0-9]{24}$')
    repository_id: int = Field(gt=0)
    repository_full_name: str
    default_branch: str
    connection_status: str


class AssetResponse(BaseModel):
    id: str
    organization_id: str
    project_id: str
    name: str
    type: AssetType
    target: str
    status: AssetStatus
    metadata: dict
    source_control: SourceControlLink | None = None
    created_at: datetime
    updated_at: datetime


class AssetPage(BaseModel):
    items: list[AssetResponse]
    total: int
    limit: int
    offset: int


class GitHubAssetLinkRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    repository_id: int = Field(gt=0)
