import subprocess
import time
import requests
import json

# Start the server in background
print("Starting server...")
server_process = subprocess.Popen(
    ["python", "server.py"],
    cwd="./backend",
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1,
)

# Wait for server to start
time.sleep(3)

try:
    # Test the attempts endpoint
    base_url = "http://localhost:8000"

    # Register
    register_data = {
        "email": f"test_capture_{int(time.time())}@example.com",
        "password": "TestPassword123!",
        "name": "Test Capture",
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

    # Get cookies for session
    cookies = login_response.cookies

    # Create identity
    identity_data = {
        "handle": f"testcapture{int(time.time())}",
        "display_name": "Test Capture",
        "headline": "Test headline",
        "current_focus": "Testing current focus field for debugging purposes",
        "availability_signal": "Available for testing",
        "prompt": "Test prompt message",
    }
    identity_response = requests.post(
        f"{base_url}/api/identity", json=identity_data, cookies=cookies
    )
    print(f"Identity creation status: {identity_response.status_code}")

    # Submit message
    identity = identity_response.json()
    message_data = {
        "message": "Test message for error capture",
        "intent_category": "collaboration",
        "time_requirement": "async",
        "challenge_answer": "",
    }
    message_response = requests.post(
        f"{base_url}/api/reach/{identity['handle']}/message", json=message_data
    )
    print(f"Message submission status: {message_response.status_code}")

    # Try to get attempts - this should trigger the error
    attempts_response = requests.get(f"{base_url}/api/attempts", cookies=cookies)
    print(f"\nAttempts status: {attempts_response.status_code}")
    print(f"Attempts response: {attempts_response.text}")

finally:
    # Kill the server
    print("\nStopping server...")
    server_process.terminate()
    server_process.wait()

    # Print server output
    print("\n=== Server Output ===")
    output = server_process.stdout.read()
    print(output)
