from fastapi import APIRouter, Depends, Query
from core.database import get_database
from core.domain_api import domain_scope, domain_operation
from models.activity import ActivityPage
from repositories.activity import ActivityRepository
from routes.projects import project_service
from services.activity import ActivityService

router = APIRouter()


def activity_service(db=Depends(get_database), projects=Depends(project_service)):
    return ActivityService(ActivityRepository(db), projects)


@router.get('', response_model=ActivityPage)
async def list_activity(limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0, le=100000),
                        project_id: str | None = None, scope=Depends(domain_scope), service=Depends(activity_service)):
    return await domain_operation(service.list(scope, limit, offset, project_id))
