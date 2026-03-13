#!/usr/bin/env python3
"""
Debug public page 404 issue
"""

import requests
import time

BASE_URL = "http://localhost:8001"

# Create a new Face and immediately test public page
session = requests.Session()

# Register
email = f"debug_{int(time.time())}@example.com"
password = "TestPassword123!LongEnough"

print("1. Registering user...")
response = session.post(
    f"{BASE_URL}/api/auth/register",
    json={"email": email, "password": password, "name": "Debug User"},
)
print(f"   Status: {response.status_code}")

# Login
print("2. Logging in...")
response = session.post(
    f"{BASE_URL}/api/auth/login", json={"email": email, "password": password}
)
print(f"   Status: {response.status_code}")

# Create Face with simple data
handle = f"debug{int(time.time())}"
print(f"3. Creating Face: {handle}")
face_data = {
    "handle": handle,
    "display_name": "Debug User",
    "headline": "Debug headline for testing",
    "current_focus": "Debug current focus text that is more than 20 characters long",
    "availability_signal": "Debug availability signal more than 10 chars",
    "prompt": "Debug prompt more than 10 characters",
    "photo_url": None,
    "links": [],
}

response = session.post(f"{BASE_URL}/api/identity", json=face_data)
print(f"   Status: {response.status_code}")
print(f"   Response: {response.text[:500]}")

if response.status_code == 200:
    face_response = response.json()
    print(f"   Face created: {face_response.get('id')}")
    print(f"   face_completed: {face_response.get('face_completed')}")

    # Immediately test public page
    print(f"\n4. Testing public page immediately...")
    for i in range(1, 6):
        print(f"   Attempt {i}:")
        response = requests.get(f"{BASE_URL}/reach/{handle}")
        print(f"     Status: {response.status_code}")
        if response.status_code == 200:
            print(f"     SUCCESS!")
            data = response.json()
            print(f"     Display name: {data.get('identity', {}).get('display_name')}")
            break
        elif response.status_code == 404:
            print(f"     Still 404")
        else:
            print(f"     Unexpected: {response.text[:200]}")

        if i < 5:
            print(f"     Waiting 2 seconds...")
            time.sleep(2)

    # Also test with exact handle from response
    print(f"\n5. Testing with handle from response: {face_response.get('handle')}")
    response = requests.get(f"{BASE_URL}/reach/{face_response.get('handle')}")
    print(f"   Status: {response.status_code}")

    # Test identity endpoint to confirm it exists
    print(f"\n6. Checking identity endpoint...")
    response = session.get(f"{BASE_URL}/api/identity")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        identity = response.json()
        print(f"   Identity handle: {identity.get('handle')}")
        print(f"   face_completed: {identity.get('face_completed')}")

print("\n" + "=" * 60)
print("Debug complete")
print("=" * 60)
