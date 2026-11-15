"""Idempotently normalize legacy HavoSec account roles and statuses."""
import asyncio
import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()


async def migrate_collection(db, collection_name: str, default_role: str) -> int:
    collection = db[collection_name]
    changed = 0
    async for account in collection.find({}, {"role": 1, "status": 1, "isActive": 1}):
        role = str(account.get("role") or default_role).strip().lower()
        role = {"super_admin": "superadmin", "super-admin": "superadmin", "viewer": "user", "client": "user"}.get(role, role)
        if role not in {"superadmin", "admin", "user"}:
            role = default_role
        account_status = account.get("status") or ("inactive" if account.get("isActive") is False else "active")
        result = await collection.update_one(
            {"_id": account["_id"]},
            {"$set": {"role": role, "status": account_status, "updatedAt": datetime.now(timezone.utc)}},
        )
        changed += result.modified_count
    return changed


async def main():
    client = AsyncIOMotorClient(os.environ.get("MONGO_URL", "mongodb://localhost:27017"))
    try:
        db = client[os.environ.get("DB_NAME", "havosec")]
        users = await migrate_collection(db, "users", "user")
        print(f"Normalized {users} user account(s).")
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(main())
