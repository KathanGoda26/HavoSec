from datetime import datetime, timezone
from fastapi import Depends, HTTPException, Query
from pymongo.errors import PyMongoError

from core.database import get_database
from core.ownership import resolve_organization
from repositories.organizations import OrganizationRepository
from utils.auth import get_current_user


async def domain_scope(user=Depends(get_current_user), db=Depends(get_database),
                       organization_id: str | None = Query(None)):
    return await resolve_organization(user, OrganizationRepository(db),
                                      platform_organization_id=organization_id)


def document_view(document):
    result = {key: value for key, value in document.items() if key != '_id'}
    result['id'] = str(document['_id'])
    # PyMongo's legacy configuration decodes UTC BSON dates without tzinfo.
    for key, value in result.items():
        if isinstance(value, datetime):
            result[key] = value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)
    return result


async def domain_operation(operation):
    try:
        return await operation
    except PyMongoError as exc:
        raise HTTPException(503, 'Domain database is unavailable; please retry') from exc
