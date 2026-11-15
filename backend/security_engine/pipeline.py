import logging
from collections import Counter
from datetime import datetime, timezone
from types import SimpleNamespace
from security_engine.normalization.semgrep import normalize_semgrep
from security_engine.executor import ExecutionError
from security_engine.policy import RepositoryPolicyError
from security_engine.storage import RunChanged

log = logging.getLogger('havosec.security_worker')
SAFE_FAILURES = (ExecutionError, RepositoryPolicyError, ValueError)


class SecurityPipeline:
    def __init__(self, repository, checkout, scanner, workspace_factory, grants, agent=None):
        self.repository, self.checkout, self.scanner = repository, checkout, scanner
        self.workspace_factory, self.grants, self.agent = workspace_factory, grants, agent

    async def process(self, run):
        fields = {'run_id': str(run['_id']), 'organization_id': run['organization_id'],
                  'project_id': run['project_id'], 'scanner': 'semgrep'}
        started = datetime.now(timezone.utc)
        try:
            _, _, _, snapshot = await self.repository.load_authorized_context(run, self.grants)
            await self.repository.heartbeat(run, 15); run['progress'] = 15
            with self.workspace_factory(str(run['_id'])) as workspace:
                checkout = await self.checkout.checkout(snapshot, workspace)
                if await self.repository.is_cancelled(run): return 'cancelled'
                await self.repository.heartbeat(run, 30); run['progress'] = 30
                scanner_result = await self.scanner.scan(workspace)
                if await self.repository.is_cancelled(run): return 'cancelled'
                await self.repository.heartbeat(run, 60); run['progress'] = 60
                context = SimpleNamespace(**snapshot.model_dump(), security_run_id=str(run['_id']),
                                          commit_sha=checkout.commit_sha)
                candidates = normalize_semgrep(scanner_result, context)
                await self.repository.heartbeat(run, 70); run['progress'] = 70
                if await self.repository.is_cancelled(run): return 'cancelled'
                agent_enriched, agent_usage = 0, {}
                if self.agent:
                    candidates, agent_enriched, agent_usage = await self.agent.enrich(candidates, scanner_result)
                await self.repository.heartbeat(run, 80); run['progress'] = 80
                if await self.repository.is_cancelled(run): return 'cancelled'
                counts = Counter(candidate.severity.value for candidate in candidates)
                duration = max(0, (datetime.now(timezone.utc) - started).total_seconds())
                summary = {'files_analyzed': None, 'scanner_findings': len(scanner_result.results),
                           'normalized_findings': len(candidates), **{key: counts.get(key, 0) for key in
                           ['critical', 'high', 'medium', 'low', 'info']},
                           'agent_enriched': agent_enriched,
                           'analysis_mode': 'agent_enriched' if agent_enriched else 'deterministic_only',
                           'agent_usage': agent_usage,
                           'duration_seconds': round(duration, 3), 'commit_sha': checkout.commit_sha}
                await self.repository.heartbeat(run, 95); run['progress'] = 95
                if await self.repository.is_cancelled(run): return 'cancelled'
                await self.repository.complete(run, scanner_result, candidates, summary)
            log.info('security_run_completed', extra=fields | {'finding_count': len(candidates), 'status': 'completed'})
            return 'completed'
        except RunChanged:
            log.info('security_run_changed', extra=fields | {'status': 'cancelled_or_changed'})
            return 'cancelled_or_changed'
        except SAFE_FAILURES as exc:
            reason = safe_reason(exc)
            await self.repository.fail(run, reason)
            log.warning('security_run_failed', extra=fields | {'status': 'failed', 'failure_type': type(exc).__name__})
            return 'failed'
        except Exception as exc:
            # Details/traceback stay in worker logs; frontend receives fixed text.
            log.exception('security_run_internal_failure', extra=fields | {'status': 'failed'})
            await self.repository.fail(run, 'Security analysis failed unexpectedly')
            return 'failed'


def safe_reason(exc):
    mapping = {'DependencyUnavailable': 'Required security tool is unavailable',
               'ExecutionTimeout': 'Security analysis timed out',
               'OutputLimitExceeded': 'Security tool output exceeded its limit',
               'RepositoryPolicyError': 'Repository is not authorized for analysis'}
    return mapping.get(type(exc).__name__, 'Security analysis could not be completed')
