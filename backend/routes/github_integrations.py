from fastapi import APIRouter, Depends, Query

from core.database import get_database
from core.domain_api import domain_operation, domain_scope
from integrations.github.config import GitHubAppSettings, GitHubConfigurationError
from models.github_integrations import (GitHubConnectResponse, GitHubIntegrationResponse,
                                        GitHubRepositoryAuthorizationUpdate, GitHubRepositoryPage,
                                        GitHubRepositoryResponse)
from repositories.github_integrations import GitHubIntegrationRepository
from utils.auth import require_roles
from utils.roles import UserRole
from services.github_integrations import GitHubIntegrationService


router = APIRouter()
manage_integrations = require_roles(UserRole.ADMIN, UserRole.SUPERADMIN)


def github_service(db=Depends(get_database)):
    try:
        settings = GitHubAppSettings.from_environment()
    except GitHubConfigurationError as exc:
        raise RuntimeError("GitHub integration is not configured") from exc
    return GitHubIntegrationService(GitHubIntegrationRepository(db), settings)


@router.get("", response_model=GitHubIntegrationResponse | None)
async def get_integration(scope=Depends(domain_scope), service=Depends(github_service)):
    return await domain_operation(service.get(scope))


@router.post("/connect", response_model=GitHubConnectResponse)
async def connect_github(user=Depends(manage_integrations), scope=Depends(domain_scope),
                         service=Depends(github_service)):
    return await domain_operation(service.begin_connection(scope, user["id"]))


@router.get("/callback", response_model=GitHubIntegrationResponse)
async def github_callback(state: str = Query(min_length=32, max_length=256),
                          installation_id: int = Query(gt=0),
                          service=Depends(github_service)):
    return await domain_operation(service.complete_connection(state, installation_id))


@router.get("/repositories", response_model=GitHubRepositoryPage)
async def list_repositories(scope=Depends(domain_scope), service=Depends(github_service)):
    items = await service.repository.list_repositories(scope)
    from core.domain_api import document_view
    return {"items": [document_view(item) for item in items], "total": len(items)}


@router.post("/repositories/refresh", response_model=GitHubRepositoryPage)
async def refresh_repositories(user=Depends(manage_integrations), scope=Depends(domain_scope),
                               service=Depends(github_service)):
    return await domain_operation(service.sync_repositories(scope))


@router.patch("/repositories/{repository_id}", response_model=GitHubRepositoryResponse)
async def authorize_repository(repository_id: int, payload: GitHubRepositoryAuthorizationUpdate,
                               user=Depends(manage_integrations), scope=Depends(domain_scope),
                               service=Depends(github_service)):
    return await domain_operation(service.authorize_repository(scope, repository_id, payload.authorized))
