from pymongo.errors import DuplicateKeyError
from datetime import datetime, timedelta, timezone
from bson import ObjectId
from pymongo import ReturnDocument


class PullRequestRepository:
    def __init__(self, db):
        self.db = db
        self.collection = db.pull_requests

    async def get_for_remediation(self, scope, remediation_id):
        return await self.collection.find_one(scope.query(remediation_id=remediation_id))

    async def create_idempotent(self, scope, document, event):
        async def save(session):
            await self.collection.insert_one(document, session=session)
            await self.db.activity_events.insert_one(event, session=session)
            return document
        try:
            async with await self.db.client.start_session() as session:
                return await session.with_transaction(save)
        except DuplicateKeyError:
            return await self.get_for_remediation(scope, document['remediation_id'])

    async def mark_remediation_stale(self, scope, remediation_id, now):
        await self.db.remediations.update_one(
            scope.query(_id=__import__('bson').ObjectId(remediation_id)),
            {'$set': {'source_integrity_status': 'stale', 'updated_at': now}},
        )

    async def apply_webhook_once(self, delivery_id, event_type, lookup, transform):
        now = datetime.now(timezone.utc)
        async def save(session):
            await self.db.github_webhook_deliveries.insert_one({
                '_id': delivery_id, 'event_type': event_type,
                'created_at': now, 'expires_at': now + timedelta(days=30),
            }, session=session)
            record = await self.collection.find_one(lookup, session=session)
            if not record:
                return None
            changes, event_metadata = transform(record)
            if not changes:
                return record
            changes['updated_at'] = now
            updated = await self.collection.find_one_and_update(
                {'_id': record['_id'], 'organization_id': record['organization_id']},
                {'$set': changes}, return_document=ReturnDocument.AFTER, session=session,
            )
            await self.db.activity_events.insert_one({
                '_id': ObjectId(), 'organization_id': record['organization_id'],
                'project_id': record['project_id'], 'actor_id': 'github-webhook',
                'event_type': event_metadata.pop('event_type'), 'entity_type': 'pull_request',
                'entity_id': str(record['_id']), 'message': event_metadata.pop('message'),
                'metadata': event_metadata, 'created_at': now,
            }, session=session)
            return updated
        try:
            async with await self.db.client.start_session() as session:
                return False, await session.with_transaction(save)
        except DuplicateKeyError:
            return True, None
