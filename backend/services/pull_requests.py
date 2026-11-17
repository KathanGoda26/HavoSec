from dataclasses import replace
from datetime import datetime, timezone

from bson import ObjectId
from fastapi import HTTPException

from core.domain_api import document_view
from integrations.github.client import GitHubAPIError, GitHubAppClient
from models.activity import ActivityType


class PullRequestService:
    def __init__(self, repository, remediation_service, github_integrations, settings):
        self.repository = repository
        self.remediations = remediation_service
        self.github_integrations = github_integrations
        self.settings = settings

    async def request_creation(self, scope, remediation_id, actor_id):
        existing = await self.repository.get_for_remediation(scope, remediation_id)
        if existing:
            return document_view(existing)
        eligibility = await self.remediations.pull_request_eligibility(scope, remediation_id)
        if not eligibility['eligible']:
            raise HTTPException(409, '; '.join(eligibility['reasons']))
        remediation = await self.remediations.get_document(scope, remediation_id)
        asset = await self.repository.db.assets.find_one(
            scope.query(_id=ObjectId(remediation['asset_id']))
        )
        source_control = asset['source_control']
        integration = await self.github_integrations.get(scope)
        client = GitHubAppClient(replace(
            self.settings, installation_id=integration['installation_id']
        ))
        try:
            current_head = await client.get_branch_head(
                source_control['repository_full_name'], source_control['default_branch'],
                read_repository_id=source_control['repository_id'],
            )
        except GitHubAPIError as exc:
            raise HTTPException(502, 'GitHub source revision could not be verified') from exc
        expected = remediation['verified_source_commit']
        if current_head != expected:
            now = datetime.now(timezone.utc)
            await self.repository.mark_remediation_stale(scope, remediation_id, now)
            raise HTTPException(409, 'Repository source changed; remediation requires re-verification')

        now = datetime.now(timezone.utc)
        branch = f"havosec/remediation-{remediation_id[:12]}"
        document = {
            '_id': ObjectId(), 'organization_id': scope.organization_id,
            'project_id': remediation['project_id'], 'asset_id': remediation['asset_id'],
            'finding_id': remediation['finding_id'], 'remediation_id': remediation_id,
            'provider': 'github', 'repository_id': source_control['repository_id'],
            'repository_full_name': source_control['repository_full_name'],
            'installation_id': integration['installation_id'], 'branch': branch,
            'base_branch': source_control['default_branch'],
            'expected_source_commit': expected,
            'verified_patch_sha256': remediation['verified_patch_sha256'],
            'commit_sha': None, 'pr_number': None, 'pr_url': None,
            'status': 'queued', 'checks_status': 'unknown', 'checks': {},
            'reverification_status': 'pending', 'error': None,
            'requested_by': actor_id, 'created_at': now, 'updated_at': now,
        }
        event = {
            '_id': ObjectId(), 'organization_id': scope.organization_id,
            'project_id': remediation['project_id'], 'actor_id': actor_id,
            'event_type': ActivityType.PULL_REQUEST_CREATION_STARTED.value,
            'entity_type': 'pull_request', 'entity_id': str(document['_id']),
            'message': 'Pull request creation queued',
            'metadata': {'remediation_id': remediation_id, 'repository_id': source_control['repository_id']},
            'created_at': now,
        }
        return document_view(await self.repository.create_idempotent(scope, document, event))

    async def get(self, scope, remediation_id):
        record = await self.repository.get_for_remediation(scope, remediation_id)
        if not record:
            raise HTTPException(404, 'Pull request not found')
        return document_view(record)
