import requests
import time
import json

BASE_URL = "http://localhost:8000"


def test_all_fixes():
    print("Testing all fixes")
    print("=" * 60)

    # 1. Start by checking if server is running
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if response.status_code != 200:
            print("Server not running")
            return False
    except:
        print("Server not running")
        return False

    print("1. Server is running ✓")

    # 2. Create user
    print("\n2. Creating test user...")
    email = f"fix_test_{int(time.time())}@example.com"
    password = "TestPassword123!"

    register_data = {"email": email, "password": password, "name": "Fix Test User"}

    response = requests.post(f"{BASE_URL}/api/auth/register", json=register_data)
    if response.status_code != 200:
        print(f"   Register failed: {response.status_code} - {response.text}")
        return False
    print("   User created ✓")

    # 3. Login
    print("\n3. Logging in...")
    login_data = {"email": email, "password": password}
    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    if response.status_code != 200:
        print(f"   Login failed: {response.status_code} - {response.text}")
        return False

    auth_cookies = response.cookies
    print("   Logged in ✓")

    # 4. Create Face
    print("\n4. Creating Face...")
    handle = f"fixtest_{int(time.time())}"

    face_data = {
        "handle": handle,
        "display_name": "Fix Test User",
        "headline": "Testing fixes",
        "current_focus": "Testing rules engine and attempts endpoint fixes",
        "availability_signal": "Testing",
        "prompt": "Test",
        "photo_url": "https://example.com/profile.jpg",
        "links": [],
    }

    response = requests.post(
        f"{BASE_URL}/api/identity", json=face_data, cookies=auth_cookies
    )
    if response.status_code != 200:
        print(f"   Face creation failed: {response.status_code} - {response.text}")
        return False
    print(f"   Face created with handle: {handle} ✓")

    # 5. Enable rules engine with quick sync rule
    print("\n5. Enabling rules engine...")

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
        print(
            f"   Rules engine enable failed: {response.status_code} - {response.text}"
        )
        return False
    print("   Rules engine enabled ✓")

    # 6. Test attempts endpoint (should return empty list, not 404)
    print("\n6. Testing attempts endpoint...")
    response = requests.get(f"{BASE_URL}/api/attempts", cookies=auth_cookies)
    if response.status_code != 200:
        print(f"   Attempts endpoint failed: {response.status_code} - {response.text}")
        return False

    attempts = response.json()
    print(f"   Attempts endpoint returned {len(attempts)} attempts (should be 0) ✓")

    # 7. Send message with "quick sync" - should be auto-rejected
    print("\n7. Testing auto-rejection of 'quick sync' message...")
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
        print(f"   Message submission failed: {response.status_code} - {response.text}")
        return False

    result = response.json()
    attempt_id = result.get("attempt_id")
    print(f"   Message submitted, attempt ID: {attempt_id}")

    # 8. Check if attempt was auto-rejected
    print("\n8. Checking if message was auto-rejected...")
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

    if attempt.get("status") == "rejected":
        print("   ✅ Message was auto-rejected by rules engine! ✓")
    else:
        print(f"   ❌ Message not auto-rejected. Status: {attempt.get('status')}")
        return False

    # 9. Test manual approval
    print("\n9. Testing manual approval...")
    response = requests.post(
        f"{BASE_URL}/api/attempts/{attempt_id}/approve", cookies=auth_cookies
    )
    if response.status_code != 200:
        print(f"   Manual approval failed: {response.status_code} - {response.text}")
        return False

    result = response.json()
    print(f"   Manual approval successful! New status: {result.get('status')} ✓")

    # 10. Test manual rejection
    print("\n10. Testing manual rejection...")
    # First send another message
    message_data2 = {
        "message": "I'd like to collaborate on your project.",
        "intent": "collaboration",
        "sender_email": "test_sender2@example.com",
        "sender_name": "Test Sender 2",
    }

    response = requests.post(
        f"{BASE_URL}/api/reach/{handle}/message", json=message_data2
    )
    if response.status_code != 200:
        print(f"   Second message submission failed: {response.status_code}")
        return False

    result2 = response.json()
    attempt_id2 = result2.get("attempt_id")
    print(f"   Second message submitted, attempt ID: {attempt_id2}")

    time.sleep(2)

    # Now reject it
    reject_data = {"reason": "Not interested in collaboration"}
    response = requests.post(
        f"{BASE_URL}/api/attempts/{attempt_id2}/reject",
        json=reject_data,
        cookies=auth_cookies,
    )
    if response.status_code != 200:
        print(f"   Manual rejection failed: {response.status_code} - {response.text}")
        return False

    result = response.json()
    print(f"   Manual rejection successful! New status: {result.get('status')} ✓")

    # 11. Test block sender
    print("\n11. Testing block sender...")
    response = requests.post(
        f"{BASE_URL}/api/attempts/{attempt_id2}/block", cookies=auth_cookies
    )
    if response.status_code != 200:
        print(f"   Block sender failed: {response.status_code} - {response.text}")
        return False

    result = response.json()
    print(f"   Block sender successful! Blocked: {result.get('blocked')} ✓")

    print("\n" + "=" * 60)
    print("ALL FIXES TESTED SUCCESSFULLY!")
    print("=" * 60)
    print("\nSummary:")
    print("1. ✅ Rules engine auto-rejects 'quick sync' messages")
    print("2. ✅ Attempts endpoint returns data (not 404)")
    print("3. ✅ Manual approval works")
    print("4. ✅ Manual rejection works")
    print("5. ✅ Block sender works")

    return True


if __name__ == "__main__":
    success = test_all_fixes()
    if not success:
        print("\n❌ Some tests failed")
        exit(1)
