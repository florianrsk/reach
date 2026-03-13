#!/usr/bin/env python3
"""
Simple test script that tests against already running servers
"""

import sys
import os
import json
import time
import requests
import socket
from datetime import datetime


class SimpleTestRunner:
    def __init__(self):
        self.backend_url = "http://localhost:8001"
        self.frontend_url = "http://localhost:3000"
        self.test_results = []

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test result"""
        result = {
            "name": name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat(),
        }
        self.test_results.append(result)

        if success:
            print(f"[PASS] - {name}")
        else:
            print(f"[FAIL] - {name}")

        if details:
            print(f"   {details}")

    def check_port(self, host: str, port: int, timeout: float = 5.0) -> bool:
        """Check if a port is open"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except:
            return False

    def run_backend_tests(self):
        """Run all backend API tests"""
        print("\n" + "=" * 60)
        print("BACKEND TESTS")
        print("=" * 60)

        # Check if backend is running
        if not self.check_port("localhost", 8001):
            print("[FAIL] Backend server not running on port 8001")
            print(
                "Start it with: cd backend && python -m uvicorn server:app --host 0.0.0.0 --port 8001"
            )
            return None

        session = requests.Session()
        csrf_token = None

        # Test 1: Health check
        try:
            response = session.get(f"{self.backend_url}/api/health", timeout=10)
            success = response.status_code == 200
            data = response.json()
            details = f"Status: {response.status_code}, MongoDB: {data.get('mongo', 'unknown')}"
            self.log_test("Health check", success, details)
        except Exception as e:
            self.log_test("Health check", False, f"Exception: {str(e)}")
            return None  # Can't continue if health check fails

        # Test 2: CSRF token
        try:
            response = session.get(f"{self.backend_url}/api/auth/csrf", timeout=10)
            success = response.status_code == 200
            if success:
                csrf_token = response.cookies.get("csrf_token")
                details = (
                    f"CSRF token obtained: {csrf_token[:20]}..."
                    if csrf_token
                    else "No CSRF token in cookies"
                )
            else:
                details = f"Status: {response.status_code}"
            self.log_test("CSRF token", success, details)
        except Exception as e:
            self.log_test("CSRF token", False, f"Exception: {str(e)}")

        # Test 3: Security headers
        try:
            response = session.get(f"{self.backend_url}/api/health", timeout=10)
            headers = response.headers

            security_headers = {
                "X-Frame-Options": headers.get("X-Frame-Options"),
                "Content-Security-Policy": headers.get("Content-Security-Policy"),
                "X-Content-Type-Options": headers.get("X-Content-Type-Options"),
            }

            # Check if headers are present
            missing = [k for k, v in security_headers.items() if not v]
            success = len(missing) == 0
            details = (
                f"Headers: {security_headers}" if success else f"Missing: {missing}"
            )
            self.log_test("Security headers", success, details)
        except Exception as e:
            self.log_test("Security headers", False, f"Exception: {str(e)}")

        # Test 4: Registration
        test_email = f"test_{int(time.time())}@example.com"
        test_password = "TestPassword123!"
        test_name = "Test User"

        try:
            headers = {}
            if csrf_token:
                headers["X-CSRF-Token"] = csrf_token

            response = session.post(
                f"{self.backend_url}/api/auth/register",
                json={
                    "email": test_email,
                    "password": test_password,
                    "name": test_name,
                },
                headers=headers,
                timeout=10,
            )

            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            self.log_test("User registration", success, details)

            # Save cookies for next tests
            if success:
                session.cookies.update(response.cookies)

        except Exception as e:
            self.log_test("User registration", False, f"Exception: {str(e)}")

        # Test 5: Login (with same user)
        try:
            headers = {}
            if csrf_token:
                headers["X-CSRF-Token"] = csrf_token

            response = session.post(
                f"{self.backend_url}/api/auth/login",
                json={"email": test_email, "password": test_password},
                headers=headers,
                timeout=10,
            )

            success = response.status_code == 200
            has_cookie = "session" in response.cookies
            details = f"Status: {response.status_code}, Cookie set: {has_cookie}"
            self.log_test("User login", success, details)

            # Update cookies
            if success:
                session.cookies.update(response.cookies)

        except Exception as e:
            self.log_test("User login", False, f"Exception: {str(e)}")

        # Test 6: Session persistence
        try:
            response = session.get(f"{self.backend_url}/api/auth/me", timeout=10)
            success = response.status_code == 200
            if success:
                user_data = response.json()
                details = f"Status: {response.status_code}, User: {user_data.get('email', 'unknown')}"
            else:
                details = f"Status: {response.status_code}"
            self.log_test("Session persistence", success, details)
        except Exception as e:
            self.log_test("Session persistence", False, f"Exception: {str(e)}")

        # Test 7: CORS headers
        try:
            response = session.get(
                f"{self.backend_url}/api/health",
                headers={"Origin": "http://localhost:3000"},
                timeout=10,
            )

            cors_headers = {
                "Access-Control-Allow-Origin": response.headers.get(
                    "Access-Control-Allow-Origin"
                ),
                "Access-Control-Allow-Credentials": response.headers.get(
                    "Access-Control-Allow-Credentials"
                ),
            }

            success = (
                cors_headers["Access-Control-Allow-Origin"] == "http://localhost:3000"
                and cors_headers["Access-Control-Allow-Credentials"] == "true"
            )
            details = f"CORS headers: {cors_headers}"
            self.log_test("CORS configuration", success, details)
        except Exception as e:
            self.log_test("CORS configuration", False, f"Exception: {str(e)}")

        # Test 8: Rate limiting (simulate failed logins)
        try:
            # Try multiple failed logins
            failed_attempts = 0
            for i in range(12):  # Try 12 times (should trigger 429 after 10)
                try:
                    response = session.post(
                        f"{self.backend_url}/api/auth/login",
                        json={
                            "email": "wrong@example.com",
                            "password": "wrongpassword",
                        },
                        headers={"X-CSRF-Token": csrf_token} if csrf_token else {},
                        timeout=5,
                    )

                    if response.status_code == 429:
                        failed_attempts = i + 1
                        break

                except:
                    pass

            success = failed_attempts >= 10  # Should trigger after 10 attempts
            details = f"Rate limit triggered after ~{failed_attempts} attempts"
            self.log_test("Rate limiting", success, details)
        except Exception as e:
            self.log_test("Rate limiting", False, f"Exception: {str(e)}")

        # Test 9: Handle creation
        test_handle = f"testuser{int(time.time())}"
        try:
            headers = {}
            if csrf_token:
                headers["X-CSRF-Token"] = csrf_token

            response = session.post(
                f"{self.backend_url}/api/identity",
                json={"handle": test_handle, "bio": "Test user bio"},
                headers=headers,
                timeout=10,
            )

            success = response.status_code == 200
            details = f"Status: {response.status_code}, Handle: {test_handle}"
            self.log_test("Handle creation", success, details)
        except Exception as e:
            self.log_test("Handle creation", False, f"Exception: {str(e)}")

        # Test 10: Duplicate handle error
        try:
            headers = {}
            if csrf_token:
                headers["X-CSRF-Token"] = csrf_token

            response = session.post(
                f"{self.backend_url}/api/identity",
                json={
                    "handle": test_handle,  # Same handle as before
                    "bio": "Another bio",
                },
                headers=headers,
                timeout=10,
            )

            # Should fail with 400 or 409
            success = response.status_code in [400, 409, 422]
            details = f"Status: {response.status_code} (expected 400/409/422)"
            self.log_test("Duplicate handle error", success, details)
        except Exception as e:
            self.log_test("Duplicate handle error", False, f"Exception: {str(e)}")

        return session

    def run_frontend_tests(self):
        """Run frontend smoke tests using requests (basic checks)"""
        print("\n" + "=" * 60)
        print("FRONTEND SMOKE TESTS")
        print("=" * 60)

        # Check if frontend is running
        if not self.check_port("localhost", 3000):
            print("[WARN] Frontend server not running on port 3000")
            print("Start it with: cd frontend && npm start")
            print("Skipping frontend tests...")
            return

        # Note: Full Playwright tests would require Playwright installation
        # These are basic smoke tests to verify pages load

        # Test 1: Landing page
        try:
            response = requests.get(f"{self.frontend_url}/", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            self.log_test("Landing page loads", success, details)
        except Exception as e:
            self.log_test("Landing page loads", False, f"Exception: {str(e)}")

        # Test 2: Register page
        try:
            response = requests.get(f"{self.frontend_url}/register", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            self.log_test("Register page loads", success, details)
        except Exception as e:
            self.log_test("Register page loads", False, f"Exception: {str(e)}")

        # Test 3: Login page
        try:
            response = requests.get(f"{self.frontend_url}/login", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            self.log_test("Login page loads", success, details)
        except Exception as e:
            self.log_test("Login page loads", False, f"Exception: {str(e)}")

        # Note: Dashboard test would require authentication
        # We'll do a basic check that the page exists
        try:
            response = requests.get(
                f"{self.frontend_url}/dashboard", timeout=10, allow_redirects=False
            )
            # Should redirect to login if not authenticated
            success = response.status_code in [200, 302, 401]
            details = f"Status: {response.status_code} (may redirect to login)"
            self.log_test("Dashboard page exists", success, details)
        except Exception as e:
            self.log_test("Dashboard page exists", False, f"Exception: {str(e)}")

        print("\n[NOTE] Full frontend E2E tests require Playwright installation.")
        print("       Run: pip install playwright && playwright install")

    def run_all_tests(self):
        """Run all tests"""
        print("=" * 60)
        print("COMPREHENSIVE PHASE 1 TEST SUITE")
        print("=" * 60)
        print("Note: This test assumes servers are already running.")
        print("Backend: http://localhost:8001")
        print("Frontend: http://localhost:3000")
        print()

        # Run backend tests
        self.run_backend_tests()

        # Run frontend tests
        self.run_frontend_tests()

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)

        passed = sum(1 for r in self.test_results if r["success"])
        total = len(self.test_results)

        print(f"\n[RESULTS] {passed}/{total} tests passed")

        if passed == total:
            print("[SUCCESS] ALL TESTS PASSED!")
        else:
            print("\nFailed tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(
                        f"  [FAIL] {result['name']}: {result.get('details', 'No details')}"
                    )

        # Save results to file
        with open("test_results.json", "w") as f:
            json.dump(self.test_results, f, indent=2)

        print(f"\n[INFO] Detailed results saved to: test_results.json")


def main():
    """Main entry point"""
    runner = SimpleTestRunner()

    try:
        runner.run_all_tests()
    except KeyboardInterrupt:
        print("\n\n[WARN] Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
