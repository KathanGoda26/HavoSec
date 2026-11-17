"""Fetch one pinned repository archive, then scan selected source files offline."""
import asyncio
import gzip
import logging
import re
import tarfile
from hashlib import sha256
from pathlib import PurePosixPath

from integrations.github.client import GitHubAPIError
from integrations.github.config import GitHubConfigurationError
from mission_orchestration.fixture_assessment import IsolatedSemgrepScanner, new_assessment_report, populate_scan_report
from mission_orchestration.github_scope import github_read_client
from security_engine.executor import ExecutionError
from security_engine.normalization.semgrep import safe_path
from security_engine.scanners.semgrep import RULES
from security_engine.workspace import RunWorkspace


MAX_ARCHIVE = 48 * 1024 * 1024
MAX_EXPANDED = 128 * 1024 * 1024
MAX_FILE = 512 * 1024
MAX_SOURCE = 16 * 1024 * 1024
MAX_FILES = 400
SOURCE_SUFFIXES = {'.py', '.js', '.jsx', '.ts', '.tsx'}
EXCLUDED_DIRS = {'node_modules', 'vendor', 'dist', 'build', '__pycache__'}
log = logging.getLogger(__name__)


class BoundedArchive:
    def __init__(self, stream):
        self.stream = stream
        self.remaining = MAX_EXPANDED

    def read(self, size):
        data = self.stream.read(min(size, self.remaining + 1))
        self.remaining -= len(data)
        if self.remaining < 0:
            raise ExecutionError('Repository archive exceeds the expanded size limit')
        return data


def materialize_source(compressed, destination):
    files, excluded = set(), 0
    gaps = set()
    total_size = 0
    root = None
    with gzip.open(compressed, 'rb') as stream, tarfile.open(fileobj=BoundedArchive(stream), mode='r|') as archive:
        for index, item in enumerate(archive):
            if index >= 12_000:
                raise ExecutionError('Repository archive has too many entries')
            top, separator, path = item.name.partition('/')
            if not re.fullmatch(r'[A-Za-z0-9_.-]+', top) or top in {'.', '..'} or root not in (None, top):
                raise ExecutionError('Repository archive has an invalid root')
            root = top
            if not separator or item.isdir():
                continue
            try:
                valid_path = '\\' not in path and safe_path(path) == path
            except ValueError:
                valid_path = False
            if not valid_path:
                gaps.add('unsafe_source_entry')
                continue
            parts = PurePosixPath(path).parts
            if (PurePosixPath(path).suffix.lower() not in SOURCE_SUFFIXES
                    or any(part.startswith('.') or part in EXCLUDED_DIRS for part in parts[:-1])):
                excluded += 1
                continue
            if not item.isfile() or len(path) > 240 or path in files:
                gaps.add('unsafe_source_entry')
                continue
            if (not 0 <= item.size <= MAX_FILE or total_size + item.size > MAX_SOURCE or len(files) >= MAX_FILES):
                gaps.add('source_limit_exceeded')
                continue
            source = archive.extractfile(item)
            if source is None:
                raise ExecutionError('Repository source could not be read')
            with source:
                content = source.read()
            if len(content) != item.size:
                raise ExecutionError('Repository source is truncated')
            output = destination / path
            output.parent.mkdir(parents=True, exist_ok=True)
            with output.open('xb') as file:
                file.write(content)
            files.add(path)
            total_size += len(content)
    return sorted(files), excluded, sorted(gaps)


async def assess_github_repository(mission, client_factory=None):
    scope, commit = mission['github_scope'], mission.get('source_commit')
    report = new_assessment_report(commit)
    report.update(repository=scope['repository'], branch=scope['branch'])
    if not isinstance(commit, str) or not re.fullmatch('[0-9a-f]{40}', commit):
        report['gaps'].append('invalid_source_commit')
        return report
    stage = 'archive download'
    try:
        with RunWorkspace(mission['_id']) as workspace:
            client = (client_factory or github_read_client)(scope)
            archive = workspace.artifacts / 'source.tar.gz'
            await asyncio.wait_for(client.download_readonly_archive(
                scope['repository'], scope['repository_id'], commit, archive, MAX_ARCHIVE,
            ), timeout=60)
            stage = 'source extraction'
            workspace.repository.mkdir()
            names, excluded, gaps = materialize_source(archive, workspace.repository)
            report['coverage'].update(expected=names, missing=names, excluded=excluded)
            report['gaps'].extend(gaps)
            if not names:
                report['gaps'].append('no_supported_source_files')
                return report
            rules = RULES.read_bytes()
            (workspace.artifacts / 'rules.yml').write_bytes(rules)
            report['rules_sha256'] = sha256(rules).hexdigest()
            scanner = IsolatedSemgrepScanner(timeout=55, max_output_bytes=2_000_000, max_findings=150, targets=names)
            stage = 'isolated scan'
            await populate_scan_report(report, mission, workspace, scanner,
                                       repository=scope['repository'], branch=scope['branch'])
    except (GitHubAPIError, GitHubConfigurationError, TimeoutError) as error:
        log.warning('GitHub assessment failed during %s (%s)', stage, type(error).__name__)
        report['gaps'].append('github_source_unavailable')
    except (ExecutionError, OSError, ValueError, KeyError, EOFError, tarfile.TarError) as error:
        log.warning('GitHub assessment failed during %s (%s)', stage, type(error).__name__)
        report['gaps'].append('repository_scan_failed')
    return report
