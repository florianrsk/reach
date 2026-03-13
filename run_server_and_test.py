import subprocess
import time
import requests
import json
import sys
import os

# Start server
print("Starting server...")
server_proc = subprocess.Popen(
    [sys.executable, "server.py"],
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

    # Register
    register_data = {
        "email": f"test_run_{int(time.time())}@example.com",
        "password": "TestPassword123!",
        "name": "Test Run",
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
        "handle": f"testrun{int(time.time())}",
        "display_name": "Test Run",
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
        "message": "Test message for run test",
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
    print(f"Attempts response: {attempts_response.text}")

finally:
    # Kill server
    print("\n=== Server Output ===")
    server_proc.terminate()
    try:
        stdout, _ = server_proc.communicate(timeout=5)
        print(stdout)
    except subprocess.TimeoutExpired:
        server_proc.kill()
        stdout, _ = server_proc.communicate()
        print(stdout)
