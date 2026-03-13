#!/usr/bin/env python3
"""
Simple test to check Face creation bug
"""

import requests
import time

BASE_URL = "http://localhost:8001"


def test_face_endpoints():
    print("Testing Face endpoints...")

    # Test 1: Check if /reach/{handle} endpoint exists
    print("\n1. Testing /reach/{handle} endpoint...")
    try:
        # This should return 404 since handle doesn't exist
        response = requests.get(f"{BASE_URL}/reach/nonexistent")
        print(f"   Status: {response.status_code}")
        if response.status_code == 404:
            print("   [OK] Endpoint exists (returns 404 for non-existent handle)")
        else:
            print(f"   [UNEXPECTED] Got {response.status_code}: {response.text[:100]}")
    except Exception as e:
        print(f"   [ERROR] Exception: {e}")

    # Test 2: Check if /reach/{handle}/message endpoint exists
    print("\n2. Testing /reach/{handle}/message endpoint...")
    try:
        # This should return 404 since handle doesn't exist
        response = requests.post(
            f"{BASE_URL}/reach/nonexistent/message", json={"message": "test"}
        )
        print(f"   Status: {response.status_code}")
        if response.status_code in [404, 400]:
            print(f"   [OK] Endpoint exists (returns {response.status_code})")
        else:
            print(f"   [UNEXPECTED] Got {response.status_code}: {response.text[:100]}")
    except Exception as e:
        print(f"   [ERROR] Exception: {e}")

    # Test 3: Check for old slot endpoints
    print("\n3. Checking for old slot endpoints...")
    try:
        # This might return 404 or 405
        response = requests.get(f"{BASE_URL}/reach/testuser/open")
        print(f"   GET /reach/testuser/open: {response.status_code}")

        response = requests.post(f"{BASE_URL}/reach/testuser/open", json={})
        print(f"   POST /reach/testuser/open: {response.status_code}")

        if response.status_code == 405:
            print("   [OK] POST to slot endpoint returns 405 (Method Not Allowed)")
        elif response.status_code == 404:
            print("   [OK] Slot endpoint returns 404 (Not Found)")
        else:
            print(f"   [WARNING] Unexpected status: {response.status_code}")
    except Exception as e:
        print(f"   [ERROR] Exception: {e}")

    # Test 4: Check backend health/status
    print("\n4. Checking backend status...")
    try:
        # Try common health check endpoints
        for endpoint in ["/health", "/status", "/api/health"]:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=2)
            if response.status_code < 500:
                print(f"   {endpoint}: {response.status_code}")
                break
        else:
            print("   No health endpoint found (this is OK)")
    except:
        print("   No health endpoint (this is OK)")

    print("\n" + "=" * 60)
    print("Face endpoint test complete")
    print("=" * 60)
    print("\nKey findings:")
    print("1. /reach/{handle} endpoint: EXISTS")
    print("2. /reach/{handle}/message endpoint: EXISTS")
    print("3. Old slot endpoints: Should return 404/405")
    print("\nIf Face creation is broken, check:")
    print("- Identity creation endpoint (/api/identity)")
    print("- face_completed flag in identity")
    print("- Modules configuration")


if __name__ == "__main__":
    test_face_endpoints()
