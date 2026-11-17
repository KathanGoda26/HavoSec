import hashlib
import json
import os
import re
from datetime import datetime, timezone

from bson import ObjectId
from fastapi import HTTPException

from core.domain_api import document_view
from integrations.github.client import GitHubAPIError
from integrations.github.config import GitHubConfigurationError
from mission_orchestration.github_scope import authorized_github_scope, resolve_github_commit
from mission_orchestration.plan import FIXTURE_REMEDIATION_MISSION, FIXTURE_SCAN_MISSION, GITHUB_SCAN_MISSION
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
            'mission_type': payload.mission_type,
        }
        digest = hashlib.sha256(json.dumps(inputs, sort_keys=True).encode()).hexdigest()
        existing = await self.repository.get_by_key(scope, request_key)
        if existing is None:
            if payload.mission_type in (FIXTURE_SCAN_MISSION, FIXTURE_REMEDIATION_MISSION):
                commit = os.environ.get('MISSION_FIXTURE_COMMIT', '')
                if not re.fullmatch('[0-9a-f]{40}', commit):
                    raise HTTPException(503, 'Fixture scanning is not configured')
                inputs['fixture_commit'] = commit
            project_id = await self.active_project(scope, inputs['project_id'])
            asset = await self.assets.get_document(scope, inputs['asset_id'])
            if asset['project_id'] != project_id:
                raise HTTPException(404, 'Asset not found in this project')
            if asset['status'] != 'active' or asset['type'] != 'repository':
                raise HTTPException(409, 'An active repository asset is required')
            if payload.mission_type == GITHUB_SCAN_MISSION:
                db = self.repository.db
                organization = await db.client_companies.find_one({'_id': ObjectId(scope.organization_id)})
                modes = (organization or {}).get('mission_policy')
                if not isinstance(modes, dict) or modes.get('github_assessment') not in ('allow', 'require_approval'):
                    raise HTTPException(403, 'GitHub assessments are disabled for this organization')
                github = await authorized_github_scope(db, scope.organization_id, asset)
                if not github:
                    raise HTTPException(409, 'Link an active, authorized GitHub repository to this asset')
                try:
                    commit = await resolve_github_commit(github)
                except (GitHubAPIError, GitHubConfigurationError) as exc:
                    raise HTTPException(502, 'The GitHub assessment commit could not be verified') from exc
                inputs.update(github_scope=github, source_commit=commit)

            now = datetime.now(timezone.utc)
            existing = await self.repository.create_with_start(scope, {
                **inputs, '_id': ObjectId(), 'organization_id': scope.organization_id,
                'requested_by': actor_id, 'request_key': request_key, 'request_digest': digest,
                'status': 'queued', 'created_at': now, 'updated_at': now,
            })
        if existing['request_digest'] != digest:
            raise HTTPException(409, 'Idempotency key already used for a different mission')
        return document_view(existing)
