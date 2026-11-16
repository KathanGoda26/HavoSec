from test_assets_runs import asset, setup
from test_projects import Collection, ORG_B, create, request

from routes.missions import router
from services import missions as mission_services


def mission_setup():
    app, db, identity = setup()
    app.include_router(router, prefix='/api/missions')
    db.missions = Collection()
    db.mission_outbox = Collection()
    project_id = create(app)
    response = asset(app, project_id, type='repository', target='https://github.com/example/repo')
    assert response.status_code == 201, response.text
    payload = {'project_id': project_id, 'asset_id': response.json()['id'], 'objective': 'Assess repository'}
    return app, db, identity, payload


def submit(app, payload):
    return request(app, 'POST', '/api/missions', json=payload,
                   headers={'Idempotency-Key': 'test-request-key-001'})


def test_mission_replay_and_organization_scope():
    app, db, identity, payload = mission_setup()
    first = submit(app, payload)
    assert first.status_code == 201, first.text
    record = first.json()
    assert record['status'] == 'queued'
    assert 'request_key' not in record
    assert submit(app, payload).json()['id'] == record['id']
    assert submit(app, {**payload, 'objective': 'Other objective'}).status_code == 409
    assert request(app, 'GET', '/api/missions').json()['total'] == 1
    assert len(db.missions.documents) == len(db.mission_outbox.documents) == 1
    assert db.mission_outbox.documents[0]['mission_id'] == record['id']
    identity['organizationId'] = ORG_B
    assert request(app, 'GET', f"/api/missions/{record['id']}").status_code == 404
    assert request(app, 'GET', '/api/missions').json()['total'] == 0
    assert submit(app, payload).status_code == 404


def test_outbox_failure_rolls_back_mission():
    app, db, _, payload = mission_setup()
    db.mission_outbox.fail_insert = True
    response = submit(app, payload)
    assert response.status_code == 503
    assert not db.missions.documents
    assert not db.mission_outbox.documents
    db.mission_outbox.fail_insert = False
    assert submit(app, payload).status_code == 201


def test_fixture_report_is_scoped_and_pins_the_operator_commit(monkeypatch):
    app, db, identity, payload = mission_setup()
    scan = {**payload, 'mission_type': 'fixture_repository_assessment'}
    monkeypatch.delenv('MISSION_FIXTURE_COMMIT', raising=False)
    assert submit(app, scan).status_code == 503
    commit = 'a' * 40
    monkeypatch.setenv('MISSION_FIXTURE_COMMIT', commit)
    created = submit(app, scan)
    assert created.status_code == 201, created.text
    assert db.missions.documents[0]['fixture_commit'] == commit
    path = f"/api/missions/{created.json()['id']}/report"
    assert request(app, 'GET', path).status_code == 404
    db.missions.documents[0]['assessment_report'] = {'commit_sha': commit, 'status': 'complete'}
    assert request(app, 'GET', path).json()['commit_sha'] == commit
    identity['organizationId'] = ORG_B
    assert request(app, 'GET', path).status_code == 404


def test_github_mission_pins_commit_and_keeps_it_on_replay(monkeypatch):
    app, db, _, payload = mission_setup()
    scan = {**payload, 'mission_type': 'github_repository_assessment'}
    assert submit(app, scan).status_code == 403
    db.client_companies.documents[0]['mission_policy'] = {'github_assessment': 'require_approval'}
    authorized = {'repository': 'example/repo', 'repository_id': 20, 'branch': 'main'}
    calls = []

    async def scope(*args):
        return authorized

    async def resolve(github):
        assert github == authorized
        calls.append(github)
        return 'b' * 40

    monkeypatch.setattr(mission_services, 'authorized_github_scope', scope)
    monkeypatch.setattr(mission_services, 'resolve_github_commit', resolve)
    created = submit(app, scan)
    assert created.status_code == 201, created.text
    assert created.json()['source_commit'] == 'b' * 40
    assert submit(app, scan).json()['id'] == created.json()['id']
    assert len(calls) == 1
    assert len(db.mission_outbox.documents) == 1
