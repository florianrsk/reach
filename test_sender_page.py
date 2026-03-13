#!/usr/bin/env python3
"""
Test script to verify sender page functionality
"""

import requests
import json
import time

BASE_URL = "http://localhost:8001"


def test_sender_page():
    """Test the new Face-based sender page"""
    print("Testing sender page...")

    session = requests.Session()

    try:
        # First, create a test user and identity
        print("1. Creating test user and Face...")

        # Get CSRF token
        csrf_response = session.get(f"{BASE_URL}/api/auth/csrf")
        csrf_token = csrf_response.cookies.get("csrf_token")

        # Register a test user
        test_email = f"test_sender_{int(time.time())}@example.com"
        register_data = {
            "email": test_email,
            "password": "SecurePass123!@#",
            "name": "Test Sender User",
        }

        headers = {}
        if csrf_token:
            headers["X-CSRF-Token"] = csrf_token

        register_response = session.post(
            f"{BASE_URL}/api/auth/register", json=register_data, headers=headers
        )

        if register_response.status_code != 200:
            print(f"Failed to register user: {register_response.status_code}")
            return False

        print("User registered")

        # Login to get session
        login_response = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": test_email, "password": "SecurePass123!@#"},
            headers=headers,
        )

        if login_response.status_code != 200:
            print(f"Failed to login: {login_response.status_code}")
            return False

        print("User logged in")

        # Create a Face-based identity
        test_handle = f"testsender{int(time.time())}"
        face_data = {
            "handle": test_handle,
            "display_name": "Test Sender Page",
            "headline": "Testing the new sender page experience",
            "current_focus": "Currently testing the Face-based sender page for Reach product rebuild",
            "availability_signal": "I check this handle daily and respond to thoughtful messages",
            "prompt": "What would you like to tell me?",
            "photo_url": None,
            "links": [{"label": "GitHub", "url": "https://github.com/test"}],
        }

        identity_response = session.post(
            f"{BASE_URL}/api/identity", json=face_data, headers=headers
        )

        if identity_response.status_code != 200:
            print(f"FAIL: Failed to create Face: {identity_response.status_code}")
            print(f"Response: {identity_response.text}")
            return False

        print("PASS: Face created")

        # Test 1: Public reach page should return Face data
        print("\n2. Testing public reach page...")
        public_response = session.get(f"{BASE_URL}/api/reach/{test_handle}")

        if public_response.status_code == 200:
            face_data = public_response.json()
            identity = face_data.get("identity", {})

            print(f"PASS: Public page loaded successfully")
            print(f"   Display Name: {identity.get('display_name')}")
            print(f"   Headline: {identity.get('headline')}")
            print(f"   Current Focus: {identity.get('current_focus')[:50]}...")
            print(f"   Prompt: {identity.get('prompt')}")
            print(f"   Face Completed: {identity.get('face_completed')}")

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
                print(f"FAIL: Missing fields: {missing_fields}")
                return False
            else:
                print("PASS: All Face fields present in public response")
        else:
            print(f"FAIL: Failed to load public page: {public_response.status_code}")
            print(f"Response: {public_response.text}")
            return False

        # Test 2: Submit a reach attempt
        print("\n3. Testing reach attempt submission...")
        attempt_data = {
            "message": "This is a test message for the new Face-based sender page. I'm testing the submission flow."
        }

        # Need new CSRF token for POST
        csrf_response = session.get(f"{BASE_URL}/api/auth/csrf")
        csrf_token = csrf_response.cookies.get("csrf_token")
        if csrf_token:
            headers["X-CSRF-Token"] = csrf_token

        submit_response = session.post(
            f"{BASE_URL}/api/reach/{test_handle}/submit",
            json=attempt_data,
            headers=headers,
        )

        if submit_response.status_code == 200:
            result = submit_response.json()
            print(f"PASS: Reach attempt submitted successfully")
            print(f"   Attempt ID: {result.get('attempt_id')}")
            print(f"   Message: {result.get('message')}")
            print(f"   Confirmation: {result.get('confirmation')}")
        else:
            print(f"FAIL: Failed to submit reach attempt: {submit_response.status_code}")
            print(f"Response: {submit_response.text}")
            return False

        # Test 3: Non-existent handle should 404
        print("\n4. Testing non-existent handle...")
        fake_response = session.get(f"{BASE_URL}/api/reach/nonexistenthandle123")

        if fake_response.status_code == 404:
            print("PASS: Non-existent handle correctly returns 404")
        else:
            print(
                f"FAIL: Non-existent handle returned {fake_response.status_code}, expected 404"
            )
            return False

        print("\n" + "=" * 60)
        print("PASS: ALL SENDER PAGE TESTS PASSED!")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"FAIL: Error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("SENDER PAGE TEST SUITE")
    print("=" * 60)

    success = test_sender_page()

    if success:
        print("\nPASS: Sender page implementation is working correctly!")
    else:
        print("\nFAIL: Sender page tests failed")

    print("\nNote: This creates a real user account and Face.")
    print("The test data will remain in the database.")
