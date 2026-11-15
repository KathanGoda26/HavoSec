"""Run one explicitly authorized, end-to-end HavoSec V1 security cycle.

Without --run this command only describes its behavior. The target is intentionally
fixed to the public OWASP Juice Shop repository; arbitrary targets are not accepted.
"""
import argparse
import asyncio
import os
import re
from functools import partial
from pathlib import Path
from urllib.parse import unquote, urlsplit
from uuid import uuid4

from bson import ObjectId
from fastapi import FastAPI
import httpx

from core.database import DatabaseSettings, create_database_client, load_backend_environment

load_backend_environment()

from core.domain_indexes import ensure_domain_indexes
from core.membership import membership_value
from routes.activity import router as activity_router
from routes.assets import router as assets_router
from routes.clients import router as clients_router
from routes.findings import router as findings_router
from routes.projects import router as projects_router
from routes.security_runs import router as runs_router
from security_engine.pipeline import SecurityPipeline
from security_engine.repository import GitRepository
from security_engine.scanners.semgrep import SemgrepScanner
from security_engine.storage import WorkerRepository
from security_engine.workspace import RunWorkspace
from utils.auth import create_access_token


REPOSITORY = 'https://github.com/juice-shop/juice-shop'
SCANNER_BIN = Path(__file__).resolve().parent / '.tools' / 'semgrep-venv' / 'Scripts'


def safe_error(exc, settings):
    message = str(exc)
    parts = urlsplit(settings.mongo_url)
    for secret in (settings.mongo_url, parts.password,
                   unquote(parts.password or ''), parts.hostname):
        if secret:
            message = message.replace(secret, '[redacted]')
    return re.sub(r'[a-zA-Z0-9.-]+\.mongodb\.net', '[server]', message)[:500]


async def eligible_admin(db, requested_org=None):
    matches = []
    async for account in db.users.find({'role': {'$in': ['admin', 'superadmin']},
                                        'status': {'$ne': 'inactive'},
                                        'isActive': {'$ne': False}}):
        organization_id, state = membership_value(account)
        if state != 'assigned' or not ObjectId.is_valid(organization_id):
            continue
        organization_id = str(ObjectId(organization_id))
        if requested_org and organization_id != str(ObjectId(requested_org)):
            continue
        organization = await db.client_companies.find_one(
            {'_id': ObjectId(organization_id), 'status': {'$ne': 'inactive'}})
        if organization:
            matches.append((account, organization_id))
    if not matches:
        superadmin = await db.users.find_one({'role': 'superadmin', 'status': {'$ne': 'inactive'},
                                              'isActive': {'$ne': False}})
        if superadmin:
            if requested_org:
                organization = await db.client_companies.find_one(
                    {'_id': ObjectId(requested_org), 'status': {'$ne': 'inactive'},
                     'isActive': {'$ne': False}})
                if organization:
                    return superadmin, str(ObjectId(requested_org))
            else:
                verification_org = await db.client_companies.find_one(
                    {'name': 'HavoSec V1 Verification', 'status': 'active',
                     'isActive': {'$ne': False}}, sort=[('created_at', -1)])
                return superadmin, str(verification_org['_id']) if verification_org else None
        raise RuntimeError('No active organization administrator is available for verification')
    organizations = sorted({item[1] for item in matches})
    if len(organizations) > 1 and not requested_org:
        raise RuntimeError('Multiple eligible organizations exist; rerun with --organization-id ' + organizations[0])
    return next(item for item in matches if item[1] == organizations[0])


def verification_app(db):
    app = FastAPI()
    app.state.db = db
    for router, prefix in ((projects_router, '/api/projects'), (assets_router, '/api/assets'),
                           (runs_router, '/api/security-runs'), (findings_router, '/api/findings'),
                           (activity_router, '/api/activity'), (clients_router, '/api/clients')):
        app.include_router(router, prefix=prefix)
    return app


async def verify(organization_id=None):
    settings = DatabaseSettings.from_environment()
    client = create_database_client(settings)
    stage = 'database connection'
    try:
        db = client[settings.database_name]
        await db.command('ping')
        await ensure_domain_indexes(db)
        stage = 'operator authorization selection'
        account, organization_id = await eligible_admin(db, organization_id)
        platform_scope = account.get('role') == 'superadmin'
        token = create_access_token(str(account['_id']))
        headers = {'Authorization': 'Bearer ' + token}
        app = verification_app(db)
        name = 'HavoSec V1 Authorized Demo ' + uuid4().hex[:8]
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://verification') as http:
            async def call(method, path, expected=200, scoped=True, **kwargs):
                if scoped and platform_scope:
                    separator = '&' if '?' in path else '?'
                    path += separator + 'organization_id=' + organization_id
                response = await http.request(method, path, headers=headers, **kwargs)
                if response.status_code != expected:
                    raise RuntimeError(f'{method} {path} returned {response.status_code}')
                return response.json()

            if platform_scope:
                stage = 'verification organization registration'
                created = await call('POST', '/api/clients/', 200, scoped=False, json={
                    'name': 'HavoSec V1 Verification', 'email': account.get('email')})
                organization_id = created['client']['id']
            stage = 'project and repository registration'
            project = await call('POST', '/api/projects', 201,
                                 json={'name': name, 'description': 'Authorized OWASP Juice Shop V1 verification'})
            asset = await call('POST', '/api/assets', 201, json={
                'project_id': project['id'], 'name': 'OWASP Juice Shop', 'type': 'repository',
                'target': REPOSITORY, 'metadata': {}})
            run = await call('POST', '/api/security-runs', 201, json={
                'project_id': project['id'], 'asset_ids': [asset['id']], 'type': 'standard'})

            stage = 'security worker execution'
            os.environ['PATH'] = str(SCANNER_BIN) + os.pathsep + os.environ.get('PATH', '')
            repository = WorkerRepository(db, 'verification-' + uuid4().hex, 960)
            claimed = await repository.claim(run['id'])
            if not claimed:
                raise RuntimeError('The newly created run could not be claimed')
            pipeline = SecurityPipeline(
                repository, GitRepository(180, 4_000_000), SemgrepScanner(600, 4_000_000, 500),
                partial(RunWorkspace, keep=False), {organization_id: frozenset({REPOSITORY})})
            outcome = await pipeline.process(claimed)

            stage = 'saved result verification'
            saved = await call('GET', '/api/security-runs/' + run['id'])
            page = await call('GET', '/api/findings?security_run_id=' + run['id'] + '&limit=100')
            events = await call('GET', '/api/activity?limit=100')
            if outcome != 'completed' or saved['status'] != 'completed':
                raise RuntimeError('The security run did not complete successfully')
            if not re.fullmatch(r'[0-9a-f]{40}', saved.get('commit_sha') or ''):
                raise RuntimeError('The checked-out commit was not persisted')
            event_types = {event['event_type'] for event in events['items']
                           if event.get('entity_id') == run['id']}
            if not {'security_run_started', 'findings_created', 'security_run_completed'} <= event_types:
                raise RuntimeError('The run lifecycle activity was not persisted')

        summary = saved.get('summary') or {}
        print('PASS: authorized repository security cycle completed and is visible through the API.')
        print('Repository:', REPOSITORY)
        print('Project:', project['id'], '-', project['name'])
        print('Asset:', asset['id'])
        print('Run:', saved['id'], '-', saved['status'])
        print('Commit:', saved['commit_sha'])
        print('Scanner:', saved.get('scanner'), saved.get('scanner_version'))
        print('Raw scanner results:', summary.get('scanner_findings', 0))
        print('Normalized findings:', summary.get('normalized_findings', 0))
        print('API-visible findings:', page['total'])
        print('Analysis mode:', saved.get('analysis_mode'))
        print('Severity counts:', {key: summary.get(key, 0) for key in ('critical', 'high', 'medium', 'low', 'info')})
        print('Temporary workspace cleanup: enabled')
    except Exception as exc:
        raise RuntimeError('Failed at ' + stage + ': ' + safe_error(exc, settings)) from exc
    finally:
        client.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true')
    parser.add_argument('--organization-id', type=str)
    args = parser.parse_args()
    if args.organization_id and not ObjectId.is_valid(args.organization_id):
        parser.error('--organization-id must be a MongoDB ObjectId')
    if args.run:
        asyncio.run(verify(args.organization_id))
    else:
        print('Pass --run to register and scan the fixed authorized OWASP Juice Shop repository once.')
