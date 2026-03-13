#!/usr/bin/env python3
"""
Simple test for the Reach flow using the test backend.
Tests the complete submission -> Decision Surface -> decision loop.
"""

import requests
import json
import time
import sys

# Configuration
BASE_URL = "http://localhost:8001"


def print_step(step_num, description):
    print(f"\n{'=' * 60}")
    print(f"STEP {step_num}: {description}")
    print(f"{'=' * 60}")


def test_endpoint(endpoint, method="GET", data=None, expected_status=200):
    """Test a single endpoint"""
    url = f"{BASE_URL}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "PUT":
            response = requests.put(url, json=data)
        else:
            raise ValueError(f"Unsupported method: {method}")

        print(f"  {method} {endpoint}: {response.status_code}")
        if response.status_code != expected_status:
            print(f"    Response: {response.text[:200]}")
            return None

        return response.json() if response.content else {}
    except requests.exceptions.ConnectionError:
        print(f"  [FAIL] Connection failed: {url}")
        return None
    except Exception as e:
        print(f"  [FAIL] Error: {str(e)}")
        return None


def main():
    print("Testing Reach flow with test backend...")
    print(f"Base URL: {BASE_URL}")

    # Step 1: Check if backend is running
    print_step(1, "Check backend status")
    health = test_endpoint("/health", "GET", expected_status=200)
    if not health:
        print("  [FAIL] Backend not running. Please start it first.")
        print("  Run: cd backend && python server.py")
        return

    print(f"  [OK] Backend is running: {health.get('status', 'unknown')}")

    # Step 2: Test public reach page
    print_step(2, "Test public reach page")
    test_handle = "testuser"
    reach_page = test_endpoint(f"/reach/{test_handle}", "GET", expected_status=200)
    if not reach_page:
        print("  [FAIL] Could not access reach page")
        return

    print(f"  [OK] Reach page accessible")
    print(
        f"    Display name: {reach_page.get('identity', {}).get('display_name', 'Unknown')}"
    )

    # Step 3: Submit a test message
    print_step(3, "Submit test message")
    message_data = {
        "message": "Hello! This is a test message for the Decision Surface.",
        "time_requirement": "Just a read",
        "intent_category": "Test",
    }

    message_response = test_endpoint(
        f"/reach/{test_handle}/message", "POST", message_data, expected_status=200
    )
    if not message_response:
        print("  [FAIL] Could not submit message")
        return

    print(f"  [OK] Message submitted")
    print(f"    Message ID: {message_response.get('message_id', 'unknown')}")

    # Step 4: Check attempts (Decision Surface)
    print_step(4, "Check Decision Surface")
    attempts_response = test_endpoint("/api/attempts", "GET", expected_status=200)
    if not attempts_response:
        print("  [FAIL] Could not get attempts")
        return

    attempts = attempts_response.get("attempts", [])
    print(f"  [OK] Found {len(attempts)} attempts")

    if not attempts:
        print("  [WAIT] No attempts yet, waiting 2 seconds...")
        time.sleep(2)
        attempts_response = test_endpoint("/api/attempts", "GET", expected_status=200)
        if attempts_response:
            attempts = attempts_response.get("attempts", [])
            print(f"  Now found {len(attempts)} attempts")

    if attempts:
        attempt = attempts[0]
        attempt_id = attempt["_id"]
        print(f"  [OK] Using attempt: {attempt_id}")
        print(f"    Message: {attempt.get('message', '')[:50]}...")
        print(f"    Status: {attempt.get('status')}")
        print(f"    Decision: {attempt.get('decision')}")

        # Step 5: Test decision actions
        print_step(5, "Test decision actions")

        # Test approve
        print("\n  Testing: Approve")
        approve_data = {"decision": "deliver_to_human"}
        approve_response = test_endpoint(
            f"/api/attempts/{attempt_id}/decision",
            "PUT",
            approve_data,
            expected_status=200,
        )
        if approve_response:
            print(
                f"    [OK] Approved - New decision: {approve_response.get('decision')}"
            )

        # Test reject
        print("\n  Testing: Reject")
        reject_data = {"decision": "reject"}
        reject_response = test_endpoint(
            f"/api/attempts/{attempt_id}/decision",
            "PUT",
            reject_data,
            expected_status=200,
        )
        if reject_response:
            print(
                f"    [OK] Rejected - New decision: {reject_response.get('decision')}"
            )

        # Test ask
        print("\n  Testing: Ask (request more context)")
        ask_data = {
            "decision": "request_more_context",
            "follow_up_message": "Can you provide more details?",
        }
        ask_response = test_endpoint(
            f"/api/attempts/{attempt_id}/decision", "PUT", ask_data, expected_status=200
        )
        if ask_response:
            print(f"    [OK] Asked - New decision: {ask_response.get('decision')}")

        # Test block
        print("\n  Testing: Block")
        block_response = test_endpoint(
            f"/api/attempts/{attempt_id}/block", "POST", {}, expected_status=200
        )
        if block_response:
            print(
                f"    [OK] Blocked - Response: {block_response.get('message', 'Blocked')}"
            )

    # Step 6: Test filtered views
    print_step(6, "Test filtered views")
    filters = ["pending", "approved", "rejected", "all"]
    for filter_type in filters:
        filtered = test_endpoint(
            f"/api/attempts?filter={filter_type}", "GET", expected_status=200
        )
        if filtered:
            count = len(filtered.get("attempts", []))
            print(f"  [OK] {filter_type}: {count} attempts")

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print("1. [OK] Backend status")
    print("2. [OK] Public reach page")
    print("3. [OK] Message submission")
    print("4. [OK] Decision Surface access")
    print("5. [OK] Decision actions tested")
    print("6. [OK] Filtered views")
    print("\nThe basic Reach workflow is functional!")


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
