from datetime import datetime
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field, model_validator


class ProjectStatus(str, Enum):
    ACTIVE = 'active'
    ARCHIVED = 'archived'


class ProjectCreate(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default='', max_length=4000)


class ProjectUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=4000)

    @model_validator(mode='after')
    def require_changes(self):
        if not self.model_fields_set or any(getattr(self, key) is None for key in self.model_fields_set):
            raise ValueError('Provide at least one non-null field to update')
        return self


class ProjectResponse(BaseModel):
    id: str
    organization_id: str
    name: str
    description: str
    status: ProjectStatus
    created_by: str
    created_at: datetime
    updated_at: datetime


class ProjectPage(BaseModel):
    items: list[ProjectResponse]
    total: int
    limit: int
    offset: int
