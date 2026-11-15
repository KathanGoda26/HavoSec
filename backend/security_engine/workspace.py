from contextlib import AbstractContextManager
from dataclasses import dataclass
from pathlib import Path
import os
import shutil
import stat
import tempfile


def remove_tree(root):
    """Remove one already-resolved workspace tree, including read-only Git files."""
    def remove_readonly(function, path, error):
        if not isinstance(error, PermissionError):
            raise error
        os.chmod(path, stat.S_IWRITE)
        function(path)
    shutil.rmtree(root, ignore_errors=False, onexc=remove_readonly)


@dataclass(frozen=True)
class WorkspacePaths:
    root: Path
    repository: Path
    artifacts: Path


class RunWorkspace(AbstractContextManager):
    """Unique workspace with unconditional cleanup unless operator explicitly preserves it."""
    def __init__(self, run_id, *, parent=None, keep=False):
        self.run_id, self.parent, self.keep = str(run_id), parent, keep
        self.paths = None

    def __enter__(self):
        parent = Path(self.parent).resolve() if self.parent else None
        if parent:
            parent.mkdir(parents=True, exist_ok=True)
        root = Path(tempfile.mkdtemp(prefix='havosec-run-', dir=parent)).resolve()
        repository, artifacts = root / 'repo', root / 'artifacts'
        artifacts.mkdir()
        self.paths = WorkspacePaths(root, repository, artifacts)
        return self.paths

    def __exit__(self, *_):
        if self.paths and not self.keep:
            remove_tree(self.paths.root)
        return False
