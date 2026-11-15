from datetime import datetime, timezone
from bson import ObjectId
from fastapi import HTTPException
from core.domain_api import document_view
from models.activity import ActivityType


def project_event(document, actor_id, event_type, changed_fields=()):
    return {
        '_id': ObjectId(), 'organization_id': document['organization_id'],
        'project_id': str(document['_id']), 'actor_id': actor_id,
        'event_type': event_type.value, 'entity_type': 'project',
        'entity_id': str(document['_id']),
        'message': {ActivityType.PROJECT_CREATED: 'Project created',
                    ActivityType.PROJECT_UPDATED: 'Project updated',
                    ActivityType.PROJECT_ARCHIVED: 'Project archived'}[event_type],
        'metadata': {'changed_fields': sorted(changed_fields)},
        'created_at': document['updated_at'],
    }


class ProjectService:
    def __init__(self, repository):
        self.repository = repository

    async def get_document(self, scope, project_id):
        document = await self.repository.get(scope, project_id)
        if document is None:
            raise HTTPException(404, 'Project not found')
        return document

    async def get(self, scope, project_id):
        return document_view(await self.get_document(scope, project_id))

    async def list(self, scope, limit, offset, status=None):
        items, total = await self.repository.list(scope, limit, offset, status)
        return {'items': [document_view(item) for item in items], 'total': total, 'limit': limit, 'offset': offset}

    async def create(self, scope, actor_id, payload):
        now = datetime.now(timezone.utc)
        document = {**payload.model_dump(), '_id': ObjectId(), 'organization_id': scope.organization_id,
                    'status': 'active', 'created_by': actor_id, 'created_at': now, 'updated_at': now}
        event = project_event(document, actor_id, ActivityType.PROJECT_CREATED)
        return document_view(await self.repository.create_with_activity(document, event))

    async def update(self, scope, project_id, actor_id, payload=None):
        document = await self.get_document(scope, project_id)
        archiving = payload is None
        if document['status'] == 'archived':
            if archiving:
                return document_view(document)
            raise HTTPException(409, 'Archived projects cannot be edited')
        changes = {'status': 'archived'} if archiving else payload.model_dump(exclude_unset=True)
        changed_fields = list(changes)
        changes['updated_at'] = datetime.now(timezone.utc)
        event = project_event({**document, **changes}, actor_id,
                              ActivityType.PROJECT_ARCHIVED if archiving else ActivityType.PROJECT_UPDATED,
                              changed_fields)
        updated = await self.repository.update_with_activity(scope, project_id, changes, event)
        if updated is None:
            raise HTTPException(409, 'Project changed; refresh and retry')
        return document_view(updated)
