"""Publish one verified synthetic patch in Tile_Studio's dedicated test branches."""
import asyncio
import base64
import json
import os
from dataclasses import replace
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from bson import ObjectId
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from core.database import DatabaseSettings, create_database_client, get_database, load_backend_environment
from core.domain_indexes import ensure_domain_indexes
from integrations.github.client import GitHubAPIError, GitHubAppClient
from integrations.github.config import GitHubAppSettings
from mission_orchestration.fixture_assessment import IsolatedSemgrepScanner, SCANNER_VERSION
from models.remediations import RemediationProposal
from routes.remediations import router
from security_engine.patch_integrity import patch_sha256
from security_engine.pull_request_pipeline import PullRequestPipeline
from security_engine.remediation_workspace import PatchApplicator, RemediationWorkspace
from security_engine.scanners.semgrep import RULES
from security_engine.storage import WorkerRepository
from security_engine.verification import compare_semgrep
from utils.auth import get_current_user


REPOSITORY = 'KathanGoda26/Tile_Studio'
REPOSITORY_ID = 1430214091
BASE_BRANCH = 'havosec/remediation-fixture-base'
PARENT = '550c53858aaddd011fa9d0d2939c98d358859618'
MONGO = 'mongodb://127.0.0.1:27249/?replicaSet=havosec_smoke'
FIXTURE = b'# Synthetic scanner fixture. Never imported by Tile_Studio.\ndef demo():\n    return eval("1 + 1")\n'
PATCH = '''--- a/app.py
+++ b/app.py
@@ -1,3 +1,3 @@
 # Synthetic scanner fixture. Never imported by Tile_Studio.
 def demo():
-    return eval("1 + 1")
+    return 2
'''


async def fixture_base(client):
    try:
        sha = await client.get_branch_head(REPOSITORY, BASE_BRANCH)
    except GitHubAPIError as error:
        if error.status_code != 404:
            raise
        blob = await client.create_blob(REPOSITORY, base64.b64encode(FIXTURE).decode('ascii'))
        tree = await client.create_tree(REPOSITORY, None, [
            {'path': 'app.py', 'mode': '100644', 'type': 'blob', 'sha': blob},
        ])
        sha = await client.create_commit(REPOSITORY, 'Seed HavoSec synthetic remediation fixture',
                                         tree, PARENT, '2026-11-17T00:00:00Z')
        await client.create_branch(REPOSITORY, BASE_BRANCH, sha)
    commit = await client.get_commit(REPOSITORY, sha)
    tree = await client.get_tree(REPOSITORY, commit['tree']['sha'])
    if set(tree) != {'app.py'} or tree['app.py'].get('mode') != '100644':
        raise RuntimeError('Refusing to use a test base with unexpected files')
    source = await client.get_blob(REPOSITORY, tree['app.py']['sha'], max_bytes=4096)
    if source != FIXTURE:
        raise RuntimeError('Refusing to use a test base with unexpected source')
    return sha, source


async def verify_patch(remediation_id, source):
    proposal = RemediationProposal(summary='Replace constant-input eval', explanation='Return the same constant.',
        affected_files=['app.py'], patch=PATCH, expected_security_effect='Removes the synthetic eval rule match.',
        potential_side_effects=[], recommended_tests=[], confidence=1)
    scanner = IsolatedSemgrepScanner(timeout=40, max_output_bytes=512_000, max_findings=20, targets=('app.py',))
    with RemediationWorkspace(remediation_id) as workspace:
        paths = workspace.paths
        paths.original.mkdir()
        (paths.original / 'app.py').write_bytes(source)
        (paths.artifacts / 'rules.yml').write_bytes(RULES.read_bytes())
        before = await scanner.scan(SimpleNamespace(repository=paths.original, artifacts=paths.artifacts))
        workspace.create_patched_copy()
        await PatchApplicator().apply(proposal, workspace, max_bytes=65_536, max_files=1, timeout=10)
        after = await scanner.scan(SimpleNamespace(repository=paths.patched, artifacts=paths.artifacts))
    if any(scan.errors or scan.scanner_version != SCANNER_VERSION or scan.metadata['scanned_paths'] != ['app.py']
           for scan in (before, after)):
        raise RuntimeError('Before and after scans did not both cover the fixture')
    if len(before.results) != 1 or after.results:
        raise RuntimeError('The expected fixture finding was not removed cleanly')
    hit = before.results[0]
    if not hit['check_id'].endswith('havosec.python.eval'):
        raise RuntimeError('The original scanner did not reproduce the fixture eval finding')
    evidence = {'rule_id': hit['check_id'], 'path': 'app.py', 'start_line': hit['start']['line']}
    result = compare_semgrep(remediation_id, {'severity': 'medium', 'evidence': evidence}, before, after)
    if result.status != 'verified':
        raise RuntimeError('The fixture patch did not pass verification')
    return proposal, evidence, result


class LostResponseClient(GitHubAppClient):
    async def create_pull_request(self, *args):
        await super().create_pull_request(*args)
        raise GitHubAPIError('Simulated lost response after GitHub accepted the PR')


async def publish(db, settings, installed, sha, proposal, evidence, result, remediation_id):
    organization, project, asset, actor, finding, integration = (ObjectId() for _ in range(6))
    scope = {'organization_id': str(organization), 'project_id': str(project)}
    now = datetime.now(timezone.utc)
    approval_digest = patch_sha256(proposal.patch)
    hex_remediation = str(remediation_id)
    link = {'provider': 'github', 'integration_id': str(integration), 'repository_id': REPOSITORY_ID,
            'repository_full_name': REPOSITORY, 'default_branch': BASE_BRANCH, 'connection_status': 'active'}
    await db.client_companies.insert_one({'_id': organization, 'status': 'active'})
    await db.projects.insert_one({'_id': project, 'organization_id': str(organization), 'status': 'active'})
    await db.assets.insert_one({'_id': asset, **scope, 'status': 'active', 'type': 'repository',
                                'source_control': link})
    await db.github_integrations.insert_one({'_id': integration, 'organization_id': str(organization),
                                             'status': 'active', **installed})
    await db.github_repositories.insert_one({'organization_id': str(organization), 'integration_id': str(integration),
        'repository_id': REPOSITORY_ID, 'full_name': REPOSITORY, 'default_branch': BASE_BRANCH,
        'authorized': True, 'connection_status': 'active'})
    await db.findings.insert_one({'_id': finding, **scope, 'asset_id': str(asset), 'status': 'open',
                                  'title': 'Synthetic eval fixture', 'severity': 'medium', 'evidence': evidence,
                                  'source_metadata': {'commit_sha': sha}})
    await db.remediations.insert_one({'_id': remediation_id, **scope, 'asset_id': str(asset), 'finding_id': str(finding),
        'status': 'awaiting_approval', 'summary': proposal.summary, 'recommendation': '', 'proposed_fix': '',
        'created_by': str(actor), 'approved_by': None, 'created_at': now, 'updated_at': now,
        'source_commit': sha, 'verified_source_commit': sha, 'verification_status': 'verified',
        'verification_result': result.model_dump(), 'proposal': proposal.model_dump(), 'verified_patch': proposal.patch,
        'verified_patch_sha256': approval_digest, 'verified_affected_files': ['app.py']})
    app = FastAPI()
    app.include_router(router, prefix='/api/remediations')
    app.dependency_overrides[get_database] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: {'id': str(actor), 'role': 'admin',
                                                           'organizationId': str(organization)}
    endpoint = '/api/remediations/' + hex_remediation
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as api:
        assert (await api.post(endpoint + '/pull-request')).status_code == 409
        stale = await api.patch(endpoint, json={'status': 'approved', 'approval_patch_sha256': '0' * 64,
                                                'approval_source_commit': sha})
        assert stale.status_code == 409
        print(f'Base commit: {sha}\nPatch SHA-256: {approval_digest}\n{proposal.patch}')
        if input('Type approve to publish this exact patch to the Tile_Studio test branch: ').strip() != 'approve':
            print('Publication cancelled.')
            return
        approved = await api.patch(endpoint, json={'status': 'approved', 'approval_patch_sha256': approval_digest,
                                                   'approval_source_commit': sha})
        assert approved.status_code == 200, approved.text
        queued = await api.post(endpoint + '/pull-request')
        assert queued.status_code == 202, queued.text
        # Keep the fixture's branch and commit identity stable across repeated runs.
        await db.pull_requests.update_one({'remediation_id': hex_remediation},
            {'$set': {'created_at': datetime(2026, 11, 17, tzinfo=timezone.utc)}})
        storage = WorkerRepository(db, 'tile-studio-publication-smoke', 300)
        claim = await storage.claim_pull_request()
        assert claim and claim['base_branch'] == BASE_BRANCH and claim['repository_id'] == REPOSITORY_ID
        publisher = PullRequestPipeline(storage,
            lambda installation, repo_id: LostResponseClient(replace(settings, installation_id=installation),
                                                                publication_repository_id=repo_id),
            PatchApplicator(), RemediationWorkspace, timeout=15, patch_max_bytes=65_536, patch_max_files=1)
        outcome = await publisher.process(claim)
        receipt = (await api.get(endpoint + '/pull-request')).json()
        if outcome != 'open':
            raise RuntimeError(receipt.get('error') or 'Publication did not complete')
        replay = await api.post(endpoint + '/pull-request')
        assert replay.json()['pr_number'] == receipt['pr_number']
        assert (await db.findings.find_one({'_id': finding}))['status'] == 'remediating'
        print(json.dumps({'pull_request': receipt['pr_url'], 'base_branch': receipt['base_branch'],
                          'patch_sha256': approval_digest, 'base_commit': sha, 'finding_status': 'remediating'}))


async def main():
    if os.environ.get('MISSION_TEST_MONGO_URL') != MONGO:
        raise RuntimeError('Run this with the isolated publication smoke launcher')
    load_backend_environment()
    settings = GitHubAppSettings.from_environment(require_installation=True)
    if settings.api_url != 'https://api.github.com':
        raise RuntimeError('The fixture can only be published on github.com')
    client = GitHubAppClient(settings, publication_repository_id=REPOSITORY_ID)
    installed = await client.get_installation()
    if any(installed['permissions'].get(permission) != 'write' for permission in ('contents', 'pull_requests')):
        raise RuntimeError('The HavoSec App installation needs Contents and Pull requests write access for this test')
    sha, source = await fixture_base(client)
    remediation_id = ObjectId(patch_sha256(sha + PATCH)[:24])
    proposal, evidence, result = await verify_patch(str(remediation_id), source)
    config = DatabaseSettings(MONGO, 'havosec_delivery_smoke_' + uuid4().hex[:16])
    mongo = create_database_client(config)
    try:
        db = mongo[config.database_name]
        await ensure_domain_indexes(db)
        await publish(db, settings, installed, sha, proposal, evidence, result, remediation_id)
    finally:
        try:
            await mongo.drop_database(config.database_name)
        finally:
            mongo.close()


if __name__ == '__main__':
    asyncio.run(main())
