import asyncio
from unittest.mock import AsyncMock, MagicMock

from core.domain_indexes import domain_index_specs
from core.ownership import OrganizationScope
from repositories.github_integrations import GitHubIntegrationRepository


ORG_A = "aaaaaaaaaaaaaaaaaaaaaaaa"


def test_github_storage_indexes_enforce_single_installation_and_repository_mapping():
    specs = domain_index_specs()
    integration_indexes = {item.document["name"]: item.document for item in specs["github_integrations"]}
    repository_indexes = {item.document["name"]: item.document for item in specs["github_repositories"]}

    assert integration_indexes["organization_unique"]["unique"] is True
    assert integration_indexes["installation_unique"]["unique"] is True
    assert repository_indexes["org_repository_unique"]["unique"] is True
    assert repository_indexes["integration_repository_unique"]["unique"] is True


def test_repository_reads_are_organization_scoped_and_can_require_authorization():
    db = MagicMock()
    db.github_integrations = AsyncMock()
    db.github_repositories = AsyncMock()
    repository = GitHubIntegrationRepository(db)
    scope = OrganizationScope(organization_id=ORG_A)

    asyncio.run(repository.get_repository(scope, 1357212288, require_authorized=True))

    db.github_repositories.find_one.assert_awaited_once_with({
        "organization_id": ORG_A,
        "repository_id": 1357212288,
        "authorized": True,
    })


def test_newly_synced_repository_defaults_to_not_authorized():
    db = MagicMock()
    db.github_integrations = AsyncMock()
    db.github_repositories = AsyncMock()
    repository = GitHubIntegrationRepository(db)
    scope = OrganizationScope(organization_id=ORG_A)

    asyncio.run(repository.upsert_repository(scope, 1357212288, {
        "full_name": "KathanGoda26/havosec-github-integration-test"
    }))

    update = db.github_repositories.find_one_and_update.await_args.args[1]
    assert update["$setOnInsert"]["authorized"] is False
    assert update["$setOnInsert"]["organization_id"] == ORG_A
