from fastapi import APIRouter, HTTPException, Request
from datetime import datetime, timedelta
import bcrypt
# import jwt
from jose import jwt, ExpiredSignatureError, JWTError
import os
import secrets
from pymongo.errors import ServerSelectionTimeoutError, AutoReconnect

router = APIRouter()

JWT_SECRET = os.environ.get("JWT_SECRET", "havosec-super-secret-jwt-key-2025")

def create_token(user_id: str):
    payload = {
        "userId": user_id,
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def verify_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.post("/login")
async def login(request: Request):
    try:
        db = request.app.state.db
        data = await request.json()
        
        email = data.get("email")
        password = data.get("password")
        
        if not email or not password:
            raise HTTPException(status_code=400, detail="Email and password required")
        
        normalized_email = email.strip().lower()
        # The application has both client users and administrator users. The
        # shared login screen must resolve either account type.
        user_collection = db.users
        user = await user_collection.find_one({"email": normalized_email})
        if not user:
            user_collection = db.admin_users
            user = await user_collection.find_one({"email": normalized_email})
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Check if locked
        lock_until = user.get("lockUntil")
        if lock_until:
            if isinstance(lock_until, str):
                try:
                    lock_until = datetime.fromisoformat(lock_until.replace("Z", "+00:00"))
                except ValueError:
                    pass
            if isinstance(lock_until, datetime):
                if lock_until.tzinfo is not None:
                    lock_until = lock_until.replace(tzinfo=None)
                if lock_until > datetime.utcnow():
                    raise HTTPException(status_code=423, detail="Account temporarily locked")
        
        if not user.get("isActive", True):
            raise HTTPException(status_code=403, detail="Account is deactivated")
        
        # Robust password type checks (handles both str and bytes)
        stored_password = user["password"]
        if isinstance(stored_password, str):
            stored_password = stored_password.encode('utf-8')
        
        input_password = password
        if isinstance(input_password, str):
            input_password = input_password.encode('utf-8')
            
        if not bcrypt.checkpw(input_password, stored_password):
            # Increment login attempts
            attempts = user.get("loginAttempts", 0) + 1
            update = {"loginAttempts": attempts}
            if attempts >= 5:
                update["lockUntil"] = datetime.utcnow() + timedelta(hours=2)
            await user_collection.update_one({"_id": user["_id"]}, {"$set": update})
            
            # Create failed login notification
            await db.notifications.insert_one({
                "userId": str(user["_id"]),
                "type": "warning",
                "title": "Failed Login Attempt",
                "message": f"Failed login attempt detected at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC",
                "read": False,
                "createdAt": datetime.utcnow()
            })
            
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Reset login attempts
        await user_collection.update_one(
            {"_id": user["_id"]},
            {"$set": {"loginAttempts": 0, "lastLogin": datetime.utcnow()}, "$unset": {"lockUntil": ""}}
        )
        
        user_id = str(user["_id"])
        token = create_token(user_id)
        
        # Create login success notification
        await db.notifications.insert_one({
            "userId": user_id,
            "type": "info",
            "title": "New Login",
            "message": f"Successful login at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC",
            "read": False,
            "createdAt": datetime.utcnow()
        })
        
        return {
            "success": True,
            "message": "Login successful",
            "token": token,
            "user": {
                "id": user_id,
                "email": user["email"],
                "firstName": user.get("firstName", ""),
                "lastName": user.get("lastName", ""),
                "role": user.get("role", "viewer"),
                "company": user.get("company", ""),
                "emailVerified": user.get("emailVerified", False)
            }
        }
    except HTTPException as he:
        raise he
    except (ServerSelectionTimeoutError, AutoReconnect) as e:
        # MongoDB being offline is an infrastructure problem, not an invalid
        # login. Return a concise actionable response instead of leaking the
        # full PyMongo topology traceback into the login form.
        raise HTTPException(
            status_code=503,
            detail="Authentication database is unavailable. Check MONGO_URL in backend/.env and restart the backend.",
        ) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Unable to complete login. Please try again.") from e

@router.get("/me")
async def get_profile(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="No token provided")
    
    token = auth_header.replace("Bearer ", "")
    payload = verify_token(token)
    
    db = request.app.state.db
    from bson import ObjectId
    user = await db.users.find_one({"_id": ObjectId(payload["userId"])})
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "user": {
            "id": str(user["_id"]),
            "email": user["email"],
            "firstName": user.get("firstName", ""),
            "lastName": user.get("lastName", ""),
            "role": user.get("role", "viewer"),
            "company": user.get("company", ""),
            "emailVerified": user.get("emailVerified", False)
        }
    }
