#!/usr/bin/env python3
"""
Migration script to update existing identities for Face system
"""

import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / "backend" / ".env")


async def migrate_identities():
    """Update existing identities for Face system"""

    # MongoDB connection
    mongo_url = os.environ["MONGO_URL"]
    db_name = os.environ["DB_NAME"]

    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]

    print("Starting Face system migration...")

    # Count existing identities
    count = await db.identities.count_documents({})
    print(f"Found {count} existing identities")

    # Update all identities to have face_completed: false
    # and add Face fields with null values
    result = await db.identities.update_many(
        {},
        {
            "$set": {
                "face_completed": False,
                "display_name": None,
                "headline": None,
                "current_focus": None,
                "availability_signal": None,
                "prompt": None,
                "photo_url": None,
                "links": None,
            }
        },
    )

    print(f"Updated {result.modified_count} identities")
    print("Migration complete!")

    # Show sample of updated identities
    print("\nSample of updated identities:")
    async for identity in db.identities.find(
        {}, {"_id": 0, "handle": 1, "face_completed": 1}
    ).limit(5):
        print(
            f"  {identity.get('handle')}: face_completed={identity.get('face_completed')}"
        )

    client.close()


if __name__ == "__main__":
    asyncio.run(migrate_identities())
