import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest
from bson import ObjectId
from fastapi import HTTPException

from core.ownership import OrganizationScope
from services.project_resources import AssetService


ORG_A = 'aaaaaaaaaaaaaaaaaaaaaaaa'
ASSET_ID = 'bbbbbbbbbbbbbbbbbbbbbbbb'


def make_service(asset_type='repository', github_repository=None):
    assets = AsyncMock()
    assets.get.return_value = {
        '_id': ObjectId(ASSET_ID), 'organization_id': ORG_A,
        'project_id': 'cccccccccccccccccccccccc', 'status': 'active',
        'type': asset_type, 'updated_at': datetime.now(timezone.utc),
    }
    assets.update_with_activity.side_effect = lambda scope, document, changes, event: {
        **document, **changes
    }
    projects = AsyncMock()
    projects.get_document.return_value = {'_id': ObjectId('cccccccccccccccccccccccc'), 'status': 'active'}
    github = AsyncMock()
    github.get_repository.return_value = github_repository
    return AssetService(assets, projects, github), assets, github


def authorized_repository(**changes):
    return {
        'integration_id': 'dddddddddddddddddddddddd',
        'repository_id': 1357212288,
        'full_name': 'KathanGoda26/havosec-github-integration-test',
        'default_branch': 'main',
        'authorized': True,
        'connection_status': 'active',
        **changes,
    }


def test_repository_asset_links_only_by_authorized_scoped_repository_id():
    service, assets, github = make_service(github_repository=authorized_repository())
    result = asyncio.run(service.link_github_repository(
        OrganizationScope(ORG_A), ASSET_ID, 'actor-a', 1357212288
    ))

    github.get_repository.assert_awaited_once_with(
        OrganizationScope(ORG_A), 1357212288, require_authorized=True
    )
    assert result['source_control']['repository_full_name'] == 'KathanGoda26/havosec-github-integration-test'
    assert result['source_control']['provider'] == 'github'
    assert assets.update_with_activity.await_args.args[3]['metadata']['repository_id'] == 1357212288


def test_arbitrary_or_cross_organization_repository_is_rejected():
    service, assets, _ = make_service(github_repository=None)
    with pytest.raises(HTTPException) as error:
        asyncio.run(service.link_github_repository(
            OrganizationScope(ORG_A), ASSET_ID, 'actor-a', 999
        ))
    assert error.value.status_code == 404
    assets.update_with_activity.assert_not_awaited()


def test_non_repository_asset_cannot_be_linked():
    service, assets, github = make_service(asset_type='domain', github_repository=authorized_repository())
    with pytest.raises(HTTPException) as error:
        asyncio.run(service.link_github_repository(
            OrganizationScope(ORG_A), ASSET_ID, 'actor-a', 1357212288
        ))
    assert error.value.status_code == 409
    github.get_repository.assert_not_awaited()
    assets.update_with_activity.assert_not_awaited()
