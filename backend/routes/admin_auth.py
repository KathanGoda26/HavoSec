"""Compatibility admin login routes using the shared auth system."""
import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Request
from utils.auth import create_access_token, get_current_user, serialize_user
from utils.roles import UserRole

router = APIRouter()

@router.post("/login")
async def admin_login(request: Request):
    data = await request.json()
    email = str(data.get("email", "")).strip().lower()
    password = data.get("password")
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password required")
    user = await request.app.state.db.users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    stored = user.get("password", "")
    stored = stored.encode() if isinstance(stored, str) else stored
    if not stored or not bcrypt.checkpw(password.encode(), stored):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if user.get("status", "active") != "active" or user.get("isActive", True) is False:
        raise HTTPException(status_code=403, detail="Account is inactive")
    safe_user = serialize_user(user, "users")
    if safe_user["role"] not in {UserRole.SUPERADMIN.value, UserRole.ADMIN.value}:
        raise HTTPException(status_code=403, detail="Administrator access required")
    return {"success": True, "token": create_access_token(str(user["_id"]), "users"), "admin": safe_user, "user": safe_user}

@router.get("/me")
async def admin_me(user=Depends(get_current_user)):
    if user["role"] not in {UserRole.SUPERADMIN.value, UserRole.ADMIN.value}:
        raise HTTPException(status_code=403, detail="Administrator access required")
    return {"user": user}
