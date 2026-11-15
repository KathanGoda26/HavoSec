"""GitHub App authentication without persisting generated credentials."""

from datetime import datetime, timedelta, timezone

import jwt

from .config import GitHubAppSettings


def create_app_jwt(settings: GitHubAppSettings, *, now: datetime | None = None) -> str:
    """Create a short-lived GitHub App JWT; callers must never log the result."""
    issued_at = now or datetime.now(timezone.utc)
    if issued_at.tzinfo is None:
        issued_at = issued_at.replace(tzinfo=timezone.utc)
    payload = {
        "iat": int((issued_at - timedelta(seconds=60)).timestamp()),
        "exp": int((issued_at + timedelta(minutes=9)).timestamp()),
        "iss": str(settings.app_id),
    }
    return jwt.encode(payload, settings.read_private_key(), algorithm="RS256")
