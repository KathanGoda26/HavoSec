"""Policy and durable admission for the fixed, side-effect-free fixture adapter."""
import hashlib
import json
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from bson import ObjectId
from fastapi import HTTPException
from mission_orchestration.plan import APPROVAL_REQUIRED, ASSESSMENT_V1, FIXTURE_SCAN_MISSION, PLAN_VERSION, TaskResult
from mission_orchestration.storage import OrchestrationStore, utc_now
from utils.auth import possible_ids, serialize_user


TASKS = {task.id: task for task in ASSESSMENT_V1}
POLICY_DENIED = 'FixturePolicyDenied'
ATTEMPT_BUSY = 'FixtureAttemptBusy'


class FixtureRejected(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def asset_scope_digest(asset):
    source = asset.get('source_control') or {}
    return digest({'id': str(asset['_id']), 'target': asset['target'],
                   'source_control': {key: source.get(key) for key in (
                       'provider', 'integration_id', 'repository_id', 'repository_full_name',
                       'default_branch', 'connection_status',
                   )}})


def execution_view(value):
    if isinstance(value, dict):
        return {key: execution_view(item) for key, item in value.items()}
    if isinstance(value, list):
        return [execution_view(item) for item in value]
    if isinstance(value, datetime) and value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


class FixtureGateway:
    def __init__(self, db):
        self.db = db

    async def transaction(self, operation):
        async with await self.db.client.start_session() as session:
            return await session.with_transaction(operation)

    async def audit(self, ref, task_id, event_type, details, session):
        await self.db.mission_execution_events.insert_one({
            'organization_id': ref.organization_id, 'mission_id': ref.mission_id,
            'operation': task_id, 'type': event_type, 'details': details, 'created_at': utc_now(),
        }, session=session)

    async def can_manage(self, actor_id, organization_id, session):
        if not isinstance(actor_id, str) or not actor_id:
            return False
        account = await self.db.users.find_one({'_id': {'$in': possible_ids(actor_id)}}, session=session)
        if not account:
            return False
        user = serialize_user(account, 'users')
        return user['status'] == 'active' and (
            user['role'] == 'superadmin'
            or (user['role'] == 'admin' and user['organizationId'] == organization_id)
        )

    async def policy(self, mission, session):
        organization_id = mission['organization_id']
        ids = [organization_id, mission.get('project_id'), mission.get('asset_id')]
        if (mission.get('mission_type') not in {'repository_assessment', FIXTURE_SCAN_MISSION}
                or not all(ObjectId.is_valid(i) for i in ids)):
            return 'deny', 'invalid_mission_scope', None

        organization = await self.db.client_companies.find_one({'_id': ObjectId(organization_id)}, session=session)
        if not organization or organization.get('status', 'active') != 'active' or organization.get('isActive') is False:
            return 'deny', 'organization_inactive', None
        if not await self.can_manage(mission.get('requested_by'), organization_id, session):
            return 'deny', 'requester_not_authorized', None

        scope = {'organization_id': organization_id, 'status': 'active'}
        project = await self.db.projects.find_one({**scope, '_id': ObjectId(mission['project_id'])}, session=session)
        asset = await self.db.assets.find_one({
            **scope, '_id': ObjectId(mission['asset_id']), 'project_id': mission['project_id'], 'type': 'repository',
        }, session=session)
        if not project or not asset or not isinstance(asset.get('target'), str):
            return 'deny', 'target_out_of_scope', None
        target = asset_scope_digest(asset)
        if mission.get('fixture_scope_digest', target) != target:
            return 'deny', 'target_changed', target

        modes = organization.get('mission_policy', {})
        mode = modes.get('fixture', 'allow') if isinstance(modes, dict) else None
        if mode not in ('allow', 'deny', 'require_approval'):
            return 'deny', 'unknown_policy', target
        return mode, 'organization_policy', target

    @staticmethod
    def ready(mission, ref, task_id):
        progress = mission.get('orchestration', {})
        return (mission['status'] in ('running', 'awaiting_approval')
                and not mission.get('cancel_requested_at') and progress.get('slot') is True
                and progress.get('workflow_id') == ref.workflow_id and progress.get('current_task') == task_id)

    async def begin(self, request, attempt_id, attempt):
        task = TASKS.get(request.task_id)
        if task is None or task.capability != 'fixture':
            raise FixtureRejected(POLICY_DENIED)
        identity = OrchestrationStore.mission_query(request.mission)

        async def admit(session):
            mission = await self.db.missions.find_one(identity, session=session)
            if not mission or not self.ready(mission, request.mission, task.id):
                return POLICY_DENIED, None
            path = f'fixture_actions.{task.id}'
            record = mission.get('fixture_actions', {}).get(task.id)
            decision, reason, target = await self.policy(mission, session)
            binding = {'organization_id': request.mission.organization_id,
                       'mission_id': request.mission.mission_id, 'plan_version': PLAN_VERSION,
                       'operation': task.id, 'inputs': task.inputs, 'target_digest': target}
            if mission['mission_type'] == FIXTURE_SCAN_MISSION:
                binding.update(mission_type=FIXTURE_SCAN_MISSION, fixture_commit=mission.get('fixture_commit'))
            action_digest = digest(binding)
            if mission.get('mission_type') != request.mission.mission_type:
                decision, reason = 'deny', 'mission_type_changed'
            if record is None:
                record = {'digest': action_digest, 'plan_version': PLAN_VERSION, 'operation': task.id,
                          'attempts': [], 'approval': None}
            elif decision != 'deny' and record['digest'] != action_digest:
                decision, reason = 'deny', 'action_changed'

            now = utc_now()
            approval = record['approval']
            if decision == 'require_approval':
                valid = approval and not approval.get('revoked_at') and (
                    approval['action_digest'] == action_digest
                    and approval.get('consumed_for', action_digest) == action_digest
                    and approval['expires_at'].replace(tzinfo=now.tzinfo) > now
                ) and await self.can_manage(approval['approver_id'], request.mission.organization_id, session)
                if valid:
                    decision, reason = 'allow', 'approved'
                else:
                    reason = 'approval_required'

            prior = record.get('decision')
            updated = {'outcome': decision, 'reason': reason}
            changed = prior != updated
            if changed:
                record['decision'] = updated
                record['decided_at'] = now
            changes = {path: record}
            if target and 'fixture_scope_digest' not in mission and decision != 'deny':
                # Missions queued with Phase 2 did not have a snapshot. Only the fixture can bind it once.
                changes['fixture_scope_digest'] = target

            error = None
            result = None
            if decision == 'deny':
                error = POLICY_DENIED
            elif decision == 'require_approval':
                error = APPROVAL_REQUIRED
            elif record.get('result'):
                result = TaskResult(**record['result'])
            else:
                active = record['attempts'][-1] if record['attempts'] else None
                if active and active['state'] == 'running':
                    if active['id'] == attempt_id:
                        return None, None
                    if active['lease_expires_at'].replace(tzinfo=now.tzinfo) > now:
                        return ATTEMPT_BUSY, None
                    active.update(state='interrupted', finished_at=now)
                    changed = True
                if len(record['attempts']) >= task.max_attempts:
                    error = POLICY_DENIED
                    record.update(decision={'outcome': 'deny', 'reason': 'attempt_limit'}, decided_at=now)
                    changed = True
                else:
                    if reason == 'approved':
                        approval['consumed_for'] = action_digest
                        approval.setdefault('consumed_at', now)
                    record['attempts'].append({'id': attempt_id, 'number': attempt, 'state': 'running',
                                               'started_at': now, 'lease_expires_at': now + timedelta(seconds=4)})
                    changes['status'] = 'running'

            if changed or len(changes) > 1:
                await self.db.missions.update_one(identity, {'$set': changes}, session=session)
            if prior != record['decision']:
                await self.audit(request.mission, task.id, 'policy_decision', {
                    **record['decision'], 'action_digest': record['digest'], 'plan_version': PLAN_VERSION,
                }, session)
            return error, result

        error, result = await self.transaction(admit)
        if error:
            raise FixtureRejected(error)
        return result

    async def keep_alive(self, request, attempt_id):
        path = f'fixture_actions.{request.task_id}.attempts'
        filters = {**OrchestrationStore.mission_query(request.mission), 'status': 'running',
                   'cancel_requested_at': None, 'orchestration.slot': True,
                   'orchestration.current_task': request.task_id,
                   path: {'$elemMatch': {'id': attempt_id, 'state': 'running'}}}
        updated = await self.db.missions.update_one(filters, {'$set': {
            f'{path}.$.lease_expires_at': utc_now() + timedelta(seconds=4),
        }})
        if not updated.matched_count:
            raise FixtureRejected(POLICY_DENIED)

    async def finish(self, request, attempt_id, state, result=None, report=None):
        path = f'fixture_actions.{request.task_id}'
        identity = OrchestrationStore.mission_query(request.mission)
        filters = {**identity, f'{path}.attempts': {'$elemMatch': {'id': attempt_id, 'state': 'running'}}}
        changes = {f'{path}.attempts.$.state': state, f'{path}.attempts.$.finished_at': utc_now()}
        if result is not None:
            changes[f'{path}.result'] = asdict(result)
            filters.update(status='running', cancel_requested_at=None,
                           **{'orchestration.slot': True, 'orchestration.current_task': request.task_id})
        if report is not None:
            changes['assessment_report'] = report
        updated = await self.db.missions.update_one(filters, {'$set': changes})
        if result is not None and not updated.matched_count:
            raise FixtureRejected(POLICY_DENIED)

    async def change_approval(self, ref, task_id, actor_id, action_digest, revoke_id=None):
        if task_id not in TASKS:
            raise HTTPException(404, 'Action not found')
        identity = OrchestrationStore.mission_query(ref)
        path = f'fixture_actions.{task_id}'

        async def change(session):
            mission = await self.db.missions.find_one(identity, session=session)
            record = mission and mission.get('fixture_actions', {}).get(task_id)
            if not record:
                raise HTTPException(404, 'Action not found')
            if not await self.can_manage(actor_id, ref.organization_id, session):
                raise HTTPException(403, 'Insufficient permissions')
            if record['digest'] != action_digest:
                raise HTTPException(409, 'Action has changed')
            prior = record.get('approval')
            now = utc_now()
            if revoke_id:
                if not prior or prior['id'] != revoke_id:
                    raise HTTPException(404, 'Approval not found')
                if prior.get('revoked_at'):
                    return prior
                approval = {**prior, 'revoked_at': now, 'revoked_by': actor_id}
            else:
                if not self.ready(mission, ref, task_id) or record['decision']['outcome'] != 'require_approval':
                    raise HTTPException(409, 'Action is not waiting for approval')
                mode, _, target = await self.policy(mission, session)
                if mode != 'require_approval' or mission.get('fixture_scope_digest') != target:
                    raise HTTPException(409, 'Action is no longer eligible for approval')
                if prior and not prior.get('revoked_at') and prior['expires_at'].replace(tzinfo=now.tzinfo) > now:
                    return prior
                approval = {'id': uuid4().hex, 'approver_id': actor_id, 'action_digest': action_digest,
                            'granted_at': now, 'expires_at': now + timedelta(minutes=15), 'max_consumptions': 1}
            await self.db.missions.update_one(identity, {'$set': {f'{path}.approval': approval}}, session=session)
            await self.audit(ref, task_id, 'approval_revoked' if revoke_id else 'approval_granted',
                             approval, session)
            return approval

        return await self.transaction(change)
