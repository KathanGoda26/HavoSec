from datetime import datetime, timezone
from bson import ObjectId
from fastapi import HTTPException
from core.domain_api import document_view
from models.activity import ActivityType


def activity_event(document, actor_id, event_type, entity_type):
    return {'_id': ObjectId(), 'organization_id': document['organization_id'],
            'project_id': document['project_id'], 'actor_id': actor_id,
            'event_type': event_type.value, 'entity_type': entity_type,
            'entity_id': str(document['_id']), 'message': event_type.value.replace('_', ' ').capitalize(),
            'metadata': {}, 'created_at': document['updated_at']}


class ProjectResourceService:
    def __init__(self, repository, projects):
        self.repository = repository
        self.projects = projects

    async def get_document(self, scope, resource_id):
        document = await self.repository.get(scope, resource_id)
        if document is None:
            raise HTTPException(404, 'Resource not found')
        await self.projects.get_document(scope, document['project_id'])
        return document

    async def get(self, scope, resource_id):
        return document_view(await self.get_document(scope, resource_id))

    async def list(self, scope, limit, offset, project_id=None, status=None):
        filters = {}
        if project_id is not None:
            project = await self.projects.get_document(scope, project_id)
            filters['project_id'] = str(project['_id'])
        if status is not None:
            filters['status'] = status.value
        items, total = await self.repository.list(scope, limit, offset, filters)
        return {'items': [document_view(item) for item in items], 'total': total, 'limit': limit, 'offset': offset}

    async def active_project(self, scope, project_id):
        project = await self.projects.get_document(scope, project_id)
        if project['status'] != 'active':
            raise HTTPException(409, 'Archived projects cannot accept changes')
        return str(project['_id'])


class AssetService(ProjectResourceService):
    def __init__(self, repository, projects, github_repositories=None):
        super().__init__(repository, projects)
        self.github_repositories = github_repositories

    async def create(self, scope, actor_id, payload):
        project_id = await self.active_project(scope, payload.project_id)
        now = datetime.now(timezone.utc)
        document = {**payload.model_dump(mode='json'), '_id': ObjectId(),
                    'organization_id': scope.organization_id, 'project_id': project_id,
                    'status': 'active', 'created_at': now, 'updated_at': now}
        event = activity_event(document, actor_id, ActivityType.ASSET_CREATED, 'asset')
        return document_view(await self.repository.create_with_activity(scope, document, event))

    async def update(self, scope, resource_id, actor_id, payload=None):
        document = await self.get_document(scope, resource_id)
        if document['status'] == 'archived':
            if payload is None:
                return document_view(document)
            raise HTTPException(409, 'Archived assets cannot be edited')
        await self.active_project(scope, document['project_id'])
        changes = {'status': 'archived'} if payload is None else payload.model_dump(exclude_unset=True)
        changes['updated_at'] = datetime.now(timezone.utc)
        event = activity_event({**document, **changes}, actor_id,
                               ActivityType.ASSET_ARCHIVED if payload is None else ActivityType.ASSET_UPDATED, 'asset')
        return document_view(await self.repository.update_with_activity(scope, document, changes, event))

    async def link_github_repository(self, scope, resource_id, actor_id, repository_id):
        document = await self.get_document(scope, resource_id)
        if document['status'] != 'active':
            raise HTTPException(409, 'Archived assets cannot be linked')
        if document['type'] != 'repository':
            raise HTTPException(409, 'Only repository assets can be linked to source control')
        if self.github_repositories is None:
            raise HTTPException(503, 'GitHub repository mapping is unavailable')
        repository = await self.github_repositories.get_repository(
            scope, repository_id, require_authorized=True
        )
        if not repository:
            raise HTTPException(404, 'Authorized GitHub repository not found')
        if repository.get('connection_status') != 'active':
            raise HTTPException(409, 'GitHub repository access needs attention')
        changes = {
            'source_control': {
                'provider': 'github',
                'integration_id': repository['integration_id'],
                'repository_id': repository['repository_id'],
                'repository_full_name': repository['full_name'],
                'default_branch': repository['default_branch'],
                'connection_status': repository['connection_status'],
            },
            'updated_at': datetime.now(timezone.utc),
        }
        event = activity_event({**document, **changes}, actor_id, ActivityType.ASSET_UPDATED, 'asset')
        event['metadata'] = {
            'provider': 'github',
            'repository_id': repository['repository_id'],
            'repository_full_name': repository['full_name'],
        }
        return document_view(await self.repository.update_with_activity(scope, document, changes, event))


class SecurityRunService(ProjectResourceService):
    def __init__(self, repository, projects, assets):
        super().__init__(repository, projects)
        self.assets = assets

    async def create(self, scope, actor_id, payload):
        project_id = await self.active_project(scope, payload.project_id)
        for asset_id in payload.asset_ids:
            asset = await self.assets.get_document(scope, asset_id)
            if asset['project_id'] != project_id:
                raise HTTPException(404, 'Asset not found in this project')
            if asset['status'] != 'active':
                raise HTTPException(409, 'Archived assets cannot be used in a run')
        now = datetime.now(timezone.utc)
        document = {**payload.model_dump(mode='json'), '_id': ObjectId(),
                    'organization_id': scope.organization_id, 'project_id': project_id,
                    'status': 'queued', 'requested_by': actor_id,
                    'started_at': None, 'completed_at': None, 'progress': 0,
                    'summary': None, 'error': None, 'created_at': now, 'updated_at': now}
        event = activity_event(document, actor_id, ActivityType.SECURITY_RUN_CREATED, 'security_run')
        return document_view(await self.repository.create_with_activity(scope, document, event, payload.asset_ids))

    async def cancel(self, scope, resource_id, actor_id):
        document = await self.get_document(scope, resource_id)
        if document['status'] == 'cancelled':
            return document_view(document)
        if document['status'] not in {'queued', 'running'}:
            raise HTTPException(409, 'Finished runs cannot be cancelled')
        now = datetime.now(timezone.utc)
        changes = {'status': 'cancelled', 'completed_at': now, 'updated_at': now}
        event = activity_event({**document, **changes}, actor_id, ActivityType.SECURITY_RUN_CANCELLED, 'security_run')
        return document_view(await self.repository.update_with_activity(
            scope, document, changes, event, require_active_project=False))
