import subprocess
import time
import requests
import json

# Kill any existing server
print("Killing any existing server...")
subprocess.run(["taskkill", "/f", "/im", "python.exe"], capture_output=True)

# Start fresh server
print("Starting fresh server...")
server_proc = subprocess.Popen(
    ["python", "server.py"],
    cwd="./backend",
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1,
)

# Wait for server to start
time.sleep(5)

try:
    base_url = "http://localhost:8000"

    # Check health
    health = requests.get(f"{base_url}/api/health")
    print(f"Health check: {health.status_code}")

    # Register
    register_data = {
        "email": f"test_fresh_{int(time.time())}@example.com",
        "password": "TestPassword123!",
        "name": "Test Fresh",
    }
    register_response = requests.post(
        f"{base_url}/api/auth/register", json=register_data
    )
    print(f"Register status: {register_response.status_code}")

    # Login
    login_response = requests.post(
        f"{base_url}/api/auth/login",
        json={"email": register_data["email"], "password": register_data["password"]},
    )
    print(f"Login status: {login_response.status_code}")

    cookies = login_response.cookies

    # Create identity
    identity_data = {
        "handle": f"testfresh{int(time.time())}",
        "display_name": "Test Fresh",
        "headline": "Test headline",
        "current_focus": "Testing current focus field",
        "availability_signal": "Available for testing",
        "prompt": "Test prompt message",
    }
    identity_response = requests.post(
        f"{base_url}/api/identity", json=identity_data, cookies=cookies
    )
    print(f"Identity creation status: {identity_response.status_code}")
    identity = identity_response.json()

    # Submit message
    message_data = {
        "message": "Test message for fresh server",
        "intent_category": "collaboration",
        "time_requirement": "async",
        "challenge_answer": "",
    }
    message_response = requests.post(
        f"{base_url}/api/reach/{identity['handle']}/message", json=message_data
    )
    print(f"Message submission status: {message_response.status_code}")

    # Wait for processing
    time.sleep(2)

    # Get attempts
    print("\n=== Getting attempts ===")
    attempts_response = requests.get(f"{base_url}/api/attempts", cookies=cookies)
    print(f"Attempts status: {attempts_response.status_code}")
    if attempts_response.status_code == 200:
        print(f"Attempts response: {attempts_response.text}")
    else:
        print(f"Attempts error: {attempts_response.text}")

    # Read server output
    print("\n=== Server output ===")
    # Try to read any output
    import sys
    import os

    if sys.platform == "win32":
        # On Windows, we can't use select, so just read what's available
        import msvcrt
        import io

        # Set stdout to non-blocking
        from ctypes import windll, byref, wintypes, WinError
        import ctypes

        # Try to read available output
        try:
            while True:
                line = server_proc.stdout.readline()
                if line:
                    print(f"SERVER: {line}", end="")
                else:
                    break
        except:
            pass
    else:
        # Unix version with select
        import select

        while True:
            ready, _, _ = select.select([server_proc.stdout], [], [], 0.1)
            if ready:
                line = server_proc.stdout.readline()
                if line:
                    print(f"SERVER: {line}", end="")
                else:
                    break
            else:
                break

finally:
    # Kill server
    print("\n=== Stopping server ===")
    server_proc.terminate()
    try:
        stdout, _ = server_proc.communicate(timeout=5)
        print("Final server output:")
        print(stdout)
    except subprocess.TimeoutExpired:
        server_proc.kill()
        stdout, _ = server_proc.communicate()
        print("Final server output (killed):")
        print(stdout)
