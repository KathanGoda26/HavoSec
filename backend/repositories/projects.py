from pymongo import ReturnDocument
from core.ids import object_id


class ProjectRepository:
    def __init__(self, db):
        self.db = db
        self.collection = db.projects

    async def get(self, scope, project_id):
        return await self.collection.find_one(scope.query(_id=object_id(project_id)))

    async def list(self, scope, limit, offset, status=None):
        query = scope.query(**({'status': status} if status else {}))
        items = await self.collection.find(query).sort([('created_at', -1), ('_id', -1)]).skip(offset).limit(limit).to_list(length=limit)
        return items, await self.collection.count_documents(query)

    async def create_with_activity(self, document, event):
        async def save(session):
            await self.collection.insert_one(document, session=session)
            await self.db.activity_events.insert_one(event, session=session)
            return document
        async with await self.db.client.start_session() as session:
            return await session.with_transaction(save)

    async def update_with_activity(self, scope, project_id, changes, event):
        async def save(session):
            document = await self.collection.find_one_and_update(
                scope.query(_id=object_id(project_id), status='active'),
                {'$set': changes}, return_document=ReturnDocument.AFTER, session=session)
            if document is not None:
                await self.db.activity_events.insert_one(event, session=session)
            return document
        async with await self.db.client.start_session() as session:
            return await session.with_transaction(save)
