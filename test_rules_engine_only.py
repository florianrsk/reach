import requests
import time
import json

BASE_URL = "http://localhost:8000"


def test_rules_engine_auto_rejection():
    """Test if rules engine auto-rejects messages with 'quick sync'"""
    print("Testing Rules Engine Auto-Rejection")
    print("=" * 50)

    # 1. Create user
    print("1. Creating test user...")
    email = f"rules_test_{int(time.time())}@example.com"
    password = "TestPassword123!"

    register_data = {"email": email, "password": password, "name": "Rules Test User"}

    response = requests.post(f"{BASE_URL}/api/auth/register", json=register_data)
    if response.status_code != 200:
        print(f"   Register failed: {response.status_code}")
        return False
    print("   User created")

    # 2. Login
    print("2. Logging in...")
    login_data = {"email": email, "password": password}
    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    if response.status_code != 200:
        print(f"   Login failed: {response.status_code}")
        return False

    auth_cookies = response.cookies
    print("   Logged in")

    # 3. Create Face
    print("3. Creating Face...")
    handle = f"rulestest_{int(time.time())}"

    face_data = {
        "handle": handle,
        "display_name": "Rules Test User",
        "headline": "Testing rules engine",
        "current_focus": "Testing auto-rejection of messages",
        "availability_signal": "Testing",
        "prompt": "Test",
        "photo_url": "https://example.com/profile.jpg",
        "links": [],
    }

    response = requests.post(
        f"{BASE_URL}/api/identity", json=face_data, cookies=auth_cookies
    )
    if response.status_code != 200:
        print(f"   Face creation failed: {response.status_code}")
        print(f"   Error: {response.text}")
        return False
    print(f"   Face created with handle: {handle}")

    # 4. Enable rules engine with quick sync rule
    print("4. Enabling rules engine...")

    rule_json = json.dumps(
        {
            "id": "quick_sync_rule",
            "name": "Reject Quick Sync",
            "description": "Reject messages mentioning quick sync",
            "condition": "message contains 'quick sync'",
            "action": "reject",
            "reason": "No quick sync meetings allowed",
            "enabled": True,
        }
    )

    update_data = {"rules_engine": {"enabled": True, "rules": [rule_json]}}

    response = requests.put(
        f"{BASE_URL}/api/modules", json=update_data, cookies=auth_cookies
    )
    if response.status_code != 200:
        print(f"   Rules engine enable failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return False
    print("   Rules engine enabled")

    # 5. Send message with "quick sync"
    print("5. Sending message with 'quick sync'...")
    message_data = {
        "message": "Let's have a quick sync tomorrow to discuss the project.",
        "intent": "meeting",
        "sender_email": "test_sender@example.com",
        "sender_name": "Test Sender",
    }

    response = requests.post(
        f"{BASE_URL}/api/reach/{handle}/message", json=message_data
    )
    if response.status_code != 200:
        print(f"   Message submission failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return False

    result = response.json()
    attempt_id = result.get("attempt_id")
    print(f"   Message submitted, attempt ID: {attempt_id}")

    # 6. Check attempt status
    print("6. Checking attempt status...")
    time.sleep(2)  # Wait for processing

    response = requests.get(f"{BASE_URL}/api/attempts", cookies=auth_cookies)
    if response.status_code != 200:
        print(f"   Failed to get attempts: {response.status_code}")
        return False

    attempts = response.json()
    print(f"   Found {len(attempts)} attempts")

    # Find our attempt
    attempt = None
    for a in attempts:
        if a.get("id") == attempt_id:
            attempt = a
            break

    if not attempt:
        print("   Could not find attempt")
        return False

    print(f"   Attempt status: {attempt.get('status')}")
    print(f"   Rejection reason: {attempt.get('rejection_reason')}")

    # 7. Check if auto-rejected
    if attempt.get("status") == "rejected":
        print("\n✅ SUCCESS: Message was auto-rejected by rules engine!")
        print(f"   Reason: {attempt.get('rejection_reason')}")
        return True
    else:
        print(f"\n⚠️  Message not auto-rejected. Status: {attempt.get('status')}")

        # Try to get more details
        print("\nChecking attempt details...")
        response = requests.get(
            f"{BASE_URL}/api/attempts/{attempt_id}", cookies=auth_cookies
        )
        if response.status_code == 200:
            attempt_details = response.json()
            print(f"   Full attempt details: {json.dumps(attempt_details, indent=2)}")

        return False


if __name__ == "__main__":
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if response.status_code != 200:
            print(f"Backend server not responding: {response.status_code}")
            print(
                "Start the server with: cd Reach-main/backend && python -c 'import server; import uvicorn; uvicorn.run(server.app, host=\"0.0.0.0\", port=8000)'"
            )
            exit(1)
    except:
        print("Backend server not running on localhost:8000")
        print(
            "Start the server with: cd Reach-main/backend && python -c 'import server; import uvicorn; uvicorn.run(server.app, host=\"0.0.0.0\", port=8000)'"
        )
        exit(1)

    # Run test
    success = test_rules_engine_auto_rejection()

    if success:
        print("\n" + "=" * 50)
        print("RULES ENGINE TEST PASSED!")
        print("=" * 50)
    else:
        print("\n" + "=" * 50)
        print("RULES ENGINE TEST FAILED")
        print("=" * 50)
