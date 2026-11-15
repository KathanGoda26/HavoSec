"""Shared JWT authentication and role authorization dependencies."""
from datetime import datetime, timedelta, timezone
import os
from bson import ObjectId
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import ExpiredSignatureError, JWTError, jwt
from utils.roles import UserRole, normalize_role, permissions_for
from core.membership import membership_value

ALGORITHM = "HS256"
ACCESS_TOKEN_MINUTES = int(os.environ.get("ACCESS_TOKEN_MINUTES", "60"))
JWT_SECRET = os.environ.get("JWT_SECRET")
if not JWT_SECRET and os.environ.get("APP_ENV", "development").lower() == "production":
    raise RuntimeError("JWT_SECRET must be configured in production")
JWT_SECRET = JWT_SECRET or "havosec-development-secret-change-me"
bearer_scheme = HTTPBearer(auto_error=False)

def create_access_token(user_id: str, account_source: str = "users") -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode({"sub": str(user_id), "source": account_source, "iat": now, "exp": now + timedelta(minutes=ACCESS_TOKEN_MINUTES), "type": "access"}, JWT_SECRET, algorithm=ALGORITHM)

def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
    except ExpiredSignatureError as exc:
        raise HTTPException(status_code=401, detail="Session expired") from exc
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid session") from exc
    user_id = payload.get("sub") or payload.get("userId") or payload.get("user_id")
    if not user_id or payload.get("type", "access") != "access":
        raise HTTPException(status_code=401, detail="Invalid session")
    payload["sub"] = str(user_id)
    return payload

def possible_ids(user_id: str):
    values = [user_id]
    try: values.append(ObjectId(user_id))
    except (TypeError, ValueError): pass
    return values

async def find_account(db, user_id: str, source: str | None = None):
    query = {"_id": {"$in": possible_ids(user_id)}}
    account = await db.users.find_one(query)
    return (account, "users") if account else (None, None)

def serialize_user(account: dict, source: str) -> dict:
    active = account.get("status", "active") == "active" and account.get("isActive", True) is not False
    role = normalize_role(account.get("role"))
    organization_id, _ = membership_value(account)
    return {"id": str(account["_id"]), "email": account.get("email", ""), "firstName": account.get("firstName", ""), "lastName": account.get("lastName", ""), "company": account.get("company", ""), "organizationId": str(organization_id) if organization_id else None, "role": role, "status": "active" if active else "inactive", "permissions": permissions_for(role), "emailVerified": account.get("emailVerified", False), "accountSource": source}

async def get_current_user(request: Request, credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)):
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Authentication required")
    payload = decode_access_token(credentials.credentials)
    account, source = await find_account(request.app.state.db, payload["sub"], payload.get("source"))
    if not account: raise HTTPException(status_code=401, detail="Account no longer exists")
    user = serialize_user(account, source)
    if user["status"] != "active": raise HTTPException(status_code=403, detail="Account is inactive")
    return user

require_authenticated_user = get_current_user

def require_roles(*roles: UserRole | str):
    allowed = {normalize_role(role) for role in roles}
    async def dependency(user=Depends(get_current_user)):
        if user["role"] not in allowed: raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return dependency

def organization_scope(user: dict, field: str = "organizationId") -> dict:
    if user["role"] == UserRole.SUPERADMIN.value: return {}
    return {field: user.get("organizationId") or "__unassigned__"}
