"""Scoped storage for assets and runs; no execution or network target access.

Parent write guards participate in the transaction to serialize against archive.
A read-only parent check would allow a concurrent archive/create write skew.
"""
from fastapi import HTTPException
from pymongo import ReturnDocument
from core.ids import object_id


class ProjectResourceRepository:
    def __init__(self, db, collection):
        self.db = db
        self.collection = collection

    async def get(self, scope, resource_id):
        return await self.collection.find_one(scope.query(_id=object_id(resource_id)))

    async def list(self, scope, limit, offset, filters):
        query = scope.query(**filters)
        items = await self.collection.find(query).sort([('created_at', -1), ('_id', -1)]).skip(offset).limit(limit).to_list(length=limit)
        return items, await self.collection.count_documents(query)

    async def guard_project(self, scope, project_id, session):
        parent = await self.db.projects.find_one_and_update(
            scope.query(_id=object_id(project_id), status='active'),
            {'$inc': {'_relationship_version': 1}}, session=session, return_document=ReturnDocument.AFTER)
        if parent is None:
            raise HTTPException(409, 'Project is no longer active; refresh and retry')

    async def create_with_activity(self, scope, document, event, asset_ids=()):
        async def save(session):
            await self.guard_project(scope, document['project_id'], session)
            for asset_id in asset_ids:
                asset = await self.db.assets.find_one_and_update(
                    scope.query(_id=object_id(asset_id), project_id=document['project_id'], status='active'),
                    {'$inc': {'_relationship_version': 1}}, session=session, return_document=ReturnDocument.AFTER)
                if asset is None:
                    raise HTTPException(409, 'An asset is no longer active; refresh and retry')
            await self.collection.insert_one(document, session=session)
            await self.db.activity_events.insert_one(event, session=session)
            return document
        async with await self.db.client.start_session() as session:
            return await session.with_transaction(save)

    async def update_with_activity(self, scope, document, changes, event, *, require_active_project=True):
        async def save(session):
            if require_active_project:
                await self.guard_project(scope, document['project_id'], session)
            updated = await self.collection.find_one_and_update(
                scope.query(_id=document['_id'], status=document['status'], updated_at=document['updated_at']),
                {'$set': changes}, session=session, return_document=ReturnDocument.AFTER)
            if updated is None:
                raise HTTPException(409, 'Resource changed; refresh and retry')
            await self.db.activity_events.insert_one(event, session=session)
            return updated
        async with await self.db.client.start_session() as session:
            return await session.with_transaction(save)
