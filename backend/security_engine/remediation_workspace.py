"""Isolated original/patched trees and deterministic SafePatch application."""
import shutil
import tempfile
from contextlib import AbstractContextManager
from dataclasses import dataclass
from pathlib import Path

from security_engine.executor import execute, controlled_environment, DependencyUnavailable, ExecutionError
from security_engine.remediation import validate_patch
from security_engine.workspace import remove_tree


@dataclass(frozen=True)
class RemediationPaths:
    root: Path
    original: Path
    patched: Path
    artifacts: Path


def tree_size(root):
    total = 0
    for path in Path(root).rglob('*'):
        if path.is_file() and not path.is_symlink():
            total += path.stat().st_size
    return total


class RemediationWorkspace(AbstractContextManager):
    def __init__(self, remediation_id, *, parent=None, keep=False, max_bytes=100_000_000):
        self.remediation_id, self.parent, self.keep = str(remediation_id), parent, keep
        self.max_bytes, self.paths = max_bytes, None

    def __enter__(self):
        parent = Path(self.parent).resolve() if self.parent else None
        if parent:
            parent.mkdir(parents=True, exist_ok=True)
        root = Path(tempfile.mkdtemp(prefix='havosec-remediation-', dir=parent)).resolve()
        original, patched, artifacts = root / 'original', root / 'patched', root / 'artifacts'
        artifacts.mkdir()
        self.paths = RemediationPaths(root, original, patched, artifacts)
        return self

    def create_patched_copy(self):
        if not self.paths.original.is_dir() or self.paths.patched.exists():
            raise ValueError('Remediation source workspace is unavailable')
        size = tree_size(self.paths.original)
        if size * 2 > self.max_bytes:
            raise ValueError('Repository exceeds the remediation workspace limit')
        shutil.copytree(self.paths.original, self.paths.patched, symlinks=True)
        if size + tree_size(self.paths.patched) > self.max_bytes:
            remove_tree(self.paths.patched)
            raise ValueError('Repository exceeds the remediation workspace limit')
        return self.paths.patched

    def __exit__(self, *_):
        if self.paths and not self.keep:
            remove_tree(self.paths.root)
        return False


class PatchApplicator:
    def __init__(self, max_output_bytes=1_000_000):
        self.max_output_bytes = max_output_bytes

    async def apply(self, proposal, workspace, *, max_bytes, max_files, timeout):
        safe = validate_patch(proposal, workspace.paths.patched,
                              max_bytes=max_bytes, max_files=max_files)
        git = shutil.which('git')
        if not git:
            raise DependencyUnavailable('Git is not installed or unavailable on PATH')
        patch_file = workspace.paths.artifacts / 'proposal.diff'
        patch_file.write_text(safe.text, encoding='utf-8', newline='\n')
        base = [git, '-C', str(workspace.paths.patched), 'apply', '--whitespace=nowarn']
        check = await execute(base + ['--check', '--', str(patch_file)], cwd=workspace.paths.root,
                              timeout=timeout, max_output_bytes=self.max_output_bytes,
                              environment=controlled_environment(),
                              artifact_prefix=str(workspace.paths.artifacts / 'patch-check'))
        if check.exit_code:
            raise ExecutionError('Proposed patch could not be applied safely')
        applied = await execute(base + ['--', str(patch_file)], cwd=workspace.paths.root,
                                timeout=timeout, max_output_bytes=self.max_output_bytes,
                                environment=controlled_environment(),
                                artifact_prefix=str(workspace.paths.artifacts / 'patch-apply'))
        if applied.exit_code:
            raise ExecutionError('Proposed patch application failed')
        return safe
