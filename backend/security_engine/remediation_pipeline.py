"""Controlled remediation verification in the existing single-worker architecture."""
import asyncio
import logging
from collections import deque
from pathlib import Path, PurePosixPath
from types import SimpleNamespace

from security_engine.executor import ExecutionError
from security_engine.policy import RepositoryPolicyError
from security_engine.remediation import PatchSafetyError
from security_engine.remediation import safe_relative_path
from security_engine.storage import RunChanged
from security_engine.verification import compare_semgrep


log = logging.getLogger('havosec.remediation_worker')


class RemediationPipeline:
    def __init__(self, repository, checkout, scanner, patcher, workspace_factory, grants,
                 *, timeout, patch_max_bytes, patch_max_files, agent=None):
        self.repository, self.checkout, self.scanner, self.patcher = repository, checkout, scanner, patcher
        self.workspace_factory, self.grants, self.timeout = workspace_factory, grants, timeout
        self.patch_max_bytes, self.patch_max_files = patch_max_bytes, patch_max_files
        self.agent = agent

    async def process(self, remediation):
        try:
            async with asyncio.timeout(self.timeout):
                return await self._process(remediation)
        except RunChanged:
            return 'cancelled_or_changed'
        except TimeoutError:
            await self.repository.fail_remediation(remediation, 'inconclusive',
                                                   'Remediation verification timed out')
            return 'inconclusive'
        except (PatchSafetyError, ValueError) as exc:
            await self.repository.fail_remediation(remediation, 'failed', _safe_failure(exc))
            return 'failed'
        except (ExecutionError, RepositoryPolicyError) as exc:
            await self.repository.fail_remediation(remediation, 'inconclusive', _safe_failure(exc))
            return 'inconclusive'
        except Exception:
            log.exception('remediation_verification_internal_failure')
            await self.repository.fail_remediation(remediation, 'inconclusive',
                                                   'Remediation verification failed unexpectedly')
            return 'inconclusive'

    async def _process(self, remediation):
        snapshot, finding, proposal, before_scan = await self.repository.load_remediation_context(
            remediation, self.grants)
        await self.repository.heartbeat_remediation(remediation)
        with self.workspace_factory(str(remediation['_id'])) as workspace:
            checkout = await self.checkout.checkout_revision(
                snapshot, workspace.paths.original, workspace.paths.artifacts,
                remediation['source_commit'])
            if checkout.commit_sha != remediation['source_commit']:
                raise ExecutionError('Exact source revision verification failed')
            if proposal is None:
                if self.agent is None:
                    raise ValueError('Automated proposal generation is unavailable')
                excerpt = _source_excerpt(workspace.paths.original, finding,
                                          self.agent.max_context_chars)
                proposal, usage = await self.agent.propose_remediation(finding, excerpt)
                if proposal is None:
                    raise ValueError('Automated proposal generation is unavailable')
                proposal = await self.repository.save_remediation_proposal(
                    remediation, proposal, {'analysis_mode': 'agent_generated',
                                             'usage': usage})
            workspace.create_patched_copy()
            await self.repository.heartbeat_remediation(remediation)
            await self.patcher.apply(proposal, workspace, max_bytes=self.patch_max_bytes,
                                     max_files=self.patch_max_files, timeout=self.timeout)
            await self.repository.heartbeat_remediation(remediation)
            scan_artifacts = workspace.paths.artifacts / 'after-scan'
            scan_artifacts.mkdir()
            after_scan = await self.scanner.scan(SimpleNamespace(
                repository=workspace.paths.patched, artifacts=scan_artifacts))
            result = compare_semgrep(str(remediation['_id']), finding, before_scan, after_scan)
            await self.repository.complete_remediation(remediation, result, after_scan)
        return result.status


def _safe_failure(exc):
    if isinstance(exc, PatchSafetyError):
        return 'The proposed patch failed safety validation'
    if isinstance(exc, RepositoryPolicyError):
        return 'The repository is no longer authorized for remediation'
    if isinstance(exc, ExecutionError):
        return 'Static remediation verification could not be completed'
    if str(exc) == 'Automated proposal generation is unavailable':
        return 'Automated remediation proposal generation is unavailable'
    return 'Remediation source evidence is invalid or unavailable'


def _source_excerpt(repository, finding, limit):
    evidence = finding.get('evidence') if isinstance(finding.get('evidence'), dict) else {}
    relative = safe_relative_path(str(evidence.get('path') or '').replace('\\', '/'))
    root = Path(repository).resolve(strict=True)
    target = root.joinpath(*PurePosixPath(relative).parts)
    current = root
    for part in PurePosixPath(relative).parts:
        current = current / part
        if current.is_symlink():
            raise PatchSafetyError('Source context cannot traverse symbolic links')
    resolved = target.resolve(strict=True)
    if root not in resolved.parents or not resolved.is_file():
        raise PatchSafetyError('Source context is outside the repository')
    target_line = max(1, int(evidence.get('start_line') or 1))
    before, selected = deque(maxlen=20), []
    with resolved.open('r', encoding='utf-8', errors='replace') as source:
        for number, line in enumerate(source, 1):
            if number < target_line:
                before.append(line)
                continue
            if not selected:
                selected.extend(before)
            selected.append(line)
            if number >= target_line + 20 or sum(map(len, selected)) >= limit:
                break
    return ''.join(selected)[:limit]
