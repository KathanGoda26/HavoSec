"""Secure organization-bound GitHub App connection and repository sync workflow."""

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import hashlib
import secrets
from urllib.parse import urlencode

from bson import ObjectId
from fastapi import HTTPException

from core.domain_api import document_view
from integrations.github.client import GitHubAPIError, GitHubAppClient
from integrations.github.config import GitHubAppSettings, GitHubConfigurationError


class GitHubIntegrationService:
    STATE_TTL = timedelta(minutes=10)

    def __init__(self, repository, settings: GitHubAppSettings):
        self.repository = repository
        self.settings = settings

    async def begin_connection(self, scope, actor_id):
        now = datetime.now(timezone.utc)
        state = secrets.token_urlsafe(32)
        await self.repository.create_connection_state({
            "_id": self._state_hash(state),
            "organization_id": scope.organization_id,
            "actor_id": actor_id,
            "expires_at": now + self.STATE_TTL,
            "created_at": now,
        })
        query = urlencode({"state": state})
        return {
            "installation_url": f"https://github.com/apps/{self.settings.app_slug}/installations/new?{query}",
            "expires_at": now + self.STATE_TTL,
        }

    async def complete_connection(self, state, installation_id: int):
        now = datetime.now(timezone.utc)
        consumed = await self.repository.consume_connection_state(self._state_hash(state), now)
        if not consumed:
            raise HTTPException(400, "GitHub connection state is invalid or expired")

        try:
            client = GitHubAppClient(replace(self.settings, installation_id=installation_id))
            installation = await client.get_installation()
        except (GitHubAPIError, GitHubConfigurationError) as exc:
            raise HTTPException(502, "GitHub installation could not be validated") from exc
        for field in ("account_id", "account_login", "account_type"):
            if not installation.get(field):
                raise HTTPException(502, "GitHub installation metadata is incomplete")

        scope = _StoredScope(consumed["organization_id"])
        existing_owner = await self.repository.find_installation_owner(installation_id)
        if existing_owner and existing_owner.get("organization_id") != scope.organization_id:
            raise HTTPException(409, "GitHub installation is already connected")
        document = {
            **installation,
            "status": "active",
            "last_synced_at": None,
            "updated_at": now,
        }
        document.setdefault("created_at", now)
        integration = await self.repository.upsert_installation(scope, document)
        await self.sync_repositories(scope, integration=integration, client=client)
        return document_view(await self.repository.get(scope))

    async def get(self, scope):
        integration = await self.repository.get(scope)
        return document_view(integration) if integration else None

    async def sync_repositories(self, scope, *, integration=None, client=None):
        integration = integration or await self.repository.get(scope)
        if not integration or integration.get("status") != "active":
            raise HTTPException(409, "GitHub integration is not active")
        try:
            client = client or GitHubAppClient(replace(
                self.settings, installation_id=integration["installation_id"]
            ))
            visible = await client.list_installation_repositories()
        except (GitHubAPIError, GitHubConfigurationError) as exc:
            raise HTTPException(502, "GitHub repositories could not be synchronized") from exc

        now = datetime.now(timezone.utc)
        integration_id = str(integration["_id"])
        visible_ids = []
        for item in visible:
            visible_ids.append(item["id"])
            await self.repository.upsert_repository(scope, item["id"], {
                "integration_id": integration_id,
                "full_name": item["full_name"],
                "default_branch": item["default_branch"] or "main",
                "private": item["private"],
                "connection_status": "active",
                "last_synced_at": now,
                "updated_at": now,
                "created_at": now,
            })
        await self.repository.revoke_missing_repositories(scope, visible_ids, {"updated_at": now})
        await self.repository.upsert_installation(scope, {"last_synced_at": now, "updated_at": now})
        items = await self.repository.list_repositories(scope)
        return {"items": [document_view(item) for item in items], "total": len(items)}

    async def authorize_repository(self, scope, repository_id: int, authorized: bool):
        integration = await self.repository.get(scope)
        if not integration or integration.get("status") != "active":
            raise HTTPException(409, "GitHub integration is not active")
        existing = await self.repository.get_repository(scope, repository_id)
        if not existing or existing.get("integration_id") != str(integration["_id"]):
            raise HTTPException(404, "GitHub repository is not available to this organization")
        if existing.get("connection_status") != "active" and authorized:
            raise HTTPException(409, "GitHub repository access needs attention")
        now = datetime.now(timezone.utc)
        updated = await self.repository.set_repository_authorized(
            scope, repository_id, authorized, {"updated_at": now}
        )
        return document_view(updated)

    @staticmethod
    def _state_hash(state):
        if not isinstance(state, str) or len(state) < 32 or len(state) > 256:
            raise HTTPException(400, "GitHub connection state is invalid or expired")
        return hashlib.sha256(state.encode("utf-8")).hexdigest()


class _StoredScope:
    def __init__(self, organization_id):
        self.organization_id = organization_id

    def query(self, **filters):
        if "organization_id" in filters:
            raise ValueError("Organization scope cannot be overridden")
        return {**filters, "organization_id": self.organization_id}
