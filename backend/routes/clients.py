"""Legacy client URLs backed by the organization service; platform-only management."""
from fastapi import APIRouter, Depends, Query
from core.database import get_database
from models.organizations import OrganizationCreate, OrganizationUpdate
from repositories.organizations import OrganizationRepository
from services.organizations import OrganizationService, database_operation
from utils.auth import require_roles
from utils.roles import UserRole

router = APIRouter(dependencies=[Depends(require_roles(UserRole.SUPERADMIN))])


def organization_service(db=Depends(get_database)):
    return OrganizationService(OrganizationRepository(db))


async def get_client_stats(db):
    total = await db.client_companies.count_documents({})
    active = await db.client_companies.count_documents({
        "isActive": {"$ne": False},
        "$or": [{"status": "active"}, {"status": {"$exists": False}}],
    })
    return {"total": total, "active": active}


@router.get("/")
async def get_clients(limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0, le=100000),
                      service=Depends(organization_service)):
    return await database_operation(service.list(limit, offset))


@router.get("/{client_id}")
async def get_client(client_id: str, service=Depends(organization_service)):
    return await database_operation(service.get(client_id))


@router.post("/")
async def create_client(payload: OrganizationCreate, service=Depends(organization_service)):
    return await database_operation(service.create(payload))


@router.put("/{client_id}")
@router.patch("/{client_id}")
async def update_client(client_id: str, payload: OrganizationUpdate, service=Depends(organization_service)):
    return await database_operation(service.update(client_id, payload))


@router.delete("/{client_id}")
async def delete_client(client_id: str, service=Depends(organization_service)):
    return await database_operation(service.deactivate(client_id))
