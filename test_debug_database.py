import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables from backend/.env
env_path = os.path.join(os.path.dirname(__file__), "Reach-main", "backend", ".env")
print(f"Loading env from: {env_path}")
load_dotenv(env_path)


async def debug_database():
    # Connect to MongoDB
    mongo_uri = os.getenv("MONGO_URL")
    if mongo_uri:
        print(f"Connecting to MongoDB with URI: {mongo_uri[:50]}...")
    else:
        print("ERROR: MONGO_URL environment variable not found!")
        return

    client = AsyncIOMotorClient(mongo_uri)
    db_name = os.getenv("DB_NAME", "reach_db")
    print(f"Using database: {db_name}")
    db = client.get_database(db_name)

    # List all identities
    print("\n=== All identities in database ===")
    cursor = db.identities.find({})
    async for doc in cursor:
        print(f"ID: {doc.get('_id')}")
        print(f"Handle: {doc.get('handle')}")
        print(f"Display name: {doc.get('display_name')}")
        print(f"Face completed: {doc.get('face_completed')}")
        print(f"Created at: {doc.get('created_at')}")
        print("---")

    # Check for testuser handle specifically
    print("\n=== Searching for 'testuser' (case variations) ===")
    handles_to_check = ["testuser", "TestUser", "TESTUSER", "Testuser"]
    for handle in handles_to_check:
        identity = await db.identities.find_one({"handle": handle.lower()})
        if identity:
            print(
                f"Found with handle '{handle}' (stored as: {identity.get('handle')}):"
            )
            print(f"  Display name: {identity.get('display_name')}")
            print(f"  Face completed: {identity.get('face_completed')}")
        else:
            print(f"NOT found with handle '{handle}' (lowercase: {handle.lower()})")

    # List all collections
    print("\n=== All collections ===")
    collections = await db.list_collection_names()
    for coll in collections:
        print(f"- {coll}")

    client.close()


if __name__ == "__main__":
    asyncio.run(debug_database())
