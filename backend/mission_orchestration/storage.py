from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from bson import ObjectId
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from mission_orchestration.plan import ProgressState, TERMINAL_STATUSES


def utc_now():
    return datetime.now(timezone.utc)


class OrchestrationStore:
    def __init__(self, db):
        self.db = db
        self.missions = db.missions
        self.outbox = db.mission_outbox

    async def check_indexes(self):
        indexes = await self.missions.index_information()
        slot = indexes.get('org_mission_slot', {})
        if (slot.get('key') != [('organization_id', 1)] or not slot.get('unique')
                or slot.get('partialFilterExpression') != {'orchestration.slot': True}):
            raise RuntimeError('Apply domain indexes before starting mission orchestration')

    @staticmethod
    def mission_query(mission):
        return {'_id': ObjectId(mission.mission_id), 'organization_id': mission.organization_id}

    async def get_mission(self, mission):
        document = await self.missions.find_one(self.mission_query(mission))
        if document is None:
            raise ValueError('Mission record is unavailable')
        return document

    @staticmethod
    def state(document):
        return ProgressState(document['status'], bool(document.get('cancel_requested_at')),
                             document.get('orchestration', {}).get('slot', False))

    async def acquire_slot(self, mission):
        try:
            document = await self.missions.find_one_and_update(
                {**self.mission_query(mission), 'status': 'queued',
                 'orchestration.workflow_id': mission.workflow_id, 'cancel_requested_at': None},
                {'$set': {'orchestration.slot': True}},
                return_document=ReturnDocument.AFTER,
            )
        except DuplicateKeyError:
            # The partial unique index admits one mission per organization.
            document = None
        return self.state(document or await self.get_mission(mission))

    async def project(self, event):
        identity = self.mission_query(event.mission)
        while True:
            current = await self.get_mission(event.mission)
            progress = current.get('orchestration') or {}
            current_version = progress.get('version', 0)
            if current_version >= event.version or current['status'] in TERMINAL_STATUSES:
                return self.state(current)
            if current_version != event.version - 1:
                raise ValueError('Mission progress event is out of sequence')
            if current['status'] not in {'queued', 'running', 'awaiting_approval'} or (
                progress.get('workflow_id', event.mission.workflow_id) != event.mission.workflow_id
            ):
                raise ValueError('Mission does not belong to this workflow')
            if event.status not in {'running', 'awaiting_approval', *TERMINAL_STATUSES} and (
                event.status != 'queued' or event.version != 1 or current['status'] != 'queued'
            ):
                raise ValueError('Invalid mission progress transition')
            if event.status in {'running', 'awaiting_approval'} and not progress.get('slot'):
                raise ValueError('Mission does not hold an organization slot')

            status = event.status
            cancellation = current.get('cancel_requested_at')
            if cancellation and status in TERMINAL_STATUSES:
                status = 'cancelled'
            changes = {'$set': {
                'status': status,
                'updated_at': utc_now(),
                'orchestration.workflow_id': event.mission.workflow_id,
                'orchestration.version': event.version,
                'orchestration.total_tasks': event.total_tasks,
                'orchestration.current_task': event.current_task,
                'orchestration.completed': [asdict(task) for task in event.completed],
            }}
            if status in TERMINAL_STATUSES:
                changes['$unset'] = {'orchestration.slot': ''}
            updated = await self.missions.find_one_and_update(
                {**identity, 'status': current['status'],
                 'orchestration.version': current_version or None, 'cancel_requested_at': cancellation},
                changes, return_document=ReturnDocument.AFTER,
            )
            if updated is not None:
                return self.state(updated)

    async def claim_command(self):
        now = utc_now()
        return await self.outbox.find_one_and_update(
            {'status': 'pending', 'type': {'$in': ['start_mission', 'cancel_mission']},
             '$or': [{'available_at': None}, {'available_at': {'$lte': now}}]},
            {'$set': {'lease_token': uuid4().hex, 'available_at': now + timedelta(seconds=30)},
             '$inc': {'attempts': 1}},
            sort=[('available_at', 1), ('created_at', 1), ('_id', 1)], return_document=ReturnDocument.AFTER,
        )

    async def deliver_command(self, command, workflow_id):
        await self.finish_command(command, {
            '$set': {'status': 'delivered', 'workflow_id': workflow_id, 'delivered_at': utc_now()},
            '$unset': {'lease_token': '', 'available_at': '', 'last_error': ''},
        })

    async def defer_command(self, command, error):
        delay = min(60, 2 ** min(command['attempts'], 6))
        await self.finish_command(command, {
            '$set': {'available_at': utc_now() + timedelta(seconds=delay), 'last_error': error},
            '$unset': {'lease_token': ''},
        })

    async def finish_command(self, command, changes):
        await self.outbox.update_one(
            {'_id': command['_id'], 'organization_id': command['organization_id'],
             'status': 'pending', 'lease_token': command['lease_token']}, changes,
        )
