from fastapi import APIRouter, HTTPException, Request, Depends
from datetime import datetime, timedelta
import secrets
import bcrypt
import hashlib
import os
from utils.auth import get_current_user
from utils.roles import UserRole

router = APIRouter()

# Token expiration times
PASSWORD_RESET_EXPIRY = timedelta(hours=1)
EMAIL_VERIFICATION_EXPIRY = timedelta(hours=24)

def generate_token():
    return secrets.token_urlsafe(32)

def token_hash(token: str):
    return hashlib.sha256(token.encode()).hexdigest()

async def find_user_by_email(db, email):
    user = await db.users.find_one({"email": email})
    return (user, "users") if user else (None, None)

@router.post("/forgot-password")
async def forgot_password(request: Request):
    """Request password reset - generates reset token"""
    db = request.app.state.db
    data = await request.json()
    email = data.get("email", "").lower()
    
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    
    user, account_source = await find_user_by_email(db, email)
    if not user:
        # Don't reveal if user exists - return success anyway
        return {"message": "If an account exists with this email, a reset link has been sent"}
    
    # Generate reset token
    reset_token = generate_token()
    expires_at = datetime.utcnow() + PASSWORD_RESET_EXPIRY
    
    # Store token in database
    await db.password_resets.delete_many({"email": email})  # Remove old tokens
    await db.password_resets.insert_one({
        "email": email,
        "tokenHash": token_hash(reset_token),
        "accountSource": account_source,
        "expiresAt": expires_at,
        "createdAt": datetime.utcnow()
    })
    
    # In production, send email here
    # For now, return token in response (for testing)
    reset_link = f"/auth/reset-password?token={reset_token}"
    
    response = {
        "message": "If an account exists with this email, a reset link has been sent",
        "expiresIn": "1 hour"
    }
    if os.environ.get("AUTH_EXPOSE_TEST_TOKENS", "").lower() == "true":
        response["resetLink"] = reset_link
    return response

@router.post("/verify-reset-token")
async def verify_reset_token(request: Request):
    """Verify if reset token is valid"""
    db = request.app.state.db
    data = await request.json()
    token = data.get("token")
    
    if not token:
        raise HTTPException(status_code=400, detail="Token is required")
    
    reset_record = await db.password_resets.find_one({"tokenHash": token_hash(token)})
    
    if not reset_record:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    
    if reset_record["expiresAt"] < datetime.utcnow():
        await db.password_resets.delete_one({"_id": reset_record["_id"]})
        raise HTTPException(status_code=400, detail="Token has expired")
    
    return {"valid": True}

@router.post("/reset-password")
async def reset_password(request: Request):
    """Reset password using token"""
    db = request.app.state.db
    data = await request.json()
    token = data.get("token")
    new_password = data.get("newPassword")
    
    if not token or not new_password:
        raise HTTPException(status_code=400, detail="Token and new password are required")
    
    if len(new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    
    reset_record = await db.password_resets.find_one({"tokenHash": token_hash(token)})
    
    if not reset_record:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    
    if reset_record["expiresAt"] < datetime.utcnow():
        await db.password_resets.delete_one({"_id": reset_record["_id"]})
        raise HTTPException(status_code=400, detail="Token has expired")
    
    # Hash new password
    hashed_password = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    
    # Update user password
    collection = db[reset_record.get("accountSource", "users")]
    result = await collection.update_one(
        {"email": reset_record["email"]},
        {"$set": {"password": hashed_password, "updatedAt": datetime.utcnow()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Delete used token
    await db.password_resets.delete_one({"_id": reset_record["_id"]})
    
    return {"message": "Password reset successful", "success": True}

@router.post("/send-verification")
async def send_verification_email(request: Request):
    """Send or resend email verification"""
    db = request.app.state.db
    data = await request.json()
    email = data.get("email", "").lower()
    
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    
    user, account_source = await find_user_by_email(db, email)
    if not user:
        return {"message": "If an eligible account exists, a verification email has been sent"}
    
    if user.get("emailVerified"):
        return {"message": "If an eligible account exists, a verification email has been sent"}
    
    # Generate verification token
    verification_token = generate_token()
    expires_at = datetime.utcnow() + EMAIL_VERIFICATION_EXPIRY
    
    # Store token
    await db.email_verifications.delete_many({"email": email})
    await db.email_verifications.insert_one({
        "email": email,
        "tokenHash": token_hash(verification_token),
        "accountSource": account_source,
        "expiresAt": expires_at,
        "createdAt": datetime.utcnow()
    })
    
    verification_link = f"/auth/verify-email?token={verification_token}"
    
    response = {
        "message": "Verification email sent",
        "expiresIn": "24 hours"
    }
    if os.environ.get("AUTH_EXPOSE_TEST_TOKENS", "").lower() == "true":
        response["verificationLink"] = verification_link
    return response

@router.post("/verify-email")
async def verify_email(request: Request):
    """Verify email using token"""
    db = request.app.state.db
    data = await request.json()
    token = data.get("token")
    
    if not token:
        raise HTTPException(status_code=400, detail="Token is required")
    
    verification_record = await db.email_verifications.find_one({"tokenHash": token_hash(token)})
    
    if not verification_record:
        raise HTTPException(status_code=400, detail="Invalid or expired verification link")
    
    if verification_record["expiresAt"] < datetime.utcnow():
        await db.email_verifications.delete_one({"_id": verification_record["_id"]})
        raise HTTPException(status_code=400, detail="Verification link has expired")
    
    # Update user as verified
    collection = db[verification_record.get("accountSource", "users")]
    result = await collection.update_one(
        {"email": verification_record["email"]},
        {"$set": {"emailVerified": True, "emailVerifiedAt": datetime.utcnow()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Delete used token
    await db.email_verifications.delete_one({"_id": verification_record["_id"]})
    
    return {"message": "Email verified successfully", "success": True}

@router.get("/verification-status/{email}")
async def get_verification_status(email: str, request: Request, current_user=Depends(get_current_user)):
    """Check email verification status"""
    db = request.app.state.db
    requested_email = email.lower()
    if current_user["role"] not in {UserRole.SUPERADMIN.value, UserRole.ADMIN.value} and current_user["email"].lower() != requested_email:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    user, _ = await find_user_by_email(db, requested_email)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "email": requested_email,
        "verified": user.get("emailVerified", False),
        "verifiedAt": user.get("emailVerifiedAt")
    }
