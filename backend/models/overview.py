from typing import Literal
from pydantic import BaseModel
from models.findings import FindingResponse
from models.security_runs import SecurityRunResponse
from models.activity import ActivityResponse


class OverviewResponse(BaseModel):
    security_score: None = None
    security_score_status: Literal['unavailable'] = 'unavailable'
    counts: dict[str, int]
    open_findings: int
    critical_findings: int
    severity_counts: dict[str, int]
    latest_security_run: SecurityRunResponse | None
    recent_findings: list[FindingResponse]
    recent_runs: list[SecurityRunResponse]
    recent_activity: list[ActivityResponse]
