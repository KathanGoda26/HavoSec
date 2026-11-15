"""Explicit live test: creates and drops ONLY a fresh havosec_test_<uuid> database.

Uses configured MongoDB server, never the configured business database. No scanners.
Run with --run; without it, no network connection or mutation occurs.
"""
import argparse
import asyncio
from datetime import datetime, timezone
from uuid import uuid4
from bson import ObjectId
from fastapi import FastAPI
import httpx
import re
from urllib.parse import urlsplit, unquote
from pymongo.errors import DuplicateKeyError

from core.database import load_backend_environment, DatabaseSettings, create_database_client
load_backend_environment()  # Load signing configuration before auth module imports.
from core.domain_indexes import ensure_domain_indexes, domain_index_specs
from core.ownership import OrganizationScope
from repositories.projects import ProjectRepository
from models.findings import FindingResponse
from utils.auth import create_access_token
from routes.projects import router as projects
from routes.assets import router as assets
from routes.security_runs import router as runs
from routes.findings import router as findings
from routes.remediations import router as remediations
from routes.activity import router as activity
from routes.domain_overview import router as overview


def safe_error(exc, settings):
    details = getattr(exc, 'details', None) or {}
    message = details.get('errmsg', type(exc).__name__)
    parts = urlsplit(settings.mongo_url)
    for secret in [settings.mongo_url, parts.username, parts.password,
                   unquote(parts.password or ''), parts.hostname]:
        if secret:
            message = message.replace(secret, '[redacted]')
    return re.sub(r'[a-zA-Z0-9.-]+\.mongodb\.net', '[server]', message)[:500]


def test_database_name():
    # Atlas in this environment permits at most 38 UTF-8 bytes.
    return 'havosec_test_' + uuid4().hex[:24]


async def verify():
    load_backend_environment()
    settings = DatabaseSettings.from_environment()
    name = test_database_name()
    assert name != settings.database_name and len(name) <= 38
    client = create_database_client(settings)
    created = False
    stage = 'database access check'
    try:
        assert name not in await client.list_database_names(), 'Test database already exists'
        db = client[name]
        created = True
        stage = 'isolated index provisioning'
        await ensure_domain_indexes(db)
        await ensure_domain_indexes(db)  # repeat provisioning must be safe
        for collection, specs in domain_index_specs().items():
            installed = await db[collection].index_information()
            assert {s.document['name'] for s in specs} <= installed.keys()
        app = FastAPI()
        stage = 'isolated API lifecycle'
        app.state.db = db
        for router, prefix in [(projects, '/api/projects'), (assets, '/api/assets'), (runs, '/api/security-runs'),
                               (findings, '/api/findings'), (remediations, '/api/remediations'),
                               (activity, '/api/activity'), (overview, '/api/domain/overview')]:
            app.include_router(router, prefix=prefix)
        org_a, org_b = ObjectId(), ObjectId()
        await db.client_companies.insert_many([{'_id': oid, 'status': 'active'} for oid in [org_a, org_b]])
        tokens = {}
        for label, role, org in [('admin', 'admin', org_a), ('user', 'user', org_a), ('other', 'admin', org_b), ('platform', 'superadmin', None)]:
            uid = ObjectId()
            await db.users.insert_one({'_id': uid, 'role': role, 'organizationId': str(org) if org else None,
                                       'status': 'active', 'email': label + '@example.test'})
            tokens[label] = {'Authorization': 'Bearer ' + create_access_token(str(uid))}
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as http:
            async def call(method, path, expected=200, who='admin', **kwargs):
                response = await http.request(method, path, headers=tokens.get(who, {}), **kwargs)
                assert response.status_code == expected, f'{method} {path}: expected {expected}, got {response.status_code}'
                return response.json() if response.content else None
            p = await call('POST', '/api/projects', 201, json={'name': 'Integration project'})
            a = await call('POST', '/api/assets', 201, json={'project_id': p['id'], 'name': 'Fixture', 'type': 'domain', 'target': 'example.test'})
            r = await call('POST', '/api/security-runs', 201, json={'project_id': p['id'], 'asset_ids': [a['id']]})
            assert r['status'] == 'queued' and r['summary'] is None
            now, fid = datetime.now(timezone.utc), ObjectId()
            f = FindingResponse(id=str(fid), organization_id=str(org_a), project_id=p['id'], asset_id=a['id'],
                security_run_id=r['id'], title='Isolated fixture', source='integration_fixture', severity='critical',
                first_detected_at=now, last_detected_at=now, created_at=now, updated_at=now).model_dump()
            f['_id'] = ObjectId(f.pop('id'))
            await db.findings.insert_one(f)
            await call('GET', '/api/findings/' + str(fid))
            await call('PATCH', '/api/findings/' + str(fid), json={'status': 'triaged'})
            m = await call('POST', '/api/remediations', 201, json={'finding_id': str(fid), 'summary': 'Manual proposal'})
            for status in ['awaiting_approval', 'approved', 'resolved']:
                await call('PATCH', '/api/remediations/' + m['id'], json={'status': status})
            summary = await call('GET', '/api/domain/overview')
            assert summary['security_score'] is None and summary['open_findings'] == 1
            assert summary['counts']['remediations'] == 1
            events = await call('GET', '/api/activity')
            assert {'finding_updated', 'remediation_created'} <= {e['event_type'] for e in events['items']}
            for base, rid in [('projects', p['id']), ('assets', a['id']), ('security-runs', r['id']), ('findings', str(fid)), ('remediations', m['id'])]:
                await call('GET', f'/api/{base}/{rid}', 404, who='other')
                await call('GET', f'/api/{base}', 401, who='anonymous')
                page = await call('GET', f'/api/{base}', who='other')
                assert page['total'] == 0
            await call('POST', '/api/projects', 403, who='user', json={'name': 'Denied'})
            await call('PATCH', '/api/remediations/' + m['id'], 403, who='user', json={'status': 'pending'})
            await call('GET', '/api/domain/overview', 403, who='platform')
            await call('GET', '/api/domain/overview?organization_id=' + str(org_a), who='platform')
            await call('DELETE', '/api/projects/' + p['id'])
            await call('POST', '/api/security-runs', 409, json={'project_id': p['id'], 'asset_ids': [a['id']]})
            await call('PATCH', '/api/security-runs/' + r['id'] + '/cancel')
        # Force a real MongoDB transaction abort using a duplicate activity _id.
        stage = 'transaction rollback verification'
        event = await db.activity_events.find_one({})
        probe = {'_id': ObjectId(), 'organization_id': str(org_a), 'name': 'Must rollback'}
        try:
            await ProjectRepository(db).create_with_activity(probe, event)
            raise AssertionError('Expected duplicate event failure')
        except DuplicateKeyError:
            assert await db.projects.find_one({'_id': probe['_id']}) is None
        print('PASS: real JWT + MongoDB lifecycle, isolation, role checks, indexes and transaction rollback.')
    except Exception as exc:
        print('Failed at ' + stage + ': ' + safe_error(exc, settings))
        raise
    finally:
        try:
            if created:
                assert name.startswith('havosec_test_') and name != settings.database_name
                await client.drop_database(name)
                print('Removed isolated test database: ' + name)
        finally:
            client.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true')
    if parser.parse_args().run:
        try:
            asyncio.run(verify())
        except Exception as exc:
            # Never print MongoDB topology/connection strings or credentials.
            code = getattr(exc, 'code', None)
            reason = {18: 'MongoDB authentication failed', 13: 'MongoDB permission denied',
                      8000: 'MongoDB Atlas rejected the operation'}.get(code, 'Inspect safely before retrying')
            if 'auth' in str(exc).lower():
                reason = 'MongoDB authentication failed; verify the configured database credentials'
            raise SystemExit(f'Integration verification failed ({type(exc).__name__}, code={code}): {reason}.')
    else:
        print('Pass --run to create, verify and remove a fresh isolated test database.')
