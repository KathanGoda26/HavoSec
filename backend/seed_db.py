import asyncio
from utils.seed import seed_database
from core.database import load_backend_environment, DatabaseSettings, create_database_client

load_backend_environment()

async def main():
    # Connect to MongoDB
    settings = DatabaseSettings.from_environment()
    client = create_database_client(settings)
    try:
        db = client[settings.database_name]
        print("Starting explicit database seeding...")
        await seed_database(db)
        print("Database seeding completed!")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(main())
