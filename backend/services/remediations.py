from datetime import datetime, timezone
from bson import ObjectId
from fastapi import HTTPException
from core.domain_api import document_view
from models.activity import ActivityType
from services.project_resources import ProjectResourceService, activity_event
from security_engine.patch_integrity import PatchIntegrityError, assert_verified_patch


# Human-managed proposals only. Approval does not execute or verify a fix.
TRANSITIONS = {
    'pending': {'in_progress', 'awaiting_approval', 'rejected'},
    'in_progress': {'pending', 'awaiting_approval'},
    'awaiting_approval': {'pending', 'approved', 'rejected'},
    'approved': {'pending', 'resolved'},
    'rejected': {'pending'},
    'resolved': {'pending'},
    'failed': {'pending'},
}


class RemediationService(ProjectResourceService):
    def __init__(self, repository, projects, findings, max_verification_attempts=1,
                 github_integrations=None):
        super().__init__(repository, projects)
        self.findings = findings
        self.max_verification_attempts = max_verification_attempts
        self.github_integrations = github_integrations

    async def get_document(self, scope, resource_id):
        document = await super().get_document(scope, resource_id)
        finding = await self.findings.get_document(scope, document['finding_id'])
        if finding['project_id'] != document['project_id']:
            raise HTTPException(404, 'Remediation relationship not found')
        return document

    async def list_filtered(self, scope, limit, offset, project_id=None, finding_id=None, status=None):
        filters = {}
        if project_id is not None:
            project = await self.projects.get_document(scope, project_id)
            filters['project_id'] = str(project['_id'])
        if finding_id is not None:
            finding = await self.findings.get_document(scope, finding_id)
            if 'project_id' in filters and filters['project_id'] != finding['project_id']:
                raise HTTPException(404, 'Remediation relationship not found')
            filters['finding_id'] = str(finding['_id'])
        if status is not None:
            filters['status'] = status.value
        items, total = await self.repository.list(scope, limit, offset, filters)
        for item in items:
            await self.get_document(scope, str(item['_id']))
        return {'items': [document_view(item) for item in items], 'total': total, 'limit': limit, 'offset': offset}

    async def create(self, scope, actor_id, payload):
        finding = await self.findings.get_document(scope, payload.finding_id)
        validation = finding.get('validation') or {}
        validation_status = validation.get('status')
        if hasattr(validation_status, 'value'):
            validation_status = validation_status.value
        if validation_status not in {'confirmed', 'likely'}:
            raise HTTPException(409, 'Finding must be validated as confirmed or likely before remediation')
        if validation_status == 'likely' and not payload.acknowledge_likely:
            raise HTTPException(409, 'Likely findings require explicit human-review acknowledgement')
        project_id = await self.active_project(scope, finding['project_id'])
        now = datetime.now(timezone.utc)
        values = payload.model_dump()
        values.pop('acknowledge_likely')
        source_metadata = finding.get('source_metadata') or {}
        document = {**values, '_id': ObjectId(), 'finding_id': str(finding['_id']),
                    'organization_id': scope.organization_id, 'project_id': project_id,
                    'asset_id': finding.get('asset_id'),
                    'source_security_run_id': finding.get('last_security_run_id') or finding.get('security_run_id'),
                    'source_commit': source_metadata.get('commit_sha'),
                    'proposal': None, 'patch_format': None,
                    'validation_status': validation_status, 'verification_status': 'not_started',
                    'verification_result': None, 'verification_attempts': 0,
                    'proposal_agent_metadata': {},
                    'status': 'pending', 'created_by': actor_id, 'approved_by': None,
                    'created_at': now, 'updated_at': now}
        event = activity_event(document, actor_id, ActivityType.REMEDIATION_CREATED, 'remediation')
        return document_view(await self.repository.create_with_activity(scope, document, event))

    async def update(self, scope, resource_id, actor_id, payload):
        document = await self.get_document(scope, resource_id)
        await self.active_project(scope, document['project_id'])
        changes = payload.model_dump(exclude_unset=True, mode='json')
        old, new = document['status'], changes.get('status', document['status'])
        if new != old and new not in TRANSITIONS[old]:
            raise HTTPException(409, 'Invalid remediation status transition')
        if new == 'approved' and new != old:
            try:
                assert_verified_patch(document)
            except PatchIntegrityError as exc:
                raise HTTPException(409, str(exc)) from exc
            if document.get('verification_status') != 'verified':
                raise HTTPException(409, 'Only a verified remediation can be approved')
            if document.get('verified_source_commit') != document.get('source_commit'):
                raise HTTPException(409, 'Verified remediation source revision is stale')
            finding = await self.findings.get_document(scope, document['finding_id'])
            if ((finding.get('source_metadata') or {}).get('commit_sha') !=
                    document.get('verified_source_commit')):
                raise HTTPException(409, 'Finding source revision changed after verification')
        editing = any(key in changes for key in ['summary', 'recommendation', 'proposed_fix'])
        if editing and (new in {'approved', 'rejected', 'resolved'} or
                        (old in {'awaiting_approval', 'approved', 'rejected', 'resolved'} and new != 'pending')):
            raise HTTPException(409, 'Return proposal to pending before editing it')
        if all(document[key] == value for key, value in changes.items()):
            return document_view(document)
        if new != old:
            changes['approved_by'] = actor_id if new == 'approved' else (document['approved_by'] if new == 'resolved' else None)
        changes['updated_at'] = datetime.now(timezone.utc)
        event = activity_event({**document, **changes}, actor_id, ActivityType.REMEDIATION_UPDATED, 'remediation')
        event['metadata'] = {'previous_status': old, 'status': new}
        return document_view(await self.repository.update_with_activity(scope, document, changes, event))

    async def queue_verification(self, scope, resource_id, actor_id):
        document = await self.get_document(scope, resource_id)
        await self.active_project(scope, document['project_id'])
        if document.get('verification_status', 'not_started') in {'queued', 'testing', 'verified'}:
            raise HTTPException(409, 'Remediation verification is already active or complete')
        attempts = int(document.get('verification_attempts', 0))
        if attempts >= self.max_verification_attempts:
            raise HTTPException(409, 'Remediation verification attempt limit reached')
        if not document.get('source_commit') or not document.get('asset_id'):
            raise HTTPException(409, 'Remediation does not have a reproducible source revision')
        if document.get('validation_status') not in {'confirmed', 'likely'}:
            raise HTTPException(409, 'Remediation is no longer eligible for verification')
        now = datetime.now(timezone.utc)
        changes = {'status': 'in_progress', 'verification_status': 'queued',
                   'verification_result': None, 'verification_attempts': attempts + 1,
                   'updated_at': now}
        event = activity_event({**document, **changes}, actor_id,
                               ActivityType.REMEDIATION_VERIFICATION_QUEUED, 'remediation')
        event['metadata'] = {'attempt': attempts + 1}
        return document_view(await self.repository.update_with_activity(
            scope, document, changes, event))

    async def pull_request_eligibility(self, scope, resource_id):
        document = await self.get_document(scope, resource_id)
        finding = await self.findings.get_document(scope, document['finding_id'])
        reasons = []
        if document.get('status') != 'approved':
            reasons.append('Remediation is not approved')
        if document.get('verification_status') != 'verified':
            reasons.append('Remediation verification is not verified')
        try:
            assert_verified_patch(document)
        except PatchIntegrityError:
            reasons.append('Verified patch integrity check failed')

        finding_commit = (finding.get('source_metadata') or {}).get('commit_sha')
        commits = {document.get('source_commit'), document.get('verified_source_commit'), finding_commit}
        if None in commits or '' in commits:
            source_status = 'unknown'
            reasons.append('Verified source revision is unavailable')
        elif len(commits) != 1:
            source_status = 'stale'
            reasons.append('Verified source revision is stale')
        else:
            source_status = 'verified'

        asset = await self.repository.db.assets.find_one(scope.query(_id=ObjectId(document['asset_id'])))
        source_control = (asset or {}).get('source_control') or {}
        if source_control.get('provider') != 'github':
            reasons.append('Repository asset is not linked to GitHub')
        elif source_control.get('connection_status') != 'active':
            reasons.append('GitHub repository connection needs attention')

        if self.github_integrations is None:
            reasons.append('GitHub integration is unavailable')
        elif source_control.get('repository_id'):
            integration = await self.github_integrations.get(scope)
            repository = await self.github_integrations.get_repository(
                scope, source_control['repository_id'], require_authorized=True
            )
            if not integration or integration.get('status') != 'active':
                reasons.append('GitHub integration is not active')
            if (not repository or repository.get('connection_status') != 'active' or
                    repository.get('integration_id') != source_control.get('integration_id')):
                reasons.append('GitHub repository is not authorized')
            active_pr = await self.github_integrations.get_active_pull_request(scope, str(document['_id']))
            if active_pr:
                reasons.append('An active pull request already exists')

        return {
            'eligible': not reasons,
            'reasons': reasons,
            'source_integrity_status': source_status,
            'requires_remote_source_check': not reasons,
        }
