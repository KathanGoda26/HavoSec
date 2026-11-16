"""Resolve an assessment only through the organization’s authorized GitHub connection."""
from dataclasses import replace
import re

from bson import ObjectId

from integrations.github.client import GitHubAPIError, GitHubAppClient
from integrations.github.config import GitHubAppSettings
from security_engine.policy import repository_branch, repository_url


async def authorized_github_scope(db, organization_id, asset, session=None):
    link = asset.get('source_control')
    if not isinstance(link, dict) or link.get('provider') != 'github' or link.get('connection_status') != 'active':
        return None
    integration_id = link.get('integration_id')
    repository_id = link.get('repository_id')
    if not ObjectId.is_valid(integration_id) or type(repository_id) is not int or repository_id <= 0:
        return None
    scope = {'organization_id': organization_id}
    integration = await db.github_integrations.find_one({
        **scope, '_id': ObjectId(integration_id), 'status': 'active',
    }, session=session)
    repository = await db.github_repositories.find_one({
        **scope, 'integration_id': integration_id, 'repository_id': repository_id,
        'authorized': True, 'connection_status': 'active',
    }, session=session)
    if not integration or not repository:
        return None
    permissions = integration.get('permissions')
    installation = integration.get('installation_id')
    name = repository.get('full_name')
    if (type(installation) is not int or installation <= 0 or not isinstance(permissions, dict)
            or permissions.get('contents') not in ('read', 'write') or not isinstance(name, str)
            or name != link.get('repository_full_name') or repository.get('default_branch') != link.get('default_branch')):
        return None
    try:
        if repository_url(f'https://github.com/{name}') != f'https://github.com/{name}':
            return None
        branch = repository_branch(repository.get('default_branch'))
    except ValueError:
        return None
    if branch is None:
        return None
    return {'repository': name, 'repository_id': repository_id, 'branch': branch,
            'installation_id': installation, 'integration_id': integration_id}


def github_read_client(scope):
    return GitHubAppClient(replace(GitHubAppSettings.from_environment(),
                                   installation_id=scope['installation_id']))


async def resolve_github_commit(scope):
    sha = await github_read_client(scope).get_branch_head(
        scope['repository'], scope['branch'], read_repository_id=scope['repository_id'],
    )
    if not isinstance(sha, str) or not re.fullmatch('[0-9a-f]{40}', sha):
        raise GitHubAPIError('GitHub returned an invalid assessment commit')
    return sha
