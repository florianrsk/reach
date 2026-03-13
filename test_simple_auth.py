#!/usr/bin/env python3
"""
Simple auth test to debug the 401 login issue
"""

import requests
import time

BASE_URL = "http://localhost:8001"

print("Testing auth endpoints...")

# Test 1: Check if backend is accessible
print("\n1. Testing backend connection...")
try:
    response = requests.get(BASE_URL, timeout=5)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text[:100]}")
except Exception as e:
    print(f"   Error: {e}")
    exit(1)

# Test 2: Register a user
print("\n2. Testing user registration...")
email = f"test_auth_{int(time.time())}@example.com"
password = "TestPassword123!LongEnough"
name = "Test Auth User"

register_data = {"email": email, "password": password, "name": name}

try:
    response = requests.post(
        f"{BASE_URL}/api/auth/register", json=register_data, timeout=10
    )
    print(f"   Status: {response.status_code}")
    print(f"   Response headers: {dict(response.headers)}")
    print(f"   Response body: {response.text[:500]}")

    if response.status_code != 200:
        print(f"   ERROR: Registration failed with {response.status_code}")
        # Try to parse error
        try:
            error_data = response.json()
            print(f"   Error details: {error_data}")
        except:
            pass
        exit(1)

except Exception as e:
    print(f"   Exception: {e}")
    import traceback

    traceback.print_exc()
    exit(1)

# Test 3: Login
print("\n3. Testing login...")
login_data = {"email": email, "password": password}

try:
    # Create a session to track cookies
    session = requests.Session()
    response = session.post(f"{BASE_URL}/api/auth/login", json=login_data, timeout=10)
    print(f"   Status: {response.status_code}")
    print(f"   Response headers: {dict(response.headers)}")
    print(f"   Response body: {response.text[:500]}")
    print(f"   Cookies: {session.cookies.get_dict()}")

    if response.status_code != 200:
        print(f"   ERROR: Login failed with {response.status_code}")
        exit(1)

    # Parse response
    try:
        login_response = response.json()
        print(f"   Login response keys: {list(login_response.keys())}")
    except:
        print(f"   Could not parse JSON response")

except Exception as e:
    print(f"   Exception: {e}")
    import traceback

    traceback.print_exc()
    exit(1)

# Test 4: Check /api/auth/me
print("\n4. Testing /api/auth/me endpoint...")
try:
    response = session.get(f"{BASE_URL}/api/auth/me", timeout=10)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text[:500]}")

    if response.status_code == 200:
        print(f"   SUCCESS: Session works!")
        user_data = response.json()
        print(f"   User email: {user_data.get('email')}")
        print(f"   User ID: {user_data.get('id')}")
    else:
        print(f"   ERROR: /api/auth/me failed with {response.status_code}")

except Exception as e:
    print(f"   Exception: {e}")
    import traceback

    traceback.print_exc()
    exit(1)

print("\n" + "=" * 60)
print("Auth test complete!")
print(f"Test user: {email}")
print("=" * 60)
