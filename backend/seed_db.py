import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from utils.seed import seed_database
import os
from dotenv import load_dotenv

load_dotenv()

async def main():
    # Connect to MongoDB
    mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    db_name = os.getenv("DB_NAME", "havosec")
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("Starting database seeding...")
    await seed_database(db)
    print("Database seeding completed!")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(main())
