"""Separate V1 polling worker: `python -m security_engine.worker`."""
import asyncio
import logging
import uuid
from functools import partial
from dataclasses import replace
from core.database import load_backend_environment, DatabaseSettings, create_database_client
from security_engine.config import EngineSettings, repository_grants
from security_engine.repository import GitRepository
from security_engine.scanners.semgrep import SemgrepScanner
from security_engine.storage import WorkerRepository
from security_engine.pipeline import SecurityPipeline
from security_engine.workspace import RunWorkspace
from security_engine.remediation_workspace import RemediationWorkspace, PatchApplicator
from security_engine.remediation_pipeline import RemediationPipeline
from security_engine.agents.analysis import configured_agent
from security_engine.pull_request_pipeline import PullRequestPipeline
from security_engine.pr_reverification_pipeline import PullRequestReverificationPipeline
from integrations.github.config import GitHubAppSettings, GitHubConfigurationError
from integrations.github.client import GitHubAppClient


async def run_worker():
    load_backend_environment()
    settings, grants = EngineSettings.from_environment(), repository_grants()
    if not settings.enabled:
        raise SystemExit('Security worker is disabled. Set SECURITY_WORKER_ENABLED=true after configuring repository grants.')
    client = create_database_client(DatabaseSettings.from_environment())
    db = client[DatabaseSettings.from_environment().database_name]
    storage = WorkerRepository(db, 'worker-' + uuid.uuid4().hex, settings.run_timeout + 60)
    agent = configured_agent(settings)
    pipeline = SecurityPipeline(storage, GitRepository(settings.checkout_timeout, settings.max_output_bytes),
        SemgrepScanner(settings.semgrep_timeout, settings.max_output_bytes, settings.max_findings),
        partial(RunWorkspace, parent=settings.workspace_root, keep=settings.keep_workspaces), grants,
        agent)
    remediation_pipeline = RemediationPipeline(
        storage, GitRepository(settings.checkout_timeout, settings.max_output_bytes),
        SemgrepScanner(settings.semgrep_timeout, settings.max_output_bytes, settings.max_findings),
        PatchApplicator(settings.max_output_bytes),
        partial(RemediationWorkspace, parent=settings.workspace_root,
                keep=settings.keep_workspaces, max_bytes=settings.remediation_workspace_limit),
        grants, timeout=settings.remediation_timeout,
        patch_max_bytes=settings.patch_max_bytes, patch_max_files=settings.patch_max_files,
        agent=agent)
    try:
        github_settings = GitHubAppSettings.from_environment()
        pull_request_pipeline = PullRequestPipeline(
            storage,
            lambda installation_id, repository_id: GitHubAppClient(replace(
                github_settings, installation_id=installation_id), publication_repository_id=repository_id),
            PatchApplicator(settings.max_output_bytes),
            partial(RemediationWorkspace, parent=settings.workspace_root,
                    keep=settings.keep_workspaces, max_bytes=settings.remediation_workspace_limit),
            timeout=settings.remediation_timeout, patch_max_bytes=settings.patch_max_bytes,
            patch_max_files=settings.patch_max_files,
        )
        pull_request_reverification_pipeline = PullRequestReverificationPipeline(
            storage,
            lambda installation_id: GitHubAppClient(replace(
                github_settings, installation_id=installation_id)),
            SemgrepScanner(settings.semgrep_timeout, settings.max_output_bytes, settings.max_findings),
            partial(RunWorkspace, parent=settings.workspace_root, keep=settings.keep_workspaces),
            max_total_bytes=settings.remediation_workspace_limit,
        )
    except GitHubConfigurationError:
        pull_request_pipeline = None
        pull_request_reverification_pipeline = None
        logging.getLogger('havosec.worker').warning(
            'github_pull_request_worker_disabled_due_to_missing_configuration')
    try:
        while True:
            await storage.fail_expired_claims()
            await storage.fail_expired_remediations()
            await storage.fail_expired_pull_requests()
            await storage.fail_expired_pull_request_reverifications()
            run = await storage.claim()
            if run:
                await pipeline.process(run)
            else:
                remediation = await storage.claim_remediation()
                if remediation:
                    await remediation_pipeline.process(remediation)
                else:
                    pull_request = await storage.claim_pull_request() if pull_request_pipeline else None
                    if pull_request:
                        await pull_request_pipeline.process(pull_request)
                    else:
                        reverification = (await storage.claim_pull_request_reverification()
                                          if pull_request_reverification_pipeline else None)
                        if reverification:
                            await pull_request_reverification_pipeline.process(reverification)
                        else:
                            await asyncio.sleep(settings.poll_interval)
    finally:
        client.close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s %(message)s')
    asyncio.run(run_worker())
