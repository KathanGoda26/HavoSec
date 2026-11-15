from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, JsonValue


class ScannerResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra='forbid')
    scanner: str
    scanner_version: str
    configuration: str
    started_at: datetime
    completed_at: datetime
    exit_code: int
    results: list[dict[str, JsonValue]]
    errors: list[dict[str, JsonValue]] = Field(default_factory=list)
    metadata: dict[str, JsonValue] = Field(default_factory=dict)
