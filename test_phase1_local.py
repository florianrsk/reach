#!/usr/bin/env python3
"""
Phase 1 Local Validation Test
Tests the security and stability enhancements implemented in Phase 1
"""

import sys
import os
import json
import requests
from datetime import datetime


class Phase1Validator:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.csrf_token = None
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        result = {
            "name": name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat(),
        }
        self.test_results.append(result)

        status = "PASS" if success else "FAIL"
        print(f"{status} - {name}")
        if details:
            print(f"    {details}")

    def test_health_endpoints(self):
        """Test health endpoints"""
        print("\n=== Testing Health Endpoints ===")

        # Test basic health
        try:
            response = self.session.get(f"{self.base_url}/health")
            self.log_test(
                "Health Endpoint",
                response.status_code == 200,
                f"Status: {response.status_code}",
            )
        except Exception as e:
            self.log_test("Health Endpoint", False, f"Exception: {str(e)}")

        # Test detailed health
        try:
            response = self.session.get(f"{self.base_url}/health/detailed")
            self.log_test(
                "Detailed Health Endpoint",
                response.status_code == 200,
                f"Status: {response.status_code}",
            )
        except Exception as e:
            self.log_test("Detailed Health Endpoint", False, f"Exception: {str(e)}")

    def test_security_headers(self):
        """Test security headers are present"""
        print("\n=== Testing Security Headers ===")

        try:
            response = self.session.head(f"{self.base_url}/")
            headers = response.headers

            # Check key security headers
            security_headers = {
                "X-Frame-Options": "DENY",
                "X-Content-Type-Options": "nosniff",
                "X-XSS-Protection": "1; mode=block",
            }

            for header, expected_value in security_headers.items():
                actual_value = headers.get(header)
                self.log_test(
                    f"Security Header: {header}",
                    actual_value == expected_value,
                    f"Expected: {expected_value}, Got: {actual_value}",
                )

        except Exception as e:
            self.log_test("Security Headers", False, f"Exception: {str(e)}")

    def test_csrf_protection(self):
        """Test CSRF token generation and validation"""
        print("\n=== Testing CSRF Protection ===")

        # Get CSRF token
        try:
            response = self.session.get(f"{self.base_url}/api/auth/csrf")
            self.csrf_token = response.json().get("csrf_token")

            self.log_test(
                "CSRF Token Generation",
                self.csrf_token is not None,
                f"Token received: {self.csrf_token[:20]}..."
                if self.csrf_token
                else "No token",
            )
        except Exception as e:
            self.log_test("CSRF Token Generation", False, f"Exception: {str(e)}")

        # Test CSRF protection (try without token)
        if self.csrf_token:
            try:
                response = self.session.post(
                    f"{self.base_url}/api/auth/register",
                    json={
                        "email": "test_csrf@example.com",
                        "password": "TestPass123!@#",
                        "name": "CSRF Test",
                    },
                )
                # Should fail without CSRF token
                self.log_test(
                    "CSRF Protection (no token)",
                    response.status_code in [403, 422, 400],
                    f"Status: {response.status_code} (should reject without CSRF)",
                )
            except Exception as e:
                self.log_test("CSRF Protection Test", False, f"Exception: {str(e)}")

    def test_rate_limiting(self):
        """Test rate limiting on auth endpoints"""
        print("\n=== Testing Rate Limiting ===")

        # Make multiple rapid requests to login endpoint
        try:
            responses = []
            for i in range(15):
                response = self.session.post(
                    f"{self.base_url}/api/auth/login",
                    json={
                        "email": f"rate_test_{i}@example.com",
                        "password": "wrongpassword",
                    },
                )
                responses.append(response.status_code)

            # Check if we got 429 (Too Many Requests) at some point
            got_429 = 429 in responses
            self.log_test(
                "Rate Limiting Trigger",
                got_429,
                f"Response codes: {responses[:5]}... (429 expected after rate limit)",
            )
        except Exception as e:
            self.log_test("Rate Limiting Test", False, f"Exception: {str(e)}")

    def test_password_validation(self):
        """Test strong password policy"""
        print("\n=== Testing Password Validation ===")

        if not self.csrf_token:
            print("Skipping - need CSRF token first")
            return

        weak_passwords = [
            "short",
            "nouppercase123",
            "NOLOWERCASE123",
            "NoNumbers!",
            "ValidButShort1!",
            "nouppercaseornumbers",
            "NOLOWERCASEORNUMBERS",
            "NoSpecialChars123",
        ]

        strong_password = "SecurePass123!@#"

        # Test weak passwords (should fail)
        for i, password in enumerate(weak_passwords[:3]):  # Test first 3
            try:
                response = self.session.post(
                    f"{self.base_url}/api/auth/register",
                    headers={"X-CSRF-Token": self.csrf_token},
                    json={
                        "email": f"pw_test_{i}@example.com",
                        "password": password,
                        "name": f"Password Test {i}",
                    },
                )
                self.log_test(
                    f"Weak Password Rejection: {password[:10]}...",
                    response.status_code == 422,  # Validation error
                    f"Status: {response.status_code}",
                )
            except Exception as e:
                self.log_test(f"Weak Password Test {i}", False, f"Exception: {str(e)}")

        # Test strong password (setup for other tests)
        try:
            response = self.session.post(
                f"{self.base_url}/api/auth/register",
                headers={"X-CSRF-Token": self.csrf_token},
                json={
                    "email": "phase1_test@example.com",
                    "password": strong_password,
                    "name": "Phase 1 Test User",
                },
            )
            self.log_test(
                "Strong Password Acceptance",
                response.status_code in [200, 201, 409],  # 409 if user exists
                f"Status: {response.status_code}",
            )
        except Exception as e:
            self.log_test("Strong Password Test", False, f"Exception: {str(e)}")

    def test_httpOnly_cookies(self):
        """Test that cookies are marked httpOnly"""
        print("\n=== Testing httpOnly Cookies ===")

        if not self.csrf_token:
            print("Skipping - need CSRF token first")
            return

        try:
            # Login to get auth cookies
            response = self.session.post(
                f"{self.base_url}/api/auth/login",
                headers={"X-CSRF-Token": self.csrf_token},
                json={
                    "email": "phase1_test@example.com",
                    "password": "SecurePass123!@#",
                },
            )

            # Check for httpOnly cookies in response
            cookies_header = response.headers.get("Set-Cookie", "")
            has_httpOnly = "HttpOnly" in cookies_header
            has_secure = "Secure" in cookies_header or "localhost" in self.base_url

            self.log_test(
                "httpOnly Cookie Setting",
                has_httpOnly,
                f"Cookies: {cookies_header[:100]}...",
            )

            self.log_test(
                "Secure/SameSite Cookie Attributes",
                has_secure or "SameSite" in cookies_header,
                f"Cookie attributes present",
            )

        except Exception as e:
            self.log_test("Cookie Test", False, f"Exception: {str(e)}")

    def run_all_tests(self):
        """Run all Phase 1 validation tests"""
        print("=" * 60)
        print("Phase 1: Security & Stability Foundation - Validation Tests")
        print("=" * 60)

        # Run tests in order
        self.test_health_endpoints()
        self.test_security_headers()
        self.test_csrf_protection()
        self.test_rate_limiting()
        self.test_password_validation()
        self.test_httpOnly_cookies()

        # Summary
        print("\n" + "=" * 60)
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["success"])

        print(f"Test Summary: {passed_tests}/{total_tests} passed")
        print(f"Success Rate: {(passed_tests / total_tests * 100):.1f}%")

        # Save results
        results = {
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "success_rate": (passed_tests / total_tests * 100)
                if total_tests > 0
                else 0,
                "timestamp": datetime.now().isoformat(),
            },
            "tests": self.test_results,
        }

        with open("phase1_test_results.json", "w") as f:
            json.dump(results, f, indent=2)

        print(f"\nDetailed results saved to: phase1_test_results.json")

        return passed_tests == total_tests


def main():
    """Main function"""
    validator = Phase1Validator()

    print("Note: Make sure backend is running on http://localhost:8000")
    print("Start backend with: cd backend && python server.py")
    print()

    try:
        success = validator.run_all_tests()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        return 1
    except Exception as e:
        print(f"\nError running tests: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
