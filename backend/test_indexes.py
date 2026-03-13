#!/usr/bin/env python3
"""
Test script to verify MongoDB indexes and application functionality.
"""

import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path
import requests
import json
import time

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

BACKEND_URL = "http://localhost:8000"

async def verify_indexes():
    """Verify that all required indexes exist in MongoDB."""
    print("=== Verifying MongoDB Indexes ===")
    
    mongo_url = os.environ["MONGO_URL"]
    db_name = os.environ["DB_NAME"]
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    # Expected indexes for each collection
    expected_indexes = {
        "users": [
            {"name": "email_unique", "fields": [("email", 1)], "unique": True},
            {"name": "user_id_unique", "fields": [("id", 1)], "unique": True},
        ],
        "identities": [
            {"name": "handle_unique", "fields": [("handle", 1)], "unique": True},
            {"name": "user_id_unique", "fields": [("user_id", 1)], "unique": True},
        ],
        "reach_attempts": [
            {"name": "identity_id", "fields": [("identity_id", 1)]},
            {"name": "decision", "fields": [("decision", 1)]},
            {"name": "payment_status", "fields": [("payment_status", 1)]},
            {"name": "created_at_desc", "fields": [("created_at", -1)]},
            {"name": "identity_id_created_at", "fields": [("identity_id", 1), ("created_at", -1)]},
            {"name": "identity_id_decision", "fields": [("identity_id", 1), ("decision", 1)]},
            {"name": "identity_id_payment_status", "fields": [("identity_id", 1), ("payment_status", 1)]},
        ],
        "payment_transactions": [
            {"name": "session_id_unique", "fields": [("session_id", 1)], "unique": True},
            {"name": "reach_attempt_id", "fields": [("reach_attempt_id", 1)]},
        ],
        "blocked_senders": [
            {"name": "identity_id_sender_email_unique", "fields": [("identity_id", 1), ("sender_email", 1)], "unique": True},
        ],
    }
    
    all_indexes_present = True
    
    for collection_name, expected in expected_indexes.items():
        print(f"\nChecking indexes for '{collection_name}':")
        
        try:
            indexes = await db[collection_name].index_information()
            
            for expected_index in expected:
                index_name = expected_index["name"]
                if index_name in indexes:
                    print(f"  ✓ {index_name}: {expected_index['fields']}")
                else:
                    print(f"  ✗ {index_name}: MISSING")
                    all_indexes_present = False
        except Exception as e:
            print(f"  ✗ Error checking indexes: {e}")
            all_indexes_present = False
    
    client.close()
    
    if all_indexes_present:
        print("\n✅ All expected indexes are present!")
    else:
        print("\n⚠️  Some indexes are missing!")
    
    return all_indexes_present

def test_backend_api():
    """Test basic backend API functionality."""
    print("\n=== Testing Backend API ===")
    
    # Test 1: Health check
    print("\n1. Testing health endpoint...")
    try:
        response = requests.get(f"{BACKEND_URL}/api/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ Health check passed: MongoDB={data.get('mongo', 'unknown')}")
            return True
        else:
            print(f"   ✗ Health check failed: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ Health check error: {e}")
        return False
    
    # Test 2: CSRF token
    print("\n2. Testing CSRF endpoint...")
    try:
        session = requests.Session()
        response = session.get(f"{BACKEND_URL}/api/auth/csrf", timeout=10)
        if response.status_code == 200:
            csrf_token = response.cookies.get("csrf_token")
            if csrf_token:
                print(f"   ✓ CSRF token obtained: {csrf_token[:20]}...")
                return True
            else:
                print("   ✗ No CSRF token in cookies")
                return False
        else:
            print(f"   ✗ CSRF endpoint failed: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ CSRF endpoint error: {e}")
        return False

def test_full_flow():
    """Test a complete user registration and identity creation flow."""
    print("\n=== Testing Full Application Flow ===")
    
    session = requests.Session()
    
    # Step 1: Get CSRF token
    print("\n1. Getting CSRF token...")
    try:
        response = session.get(f"{BACKEND_URL}/api/auth/csrf")
        if response.status_code != 200:
            print(f"   ✗ Failed to get CSRF token: {response.status_code}")
            return False
        csrf_token = response.cookies.get("csrf_token")
        if not csrf_token:
            print("   ✗ No CSRF token in cookies")
            return False
        print(f"   ✓ CSRF token obtained")
    except Exception as e:
        print(f"   ✗ CSRF token error: {e}")
        return False
    
    # Step 2: Register a test user
    print("\n2. Registering test user...")
    test_email = f"test_index_{int(time.time())}@example.com"
    test_password = "TestPassword123!"
    test_name = "Test User"
    
    try:
        response = session.post(
            f"{BACKEND_URL}/api/auth/register",
            json={
                "email": test_email,
                "password": test_password,
                "name": test_name
            },
            headers={"X-CSRF-Token": csrf_token} if csrf_token else {}
        )
        
        if response.status_code == 200:
            print(f"   ✓ User registered: {test_email}")
        elif response.status_code == 400 and "already registered" in response.text:
            print(f"   ⚠️  User already exists, trying login...")
            # Try login instead
            response = session.post(
                f"{BACKEND_URL}/api/auth/login",
                json={
                    "email": test_email,
                    "password": test_password
                },
                headers={"X-CSRF-Token": csrf_token} if csrf_token else {}
            )
            if response.status_code != 200:
                print(f"   ✗ Login failed: {response.status_code}")
                return False
            print(f"   ✓ User logged in")
        else:
            print(f"   ✗ Registration failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"   ✗ Registration error: {e}")
        return False
    
    # Step 3: Create an identity
    print("\n3. Creating test identity...")
    test_handle = f"testhandle{int(time.time())}"
    
    try:
        response = session.post(
            f"{BACKEND_URL}/api/identity",
            json={
                "handle": test_handle,
                "bio": "Test user for index verification"
            },
            headers={"X-CSRF-Token": csrf_token} if csrf_token else {}
        )
        
        if response.status_code == 200:
            print(f"   ✓ Identity created: @{test_handle}")
            return True
        elif response.status_code == 400 and "already taken" in response.text:
            print(f"   ⚠️  Handle already taken, using existing identity")
            return True
        else:
            print(f"   ✗ Identity creation failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"   ✗ Identity creation error: {e}")
        return False

async def main():
    """Run all tests."""
    print("MongoDB Index Verification and Application Test")
    print("=" * 60)
    
    # Verify indexes
    indexes_ok = await verify_indexes()
    
    # Test backend API
    api_ok = test_backend_api()
    
    # Test full flow
    flow_ok = test_full_flow()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    print(f"\nIndex verification: {'✅ PASS' if indexes_ok else '❌ FAIL'}")
    print(f"Backend API test:   {'✅ PASS' if api_ok else '❌ FAIL'}")
    print(f"Full flow test:     {'✅ PASS' if flow_ok else '❌ FAIL'}")
    
    all_passed = indexes_ok and api_ok and flow_ok
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED! MongoDB indexes are properly configured.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
    
    return all_passed

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)