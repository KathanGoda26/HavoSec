"""Conservative deterministic assessment of scanner evidence; no code execution."""
from datetime import datetime, timezone
from models.findings import ValidationResult, ValidationStatus


REQUIRED_SEMGREP_EVIDENCE = ('rule_id', 'path', 'start_line', 'end_line', 'snippet_sha256')


def validate_finding(finding, actor_id):
    evidence = finding.get('evidence') if isinstance(finding.get('evidence'), dict) else {}
    metadata = finding.get('source_metadata') if isinstance(finding.get('source_metadata'), dict) else {}
    factors, uncertainties = [], []
    complete_evidence = all(evidence.get(key) not in (None, '') for key in REQUIRED_SEMGREP_EVIDENCE)
    if finding.get('source') == 'semgrep':
        factors.append('Finding was produced by the configured deterministic Semgrep scanner.')
    else:
        uncertainties.append('Finding source is not the configured Semgrep scanner.')
    if complete_evidence:
        factors.append('Rule, repository-relative location, line range, and source hash evidence are present.')
    else:
        uncertainties.append('Deterministic scanner evidence is incomplete.')
    if metadata.get('commit_sha'):
        factors.append('The finding is tied to a recorded source commit.')
    else:
        uncertainties.append('A source commit is not recorded in finding metadata.')
    if finding.get('fingerprint'):
        factors.append('A stable finding fingerprint is available for repeat-run correlation.')
    else:
        uncertainties.append('A stable finding fingerprint is unavailable.')

    sufficient = finding.get('source') == 'semgrep' and complete_evidence and bool(metadata.get('commit_sha')) and bool(finding.get('fingerprint'))
    status, confidence = ('likely', 0.8) if sufficient else ('needs_review', 0.4)
    return ValidationResult(
        finding_id=str(finding['_id']),
        security_run_id=finding.get('last_security_run_id') or finding.get('security_run_id'),
        status=status,
        confidence=confidence,
        reasoning_summary=('Deterministic scanner evidence is internally consistent, but exploitability has not been demonstrated.'
                           if sufficient else 'Available evidence is insufficient for a reliable automated validation decision.'),
        evidence_summary=('Semgrep rule and location evidence were checked without executing repository code or contacting a target.'),
        supporting_factors=factors,
        uncertainties=uncertainties + ['No exploit or dynamic validation was executed.'],
        validated_at=datetime.now(timezone.utc),
        validation_method='deterministic',
        requested_by=actor_id,
    )


def apply_agent_assessment(deterministic, assessment):
    """Application-owned conservative decision policy; the model only recommends."""
    if assessment is None:
        return deterministic
    recommended, confidence = assessment.status, assessment.confidence
    if deterministic.status.value == 'likely' and recommended == 'confirmed' and confidence >= 0.85:
        status = 'confirmed'
    elif deterministic.status.value == 'likely' and recommended in {'confirmed', 'likely'}:
        status = 'likely'
    elif recommended == 'rejected' and confidence >= 0.9:
        status = 'rejected'
    else:
        status = 'needs_review'
    return deterministic.model_copy(update={
        'status': ValidationStatus(status),
        'confidence': confidence,
        'reasoning_summary': assessment.summary,
        'supporting_factors': assessment.supporting_factors,
        'uncertainties': assessment.uncertainties,
        'validation_method': 'agent_assisted',
    })
