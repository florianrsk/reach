#!/usr/bin/env python3
"""Test cookie-based authentication"""

import requests
import json

BASE_URL = "http://localhost:8001"


def test_cookie_auth():
    """Test registration and login with cookies"""

    # Test data
    test_email = f"test_{hash('test')}@example.com"
    test_password = "SecurePass123!"
    test_name = "Test User"

    print("Testing cookie-based authentication...")

    # Create a session to maintain cookies
    session = requests.Session()

    # Test registration
    print("1. Testing registration...")
    try:
        reg_data = {"email": test_email, "password": test_password, "name": test_name}

        response = session.post(
            f"{BASE_URL}/api/auth/register",
            json=reg_data,
            headers={"Content-Type": "application/json"},
        )

        if response.status_code == 200:
            print(f"   ✓ Registration successful: {response.status_code}")
            result = response.json()
            print(f"   User: {result['user']['email']}")
            print(f"   CSRF token in response: {'csrf_token' in result}")

            # Check cookies
            cookies = session.cookies.get_dict()
            print(f"   Cookies set: {list(cookies.keys())}")
            print(f"   Has access_token cookie: {'access_token' in cookies}")
            print(f"   Has csrf_token cookie: {'csrf_token' in cookies}")
        else:
            print(f"   ✗ Registration failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except Exception as e:
        print(f"   ✗ Registration error: {e}")
        return False

    # Test getting current user (should work with cookies)
    print("\n2. Testing get current user with cookies...")
    try:
        response = session.get(f"{BASE_URL}/api/auth/me")

        if response.status_code == 200:
            print(f"   ✓ Get current user successful: {response.status_code}")
            user = response.json()
            print(f"   User email matches: {user['email'] == test_email}")
        else:
            print(f"   ✗ Get current user failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except Exception as e:
        print(f"   ✗ Get current user error: {e}")
        return False

    # Test logout
    print("\n3. Testing logout...")
    try:
        response = session.post(f"{BASE_URL}/api/auth/logout")

        if response.status_code == 200:
            print(f"   ✓ Logout successful: {response.status_code}")

            # Check cookies were cleared
            cookies = session.cookies.get_dict()
            print(f"   Cookies after logout: {cookies}")
        else:
            print(f"   ✗ Logout failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except Exception as e:
        print(f"   ✗ Logout error: {e}")
        return False

    # Test getting current user after logout (should fail)
    print("\n4. Testing get current user after logout...")
    try:
        response = session.get(f"{BASE_URL}/api/auth/me")

        if response.status_code == 401:
            print(f"   ✓ Correctly rejected after logout: {response.status_code}")
        else:
            print(f"   ✗ Should have been rejected: {response.status_code}")
            return False

    except Exception as e:
        print(f"   ✗ Get current user after logout error: {e}")
        return False

    print("\n✅ All cookie authentication tests passed!")
    return True


def test_password_validation():
    """Test password validation rules"""

    print("\nTesting password validation...")

    test_cases = [
        ("short", "Password must be at least 12 characters long"),
        ("nouppercase123!", "Password must contain at least one uppercase letter"),
        ("NOLOWERCASE123!", "Password must contain at least one lowercase letter"),
        ("NoNumbers!", "Password must contain at least one number"),
        ("NoSpecial123", "Password must contain at least one special character"),
        ("password123!", "Password is too common"),
        ("SecurePass123!", None),  # Should pass
    ]

    session = requests.Session()

    for password, expected_error in test_cases:
        test_email = f"test_{hash(password)}@example.com"

        reg_data = {"email": test_email, "password": password, "name": "Test User"}

        try:
            response = session.post(
                f"{BASE_URL}/api/auth/register",
                json=reg_data,
                headers={"Content-Type": "application/json"},
            )

            if expected_error:
                if response.status_code == 422:
                    error_detail = response.json().get("detail", [{}])[0].get("msg", "")
                    if expected_error in error_detail:
                        print(
                            f"   ✓ Correctly rejected '{password[:10]}...': {expected_error}"
                        )
                    else:
                        print(
                            f"   ✗ Wrong error for '{password[:10]}...': {error_detail}"
                        )
                        return False
                else:
                    print(
                        f"   ✗ Should have rejected '{password[:10]}...' but got {response.status_code}"
                    )
                    return False
            else:
                if response.status_code == 200:
                    print(f"   ✓ Accepted valid password")
                else:
                    print(
                        f"   ✗ Should have accepted valid password but got {response.status_code}: {response.text}"
                    )
                    return False

        except Exception as e:
            print(f"   ✗ Error testing password '{password[:10]}...': {e}")
            return False

    print("✅ All password validation tests passed!")
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Cookie Authentication & Password Validation")
    print("=" * 60)

    # Note: This test requires the backend to be running
    print("\nNote: Make sure the backend is running on http://localhost:8001")
    print("Run: cd backend && uvicorn server:app --reload --port 8001")

    input("\nPress Enter to start tests...")

    try:
        # Test password validation first (doesn't require backend)
        if test_password_validation():
            # Test cookie auth (requires backend)
            test_cookie_auth()
    except requests.exceptions.ConnectionError:
        print("\n❌ Cannot connect to backend. Please start the server first.")
        print("Run: cd backend && uvicorn server:app --reload --port 8001")
    except Exception as e:
        print(f"\n❌ Test error: {e}")
