from test_assets_runs import asset, setup
from test_projects import Collection, ORG_B, create, request

from routes.missions import router


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
