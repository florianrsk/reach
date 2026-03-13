#!/usr/bin/env python3
"""
Test script to verify Face creation functionality
"""

import requests
import json
import time

BASE_URL = "http://localhost:8001"


def test_face_creation():
    """Test the new Face-based identity creation"""
    print("Testing Face creation...")

    # Get CSRF token first
    session = requests.Session()

    try:
        # Get CSRF token
        csrf_response = session.get(f"{BASE_URL}/api/auth/csrf")
        csrf_token = csrf_response.cookies.get("csrf_token")
        print(f"CSRF token: {csrf_token[:20]}...")

        # Create a unique handle
        test_handle = f"testface{int(time.time())}"

        # Create Face-based identity
        face_data = {
            "handle": test_handle,
            "display_name": "Test Face User",
            "headline": "Software developer testing the new Face system",
            "current_focus": "Currently working on testing the Face creation flow for the Reach product rebuild",
            "availability_signal": "I check this handle daily and respond to all thoughtful messages",
            "prompt": "What are you working on and why did you think of me?",
            "photo_url": None,
            "links": [
                {"label": "My Work", "url": "https://example.com/work"},
                {"label": "GitHub", "url": "https://github.com/test"},
            ],
        }

        headers = {}
        if csrf_token:
            headers["X-CSRF-Token"] = csrf_token

        response = session.post(
            f"{BASE_URL}/api/identity", json=face_data, headers=headers
        )

        print(f"Response status: {response.status_code}")

        if response.status_code == 200:
            identity = response.json()
            print("\n✅ Face created successfully!")
            print(f"Handle: {identity.get('handle')}")
            print(f"Display Name: {identity.get('display_name')}")
            print(f"Headline: {identity.get('headline')}")
            print(f"Face Completed: {identity.get('face_completed')}")
            print(f"Prompt: {identity.get('prompt')}")
            print(f"Links: {identity.get('links')}")

            # Verify all Face fields are present
            required_fields = [
                "display_name",
                "headline",
                "current_focus",
                "availability_signal",
                "prompt",
                "face_completed",
            ]

            missing_fields = []
            for field in required_fields:
                if field not in identity:
                    missing_fields.append(field)

            if missing_fields:
                print(f"\n❌ Missing fields: {missing_fields}")
                return False
            else:
                print("\n✅ All Face fields present!")
                return True
        else:
            print(f"❌ Failed to create Face: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_face_validation():
    """Test Face field validation"""
    print("\n\nTesting Face validation...")

    session = requests.Session()

    try:
        # Get CSRF token
        csrf_response = session.get(f"{BASE_URL}/api/auth/csrf")
        csrf_token = csrf_response.cookies.get("csrf_token")

        # Test 1: Missing required field
        test_handle = f"testval{int(time.time())}"
        invalid_face = {
            "handle": test_handle,
            "display_name": "Test",
            "headline": "Too short",  # Should fail - needs 10+ chars
            "current_focus": "Short",  # Should fail - needs 20+ chars
            "availability_signal": "Short",  # Should fail - needs 10+ chars
            "prompt": "Short",  # Should fail - needs 10+ chars
            "photo_url": None,
            "links": None,
        }

        headers = {}
        if csrf_token:
            headers["X-CSRF-Token"] = csrf_token

        response = session.post(
            f"{BASE_URL}/api/identity", json=invalid_face, headers=headers
        )

        print(f"Validation test response: {response.status_code}")
        if response.status_code != 200:
            print("✅ Validation working correctly (rejected invalid data)")
        else:
            print("❌ Validation failed (accepted invalid data)")
            return False

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("FACE CREATION TEST SUITE")
    print("=" * 60)

    success1 = test_face_creation()
    success2 = test_face_validation()

    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)

    if success1 and success2:
        print("✅ All Face tests passed!")
    else:
        print("❌ Some Face tests failed")

    print("\nNote: This test doesn't create a real user account,")
    print("so it will fail if user authentication is required.")
    print("Run the full test suite with: python final_test.py")
