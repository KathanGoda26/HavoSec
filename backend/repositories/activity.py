class ActivityRepository:
    def __init__(self, db):
        self.collection = db.activity_events

    async def list(self, scope, limit, offset, project_id=None):
        query = scope.query(**({'project_id': project_id} if project_id else {}))
        items = await self.collection.find(query).sort([('created_at', -1), ('_id', -1)]).skip(offset).limit(limit).to_list(length=limit)
        return items, await self.collection.count_documents(query)
