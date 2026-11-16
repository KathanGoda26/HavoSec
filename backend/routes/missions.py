from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query

from core.database import get_database
from core.domain_api import domain_operation, domain_scope
from mission_orchestration.governance import FixtureGateway, execution_view
from mission_orchestration.plan import MissionRef
from models.missions import FixtureApprovalRequest, MissionCreate, MissionPage, MissionResponse, MissionStatus
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


@router.get('/{mission_id}/report')
async def get_mission_report(mission_id: str, scope=Depends(domain_scope), service=Depends(mission_service)):
    mission = await domain_operation(service.get_document(scope, mission_id))
    if 'assessment_report' not in mission:
        raise HTTPException(404, 'Assessment report is unavailable')
    return execution_view(mission['assessment_report'])


@router.post('/{mission_id}/cancel', response_model=MissionResponse, dependencies=[Depends(manage_projects)])
async def cancel_mission(mission_id: str, scope=Depends(domain_scope), service=Depends(mission_service)):
    return await domain_operation(service.cancel(scope, mission_id))


@router.get('/{mission_id}/actions', dependencies=[Depends(manage_projects)])
async def get_mission_actions(mission_id: str, scope=Depends(domain_scope), service=Depends(mission_service)):
    mission = await domain_operation(service.get_document(scope, mission_id))
    return execution_view(list(mission.get('fixture_actions', {}).values()))


@router.post('/{mission_id}/actions/{task_id}/approve')
async def approve_mission_action(
    mission_id: str, task_id: str, payload: FixtureApprovalRequest,
    user=Depends(manage_projects), scope=Depends(domain_scope), service=Depends(mission_service),
    db=Depends(get_database),
):
    mission = await domain_operation(service.get_document(scope, mission_id))
    ref = MissionRef(scope.organization_id, str(mission['_id']))
    approval = await domain_operation(FixtureGateway(db).change_approval(ref, task_id, user['id'], payload.action_digest))
    return execution_view(approval)


@router.post('/{mission_id}/actions/{task_id}/approvals/{approval_id}/revoke')
async def revoke_mission_action_approval(
    mission_id: str, task_id: str, approval_id: str, payload: FixtureApprovalRequest,
    user=Depends(manage_projects), scope=Depends(domain_scope), service=Depends(mission_service),
    db=Depends(get_database),
):
    mission = await domain_operation(service.get_document(scope, mission_id))
    ref = MissionRef(scope.organization_id, str(mission['_id']))
    approval = await domain_operation(
        FixtureGateway(db).change_approval(ref, task_id, user['id'], payload.action_digest, revoke_id=approval_id)
    )
    return execution_view(approval)
