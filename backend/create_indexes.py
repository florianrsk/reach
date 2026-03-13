#!/usr/bin/env python3
"""
Script to create MongoDB indexes for the Reach application.
Run this script to create optimal indexes for query performance.
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

# MongoDB connection
mongo_url = os.environ["MONGO_URL"]
db_name = os.environ["DB_NAME"]

async def create_indexes():
    """Create all necessary indexes for the Reach application."""
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print(f"Connecting to MongoDB: {mongo_url}")
    print(f"Database: {db_name}")
    
    # 1. Indexes for users collection
    print("\n=== Creating indexes for 'users' collection ===")
    
    # Email index (unique for user lookup by email)
    await db.users.create_index([("email", 1)], unique=True, name="email_unique")
    print("✓ Created index on 'email' (unique)")
    
    # User ID index (for lookups by user ID)
    await db.users.create_index([("id", 1)], unique=True, name="user_id_unique")
    print("✓ Created index on 'id' (unique)")
    
    # 2. Indexes for identities collection
    print("\n=== Creating indexes for 'identities' collection ===")
    
    # Handle index (unique for identity/handle lookup by handle)
    await db.identities.create_index([("handle", 1)], unique=True, name="handle_unique")
    print("✓ Created index on 'handle' (unique)")
    
    # User ID index (for finding identity by user ID)
    await db.identities.create_index([("user_id", 1)], unique=True, name="user_id_unique")
    print("✓ Created index on 'user_id' (unique)")
    
    # 3. Indexes for reach_attempts collection
    print("\n=== Creating indexes for 'reach_attempts' collection ===")
    
    # Identity ID index (for finding attempts by identity ID)
    await db.reach_attempts.create_index([("identity_id", 1)], name="identity_id")
    print("✓ Created index on 'identity_id'")
    
    # Decision status index (for filtering by decision)
    await db.reach_attempts.create_index([("decision", 1)], name="decision")
    print("✓ Created index on 'decision'")
    
    # Payment status index (for filtering by payment status)
    await db.reach_attempts.create_index([("payment_status", 1)], name="payment_status")
    print("✓ Created index on 'payment_status'")
    
    # Created_at index (for sorting by created_at)
    await db.reach_attempts.create_index([("created_at", -1)], name="created_at_desc")
    print("✓ Created index on 'created_at' (descending)")
    
    # Compound index: identity_id + created_at (for common query pattern)
    await db.reach_attempts.create_index(
        [("identity_id", 1), ("created_at", -1)], 
        name="identity_id_created_at"
    )
    print("✓ Created compound index on 'identity_id' + 'created_at'")
    
    # Compound index: identity_id + decision (for stats queries)
    await db.reach_attempts.create_index(
        [("identity_id", 1), ("decision", 1)], 
        name="identity_id_decision"
    )
    print("✓ Created compound index on 'identity_id' + 'decision'")
    
    # Compound index: identity_id + payment_status (for stats queries)
    await db.reach_attempts.create_index(
        [("identity_id", 1), ("payment_status", 1)], 
        name="identity_id_payment_status"
    )
    print("✓ Created compound index on 'identity_id' + 'payment_status'")
    
    # 4. Indexes for payment_transactions collection
    print("\n=== Creating indexes for 'payment_transactions' collection ===")
    
    # Session ID index (for finding transactions by session ID)
    await db.payment_transactions.create_index([("session_id", 1)], unique=True, name="session_id_unique")
    print("✓ Created index on 'session_id' (unique)")
    
    # Reach attempt ID index (for finding transactions by reach attempt ID)
    await db.payment_transactions.create_index([("reach_attempt_id", 1)], name="reach_attempt_id")
    print("✓ Created index on 'reach_attempt_id'")
    
    # 5. Indexes for blocked_senders collection
    print("\n=== Creating indexes for 'blocked_senders' collection ===")
    
    # Identity ID + sender email compound index (unique)
    await db.blocked_senders.create_index(
        [("identity_id", 1), ("sender_email", 1)], 
        unique=True, 
        name="identity_id_sender_email_unique"
    )
    print("✓ Created compound index on 'identity_id' + 'sender_email' (unique)")
    
    print("\n✅ All indexes created successfully!")
    
    # List all indexes for verification
    print("\n=== Verifying indexes ===")
    collections = ["users", "identities", "reach_attempts", "payment_transactions", "blocked_senders"]
    
    for collection_name in collections:
        print(f"\nIndexes for '{collection_name}' collection:")
        indexes = await db[collection_name].index_information()
        for index_name, index_info in indexes.items():
            if index_name != "_id_":  # Skip default _id index
                key = index_info.get("key", [])
                unique = index_info.get("unique", False)
                print(f"  - {index_name}: {key} {'(unique)' if unique else ''}")
    
    client.close()
    print("\n✅ Index creation completed!")

async def verify_query_performance():
    """Verify that indexes will be used for common queries."""
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("\n=== Verifying query performance ===")
    
    # Test queries that should use indexes
    test_queries = [
        ("users", {"email": "test@example.com"}, "User lookup by email"),
        ("identities", {"handle": "testhandle"}, "Identity lookup by handle"),
        ("identities", {"user_id": "test-user-id"}, "Identity lookup by user ID"),
        ("reach_attempts", {"identity_id": "test-identity-id"}, "Attempts by identity ID"),
        ("reach_attempts", {"decision": "reject"}, "Attempts by decision"),
        ("reach_attempts", {"payment_status": "completed"}, "Attempts by payment status"),
    ]
    
    for collection_name, query, description in test_queries:
        print(f"\nTesting: {description}")
        print(f"  Query: {query}")
        
        # Use explain to see if index is used
        try:
            cursor = db[collection_name].find(query)
            explain = await cursor.explain()
            winning_plan = explain.get("queryPlanner", {}).get("winningPlan", {})
            
            if winning_plan.get("inputStage", {}).get("stage") == "IXSCAN":
                print("  ✅ Query will use index")
            elif winning_plan.get("stage") == "IXSCAN":
                print("  ✅ Query will use index")
            else:
                print("  ⚠️  Query may not use index (COLLSCAN)")
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    client.close()

if __name__ == "__main__":
    print("MongoDB Index Creation Script")
    print("=" * 40)
    
    # Create indexes
    asyncio.run(create_indexes())
    
    # Note: Verification requires actual data in the database
    # Uncomment the line below to run verification (requires data)
    # asyncio.run(verify_query_performance())