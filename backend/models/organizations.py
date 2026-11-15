"""Validated compatibility inputs for client-company organization APIs."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, EmailStr, model_validator


class OrganizationUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    name: str | None = Field(default=None, min_length=1, max_length=200)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=80)
    website: str | None = Field(default=None, max_length=1000)
    industry: str | None = Field(default=None, max_length=200)
    size: str | None = Field(default=None, max_length=100)
    subscription: str | dict | None = None
    services: list[str] | None = Field(default=None, max_length=100)
    securityModels: dict[str, bool] | None = None
    isActive: bool | None = None
    status: Literal['active', 'inactive'] | None = None

    @model_validator(mode='after')
    def validate_state(self):
        for name in ('name', 'email', 'isActive', 'status', 'services', 'securityModels', 'subscription'):
            if name in self.model_fields_set and getattr(self, name) is None:
                raise ValueError(f'{name} cannot be null')
        if self.status is not None and self.isActive is not None:
            if (self.status == 'active') != self.isActive:
                raise ValueError('status and isActive must agree')
        return self


class OrganizationCreate(OrganizationUpdate):
    name: str = Field(min_length=1, max_length=200)
    email: EmailStr
