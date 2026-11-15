"""Cryptographic identity for the exact patch that passed verification."""

import hashlib
import hmac


class PatchIntegrityError(ValueError):
    pass


def patch_sha256(patch: str) -> str:
    if not isinstance(patch, str) or not patch:
        raise PatchIntegrityError("Verified patch is unavailable")
    return hashlib.sha256(patch.encode("utf-8")).hexdigest()


def assert_verified_patch(remediation: dict) -> str:
    patch = remediation.get("verified_patch")
    expected = remediation.get("verified_patch_sha256")
    if not isinstance(expected, str) or len(expected) != 64:
        raise PatchIntegrityError("Verified patch integrity evidence is unavailable")
    actual = patch_sha256(patch)
    if not hmac.compare_digest(actual, expected):
        raise PatchIntegrityError("Verified patch integrity check failed")
    proposal = remediation.get("proposal") or {}
    if not hmac.compare_digest(patch, proposal.get("patch", "")):
        raise PatchIntegrityError("Stored proposal no longer matches the verified patch")
    declared = proposal.get("affected_files")
    verified_files = remediation.get("verified_affected_files")
    if not isinstance(declared, list) or declared != verified_files:
        raise PatchIntegrityError("Verified affected-file set no longer matches")
    return actual


def assert_patch_secret_safe(remediation: dict) -> None:
    from security_engine.agents.analysis import safe_snippet
    patch = remediation.get('verified_patch')
    files = remediation.get('verified_affected_files') or []
    if not isinstance(patch, str) or any(
            safe_snippet(path, patch, len(patch)) is None for path in files):
        raise PatchIntegrityError('Verified patch is not safe for pull request publication')
