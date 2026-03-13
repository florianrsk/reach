import requests
import json
import time

base_url = "http://localhost:8000"

# Register
register_data = {
    "email": f"test_simple_{int(time.time())}@example.com",
    "password": "TestPassword123!",
    "name": "Test Simple",
}
register_response = requests.post(f"{base_url}/api/auth/register", json=register_data)
print(f"Register status: {register_response.status_code}")

# Login
login_response = requests.post(
    f"{base_url}/api/auth/login",
    json={"email": register_data["email"], "password": register_data["password"]},
)
print(f"Login status: {login_response.status_code}")

# Get cookies for session
cookies = login_response.cookies
print(f"Cookies: {cookies}")

# Create identity
identity_data = {
    "handle": f"testsimple{int(time.time())}",
    "display_name": "Test Simple",
    "headline": "Test headline",
    "current_focus": "Testing current focus field for debugging purposes",
    "availability_signal": "Available for testing",
    "prompt": "Test prompt message",
}
identity_response = requests.post(
    f"{base_url}/api/identity", json=identity_data, cookies=cookies
)
print(f"Identity creation status: {identity_response.status_code}")
identity = identity_response.json()
print(f"Identity handle: {identity['handle']}")

# Submit message
message_data = {
    "message": "Test message for simple debug",
    "intent_category": "collaboration",
    "time_requirement": "async",
    "challenge_answer": "",
}
message_response = requests.post(
    f"{base_url}/api/reach/{identity['handle']}/message", json=message_data
)
print(f"Message submission status: {message_response.status_code}")
print(f"Message response: {message_response.text}")

# Wait a bit for server to process
time.sleep(1)

# Try to get attempts
print("\n=== Getting attempts ===")
attempts_response = requests.get(f"{base_url}/api/attempts", cookies=cookies)
print(f"Attempts status: {attempts_response.status_code}")
print(f"Attempts response: {attempts_response.text}")

# Also try to get raw attempt data
print("\n=== Trying to get attempt by ID ===")
attempt_id = json.loads(message_response.text)["attempt_id"]
attempt_detail_response = requests.get(
    f"{base_url}/api/attempts/{attempt_id}", cookies=cookies
)
print(f"Attempt detail status: {attempt_detail_response.status_code}")
print(f"Attempt detail: {attempt_detail_response.text}")
