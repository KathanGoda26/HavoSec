from fastapi import APIRouter, Depends, Query
from core.database import get_database
from core.domain_api import domain_operation, domain_scope
from models.assets import (AssetCreate, AssetUpdate, AssetResponse, AssetPage, AssetStatus,
                           GitHubAssetLinkRequest)
from repositories.project_resources import ProjectResourceRepository
from repositories.github_integrations import GitHubIntegrationRepository
from routes.projects import project_service, manage_projects
from services.project_resources import AssetService

router = APIRouter()


def asset_service(db=Depends(get_database), projects=Depends(project_service)):
    github = (GitHubIntegrationRepository(db)
              if all(getattr(db, name, None) is not None for name in
                     ('github_integrations', 'github_repositories', 'github_connection_states'))
              else None)
    return AssetService(ProjectResourceRepository(db, db.assets), projects,
                        github)


@router.get('', response_model=AssetPage)
async def list_assets(limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0, le=100000),
                      project_id: str | None = None, status: AssetStatus | None = None,
                      scope=Depends(domain_scope), service=Depends(asset_service)):
    return await domain_operation(service.list(scope, limit, offset, project_id, status))


@router.post('', response_model=AssetResponse, status_code=201)
async def create_asset(payload: AssetCreate, user=Depends(manage_projects),
                       scope=Depends(domain_scope), service=Depends(asset_service)):
    return await domain_operation(service.create(scope, user['id'], payload))


@router.get('/{asset_id}', response_model=AssetResponse)
async def get_asset(asset_id: str, scope=Depends(domain_scope), service=Depends(asset_service)):
    return await domain_operation(service.get(scope, asset_id))


@router.patch('/{asset_id}', response_model=AssetResponse)
async def update_asset(asset_id: str, payload: AssetUpdate, user=Depends(manage_projects),
                       scope=Depends(domain_scope), service=Depends(asset_service)):
    return await domain_operation(service.update(scope, asset_id, user['id'], payload))


@router.delete('/{asset_id}', response_model=AssetResponse)
async def archive_asset(asset_id: str, user=Depends(manage_projects),
                        scope=Depends(domain_scope), service=Depends(asset_service)):
    return await domain_operation(service.update(scope, asset_id, user['id']))


@router.put('/{asset_id}/github-repository', response_model=AssetResponse)
async def link_github_repository(asset_id: str, payload: GitHubAssetLinkRequest,
                                 user=Depends(manage_projects), scope=Depends(domain_scope),
                                 service=Depends(asset_service)):
    return await domain_operation(service.link_github_repository(
        scope, asset_id, user['id'], payload.repository_id
    ))
