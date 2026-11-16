import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from security_engine.executor import execute, controlled_environment, DependencyUnavailable, ExecutionError
from security_engine.scanners.base import ScannerResult


RULES = Path(__file__).resolve().parents[1] / 'rules' / 'semgrep-v1.yml'


class SemgrepScanner:
    def __init__(self, timeout, max_output_bytes, max_findings):
        self.timeout, self.max_output_bytes, self.max_findings = timeout, max_output_bytes, max_findings

    @staticmethod
    def arguments(config, *targets):
        return ['scan', '--json', '--metrics=off', '--disable-version-check', '--config', config,
                '--', *(targets or ('.',))]

    async def _run(self, workspace):
        binary = shutil.which('semgrep')
        if not binary:
            raise DependencyUnavailable('Semgrep is not installed or unavailable on PATH')
        return await execute([binary, *self.arguments(str(RULES))],
                             cwd=workspace.repository, timeout=self.timeout, max_output_bytes=self.max_output_bytes,
                             environment=controlled_environment(), artifact_prefix=str(workspace.artifacts / 'semgrep'))

    async def scan(self, workspace):
        started = datetime.now(timezone.utc)
        result = await self._run(workspace)
        try:
            payload = json.loads(result.stdout)
            findings, errors = payload['results'], payload.get('errors', [])
            if not isinstance(findings, list) or not isinstance(errors, list):
                raise ValueError()
            if len(findings) > self.max_findings:
                raise ExecutionError('Semgrep result count exceeded its configured limit')
            version = str(payload.get('version') or 'unknown')[:100]
            paths = payload.get('paths') or {}
            scanned = paths.get('scanned') if isinstance(paths, dict) else None
        except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            raise ExecutionError('Semgrep returned invalid JSON') from exc
        # We do not pass --error, so this adapter accepts only a successful zero exit.
        if result.exit_code != 0:
            raise ExecutionError('Semgrep scan failed')
        return ScannerResult(scanner='semgrep', scanner_version=version, configuration='havosec-semgrep-v1',
                             started_at=started, completed_at=datetime.now(timezone.utc), exit_code=result.exit_code,
                             results=findings, errors=errors, metadata={
                                 'result_count': len(findings),
                                 'scanned_paths': scanned if isinstance(scanned, list) else [],
                             })
