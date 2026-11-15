import hashlib
import json
from datetime import datetime, timezone

from bson import ObjectId
from fastapi import HTTPException

from core.domain_api import document_view
from services.project_resources import ProjectResourceService


class MissionService(ProjectResourceService):
    def __init__(self, repository, projects, assets):
        super().__init__(repository, projects)
        self.assets = assets

    async def cancel(self, scope, mission_id):
        mission = await self.get_document(scope, mission_id)
        updated = await self.repository.request_cancellation(scope, mission)
        if updated is None:
            raise HTTPException(404, 'Resource not found')
        return document_view(updated)

    async def create(self, scope, actor_id, payload, request_key):
        inputs = {
            'project_id': payload.project_id.lower(),
            'asset_id': payload.asset_id.lower(),
            'objective': payload.objective,
            'mission_type': 'repository_assessment',
        }
        digest = hashlib.sha256(json.dumps(inputs, sort_keys=True).encode()).hexdigest()
        existing = await self.repository.get_by_key(scope, request_key)
        if existing is None:
            project_id = await self.active_project(scope, inputs['project_id'])
            asset = await self.assets.get_document(scope, inputs['asset_id'])
            if asset['project_id'] != project_id:
                raise HTTPException(404, 'Asset not found in this project')
            if asset['status'] != 'active' or asset['type'] != 'repository':
                raise HTTPException(409, 'An active repository asset is required')

            now = datetime.now(timezone.utc)
            existing = await self.repository.create_with_start(scope, {
                **inputs, '_id': ObjectId(), 'organization_id': scope.organization_id,
                'requested_by': actor_id, 'request_key': request_key, 'request_digest': digest,
                'status': 'queued', 'created_at': now, 'updated_at': now,
            })
        if existing['request_digest'] != digest:
            raise HTTPException(409, 'Idempotency key already used for a different mission')
        return document_view(existing)
