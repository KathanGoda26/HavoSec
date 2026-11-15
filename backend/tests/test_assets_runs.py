from copy import deepcopy
import pytest

from test_projects import application, request, create, Collection, ORG_A, ORG_B
from routes.assets import router as assets_router
from routes.security_runs import router as runs_router


def setup(role='admin'):
    app, db, identity = application(role)
    db.assets = Collection()
    db.security_runs = Collection()
    app.include_router(assets_router, prefix='/api/assets')
    app.include_router(runs_router, prefix='/api/security-runs')
    return app, db, identity


def asset(app, project_id, **changes):
    return request(app, 'POST', '/api/assets', json={
        'project_id': project_id, 'name': 'Website', 'type': 'domain', 'target': 'example.com', **changes})


def run(app, project_id, asset_ids, **changes):
    return request(app, 'POST', '/api/security-runs', json={
        'project_id': project_id, 'asset_ids': asset_ids, **changes})


def records():
    app, db, identity = setup()
    project_id = create(app)
    response = asset(app, project_id)
    assert response.status_code == 201, response.text
    asset_id = response.json()['id']
    response = run(app, project_id, [asset_id])
    assert response.status_code == 201, response.text
    return app, db, identity, project_id, asset_id, response.json()['id']


def test_lifecycle_no_execution_and_activity():
    app, db, _, project_id, asset_id, run_id = records()
    result = request(app, 'GET', '/api/security-runs/' + run_id).json()
    assert result['status'] == 'queued' and result['progress'] == 0
    assert result['started_at'] is None and result['summary'] is None and result['error'] is None
    assert result['requested_by'] == 'actor-a'
    assert request(app, 'PATCH', '/api/assets/' + asset_id, json={'name': 'Renamed'}).status_code == 200
    for _ in range(2):
        result = request(app, 'PATCH', f'/api/security-runs/{run_id}/cancel')
        assert result.status_code == 200 and result.json()['status'] == 'cancelled'
    assert result.json()['completed_at'].endswith('Z')
    for _ in range(2):
        assert request(app, 'DELETE', '/api/assets/' + asset_id).status_code == 200
    assert len(db.assets.documents) == 1
    assert request(app, 'PATCH', '/api/assets/' + asset_id, json={'target': 'new'}).status_code == 409
    assert run(app, project_id, [asset_id]).status_code == 409
    events = request(app, 'GET', '/api/activity').json()['items']
    assert {e['event_type'] for e in events} == {'project_created', 'asset_created', 'asset_updated',
                                               'asset_archived', 'security_run_created', 'security_run_cancelled'}
    assert len(events) == 6


@pytest.mark.parametrize('role', ['admin', 'user'])
def test_other_organization_cannot_access_resources(role):
    app, db, identity, project_id, asset_id, run_id = records()
    identity.update(role=role, organizationId=ORG_B)
    for path in ['/api/assets', '/api/security-runs']:
        assert request(app, 'GET', path).json()['total'] == 0
        assert request(app, 'GET', path + '?project_id=' + project_id).status_code == 404
    for path in ['/api/assets/' + asset_id, '/api/security-runs/' + run_id]:
        assert request(app, 'GET', path).status_code == 404
    assert request(app, 'PATCH', '/api/assets/' + asset_id, json={'name': 'No'}).status_code == (404 if role == 'admin' else 403)
    assert request(app, 'DELETE', '/api/assets/' + asset_id).status_code == (404 if role == 'admin' else 403)
    assert request(app, 'PATCH', f'/api/security-runs/{run_id}/cancel').status_code == (404 if role == 'admin' else 403)
    assert len(db.activity_events.documents) == 3


def test_cross_project_and_foreign_asset_assignment():
    app, _, identity, project_id, asset_id, _ = records()
    second = create(app)
    assert run(app, second, [asset_id]).status_code == 404
    identity['organizationId'] = ORG_B
    own = create(app)
    assert asset(app, project_id).status_code == 404
    assert run(app, own, [asset_id]).status_code == 404


@pytest.mark.parametrize('method,path', [('GET', '/api/assets'), ('POST', '/api/assets'),
    ('GET', '/api/assets/' + ORG_A), ('PATCH', '/api/assets/' + ORG_A), ('DELETE', '/api/assets/' + ORG_A),
    ('GET', '/api/security-runs'), ('POST', '/api/security-runs'), ('GET', '/api/security-runs/' + ORG_A),
    ('PATCH', '/api/security-runs/' + ORG_A + '/cancel')])
def test_unauthenticated(method, path):
    app, _, _ = setup(None)
    assert request(app, method, path, json={}).status_code == 401


def test_user_reads_but_cannot_write():
    app, _, identity, project_id, asset_id, run_id = records()
    identity['role'] = 'user'
    assert request(app, 'GET', '/api/assets/' + asset_id).status_code == 200
    assert request(app, 'GET', '/api/security-runs/' + run_id).status_code == 200
    assert asset(app, project_id).status_code == 403
    assert run(app, project_id, [asset_id]).status_code == 403
    assert request(app, 'PATCH', '/api/assets/' + asset_id, json={'name': 'No'}).status_code == 403
    assert request(app, 'DELETE', '/api/assets/' + asset_id).status_code == 403
    assert request(app, 'PATCH', f'/api/security-runs/{run_id}/cancel').status_code == 403


@pytest.mark.parametrize('field', ['organization_id', 'created_at', 'status', 'created_by', '_id'])
def test_controlled_asset_fields(field):
    app, _, _ = setup()
    assert asset(app, create(app), **{field: 'invalid'}).status_code == 422


@pytest.mark.parametrize('field', ['organization_id', 'requested_by', 'status', 'progress', 'summary', 'started_at'])
def test_controlled_run_fields(field):
    app, _, _, project_id, asset_id, _ = records()
    assert run(app, project_id, [asset_id], **{field: 'invalid'}).status_code == 422


@pytest.mark.parametrize('asset_ids', [[], ['bad'], [ORG_A, ORG_A], [ORG_A, ORG_A.upper()], [ORG_A] * 101])
def test_invalid_run_assets(asset_ids):
    app, _, _ = setup()
    assert run(app, create(app), asset_ids).status_code == 422


def test_metadata_validation_and_immutable_project_type():
    app, _, _, project_id, asset_id, _ = records()
    assert asset(app, project_id, metadata={'large': 'x' * 16385}).status_code == 422
    assert asset(app, project_id, metadata=['not an object']).status_code == 422
    assert asset(app, project_id, target=' ').status_code == 422
    assert asset(app, project_id, type='scanner').status_code == 422
    for payload in [{}, {'name': None}, {'project_id': project_id}, {'type': 'api'}]:
        assert request(app, 'PATCH', '/api/assets/' + asset_id, json=payload).status_code == 422


def test_archived_project_blocks_new_work_but_allows_cancellation():
    app, _, _, project_id, asset_id, run_id = records()
    assert request(app, 'DELETE', '/api/projects/' + project_id).status_code == 200
    assert asset(app, project_id).status_code == 409
    assert run(app, project_id, [asset_id]).status_code == 409
    assert request(app, 'PATCH', '/api/assets/' + asset_id, json={'name': 'No'}).status_code == 409
    assert request(app, 'GET', '/api/assets/' + asset_id).status_code == 200
    assert request(app, 'PATCH', f'/api/security-runs/{run_id}/cancel').status_code == 200


@pytest.mark.parametrize('status,code', [('running', 200), ('completed', 409), ('failed', 409)])
def test_cancel_lifecycle(status, code):
    app, db, _, _, _, run_id = records()
    db.security_runs.documents[0]['status'] = status
    assert request(app, 'PATCH', f'/api/security-runs/{run_id}/cancel').status_code == code


@pytest.mark.parametrize('path', ['/api/assets', '/api/security-runs'])
def test_lists_and_validation(path):
    app, _, _, project_id, _, _ = records()
    assert request(app, 'GET', path + '?project_id=' + project_id).json()['total'] == 1
    assert request(app, 'GET', path + '?limit=1&offset=1').json()['items'] == []
    for query in ['limit=0', 'limit=101', 'offset=-1', 'offset=100001', 'status=invalid']:
        assert request(app, 'GET', path + '?' + query).status_code == 422
    assert request(app, 'GET', path + '/invalid').status_code == 404


@pytest.mark.parametrize('operation', ['asset_create', 'asset_update', 'asset_archive', 'run_create', 'run_cancel'])
def test_transaction_failure_leaves_no_partial_write(operation):
    app, db, _, project_id, asset_id, run_id = records()
    collections = [db.projects, db.assets, db.security_runs, db.activity_events]
    before = [deepcopy(c.documents) for c in collections]
    db.activity_events.fail_insert = True
    actions = {
        'asset_create': lambda: asset(app, project_id),
        'asset_update': lambda: request(app, 'PATCH', '/api/assets/' + asset_id, json={'name': 'Changed'}),
        'asset_archive': lambda: request(app, 'DELETE', '/api/assets/' + asset_id),
        'run_create': lambda: run(app, project_id, [asset_id]),
        'run_cancel': lambda: request(app, 'PATCH', f'/api/security-runs/{run_id}/cancel'),
    }
    response = actions[operation]()
    assert response.status_code == 503 and 'sensitive' not in response.text
    assert [c.documents for c in collections] == before


def test_main_routes_registered():
    from server import app
    assert {'/api/assets', '/api/security-runs', '/api/security-runs/{run_id}/cancel'} <= {r.path for r in app.routes}


@pytest.mark.parametrize('changed_resource', ['project', 'asset'])
def test_transaction_rechecks_archive_after_preflight(monkeypatch, changed_resource):
    from repositories.project_resources import ProjectResourceRepository
    app, db, _, project_id, asset_id, _ = records()
    original = ProjectResourceRepository.create_with_activity

    async def archive_then_save(self, *args, **kwargs):
        collection = db.projects if changed_resource == 'project' else db.assets
        collection.documents[0]['status'] = 'archived'
        return await original(self, *args, **kwargs)

    monkeypatch.setattr(ProjectResourceRepository, 'create_with_activity', archive_then_save)
    assert run(app, project_id, [asset_id]).status_code == 409
    assert len(db.security_runs.documents) == 1
    assert len(db.activity_events.documents) == 3


def test_cancellation_does_not_overwrite_concurrent_completion(monkeypatch):
    from repositories.project_resources import ProjectResourceRepository
    app, db, _, _, _, run_id = records()
    original = ProjectResourceRepository.update_with_activity

    async def complete_then_save(self, *args, **kwargs):
        db.security_runs.documents[0]['status'] = 'completed'
        return await original(self, *args, **kwargs)

    monkeypatch.setattr(ProjectResourceRepository, 'update_with_activity', complete_then_save)
    assert request(app, 'PATCH', f'/api/security-runs/{run_id}/cancel').status_code == 409
    assert db.security_runs.documents[0]['status'] == 'completed'
    assert len(db.activity_events.documents) == 3


@pytest.mark.parametrize('path', ['/api/assets', '/api/security-runs'])
def test_platform_scope_and_customer_selector_rejection(path):
    app, _, identity, _, _, _ = records()
    assert request(app, 'GET', path + '?organization_id=' + ORG_A).status_code == 403
    identity['role'] = 'superadmin'
    assert request(app, 'GET', path).status_code == 403
    assert request(app, 'GET', path + '?organization_id=' + ORG_A).json()['total'] == 1
    assert request(app, 'GET', path + '?organization_id=' + ORG_B).json()['total'] == 0
