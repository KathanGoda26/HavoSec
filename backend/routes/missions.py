from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query

from core.database import get_database
from core.domain_api import domain_operation, domain_scope
from models.missions import MissionCreate, MissionPage, MissionResponse, MissionStatus
from repositories.missions import MissionRepository
from routes.assets import asset_service
from routes.projects import manage_projects, project_service
from services.missions import MissionService

router = APIRouter()


def mission_service(db=Depends(get_database), projects=Depends(project_service), assets=Depends(asset_service)):
    return MissionService(MissionRepository(db), projects, assets)


@router.post('', response_model=MissionResponse, status_code=201)
async def create_mission(
    payload: MissionCreate,
    request_key: Annotated[str, Header(alias='Idempotency-Key', pattern=r'^[A-Za-z0-9_-]{16,128}$')],
    user=Depends(manage_projects),
    scope=Depends(domain_scope),
    service=Depends(mission_service),
):
    return await domain_operation(service.create(scope, user['id'], payload, request_key))


@router.get('', response_model=MissionPage)
async def list_missions(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0, le=100000),
    project_id: str | None = None,
    status: MissionStatus | None = None,
    scope=Depends(domain_scope),
    service=Depends(mission_service),
):
    return await domain_operation(service.list(scope, limit, offset, project_id, status))


@router.get('/{mission_id}', response_model=MissionResponse)
async def get_mission(mission_id: str, scope=Depends(domain_scope), service=Depends(mission_service)):
    return await domain_operation(service.get(scope, mission_id))


@router.post('/{mission_id}/cancel', response_model=MissionResponse, dependencies=[Depends(manage_projects)])
async def cancel_mission(mission_id: str, scope=Depends(domain_scope), service=Depends(mission_service)):
    return await domain_operation(service.cancel(scope, mission_id))
