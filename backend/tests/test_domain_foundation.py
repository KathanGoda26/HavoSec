import asyncio
from unittest.mock import AsyncMock

import pytest
from bson import ObjectId
from fastapi import HTTPException
from pymongo.errors import ServerSelectionTimeoutError

from core.database import DatabaseSettings
from core.ids import canonical_id, object_id
from core.ownership import resolve_organization
from repositories.organizations import OrganizationRepository

ORG_A = 'aaaaaaaaaaaaaaaaaaaaaaaa'
ORG_B = 'bbbbbbbbbbbbbbbbbbbbbbbb'


def run_scope(user, organization=None, **kwargs):
    repo = AsyncMock()
    repo.find_by_id.return_value = organization
    return asyncio.run(resolve_organization(user, repo, **kwargs)), repo


@pytest.mark.parametrize('role', ['admin', 'user'])
def test_customer_scope_comes_from_identity(role):
    scope, repo = run_scope({'role': role, 'organizationId': ORG_A}, {'_id': ObjectId(ORG_A), 'isActive': True})
    repo.find_by_id.assert_awaited_once_with(ORG_A)
    assert scope.query(project_id='project') == {'organization_id': ORG_A, 'project_id': 'project'}
    with pytest.raises(ValueError):
        scope.query(organization_id=ORG_B)


@pytest.mark.parametrize('role', ['admin', 'user'])
def test_customers_cannot_select_another_organization(role):
    with pytest.raises(HTTPException) as error:
        run_scope({'role': role, 'organizationId': ORG_A}, platform_organization_id=ORG_B)
    assert error.value.status_code == 403


@pytest.mark.parametrize('assignment,organization', [
    (None, None), ('invalid', None), (ORG_A, None),
    (ORG_A, {'isActive': False}), (ORG_A, {'status': 'inactive'}),
])
def test_missing_dangling_or_inactive_assignment_fails_closed(assignment, organization):
    with pytest.raises(HTTPException) as error:
        run_scope({'role': 'admin', 'organizationId': assignment}, organization)
    assert error.value.status_code == 403


def test_superadmin_requires_explicit_single_organization():
    with pytest.raises(HTTPException) as error:
        run_scope({'role': 'superadmin'})
    assert error.value.status_code == 403
    scope, _ = run_scope({'role': 'superadmin'}, {'isActive': True}, platform_organization_id=ORG_B)
    assert scope.query() == {'organization_id': ORG_B}


def test_database_failure_is_safe():
    repo = AsyncMock()
    repo.find_by_id.side_effect = ServerSelectionTimeoutError('sensitive connection details')
    with pytest.raises(HTTPException) as error:
        asyncio.run(resolve_organization({'role': 'user', 'organizationId': ORG_A}, repo))
    assert error.value.status_code == 503
    assert 'sensitive' not in error.value.detail


@pytest.mark.parametrize('value', ['', 'not-an-id', None, {}, 123])
def test_bad_ids_return_controlled_not_found(value):
    with pytest.raises(HTTPException) as error:
        object_id(value)
    assert error.value.status_code == 404


def test_id_normalization_and_existing_collection():
    assert canonical_id(ORG_A.upper()) == ORG_A
    db = AsyncMock()
    asyncio.run(OrganizationRepository(db).find_by_id(ORG_A))
    db.client_companies.find_one.assert_awaited_once_with({'_id': ObjectId(ORG_A)})


def test_database_config_never_displays_connection_secret(monkeypatch):
    monkeypatch.setenv('MONGO_URL', 'mongodb://test:private@localhost:27017')
    monkeypatch.setenv('DB_NAME', 'test_foundation')
    settings = DatabaseSettings.from_environment()
    assert settings.database_name == 'test_foundation'
    assert 'private' not in repr(settings)


def test_lifespan_does_not_seed_business_data(monkeypatch):
    import server
    from unittest.mock import MagicMock
    client = MagicMock()
    monkeypatch.setattr(server, 'create_database_client', lambda settings: client)

    async def check():
        async with server.lifespan(server.app):
            assert server.app.state.db is client.__getitem__.return_value
        client.close.assert_called_once()
        # Startup only selects a database; it must not access business collections.
        assert client.__getitem__.return_value.mock_calls == []
    asyncio.run(check())
