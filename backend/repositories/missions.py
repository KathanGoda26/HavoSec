from datetime import datetime, timezone

from bson import ObjectId
from fastapi import HTTPException
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from repositories.project_resources import ProjectResourceRepository
from mission_orchestration.governance import asset_scope_digest
from mission_orchestration.plan import TERMINAL_STATUSES


class MissionRepository(ProjectResourceRepository):
    def __init__(self, db):
        super().__init__(db, db.missions)

    async def get_by_key(self, scope, request_key):
        return await self.collection.find_one(scope.query(request_key=request_key))

    async def create_with_start(self, scope, mission):
        command = {
            '_id': mission['_id'],
            'organization_id': scope.organization_id,
            'mission_id': str(mission['_id']),
            'type': 'start_mission',
            'status': 'pending',
            'created_at': mission['created_at'],
        }

        async def save(session):
            await self.guard_project(scope, mission['project_id'], session)
            asset = await self.db.assets.find_one_and_update(
                scope.query(_id=ObjectId(mission['asset_id']), project_id=mission['project_id'],
                            status='active', type='repository'),
                {'$inc': {'_relationship_version': 1}}, session=session,
                return_document=ReturnDocument.AFTER,
            )
            if asset is None:
                raise HTTPException(409, 'Repository asset changed; refresh and retry')
            scoped_mission = {**mission, 'fixture_scope_digest': asset_scope_digest(asset)}
            await self.collection.insert_one(scoped_mission, session=session)
            await self.db.mission_outbox.insert_one(command, session=session)
            return scoped_mission

        try:
            async with await self.db.client.start_session() as session:
                return await session.with_transaction(save)
        except DuplicateKeyError:
            existing = await self.get_by_key(scope, mission['request_key'])
            if existing is None:
                raise
            return existing

    async def request_cancellation(self, scope, mission):
        query = scope.query(_id=mission['_id'])

        async def save(session):
            now = datetime.now(timezone.utc)
            updated = await self.collection.find_one_and_update(
                {**query, 'status': {'$nin': sorted(TERMINAL_STATUSES)}, 'cancel_requested_at': None},
                {'$set': {'cancel_requested_at': now, 'updated_at': now}}, session=session,
                return_document=ReturnDocument.AFTER,
            )
            if updated is None:
                return await self.collection.find_one(query, session=session)
            await self.db.mission_outbox.insert_one({
                '_id': f"cancel:{mission['_id']}",
                'organization_id': scope.organization_id,
                'mission_id': str(mission['_id']),
                'type': 'cancel_mission',
                'status': 'pending',
                'created_at': now,
            }, session=session)
            return updated

        async with await self.db.client.start_session() as session:
            return await session.with_transaction(save)
