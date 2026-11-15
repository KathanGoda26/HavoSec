import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from core.ownership import OrganizationScope
from integrations.github.config import GitHubAppSettings
from services.github_integrations import GitHubIntegrationService


ORG_A = "aaaaaaaaaaaaaaaaaaaaaaaa"


def service(repository):
    return GitHubIntegrationService(
        repository,
        GitHubAppSettings(4830110, __import__("pathlib").Path("unused.pem"), None),
    )


def test_connection_state_is_hashed_and_bound_to_actor_and_organization():
    repository = AsyncMock()
    result = asyncio.run(service(repository).begin_connection(
        OrganizationScope(ORG_A), "bbbbbbbbbbbbbbbbbbbbbbbb"
    ))

    stored = repository.create_connection_state.await_args.args[0]
    returned_state = result["installation_url"].split("state=", 1)[1]
    assert returned_state not in str(stored)
    assert stored["organization_id"] == ORG_A
    assert stored["actor_id"] == "bbbbbbbbbbbbbbbbbbbbbbbb"
    assert stored["expires_at"] <= datetime.now(timezone.utc) + timedelta(minutes=10)


def test_invalid_or_replayed_callback_state_fails_closed():
    repository = AsyncMock()
    repository.consume_connection_state.return_value = None

    with pytest.raises(HTTPException) as error:
        asyncio.run(service(repository).complete_connection("x" * 43, 159047858))

    assert error.value.status_code == 400
    assert "token" not in error.value.detail.lower()


def test_short_callback_state_is_rejected_before_database_lookup():
    repository = AsyncMock()
    with pytest.raises(HTTPException) as error:
        asyncio.run(service(repository).complete_connection("short", 159047858))
    assert error.value.status_code == 400
    repository.consume_connection_state.assert_not_awaited()
