from datetime import datetime, timezone
from fastapi import HTTPException
from core.domain_api import document_view
from models.activity import ActivityType
from services.project_resources import ProjectResourceService, activity_event
from security_engine.validation import validate_finding, apply_agent_assessment


class FindingService(ProjectResourceService):
    def __init__(self, repository, projects, assets, runs, agent=None):
        super().__init__(repository, projects)
        self.assets = assets
        self.runs = runs
        self.agent = agent

    async def get_document(self, scope, resource_id):
        document = await super().get_document(scope, resource_id)
        await self.validate_links(scope, document)
        return document

    async def validate_links(self, scope, document):
        asset_id, run_id = document.get('asset_id'), document.get('security_run_id')
        for resource_id, service in [(asset_id, self.assets), (run_id, self.runs)]:
            if resource_id is not None:
                linked = await service.get_document(scope, resource_id)
                if linked['project_id'] != document['project_id']:
                    raise HTTPException(404, 'Finding relationship not found')
                if service is self.runs and asset_id is not None and asset_id not in linked['asset_ids']:
                    raise HTTPException(404, 'Finding asset is not part of the run')

    async def list_filtered(self, scope, limit, offset, project_id=None, asset_id=None,
                            security_run_id=None, severity=None, status=None):
        filters = {}
        selected_project = None
        for key, value, service in [('project_id', project_id, self.projects),
                                    ('asset_id', asset_id, self.assets), ('security_run_id', security_run_id, self.runs)]:
            if value is not None:
                linked = await service.get_document(scope, value)
                parent = str(linked['_id']) if key == 'project_id' else linked['project_id']
                if selected_project is not None and parent != selected_project:
                    raise HTTPException(404, 'Finding relationship not found')
                selected_project = parent
                filters['security_run_ids' if key == 'security_run_id' else key] = str(linked['_id'])
        if severity is not None:
            filters['severity'] = severity.value
        if status is not None:
            filters['status'] = status.value
        items, total = await self.repository.list(scope, limit, offset, filters)
        # Fail closed even for inconsistent records inserted outside these APIs.
        for item in items:
            await self.projects.get_document(scope, item['project_id'])
            await self.validate_links(scope, item)
        return {'items': [document_view(item) for item in items], 'total': total, 'limit': limit, 'offset': offset}

    async def update(self, scope, resource_id, actor_id, payload):
        document = await self.get_document(scope, resource_id)
        await self.active_project(scope, document['project_id'])
        if document['status'] == payload.status.value:
            return document_view(document)
        changes = {'status': payload.status.value, 'updated_at': datetime.now(timezone.utc)}
        event = activity_event({**document, **changes}, actor_id, ActivityType.FINDING_UPDATED, 'finding')
        event['metadata'] = {'previous_status': document['status'], 'status': changes['status']}
        return document_view(await self.repository.update_with_activity(scope, document, changes, event))

    async def validate(self, scope, resource_id, actor_id):
        document = await self.get_document(scope, resource_id)
        await self.active_project(scope, document['project_id'])
        result = validate_finding(document, actor_id)
        if self.agent:
            assessment, _ = await self.agent.validate(document, result)
            result = apply_agent_assessment(result, assessment)
        validation = result.model_dump(mode='python')
        changes = {'validation': validation, 'updated_at': datetime.now(timezone.utc)}
        event = activity_event({**document, **changes}, actor_id, ActivityType.FINDING_VALIDATED, 'finding')
        event['metadata'] = {'validation_status': validation['status'],
                             'validation_method': validation['validation_method'],
                             'confidence': validation['confidence']}
        updated = await self.repository.update_with_activity(scope, document, changes, event)
        return updated['validation']
