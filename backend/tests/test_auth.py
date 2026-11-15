from datetime import datetime, timedelta, timezone
from jose import jwt
from utils.auth import ALGORITHM, JWT_SECRET, create_access_token, decode_access_token, organization_scope
from utils.roles import UserRole, normalize_role, permissions_for

def test_role_aliases_do_not_elevate_users():
    assert normalize_role("viewer") == "user"
    assert normalize_role("super_admin") == "superadmin"
    assert normalize_role("unknown") == "user"
    assert "platform:manage" not in permissions_for("user")

def test_access_token_has_identity_and_expiration():
    payload = decode_access_token(create_access_token("abc", "users"))
    assert payload["sub"] == "abc"
    assert payload["source"] == "users"
    assert payload["exp"] > payload["iat"]

def test_expired_access_token_is_rejected():
    token = jwt.encode({"sub": "abc", "type": "access", "exp": datetime.now(timezone.utc) - timedelta(seconds=1)}, JWT_SECRET, algorithm=ALGORITHM)
    try:
        decode_access_token(token)
        assert False, "expired token was accepted"
    except Exception as error:
        assert getattr(error, "status_code", None) == 401

def test_organization_scope():
    assert organization_scope({"role": UserRole.SUPERADMIN.value}) == {}
    assert organization_scope({"role": "admin", "organizationId": "org-1"}) == {"organizationId": "org-1"}
