"""Deterministic Semgrep before/after comparison for isolated remediations."""
from collections import Counter
from datetime import datetime, timezone

from models.remediations import VerificationResult


SEVERITY_RANK = {'INFO': 0, 'LOW': 1, 'WARNING': 2, 'MEDIUM': 2, 'ERROR': 3,
                 'HIGH': 3, 'CRITICAL': 4}
SEVERITY_NAME = {'INFO': 'info', 'LOW': 'low', 'WARNING': 'medium', 'MEDIUM': 'medium',
                 'ERROR': 'high', 'HIGH': 'high', 'CRITICAL': 'critical'}


def _record(item):
    extra = item.get('extra') if isinstance(item.get('extra'), dict) else {}
    start = item.get('start') if isinstance(item.get('start'), dict) else {}
    severity = str(extra.get('severity') or 'INFO').upper()
    return {'rule': str(item.get('check_id') or ''),
            'path': str(item.get('path') or '').replace('\\', '/'),
            'line': int(start.get('line') or 0), 'severity': severity}


def _key(record):
    return record['rule'], record['path'], record['line']


def _stable_key(record):
    return record['rule'], record['path']


def _counts(records):
    values = Counter(SEVERITY_NAME.get(item['severity'], 'info') for item in records)
    return {name: values.get(name, 0) for name in ('critical', 'high', 'medium', 'low', 'info')}


def compare_semgrep(remediation_id, finding, before_scan, after_scan):
    before = [_record(item) for item in before_scan.results]
    after = [_record(item) for item in after_scan.results]
    evidence = finding.get('evidence') if isinstance(finding.get('evidence'), dict) else {}
    location = str(finding.get('location') or '')
    fallback_path, _, fallback_lines = location.partition(':')
    fallback_line = fallback_lines.partition('-')[0]
    target = (str(evidence.get('rule_id') or finding.get('category') or ''),
              str(evidence.get('path') or fallback_path).replace('\\', '/'),
              int(evidence.get('start_line') or fallback_line or 0))
    original_present = target in {_key(item) for item in after}
    remaining = Counter(_stable_key(item) for item in before)
    new = []
    for item in after:
        key = _stable_key(item)
        if remaining[key]:
            remaining[key] -= 1
        else:
            new.append(item)
    raw_severity = finding.get('severity') or 'info'
    finding_severity = getattr(raw_severity, 'value', raw_severity)
    threshold = SEVERITY_RANK.get(str(finding_severity).upper(), 0)
    regressions = [item for item in new if SEVERITY_RANK.get(item['severity'], 0) >= threshold]
    if original_present:
        status, summary = 'failed', 'The original Semgrep finding remains after the proposed patch.'
    elif regressions:
        status, summary = 'failed', 'The original finding disappeared, but equal-or-higher severity findings were introduced.'
    else:
        status, summary = 'verified', 'The original Semgrep finding disappeared with no new equal-or-higher severity findings.'
    return VerificationResult(
        remediation_id=str(remediation_id), status=status,
        original_finding_present=original_present,
        new_findings_count=len(new), new_equal_or_higher_findings_count=len(regressions),
        before_finding_count=len(before), after_finding_count=len(after),
        before_severity_counts=_counts(before), after_severity_counts=_counts(after),
        scanner=after_scan.scanner, scanner_version=after_scan.scanner_version,
        summary=summary, verified_at=datetime.now(timezone.utc))
