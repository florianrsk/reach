#!/usr/bin/env python3
"""
Quick test for Face creation
"""

import requests
import time

BASE_URL = "http://localhost:8001"

# Create user
email = f"quick_{int(time.time())}@example.com"
password = "Testpassword123!Long"

print("1. Creating user...")
response = requests.post(
    f"{BASE_URL}/api/auth/register",
    json={"email": email, "password": password, "name": "Quick Test"},
)
print(f"   Status: {response.status_code}")

# Login
print("2. Logging in...")
session = requests.Session()
response = session.post(
    f"{BASE_URL}/api/auth/login", json={"email": email, "password": password}
)
print(f"   Status: {response.status_code}")

# Create Face
handle = f"quicktest{int(time.time())}"
print(f"3. Creating Face: {handle}")
response = session.post(
    f"{BASE_URL}/api/identity",
    json={
        "handle": handle,
        "display_name": "Quick Test",
        "headline": "Quick test",
        "current_focus": "Testing quickly",
        "availability_signal": "Testing",
        "prompt": "Test",
        "photo_url": None,
        "links": [],
    },
)
print(f"   Status: {response.status_code}")
print(f"   Response: {response.text[:200]}")

# Wait a moment
print("4. Waiting 2 seconds...")
time.sleep(2)

# Test public page
print(f"5. Testing public page: /reach/{handle}")
for i in range(3):
    response = requests.get(f"{BASE_URL}/reach/{handle}")
    print(f"   Attempt {i + 1}: {response.status_code}")
    if response.status_code == 200:
        print(f"   Success! {response.text[:100]}")
        break
    time.sleep(1)
else:
    print("   Failed after 3 attempts")

# Test with lowercase
print(f"6. Testing with lowercase: /reach/{handle.lower()}")
response = requests.get(f"{BASE_URL}/reach/{handle.lower()}")
print(f"   Status: {response.status_code}")
