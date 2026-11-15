import asyncio
from copy import deepcopy
from unittest.mock import AsyncMock

import httpx
import pytest
from bson import ObjectId
from fastapi import FastAPI
from pydantic import ValidationError
from pymongo.errors import AutoReconnect

from audit_organizations import audit_memberships
from core.membership import membership_value
from models.organizations import OrganizationCreate, OrganizationUpdate
from routes.clients import router, organization_service
from services.organizations import OrganizationService, organization_view
from utils.auth import get_current_user, serialize_user

ORG = 'aaaaaaaaaaaaaaaaaaaaaaaa'


def request(app, method, url, **kwargs):
    async def send():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
            return await client.request(method, url, **kwargs)
    return asyncio.run(send())


def application(role=None):
    app = FastAPI()
    app.include_router(router, prefix='/api/admin/clients')
    repo = AsyncMock()
    repo.find_by_id.return_value = {'_id': ObjectId(ORG), 'name': 'Legacy', 'email': 'test@example.com'}
    repo.list.return_value = ([repo.find_by_id.return_value], 1)
    repo.update.return_value = {**repo.find_by_id.return_value, 'status': 'inactive', 'isActive': False}
    app.dependency_overrides[organization_service] = lambda: OrganizationService(repo)
    if role:
        app.dependency_overrides[get_current_user] = lambda: {'id': 'u1', 'role': role, 'organizationId': ORG}
    return app, repo


@pytest.mark.parametrize('role,code', [(None, 401), ('admin', 403), ('user', 403)])
@pytest.mark.parametrize('method,path,body', [
    ('GET', '/', None), ('GET', '/' + ORG, None),
    ('POST', '/', {'name': 'Test', 'email': 'test@example.com'}),
    ('PATCH', '/' + ORG, {'name': 'Updated'}), ('PUT', '/' + ORG, {'name': 'Updated'}),
    ('DELETE', '/' + ORG, None),
])
def test_company_management_is_platform_only(role, code, method, path, body):
    app, repo = application(role)
    assert request(app, method, '/api/admin/clients' + path, json=body).status_code == code
    assert not repo.mock_calls


def test_superadmin_compatibility_read_and_bounded_pagination():
    app, repo = application('superadmin')
    result = request(app, 'GET', '/api/admin/clients/')
    assert result.status_code == 200
    assert result.json()['clients'][0]['status'] == 'active'
    assert result.json()['clients'][0]['id'] == ORG
    assert request(app, 'GET', '/api/admin/clients/?limit=0').status_code == 422
    assert request(app, 'GET', '/api/admin/clients/?limit=101').status_code == 422
    assert request(app, 'GET', '/api/admin/clients/?offset=-1').status_code == 422


def test_create_fields_are_controlled_and_utc():
    app, repo = application('superadmin')
    result = request(app, 'POST', '/api/admin/clients/', json={'name': 'Example', 'email': 'test@example.com'})
    assert result.status_code == 200
    doc = repo.insert.call_args.args[0]
    assert doc['status'] == 'active' and doc['isActive'] is True
    assert doc['created_at'].tzinfo is not None
    assert doc['slug'].endswith(str(doc['_id']))
    for field in ['organization_id', 'created_by', 'createdAt', 'slug', '_id']:
        assert request(app, 'POST', '/api/admin/clients/', json={
            'name': 'Example', 'email': 'test@example.com', field: 'injected'}).status_code == 422


def test_deactivate_preserves_history_and_is_atomic():
    app, repo = application('superadmin')
    response = request(app, 'DELETE', '/api/admin/clients/' + ORG)
    assert response.status_code == 200
    assert response.json()['client']['status'] == 'inactive'
    assert repo.update.call_args.args[1]['isActive'] is False
    repo.delete_one.assert_not_called()


def test_safe_database_failure():
    app, repo = application('superadmin')
    repo.find_by_id.side_effect = AutoReconnect('private topology')
    response = request(app, 'GET', '/api/admin/clients/' + ORG)
    assert response.status_code == 503
    assert 'private' not in response.text


@pytest.mark.parametrize('data', [{'name': ''}, {'name': None}, {'status': 'deleted'},
                               {'status': 'inactive', 'isActive': True}, {'role': 'superadmin'}])
def test_invalid_update_rejected(data):
    with pytest.raises(ValidationError):
        OrganizationUpdate(**data)


def test_legacy_view_does_not_mutate_or_lose_company_fields():
    document = {'_id': ObjectId(ORG), 'name': 'Legacy', 'services': ['service'], 'isActive': False}
    original = deepcopy(document)
    view = organization_view(document)
    assert view['status'] == 'inactive'
    assert view['services'] == ['service']
    assert document == original


def test_audit_is_read_only_and_flags_ambiguous_memberships():
    users = [
        {'_id': '1', 'role': 'admin', 'organizationId': ORG},
        {'_id': '2', 'role': 'user'},
        {'_id': '3', 'role': 'user', 'organizationId': 'bbbbbbbbbbbbbbbbbbbbbbbb'},
        {'_id': '4', 'role': 'user', 'organizationId': ORG, 'clientId': 'cccccccccccccccccccccccc'},
        {'_id': '5', 'role': 'superadmin'},
    ]
    before = deepcopy(users)
    report = audit_memberships(users, [{'_id': ObjectId(ORG), 'isActive': True}])
    assert report['valid_customer_assignments'] == 1
    assert [issue['issue'] for issue in report['issues']] == ['missing', 'dangling', 'conflicting']
    assert users == before
    assert serialize_user(users[3], 'users')['organizationId'] is None
    assert membership_value({'organizationId': ObjectId(ORG), 'clientId': ORG.upper()}) == (ORG, 'assigned')


@pytest.mark.parametrize('role', ['admin', 'user'])
@pytest.mark.parametrize('method,path', [
    ('GET', '/api/admin/dashboard'), ('GET', '/api/admin/content/'),
    ('PUT', '/api/content/header'), ('POST', '/api/blog/'),
    ('GET', '/api/demo/'), ('GET', '/api/book-demo/'),
    ('PUT', '/api/seo/global'), ('POST', '/api/notifications/'),
    ('GET', '/api/uploads/'),
])
def test_platform_aliases_cannot_bypass_customer_role_guard(role, method, path):
    from server import app
    app.dependency_overrides[get_current_user] = lambda: {'id': 'u1', 'role': role}
    try:
        assert request(app, method, path, json={}).status_code == 403
    finally:
        app.dependency_overrides.clear()
