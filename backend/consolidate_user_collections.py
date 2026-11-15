"""One-time migration from admin_users to users plus three role test accounts."""
import asyncio
import os
import secrets
from datetime import datetime, timezone
from pathlib import Path

import bcrypt
from bson import ObjectId
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

from utils.roles import normalize_role

load_dotenv(Path(__file__).with_name(".env"))

ROLE_RANK = {"user": 1, "admin": 2, "superadmin": 3}
ROLE_ACCOUNTS = (
    ("superadmin.demo@havosec.com", "Demo", "Superadmin", "superadmin"),
    ("admin.demo@havosec.com", "Demo", "Admin", "admin"),
    ("user.demo@havosec.com", "Demo", "User", "user"),
)


async def migrate_admins(db) -> int:
    if "admin_users" not in await db.list_collection_names():
        return 0
    migrated = 0
    async for legacy in db.admin_users.find({}):
        email = str(legacy.get("email", "")).strip().lower()
        if not email:
            continue
        legacy["email"] = email
        legacy["role"] = normalize_role(legacy.get("role") or "admin")
        legacy["status"] = legacy.get("status") or ("inactive" if legacy.get("isActive") is False else "active")
        existing = await db.users.find_one({"email": email})
        if existing:
            existing_role = normalize_role(existing.get("role"))
            if ROLE_RANK[legacy["role"]] > ROLE_RANK[existing_role]:
                await db.users.update_one(
                    {"_id": existing["_id"]},
                    {"$set": {"role": legacy["role"], "updatedAt": datetime.now(timezone.utc)}},
                )
        else:
            try:
                await db.users.insert_one(legacy)
            except Exception:
                legacy.pop("_id", None)
                await db.users.insert_one(legacy)
        migrated += 1
    return migrated


async def create_role_accounts(db):
    organization_id = ObjectId()
    credentials = []
    now = datetime.now(timezone.utc)
    for email, first_name, last_name, role in ROLE_ACCOUNTS:
        password = secrets.token_urlsafe(18)
        document = {
            "email": email,
            "password": bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode(),
            "firstName": first_name,
            "lastName": last_name,
            "role": role,
            "status": "active",
            "isActive": True,
            "emailVerified": True,
            "updatedAt": now,
        }
        if role != "superadmin":
            document["organizationId"] = organization_id
        await db.users.update_one(
            {"email": email},
            {"$set": document, "$setOnInsert": {"createdAt": now}},
            upsert=True,
        )
        credentials.append((role, email, password))
    return credentials


async def main():
    mongo_url = os.environ.get("MONGO_URL")
    if not mongo_url:
        raise SystemExit("MONGO_URL is required in backend/.env")
    client = AsyncIOMotorClient(mongo_url)
    try:
        db = client[os.environ.get("DB_NAME", "havosec")]
        migrated = await migrate_admins(db)
        credentials = await create_role_accounts(db)
        await db.password_resets.update_many({"accountSource": "admin_users"}, {"$set": {"accountSource": "users"}})
        await db.email_verifications.update_many({"accountSource": "admin_users"}, {"$set": {"accountSource": "users"}})
        for role, email, _ in credentials:
            account = await db.users.find_one({"email": email, "role": role, "status": "active"})
            if not account:
                raise RuntimeError(f"Verification failed for {role}")
        if "admin_users" in await db.list_collection_names():
            await db.admin_users.drop()
        print(f"Migrated {migrated} legacy admin account(s); admin_users removed.")
        print("Temporary credentials (change these passwords after first login):")
        for role, email, password in credentials:
            print(f"{role}: {email} | {password}")
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(main())
