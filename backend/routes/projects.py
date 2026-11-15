from fastapi import APIRouter, Depends, Query
from core.database import get_database
from core.domain_api import domain_operation, domain_scope
from models.projects import ProjectCreate, ProjectUpdate, ProjectResponse, ProjectPage, ProjectStatus
from repositories.projects import ProjectRepository
from services.projects import ProjectService
from utils.auth import require_roles
from utils.roles import UserRole

router = APIRouter()
manage_projects = require_roles(UserRole.ADMIN, UserRole.SUPERADMIN)


def project_service(db=Depends(get_database)):
    return ProjectService(ProjectRepository(db))


@router.get('', response_model=ProjectPage)
async def list_projects(limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0, le=100000),
                        status: ProjectStatus | None = None, scope=Depends(domain_scope), service=Depends(project_service)):
    return await domain_operation(service.list(scope, limit, offset, status.value if status else None))


@router.post('', response_model=ProjectResponse, status_code=201)
async def create_project(payload: ProjectCreate, user=Depends(manage_projects),
                         scope=Depends(domain_scope), service=Depends(project_service)):
    return await domain_operation(service.create(scope, user['id'], payload))


@router.get('/{project_id}', response_model=ProjectResponse)
async def get_project(project_id: str, scope=Depends(domain_scope), service=Depends(project_service)):
    return await domain_operation(service.get(scope, project_id))


@router.patch('/{project_id}', response_model=ProjectResponse)
async def update_project(project_id: str, payload: ProjectUpdate, user=Depends(manage_projects),
                         scope=Depends(domain_scope), service=Depends(project_service)):
    return await domain_operation(service.update(scope, project_id, user['id'], payload))


@router.delete('/{project_id}', response_model=ProjectResponse)
async def archive_project(project_id: str, user=Depends(manage_projects),
                          scope=Depends(domain_scope), service=Depends(project_service)):
    return await domain_operation(service.update(scope, project_id, user['id']))
