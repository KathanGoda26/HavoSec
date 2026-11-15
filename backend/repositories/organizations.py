"""Existing client companies are customer organizations, not a new collection."""
from core.ids import object_id
from pymongo import ReturnDocument


class OrganizationRepository:
    def __init__(self, db):
        self.collection = db.client_companies

    async def find_by_id(self, organization_id):
        return await self.collection.find_one({'_id': object_id(organization_id)})

    async def list(self, limit, offset):
        records = await self.collection.find({}).sort('_id', -1).skip(offset).limit(limit).to_list(length=limit)
        return records, await self.collection.count_documents({})

    async def insert(self, document):
        await self.collection.insert_one(document)

    async def update(self, identity, changes):
        return await self.collection.find_one_and_update(
            {'_id': object_id(identity)}, {'$set': changes}, return_document=ReturnDocument.AFTER)
