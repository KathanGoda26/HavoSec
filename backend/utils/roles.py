"""Central role definitions and compatibility aliases."""
from enum import Enum

class UserRole(str, Enum):
    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    USER = "user"

ROLE_ALIASES = {"super_admin": "superadmin", "super-admin": "superadmin", "viewer": "user", "client": "user"}
ROLE_PERMISSIONS = {
    "superadmin": ["dashboard:read", "security:write", "settings:write", "users:manage", "roles:manage", "platform:manage"],
    "admin": ["dashboard:read", "security:write", "settings:write", "users:manage"],
    "user": ["dashboard:read"],
}

def normalize_role(value) -> str:
    raw = value.value if isinstance(value, UserRole) else str(value or "user")
    role = ROLE_ALIASES.get(raw.strip().lower().replace(" ", "_"), raw.strip().lower().replace(" ", "_"))
    return role if role in ROLE_PERMISSIONS else "user"

def permissions_for(value):
    return list(ROLE_PERMISSIONS[normalize_role(value)])
