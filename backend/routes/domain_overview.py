"""New domain overview; preserve the legacy /api/dashboard/overview contract."""
from fastapi import APIRouter, Depends
from core.database import get_database
from core.domain_api import domain_scope, domain_operation
from repositories.overview import OverviewRepository
from services.overview import OverviewService
from models.overview import OverviewResponse
from routes.projects import project_service
from routes.findings import finding_service
from routes.security_runs import run_service
from routes.activity import activity_service

router = APIRouter()


def overview_service(db=Depends(get_database), projects=Depends(project_service), findings=Depends(finding_service),
                     runs=Depends(run_service), activity=Depends(activity_service)):
    return OverviewService(OverviewRepository(db), projects, findings, runs, activity)


@router.get('', response_model=OverviewResponse)
async def overview(project_id: str | None = None, scope=Depends(domain_scope), service=Depends(overview_service)):
    return await domain_operation(service.get(scope, project_id))
