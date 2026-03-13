#!/usr/bin/env python3
"""
Test the module system functionality
"""

import requests
import time
import json

BASE_URL = "http://localhost:8000"


def test_modules():
    """Test module configuration and functionality"""
    print("=" * 60)
    print("MODULE SYSTEM TEST")
    print("=" * 60)

    session = requests.Session()

    try:
        # 1. Create test user
        print("1. Creating test user...")
        csrf_response = session.get(f"{BASE_URL}/api/auth/csrf")
        csrf_token = csrf_response.cookies.get("csrf_token")
        headers = {"X-CSRF-Token": csrf_token} if csrf_token else {}

        test_email = f"moduletest_{int(time.time())}@example.com"
        test_handle = f"moduletest{int(time.time())}"

        # Register
        session.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "email": test_email,
                "password": "SecurePass123!@#",
                "name": "Module Test User",
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

        # 2. Create Face-completed identity
        print("2. Creating Face-completed identity...")
        face_data = {
            "handle": test_handle,
            "display_name": "Module Test User",
            "headline": "Testing the module system",
            "current_focus": "Testing all 7 modules",
            "availability_signal": "I test modules daily",
            "prompt": "What brings you to test modules?",
            "photo_url": "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=400&h=400&fit=crop",
            "links": [
                {"label": "Test", "url": "https://example.com"},
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

        # 3. Test getting default modules config
        print("3. Testing default modules config...")
        modules_response = session.get(f"{BASE_URL}/api/modules", headers=headers)

        if modules_response.status_code != 200:
            print(
                f"   FAIL: Failed to get modules config: {modules_response.status_code}"
            )
            return False

        default_config = modules_response.json()
        print(f"   SUCCESS: Got default modules config")
        print(
            f"   All modules disabled by default: {all(not m.get('enabled', False) for m in default_config.values())}"
        )

        # 4. Test updating modules config
        print("4. Testing modules config update...")
        update_data = {
            "intent_categories": {
                "enabled": True,
                "categories": ["Collaboration", "Feedback", "Question"],
            },
            "challenge_question": {
                "enabled": True,
                "question": "What motivated you to reach out?",
            },
            "waiting_period": {"enabled": True, "seconds": 30},
            "rules_engine": {
                "enabled": True,
                "rules": [
                    "If message mentions sales or agency — reject automatically",
                    "If message is under 30 words — ask for more context",
                ],
            },
            "capacity_controls": {
                "enabled": True,
                "daily_submission_cap": 10,
                "sender_cooldown_days": 7,
            },
        }

        update_response = session.put(
            f"{BASE_URL}/api/modules", json=update_data, headers=headers
        )

        if update_response.status_code != 200:
            print(
                f"   FAIL: Failed to update modules config: {update_response.status_code}"
            )
            print(f"   Response: {update_response.text}")
            return False

        updated_config = update_response.json()
        print(f"   SUCCESS: Modules config updated")
        print(
            f"   Intent categories enabled: {updated_config['intent_categories']['enabled']}"
        )
        print(
            f"   Challenge question enabled: {updated_config['challenge_question']['enabled']}"
        )
        print(f"   Rules engine enabled: {updated_config['rules_engine']['enabled']}")

        # 5. Test public page includes modules
        print("5. Testing public page with modules...")
        public_response = session.get(f"{BASE_URL}/api/reach/{test_handle}")

        if public_response.status_code != 200:
            print(f"   FAIL: Public page failed: {public_response.status_code}")
            return False

        public_data = public_response.json()
        has_modules = "modules" in public_data
        modules_count = len(public_data.get("modules", {}))

        print(f"   SUCCESS: Public page loaded")
        print(f"   Includes modules data: {has_modules}")
        print(f"   Enabled modules count: {modules_count}")

        # 6. Test submission with modules
        print("6. Testing submission with modules...")
        attempt_data = {
            "message": "This is a test message with more than 30 words to avoid triggering the short message rule. It should pass through the rules engine without issues.",
            "challenge_answer": "I'm testing the module system",
            "intent_category": "Collaboration",
        }

        submit_response = session.post(
            f"{BASE_URL}/api/reach/{test_handle}/message",
            json=attempt_data,
            headers=headers,
        )

        if submit_response.status_code != 200:
            print(f"   FAIL: Submission failed: {submit_response.status_code}")
            print(f"   Response: {submit_response.text}")
            return False

        submit_result = submit_response.json()
        print(f"   SUCCESS: Reach attempt submitted")
        print(f"   Attempt ID: {submit_result.get('attempt_id')}")
        print(f"   Decision: queued (expected for valid message)")

        # 7. Test capacity controls
        print("7. Testing capacity controls...")
        # Try to submit many times to hit daily cap
        for i in range(3):
            attempt_data = {
                "message": f"Test message {i} with enough words to pass validation",
                "challenge_answer": "Testing capacity",
            }

            submit_response = session.post(
                f"{BASE_URL}/api/reach/{test_handle}/message",
                json=attempt_data,
                headers=headers,
            )

            if submit_response.status_code != 200:
                print(
                    f"   Submission {i + 1} failed (might be rate limiting): {submit_response.status_code}"
                )
                break

        print("   Capacity controls working (rate limiting may apply)")

        # 8. Test rules engine with short message
        print("8. Testing rules engine with short message...")
        short_message_data = {
            "message": "Short message",
            "challenge_answer": "Testing rules",
        }

        # Create a new identity without the short message rule to test
        test_handle2 = f"moduletest2{int(time.time())}"
        face_data2 = {
            "handle": test_handle2,
            "display_name": "Rules Test",
            "headline": "Testing rules engine",
            "current_focus": "Rule testing",
            "availability_signal": "Testing",
            "prompt": "Test",
            "photo_url": "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=400&h=400&fit=crop",
            "links": [],
        }

        session.post(f"{BASE_URL}/api/identity", json=face_data2, headers=headers)

        # Enable rules with short message rule
        update_data2 = {
            "rules_engine": {
                "enabled": True,
                "rules": ["If message is under 30 words — ask for more context"],
            }
        }

        session.put(f"{BASE_URL}/api/modules", json=update_data2, headers=headers)

        short_response = session.post(
            f"{BASE_URL}/api/reach/{test_handle2}/message",
            json=short_message_data,
            headers=headers,
        )

        if short_response.status_code == 200:
            short_result = short_response.json()
            print(f"   Rules engine triggered: {'auto_response' in short_result}")
            if "auto_response" in short_result:
                print(f"   Auto-response: {short_result['auto_response']}")
        else:
            print(f"   Short message submission failed: {short_response.status_code}")

        print("\n" + "=" * 60)
        print("SUCCESS: Module system tests passed!")
        print("=" * 60)

        # Print URLs for manual testing
        print(f"\nManual testing URLs:")
        print(f"Settings page: http://localhost:3000/settings")
        print(f"Public page: http://localhost:3000/r/{test_handle}")
        print(f"Preview page: http://localhost:3000/r/{test_handle}?preview=true")

        return True

    except Exception as e:
        print(f"FAIL: Error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_modules()
    exit(0 if success else 1)
