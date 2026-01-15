from fastapi import APIRouter, HTTPException, Request, Depends
from datetime import datetime, timedelta
import bcrypt
import jwt
import os

router = APIRouter()

JWT_SECRET = os.environ.get("ADMIN_JWT_SECRET", "havosec-admin-super-secret-jwt-key-2025")

def create_token(user_id: str, email: str):
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def verify_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.post("/login")
async def admin_login(request: Request):
    db = request.app.state.db
    data = await request.json()
    
    email = data.get("email")
    password = data.get("password")
    
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password required")
    
    user = await db.admin_users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not bcrypt.checkpw(password.encode(), user["password"].encode()):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(str(user["_id"]), user["email"])
    
    return {
        "success": True,
        "token": token,
        "user": {
            "id": str(user["_id"]),
            "email": user["email"],
            "firstName": user.get("firstName", ""),
            "lastName": user.get("lastName", ""),
            "role": user.get("role", "admin")
        }
    }

@router.get("/me")
async def get_current_user(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="No token provided")
    
    token = auth_header.replace("Bearer ", "")
    payload = verify_token(token)
    
    db = request.app.state.db
    from bson import ObjectId
    user = await db.admin_users.find_one({"_id": ObjectId(payload["user_id"])})
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "user": {
            "id": str(user["_id"]),
            "email": user["email"],
            "firstName": user.get("firstName", ""),
            "lastName": user.get("lastName", ""),
            "role": user.get("role", "admin")
        }
    }
