"""Re-scan the exact remote GitHub PR commit before declaring review readiness."""

from pathlib import PurePosixPath
from types import SimpleNamespace

from integrations.github.client import GitHubAPIError
from security_engine.executor import ExecutionError
from security_engine.remediation import PatchSafetyError, safe_relative_path
from security_engine.storage import RunChanged
from security_engine.verification import compare_semgrep


class PullRequestReverificationPipeline:
    def __init__(self, storage, client_factory, scanner, workspace_factory, *,
                 max_files=5000, max_total_bytes=100_000_000, max_file_bytes=10_000_000):
        self.storage, self.client_factory, self.scanner = storage, client_factory, scanner
        self.workspace_factory = workspace_factory
        self.max_files, self.max_total_bytes, self.max_file_bytes = max_files, max_total_bytes, max_file_bytes

    async def process(self, record):
        try:
            return await self._process(record)
        except RunChanged:
            return 'cancelled_or_changed'
        except (ValueError, PatchSafetyError, GitHubAPIError, ExecutionError):
            await self.storage.fail_pull_request_reverification(
                record, 'Exact pull request commit could not be re-verified safely')
        except Exception:
            await self.storage.fail_pull_request_reverification(
                record, 'Pull request re-verification failed unexpectedly')
        return 'inconclusive'

    async def _process(self, record):
        remediation, finding, integration, _, before_scan = (
            await self.storage.load_pull_request_reverification_context(record))
        client = self.client_factory(integration['installation_id'])
        repository, commit_sha = record['repository_full_name'], record['commit_sha']
        if await client.get_branch_head(repository, record['branch']) != commit_sha:
            raise ValueError('Pull request branch no longer matches the recorded commit')
        commit = await client.get_commit(repository, commit_sha)
        tree_sha = (commit.get('tree') or {}).get('sha')
        if not isinstance(tree_sha, str) or len(tree_sha) != 40:
            raise GitHubAPIError('GitHub returned an invalid commit tree')
        tree = await client.get_tree(repository, tree_sha)
        blobs = [(path, entry) for path, entry in tree.items()
                 if entry.get('type') == 'blob' and entry.get('mode') in {'100644', '100755'}]
        if not blobs or len(blobs) > self.max_files:
            raise ValueError('Pull request repository exceeds the verification file limit')

        total = 0
        with self.workspace_factory(str(record['_id'])) as workspace:
            workspace.repository.mkdir()
            for raw_path, entry in blobs:
                relative = safe_relative_path(raw_path)
                if PurePosixPath(relative).parts[0].lower() == '.git':
                    raise ValueError('Git control paths cannot be materialized')
                content = await client.get_blob(
                    repository, entry.get('sha'), max_bytes=self.max_file_bytes)
                total += len(content)
                if total > self.max_total_bytes:
                    raise ValueError('Pull request repository exceeds the verification size limit')
                target = workspace.repository.joinpath(*PurePosixPath(relative).parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(content)
            after_scan = await self.scanner.scan(SimpleNamespace(
                repository=workspace.repository, artifacts=workspace.artifacts))
            result = compare_semgrep(record['remediation_id'], finding, before_scan, after_scan)
        await self.storage.complete_pull_request_reverification(record, result)
        return result.status
