#!/usr/bin/env python3
"""
Test Face creation with proper field lengths
"""

import requests
import time

BASE_URL = "http://localhost:8001"

print("Testing Face creation with proper validation...")

# Create session and login
session = requests.Session()

# Register and login
email = f"face_test_{int(time.time())}@example.com"
password = "TestPassword123!LongEnough"
name = "Face Test User"

print(f"\n1. Creating user: {email}")
register_data = {"email": email, "password": password, "name": name}

response = session.post(f"{BASE_URL}/api/auth/register", json=register_data)
if response.status_code != 200:
    print(f"   Registration failed: {response.status_code} - {response.text}")
    exit(1)

print("2. Logging in...")
login_data = {"email": email, "password": password}
response = session.post(f"{BASE_URL}/api/auth/login", json=login_data)
if response.status_code != 200:
    print(f"   Login failed: {response.status_code} - {response.text}")
    exit(1)

print("3. Creating Face...")
handle = f"facetest{int(time.time())}"

# Based on validation errors from earlier:
# - headline: min 10 chars, max 100 chars
# - current_focus: min 20 chars, max 300 chars
# - availability_signal: min 10 chars, max 200 chars
# - prompt: min 10 chars, max 200 chars

face_data = {
    "handle": handle,
    "display_name": "Face Test User Display Name",
    "headline": "Software Developer with backend systems and API design experience",
    "current_focus": "Currently focused on building scalable microservices architecture and improving system reliability through comprehensive testing and monitoring. This text is definitely more than 20 characters long.",
    "availability_signal": "I check my messages daily and typically respond within 24 hours for urgent matters. Regular updates weekly.",
    "prompt": "What brings you to my page today? Please share what you're working on and how I might be able to help or collaborate.",
    "photo_url": "https://example.com/profile.jpg",
    "links": [
        {"label": "GitHub", "url": "https://github.com/testuser"},
        {"label": "LinkedIn", "url": "https://linkedin.com/in/testuser"},
    ],
}

print(f"   Handle: {handle}")
print(f"   Headline length: {len(face_data['headline'])}")
print(f"   Current focus length: {len(face_data['current_focus'])}")
print(f"   Availability signal length: {len(face_data['availability_signal'])}")
print(f"   Prompt length: {len(face_data['prompt'])}")

response = session.post(f"{BASE_URL}/api/identity", json=face_data)
print(f"   Response status: {response.status_code}")

if response.status_code == 200 or response.status_code == 201:
    face_response = response.json()
    print(f"\n   SUCCESS: Face created!")
    print(f"   Face ID: {face_response.get('id')}")
    print(f"   Face handle: {face_response.get('handle')}")
    print(f"   Face completed: {face_response.get('face_completed')}")

    if "modules_config" in face_response:
        print(f"   Modules config: {list(face_response['modules_config'].keys())}")
    else:
        print(f"   Warning: No modules_config in response")

    # Test public page
    print(f"\n4. Testing public Face page at /reach/{handle}")
    response = requests.get(f"{BASE_URL}/reach/{handle}")
    print(f"   Public page status: {response.status_code}")

    if response.status_code == 200:
        public_data = response.json()
        print(
            f"   Public page loaded: {public_data.get('identity', {}).get('display_name')}"
        )
        if "modules" in public_data:
            print(
                f"   Modules in public response: {list(public_data['modules'].keys())}"
            )
    else:
        print(f"   Public page error: {response.text[:200]}")

else:
    print(f"\n   ERROR: Face creation failed")
    print(f"   Response: {response.text}")

    # Try to parse validation errors
    if response.status_code == 422:
        try:
            errors = response.json()
            print(f"   Validation errors:")
            for error in errors.get("detail", []):
                print(f"     - {error.get('loc')}: {error.get('msg')}")
        except:
            pass

print("\n" + "=" * 60)
print("Face creation test complete!")
print("=" * 60)
