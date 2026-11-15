"""Idempotently create the first superadmin from environment variables.

Required: SUPERADMIN_EMAIL and SUPERADMIN_PASSWORD.
Run explicitly from the repository root; it is never invoked at app startup.
"""
import asyncio
import os
from datetime import datetime
import bcrypt
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv("backend/.env")

async def main():
    email = os.environ.get("SUPERADMIN_EMAIL", "").strip().lower()
    password = os.environ.get("SUPERADMIN_PASSWORD", "")
    if not email or len(password) < 12:
        raise SystemExit("Set SUPERADMIN_EMAIL and SUPERADMIN_PASSWORD (minimum 12 characters).")
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ.get("DB_NAME", "havosec")]
    existing = await db.users.find_one({"email": email})
    if existing:
        print("Superadmin bootstrap skipped: account already exists; password was not changed.")
        client.close()
        return
    now = datetime.utcnow()
    await db.users.insert_one({"email": email, "password": bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode(), "firstName": "Platform", "lastName": "Administrator", "role": "superadmin", "status": "active", "isActive": True, "createdAt": now, "updatedAt": now})
    client.close()
    print("Superadmin created successfully.")

if __name__ == "__main__":
    asyncio.run(main())
