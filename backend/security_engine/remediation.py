"""Validation for untrusted agent-proposed unified diffs; does not apply patches."""
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from models.remediations import RemediationProposal


class PatchSafetyError(ValueError):
    pass


@dataclass(frozen=True)
class SafePatch:
    text: str
    files: tuple[str, ...]
    size_bytes: int


def safe_relative_path(value):
    if not isinstance(value, str) or not value or '\\' in value or '\x00' in value:
        raise PatchSafetyError('Patch path is invalid')
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {'', '.', '..'} or ':' in part for part in path.parts):
        raise PatchSafetyError('Patch path must be repository-relative')
    return path.as_posix()


def _header_path(line, prefix):
    value = line[len(prefix):].split('\t', 1)[0].strip()
    required = 'a/' if prefix == '--- ' else 'b/'
    if value == '/dev/null' or not value.startswith(required):
        raise PatchSafetyError('V1 patches may only modify existing repository files')
    return safe_relative_path(value[2:])


def validate_patch(proposal: RemediationProposal, repository, *, max_bytes, max_files):
    encoded = proposal.patch.encode('utf-8')
    if len(encoded) > max_bytes:
        raise PatchSafetyError('Patch exceeds the configured size limit')
    if '\r' in proposal.patch or 'GIT binary patch' in proposal.patch or 'Binary files ' in proposal.patch:
        raise PatchSafetyError('Binary or non-canonical patches are not supported')
    lines, files, index = proposal.patch.splitlines(), [], 0
    while index < len(lines):
        if lines[index].startswith(('diff --git ', 'index ')):
            index += 1
            continue
        if not lines[index].startswith('--- '):
            raise PatchSafetyError('Patch contains malformed content')
        if index + 1 >= len(lines) or not lines[index + 1].startswith('+++ '):
            raise PatchSafetyError('Patch file headers are incomplete')
        old, new = _header_path(lines[index], '--- '), _header_path(lines[index + 1], '+++ ')
        if old != new:
            raise PatchSafetyError('V1 patches cannot rename files')
        files.append(old)
        index += 2
        saw_hunk = False
        while index < len(lines) and not lines[index].startswith('--- '):
            if lines[index].startswith('@@ '):
                saw_hunk = True
            elif lines[index].startswith(('diff --git ', 'index ')):
                break
            elif saw_hunk and not lines[index].startswith((' ', '+', '-', '\\')):
                raise PatchSafetyError('Patch hunk contains malformed content')
            index += 1
        if not saw_hunk:
            raise PatchSafetyError('Patch must contain a unified-diff hunk')
    if not files or len(files) != len(set(files)):
        raise PatchSafetyError('Patch must modify unique files')
    if len(files) > max_files:
        raise PatchSafetyError('Patch exceeds the configured file limit')
    declared = tuple(safe_relative_path(path) for path in proposal.affected_files)
    if set(declared) != set(files):
        raise PatchSafetyError('Affected files do not match the patch')
    root = Path(repository).resolve(strict=True)
    for relative in files:
        candidate = root / Path(*PurePosixPath(relative).parts)
        current = root
        for part in PurePosixPath(relative).parts:
            current = current / part
            if current.is_symlink():
                raise PatchSafetyError('Patch cannot modify files through symbolic links')
        resolved = candidate.resolve(strict=True)
        if root not in resolved.parents or not resolved.is_file():
            raise PatchSafetyError('Patch target is outside the repository or is not a file')
    return SafePatch(proposal.patch, tuple(files), len(encoded))
