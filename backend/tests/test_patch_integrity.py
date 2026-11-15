import copy
import hashlib

import pytest

from security_engine.patch_integrity import (PatchIntegrityError, assert_patch_secret_safe,
                                             assert_verified_patch, patch_sha256)


PATCH = "--- a/app.py\n+++ b/app.py\n@@ -1 +1 @@\n-old\n+new\n"


def remediation():
    return {
        "proposal": {"patch": PATCH, "affected_files": ["app.py"]},
        "verified_patch": PATCH,
        "verified_patch_sha256": hashlib.sha256(PATCH.encode("utf-8")).hexdigest(),
        "verified_affected_files": ["app.py"],
    }


def test_exact_verified_patch_hash_chain_passes():
    record = remediation()
    assert assert_verified_patch(record) == patch_sha256(PATCH)


@pytest.mark.parametrize("mutation", ["verified_patch", "proposal_patch", "files", "hash"])
def test_any_post_verification_mutation_is_rejected(mutation):
    record = copy.deepcopy(remediation())
    if mutation == "verified_patch":
        record["verified_patch"] += "\n"
    elif mutation == "proposal_patch":
        record["proposal"]["patch"] += "\n"
    elif mutation == "files":
        record["proposal"]["affected_files"] = ["other.py"]
    else:
        record["verified_patch_sha256"] = "0" * 64
    with pytest.raises(PatchIntegrityError):
        assert_verified_patch(record)


def test_hash_is_over_exact_utf8_bytes_without_normalization():
    assert patch_sha256(PATCH) != patch_sha256(PATCH.replace("\n", "\r\n"))


def test_secret_material_is_rejected_before_pr_delivery():
    record = remediation()
    secret_patch = PATCH.replace('+new', '+access_token="ghp_abcdefghijklmnopqrstuvwxyz123456"')
    record['verified_patch'] = secret_patch
    record['proposal']['patch'] = secret_patch
    record['verified_patch_sha256'] = patch_sha256(secret_patch)
    with pytest.raises(PatchIntegrityError):
        assert_patch_secret_safe(record)
