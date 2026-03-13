import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), "Reach-main", "backend", ".env")
load_dotenv(env_path)


async def test_mongo_connection():
    mongo_url = os.getenv("MONGO_URL")
    print(f"MongoDB URL: {mongo_url}")

    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(mongo_url)

        # Test connection
        await client.admin.command("ping")
        print("SUCCESS: MongoDB connection successful!")

        # List databases
        print("\nAvailable databases:")
        databases = await client.list_database_names()
        for db_name in databases:
            print(f"  - {db_name}")

        # Check reach_db
        db = client["reach_db"]
        print(f"\nCollections in reach_db:")
        collections = await db.list_collection_names()
        for coll in collections:
            print(f"  - {coll}")

            # Count documents
            count = await db[coll].count_documents({})
            print(f"    Documents: {count}")

            # Show first few documents if any
            if count > 0:
                cursor = db[coll].find({}).limit(3)
                async for doc in cursor:
                    print(
                        f"    Sample: {doc.get('_id')} - {doc.get('handle', 'No handle')}"
                    )

        client.close()

    except Exception as e:
        print(f"ERROR: MongoDB connection failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_mongo_connection())
