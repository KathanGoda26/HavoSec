from hashlib import sha256
from pathlib import PurePosixPath
from pydantic import BaseModel, ConfigDict, Field, JsonValue
from models.findings import Severity


SEVERITY = {'ERROR': Severity.HIGH, 'WARNING': Severity.MEDIUM, 'INFO': Severity.LOW,
            'INVENTORY': Severity.INFO, 'EXPERIMENT': Severity.INFO}


class CandidateFinding(BaseModel):
    model_config = ConfigDict(frozen=True, extra='forbid')
    fingerprint: str
    title: str
    description: str
    category: str
    severity: Severity
    confidence: float = Field(ge=0, le=1)
    file_path: str
    start_line: int = Field(ge=1)
    end_line: int = Field(ge=1)
    rule_id: str
    evidence: dict
    scanner: str = 'semgrep'
    scanner_version: str
    repository: str
    branch: str | None
    commit_sha: str
    organization_id: str
    project_id: str
    asset_id: str
    security_run_id: str
    analysis: dict[str, JsonValue] | None = None


def safe_path(value):
    if not isinstance(value, str):
        raise ValueError('Invalid Semgrep path')
    normalized = value.replace('\\', '/')
    path = PurePosixPath(normalized)
    if (path.is_absolute() or not path.parts or
            any(part in {'', '.', '..'} or ':' in part or '\x00' in part for part in path.parts)):
        raise ValueError('Semgrep path is not repository-relative')
    parts = list(path.parts)
    if not parts:
        raise ValueError('Invalid Semgrep path')
    return PurePosixPath(*parts).as_posix()


def fingerprint(context, rule_id, path, start_line, snippet_hash):
    values = [context.organization_id, context.project_id, context.asset_id, 'semgrep',
              rule_id, path, str(start_line), snippet_hash]
    return sha256('\0'.join(values).encode('utf-8')).hexdigest()


def normalize_semgrep(scanner_result, context):
    candidates = []
    for item in scanner_result.results:
        try:
            rule_id, path = str(item['check_id'])[:300], safe_path(item['path'])
            start, end = int(item['start']['line']), int(item['end']['line'])
            if start < 1 or end < start:
                raise ValueError()
            extra = item.get('extra') or {}
            message = str(extra.get('message') or rule_id)[:4000]
            semgrep_severity = str(extra.get('severity') or 'INFO').upper()
            severity = SEVERITY.get(semgrep_severity, Severity.INFO)
            lines = str(extra.get('lines') or '')[:8000]
            snippet_hash = sha256(lines.encode('utf-8')).hexdigest()
            candidates.append(CandidateFinding(
                fingerprint=fingerprint(context, rule_id, path, start, snippet_hash), title=message[:300],
                description=message, category=rule_id, severity=severity, confidence=0.7,
                file_path=path, start_line=start, end_line=end, rule_id=rule_id,
                evidence={'rule_id': rule_id, 'path': path, 'start_line': start, 'end_line': end,
                          'snippet_sha256': snippet_hash, 'scanner_message': message},
                scanner_version=scanner_result.scanner_version, repository=context.repository,
                branch=context.branch, commit_sha=context.commit_sha, organization_id=context.organization_id,
                project_id=context.project_id, asset_id=context.asset_id, security_run_id=context.security_run_id))
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError('Invalid Semgrep finding structure') from exc
    return candidates
