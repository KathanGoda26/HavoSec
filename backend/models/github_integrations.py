"""Organization-scoped GitHub installation and repository authorization models."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class GitHubConnectionStatus(str, Enum):
    ACTIVE = "active"
    NEEDS_ATTENTION = "needs_attention"
    DISCONNECTED = "disconnected"


class GitHubIntegrationResponse(BaseModel):
    id: str
    organization_id: str
    installation_id: int
    account_id: int
    account_login: str
    account_type: str
    status: GitHubConnectionStatus
    permissions: dict[str, str]
    repository_selection: str
    last_synced_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class GitHubRepositoryResponse(BaseModel):
    id: str
    organization_id: str
    integration_id: str
    repository_id: int
    full_name: str
    default_branch: str
    private: bool
    authorized: bool
    connection_status: GitHubConnectionStatus
    last_synced_at: datetime
    created_at: datetime
    updated_at: datetime


class GitHubRepositoryAuthorizationUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    authorized: bool


class GitHubRepositorySyncItem(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    repository_id: int = Field(gt=0)
    full_name: str = Field(min_length=3, max_length=255, pattern=r"^[^/\s]+/[^/\s]+$")
    default_branch: str = Field(min_length=1, max_length=255)
    private: bool


class GitHubConnectResponse(BaseModel):
    installation_url: str
    expires_at: datetime


class GitHubRepositoryPage(BaseModel):
    items: list[GitHubRepositoryResponse]
    total: int
