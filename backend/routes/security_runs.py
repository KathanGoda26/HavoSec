from fastapi import APIRouter, Depends, Query
from core.database import get_database
from core.domain_api import domain_operation, domain_scope
from models.security_runs import SecurityRunCreate, SecurityRunResponse, SecurityRunPage, RunStatus
from repositories.project_resources import ProjectResourceRepository
from routes.projects import project_service, manage_projects
from routes.assets import asset_service
from services.project_resources import SecurityRunService

router = APIRouter()


def run_service(db=Depends(get_database), projects=Depends(project_service), assets=Depends(asset_service)):
    return SecurityRunService(ProjectResourceRepository(db, db.security_runs), projects, assets)


@router.get('', response_model=SecurityRunPage)
async def list_runs(limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0, le=100000),
                    project_id: str | None = None, status: RunStatus | None = None,
                    scope=Depends(domain_scope), service=Depends(run_service)):
    return await domain_operation(service.list(scope, limit, offset, project_id, status))


@router.post('', response_model=SecurityRunResponse, status_code=201)
async def create_run(payload: SecurityRunCreate, user=Depends(manage_projects),
                     scope=Depends(domain_scope), service=Depends(run_service)):
    return await domain_operation(service.create(scope, user['id'], payload))


@router.get('/{run_id}', response_model=SecurityRunResponse)
async def get_run(run_id: str, scope=Depends(domain_scope), service=Depends(run_service)):
    return await domain_operation(service.get(scope, run_id))


@router.patch('/{run_id}/cancel', response_model=SecurityRunResponse)
async def cancel_run(run_id: str, user=Depends(manage_projects),
                     scope=Depends(domain_scope), service=Depends(run_service)):
    return await domain_operation(service.cancel(scope, run_id, user['id']))
