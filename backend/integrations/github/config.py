"""Fail-closed GitHub App configuration loaded from the environment."""

from dataclasses import dataclass, field
import os
from pathlib import Path
from pydantic import SecretStr


class GitHubConfigurationError(RuntimeError):
    """Raised when GitHub App credentials are absent or unsafe to use."""


@dataclass(frozen=True)
class GitHubWebhookSettings:
    secret: SecretStr = field(repr=False)
    max_payload_bytes: int = 1_000_000

    @classmethod
    def from_environment(cls):
        secret = os.environ.get("GITHUB_WEBHOOK_SECRET", "")
        if len(secret.encode("utf-8")) < 32:
            raise GitHubConfigurationError("GITHUB_WEBHOOK_SECRET must contain at least 32 bytes")
        raw_limit = os.environ.get("GITHUB_WEBHOOK_MAX_BYTES", "1000000")
        try:
            limit = int(raw_limit)
        except ValueError as exc:
            raise GitHubConfigurationError("GITHUB_WEBHOOK_MAX_BYTES is invalid") from exc
        if not 1024 <= limit <= 5_000_000:
            raise GitHubConfigurationError("GITHUB_WEBHOOK_MAX_BYTES is invalid")
        return cls(SecretStr(secret), limit)


@dataclass(frozen=True)
class GitHubAppSettings:
    app_id: int
    private_key_path: Path = field(repr=False)
    installation_id: int | None = None
    api_url: str = "https://api.github.com"
    app_slug: str = "havosec-remediation-integration"

    @classmethod
    def from_environment(cls, *, require_installation: bool = False):
        app_id = _positive_integer("GITHUB_APP_ID")
        installation_id = _optional_positive_integer("GITHUB_INSTALLATION_ID")
        if require_installation and installation_id is None:
            raise GitHubConfigurationError("GITHUB_INSTALLATION_ID is required")

        raw_path = os.environ.get("GITHUB_APP_PRIVATE_KEY_PATH", "").strip()
        if not raw_path:
            raise GitHubConfigurationError("GITHUB_APP_PRIVATE_KEY_PATH is required")
        key_path = Path(raw_path).expanduser().resolve()
        if not key_path.is_file():
            raise GitHubConfigurationError("GitHub App private key file is unavailable")

        api_url = os.environ.get("GITHUB_API_URL", "https://api.github.com").strip().rstrip("/")
        if not api_url.startswith("https://"):
            raise GitHubConfigurationError("GITHUB_API_URL must use HTTPS")
        app_slug = os.environ.get("GITHUB_APP_SLUG", "havosec-remediation-integration").strip()
        if not app_slug or any(character not in "abcdefghijklmnopqrstuvwxyz0123456789-" for character in app_slug):
            raise GitHubConfigurationError("GITHUB_APP_SLUG is invalid")
        return cls(app_id, key_path, installation_id, api_url, app_slug)

    def read_private_key(self) -> bytes:
        try:
            key = self.private_key_path.read_bytes()
        except OSError as exc:
            raise GitHubConfigurationError("GitHub App private key file is unavailable") from exc
        if not key.startswith(b"-----BEGIN") or b"PRIVATE KEY-----" not in key[:80]:
            raise GitHubConfigurationError("GitHub App private key file is invalid")
        return key


def _positive_integer(name: str) -> int:
    value = os.environ.get(name, "").strip()
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise GitHubConfigurationError(f"{name} must be a positive integer") from exc
    if parsed <= 0:
        raise GitHubConfigurationError(f"{name} must be a positive integer")
    return parsed


def _optional_positive_integer(name: str) -> int | None:
    value = os.environ.get(name, "").strip()
    if not value:
        return None
    try:
        parsed = int(value)
    except ValueError as exc:
        raise GitHubConfigurationError(f"{name} must be a positive integer") from exc
    if parsed <= 0:
        raise GitHubConfigurationError(f"{name} must be a positive integer")
    return parsed
