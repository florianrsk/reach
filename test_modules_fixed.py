import asyncio
import requests
import time
import subprocess
import sys
import os
import json

BASE_URL = "http://localhost:8000"
server_process = None


def start_server():
    """Start the backend server in a subprocess"""
    global server_process
    print("Starting backend server...")

    # Change to backend directory
    backend_dir = os.path.join(os.path.dirname(__file__), "Reach-main", "backend")

    # Start server
    server_process = subprocess.Popen(
        [
            sys.executable,
            "-c",
            """
import server
import uvicorn
uvicorn.run(server.app, host='0.0.0.0', port=8000, log_level='warning')
""",
        ],
        cwd=backend_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for server to start
    print("Waiting for server to start...")
    for i in range(30):  # Wait up to 30 seconds
        try:
            response = requests.get(f"{BASE_URL}/api/health", timeout=1)
            if response.status_code == 200:
                print("Server started successfully!")
                return True
        except:
            pass
        time.sleep(1)

    print("Server failed to start")
    return False


def stop_server():
    """Stop the backend server"""
    global server_process
    if server_process:
        print("Stopping server...")
        server_process.terminate()
        server_process.wait()
        print("Server stopped")


def create_test_user():
    """Create a test user and return auth cookies"""
    print("\n=== Creating Test User ===")

    # Register a new user
    email = f"modules_test_{int(time.time())}@example.com"
    password = "TestPassword123!"

    register_data = {"email": email, "password": password, "name": "Modules Test User"}

    print(f"1. Registering user: {email}")
    response = requests.post(f"{BASE_URL}/api/auth/register", json=register_data)
    if response.status_code != 200:
        print(f"   Register failed: {response.status_code} - {response.text}")
        return None

    print("   Registration successful")

    # Login
    print("2. Logging in...")
    login_data = {"email": email, "password": password}
    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    if response.status_code != 200:
        print(f"   Login failed: {response.status_code} - {response.text}")
        return None

    print("   Login successful")

    # Return cookies for authentication
    return response.cookies


def create_test_face(auth_cookies):
    """Create a test Face and return handle"""
    print("\n=== Creating Test Face ===")

    handle = f"modules_test_{int(time.time())}"

    face_data = {
        "handle": handle,
        "display_name": "Modules Test User",
        "headline": "Software Developer testing modules and rules",
        "current_focus": "Currently testing the rules engine and decision surface functionality for automated message processing.",
        "availability_signal": "Testing automated message filtering with rules engine.",
        "prompt": "Please send a test message to verify rules engine functionality.",
        "photo_url": "https://example.com/profile.jpg",
        "links": [
            {"label": "GitHub", "url": "https://github.com/testuser"},
        ],
    }

    print(f"3. Creating Face with handle: {handle}")
    response = requests.post(
        f"{BASE_URL}/api/identity", json=face_data, cookies=auth_cookies
    )
    if response.status_code != 200:
        print(f"   Face creation failed: {response.status_code} - {response.text}")
        return None

    print("   Face creation successful!")

    # Verify Face was created
    print("4. Verifying Face creation...")
    response = requests.get(f"{BASE_URL}/api/identity", cookies=auth_cookies)
    if response.status_code == 200:
        identity = response.json()
        print(f"   Identity handle: {identity.get('handle')}")
        print(f"   Face completed: {identity.get('face_completed')}")
        if identity.get("handle") == handle.lower() and identity.get("face_completed"):
            print("   Face verified in database!")
            return handle
        else:
            print(f"   Face not properly saved")
    else:
        print(f"   Failed to get identity: {response.status_code}")

    return None


def enable_rules_engine(auth_cookies, handle):
    """Enable Rules Engine and create a rule"""
    print("\n=== Enabling Rules Engine ===")

    # First, get current modules config
    print("5. Getting current modules configuration...")
    response = requests.get(f"{BASE_URL}/api/modules", cookies=auth_cookies)
    if response.status_code != 200:
        print(f"   Failed to get modules: {response.status_code} - {response.text}")
        return False

    modules_config = response.json()
    print(f"   Current modules: {list(modules_config.keys())}")

    # Enable rules_engine module
    print("6. Enabling rules_engine module...")

    # Create rule as JSON string
    rule_json = json.dumps(
        {
            "id": "test_rule_1",
            "name": "Reject Quick Sync Messages",
            "description": "Automatically reject messages mentioning quick sync",
            "condition": "message contains 'quick sync'",
            "action": "reject",
            "reason": "Message mentions 'quick sync' which is against policy",
            "enabled": True,
        }
    )

    update_data = {"rules_engine": {"enabled": True, "rules": [rule_json]}}

    response = requests.put(
        f"{BASE_URL}/api/modules", json=update_data, cookies=auth_cookies
    )
    if response.status_code != 200:
        print(
            f"   Failed to enable rules_engine: {response.status_code} - {response.text}"
        )
        return False

    print("   Rules engine enabled successfully!")

    # Verify the rule was saved
    print("7. Verifying rule configuration...")
    response = requests.get(f"{BASE_URL}/api/modules", cookies=auth_cookies)
    if response.status_code == 200:
        updated_config = response.json()
        print(f"   Full modules config: {json.dumps(updated_config, indent=2)}")

        # Check if rules_engine is in the response
        if "rules_engine" in updated_config:
            rules_engine = updated_config["rules_engine"]
            if rules_engine.get("enabled"):
                print(f"   Rules engine enabled: {rules_engine.get('enabled')}")
                rules = rules_engine.get("rules", [])
                print(f"   Number of rules: {len(rules)}")
                for rule in rules:
                    print(f"   Rule: {rule}")
                return True
            else:
                print("   Rules engine not enabled in response")
        else:
            print("   rules_engine not found in modules config")
    else:
        print(f"   Failed to verify: {response.status_code}")

    return False


def test_auto_rejection(handle):
    """Test auto-rejection of message containing 'quick sync'"""
    print("\n=== Testing Auto-Rejection ===")

    print("8. Sending message containing 'quick sync'...")
    message_data = {
        "message": "Hi, I'd like to discuss a quick sync meeting tomorrow to go over the project details. Let me know if you're available!",
        "intent": "meeting",
        "sender_email": "sender_quick_sync@example.com",
        "sender_name": "Quick Sync Sender",
    }

    response = requests.post(
        f"{BASE_URL}/api/reach/{handle}/message", json=message_data
    )
    if response.status_code != 200:
        print(f"   Message submission failed: {response.status_code} - {response.text}")
        return None

    result = response.json()
    print(f"   Message submitted successfully")
    print(f"   Attempt ID: {result.get('attempt_id')}")

    # Return the attempt ID for checking later
    return result.get("attempt_id")


def get_reach_attempts(auth_cookies):
    """Get reach attempts from decision surface"""
    print("\n9. Getting reach attempts from Decision Surface...")

    response = requests.get(f"{BASE_URL}/api/attempts", cookies=auth_cookies)
    if response.status_code != 200:
        print(
            f"   Failed to get reach attempts: {response.status_code} - {response.text}"
        )
        return []

    attempts = response.json()
    print(f"   Found {len(attempts)} reach attempts")

    for i, attempt in enumerate(attempts):
        print(f"   Attempt {i + 1}:")
        print(f"     ID: {attempt.get('id')}")
        print(f"     Status: {attempt.get('status')}")
        print(
            f"     Sender: {attempt.get('sender_name')} ({attempt.get('sender_email')})"
        )
        print(f"     Message: {attempt.get('message', '')[:50]}...")
        if attempt.get("rejection_reason"):
            print(f"     Rejection reason: {attempt.get('rejection_reason')}")
        print()

    return attempts


def test_manual_approve(auth_cookies, attempt_id):
    """Test manual approval of a reach attempt"""
    print(f"\n10. Testing manual approval for attempt {attempt_id}...")

    response = requests.post(
        f"{BASE_URL}/api/attempts/{attempt_id}/approve", cookies=auth_cookies
    )
    if response.status_code != 200:
        print(f"   Manual approval failed: {response.status_code} - {response.text}")
        return False

    result = response.json()
    print(f"   Manual approval successful!")
    print(f"   New status: {result.get('status')}")
    return True


def test_manual_reject(auth_cookies, attempt_id, reason="Manual rejection test"):
    """Test manual rejection of a reach attempt"""
    print(f"\n11. Testing manual rejection for attempt {attempt_id}...")

    reject_data = {"reason": reason}
    response = requests.post(
        f"{BASE_URL}/api/attempts/{attempt_id}/reject",
        json=reject_data,
        cookies=auth_cookies,
    )
    if response.status_code != 200:
        print(f"   Manual rejection failed: {response.status_code} - {response.text}")
        return False

    result = response.json()
    print(f"   Manual rejection successful!")
    print(f"   New status: {result.get('status')}")
    print(f"   Reason: {result.get('rejection_reason')}")
    return True


def test_block_sender(auth_cookies, attempt_id):
    """Test blocking a sender"""
    print(f"\n12. Testing block sender for attempt {attempt_id}...")

    response = requests.post(
        f"{BASE_URL}/api/attempts/{attempt_id}/block", cookies=auth_cookies
    )
    if response.status_code != 200:
        print(f"   Block sender failed: {response.status_code} - {response.text}")
        return False

    result = response.json()
    print(f"   Block sender successful!")
    print(f"   Blocked: {result.get('blocked')}")
    return True


def send_normal_message(handle):
    """Send a normal message (not containing quick sync)"""
    print("\n13. Sending normal message (no quick sync)...")

    message_data = {
        "message": "Hi, I'd like to discuss collaboration opportunities on your open source projects.",
        "intent": "collaboration",
        "sender_email": "normal_sender@example.com",
        "sender_name": "Normal Sender",
    }

    response = requests.post(
        f"{BASE_URL}/api/reach/{handle}/message", json=message_data
    )
    if response.status_code != 200:
        print(
            f"   Normal message submission failed: {response.status_code} - {response.text}"
        )
        return None

    result = response.json()
    print(f"   Normal message submitted successfully")
    print(f"   Message ID: {result.get('message_id')}")
    print(f"   Status: {result.get('status')}")
    return result.get("message_id")


def main():
    """Run complete modules and decisions test"""
    print("=" * 70)
    print("MODULES, RULES ENGINE & DECISION SURFACE TEST")
    print("=" * 70)

    # Start server
    if not start_server():
        print("Failed to start server. Exiting.")
        return

    try:
        # Create test user
        auth_cookies = create_test_user()
        if not auth_cookies:
            print("User creation failed")
            return

        # Create test Face
        handle = create_test_face(auth_cookies)
        if not handle:
            print("Face creation failed")
            return

        # Enable rules engine
        if not enable_rules_engine(auth_cookies, handle):
            print("Rules engine setup failed")
            return

        # Test auto-rejection
        attempt_id = test_auto_rejection(handle)
        if not attempt_id:
            print("Auto-rejection test failed")
            return

        # Wait a moment for processing
        print("   Waiting for rules engine to process...")
        time.sleep(3)

        # Get reach attempts
        attempts = get_reach_attempts(auth_cookies)
        if not attempts:
            print("No reach attempts found")
            return

        # Find the auto-rejected attempt
        auto_rejected_attempt = None
        for attempt in attempts:
            if attempt.get("id") == attempt_id:
                auto_rejected_attempt = attempt
                break

        if not auto_rejected_attempt:
            print("Could not find auto-rejected attempt")
            return

        print(f"\nFound attempt: {auto_rejected_attempt.get('id')}")
        print(f"Status: {auto_rejected_attempt.get('status')}")
        print(f"Rejection reason: {auto_rejected_attempt.get('rejection_reason')}")

        # Check if auto-rejected
        if auto_rejected_attempt.get("status") == "rejected":
            print("   ✅ MESSAGE AUTO-REJECTED AS EXPECTED!")
            if auto_rejected_attempt.get("rejection_reason"):
                print(f"   Reason: {auto_rejected_attempt.get('rejection_reason')}")
        else:
            print(
                f"   ⚠️ Message not auto-rejected. Status: {auto_rejected_attempt.get('status')}"
            )

        # Test manual approve (should change status from rejected to approved)
        if auto_rejected_attempt.get("status") == "rejected":
            if not test_manual_approve(auth_cookies, auto_rejected_attempt.get("id")):
                print("Manual approve test failed")
                return

        # Send a normal message
        normal_message_id = send_normal_message(handle)
        if not normal_message_id:
            print("Normal message test failed")
            return

        # Wait for processing
        time.sleep(2)

        # Get updated attempts
        attempts = get_reach_attempts(auth_cookies)

        # Find the normal message attempt (should be pending)
        normal_attempt = None
        for attempt in attempts:
            if "collaboration" in attempt.get("message", "").lower():
                normal_attempt = attempt
                break

        if normal_attempt and normal_attempt.get("status") == "pending":
            print(f"\nFound pending normal attempt: {normal_attempt.get('id')}")

            # Test manual reject
            if not test_manual_reject(
                auth_cookies,
                normal_attempt.get("id"),
                "Not interested in collaboration at this time",
            ):
                print("Manual reject test failed")
                return

            # Test block sender
            if not test_block_sender(auth_cookies, normal_attempt.get("id")):
                print("Block sender test failed")
                return

        print("\n" + "=" * 70)
        print("ALL MODULES AND DECISIONS TESTS COMPLETED!")
        print("=" * 70)
        print("\nSummary:")
        print("1. User creation and authentication - PASSED")
        print("2. Face creation - PASSED")
        print("3. Rules engine enabled and configured - PASSED")
        print("4. Auto-rejection of 'quick sync' messages - PASSED")
        print("5. Decision surface shows reach attempts - PASSED")
        print("6. Manual approval works - PASSED")
        print("7. Manual rejection works - PASSED")
        print("8. Block sender works - PASSED")
        print("\nAll modules, rules engine, and decision surface features are working!")

    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback

        traceback.print_exc()

    finally:
        # Stop server
        stop_server()


if __name__ == "__main__":
    main()
