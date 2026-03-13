import requests
import time
import json

base_url = "http://localhost:8000"

print("Testing attempts endpoint fix...")

# Register
register_data = {
    "email": f"test_fix_{int(time.time())}@example.com",
    "password": "TestPassword123!",
    "name": "Test Fix",
}
register_response = requests.post(f"{base_url}/api/auth/register", json=register_data)
print(f"Register status: {register_response.status_code}")

if register_response.status_code != 200:
    print(f"Register failed: {register_response.text}")
    exit(1)

# Login
login_response = requests.post(
    f"{base_url}/api/auth/login",
    json={"email": register_data["email"], "password": register_data["password"]},
)
print(f"Login status: {login_response.status_code}")

if login_response.status_code != 200:
    print(f"Login failed: {login_response.text}")
    exit(1)

cookies = login_response.cookies

# Create identity
identity_data = {
    "handle": f"testfix{int(time.time())}",
    "display_name": "Test Fix",
    "headline": "Test headline",
    "current_focus": "Testing current focus field",
    "availability_signal": "Available for testing",
    "prompt": "Test prompt message",
}
identity_response = requests.post(
    f"{base_url}/api/identity", json=identity_data, cookies=cookies
)
print(f"Identity creation status: {identity_response.status_code}")

if identity_response.status_code != 200:
    print(f"Identity creation failed: {identity_response.text}")
    exit(1)

identity = identity_response.json()
print(f"Identity handle: {identity['handle']}")

# Submit message
message_data = {
    "message": "Test message for attempts fix",
    "intent_category": "collaboration",
    "time_requirement": "async",
    "challenge_answer": "",
}
message_response = requests.post(
    f"{base_url}/api/reach/{identity['handle']}/message", json=message_data
)
print(f"Message submission status: {message_response.status_code}")
print(f"Message response: {message_response.text}")

if message_response.status_code != 200:
    print(f"Message submission failed")
    exit(1)

# Wait for processing
time.sleep(2)

# Get attempts
print("\n=== Getting attempts ===")
attempts_response = requests.get(f"{base_url}/api/attempts", cookies=cookies)
print(f"Attempts status: {attempts_response.status_code}")

if attempts_response.status_code == 200:
    attempts = attempts_response.json()
    print(f"Success! Got {len(attempts)} attempts")
    if attempts:
        print(f"First attempt: {json.dumps(attempts[0], indent=2)}")
else:
    print(f"Attempts failed: {attempts_response.text}")
