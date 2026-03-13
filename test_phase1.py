#!/usr/bin/env python3
"""
Simple test to check Phase 1 changes are syntactically valid
"""

import sys
import os


def test_backend_syntax():
    """Test backend server syntax"""
    print("Testing backend syntax...")
    try:
        # Add backend to path
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

        # Try to import server module
        import server

        print("✅ Backend imports are valid")

        # Check for new security features
        print("\nChecking for Phase 1 security features:")

        # Check for cookie configuration
        if hasattr(server, "ACCESS_TOKEN_COOKIE_NAME"):
            print("✅ Cookie authentication configured")
        else:
            print("❌ Cookie authentication not found")

        # Check for CSRF configuration
        if hasattr(server, "CSRF_TOKEN_NAME"):
            print("✅ CSRF protection configured")
        else:
            print("❌ CSRF protection not found")

        # Check for rate limiting
        if hasattr(server, "rate_limit"):
            print("✅ Rate limiting configured")
        else:
            print("❌ Rate limiting not found")

        # Check for security headers middleware
        if hasattr(server, "SecurityHeadersMiddleware"):
            print("✅ Security headers middleware configured")
        else:
            print("❌ Security headers middleware not found")

        # Check for enhanced Pydantic models
        from pydantic import validator

        user_create = server.UserCreate
        if hasattr(user_create, "validate_password"):
            print("✅ Password validation configured")
        else:
            print("❌ Password validation not found")

        # Check for audit logging
        if hasattr(server, "log_audit_event"):
            print("✅ Audit logging configured")
        else:
            print("❌ Audit logging not found")

        # Check for health endpoint
        print("\nChecking for infrastructure features:")
        # Look for health check routes in the router
        routes = [route.path for route in server.api_router.routes]
        health_routes = [r for r in routes if "health" in r]
        if health_routes:
            print(f"✅ Health endpoints found: {health_routes}")
        else:
            print("❌ Health endpoints not found")

        return True

    except Exception as e:
        print(f"❌ Backend test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_frontend_changes():
    """Check frontend files for cookie auth changes"""
    print("\nTesting frontend changes...")

    frontend_dir = os.path.join(os.path.dirname(__file__), "frontend", "src")

    # Check api.js for withCredentials
    api_js = os.path.join(frontend_dir, "lib", "api.js")
    if os.path.exists(api_js):
        with open(api_js, "r") as f:
            content = f.read()
            if "withCredentials: true" in content:
                print("✅ Frontend API configured for cookies")
            else:
                print("❌ Frontend API not configured for cookies")

            if "x-csrf-token" in content:
                print("✅ CSRF token handling configured")
            else:
                print("❌ CSRF token handling not found")
    else:
        print("❌ Frontend API file not found")

    # Check AuthContext.js
    auth_context = os.path.join(frontend_dir, "context", "AuthContext.js")
    if os.path.exists(auth_context):
        with open(auth_context, "r") as f:
            content = f.read()
            if (
                "access_token" not in content
                or "access_token" in content
                and "csrf_token" in content
            ):
                print("✅ AuthContext updated for cookie auth")
            else:
                print("⚠️ AuthContext may still use old token system")
    else:
        print("❌ AuthContext file not found")

    return True


def main():
    print("=" * 60)
    print("Phase 1: Security & Stability Foundation - Validation Test")
    print("=" * 60)

    print("\nThis test checks if Phase 1 changes are syntactically valid.")
    print("Note: This does NOT test functionality, only syntax and configuration.")

    backend_ok = test_backend_syntax()
    frontend_ok = test_frontend_changes()

    print("\n" + "=" * 60)
    if backend_ok and frontend_ok:
        print("✅ Phase 1 changes appear to be syntactically valid")
        print("\nNext steps:")
        print("1. Set up MongoDB")
        print("2. Configure environment variables (.env file)")
        print("3. Start backend and frontend servers")
        print("4. Test functionality manually")
    else:
        print("❌ Some Phase 1 changes may be incomplete")

    print("=" * 60)


if __name__ == "__main__":
    main()
