"""In-process API tests using real services/repositories and a transactional DB double.

These do not contact MongoDB; replica-set integration remains a final-step check.
"""
import asyncio
from copy import deepcopy

import httpx
import pytest
from bson import ObjectId
from fastapi import FastAPI
from pymongo.errors import AutoReconnect

from core.database import get_database
from routes.projects import router as projects_router
from routes.activity import router as activity_router
from utils.auth import get_current_user

ORG_A = 'aaaaaaaaaaaaaaaaaaaaaaaa'
ORG_B = 'bbbbbbbbbbbbbbbbbbbbbbbb'


def matches(document, query):
    return all(value in document.get(key, []) if isinstance(document.get(key), list)
               else document.get(key) == value for key, value in query.items())


class Cursor:
    def __init__(self, documents):
        self.documents = deepcopy(documents)

    def sort(self, fields):
        for key, direction in reversed(fields):
            self.documents.sort(key=lambda doc: doc[key], reverse=direction == -1)
        return self

    def skip(self, offset):
        self.documents = self.documents[offset:]
        return self

    def limit(self, limit):
        self.documents = self.documents[:limit]
        return self

    async def to_list(self, length):
        return self.documents[:length]


class Collection:
    def __init__(self):
        self.documents = []
        self.fail_insert = False

    def find(self, query):
        return Cursor([doc for doc in self.documents if matches(doc, query)])

    async def count_documents(self, query):
        return sum(matches(doc, query) for doc in self.documents)

    async def find_one(self, query):
        return deepcopy(next((doc for doc in self.documents if matches(doc, query)), None))

    async def insert_one(self, document, session=None):
        assert session is not None
        if self.fail_insert:
            raise AutoReconnect('sensitive database details')
        self.documents.append(deepcopy(document))

    async def find_one_and_update(self, query, update, return_document=None, session=None):
        assert session is not None
        for doc in self.documents:
            if matches(doc, query):
                doc.update(deepcopy(update.get('$set', {})))
                for key, value in update.get('$inc', {}).items():
                    doc[key] = doc.get(key, 0) + value
                return deepcopy(doc)
        return None


class Session:
    def __init__(self, db):
        self.db = db

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def with_transaction(self, callback):
        collections = [value for value in vars(self.db).values() if isinstance(value, Collection)]
        before = [deepcopy(item.documents) for item in collections]
        try:
            return await callback(self)
        except Exception:
            for collection, snapshot in zip(collections, before):
                collection.documents = snapshot
            raise


class Database:
    def __getitem__(self, name):
        return getattr(self, name)

    def __init__(self):
        self.projects = Collection()
        self.activity_events = Collection()
        self.client_companies = Collection()
        self.client_companies.documents = [{'_id': ObjectId(org), 'status': 'active'} for org in [ORG_A, ORG_B]]
        self.client = self

    async def start_session(self):
        return Session(self)


def application(role='admin', organization=ORG_A):
    app = FastAPI()
    app.include_router(projects_router, prefix='/api/projects')
    app.include_router(activity_router, prefix='/api/activity')
    db = Database()
    app.dependency_overrides[get_database] = lambda: db
    identity = {'id': 'actor-a', 'role': role, 'organizationId': organization}
    if role:
        app.dependency_overrides[get_current_user] = lambda: identity
    return app, db, identity


def request(app, method, path, **kwargs):
    async def send():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
            return await client.request(method, path, **kwargs)
    return asyncio.run(send())


def create(app, **kwargs):
    response = request(app, 'POST', '/api/projects', json={'name': 'Test project', **kwargs})
    assert response.status_code == 201, response.text
    return response.json()['id']


def test_project_lifecycle_and_history_survive_archive():
    app, db, _ = application()
    project_id = create(app, description='Description')
    project = request(app, 'GET', f'/api/projects/{project_id}').json()
    assert project['organization_id'] == ORG_A and project['created_by'] == 'actor-a'
    assert project['created_at'].endswith('Z')
    assert request(app, 'PATCH', f'/api/projects/{project_id}', json={'name': 'Renamed'}).status_code == 200
    archived = request(app, 'DELETE', f'/api/projects/{project_id}')
    assert archived.json()['status'] == 'archived'
    assert request(app, 'DELETE', f'/api/projects/{project_id}').status_code == 200
    assert len(db.projects.documents) == 1
    assert request(app, 'PATCH', f'/api/projects/{project_id}', json={'name': 'No'}).status_code == 409
    assert request(app, 'GET', '/api/projects?status=active').json()['total'] == 0
    assert request(app, 'GET', '/api/projects?status=archived').json()['total'] == 1
    events = request(app, 'GET', f'/api/activity?project_id={project_id}').json()['items']
    assert [e['event_type'] for e in events] == ['project_archived', 'project_updated', 'project_created']
    assert all(e['actor_id'] == 'actor-a' and e['organization_id'] == ORG_A for e in events)


@pytest.mark.parametrize('method,path', [('GET', '/api/projects'), ('POST', '/api/projects'),
    ('GET', '/api/projects/' + ORG_A), ('PATCH', '/api/projects/' + ORG_A),
    ('DELETE', '/api/projects/' + ORG_A), ('GET', '/api/activity')])
def test_no_authentication(method, path):
    app, _, _ = application(None)
    assert request(app, method, path, json={'name': 'Test'}).status_code == 401


@pytest.mark.parametrize('method', ['POST', 'PATCH', 'DELETE'])
def test_read_only_user_cannot_manage_projects(method):
    app, db, identity = application()
    project_id = create(app)
    identity['role'] = 'user'
    path = '/api/projects' + ('' if method == 'POST' else '/' + project_id)
    assert request(app, method, path, json={'name': 'No'}).status_code == 403
    assert len(db.activity_events.documents) == 1
    assert request(app, 'GET', '/api/projects').json()['total'] == 1
    assert request(app, 'GET', '/api/activity').json()['total'] == 1


@pytest.mark.parametrize('role', ['admin', 'user'])
def test_organization_isolation(role):
    app, db, identity = application()
    project_id = create(app)
    identity.update(role=role, organizationId=ORG_B)
    assert request(app, 'GET', '/api/projects').json()['items'] == []
    assert request(app, 'GET', '/api/activity').json()['items'] == []
    assert request(app, 'GET', f'/api/projects/{project_id}').status_code == 404
    assert request(app, 'GET', f'/api/activity?project_id={project_id}').status_code == 404
    for method in ['PATCH', 'DELETE']:
        assert request(app, method, f'/api/projects/{project_id}', json={'name': 'Stolen'}).status_code == (404 if role == 'admin' else 403)
    assert db.projects.documents[0]['name'] == 'Test project'


@pytest.mark.parametrize('field', ['organization_id', 'created_by', 'created_at', '_id', 'status'])
def test_server_controlled_fields_rejected(field):
    app, _, _ = application()
    assert request(app, 'POST', '/api/projects', json={'name': 'Test', field: 'injected'}).status_code == 422
    project_id = create(app)
    assert request(app, 'PATCH', f'/api/projects/{project_id}', json={field: 'injected'}).status_code == 422


@pytest.mark.parametrize('payload', [{}, {'name': None}, {'description': None}, {'name': '  '}, {'description': 'a' * 4001}])
def test_invalid_updates(payload):
    app, _, _ = application()
    project_id = create(app)
    assert request(app, 'PATCH', f'/api/projects/{project_id}', json=payload).status_code == 422


@pytest.mark.parametrize('query', ['limit=0', 'limit=101', 'offset=-1', 'offset=100001'])
@pytest.mark.parametrize('path', ['/api/projects', '/api/activity'])
def test_bounded_pagination(path, query):
    app, _, _ = application()
    assert request(app, 'GET', path + '?' + query).status_code == 422


def test_pagination_and_bad_ids():
    app, _, _ = application()
    create(app)
    create(app)
    for path in ['/api/projects', '/api/activity']:
        result = request(app, 'GET', path + '?limit=1&offset=1').json()
        assert result['total'] == 2 and len(result['items']) == 1
    for path in ['/api/projects/not-an-id', '/api/activity?project_id=bad']:
        assert request(app, 'GET', path).status_code == 404


@pytest.mark.parametrize('organization', [None, 'invalid', 'cccccccccccccccccccccccc'])
def test_missing_or_invalid_membership_fails_closed(organization):
    app, _, _ = application(organization=organization)
    assert request(app, 'GET', '/api/projects').status_code == 403


def test_inactive_organization_and_explicit_superadmin_scope():
    app, db, identity = application()
    assert request(app, 'GET', '/api/projects?organization_id=' + ORG_B).status_code == 403
    identity['role'] = 'superadmin'
    assert request(app, 'GET', '/api/projects').status_code == 403
    assert request(app, 'POST', '/api/projects?organization_id=' + ORG_B, json={'name': 'Platform-created'}).status_code == 201
    assert db.projects.documents[0]['organization_id'] == ORG_B
    assert request(app, 'GET', '/api/activity?organization_id=' + ORG_B).json()['total'] == 1
    db.client_companies.documents[1]['status'] = 'inactive'
    assert request(app, 'GET', '/api/projects?organization_id=' + ORG_B).status_code == 403


@pytest.mark.parametrize('operation', ['create', 'update', 'archive'])
def test_activity_failure_rolls_back_project_write(operation):
    app, db, _ = application()
    project_id = create(app)
    snapshot = deepcopy(db.projects.documents)
    db.activity_events.fail_insert = True
    method, path, payload = ('POST', '/api/projects', {'name': 'New'}) if operation == 'create' else (
        'PATCH' if operation == 'update' else 'DELETE', f'/api/projects/{project_id}', {'name': 'Changed'})
    result = request(app, method, path, json=payload)
    assert result.status_code == 503
    assert 'sensitive' not in result.text
    assert db.projects.documents == snapshot
    assert len(db.activity_events.documents) == 1


def test_activity_cannot_be_fabricated_over_http():
    app, _, _ = application()
    assert request(app, 'POST', '/api/activity', json={'event_type': 'project_created'}).status_code == 405


def test_new_routes_mounted_in_main_app():
    from server import app
    paths = {route.path for route in app.routes}
    assert {'/api/projects', '/api/projects/{project_id}', '/api/activity'} <= paths
