from copy import deepcopy
from unittest.mock import AsyncMock
import pytest
from pymongo.errors import AutoReconnect
from test_findings_remediations import setup
from test_projects import request, ORG_A, ORG_B
from routes.domain_overview import router
from utils.auth import get_current_user
from core.domain_indexes import domain_index_specs, ensure_domain_indexes
import asyncio


def application():
    app, db, identity, project_id, _, _ = setup()
    app.include_router(router, prefix='/api/domain/overview')
    return app, db, identity, project_id


def test_actual_counts_and_unavailable_score():
    app, _, _, project_id = application()
    result = request(app, 'GET', '/api/domain/overview?project_id=' + project_id)
    assert result.status_code == 200, result.text
    body = result.json()
    assert body['security_score'] is None and body['security_score_status'] == 'unavailable'
    assert body['counts'] == dict.fromkeys(['projects', 'assets', 'security_runs', 'findings', 'remediations'], 1)
    assert body['open_findings'] == 1 and body['critical_findings'] == 0
    assert body['severity_counts']['high'] == 1
    assert body['latest_security_run']['status'] == 'queued'
    assert len(body['recent_activity']) <= 5


def test_scope_empty_and_rejected_selectors():
    app, _, identity, project_id = application()
    assert request(app, 'GET', '/api/domain/overview?organization_id=' + ORG_A).status_code == 403
    identity['organizationId'] = ORG_B
    result = request(app, 'GET', '/api/domain/overview').json()
    assert all(v == 0 for v in result['counts'].values())
    assert result['latest_security_run'] is None and result['recent_activity'] == []
    assert request(app, 'GET', '/api/domain/overview?project_id=' + project_id).status_code == 404
    identity['role'] = 'superadmin'
    assert request(app, 'GET', '/api/domain/overview').status_code == 403
    assert request(app, 'GET', '/api/domain/overview?organization_id=' + ORG_A).json()['open_findings'] == 1


def test_unauthenticated_and_db_failure():
    app, db, _, _ = application()
    db.findings.count_documents = AsyncMock(side_effect=AutoReconnect('secret'))
    result = request(app, 'GET', '/api/domain/overview')
    assert result.status_code == 503 and 'secret' not in result.text
    del app.dependency_overrides[get_current_user]
    assert request(app, 'GET', '/api/domain/overview').status_code == 401


def test_resolved_counts_and_bounded_recent():
    from bson import ObjectId
    app, db, _, _ = application()
    db.findings.documents[0].update(status='resolved', severity='critical')
    for _ in range(8):
        item = deepcopy(db.activity_events.documents[0])
        item['_id'] = ObjectId()
        db.activity_events.documents.append(item)
    body = request(app, 'GET', '/api/domain/overview').json()
    assert body['critical_findings'] == body['open_findings'] == 0
    assert body['severity_counts']['critical'] == 1
    assert len(body['recent_activity']) == 5


def test_explicit_indexes_are_scoped_with_documented_worker_exceptions():
    specs = domain_index_specs()
    unique_names = set()
    global_indexes = {'installation_unique', 'status_updated', 'integration_repository_unique',
                      'expires_ttl', 'delivery_ttl'}
    for collection, indexes in specs.items():
        assert len({index.document['name'] for index in indexes}) == len(indexes)
        for index in indexes:
            if index.document['name'] == 'created_ttl':
                assert list(index.document['key']) == ['created_at']
                assert index.document['expireAfterSeconds'] == 2592000
            elif collection == 'mission_outbox':
                # The dispatcher claims pending work for all organizations.
                assert index.document['name'] in {'pending_commands', 'dispatch_schedule'}
                assert next(iter(index.document['key'])) == 'status'
            elif index.document['name'] not in global_indexes:
                assert next(iter(index.document['key'])) == 'organization_id'
            if index.document.get('unique', False):
                unique_names.add(index.document['name'])
    assert unique_names == {'org_fingerprint', 'org_run_scanner', 'organization_unique',
                            'installation_unique', 'org_repository_unique',
                            'integration_repository_unique', 'one_pr_per_remediation',
                            'org_request_key', 'org_mission_slot'}
    db = {name: AsyncMock() for name in specs}
    asyncio.run(ensure_domain_indexes(db))
    for name in specs:
        db[name].create_indexes.assert_awaited_once()
