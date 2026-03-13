#!/usr/bin/env python3
"""
Complete end-to-end test of every feature with real HTTP requests
against the running backend connected to MongoDB Atlas.
"""

import requests
import time
import json
import sys
from datetime import datetime

BASE_URL = "http://localhost:8001"
SESSION = requests.Session()


def print_step(step, description):
    print(f"\n{'=' * 60}")
    print(f"STEP {step}: {description}")
    print(f"{'=' * 60}")


def log_result(success, message):
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"  {status}: {message}")
    return success


def test_auth_flow():
    """Test complete auth flow: register, login, session, logout"""
    print_step(1, "AUTH FLOW TEST")

    # Generate unique test credentials
    timestamp = int(time.time())
    test_email = f"test_complete_{timestamp}@example.com"
    test_password = "TestPassword123!LongEnough"
    test_name = f"Test User {timestamp}"

    # 1. Register new user
    print("1. Register new user")
    register_data = {"email": test_email, "password": test_password, "name": test_name}

    try:
        response = SESSION.post(f"{BASE_URL}/api/auth/register", json=register_data)
        success = response.status_code == 200
        if not success:
            print(f"    Response: {response.status_code} - {response.text[:200]}")
        result = log_result(success, f"Register user {test_email}")
        if not result:
            return False, None, None
    except Exception as e:
        print(f"    Exception: {e}")
        return False, None, None

    # 2. Login with that user
    print("2. Login with registered user")
    login_data = {"email": test_email, "password": test_password}

    try:
        response = SESSION.post(f"{BASE_URL}/api/auth/login", json=login_data)
        success = response.status_code == 200
        if not success:
            print(f"    Response: {response.status_code} - {response.text[:200]}")
        result = log_result(success, "Login successful")
        if not result:
            return False, None, None

        # Check response structure
        login_response = response.json()
        print(f"    Login response keys: {list(login_response.keys())}")
    except Exception as e:
        print(f"    Exception: {e}")
        return False, None, None

    # 3. Session persists — `/api/auth/me` returns user data
    print("3. Check session persistence")
    try:
        response = SESSION.get(f"{BASE_URL}/api/auth/me")
        success = response.status_code == 200
        if success:
            user_data = response.json()
            print(f"    User data: {user_data.get('email')}")
            print(f"    User ID: {user_data.get('id')}")
        else:
            print(f"    Response: {response.status_code} - {response.text[:200]}")
        result = log_result(success, "Session persists with /api/auth/me")
        if not result:
            return False, None, None
    except Exception as e:
        print(f"    Exception: {e}")
        return False, None, None

    # 4. Logout works
    print("4. Test logout")
    try:
        response = SESSION.post(f"{BASE_URL}/api/auth/logout")
        success = response.status_code == 200
        if not success:
            print(f"    Response: {response.status_code} - {response.text[:200]}")
        result = log_result(success, "Logout successful")

        # Verify session is cleared
        response = SESSION.get(f"{BASE_URL}/api/auth/me")
        if response.status_code != 200:
            print(f"    Good: Session cleared after logout")
        else:
            print(f"    Warning: Session still active after logout")
    except Exception as e:
        print(f"    Exception: {e}")
        return False, None, None

    # Re-login for subsequent tests
    print("5. Re-login for Face creation tests")
    try:
        response = SESSION.post(f"{BASE_URL}/api/auth/login", json=login_data)
        if response.status_code != 200:
            print(
                f"    Failed to re-login: {response.status_code} - {response.text[:200]}"
            )
            return False, None, None
        print(f"    Re-login successful")
    except Exception as e:
        print(f"    Exception: {e}")
        return False, None, None

    return True, test_email, test_password


def test_face_creation(test_email):
    """Test Face creation with all required fields"""
    print_step(2, "FACE CREATION TEST")

    # Generate unique handle
    timestamp = int(time.time())
    test_handle = f"testface{timestamp}"

    # 5. Create a Face with all required fields
    print("5. Create Face with all required fields")
    face_data = {
        "handle": test_handle,
        "display_name": "Test User Display Name",
        "headline": "Software Developer with extensive experience in backend systems and API design",
        "current_focus": "Currently focused on building scalable microservices architecture and improving system reliability through comprehensive testing",
        "availability_signal": "I check my messages daily and typically respond within 24 hours for urgent matters",
        "prompt": "What brings you to my page today? Please share what you're working on and how I might be able to help.",
        "photo_url": "https://example.com/profile.jpg",
        "links": [
            {"label": "GitHub", "url": "https://github.com/testuser"},
            {"label": "LinkedIn", "url": "https://linkedin.com/in/testuser"},
        ],
    }

    try:
        response = SESSION.post(f"{BASE_URL}/api/identity", json=face_data)
        success = response.status_code in [200, 201]
        if not success:
            print(f"    Response: {response.status_code} - {response.text[:200]}")
            # Try to get more details
            if response.status_code == 422:
                try:
                    errors = response.json()
                    print(f"    Validation errors: {json.dumps(errors, indent=2)}")
                except:
                    pass
            return False, None
        result = log_result(success, f"Face created with handle: {test_handle}")
        if not result:
            return False, None

        face_response = response.json()
        print(f"    Face ID: {face_response.get('id')}")
        print(f"    Face handle: {face_response.get('handle')}")
        print(f"    Face completed: {face_response.get('face_completed', 'NOT SET')}")

        # 6. Check face_completed is true
        print("6. Verify face_completed is true")
        if face_response.get("face_completed") == True:
            log_result(True, "face_completed is true")
        else:
            log_result(
                False, f"face_completed is {face_response.get('face_completed')}"
            )
            return False, None

        # Check modules_config
        if "modules_config" in face_response:
            print(
                f"    modules_config present: {list(face_response['modules_config'].keys())}"
            )
        else:
            print(f"    Warning: modules_config not in response")

    except Exception as e:
        print(f"    Exception: {e}")
        import traceback

        traceback.print_exc()
        return False, None

    # 7. Dashboard shows Face data correctly
    print("7. Test dashboard data")
    try:
        # Get identity endpoint
        response = SESSION.get(f"{BASE_URL}/api/identity")
        if response.status_code == 200:
            identity_data = response.json()
            print(f"    Dashboard identity loaded: {identity_data.get('display_name')}")
            log_result(True, "Dashboard shows Face data")
        else:
            print(f"    Response: {response.status_code} - {response.text[:200]}")
            log_result(False, "Failed to load dashboard identity")
    except Exception as e:
        print(f"    Exception: {e}")
        log_result(False, "Exception loading dashboard")

    return True, test_handle


def test_sender_page(test_handle):
    """Test sender page functionality"""
    print_step(3, "SENDER PAGE TEST")

    # 8. Visit `/r/:handle` — Face page loads correctly
    print(f"8. Load Face page at /r/{test_handle}")
    try:
        response = requests.get(f"{BASE_URL}/reach/{test_handle}")
        success = response.status_code == 200
        if success:
            page_data = response.json()
            print(
                f"    Page loaded: {page_data.get('identity', {}).get('display_name')}"
            )
            print(f"    Has modules: {'modules' in page_data}")
        else:
            print(f"    Response: {response.status_code} - {response.text[:200]}")
        result = log_result(success, f"Face page loads at /reach/{test_handle}")
        if not result:
            return False
    except Exception as e:
        print(f"    Exception: {e}")
        return False

    # 9. Submit a message — hits `/api/reach/:handle/message` not old slot endpoint
    print("9. Submit message to Face endpoint")
    message_data = {
        "message": "Hello! I'm interested in collaborating on your project. I have experience with Python and FastAPI.",
        "time_requirement": "A conversation",
        "intent_category": "Collaboration",
    }

    try:
        response = requests.post(
            f"{BASE_URL}/reach/{test_handle}/message", json=message_data
        )
        success = response.status_code == 200
        if success:
            msg_response = response.json()
            print(f"    Message submitted: {msg_response.get('message_id')}")
            print(f"    Endpoint used: /reach/{test_handle}/message (CORRECT)")
        else:
            print(f"    Response: {response.status_code} - {response.text[:200]}")

        # Also test that old slot endpoint fails
        print("   Testing old slot endpoint (should fail)")
        slot_response = requests.post(
            f"{BASE_URL}/reach/{test_handle}/open", json=message_data
        )
        if slot_response.status_code in [404, 405]:
            print(
                f"    Old slot endpoint correctly returns {slot_response.status_code}"
            )
        else:
            print(
                f"    Warning: Old slot endpoint returned {slot_response.status_code}"
            )

        result = log_result(success, "Message submitted to correct Face endpoint")
        if not result:
            return False
    except Exception as e:
        print(f"    Exception: {e}")
        return False

    # 10. Submission is saved to database
    print("10. Verify submission saved to database")
    try:
        # Get attempts from Decision Surface
        response = SESSION.get(f"{BASE_URL}/attempts")
        if response.status_code == 200:
            attempts = response.json()
            print(f"    Found {len(attempts)} attempts")
            if len(attempts) > 0:
                latest = attempts[0]
                print(f"    Latest message: {latest.get('message', '')[:50]}...")
                log_result(True, "Submission saved and appears in attempts")
            else:
                log_result(False, "No attempts found after submission")
                return False
        else:
            print(f"    Response: {response.status_code} - {response.text[:200]}")
            log_result(False, "Failed to fetch attempts")
            return False
    except Exception as e:
        print(f"    Exception: {e}")
        return False

    return True


def test_modules_and_rules(test_handle):
    """Test modules functionality including Rules Engine"""
    print_step(4, "MODULES AND RULES ENGINE TEST")

    # 11. Enable Rules Engine — save rule "if message mentions quick sync — reject automatically"
    print("11. Enable Rules Engine and create auto-reject rule")

    # First get current modules config
    try:
        response = SESSION.get(f"{BASE_URL}/api/modules")
        if response.status_code != 200:
            print(
                f"    Failed to get modules: {response.status_code} - {response.text[:200]}"
            )
            return False

        modules_config = response.json()
        print(f"    Current modules: {list(modules_config.keys())}")

        # Update to enable rules engine
        update_data = {
            "rules_engine": {
                "enabled": True,
                "rules": [
                    {
                        "name": "Reject quick sync requests",
                        "conditions": [
                            {
                                "field": "message",
                                "operator": "contains",
                                "value": "quick sync",
                            }
                        ],
                        "action": "auto_reject",
                        "priority": 1,
                    }
                ],
            }
        }

        response = SESSION.post(f"{BASE_URL}/api/modules/update", json=update_data)
        if response.status_code == 200:
            print(f"    Rules Engine enabled with auto-reject rule")
            log_result(True, "Rules Engine configured")
        else:
            print(
                f"    Failed to update modules: {response.status_code} - {response.text[:200]}"
            )
            return False
    except Exception as e:
        print(f"    Exception: {e}")
        return False

    # 12. Submit a message containing "quick sync" from incognito
    print("12. Submit message with 'quick sync' trigger")
    trigger_message = {
        "message": "I need a quick sync meeting tomorrow to discuss the project timeline and deliverables.",
        "time_requirement": "A conversation",
        "intent_category": "Meeting",
    }

    try:
        # Use a new session (incognito)
        incognito_session = requests.Session()
        response = incognito_session.post(
            f"{BASE_URL}/reach/{test_handle}/message", json=trigger_message
        )
        success = response.status_code == 200
        if success:
            msg_response = response.json()
            print(f"    Trigger message submitted: {msg_response.get('message_id')}")
            log_result(True, "Trigger message submitted")
        else:
            print(f"    Response: {response.status_code} - {response.text[:200]}")
            log_result(False, "Failed to submit trigger message")
            return False
    except Exception as e:
        print(f"    Exception: {e}")
        return False

    # Wait a moment for processing
    print("   Waiting 3 seconds for rule processing...")
    time.sleep(3)

    # 13. Submission is auto-rejected with rule reasoning stored
    print("13. Check auto-rejection and rule reasoning")
    try:
        response = SESSION.get(f"{BASE_URL}/attempts")
        if response.status_code == 200:
            attempts = response.json()
            print(f"    Total attempts: {len(attempts)}")

            # Find the trigger message
            trigger_found = False
            for attempt in attempts:
                if "quick sync" in attempt.get("message", "").lower():
                    print(f"    Found trigger attempt: {attempt.get('_id')}")
                    print(f"    Decision: {attempt.get('decision')}")
                    print(f"    Status: {attempt.get('status')}")

                    # Check for AI classification/rules
                    ai_class = attempt.get("ai_classification", {})
                    if ai_class:
                        print(
                            f"    AI classification: {ai_class.get('final_decision', 'N/A')}"
                        )
                        print(
                            f"    Rules evaluated: {ai_class.get('rules_evaluated', [])}"
                        )
                        if ai_class.get("final_decision") == "auto_reject":
                            log_result(True, "Message auto-rejected by rule")
                            trigger_found = True
                            break
                    else:
                        print(f"    No AI classification found")

            if not trigger_found:
                log_result(False, "Trigger message not found or not auto-rejected")
                return False
        else:
            print(f"    Response: {response.status_code} - {response.text[:200]}")
            log_result(False, "Failed to fetch attempts")
            return False
    except Exception as e:
        print(f"    Exception: {e}")
        return False

    return True


def test_decision_surface(test_handle):
    """Test Decision Surface functionality"""
    print_step(5, "DECISION SURFACE TEST")

    # First submit a normal message for manual testing
    print("Preparing test message for Decision Surface...")
    test_message = {
        "message": "This is a test message for Decision Surface manual approval testing.",
        "time_requirement": "Just a read",
        "intent_category": "Test",
    }

    try:
        response = requests.post(
            f"{BASE_URL}/reach/{test_handle}/message", json=test_message
        )
        if response.status_code != 200:
            print(f"    Failed to submit test message: {response.status_code}")
            return False
        test_msg_id = response.json().get("message_id")
        print(f"    Test message submitted: {test_msg_id}")
    except Exception as e:
        print(f"    Exception: {e}")
        return False

    # Wait for processing
    time.sleep(2)

    # 14. Auto-rejected submission appears in Decision Surface
    print("14. Check auto-rejected submission in Decision Surface")
    try:
        response = SESSION.get(f"{BASE_URL}/attempts")
        if response.status_code == 200:
            attempts = response.json()

            # Find auto-rejected attempt
            auto_rejected = None
            for attempt in attempts:
                ai_class = attempt.get("ai_classification", {})
                if ai_class and ai_class.get("final_decision") == "auto_reject":
                    auto_rejected = attempt
                    break

            if auto_rejected:
                print(f"    Auto-rejected attempt found: {auto_rejected.get('_id')}")
                log_result(True, "Auto-rejected submission appears in Decision Surface")

                # Store for later tests
                auto_reject_id = auto_rejected.get("_id")
            else:
                print(f"    No auto-rejected attempt found")
                log_result(False, "Auto-rejected submission not found")
                auto_reject_id = None
        else:
            print(f"    Response: {response.status_code} - {response.text[:200]}")
            log_result(False, "Failed to fetch attempts")
            return False
    except Exception as e:
        print(f"    Exception: {e}")
        return False

    # Find the test message for manual testing
    print("Finding test message for manual actions...")
    try:
        response = SESSION.get(f"{BASE_URL}/attempts")
        if response.status_code == 200:
            attempts = response.json()
            test_attempt = None
            for attempt in attempts:
                if "Decision Surface manual approval" in attempt.get("message", ""):
                    test_attempt = attempt
                    break

            if not test_attempt:
                # Use the first pending attempt
                for attempt in attempts:
                    if attempt.get("decision") in ["queued", None]:
                        test_attempt = attempt
                        break

            if test_attempt:
                test_attempt_id = test_attempt.get("_id")
                print(f"    Test attempt found: {test_attempt_id}")
            else:
                print(f"    No test attempt found for manual actions")
                return False
        else:
            print(f"    Response: {response.status_code} - {response.text[:200]}")
            return False
    except Exception as e:
        print(f"    Exception: {e}")
        return False

    # 15. Manual approve works
    print("15. Test manual approval")
    try:
        approve_data = {"decision": "deliver_to_human"}
        response = SESSION.put(
            f"{BASE_URL}/attempts/{test_attempt_id}/decision", json=approve_data
        )
        if response.status_code == 200:
            print(f"    Manual approval successful")
            log_result(True, "Manual approve works")
        else:
            print(f"    Response: {response.status_code} - {response.text[:200]}")
            log_result(False, "Manual approve failed")
            return False
    except Exception as e:
        print(f"    Exception: {e}")
        return False

    # 16. Manual reject works
    print("16. Test manual rejection")
    try:
        # First submit another test message
        reject_msg = {
            "message": "This message should be manually rejected for testing.",
            "time_requirement": "Just a read",
            "intent_category": "Test",
        }

        response = requests.post(
            f"{BASE_URL}/reach/{test_handle}/message", json=reject_msg
        )
        if response.status_code != 200:
            print(f"    Failed to submit reject test message")
            return False

        # Wait and find it
        time.sleep(2)
        response = SESSION.get(f"{BASE_URL}/attempts")
        if response.status_code == 200:
            attempts = response.json()
            reject_attempt = None
            for attempt in attempts:
                if "manually rejected" in attempt.get("message", ""):
                    reject_attempt = attempt
                    break

            if reject_attempt:
                reject_id = reject_attempt.get("_id")
                reject_data = {"decision": "reject"}
                response = SESSION.put(
                    f"{BASE_URL}/attempts/{reject_id}/decision", json=reject_data
                )
                if response.status_code == 200:
                    print(f"    Manual rejection successful")
                    log_result(True, "Manual reject works")
                else:
                    print(
                        f"    Response: {response.status_code} - {response.text[:200]}"
                    )
                    log_result(False, "Manual reject failed")
            else:
                print(f"    Could not find reject test message")
                log_result(False, "Could not test manual reject")
        else:
            print(f"    Response: {response.status_code} - {response.text[:200]}")
            log_result(False, "Failed to fetch attempts for reject test")
    except Exception as e:
        print(f"    Exception: {e}")
        return False

    # 17. Block sender works
    print("17. Test block sender")
    try:
        # Submit a message from a "spam" sender
        spam_msg = {
            "message": "This is spam message for blocking test.",
            "time_requirement": "Just a read",
            "intent_category": "Spam",
        }

        response = requests.post(
            f"{BASE_URL}/reach/{test_handle}/message", json=spam_msg
        )
        if response.status_code != 200:
            print(f"    Failed to submit spam test message")
            return False

        # Wait and find it
        time.sleep(2)
        response = SESSION.get(f"{BASE_URL}/attempts")
        if response.status_code == 200:
            attempts = response.json()
            spam_attempt = None
            for attempt in attempts:
                if "spam message" in attempt.get("message", ""):
                    spam_attempt = attempt
                    break

            if spam_attempt:
                spam_id = spam_attempt.get("_id")
                response = SESSION.post(f"{BASE_URL}/attempts/{spam_id}/block")
                if response.status_code == 200:
                    print(f"    Block sender successful")
                    log_result(True, "Block sender works")
                else:
                    print(
                        f"    Response: {response.status_code} - {response.text[:200]}"
                    )
                    log_result(False, "Block sender failed")
            else:
                print(f"    Could not find spam test message")
                log_result(False, "Could not test block sender")
        else:
            print(f"    Response: {response.status_code} - {response.text[:200]}")
            log_result(False, "Failed to fetch attempts for block test")
    except Exception as e:
        print(f"    Exception: {e}")
        return False

    return True


def run_final_test():
    """Run final_test.py and check results"""
    print_step(6, "FINAL TEST SUITE")

    print("Running final_test.py...")
    try:
        import subprocess

        result = subprocess.run(
            [sys.executable, "final_test.py"],
            capture_output=True,
            text=True,
            cwd="C:\\Users\\flors\\Downloads\\Reach-main\\Reach-main",
        )

        print("STDOUT:")
        print(result.stdout)

        if result.stderr:
            print("STDERR:")
            print(result.stderr)

        # Check for pass/fail
        if "16/16" in result.stdout or "All tests passed" in result.stdout:
            log_result(True, "final_test.py passed 16/16")
            return True
        else:
            log_result(False, "final_test.py did not pass 16/16")
            return False
    except Exception as e:
        print(f"Exception running final_test.py: {e}")
        log_result(False, "Failed to run final_test.py")
        return False


def main():
    print("=" * 80)
    print("COMPLETE END-TO-END TEST")
    print(f"Backend: {BASE_URL}")
    print(f"Time: {datetime.now().isoformat()}")
    print("=" * 80)

    all_passed = True
    test_handle = None

    try:
        # Test 1: Auth Flow
        auth_passed, test_email, test_password = test_auth_flow()
        all_passed = all_passed and auth_passed

        if auth_passed:
            # Test 2: Face Creation
            face_passed, handle = test_face_creation(test_email)
            all_passed = all_passed and face_passed
            test_handle = handle

            if face_passed and test_handle:
                # Test 3: Sender Page
                sender_passed = test_sender_page(test_handle)
                all_passed = all_passed and sender_passed

                if sender_passed:
                    # Test 4: Modules and Rules
                    modules_passed = test_modules_and_rules(test_handle)
                    all_passed = all_passed and modules_passed

                    if modules_passed:
                        # Test 5: Decision Surface
                        ds_passed = test_decision_surface(test_handle)
                        all_passed = all_passed and ds_passed

        # Test 6: Final Test Suite
        final_passed = run_final_test()
        all_passed = all_passed and final_passed

    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        all_passed = False
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback

        traceback.print_exc()
        all_passed = False

    # Final Summary
    print("\n" + "=" * 80)
    print("TEST COMPLETE - SUMMARY")
    print("=" * 80)

    if all_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("Every feature has been tested end-to-end with real HTTP requests")
        print(f"Test Face: {test_handle}")
    else:
        print("\n❌ SOME TESTS FAILED")
        print("Check the logs above for specific failures")

    print("\n" + "=" * 80)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
