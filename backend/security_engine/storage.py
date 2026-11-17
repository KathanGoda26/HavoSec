"""MongoDB worker state and transactional result persistence."""
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from pymongo import ReturnDocument
from fastapi import HTTPException
from core.ids import object_id
from core.ownership import OrganizationScope
from core.membership import membership_value
from models.findings import FindingResponse
from models.remediations import RemediationProposal, VerificationResult
from security_engine.scanners.base import ScannerResult
from security_engine.patch_integrity import patch_sha256


class RunChanged(RuntimeError):
    pass


class WorkerRepository:
    def __init__(self, db, worker_id, lease_seconds):
        self.db, self.worker_id, self.lease_seconds = db, worker_id, lease_seconds

    async def fail_expired_claims(self):
        recovered = 0
        while True:
            now = datetime.now(timezone.utc)
            async def save(session):
                run = await self.db.security_runs.find_one_and_update(
                    {'status': 'running', 'claim_expires_at': {'$lt': now}},
                    {'$set': {'status': 'failed', 'completed_at': now, 'updated_at': now,
                              'error': 'Security worker stopped before the run completed'},
                     '$unset': {'worker_id': '', 'claim_expires_at': ''}},
                    sort=[('claim_expires_at', 1), ('_id', 1)],
                    return_document=ReturnDocument.AFTER, session=session)
                if run:
                    await self.db.activity_events.insert_one(
                        event(run, 'security_run_failed', 'Security run failed', now,
                              {'reason': 'Worker claim expired'}), session=session)
                return run
            async with await self.db.client.start_session() as session:
                run = await session.with_transaction(save)
            if not run:
                return recovered
            recovered += 1

    async def fail_expired_remediations(self):
        recovered = 0
        while True:
            now = datetime.now(timezone.utc)
            async def save(session):
                remediation = await self.db.remediations.find_one_and_update(
                    {'verification_status': 'testing', 'claim_expires_at': {'$lt': now}},
                    {'$set': {'verification_status': 'inconclusive', 'status': 'failed',
                              'updated_at': now, 'verified_at': now,
                              'verification_result': VerificationResult(
                                  remediation_id='0' * 24, status='inconclusive',
                                  original_finding_present=None, new_findings_count=0,
                                  new_equal_or_higher_findings_count=0, before_finding_count=0,
                                  after_finding_count=0, before_severity_counts={},
                                  after_severity_counts={}, scanner='semgrep',
                                  scanner_version='unavailable',
                                  summary='Security worker stopped before verification completed',
                                  verified_at=now).model_dump(mode='python')},
                     '$unset': {'worker_id': '', 'claim_expires_at': ''}},
                    sort=[('claim_expires_at', 1), ('_id', 1)],
                    return_document=ReturnDocument.AFTER, session=session)
                if remediation:
                    remediation['verification_result']['remediation_id'] = str(remediation['_id'])
                    await self.db.remediations.update_one(
                        {'_id': remediation['_id']},
                        {'$set': {'verification_result.remediation_id': str(remediation['_id'])}},
                        session=session)
                    await self.db.activity_events.insert_one(
                        remediation_event(remediation, 'remediation_failed',
                                          'Remediation verification claim expired', now,
                                          {'verification_status': 'inconclusive'}), session=session)
                return remediation
            async with await self.db.client.start_session() as session:
                remediation = await session.with_transaction(save)
            if not remediation:
                return recovered
            recovered += 1

    async def fail_expired_pull_requests(self):
        now = datetime.now(timezone.utc)
        result = await self.db.pull_requests.update_many(
            {'status': 'creating', 'claim_expires_at': {'$lt': now}},
            {'$set': {'status': 'queued', 'updated_at': now},
             '$unset': {'worker_id': '', 'claim_expires_at': ''}},
        )
        return result.modified_count

    async def fail_expired_pull_request_reverifications(self):
        now = datetime.now(timezone.utc)
        result = await self.db.pull_requests.update_many(
            {'reverification_status': 'testing', 'reverification_claim_expires_at': {'$lt': now}},
            {'$set': {'reverification_status': 'queued', 'updated_at': now},
             '$unset': {'reverification_worker_id': '', 'reverification_claim_expires_at': ''}},
        )
        return result.modified_count

    async def claim(self, run_id=None):
        now = datetime.now(timezone.utc)
        async def save(session):
            query = {'status': 'queued'}
            if run_id is not None:
                query['_id'] = object_id(run_id)
            run = await self.db.security_runs.find_one_and_update(
                query,
                {'$set': {'status': 'running', 'progress': 5, 'started_at': now, 'updated_at': now,
                          'worker_id': self.worker_id,
                          'claim_expires_at': now + timedelta(seconds=self.lease_seconds)}},
                sort=[('created_at', 1), ('_id', 1)], return_document=ReturnDocument.AFTER, session=session)
            if run:
                await self.db.activity_events.insert_one(
                    event(run, 'security_run_started', 'Security run started', now, {}), session=session)
            return run
        async with await self.db.client.start_session() as session:
            return await session.with_transaction(save)

    async def claim_remediation(self):
        now = datetime.now(timezone.utc)
        async def save(session):
            remediation = await self.db.remediations.find_one_and_update(
                {'verification_status': 'queued'},
                {'$set': {'verification_status': 'testing', 'updated_at': now,
                          'verification_started_at': now, 'worker_id': self.worker_id,
                          'claim_expires_at': now + timedelta(seconds=self.lease_seconds)}},
                sort=[('updated_at', 1), ('_id', 1)], return_document=ReturnDocument.AFTER,
                session=session)
            if remediation:
                await self.db.activity_events.insert_one(
                    remediation_event(remediation, 'remediation_verification_started',
                                      'Remediation verification started', now, {}), session=session)
            return remediation
        async with await self.db.client.start_session() as session:
            return await session.with_transaction(save)

    async def claim_pull_request(self):
        now = datetime.now(timezone.utc)
        record = await self.db.pull_requests.find_one_and_update(
            {'status': 'queued'},
            {'$set': {'status': 'creating', 'worker_id': self.worker_id,
                      'claim_expires_at': now + timedelta(seconds=self.lease_seconds),
                      'updated_at': now}},
            sort=[('created_at', 1), ('_id', 1)], return_document=ReturnDocument.AFTER,
        )
        return record

    async def claim_pull_request_reverification(self):
        now = datetime.now(timezone.utc)
        record = await self.db.pull_requests.find_one_and_update(
            {'status': 'open', 'reverification_status': 'queued',
             'commit_sha': {'$type': 'string'}},
            {'$set': {'reverification_status': 'testing',
                      'reverification_worker_id': self.worker_id,
                      'reverification_claim_expires_at': now + timedelta(seconds=self.lease_seconds),
                      'updated_at': now}},
            sort=[('updated_at', 1), ('_id', 1)], return_document=ReturnDocument.AFTER,
        )
        if record:
            await self.db.activity_events.insert_one({
                '_id': ObjectId(), 'organization_id': record['organization_id'],
                'project_id': record['project_id'], 'actor_id': 'security-worker',
                'event_type': 'remediation_reverification_started', 'entity_type': 'pull_request',
                'entity_id': str(record['_id']), 'message': 'Pull request re-verification started',
                'metadata': {'commit_sha': record['commit_sha']}, 'created_at': now,
            })
        return record

    def owned_pull_request(self, record):
        return {'_id': record['_id'], 'organization_id': record['organization_id'],
                'status': 'creating', 'worker_id': self.worker_id}

    def owned_pull_request_reverification(self, record):
        return {'_id': record['_id'], 'organization_id': record['organization_id'],
                'status': 'open', 'commit_sha': record['commit_sha'],
                'reverification_status': 'testing', 'reverification_worker_id': self.worker_id}

    async def load_pull_request_context(self, record):
        scope = OrganizationScope(record['organization_id'])
        remediation = await self.db.remediations.find_one(scope.query(
            _id=object_id(record['remediation_id']), status='approved', verification_status='verified'))
        finding = await self.db.findings.find_one(scope.query(_id=object_id(record['finding_id'])))
        asset = await self.db.assets.find_one(scope.query(_id=object_id(record['asset_id']), status='active'))
        integration = await self.db.github_integrations.find_one(scope.query(
            installation_id=record['installation_id'], status='active'))
        repository = await self.db.github_repositories.find_one(scope.query(
            repository_id=record['repository_id'], authorized=True, connection_status='active'))
        if not all((remediation, finding, asset, integration, repository)):
            raise ValueError('Pull request authorization context is unavailable')
        link = asset.get('source_control') or {}
        if (link.get('integration_id') != str(integration['_id']) or
                link.get('repository_id') != repository['repository_id'] or
                link.get('repository_full_name') != record['repository_full_name'] or
                repository.get('integration_id') != str(integration['_id'])):
            raise ValueError('Pull request repository authorization changed')
        from security_engine.patch_integrity import assert_verified_patch
        digest = assert_verified_patch(remediation)
        source = remediation.get('verified_source_commit')
        finding_source = (finding.get('source_metadata') or {}).get('commit_sha')
        if (source != remediation.get('source_commit') or source != finding_source or
                source != record.get('expected_source_commit') or
                digest != record.get('verified_patch_sha256')):
            raise ValueError('Pull request source or patch integrity changed')
        project = await self.db.projects.find_one(
            scope.query(_id=object_id(record['project_id']), status='active'))
        if not project or asset.get('project_id') != str(project['_id']):
            raise ValueError('Pull request project authorization changed')
        return remediation, finding, asset, integration, repository

    async def renew_pull_request_claim(self, record):
        now = datetime.now(timezone.utc)
        result = await self.db.pull_requests.update_one(
            {**self.owned_pull_request(record), 'claim_expires_at': {'$gt': now}},
            {'$set': {'claim_expires_at': now + timedelta(seconds=self.lease_seconds)}})
        if not result.matched_count:
            raise RunChanged('Pull request operation is no longer owned by this worker')

    async def complete_pull_request(self, record, commit_sha, pull_request):
        now = datetime.now(timezone.utc)
        async def save(session):
            update = await self.db.pull_requests.update_one(
                self.owned_pull_request(record),
                {'$set': {'status': 'open', 'commit_sha': commit_sha,
                          'pr_number': pull_request['number'], 'pr_url': pull_request['url'],
                          'checks_status': 'unknown', 'checks': {},
                          'reverification_status': 'queued', 'reverification_result': None,
                          'readiness_status': 'waiting',
                          'updated_at': now, 'error': None},
                 '$unset': {'worker_id': '', 'claim_expires_at': ''}}, session=session)
            if update.modified_count != 1:
                raise RunChanged('Pull request operation is no longer owned by this worker')
            await self.db.activity_events.insert_one(
                {'_id': ObjectId(), 'organization_id': record['organization_id'],
                 'project_id': record['project_id'], 'actor_id': 'security-worker',
                 'event_type': 'pull_request_created', 'entity_type': 'pull_request',
                 'entity_id': str(record['_id']), 'message': 'Pull request created',
                 'metadata': {'pr_number': pull_request['number'], 'commit_sha': commit_sha},
                 'created_at': now}, session=session)
            await self.db.findings.update_one(
                {'_id': object_id(record['finding_id']), 'organization_id': record['organization_id'],
                 'status': {'$ne': 'resolved'}},
                {'$set': {'status': 'remediating', 'updated_at': now}}, session=session)
        async with await self.db.client.start_session() as session:
            await session.with_transaction(save)

    async def fail_pull_request(self, record, reason):
        now = datetime.now(timezone.utc)
        async def save(session):
            update = await self.db.pull_requests.update_one(
                self.owned_pull_request(record),
                {'$set': {'status': 'failed', 'error': reason, 'updated_at': now},
                 '$unset': {'worker_id': '', 'claim_expires_at': ''}}, session=session)
            if update.modified_count:
                await self.db.activity_events.insert_one(
                    {'_id': ObjectId(), 'organization_id': record['organization_id'],
                     'project_id': record['project_id'], 'actor_id': 'security-worker',
                     'event_type': 'pull_request_failed', 'entity_type': 'pull_request',
                     'entity_id': str(record['_id']), 'message': 'Pull request creation failed',
                     'metadata': {'reason': reason}, 'created_at': now}, session=session)
        async with await self.db.client.start_session() as session:
            await session.with_transaction(save)

    async def load_pull_request_reverification_context(self, record):
        context = await self.load_pull_request_context(record)
        remediation, finding, asset, integration, repository = context
        scan = await self.db.scanner_results.find_one({
            'organization_id': record['organization_id'],
            'security_run_id': remediation.get('source_security_run_id'),
            'asset_id': record['asset_id'],
        })
        if not scan:
            raise ValueError('Original scanner evidence is unavailable')
        before = ScannerResult.model_validate({key: scan[key] for key in
            ('scanner', 'scanner_version', 'configuration', 'started_at', 'completed_at',
             'exit_code', 'results', 'errors', 'metadata') if key in scan})
        return remediation, finding, integration, repository, before

    async def complete_pull_request_reverification(self, record, result):
        result = VerificationResult.model_validate(result)
        now = result.verified_at
        verified = result.status == 'verified'
        async def save(session):
            current = await self.db.pull_requests.find_one(
                self.owned_pull_request_reverification(record), session=session)
            if not current:
                raise RunChanged('PR re-verification is no longer owned by this worker')
            readiness = ('ready_for_review' if verified and current.get('checks_status') == 'passing'
                         else 'waiting')
            update = await self.db.pull_requests.update_one(
                self.owned_pull_request_reverification(record),
                {'$set': {'reverification_status': result.status,
                          'reverification_result': result.model_dump(mode='python'),
                          'readiness_status': readiness, 'updated_at': now},
                 '$unset': {'reverification_worker_id': '',
                            'reverification_claim_expires_at': ''}}, session=session)
            if update.modified_count != 1:
                raise RunChanged('PR re-verification is no longer owned by this worker')
            await self.db.activity_events.insert_one({
                '_id': ObjectId(), 'organization_id': record['organization_id'],
                'project_id': record['project_id'], 'actor_id': 'security-worker',
                'event_type': ('remediation_reverification_passed' if verified
                               else 'remediation_reverification_failed'),
                'entity_type': 'pull_request', 'entity_id': str(record['_id']),
                'message': ('Pull request re-verification passed' if verified
                            else 'Pull request re-verification failed'),
                'metadata': {'commit_sha': record['commit_sha'],
                             'new_findings_count': result.new_findings_count,
                             'new_equal_or_higher_findings_count': result.new_equal_or_higher_findings_count},
                'created_at': now}, session=session)
        async with await self.db.client.start_session() as session:
            await session.with_transaction(save)

    async def fail_pull_request_reverification(self, record, reason):
        now = datetime.now(timezone.utc)
        async def save(session):
            update = await self.db.pull_requests.update_one(
                self.owned_pull_request_reverification(record),
                {'$set': {'reverification_status': 'inconclusive', 'readiness_status': 'waiting',
                          'error': reason, 'updated_at': now},
                 '$unset': {'reverification_worker_id': '', 'reverification_claim_expires_at': ''}},
                session=session)
            if update.modified_count:
                await self.db.activity_events.insert_one({
                    '_id': ObjectId(), 'organization_id': record['organization_id'],
                    'project_id': record['project_id'], 'actor_id': 'security-worker',
                    'event_type': 'remediation_reverification_failed', 'entity_type': 'pull_request',
                    'entity_id': str(record['_id']), 'message': 'Pull request re-verification failed',
                    'metadata': {'commit_sha': record['commit_sha'], 'reason': reason},
                    'created_at': now}, session=session)
            return update.modified_count
        async with await self.db.client.start_session() as session:
            return await session.with_transaction(save)

    def owned_remediation(self, remediation):
        return {'_id': remediation['_id'], 'organization_id': remediation['organization_id'],
                'verification_status': 'testing', 'worker_id': self.worker_id}

    async def heartbeat_remediation(self, remediation):
        now = datetime.now(timezone.utc)
        result = await self.db.remediations.update_one(
            self.owned_remediation(remediation),
            {'$set': {'updated_at': now,
                      'claim_expires_at': now + timedelta(seconds=self.lease_seconds)}})
        if result.modified_count != 1:
            raise RunChanged('Remediation is no longer owned by this worker')

    async def load_remediation_context(self, remediation, grants):
        scope = OrganizationScope(remediation['organization_id'])
        project = await self.db.projects.find_one(scope.query(_id=object_id(remediation['project_id'])))
        asset = await self.db.assets.find_one(scope.query(_id=object_id(remediation.get('asset_id'))))
        finding = await self.db.findings.find_one(scope.query(_id=object_id(remediation['finding_id'])))
        if not project or not asset or not finding:
            raise ValueError('Remediation source relationship is unavailable')
        if (str(asset.get('project_id')) != remediation['project_id'] or
                str(finding.get('project_id')) != remediation['project_id'] or
                str(finding.get('asset_id')) != str(asset['_id'])):
            raise ValueError('Remediation source relationship is invalid')
        source_commit = remediation.get('source_commit')
        finding_commit = (finding.get('source_metadata') or {}).get('commit_sha')
        if not source_commit or source_commit != finding_commit:
            raise ValueError('Remediation source revision is unavailable or stale')
        proposal = (RemediationProposal.model_validate(remediation['proposal'])
                    if remediation.get('proposal') is not None else None)
        source_run_id = remediation.get('source_security_run_id')
        scan = await self.db.scanner_results.find_one(scope.query(
            security_run_id=source_run_id, asset_id=str(asset['_id'])))
        if not scan:
            raise ValueError('Original scanner evidence is unavailable')
        before = ScannerResult.model_validate({key: scan[key] for key in
            ('scanner', 'scanner_version', 'configuration', 'started_at', 'completed_at',
             'exit_code', 'results', 'errors', 'metadata') if key in scan})
        from security_engine.policy import authorize_repository
        snapshot = authorize_repository(scope, project, asset, grants)
        return snapshot, finding, proposal, before

    async def save_remediation_proposal(self, remediation, proposal, metadata):
        proposal = RemediationProposal.model_validate(proposal)
        now = datetime.now(timezone.utc)
        result = await self.db.remediations.update_one(
            self.owned_remediation(remediation),
            {'$set': {'proposal': proposal.model_dump(mode='python'),
                      'patch_format': 'unified_diff',
                      'proposal_agent_metadata': metadata, 'updated_at': now,
                      'claim_expires_at': now + timedelta(seconds=self.lease_seconds)}})
        if result.modified_count != 1:
            raise RunChanged('Remediation changed before its proposal was stored')
        remediation['proposal'] = proposal.model_dump(mode='python')
        return proposal

    async def complete_remediation(self, remediation, result, after_scan):
        result = VerificationResult.model_validate(result)
        now = result.verified_at
        async def save(session):
            raw = after_scan.model_dump(mode='python') | {
                '_id': ObjectId(), 'organization_id': remediation['organization_id'],
                'project_id': remediation['project_id'], 'asset_id': remediation['asset_id'],
                'remediation_id': str(remediation['_id']), 'phase': 'after_patch', 'created_at': now}
            await self.db.scanner_results.insert_one(raw, session=session)
            verified = result.status == 'verified'
            proposal_data = remediation.get('proposal')
            proposal = RemediationProposal.model_validate(proposal_data) if proposal_data else None
            integrity = ({'verified_patch': proposal.patch,
                          'verified_patch_sha256': patch_sha256(proposal.patch),
                          'verified_source_commit': remediation['source_commit'],
                          'verified_affected_files': proposal.affected_files,
                          'source_integrity_status': 'verified'}
                         if verified and proposal else {})
            unset = {'worker_id': '', 'claim_expires_at': ''}
            if not verified:
                unset.update({'verified_patch': '', 'verified_patch_sha256': '',
                              'verified_source_commit': '', 'verified_affected_files': '',
                              'source_integrity_status': ''})
            update = await self.db.remediations.update_one(
                self.owned_remediation(remediation),
                {'$set': {'verification_status': result.status,
                          'verification_result': result.model_dump(mode='python'),
                          'status': 'awaiting_approval' if verified else 'failed', **integrity,
                          'verified_at': now, 'updated_at': now},
                 '$unset': unset}, session=session)
            if update.modified_count != 1:
                raise RunChanged('Remediation changed before verification was committed')
            event_type = 'remediation_verified' if verified else 'remediation_failed'
            await self.db.activity_events.insert_one(
                remediation_event(remediation, event_type,
                                  'Remediation verified' if verified else 'Remediation verification failed',
                                  now, {'verification_status': result.status,
                                        'new_findings_count': result.new_findings_count,
                                        'new_equal_or_higher_findings_count': result.new_equal_or_higher_findings_count}),
                session=session)
        async with await self.db.client.start_session() as session:
            await session.with_transaction(save)

    async def fail_remediation(self, remediation, verification_status, reason):
        now = datetime.now(timezone.utc)
        result = VerificationResult(
            remediation_id=str(remediation['_id']), status=verification_status,
            original_finding_present=None, new_findings_count=0,
            new_equal_or_higher_findings_count=0, before_finding_count=0,
            after_finding_count=0, before_severity_counts={}, after_severity_counts={},
            scanner='semgrep', scanner_version='unavailable', summary=reason, verified_at=now)
        async def save(session):
            update = await self.db.remediations.update_one(
                self.owned_remediation(remediation),
                {'$set': {'verification_status': verification_status,
                          'verification_result': result.model_dump(mode='python'),
                          'status': 'failed', 'verified_at': now, 'updated_at': now},
                 '$unset': {'worker_id': '', 'claim_expires_at': '', 'verified_patch': '',
                            'verified_patch_sha256': '', 'verified_source_commit': '',
                            'verified_affected_files': '', 'source_integrity_status': ''}}, session=session)
            if update.modified_count:
                await self.db.activity_events.insert_one(
                    remediation_event(remediation, 'remediation_failed',
                                      'Remediation verification failed', now,
                                      {'verification_status': verification_status, 'reason': reason}), session=session)
        async with await self.db.client.start_session() as session:
            await session.with_transaction(save)

    def owned(self, run):
        return {'_id': run['_id'], 'organization_id': run['organization_id'],
                'status': 'running', 'worker_id': self.worker_id}

    async def heartbeat(self, run, progress):
        now = datetime.now(timezone.utc)
        result = await self.db.security_runs.update_one(
            self.owned(run), {'$set': {'progress': progress, 'updated_at': now,
                                       'claim_expires_at': now + timedelta(seconds=self.lease_seconds)}})
        if result.modified_count != 1:
            raise RunChanged('Run was cancelled or is no longer owned by this worker')

    async def is_cancelled(self, run):
        current = await self.db.security_runs.find_one({'_id': run['_id']}, {'status': 1})
        return not current or current.get('status') == 'cancelled'

    async def load_authorized_context(self, run, grants):
        scope = OrganizationScope(run['organization_id'])
        project = await self.db.projects.find_one(scope.query(_id=object_id(run['project_id'])))
        if not project:
            raise ValueError('Run project is unavailable')
        ids = run.get('asset_ids') or []
        if len(ids) != 1:
            raise ValueError('V1 runs require exactly one repository asset')
        asset = await self.db.assets.find_one(scope.query(_id=object_id(ids[0])))
        if not asset:
            raise ValueError('Run repository asset is unavailable')
        user = await self.db.users.find_one({'_id': {'$in': [run.get('requested_by'), object_id(run.get('requested_by'))]}})
        membership, state = membership_value(user or {})
        if (not user or user.get('status', 'active') != 'active' or user.get('role') not in {'admin', 'superadmin'} or
                (user.get('role') != 'superadmin' and (state != 'assigned' or str(membership) != run['organization_id']))):
            raise ValueError('Run requester is no longer authorized')
        from security_engine.policy import authorize_repository
        return scope, project, asset, authorize_repository(scope, project, asset, grants)

    async def complete(self, run, scanner_result, candidates, summary):
        now = datetime.now(timezone.utc)
        async def save(session):
            for candidate in candidates:
                finding = candidate_to_document(candidate, now)
                await self.db.findings.update_one(
                    {'organization_id': run['organization_id'], 'fingerprint': finding['fingerprint']},
                    {'$set': {key: value for key, value in finding.items() if key not in {'_id', 'created_at', 'first_detected_at', 'status', 'security_run_id', 'security_run_ids'}},
                     '$addToSet': {'security_run_ids': finding['security_run_id']},
                     '$setOnInsert': {'_id': finding['_id'], 'created_at': now,
                                      'first_detected_at': now, 'status': 'new'}},
                    upsert=True, session=session)
            raw = scanner_result.model_dump(mode='python') | {
                '_id': ObjectId(), 'organization_id': run['organization_id'],
                'project_id': run['project_id'], 'asset_id': run['asset_ids'][0],
                'security_run_id': str(run['_id']), 'created_at': now}
            await self.db.scanner_results.insert_one(raw, session=session)
            update = await self.db.security_runs.update_one(
                self.owned(run), {'$set': {'status': 'completed', 'progress': 100, 'summary': summary,
                                           'commit_sha': summary['commit_sha'], 'scanner': scanner_result.scanner,
                                           'scanner_version': scanner_result.scanner_version,
                                           'analysis_mode': summary.get('analysis_mode', 'deterministic_only'),
                                           'completed_at': now, 'updated_at': now,
                                           'error': None}, '$unset': {'worker_id': '', 'claim_expires_at': ''}}, session=session)
            if update.modified_count != 1:
                raise RunChanged('Run was cancelled before results were committed')
            await self.db.activity_events.insert_many([
                event(run, 'findings_created', f'{len(candidates)} findings created', now,
                      {'count': len(candidates)}),
                event(run, 'security_run_completed', 'Security run completed', now, summary)], session=session)
        async with await self.db.client.start_session() as session:
            await session.with_transaction(save)

    async def fail(self, run, reason):
        now = datetime.now(timezone.utc)
        async def save(session):
            update = await self.db.security_runs.update_one(
                self.owned(run), {'$set': {'status': 'failed', 'completed_at': now, 'updated_at': now,
                                           'error': reason, 'progress': min(int(run.get('progress', 5)), 99)},
                                  '$unset': {'worker_id': '', 'claim_expires_at': ''}}, session=session)
            if update.modified_count:
                await self.db.activity_events.insert_one(
                    event(run, 'security_run_failed', 'Security run failed', now, {'reason': reason}), session=session)
        async with await self.db.client.start_session() as session:
            await session.with_transaction(save)


def event(run, event_type, message, now, metadata):
    return {'_id': ObjectId(), 'organization_id': run['organization_id'], 'project_id': run['project_id'],
            'actor_id': 'security-worker', 'event_type': event_type, 'entity_type': 'security_run',
            'entity_id': str(run['_id']), 'message': message, 'metadata': metadata, 'created_at': now}


def remediation_event(remediation, event_type, message, now, metadata):
    return {'_id': ObjectId(), 'organization_id': remediation['organization_id'],
            'project_id': remediation['project_id'], 'actor_id': 'security-worker',
            'event_type': event_type, 'entity_type': 'remediation',
            'entity_id': str(remediation['_id']), 'message': message,
            'metadata': metadata, 'created_at': now}


def candidate_to_document(candidate, now):
    data = candidate.model_dump(mode='json')
    location = f"{data.pop('file_path')}:{data.pop('start_line')}-{data.pop('end_line')}"
    fingerprint = data.pop('fingerprint')
    rule_id = data.pop('rule_id')
    repository = data.pop('repository'); branch = data.pop('branch'); commit = data.pop('commit_sha')
    analysis = data.pop('analysis')
    data.pop('scanner_version')
    data['source'] = data.pop('scanner')
    data['last_security_run_id'] = data['security_run_id']
    data['security_run_ids'] = [data['security_run_id']]
    document = {'_id': ObjectId(), **data, 'fingerprint': fingerprint, 'location': location,
                'affected_component': location.split(':', 1)[0], 'cvss': None, 'references': [],
                'status': 'new', 'first_detected_at': now, 'last_detected_at': now,
                'created_at': now, 'updated_at': now,
                'source_metadata': {'rule_id': rule_id, 'repository': repository, 'branch': branch,
                                    'commit_sha': commit,
                                    'analysis_mode': 'agent_enriched' if analysis else 'deterministic_only'}}
    if analysis:
        document['source_metadata']['agent_analysis'] = analysis
    FindingResponse.model_validate({'id': str(document['_id']), **document})
    return document
