import asyncio
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from bson import ObjectId

from integrations.github.client import GitHubAPIError
from security_engine.pull_request_pipeline import PullRequestPipeline
from security_engine.remediation_workspace import RemediationWorkspace


PATCH = "--- a/app.py\n+++ b/app.py\n@@ -1 +1 @@\n-print('old')\n+print('safe')\n"


class Patcher:
    async def apply(self, proposal, workspace, **kwargs):
        workspace.paths.patched.joinpath('app.py').write_text("print('safe')\n", encoding='utf-8')
        return SimpleNamespace(files=('app.py',))


def record():
    return {
        '_id': ObjectId(), 'organization_id': 'a' * 24, 'project_id': 'b' * 24,
        'asset_id': 'c' * 24, 'finding_id': 'd' * 24, 'remediation_id': 'e' * 24,
        'repository_full_name': 'KathanGoda26/havosec-github-integration-test',
        'base_branch': 'main', 'branch': 'havosec/remediation-' + 'e' * 12,
        'expected_source_commit': '1' * 40, 'verified_patch_sha256': __import__('hashlib').sha256(PATCH.encode()).hexdigest(),
        'created_at': datetime(2026, 9, 4, tzinfo=timezone.utc),
    }


@pytest.mark.parametrize('lose_response', [False, True])
def test_exact_patch_creates_one_deterministic_commit_branch_and_pr(tmp_path, lose_response):
    item = record()
    remediation = {
        'proposal': {'summary': 'Fix', 'explanation': 'Fix safely', 'affected_files': ['app.py'],
                     'patch': PATCH, 'expected_security_effect': 'Removes issue',
                     'potential_side_effects': [], 'recommended_tests': [], 'confidence': 1},
        'verified_patch': PATCH, 'verified_patch_sha256': item['verified_patch_sha256'],
        'verified_affected_files': ['app.py'], 'source_commit': '1' * 40,
        'verified_source_commit': '1' * 40,
    }
    storage = AsyncMock()
    storage.load_pull_request_context.return_value = (
        remediation, {'title': 'Unsafe eval', 'severity': 'medium'}, {},
        {'installation_id': 159047858}, {},
    )
    client = AsyncMock()
    branch_created = False
    pr_created = False
    receipt = {'number': 1, 'url': 'https://github.com/test/pull/1', 'state': 'open'}

    async def head(_, branch):
        if branch == 'main':
            return '1' * 40
        if branch_created:
            return '6' * 40
        raise GitHubAPIError('missing', 404)

    async def branch(*args):
        nonlocal branch_created
        branch_created = True
        if lose_response:
            raise GitHubAPIError('connection closed')

    async def create_pr(*args):
        nonlocal pr_created
        pr_created = True
        if lose_response:
            raise GitHubAPIError('connection closed')
        return receipt

    async def find_pr(*args):
        return receipt if pr_created else None

    client.get_branch_head.side_effect = head
    client.get_commit.return_value = {'tree': {'sha': '2' * 40}}
    client.get_tree.return_value = {'app.py': {'type': 'blob', 'mode': '100644', 'sha': '3' * 40}}
    client.get_blob.return_value = b"print('old')\n"
    client.create_blob.return_value = '4' * 40
    client.create_tree.return_value = '5' * 40
    client.create_commit.return_value = '6' * 40
    client.create_branch.side_effect = branch
    client.find_pull_request.side_effect = find_pr
    client.create_pull_request.side_effect = create_pr
    pipeline = PullRequestPipeline(
        storage, lambda *_: client, Patcher(),
        lambda identity: RemediationWorkspace(identity, parent=tmp_path),
        timeout=30, patch_max_bytes=65536, patch_max_files=5,
    )
    assert asyncio.run(pipeline.process(item)) == 'open'
    assert asyncio.run(pipeline.process(item)) == 'open'
    client.create_branch.assert_awaited_once_with(item['repository_full_name'], item['branch'], '6' * 40)
    client.create_pull_request.assert_awaited_once()
    assert storage.complete_pull_request.await_count == 2
    assert all(call.args == (item, '6' * 40, receipt)
               for call in storage.complete_pull_request.await_args_list)


def test_extra_changed_file_aborts_before_github_writes(tmp_path):
    class ExtraPatcher(Patcher):
        async def apply(self, proposal, workspace, **kwargs):
            result = await super().apply(proposal, workspace, **kwargs)
            workspace.paths.patched.joinpath('extra.py').write_text('extra', encoding='utf-8')
            return result

    item = record()
    remediation = {'proposal': {'summary': 'Fix', 'explanation': 'Fix safely', 'affected_files': ['app.py'],
        'patch': PATCH, 'expected_security_effect': 'Removes issue', 'potential_side_effects': [],
        'recommended_tests': [], 'confidence': 1}, 'verified_patch': PATCH,
        'verified_patch_sha256': item['verified_patch_sha256'], 'verified_affected_files': ['app.py'],
        'source_commit': '1' * 40, 'verified_source_commit': '1' * 40}
    storage, client = AsyncMock(), AsyncMock()
    storage.load_pull_request_context.return_value = (remediation, {}, {}, {'installation_id': 1}, {})
    client.get_branch_head.return_value = '1' * 40
    client.get_commit.return_value = {'tree': {'sha': '2' * 40}}
    client.get_tree.return_value = {'app.py': {'type': 'blob', 'mode': '100644', 'sha': '3' * 40}}
    client.get_blob.return_value = b"print('old')\n"
    pipeline = PullRequestPipeline(storage, lambda *_: client, ExtraPatcher(),
        lambda identity: RemediationWorkspace(identity, parent=tmp_path), timeout=30,
        patch_max_bytes=65536, patch_max_files=5)
    assert asyncio.run(pipeline.process(item)) == 'failed'
    client.create_blob.assert_not_awaited()
    storage.fail_pull_request.assert_awaited_once()
