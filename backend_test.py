#!/usr/bin/env python3

import requests
import sys
import json
import uuid
from datetime import datetime


class ReachAPITester:
    def __init__(self, base_url="https://accesslayer.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.user_data = None
        self.identity_data = None
        self.slot_data = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1

        result = {
            "test": name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat(),
        }
        self.test_results.append(result)

        status = "PASS" if success else "FAIL"
        print(f"{status} - {name}")
        if details:
            print(f"    {details}")

    def run_test(
        self, name, method, endpoint, expected_status, data=None, headers=None
    ):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        test_headers = {"Content-Type": "application/json"}

        if self.token:
            test_headers["Authorization"] = f"Bearer {self.token}"

        if headers:
            test_headers.update(headers)

        try:
            if method == "GET":
                response = requests.get(url, headers=test_headers, timeout=30)
            elif method == "POST":
                response = requests.post(
                    url, json=data, headers=test_headers, timeout=30
                )
            elif method == "PUT":
                response = requests.put(
                    url, json=data, headers=test_headers, timeout=30
                )
            elif method == "DELETE":
                response = requests.delete(url, headers=test_headers, timeout=30)

            success = response.status_code == expected_status
            details = f"Status: {response.status_code}"

            if not success:
                details += f" (expected {expected_status})"
                try:
                    error_data = response.json()
                    details += f" - {error_data.get('detail', 'No error details')}"
                except:
                    details += f" - {response.text[:100]}"

            self.log_test(name, success, details)

            if success:
                try:
                    return response.json()
                except:
                    return {}
            return None

        except Exception as e:
            self.log_test(name, False, f"Exception: {str(e)}")
            return None

    def test_health_endpoints(self):
        """Test basic health endpoints"""
        print("\nTesting Health Endpoints...")

        self.run_test("API Root", "GET", "", 200)
        self.run_test("Health Check", "GET", "health", 200)

    def test_auth_flow(self):
        """Test authentication flow"""
        print("\nTesting Authentication Flow...")

        # Generate unique test user
        timestamp = datetime.now().strftime("%H%M%S")
        test_email = f"test_{timestamp}@example.com"
        test_password = "TestPass123!"
        test_name = f"Test User {timestamp}"

        # Test registration
        register_data = {
            "email": test_email,
            "password": test_password,
            "name": test_name,
        }

        result = self.run_test(
            "User Registration", "POST", "auth/register", 200, register_data
        )
        if result:
            self.token = result.get("access_token")
            self.user_data = result.get("user")

        # Test login
        login_data = {"email": test_email, "password": test_password}

        login_result = self.run_test(
            "User Login", "POST", "auth/login", 200, login_data
        )
        if login_result:
            self.token = login_result.get("access_token")

        # Test get current user
        self.run_test("Get Current User", "GET", "auth/me", 200)

        # Test invalid credentials
        invalid_login = {"email": test_email, "password": "wrongpassword"}
        self.run_test("Invalid Login", "POST", "auth/login", 401, invalid_login)

    def test_identity_management(self):
        """Test identity creation and management"""
        print("\nTesting Identity Management...")

        if not self.token:
            self.log_test("Identity Tests", False, "No auth token available")
            return

        # Test get identity (should be None initially)
        self.run_test("Get Identity (Empty)", "GET", "identity", 200)

        # Create identity
        timestamp = datetime.now().strftime("%H%M%S")
        handle = f"testuser{timestamp}"

        identity_data = {
            "handle": handle,
            "type": "person",
            "bio": "Test user for API testing",
        }

        result = self.run_test(
            "Create Identity", "POST", "identity", 200, identity_data
        )
        if result:
            self.identity_data = result

        # Test get my identity
        self.run_test("Get My Identity", "GET", "identity", 200)

        # Test get identity by handle
        if self.identity_data:
            self.run_test("Get Identity by Handle", "GET", f"identity/{handle}", 200)

        # Test duplicate handle
        self.run_test("Duplicate Handle", "POST", "identity", 400, identity_data)

    def test_slot_management(self):
        """Test slot creation and management"""
        print("\nTesting Slot Management...")

        if not self.token or not self.identity_data:
            self.log_test("Slot Tests", False, "No auth token or identity available")
            return

        # Get initial slots (should have default 'open' slot)
        slots_result = self.run_test("Get Initial Slots", "GET", "slots", 200)

        # Create new slot
        slot_data = {
            "name": "business",
            "description": "Business inquiries and partnerships",
            "visibility": "public",
        }

        result = self.run_test("Create Slot", "POST", "slots", 200, slot_data)
        if result:
            self.slot_data = result

        # Get all slots
        self.run_test("Get All Slots", "GET", "slots", 200)

        # Get specific slot
        if self.slot_data:
            slot_id = self.slot_data["id"]
            self.run_test("Get Specific Slot", "GET", f"slots/{slot_id}", 200)

            # Update slot
            update_data = {"description": "Updated business inquiries description"}
            self.run_test("Update Slot", "PUT", f"slots/{slot_id}", 200, update_data)

            # Update slot policy
            policy_data = {
                "conditions": [{"type": "intent", "value": "business"}],
                "actions": {"default": "queue"},
                "fallback": "queue",
                "payment_amount": 25.0,
            }
            self.run_test(
                "Update Slot Policy", "PUT", f"slots/{slot_id}/policy", 200, policy_data
            )

        # Test duplicate slot name
        self.run_test("Duplicate Slot Name", "POST", "slots", 400, slot_data)

    def test_public_reach_endpoints(self):
        """Test public reach endpoints"""
        print("\nTesting Public Reach Endpoints...")

        if not self.identity_data:
            self.log_test("Public Reach Tests", False, "No identity available")
            return

        handle = self.identity_data["handle"]

        # Test get public reach page
        self.run_test("Get Public Reach Page", "GET", f"reach/{handle}", 200)

        # Test get public slot (default 'open' slot)
        self.run_test("Get Public Slot", "GET", f"reach/{handle}/open", 200)

        # Test submit reach attempt
        reach_data = {
            "intent": "business",
            "reason": "Testing the reach API functionality",
            "message": "This is a test message for API validation",
            "sender_email": "tester@example.com",
            "sender_name": "API Tester",
        }

        result = self.run_test(
            "Submit Reach Attempt", "POST", f"reach/{handle}/open", 200, reach_data
        )

        # Test invalid handle
        self.run_test("Invalid Handle", "GET", "reach/nonexistent", 404)

        # Test invalid slot
        self.run_test("Invalid Slot", "GET", f"reach/{handle}/nonexistent", 404)

    def test_reach_attempts_management(self):
        """Test reach attempts management"""
        print("\nTesting Reach Attempts Management...")

        if not self.token:
            self.log_test("Reach Attempts Tests", False, "No auth token available")
            return

        # Get reach attempts
        attempts_result = self.run_test("Get Reach Attempts", "GET", "attempts", 200)

        # If we have attempts, test getting specific attempt
        if attempts_result and len(attempts_result) > 0:
            attempt_id = attempts_result[0]["id"]
            self.run_test("Get Specific Attempt", "GET", f"attempts/{attempt_id}", 200)

            # Test updating attempt decision
            self.run_test(
                "Update Attempt Decision",
                "PUT",
                f"attempts/{attempt_id}/decision?decision=deliver_to_human",
                200,
            )

    def test_stats_endpoint(self):
        """Test stats endpoint"""
        print("\nTesting Stats Endpoint...")

        if not self.token:
            self.log_test("Stats Test", False, "No auth token available")
            return

        self.run_test("Get Stats", "GET", "stats", 200)

    def test_payment_endpoints(self):
        """Test payment endpoints (basic structure)"""
        print("\nTesting Payment Endpoints...")

        # Note: We can't fully test payments without a real reach attempt that requires payment
        # But we can test the endpoint structure

        # Test payment status with invalid session
        self.run_test(
            "Payment Status (Invalid)", "GET", "payments/status/invalid_session", 404
        )

    def run_all_tests(self):
        """Run all test suites"""
        print("Starting Reach API Tests")
        print(f"Base URL: {self.base_url}")
        print("=" * 50)

        try:
            self.test_health_endpoints()
            self.test_auth_flow()
            self.test_identity_management()
            self.test_slot_management()
            self.test_public_reach_endpoints()
            self.test_reach_attempts_management()
            self.test_stats_endpoint()
            self.test_payment_endpoints()

        except Exception as e:
            print(f"\nTest suite failed with exception: {e}")

        # Print summary
        print("\n" + "=" * 50)
        print(f"Test Summary: {self.tests_passed}/{self.tests_run} passed")

        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return 0
        else:
            print(f"{self.tests_run - self.tests_passed} tests failed")
            return 1

    def get_failed_tests(self):
        """Get list of failed tests"""
        return [test for test in self.test_results if not test["success"]]


def main():
    tester = ReachAPITester()
    exit_code = tester.run_all_tests()

    # Save detailed results
    with open("test_reports/backend_test_results.json", "w") as f:
        json.dump(
            {
                "summary": {
                    "total_tests": tester.tests_run,
                    "passed_tests": tester.tests_passed,
                    "failed_tests": tester.tests_run - tester.tests_passed,
                    "success_rate": (tester.tests_passed / tester.tests_run * 100)
                    if tester.tests_run > 0
                    else 0,
                },
                "failed_tests": tester.get_failed_tests(),
                "all_results": tester.test_results,
            },
            f,
            indent=2,
        )

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
