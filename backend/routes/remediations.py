from fastapi import APIRouter, Depends, Query
from core.database import get_database
from core.domain_api import domain_operation, domain_scope
from models.remediations import (RemediationCreate, RemediationUpdate, RemediationResponse,
                                 RemediationPage, RemediationStatus, PullRequestEligibility)
from repositories.project_resources import ProjectResourceRepository
from repositories.github_integrations import GitHubIntegrationRepository
from repositories.pull_requests import PullRequestRepository
from services.pull_requests import PullRequestService
from models.pull_requests import PullRequestResponse
from integrations.github.config import GitHubAppSettings, GitHubConfigurationError
from routes.projects import project_service, manage_projects
from routes.findings import finding_service
from services.remediations import RemediationService
from security_engine.config import EngineSettings

router = APIRouter()


def remediation_service(db=Depends(get_database), projects=Depends(project_service), findings=Depends(finding_service)):
    attempts = EngineSettings.from_environment().max_remediation_attempts
    github = (GitHubIntegrationRepository(db)
              if all(getattr(db, name, None) is not None for name in
                     ('github_integrations', 'github_repositories', 'github_connection_states'))
              else None)
    return RemediationService(ProjectResourceRepository(db, db.remediations), projects, findings,
                              attempts, github)


def pull_request_service(db=Depends(get_database), remediations=Depends(remediation_service)):
    try:
        settings = GitHubAppSettings.from_environment()
    except GitHubConfigurationError as exc:
        raise RuntimeError('GitHub integration is not configured') from exc
    github = GitHubIntegrationRepository(db)
    return PullRequestService(PullRequestRepository(db), remediations, github, settings)


@router.get('', response_model=RemediationPage)
async def list_remediations(limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0, le=100000),
                            project_id: str | None = None, finding_id: str | None = None,
                            status: RemediationStatus | None = None, scope=Depends(domain_scope), service=Depends(remediation_service)):
    return await domain_operation(service.list_filtered(scope, limit, offset, project_id, finding_id, status))


@router.post('', response_model=RemediationResponse, status_code=201)
async def create_remediation(payload: RemediationCreate, user=Depends(manage_projects),
                             scope=Depends(domain_scope), service=Depends(remediation_service)):
    return await domain_operation(service.create(scope, user['id'], payload))


@router.get('/{remediation_id}', response_model=RemediationResponse)
async def get_remediation(remediation_id: str, scope=Depends(domain_scope), service=Depends(remediation_service)):
    return await domain_operation(service.get(scope, remediation_id))


@router.patch('/{remediation_id}', response_model=RemediationResponse)
async def update_remediation(remediation_id: str, payload: RemediationUpdate, user=Depends(manage_projects),
                             scope=Depends(domain_scope), service=Depends(remediation_service)):
    return await domain_operation(service.update(scope, remediation_id, user['id'], payload))


@router.post('/{remediation_id}/verify', response_model=RemediationResponse, status_code=202)
async def verify_remediation(remediation_id: str, user=Depends(manage_projects),
                             scope=Depends(domain_scope), service=Depends(remediation_service)):
    return await domain_operation(service.queue_verification(scope, remediation_id, user['id']))


@router.get('/{remediation_id}/pull-request-eligibility', response_model=PullRequestEligibility)
async def pull_request_eligibility(remediation_id: str, scope=Depends(domain_scope),
                                   service=Depends(remediation_service)):
    return await domain_operation(service.pull_request_eligibility(scope, remediation_id))


@router.post('/{remediation_id}/pull-request', response_model=PullRequestResponse, status_code=202)
async def create_pull_request(remediation_id: str, user=Depends(manage_projects),
                              scope=Depends(domain_scope), service=Depends(pull_request_service)):
    return await domain_operation(service.request_creation(scope, remediation_id, user['id']))


@router.get('/{remediation_id}/pull-request', response_model=PullRequestResponse)
async def get_pull_request(remediation_id: str, scope=Depends(domain_scope),
                           service=Depends(pull_request_service)):
    return await domain_operation(service.get(scope, remediation_id))
