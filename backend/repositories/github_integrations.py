"""MongoDB persistence with organization isolation for GitHub integrations."""

from pymongo import ReturnDocument

from core.ids import object_id


class GitHubIntegrationRepository:
    def __init__(self, db):
        self.db = db
        self.integrations = db.github_integrations
        self.repositories = db.github_repositories
        self.connection_states = db.github_connection_states

    async def get_active_pull_request(self, scope, remediation_id: str):
        return await self.db.pull_requests.find_one(scope.query(
            remediation_id=remediation_id, status={"$in": ["creating", "open"]}
        ))

    async def create_connection_state(self, document):
        await self.connection_states.insert_one(document)

    async def consume_connection_state(self, state_hash, now):
        return await self.connection_states.find_one_and_delete({
            "_id": state_hash,
            "expires_at": {"$gt": now},
        })

    async def get(self, scope):
        return await self.integrations.find_one(scope.query())

    async def get_by_installation(self, scope, installation_id: int):
        return await self.integrations.find_one(scope.query(installation_id=installation_id))

    async def find_installation_owner(self, installation_id: int):
        return await self.integrations.find_one(
            {"installation_id": installation_id}, {"organization_id": 1}
        )

    async def upsert_installation(self, scope, document):
        changes = dict(document)
        created_at = changes.pop("created_at", None)
        insert_fields = {"organization_id": scope.organization_id}
        if created_at is not None:
            insert_fields["created_at"] = created_at
        return await self.integrations.find_one_and_update(
            scope.query(),
            {"$set": changes, "$setOnInsert": insert_fields},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )

    async def mark_disconnected(self, scope, changes):
        return await self.integrations.find_one_and_update(
            scope.query(), {"$set": changes}, return_document=ReturnDocument.AFTER
        )

    async def list_repositories(self, scope, *, authorized: bool | None = None):
        query = scope.query(**({"authorized": authorized} if authorized is not None else {}))
        return await self.repositories.find(query).sort("full_name", 1).to_list(length=1000)

    async def get_repository(self, scope, repository_id: int, *, require_authorized: bool = False):
        query = {"repository_id": repository_id}
        if require_authorized:
            query["authorized"] = True
        return await self.repositories.find_one(scope.query(**query))

    async def upsert_repository(self, scope, repository_id: int, document):
        changes = dict(document)
        created_at = changes.pop("created_at", None)
        insert_fields = {
            "organization_id": scope.organization_id,
            "repository_id": repository_id,
            "authorized": False,
        }
        if created_at is not None:
            insert_fields["created_at"] = created_at
        return await self.repositories.find_one_and_update(
            scope.query(repository_id=repository_id),
            {
                "$set": changes,
                "$setOnInsert": insert_fields,
            },
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )

    async def set_repository_authorized(self, scope, repository_id: int, authorized: bool, changes):
        return await self.repositories.find_one_and_update(
            scope.query(repository_id=repository_id),
            {"$set": {**changes, "authorized": authorized}},
            return_document=ReturnDocument.AFTER,
        )

    async def revoke_missing_repositories(self, scope, visible_repository_ids: list[int], changes):
        return await self.repositories.update_many(
            scope.query(repository_id={"$nin": visible_repository_ids}),
            {"$set": {**changes, "authorized": False, "connection_status": "needs_attention"}},
        )
