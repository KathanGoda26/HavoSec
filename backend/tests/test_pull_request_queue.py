import asyncio
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from bson import ObjectId
from fastapi import HTTPException

from core.ownership import OrganizationScope
from integrations.github.config import GitHubAppSettings
from services.pull_requests import PullRequestService


ORG = 'aaaaaaaaaaaaaaaaaaaaaaaa'
RID = 'bbbbbbbbbbbbbbbbbbbbbbbb'


def fixture():
    repository = AsyncMock()
    repository.get_for_remediation.return_value = None
    repository.db.assets.find_one.return_value = {'source_control': {
        'provider': 'github', 'repository_id': 1357212288,
        'repository_full_name': 'KathanGoda26/havosec-github-integration-test',
        'default_branch': 'main', 'integration_id': 'd' * 24,
    }}
    repository.create_idempotent.side_effect = lambda scope, document, event: document
    remediations = AsyncMock()
    remediations.pull_request_eligibility.return_value = {
        'eligible': True, 'reasons': [], 'requires_remote_source_check': True,
    }
    remediations.get_document.return_value = {
        '_id': ObjectId(RID), 'project_id': 'c' * 24, 'asset_id': 'e' * 24,
        'finding_id': 'f' * 24, 'verified_source_commit': '1' * 40,
        'verified_patch_sha256': '2' * 64,
    }
    github = AsyncMock()
    github.get.return_value = {'installation_id': 159047858}
    service = PullRequestService(
        repository, remediations, github,
        GitHubAppSettings(4830110, Path('unused.pem')),
    )
    return service, repository


def test_creation_is_deterministic_and_queued_after_live_source_check():
    service, repository = fixture()
    client = AsyncMock()
    client.get_branch_head.return_value = '1' * 40
    with patch('services.pull_requests.GitHubAppClient', return_value=client):
        result = asyncio.run(service.request_creation(OrganizationScope(ORG), RID, 'actor-a'))
    assert result['branch'] == 'havosec/remediation-' + RID[:12]
    assert result['status'] == 'queued'
    assert result['expected_source_commit'] == '1' * 40
    assert repository.create_idempotent.await_count == 1


def test_source_change_marks_remediation_stale_and_does_not_queue():
    service, repository = fixture()
    client = AsyncMock()
    client.get_branch_head.return_value = '9' * 40
    with patch('services.pull_requests.GitHubAppClient', return_value=client):
        with pytest.raises(HTTPException) as error:
            asyncio.run(service.request_creation(OrganizationScope(ORG), RID, 'actor-a'))
    assert error.value.status_code == 409
    repository.mark_remediation_stale.assert_awaited_once()
    repository.create_idempotent.assert_not_awaited()


def test_repeat_request_returns_existing_record_without_github_call():
    service, repository = fixture()
    repository.get_for_remediation.return_value = {
        '_id': ObjectId(), 'organization_id': ORG, 'remediation_id': RID,
    }
    with patch('services.pull_requests.GitHubAppClient') as client:
        result = asyncio.run(service.request_creation(OrganizationScope(ORG), RID, 'actor-a'))
    assert result['remediation_id'] == RID
    client.assert_not_called()
