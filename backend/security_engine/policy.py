"""Fail-closed V1 public GitHub repository grants, configured by the operator.

Membership in a HavoSec project alone is not proof of repository authorization.
The operator must grant an exact repository URL to an exact organization ID.
"""
import re
from urllib.parse import urlsplit
from pydantic import BaseModel, ConfigDict


class RepositoryPolicyError(ValueError):
    """Safe fixed-text policy error; never include a supplied URL or secret."""


def repository_url(value: str) -> str:
    if not isinstance(value, str) or len(value) > 2048 or value != value.strip():
        raise RepositoryPolicyError('Invalid repository reference')
    try:
        parsed = urlsplit(value)
        if (parsed.scheme != 'https' or parsed.netloc != 'github.com' or parsed.query or parsed.fragment
                or '?' in value or '#' in value):
            raise ValueError()
        path = parsed.path.removesuffix('/').removesuffix('.git')
        if not re.fullmatch(r'/[A-Za-z0-9][A-Za-z0-9-]{0,38}/[A-Za-z0-9_.-]{1,100}', path):
            raise ValueError()
        if path.rsplit('/', 1)[1] in {'.', '..'}:
            raise ValueError()
        return 'https://github.com' + path
    except ValueError as exc:
        raise RepositoryPolicyError('Only credential-free public GitHub HTTPS repository URLs are supported') from exc


def repository_branch(value):
    if value is None:
        return None
    if (not isinstance(value, str) or len(value) > 200 or
            not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_./-]*', value) or
            any(part in {'', '.', '..'} or part.startswith('.') or part.endswith(('.', '.lock')) for part in value.split('/')) or
            '..' in value):
        raise RepositoryPolicyError('Invalid repository branch')
    return value


class RepositorySnapshot(BaseModel):
    model_config = ConfigDict(frozen=True, extra='forbid')
    organization_id: str
    project_id: str
    asset_id: str
    provider: str = 'github'
    repository: str
    branch: str | None = None


def authorize_repository(scope, project, asset, grants):
    """Used after authenticated scope resolution; recheck again before checkout.

No metadata may grant access or select a local path, executable or scanner flags.
Only selected_branch/default_branch is read from metadata in V1.
"""
    organization_id = scope.organization_id
    if (project.get('organization_id') != organization_id or asset.get('organization_id') != organization_id
            or asset.get('project_id') != str(project['_id'])):
        raise RepositoryPolicyError('Repository ownership does not match the run')
    if project.get('status') != 'active' or asset.get('status') != 'active':
        raise RepositoryPolicyError('Project and repository asset must be active')
    if asset.get('type') != 'repository':
        raise RepositoryPolicyError('V1 execution supports repository assets only')
    target = repository_url(asset.get('target'))
    if target not in grants.get(organization_id, ()):
        raise RepositoryPolicyError('Repository is not authorized for this organization')
    metadata = asset.get('metadata') or {}
    if not isinstance(metadata, dict):
        raise RepositoryPolicyError('Invalid repository metadata')
    branch = metadata.get('selected_branch', metadata.get('default_branch'))
    return RepositorySnapshot(organization_id=organization_id, project_id=str(project['_id']),
                              asset_id=str(asset['_id']), repository=target, branch=repository_branch(branch))
