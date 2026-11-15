import json
import pytest
from bson import ObjectId
from core.ownership import OrganizationScope
from security_engine.config import EngineSettings, repository_grants
from security_engine.policy import authorize_repository, repository_url, repository_branch, RepositoryPolicyError

ORG = 'aaaaaaaaaaaaaaaaaaaaaaaa'
URL = 'https://github.com/juice-shop/juice-shop'


def fixture():
    project = {'_id': ObjectId(), 'organization_id': ORG, 'status': 'active'}
    asset = {'_id': ObjectId(), 'organization_id': ORG, 'project_id': str(project['_id']),
             'status': 'active', 'type': 'repository', 'target': URL, 'metadata': {}}
    return project, asset


def test_disabled_by_default_and_no_grants():
    config = EngineSettings.from_environment({})
    assert not config.enabled and not config.agent_enabled and not config.keep_workspaces
    project, asset = fixture()
    with pytest.raises(RepositoryPolicyError):
        authorize_repository(OrganizationScope(ORG), project, asset, repository_grants({}))


def test_explicit_organization_grant_and_snapshot():
    project, asset = fixture()
    grants = repository_grants({'SECURITY_REPOSITORY_GRANTS': json.dumps({ORG: [URL + '.git']})})
    asset['metadata'] = {'selected_branch': 'release/v1', 'command': 'ignored', 'authorized': True}
    result = authorize_repository(OrganizationScope(ORG), project, asset, grants)
    assert result.repository == URL and result.branch == 'release/v1'
    assert 'command' not in result.model_dump()


@pytest.mark.parametrize('url', ['http://github.com/a/b', 'file:///tmp/repo', 'git@github.com:a/b',
    'https://user:secret@github.com/a/b', 'https://localhost/a/b', 'https://127.0.0.1/a/b',
    'https://github.com.evil.test/a/b', 'https://github.com:443/a/b', 'https://github.com/a/b?x=1',
    'https://github.com/a/b#main', 'https://github.com/a/%2e%2e', 'https://github.com/a/../b',
    'https://github.com/a/b/tree/main', '--upload-pack=evil', ' https://github.com/a/b', None])
def test_unsafe_repository_urls_rejected(url):
    with pytest.raises(RepositoryPolicyError):
        repository_url(url)


@pytest.mark.parametrize('branch', ['--config=evil', '../main', 'a..b', 'a//b', 'a.lock', '.hidden',
                                    'a/.hidden', 'a@{b}', 'a;cmd', 'a\\b', 'a\ncmd', 'x' * 201])
def test_unsafe_branches(branch):
    with pytest.raises(RepositoryPolicyError):
        repository_branch(branch)


@pytest.mark.parametrize('field,value', [('organization_id', 'bbbbbbbbbbbbbbbbbbbbbbbb'),
    ('project_id', 'cccccccccccccccccccccccc'), ('status', 'archived'), ('type', 'host')])
def test_asset_relationships(field, value):
    project, asset = fixture()
    asset[field] = value
    with pytest.raises(RepositoryPolicyError):
        authorize_repository(OrganizationScope(ORG), project, asset, {ORG: {URL}})


def test_project_and_grant_boundaries():
    project, asset = fixture()
    with pytest.raises(RepositoryPolicyError):
        authorize_repository(OrganizationScope(ORG), project, asset, {'bbbbbbbbbbbbbbbbbbbbbbbb': {URL}})
    project['status'] = 'archived'
    with pytest.raises(RepositoryPolicyError):
        authorize_repository(OrganizationScope(ORG), project, asset, {ORG: {URL}})


@pytest.mark.parametrize('raw', ['[]', '{"*": []}', '{"bad": []}', '{',
    json.dumps({ORG: ['https://user:password@github.com/a/b']})])
def test_invalid_grants_do_not_echo_input(raw):
    with pytest.raises(ValueError, match='^Invalid SECURITY_REPOSITORY_GRANTS configuration$'):
        repository_grants({'SECURITY_REPOSITORY_GRANTS': raw})


@pytest.mark.parametrize('setting,value', [('SEMGREP_TIMEOUT', '0'), ('SECURITY_MAX_OUTPUT_BYTES', '99999999'),
    ('MAX_AGENT_FINDINGS_PER_RUN', '10000'), ('SECURITY_RUN_TIMEOUT', '60'), ('SECURITY_WORKER_ENABLED', 'maybe'),
    ('PATCH_MAX_BYTES', '10'), ('PATCH_MAX_FILES', '0'), ('MAX_REMEDIATION_ATTEMPTS', '3'),
    ('REMEDIATION_WORKSPACE_LIMIT', '100')])
def test_bounded_settings(setting, value):
    with pytest.raises(ValueError):
        EngineSettings.from_environment({setting: value})
