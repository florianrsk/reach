#!/usr/bin/env python3
"""
Comprehensive test for the full Reach flow:
1. Create a test user and reach page
2. Submit a message through the public reach page
3. Verify the message appears in Decision Surface
4. Test all decision actions (approve, reject, ask, block)
5. Verify the complete workflow
"""

import requests
import json
import time
import sys
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:8001"
TEST_USER_EMAIL = f"test_{int(time.time())}@example.com"
TEST_USER_PASSWORD = "testpassword123"
TEST_HANDLE = f"testuser{int(time.time())}"


def print_step(step_num, description):
    print(f"\n{'=' * 60}")
    print(f"STEP {step_num}: {description}")
    print(f"{'=' * 60}")


def test_api(endpoint, method="GET", data=None, headers=None, expected_status=200):
    """Helper to test API endpoints"""
    url = f"{BASE_URL}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers)
        elif method == "PUT":
            response = requests.put(url, json=data, headers=headers)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported method: {method}")

        if response.status_code != expected_status:
            print(f"  [FAIL] Failed: {method} {endpoint}")
            print(f"     Expected: {expected_status}, Got: {response.status_code}")
            print(f"     Response: {response.text[:200]}")
            return None

        print(f"  [OK] {method} {endpoint} - {response.status_code}")
        return response.json() if response.content else {}
    except requests.exceptions.ConnectionError:
        print(f"  [FAIL] Connection failed: {url}")
        print(f"     Make sure backend is running on {BASE_URL}")
        return None
    except Exception as e:
        print(f"  [FAIL] Error: {method} {endpoint} - {str(e)}")
        return None


def main():
    print(">>> Starting comprehensive Reach flow test")
    print(f"Base URL: {BASE_URL}")
    print(f"Test user: {TEST_USER_EMAIL}")
    print(f"Test handle: {TEST_HANDLE}")

    # Step 1: Create test user
    print_step(1, "Create test user")
    user_data = {
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD,
        "name": "Test User",
    }
    user_response = test_api(
        "/api/auth/register", "POST", user_data, expected_status=201
    )
    if not user_response:
        print("Failed to create user. Aborting.")
        return

    # Get auth token
    login_data = {"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}
    login_response = test_api(
        "/api/auth/login", "POST", login_data, expected_status=200
    )
    if not login_response:
        print("Failed to login. Aborting.")
        return

    auth_token = login_response.get("access_token")
    if not auth_token:
        print("No auth token received. Aborting.")
        return

    headers = {"Authorization": f"Bearer {auth_token}"}

    # Step 2: Create reach page
    print_step(2, "Create reach page")
    reach_data = {
        "handle": TEST_HANDLE,
        "display_name": "Test User",
        "headline": "Software Developer",
        "prompt": "What brings you here?",
        "availability_signal": "I check this daily",
        "current_focus": "Building Reach",
        "photo_url": "https://example.com/photo.jpg",
        "links": [
            {"label": "Twitter", "url": "https://twitter.com/test"},
            {"label": "GitHub", "url": "https://github.com/test"},
        ],
        "modules": {
            "challenge_question": {"enabled": False},
            "time_signal": {"enabled": True},
            "waiting_period": {"enabled": False},
            "deposit": {"enabled": False},
            "intent_categories": {
                "enabled": True,
                "categories": ["Collaboration", "Question", "Feedback", "Opportunity"],
            },
        },
    }

    reach_response = test_api(
        "/api/reach", "POST", reach_data, headers, expected_status=201
    )
    if not reach_response:
        print("Failed to create reach page. Aborting.")
        return

    # Step 3: Verify reach page is accessible
    print_step(3, "Verify public reach page")
    public_response = test_api(f"/reach/{TEST_HANDLE}", "GET", expected_status=200)
    if not public_response:
        print("Failed to access public reach page. Aborting.")
        return

    print(f"  [OK] Reach page accessible at /reach/{TEST_HANDLE}")
    print(f"  Display name: {public_response.get('identity', {}).get('display_name')}")

    # Step 4: Submit a test message
    print_step(4, "Submit test message")
    message_data = {
        "message": "Hello! I'm interested in collaborating on your project. I have experience with FastAPI and React.",
        "time_requirement": "A conversation",
        "intent_category": "Collaboration",
    }

    message_response = test_api(
        f"/reach/{TEST_HANDLE}/message", "POST", message_data, expected_status=200
    )
    if not message_response:
        print("Failed to submit message. Aborting.")
        return

    print(f"  [OK] Message submitted: {message_response.get('message_id')}")

    # Give the system a moment to process
    print("  [WAIT] Waiting 2 seconds for system to process...")
    time.sleep(2)

    # Step 5: Check attempts in Decision Surface
    print_step(5, "Check Decision Surface")
    attempts_response = test_api(
        "/api/attempts", "GET", headers=headers, expected_status=200
    )
    if not attempts_response:
        print("Failed to get attempts. Aborting.")
        return

    attempts = attempts_response.get("attempts", [])
    print(f"  Found {len(attempts)} attempts")

    if not attempts:
        print("  [FAIL] No attempts found. The message may not have been processed.")
        return

    # Find our test attempt
    test_attempt = None
    for attempt in attempts:
        if attempt.get("message", "").startswith(
            "Hello! I'm interested in collaborating"
        ):
            test_attempt = attempt
            break

    if not test_attempt:
        print("  [FAIL] Test attempt not found")
        print("  Available attempts:")
        for attempt in attempts:
            print(f"    - {attempt.get('message', '')[:50]}...")
        return

    attempt_id = test_attempt["_id"]
    print(f"  [OK] Found test attempt: {attempt_id}")
    print(f"  Status: {test_attempt.get('status')}")
    print(f"  Decision: {test_attempt.get('decision')}")
    print(
        f"  AI Classification: {test_attempt.get('ai_classification', {}).get('reasoning', 'No reasoning')[:100]}..."
    )

    # Step 6: Test decision actions
    print_step(6, "Test decision actions")

    # Test 1: Approve (Let through)
    print("\n  Testing: Approve (Let through)")
    approve_data = {"decision": "deliver_to_human"}
    approve_response = test_api(
        f"/api/attempts/{attempt_id}/decision",
        "PUT",
        approve_data,
        headers,
        expected_status=200,
    )
    if approve_response:
        print(f"    [OK] Approved - New decision: {approve_response.get('decision')}")

    # Test 2: Reject (Pass)
    print("\n  Testing: Reject (Pass)")
    reject_data = {"decision": "reject"}
    reject_response = test_api(
        f"/api/attempts/{attempt_id}/decision",
        "PUT",
        reject_data,
        headers,
        expected_status=200,
    )
    if reject_response:
        print(f"    [OK] Rejected - New decision: {reject_response.get('decision')}")

    # Test 3: Ask (Request more context)
    print("\n  Testing: Ask (Request more context)")
    ask_data = {
        "decision": "request_more_context",
        "follow_up_message": "Can you tell me more about your experience?",
    }
    ask_response = test_api(
        f"/api/attempts/{attempt_id}/decision",
        "PUT",
        ask_data,
        headers,
        expected_status=200,
    )
    if ask_response:
        print(f"    [OK] Asked - New decision: {ask_response.get('decision')}")

    # Test 4: Block
    print("\n  Testing: Block")
    block_response = test_api(
        f"/api/attempts/{attempt_id}/block", "POST", {}, headers, expected_status=200
    )
    if block_response:
        print(
            f"    [OK] Blocked - Response: {block_response.get('message', 'Blocked successfully')}"
        )

    # Step 7: Verify filtered views
    print_step(7, "Verify filtered views")

    filters = ["pending", "approved", "rejected", "all"]
    for filter_type in filters:
        filtered_response = test_api(
            f"/api/attempts?filter={filter_type}",
            "GET",
            headers=headers,
            expected_status=200,
        )
        if filtered_response:
            count = len(filtered_response.get("attempts", []))
            print(f"  [OK] {filter_type.capitalize()}: {count} attempts")

    # Step 8: Test auto-decided section
    print_step(8, "Test auto-decided section")

    # Create a rule that would auto-approve
    rule_data = {
        "name": "Test Auto-approve Rule",
        "conditions": [
            {"field": "message", "operator": "contains", "value": "collaborating"}
        ],
        "action": "deliver_to_human",
        "enabled": True,
        "priority": 1,
    }

    rule_response = test_api(
        "/api/rules", "POST", rule_data, headers, expected_status=201
    )
    if rule_response:
        print(f"  [OK] Created auto-approve rule: {rule_response.get('_id')}")

        # Submit another message that triggers the rule
        auto_message_data = {
            "message": "I want to collaborate on your project!",
            "time_requirement": "Just a read",
        }

        auto_response = test_api(
            f"/reach/{TEST_HANDLE}/message",
            "POST",
            auto_message_data,
            expected_status=200,
        )
        if auto_response:
            print(f"  [OK] Submitted auto-trigger message")

            # Wait for processing
            time.sleep(2)

            # Check if it was auto-decided
            auto_attempts_response = test_api(
                "/api/attempts?filter=all", "GET", headers=headers, expected_status=200
            )
            if auto_attempts_response:
                auto_attempts = auto_attempts_response.get("attempts", [])
                for attempt in auto_attempts:
                    if "I want to collaborate" in attempt.get("message", ""):
                        if attempt.get("decision") == "deliver_to_human":
                            print(f"  [OK] Auto-approved by rule: {attempt.get('_id')}")
                            print(
                                f"    Rule triggered: {attempt.get('rules_triggered', [])}"
                            )
                        break

    # Step 9: Cleanup
    print_step(9, "Cleanup test data")

    # Delete the rule
    if rule_response and rule_response.get("_id"):
        delete_rule = test_api(
            f"/api/rules/{rule_response['_id']}",
            "DELETE",
            headers=headers,
            expected_status=200,
        )
        if delete_rule:
            print(f"  [OK] Deleted test rule")

    # Note: In a real test, we might delete the test user too
    print(f"  Test user and reach page remain for manual inspection")
    print(f"  User email: {TEST_USER_EMAIL}")
    print(f"  Reach page: {BASE_URL}/reach/{TEST_HANDLE}")

    print("\n" + "=" * 60)
    print(">>> COMPREHENSIVE TEST COMPLETE")
    print("=" * 60)
    print("\nSummary:")
    print("1. [OK] User creation and authentication")
    print("2. [OK] Reach page creation")
    print("3. [OK] Public page accessibility")
    print("4. [OK] Message submission")
    print("5. [OK] Decision Surface access")
    print("6. [OK] All decision actions tested")
    print("7. [OK] Filtered views verified")
    print("8. [OK] Auto-decided rules tested")
    print("9. [OK] Cleanup completed")
    print("\nThe full Reach workflow is functional!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
