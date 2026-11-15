"""Deliver one exact verified patch to GitHub without regenerating it."""

import base64
from datetime import timezone
from pathlib import Path, PurePosixPath

from integrations.github.client import GitHubAPIError, GitHubAppClient
from models.remediations import RemediationProposal
from security_engine.executor import ExecutionError
from security_engine.patch_integrity import (PatchIntegrityError, assert_patch_secret_safe,
                                             assert_verified_patch)
from security_engine.remediation import PatchSafetyError, safe_relative_path
from security_engine.storage import RunChanged


class PullRequestPipeline:
    def __init__(self, storage, client_factory, patcher, workspace_factory, *,
                 timeout, patch_max_bytes, patch_max_files, max_source_file_bytes=10_000_000):
        self.storage, self.client_factory, self.patcher = storage, client_factory, patcher
        self.workspace_factory = workspace_factory
        self.timeout, self.patch_max_bytes, self.patch_max_files = timeout, patch_max_bytes, patch_max_files
        self.max_source_file_bytes = max_source_file_bytes

    async def process(self, record):
        try:
            return await self._process(record)
        except RunChanged:
            return 'cancelled_or_changed'
        except (ValueError, PatchIntegrityError, PatchSafetyError):
            await self.storage.fail_pull_request(record, 'Stored remediation integrity validation failed')
        except (GitHubAPIError, ExecutionError):
            await self.storage.fail_pull_request(record, 'Pull request delivery could not be completed safely')
        except Exception:
            await self.storage.fail_pull_request(record, 'Pull request delivery failed unexpectedly')
        return 'failed'

    async def _process(self, record):
        remediation, finding, _, integration, repository = await self.storage.load_pull_request_context(record)
        assert_verified_patch(remediation)
        assert_patch_secret_safe(remediation)
        proposal = RemediationProposal.model_validate(remediation['proposal'])
        client = self.client_factory(integration['installation_id'])
        name, base, expected = record['repository_full_name'], record['base_branch'], record['expected_source_commit']
        if await client.get_branch_head(name, base) != expected:
            raise ValueError('Repository source changed after PR operation was queued')
        commit = await client.get_commit(name, expected)
        base_tree = (commit.get('tree') or {}).get('sha')
        if not isinstance(base_tree, str) or len(base_tree) != 40:
            raise GitHubAPIError('GitHub returned an invalid commit tree')
        remote_tree = await client.get_tree(name, base_tree)

        with self.workspace_factory(str(record['_id'])) as workspace:
            workspace.paths.original.mkdir()
            modes = {}
            for declared in proposal.affected_files:
                relative = safe_relative_path(declared)
                entry = remote_tree.get(relative)
                if not entry or entry.get('type') != 'blob' or entry.get('mode') not in {'100644', '100755'}:
                    raise ValueError('Verified affected file is unavailable at the expected commit')
                content = await client.get_blob(name, entry.get('sha'), max_bytes=self.max_source_file_bytes)
                target = workspace.paths.original.joinpath(*PurePosixPath(relative).parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(content)
                modes[relative] = entry['mode']
            workspace.create_patched_copy()
            safe_patch = await self.patcher.apply(
                proposal, workspace, max_bytes=self.patch_max_bytes,
                max_files=self.patch_max_files, timeout=self.timeout,
            )
            changed = _changed_files(workspace.paths.original, workspace.paths.patched)
            if set(changed) != set(safe_patch.files) or set(changed) != set(remediation['verified_affected_files']):
                raise PatchIntegrityError('Actual changed files do not match the verified patch')
            tree_entries = []
            for relative in changed:
                content = workspace.paths.patched.joinpath(*PurePosixPath(relative).parts).read_bytes()
                blob_sha = await client.create_blob(name, base64.b64encode(content).decode('ascii'))
                tree_entries.append({'path': relative, 'mode': modes[relative], 'type': 'blob', 'sha': blob_sha})

        tree_sha = await client.create_tree(name, base_tree, tree_entries)
        created_at = record['created_at']
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        timestamp = created_at.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')
        commit_sha = await client.create_commit(
            name, f"HavoSec remediation {record['remediation_id']}", tree_sha, expected, timestamp
        )
        branch_head = await _branch_head_or_none(client, name, record['branch'])
        if branch_head is None:
            try:
                await client.create_branch(name, record['branch'], commit_sha)
            except GitHubAPIError as exc:
                if exc.status_code != 422 or await client.get_branch_head(name, record['branch']) != commit_sha:
                    raise
        elif branch_head != commit_sha:
            raise ValueError('Deterministic HavoSec branch already points to unexpected content')

        owner = name.split('/', 1)[0]
        pull_request = await client.find_pull_request(name, owner, record['branch'], base)
        if pull_request is None:
            title = _title(finding.get('title'))
            body = _body(record, remediation, finding)
            try:
                pull_request = await client.create_pull_request(name, title, body, record['branch'], base)
            except GitHubAPIError as exc:
                if exc.status_code != 422:
                    raise
                pull_request = await client.find_pull_request(name, owner, record['branch'], base)
                if pull_request is None:
                    raise
        await self.storage.complete_pull_request(record, commit_sha, pull_request)
        return 'open'


async def _branch_head_or_none(client, repository, branch):
    try:
        return await client.get_branch_head(repository, branch)
    except GitHubAPIError as exc:
        if exc.status_code == 404:
            return None
        raise


def _changed_files(original: Path, patched: Path):
    original_files = {path.relative_to(original).as_posix(): path for path in original.rglob('*') if path.is_file()}
    patched_files = {path.relative_to(patched).as_posix(): path for path in patched.rglob('*') if path.is_file()}
    if set(original_files) != set(patched_files):
        raise PatchIntegrityError('Verified patch unexpectedly added or removed files')
    return sorted(path for path in original_files
                  if original_files[path].read_bytes() != patched_files[path].read_bytes())


def _title(value):
    clean = ' '.join(str(value or 'verified security finding').split())[:160]
    return f"[HavoSec] Fix {clean}"[:200]


def _body(record, remediation, finding):
    files = '\n'.join(f"- `{path}`" for path in remediation['verified_affected_files'])
    return (f"## HavoSec verified remediation\n\n"
            f"**Finding:** {str(finding.get('title') or 'Security finding')[:300]}\n\n"
            f"**Severity:** {finding.get('severity', 'unknown')}\n\n"
            f"**Source commit:** `{record['expected_source_commit']}`\n\n"
            f"**Verified patch SHA-256:** `{record['verified_patch_sha256']}`\n\n"
            f"**Affected files:**\n{files}\n\n"
            "This patch was verified in an isolated HavoSec workspace. "
            "Human review and repository CI are still required. HavoSec will not merge this pull request.\n")
