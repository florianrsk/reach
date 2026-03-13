import asyncio
import requests
import time
import subprocess
import sys
import os
from threading import Thread

BASE_URL = "http://localhost:8000"
server_process = None


def start_server():
    """Start the backend server in a subprocess"""
    global server_process
    print("Starting backend server...")

    # Change to backend directory
    backend_dir = os.path.join(os.path.dirname(__file__), "Reach-main", "backend")

    # Start server
    server_process = subprocess.Popen(
        [
            sys.executable,
            "-c",
            """
import server
import uvicorn
uvicorn.run(server.app, host='0.0.0.0', port=8000, log_level='warning')
""",
        ],
        cwd=backend_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for server to start
    print("Waiting for server to start...")
    for i in range(30):  # Wait up to 30 seconds
        try:
            response = requests.get(f"{BASE_URL}/api/health", timeout=1)
            if response.status_code == 200:
                print("Server started successfully!")
                return True
        except:
            pass
        time.sleep(1)

    print("Server failed to start")
    return False


def stop_server():
    """Stop the backend server"""
    global server_process
    if server_process:
        print("Stopping server...")
        server_process.terminate()
        server_process.wait()
        print("Server stopped")


def test_auth():
    """Test authentication flow"""
    print("\n=== Testing Auth Flow ===")

    # Register a new user
    email = f"test{int(time.time())}@example.com"
    password = "TestPassword123!"

    register_data = {"email": email, "password": password, "name": "Test User"}

    print(f"1. Registering user: {email}")
    response = requests.post(f"{BASE_URL}/api/auth/register", json=register_data)
    if response.status_code != 200:
        print(f"   Register failed: {response.status_code} - {response.text}")
        return None

    print("   Registration successful")

    # Login
    print("2. Logging in...")
    login_data = {"email": email, "password": password}
    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    if response.status_code != 200:
        print(f"   Login failed: {response.status_code} - {response.text}")
        return None

    print("   Login successful")

    # Get cookies for authentication
    cookies = response.cookies
    print(f"   Got cookies: {list(cookies.keys())}")

    return cookies


def test_face_creation(auth_cookies):
    """Test Face creation"""
    print("\n=== Testing Face Creation ===")

    cookies = auth_cookies
    handle = f"complete_test_{int(time.time())}"

    face_data = {
        "handle": handle,
        "display_name": "Complete Test User",
        "headline": "Software Developer with backend systems and API design experience",
        "current_focus": "Currently focused on building scalable microservices architecture and improving system reliability through comprehensive testing and monitoring. This text is definitely more than 20 characters long.",
        "availability_signal": "I check my messages daily and typically respond within 24 hours for urgent matters. Regular updates weekly.",
        "prompt": "What brings you to my page today? Please share what you're working on and how I might be able to help or collaborate.",
        "photo_url": "https://example.com/profile.jpg",
        "links": [
            {"label": "GitHub", "url": "https://github.com/testuser"},
            {"label": "LinkedIn", "url": "https://linkedin.com/in/testuser"},
        ],
    }

    print(f"3. Creating Face with handle: {handle}")
    response = requests.post(
        f"{BASE_URL}/api/identity", json=face_data, cookies=cookies
    )
    if response.status_code != 200:
        print(f"   Face creation failed: {response.status_code} - {response.text}")
        return None

    print("   Face creation successful!")

    # Verify Face was created
    print("4. Verifying Face creation...")
    response = requests.get(f"{BASE_URL}/api/identity", cookies=cookies)
    if response.status_code == 200:
        identity = response.json()
        print(f"   Identity handle: {identity.get('handle')}")
        print(f"   Face completed: {identity.get('face_completed')}")
        if identity.get("handle") == handle.lower() and identity.get("face_completed"):
            print("   Face verified in database!")
            return handle
        else:
            print(
                f"   Face not properly saved: handle={identity.get('handle')}, completed={identity.get('face_completed')}"
            )
    else:
        print(f"   Failed to get identity: {response.status_code} - {response.text}")

    return None


def test_public_page(handle):
    """Test public Face page"""
    print("\n=== Testing Public Face Page ===")

    print(f"5. Testing public page for handle: {handle}")

    # Wait a moment for database to sync
    time.sleep(2)

    response = requests.get(f"{BASE_URL}/api/reach/{handle}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Public page successful!")
        print(f"   Handle: {data.get('identity', {}).get('handle')}")
        print(f"   Display name: {data.get('identity', {}).get('display_name')}")
        print(f"   Has modules config: {'modules' in data}")
        return True
    else:
        print(f"   Public page failed: {response.status_code} - {response.text}")
        return False


def test_sender_page(handle):
    """Test sender page message submission"""
    print("\n=== Testing Sender Page ===")

    print(f"6. Testing sender page for handle: {handle}")

    message_data = {
        "message": "Hello! I'm interested in collaborating on your backend projects.",
        "intent": "collaboration",
        "sender_email": "sender@example.com",
        "sender_name": "Test Sender",
    }

    response = requests.post(
        f"{BASE_URL}/api/reach/{handle}/message", json=message_data
    )
    if response.status_code == 200:
        data = response.json()
        print(f"   Message submission successful!")
        print(f"   Message ID: {data.get('message_id')}")
        print(f"   Status: {data.get('status')}")
        return True
    else:
        print(f"   Message submission failed: {response.status_code} - {response.text}")
        return False


def main():
    """Run complete end-to-end test"""
    print("=" * 60)
    print("COMPLETE END-TO-END TEST")
    print("=" * 60)

    # Start server
    if not start_server():
        print("Failed to start server. Exiting.")
        return

    try:
        # Test auth
        auth_cookies = test_auth()
        if not auth_cookies:
            print("Auth test failed")
            return

        # Test Face creation
        handle = test_face_creation(auth_cookies)
        if not handle:
            print("Face creation test failed")
            return

        # Test public page
        if not test_public_page(handle):
            print("Public page test failed")
            return

        # Test sender page
        if not test_sender_page(handle):
            print("Sender page test failed")
            return

        print("\n" + "=" * 60)
        print("ALL TESTS PASSED!")
        print("=" * 60)
        print("\nSummary:")
        print("1. Auth flow (register, login, session) - PASSED")
        print("2. Face creation with validation - PASSED")
        print("3. Public Face page access - PASSED")
        print("4. Sender page message submission - PASSED")
        print("\nThe Reach application is fully functional!")

    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback

        traceback.print_exc()

    finally:
        # Stop server
        stop_server()


if __name__ == "__main__":
    main()
