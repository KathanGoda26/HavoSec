from fastapi import APIRouter, Depends, Query
from core.database import get_database
from core.domain_api import domain_operation, domain_scope
from models.findings import FindingUpdate, FindingResponse, FindingPage, FindingStatus, Severity, ValidationResult
from repositories.project_resources import ProjectResourceRepository
from routes.projects import project_service, manage_projects
from routes.assets import asset_service
from routes.security_runs import run_service
from services.findings import FindingService
from security_engine.agents.analysis import configured_agent
from security_engine.config import EngineSettings

router = APIRouter()


def finding_service(db=Depends(get_database), projects=Depends(project_service),
                    assets=Depends(asset_service), runs=Depends(run_service)):
    return FindingService(ProjectResourceRepository(db, db.findings), projects, assets, runs,
                          configured_agent(EngineSettings.from_environment()))


@router.get('', response_model=FindingPage)
async def list_findings(limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0, le=100000),
                        project_id: str | None = None, asset_id: str | None = None, security_run_id: str | None = None,
                        severity: Severity | None = None, status: FindingStatus | None = None,
                        scope=Depends(domain_scope), service=Depends(finding_service)):
    return await domain_operation(service.list_filtered(scope, limit, offset, project_id, asset_id, security_run_id, severity, status))


@router.get('/{finding_id}', response_model=FindingResponse)
async def get_finding(finding_id: str, scope=Depends(domain_scope), service=Depends(finding_service)):
    return await domain_operation(service.get(scope, finding_id))


@router.patch('/{finding_id}', response_model=FindingResponse)
async def update_finding(finding_id: str, payload: FindingUpdate, user=Depends(manage_projects),
                         scope=Depends(domain_scope), service=Depends(finding_service)):
    return await domain_operation(service.update(scope, finding_id, user['id'], payload))


@router.post('/{finding_id}/validate', response_model=ValidationResult)
async def validate_finding(finding_id: str, user=Depends(manage_projects),
                           scope=Depends(domain_scope), service=Depends(finding_service)):
    return await domain_operation(service.validate(scope, finding_id, user['id']))
