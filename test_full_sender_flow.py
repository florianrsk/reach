#!/usr/bin/env python3
"""
Test the full sender page flow with a Face-completed identity
"""

import requests
import time
import json

BASE_URL = "http://localhost:8000"


def test_full_flow():
    """Test creating a Face and accessing the sender page"""
    print("Testing full sender page flow...")

    session = requests.Session()

    try:
        # 1. Register and login
        print("1. Creating test user...")
        csrf_response = session.get(f"{BASE_URL}/api/auth/csrf")
        csrf_token = csrf_response.cookies.get("csrf_token")

        test_email = f"fulltest_{int(time.time())}@example.com"
        headers = {"X-CSRF-Token": csrf_token} if csrf_token else {}

        # Register
        session.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "email": test_email,
                "password": "SecurePass123!@#",
                "name": "Full Test User",
            },
            headers=headers,
        )

        # Login
        session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": test_email, "password": "SecurePass123!@#"},
            headers=headers,
        )

        print("   User created and logged in")

        # 2. Create a Face-completed identity
        print("2. Creating Face-completed identity...")
        test_handle = f"fulltest{int(time.time())}"

        face_data = {
            "handle": test_handle,
            "display_name": "Alex Johnson",
            "headline": "Product designer building human-centered tools",
            "current_focus": "Redesigning how people connect online without the noise of traditional communication channels",
            "availability_signal": "I check reach requests every Tuesday and Friday",
            "prompt": "What's on your mind and how can I help?",
            "photo_url": "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=400&h=400&fit=crop",
            "links": [
                {"label": "Portfolio", "url": "https://alexjohnson.design"},
                {"label": "Writing", "url": "https://blog.alexjohnson.design"},
            ],
        }

        response = session.post(
            f"{BASE_URL}/api/identity", json=face_data, headers=headers
        )

        if response.status_code != 200:
            print(f"   FAIL: Failed to create Face: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

        print(f"   Face created: {test_handle}")

        # 3. Test public sender page
        print("3. Testing public sender page...")
        public_response = session.get(f"{BASE_URL}/api/reach/{test_handle}")

        if public_response.status_code != 200:
            print(f"   FAIL: Public page failed: {public_response.status_code}")
            print(f"   Response: {public_response.text}")
            return False

        face_data = public_response.json()
        identity = face_data.get("identity", {})

        print(f"   SUCCESS: Public page loaded")
        print(f"   Display Name: {identity.get('display_name')}")
        print(f"   Headline: {identity.get('headline')}")
        print(f"   Current Focus: {identity.get('current_focus')[:60]}...")
        print(f"   Availability: {identity.get('availability_signal')}")
        print(f"   Prompt: {identity.get('prompt')}")
        print(f"   Photo URL: {'Yes' if identity.get('photo_url') else 'No'}")
        print(f"   Links: {len(identity.get('links', []))}")

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
            print(f"   FAIL: Missing fields: {missing_fields}")
            return False

        # 4. Test submitting a reach attempt
        print("4. Testing reach attempt submission...")

        # Get fresh CSRF token
        csrf_response = session.get(f"{BASE_URL}/api/auth/csrf")
        csrf_token = csrf_response.cookies.get("csrf_token")
        headers = {"X-CSRF-Token": csrf_token} if csrf_token else {}

        attempt_data = {
            "message": "Hi Alex, I came across your work on human-centered design and was really impressed. I'm working on a similar project focused on reducing notification fatigue in team collaboration tools. Would you be open to a brief conversation about your approach to designing for attention?"
        }

        submit_response = session.post(
            f"{BASE_URL}/api/reach/{test_handle}/message",
            json=attempt_data,
            headers=headers,
        )

        if submit_response.status_code == 200:
            result = submit_response.json()
            print(f"   SUCCESS: Reach attempt submitted")
            print(f"   Attempt ID: {result.get('attempt_id')}")
            print(f"   Message: {result.get('message')}")
        else:
            print(f"   FAIL: Submission failed: {submit_response.status_code}")
            print(f"   Response: {submit_response.text}")
            return False

        # 5. Test error cases
        print("5. Testing error cases...")

        # Non-existent handle
        fake_response = session.get(f"{BASE_URL}/api/reach/nonexistent123456")
        if fake_response.status_code == 404:
            print("   SUCCESS: Non-existent handle returns 404")
        else:
            print(f"   FAIL: Non-existent handle returned {fake_response.status_code}")
            return False

        print("\n" + "=" * 60)
        print("SUCCESS: Full sender page flow works correctly!")
        print("=" * 60)

        # Print the reach URL for manual testing
        print(f"\nReach URL for manual testing: http://localhost:3000/r/{test_handle}")
        print("(Start frontend with: cd frontend && npm start)")

        return True

    except Exception as e:
        print(f"FAIL: Error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("FULL SENDER PAGE FLOW TEST")
    print("=" * 60)

    success = test_full_flow()

    if success:
        print("\nPASS: Step 2 - The Sender Page is complete and working!")
    else:
        print("\nFAIL: Sender page tests failed")
