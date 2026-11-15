from dataclasses import dataclass
from pathlib import Path
import shutil
import re
from security_engine.executor import execute, controlled_environment, DependencyUnavailable, ExecutionError


@dataclass(frozen=True)
class CheckoutResult:
    commit_sha: str
    branch: str | None


class GitRepository:
    def __init__(self, timeout, max_output_bytes):
        self.timeout, self.max_output_bytes = timeout, max_output_bytes

    async def checkout(self, snapshot, workspace):
        git = shutil.which('git')
        if not git:
            raise DependencyUnavailable('Git is not installed or unavailable on PATH')
        args = [git, '-c', 'credential.helper=', '-c', 'core.askPass=', 'clone', '--depth', '1', '--no-tags']
        if snapshot.branch:
            args.extend(['--branch', snapshot.branch, '--single-branch'])
        args.extend(['--', snapshot.repository, str(workspace.repository)])
        result = await execute(args, cwd=workspace.root, timeout=self.timeout,
                               max_output_bytes=self.max_output_bytes, environment=controlled_environment(),
                               artifact_prefix=str(workspace.artifacts / 'git-clone'))
        if result.exit_code:
            raise ExecutionError('Repository checkout failed')
        revision = await execute([git, '-C', str(workspace.repository), 'rev-parse', '--verify', 'HEAD'],
                                 cwd=workspace.root, timeout=min(30, self.timeout), max_output_bytes=4096,
                                 environment=controlled_environment(),
                                 artifact_prefix=str(workspace.artifacts / 'git-revision'))
        sha = revision.stdout.decode('ascii', errors='strict').strip().lower()
        if revision.exit_code or len(sha) != 40 or any(ch not in '0123456789abcdef' for ch in sha):
            raise ExecutionError('Checked out repository revision could not be verified')
        return CheckoutResult(sha, snapshot.branch)

    async def checkout_revision(self, snapshot, destination, artifacts, commit_sha):
        if not isinstance(commit_sha, str) or not re.fullmatch(r'[0-9a-f]{40}', commit_sha):
            raise ExecutionError('Source revision is invalid')
        git = shutil.which('git')
        if not git:
            raise DependencyUnavailable('Git is not installed or unavailable on PATH')
        destination, artifacts = Path(destination), Path(artifacts)
        commands = [
            [git, 'init', '--quiet', '--', str(destination)],
            [git, '-C', str(destination), 'remote', 'add', 'origin', snapshot.repository],
            [git, '-c', 'credential.helper=', '-c', 'core.askPass=', '-C', str(destination),
             'fetch', '--quiet', '--depth', '1', '--no-tags', 'origin', commit_sha],
            [git, '-C', str(destination), 'checkout', '--quiet', '--detach', 'FETCH_HEAD'],
        ]
        for index, args in enumerate(commands):
            result = await execute(args, cwd=destination.parent, timeout=self.timeout,
                                   max_output_bytes=self.max_output_bytes,
                                   environment=controlled_environment(),
                                   artifact_prefix=str(artifacts / f'git-remediation-{index}'))
            if result.exit_code:
                raise ExecutionError('Exact source revision checkout failed')
        revision = await execute([git, '-C', str(destination), 'rev-parse', '--verify', 'HEAD'],
                                 cwd=destination.parent, timeout=min(30, self.timeout), max_output_bytes=4096,
                                 environment=controlled_environment(),
                                 artifact_prefix=str(artifacts / 'git-remediation-revision'))
        actual = revision.stdout.decode('ascii', errors='strict').strip().lower()
        if revision.exit_code or actual != commit_sha:
            raise ExecutionError('Checked out source revision does not match the Finding')
        return CheckoutResult(actual, None)
