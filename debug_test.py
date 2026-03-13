#!/usr/bin/env python3
"""
Debug script to test identity creation
"""

import requests
import time
import json


def test_identity_creation():
    print("Testing identity creation endpoint...")

    # Create a session
    s = requests.Session()

    # Step 1: Get CSRF token
    print("\n1. Getting CSRF token...")
    try:
        resp = s.get("http://localhost:8000/api/auth/csrf")
        print(f"   Status: {resp.status_code}")
        csrf_token = s.cookies.get("csrf_token")
        print(f"   CSRF token in cookies: {'csrf_token' in s.cookies}")
        print(f"   CSRF token value: {csrf_token[:20] if csrf_token else 'None'}...")
    except Exception as e:
        print(f"   Error: {e}")
        return

    # Step 2: Register a user
    print("\n2. Registering user...")
    email = f"test_{int(time.time())}@example.com"
    password = "TestPassword123!"
    try:
        resp = s.post(
            "http://localhost:8000/api/auth/register",
            json={"email": email, "password": password, "name": "Test User"},
            headers={"X-CSRF-Token": csrf_token} if csrf_token else {},
        )
        print(f"   Status: {resp.status_code}")
        print(f"   Response: {resp.text[:200]}")
        print(f"   Cookies after register: {list(s.cookies.keys())}")
    except Exception as e:
        print(f"   Error: {e}")
        return

    # Step 3: Login
    print("\n3. Logging in...")
    try:
        resp = s.post(
            "http://localhost:8000/api/auth/login",
            json={"email": email, "password": password},
            headers={"X-CSRF-Token": csrf_token} if csrf_token else {},
        )
        print(f"   Status: {resp.status_code}")
        print(f"   Response: {resp.text[:200]}")
        print(f"   Cookies after login: {list(s.cookies.keys())}")
        for cookie in s.cookies:
            print(f"     {cookie.name}: {cookie.value[:50]}...")
    except Exception as e:
        print(f"   Error: {e}")
        return

    # Step 4: Test /auth/me endpoint to verify authentication
    print("\n4. Testing /auth/me endpoint...")
    try:
        resp = s.get("http://localhost:8000/api/auth/me")
        print(f"   Status: {resp.status_code}")
        print(f"   Response: {resp.text[:200]}")
    except Exception as e:
        print(f"   Error: {e}")
        return

    # Step 5: Create identity
    print("\n5. Creating identity...")
    handle = f"testuser{int(time.time())}"
    try:
        resp = s.post(
            "http://localhost:8000/api/identity",
            json={
                "handle": handle,
                "bio": "Test bio",
                "type": "person",  # Explicitly include type
            },
            headers={"X-CSRF-Token": csrf_token} if csrf_token else {},
        )
        print(f"   Status: {resp.status_code}")
        print(f"   Response: {resp.text}")
        if resp.status_code != 200:
            print(f"   Error details: {resp.text}")
    except Exception as e:
        print(f"   Error: {e}")
        import traceback

        traceback.print_exc()
        return

    print("\n" + "=" * 60)
    if resp.status_code == 200:
        print("✅ Identity creation successful!")
    else:
        print("❌ Identity creation failed")


if __name__ == "__main__":
    test_identity_creation()
