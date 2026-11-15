from copy import deepcopy
from datetime import datetime, timezone, timedelta
from bson import ObjectId
import pytest
from pydantic import ValidationError

from test_assets_runs import records
from test_projects import Collection, request, ORG_A, ORG_B, create
from models.findings import FindingResponse
from routes.findings import router as findings_router
from routes.remediations import router as remediations_router
from utils.auth import get_current_user


def setup():
    app, db, identity, project_id, asset_id, run_id = records()
    db.findings = Collection()
    db.remediations = Collection()
    app.include_router(findings_router, prefix='/api/findings')
    app.include_router(remediations_router, prefix='/api/remediations')
    now = datetime.now(timezone.utc)
    finding_id = str(ObjectId())
    # Trusted test fixture only; no HTTP finding creation or live database write.
    record = FindingResponse(id=finding_id, organization_id=ORG_A, project_id=project_id,
        asset_id=asset_id, security_run_id=run_id, title='Test finding', severity='high',
        source='test_fixture', first_detected_at=now, last_detected_at=now, created_at=now, updated_at=now).model_dump()
    record['_id'] = ObjectId(record.pop('id'))
    record['validation'] = {'finding_id': finding_id, 'security_run_id': run_id,
        'status': 'confirmed', 'confidence': 0.9, 'reasoning_summary': 'Trusted test fixture.',
        'evidence_summary': 'Test-only evidence.', 'supporting_factors': ['Test setup'],
        'uncertainties': [], 'validated_at': now, 'validation_method': 'deterministic',
        'requested_by': 'test-setup'}
    db.findings.documents.append(record)
    response = request(app, 'POST', '/api/remediations', json={'finding_id': finding_id, 'summary': 'Review input validation'})
    assert response.status_code == 201, response.text
    return app, db, identity, project_id, finding_id, response.json()['id']


def patch(app, remediation_id, **payload):
    return request(app, 'PATCH', '/api/remediations/' + remediation_id, json=payload)


def test_lifecycle_approval_history_and_no_execution():
    app, db, identity, _, finding_id, remediation_id = setup()
    created = request(app, 'GET', '/api/remediations/' + remediation_id).json()
    assert created['asset_id'] and created['source_security_run_id']
    assert created['proposal'] is None and created['verification_status'] == 'not_started'
    assert request(app, 'PATCH', '/api/findings/' + finding_id, json={'status': 'triaged'}).status_code == 200
    assert patch(app, remediation_id, status='approved').status_code == 409
    for status in ['in_progress', 'awaiting_approval']:
        result = patch(app, remediation_id, status=status)
        assert result.status_code == 200, result.text
    # M5 requires immutable verification evidence before human approval.
    assert patch(app, remediation_id, status='approved').status_code == 409
    assert result.json()['approved_by'] is None
    assert patch(app, remediation_id, proposed_fix='different').status_code == 409
    assert patch(app, remediation_id, status='pending', proposed_fix='New proposal').json()['approved_by'] is None
    assert request(app, 'GET', '/api/findings/' + finding_id).json()['status'] == 'triaged'
    assert db.security_runs.documents[0]['status'] == 'queued'
    events = request(app, 'GET', '/api/activity').json()['items']
    assert {'finding_updated', 'remediation_created', 'remediation_updated'} <= {e['event_type'] for e in events}
    count = len(events)
    assert patch(app, remediation_id, status='pending').status_code == 200
    assert request(app, 'GET', '/api/activity').json()['total'] == count


def test_deterministic_validation_is_conservative_and_persisted():
    app, db, identity, _, finding_id, _ = setup()
    finding = db.findings.documents[0]
    finding.update(source='semgrep', fingerprint='a' * 64, confidence=0.7,
                   evidence={'rule_id': 'havosec.python.eval', 'path': 'app.py', 'start_line': 3,
                             'end_line': 3, 'snippet_sha256': 'b' * 64},
                   source_metadata={'commit_sha': 'c' * 40})
    response = request(app, 'POST', f'/api/findings/{finding_id}/validate')
    assert response.status_code == 200, response.text
    result = response.json()
    assert result['status'] == 'likely' and result['confidence'] == 0.8
    assert result['validation_method'] == 'deterministic' and result['requested_by'] == identity['id']
    saved = request(app, 'GET', f'/api/findings/{finding_id}').json()
    assert saved['validation']['status'] == 'likely'
    assert saved['status'] == 'new'  # Isolated assessment is not confirmation or resolution.
    events = request(app, 'GET', '/api/activity').json()['items']
    assert events[0]['event_type'] == 'finding_validated'


def test_incomplete_evidence_requires_review():
    app, _, _, _, finding_id, _ = setup()
    result = request(app, 'POST', f'/api/findings/{finding_id}/validate')
    assert result.status_code == 200
    assert result.json()['status'] == 'needs_review'
    assert result.json()['uncertainties']


def test_remediation_requires_eligible_stored_validation_and_likely_acknowledgement():
    app, db, _, _, finding_id, _ = setup()
    finding = db.findings.documents[0]
    finding.pop('validation')
    payload = {'finding_id': finding_id, 'summary': 'Second proposal'}
    assert request(app, 'POST', '/api/remediations', json=payload).status_code == 409
    finding['validation'] = {'status': 'needs_review'}
    assert request(app, 'POST', '/api/remediations', json=payload).status_code == 409
    finding['validation'] = {'status': 'likely'}
    assert request(app, 'POST', '/api/remediations', json=payload).status_code == 409
    accepted = request(app, 'POST', '/api/remediations', json=payload | {'acknowledge_likely': True})
    assert accepted.status_code == 201
    assert 'acknowledge_likely' not in db.remediations.documents[-1]


@pytest.mark.parametrize('role', ['admin', 'user'])
def test_tenant_isolation(role):
    app, _, identity, project_id, finding_id, remediation_id = setup()
    identity.update(role=role, organizationId=ORG_B)
    for base, resource_id in [('findings', finding_id), ('remediations', remediation_id)]:
        assert request(app, 'GET', '/api/' + base).json()['items'] == []
        assert request(app, 'GET', f'/api/{base}/{resource_id}').status_code == 404
        assert request(app, 'GET', f'/api/{base}?project_id={project_id}').status_code == 404
        assert request(app, 'PATCH', f'/api/{base}/{resource_id}', json={'status': 'resolved'}).status_code == (404 if role == 'admin' else 403)
    assert request(app, 'POST', '/api/remediations', json={'finding_id': finding_id, 'summary': 'No'}).status_code == (404 if role == 'admin' else 403)
    assert request(app, 'POST', f'/api/findings/{finding_id}/validate').status_code == (404 if role == 'admin' else 403)


@pytest.mark.parametrize('method,path', [('GET', '/api/findings'), ('GET', '/api/findings/' + ORG_A),
    ('PATCH', '/api/findings/' + ORG_A), ('POST', '/api/findings/' + ORG_A + '/validate'),
    ('GET', '/api/remediations'), ('POST', '/api/remediations'),
    ('GET', '/api/remediations/' + ORG_A), ('PATCH', '/api/remediations/' + ORG_A)])
def test_authentication(method, path):
    app, _, _, _, _, _ = setup()
    del app.dependency_overrides[get_current_user]
    assert request(app, method, path, json={}).status_code == 401


def test_user_read_only():
    app, _, identity, _, finding_id, remediation_id = setup()
    identity['role'] = 'user'
    for path in ['/api/findings', '/api/remediations']:
        assert request(app, 'GET', path).status_code == 200
    assert patch(app, remediation_id, status='approved').status_code == 403
    assert request(app, 'PATCH', '/api/findings/' + finding_id, json={'status': 'resolved'}).status_code == 403
    assert request(app, 'POST', '/api/findings/' + finding_id + '/validate').status_code == 403
    assert request(app, 'POST', '/api/remediations', json={'finding_id': finding_id, 'summary': 'No'}).status_code == 403


@pytest.mark.parametrize('field', ['organization_id', 'project_id', 'created_by', 'approved_by', 'created_at', 'status'])
def test_remediation_controlled_fields(field):
    app, _, _, _, finding_id, remediation_id = setup()
    assert request(app, 'POST', '/api/remediations', json={'finding_id': finding_id, 'summary': 'No', field: 'injected'}).status_code == 422
    if field != 'status':
        assert patch(app, remediation_id, **{field: 'injected'}).status_code == 422


def test_findings_cannot_be_fabricated_or_rewritten():
    app, _, _, _, finding_id, _ = setup()
    assert request(app, 'POST', '/api/findings', json={}).status_code == 405
    for field in ['severity', 'evidence', 'source', 'asset_id', 'organization_id']:
        assert request(app, 'PATCH', '/api/findings/' + finding_id, json={'status': 'triaged', field: 'injected'}).status_code == 422


@pytest.mark.parametrize('base', ['findings', 'remediations'])
def test_filters_pagination_and_bad_ids(base):
    app, _, _, project_id, finding_id, _ = setup()
    assert request(app, 'GET', f'/api/{base}?project_id={project_id}').json()['total'] == 1
    assert request(app, 'GET', f'/api/{base}?limit=1&offset=1').json()['items'] == []
    for query in ['limit=0', 'limit=101', 'offset=-1', 'offset=100001', 'status=invalid']:
        assert request(app, 'GET', f'/api/{base}?{query}').status_code == 422
    assert request(app, 'GET', f'/api/{base}/bad').status_code == 404
    assert request(app, 'GET', f'/api/{base}?project_id=bad').status_code == 404
    assert request(app, 'GET', '/api/findings?severity=low').json()['total'] == 0
    assert request(app, 'GET', '/api/remediations?finding_id=' + finding_id).json()['total'] == 1


def test_cross_project_relationships_fail_closed():
    app, db, _, _, finding_id, remediation_id = setup()
    other = create(app)
    db.findings.documents[0]['project_id'] = other
    assert request(app, 'GET', '/api/findings/' + finding_id).status_code == 404
    assert request(app, 'GET', '/api/findings').status_code == 404
    assert request(app, 'GET', '/api/remediations/' + remediation_id).status_code == 404


def test_archived_project_preserves_reads_blocks_writes():
    app, _, _, project_id, finding_id, remediation_id = setup()
    request(app, 'DELETE', '/api/projects/' + project_id)
    assert request(app, 'GET', '/api/findings/' + finding_id).status_code == 200
    assert request(app, 'GET', '/api/remediations/' + remediation_id).status_code == 200
    assert patch(app, remediation_id, summary='No').status_code == 409
    assert request(app, 'PATCH', '/api/findings/' + finding_id, json={'status': 'resolved'}).status_code == 409
    assert request(app, 'POST', '/api/remediations', json={'finding_id': finding_id, 'summary': 'No'}).status_code == 409


@pytest.mark.parametrize('operation', ['finding_update', 'finding_validation', 'remediation_create', 'remediation_update'])
def test_activity_failure_rolls_back(operation):
    app, db, _, _, finding_id, remediation_id = setup()
    collections = [db.projects, db.findings, db.remediations, db.activity_events]
    before = [deepcopy(c.documents) for c in collections]
    db.activity_events.fail_insert = True
    if operation == 'finding_update':
        result = request(app, 'PATCH', '/api/findings/' + finding_id, json={'status': 'resolved'})
    elif operation == 'finding_validation':
        result = request(app, 'POST', '/api/findings/' + finding_id + '/validate')
    elif operation == 'remediation_create':
        result = request(app, 'POST', '/api/remediations', json={'finding_id': finding_id, 'summary': 'Another'})
    else:
        result = patch(app, remediation_id, summary='Changed')
    assert result.status_code == 503 and 'sensitive' not in result.text
    assert [c.documents for c in collections] == before


def test_stale_proposal_cannot_be_approved(monkeypatch):
    from repositories.project_resources import ProjectResourceRepository
    app, db, _, _, _, remediation_id = setup()
    assert patch(app, remediation_id, status='awaiting_approval').status_code == 200
    original = ProjectResourceRepository.update_with_activity

    async def concurrent_change(self, *args, **kwargs):
        db.remediations.documents[0]['updated_at'] += timedelta(seconds=1)
        return await original(self, *args, **kwargs)

    monkeypatch.setattr(ProjectResourceRepository, 'update_with_activity', concurrent_change)
    assert patch(app, remediation_id, status='approved').status_code == 409
    assert db.remediations.documents[0]['approved_by'] is None


def test_admin_can_queue_one_bounded_asynchronous_verification_attempt():
    app, db, _, _, _, remediation_id = setup()
    remediation = db.remediations.documents[0]
    remediation['source_commit'] = 'a' * 40
    response = request(app, 'POST', f'/api/remediations/{remediation_id}/verify')
    assert response.status_code == 202, response.text
    queued = response.json()
    assert queued['status'] == 'in_progress'
    assert queued['verification_status'] == 'queued'
    assert queued['verification_attempts'] == 1
    assert queued['verification_result'] is None
    assert request(app, 'POST', f'/api/remediations/{remediation_id}/verify').status_code == 409
    event = request(app, 'GET', '/api/activity').json()['items'][0]
    assert event['event_type'] == 'remediation_verification_queued'
    assert event['metadata']['attempt'] == 1


def test_verification_queue_requires_reproducible_source_and_admin_role():
    app, db, identity, _, _, remediation_id = setup()
    assert request(app, 'POST', f'/api/remediations/{remediation_id}/verify').status_code == 409
    db.remediations.documents[0]['source_commit'] = 'a' * 40
    identity['role'] = 'user'
    assert request(app, 'POST', f'/api/remediations/{remediation_id}/verify').status_code == 403


@pytest.mark.parametrize('field,value', [('cvss', 11), ('confidence', 2), ('evidence', {'x': 'a' * 65537}), ('source_metadata', {'x': float('nan')})])
def test_finding_record_bounds(field, value):
    _, db, _, _, finding_id, _ = setup()
    record = {**db.findings.documents[0], 'id': finding_id, field: value}
    with pytest.raises(ValidationError):
        FindingResponse.model_validate(record)


def test_platform_scope_and_routes():
    app, _, identity, _, _, _ = setup()
    assert request(app, 'GET', '/api/findings?organization_id=' + ORG_A).status_code == 403
    identity['role'] = 'superadmin'
    for path in ['/api/findings', '/api/remediations']:
        assert request(app, 'GET', path).status_code == 403
        assert request(app, 'GET', path + '?organization_id=' + ORG_A).json()['total'] == 1
        assert request(app, 'GET', path + '?organization_id=' + ORG_B).json()['total'] == 0
    from server import app as main_app
    assert {'/api/findings', '/api/remediations'} <= {r.path for r in main_app.routes}
