"""Authentication and normalization for untrusted GitHub webhook requests."""

import hashlib
import hmac
import re


class GitHubWebhookError(ValueError):
    pass


DELIVERY_PATTERN = re.compile(r"^[0-9a-fA-F-]{16,64}$")
SUPPORTED_EVENTS = {"pull_request", "check_run", "check_suite", "workflow_run"}


def verify_signature(body: bytes, signature: str | None, secret: str) -> None:
    if not signature or not re.fullmatch(r"sha256=[0-9a-f]{64}", signature):
        raise GitHubWebhookError("GitHub webhook signature is missing or invalid")
    expected = "sha256=" + hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise GitHubWebhookError("GitHub webhook signature is missing or invalid")


def validate_delivery(value: str | None) -> str:
    if not value or not DELIVERY_PATTERN.fullmatch(value):
        raise GitHubWebhookError("GitHub delivery identifier is missing or invalid")
    return value.lower()


def check_state(status, conclusion) -> str:
    if status != "completed":
        return "pending"
    if conclusion in {"success", "neutral", "skipped"}:
        return "passing"
    if conclusion in {"failure", "cancelled", "timed_out", "action_required",
                      "stale", "startup_failure"}:
        return "failing"
    return "unknown"


def aggregate_checks(checks: dict) -> str:
    states = set(checks.values())
    if "failing" in states:
        return "failing"
    if "pending" in states:
        return "pending"
    if states and states <= {"passing"}:
        return "passing"
    return "unknown"
