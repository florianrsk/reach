#!/usr/bin/env python3
"""
Test Face creation bug
"""

import requests
import json
import time

BASE_URL = "http://localhost:8001"
TEST_EMAIL = f"test_face_{int(time.time())}@example.com"
TEST_PASSWORD = "Testpassword123!Long"


def test_face_creation():
    print("Testing Face creation...")

    # 1. Create user
    print("1. Creating test user...")
    user_data = {"email": TEST_EMAIL, "password": TEST_PASSWORD, "name": "Test User"}

    try:
        response = requests.post(f"{BASE_URL}/api/auth/register", json=user_data)
        print(f"   Register: {response.status_code}")
        if response.status_code != 200:
            print(f"   Error: {response.text}")
            return False
    except Exception as e:
        print(f"   Exception: {e}")
        return False

    # 2. Login
    print("2. Logging in...")
    login_data = {"email": TEST_EMAIL, "password": TEST_PASSWORD}
    try:
        # Create a session to handle cookies
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json=login_data)
        print(f"   Login: {response.status_code}")
        if response.status_code != 200:
            print(f"   Error: {response.text}")
            return False

        login_json = response.json()
        print(f"   Login response keys: {list(login_json.keys())}")

        # Check for cookies
        cookies = session.cookies.get_dict()
        print(f"   Cookies: {cookies}")

        # Use the session for subsequent requests
        # The auth is handled via cookies, not Authorization header
        return session, login_json.get("csrf_token", "")

    except Exception as e:
        print(f"   Exception: {e}")
        return False, ""

    # 3. Create Face
    print("3. Creating Face...")
    face_data = {
        "handle": f"testuser{int(time.time())}",
        "display_name": "Test User",
        "headline": "Software Developer",
        "current_focus": "Testing Reach",
        "availability_signal": "I check this daily",
        "prompt": "What brings you here?",
        "photo_url": "https://example.com/photo.jpg",
        "links": [
            {"label": "GitHub", "url": "https://github.com/test"},
            {"label": "Twitter", "url": "https://twitter.com/test"},
        ],
        "modules_config": {
            "challenge_question": {"enabled": False},
            "time_signal": {"enabled": True},
            "waiting_period": {"enabled": False},
            "deposit": {"enabled": False},
            "intent_categories": {
                "enabled": True,
                "categories": ["Collaboration", "Question", "Feedback"],
            },
        },
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/identity", json=face_data, headers=headers
        )
        print(f"   Face creation: {response.status_code}")
        if response.status_code != 201:
            print(f"   Error: {response.text}")
            return False

        face_response = response.json()
        print(f"   Face created: {face_response.get('handle')}")
        print(f"   Face completed: {face_response.get('face_completed', False)}")

        # Check if face_completed is True
        if not face_response.get("face_completed", False):
            print("   ERROR: face_completed is not True!")
            return False

    except Exception as e:
        print(f"   Exception: {e}")
        return False

    # 4. Test public reach page
    print("4. Testing public reach page...")
    handle = face_data["handle"]
    try:
        response = requests.get(f"{BASE_URL}/reach/{handle}")
        print(f"   Public page: {response.status_code}")
        if response.status_code != 200:
            print(f"   Error: {response.text}")
            return False

        public_data = response.json()
        print(f"   Display name: {public_data.get('identity', {}).get('display_name')}")
        print(
            f"   Face completed in response: {public_data.get('identity', {}).get('face_completed', False)}"
        )

    except Exception as e:
        print(f"   Exception: {e}")
        return False

    # 5. Test message submission
    print("5. Testing message submission...")
    message_data = {
        "message": "Hello! This is a test message for the Face system.",
        "time_requirement": "Just a read",
        "intent_category": "Test",
    }

    try:
        response = requests.post(
            f"{BASE_URL}/reach/{handle}/message", json=message_data
        )
        print(f"   Message submission: {response.status_code}")
        if response.status_code != 200:
            print(f"   Error: {response.text}")
            return False

        print(f"   Message ID: {response.json().get('message_id')}")

    except Exception as e:
        print(f"   Exception: {e}")
        return False

    print("\n[OK] Face creation test PASSED!")
    print(f"Test user: {TEST_EMAIL}")
    print(f"Test handle: {handle}")
    return True


if __name__ == "__main__":
    try:
        success = test_face_creation()
        if not success:
            print("\n[FAIL] Face creation test FAILED!")
            exit(1)
    except KeyboardInterrupt:
        print("\nTest interrupted")
        exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback

        traceback.print_exc()
        exit(1)
