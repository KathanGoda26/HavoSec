from datetime import datetime, timezone
import re
from bson import ObjectId
from fastapi import HTTPException
from pymongo.errors import PyMongoError


def organization_view(document):
    """Preserve legacy fields while exposing canonical organization metadata."""
    result = dict(document)
    result['id'] = str(result.pop('_id'))
    active = result.get('isActive', True) is not False and result.get('status', 'active') == 'active'
    result['status'] = 'active' if active else 'inactive'
    result['isActive'] = active
    result.setdefault('slug', organization_slug(result.get('name', ''), result['id']))
    result.setdefault('created_at', result.get('createdAt'))
    result.setdefault('updated_at', result.get('updatedAt', result.get('created_at')))
    return result


def organization_slug(name, identity):
    stem = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')[:80] or 'organization'
    return f'{stem}-{identity}'


class OrganizationService:
    def __init__(self, repository):
        self.repository = repository

    async def list(self, limit, offset):
        records, total = await self.repository.list(limit, offset)
        return {'clients': [organization_view(record) for record in records], 'total': total}

    async def get(self, identity):
        record = await self.repository.find_by_id(identity)
        if not record:
            raise HTTPException(404, 'Client not found')
        return organization_view(record)

    async def create(self, payload):
        now = datetime.now(timezone.utc)
        document = payload.model_dump(exclude_unset=True)
        identity = ObjectId()
        document.update(_id=identity, slug=organization_slug(document['name'], str(identity)),
                        created_at=now, updated_at=now, createdAt=now, updatedAt=now)
        document.setdefault('subscription', {'plan': 'free', 'status': 'trial'})
        document.setdefault('services', [])
        document.setdefault('securityModels', {'offensive': False, 'defensive': False})
        self.normalize_state(document, default=True)
        await self.repository.insert(document)
        return {'message': 'Client created', 'client': organization_view(document)}

    @staticmethod
    def normalize_state(changes, default=False):
        if 'status' in changes:
            changes['isActive'] = changes['status'] == 'active'
        elif 'isActive' in changes:
            changes['status'] = 'active' if changes['isActive'] else 'inactive'
        elif default:
            changes.update(status='active', isActive=True)

    async def update(self, identity, payload):
        changes = payload.model_dump(exclude_unset=True)
        if not changes:
            raise HTTPException(400, 'No changes supplied')
        self.normalize_state(changes)
        now = datetime.now(timezone.utc)
        changes.update(updated_at=now, updatedAt=now)
        record = await self.repository.update(identity, changes)
        if not record:
            raise HTTPException(404, 'Client not found')
        return {'message': 'Client updated', 'client': organization_view(record)}

    async def deactivate(self, identity):
        now = datetime.now(timezone.utc)
        record = await self.repository.update(identity, {'status': 'inactive', 'isActive': False,
                                                        'updated_at': now, 'updatedAt': now})
        if not record:
            raise HTTPException(404, 'Client not found')
        return {'message': 'Client deactivated; history preserved', 'client': organization_view(record)}


async def database_operation(operation):
    try:
        return await operation
    except PyMongoError as exc:
        raise HTTPException(503, 'Organization database is unavailable') from exc
