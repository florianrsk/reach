import requests
import time
import json

BASE_URL = "http://localhost:8000"

print("Debugging auto-rejection...")
print("=" * 60)

# 1. Create user
email = f"debug_{int(time.time())}@example.com"
password = "TestPassword123!"

register_data = {"email": email, "password": password, "name": "Debug User"}
response = requests.post(f"{BASE_URL}/api/auth/register", json=register_data)
if response.status_code != 200:
    print(f"FAIL - Register: {response.status_code} - {response.text}")
    exit(1)
print("OK - User created")

# 2. Login
login_data = {"email": email, "password": password}
response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
if response.status_code != 200:
    print(f"FAIL - Login: {response.status_code} - {response.text}")
    exit(1)

auth_cookies = response.cookies
print("OK - Logged in")

# 3. Create Face
handle = f"debugface_{int(time.time())}"
face_data = {
    "handle": handle,
    "display_name": "Debug User",
    "headline": "Software Developer",
    "current_focus": "Debugging rules engine",
    "availability_signal": "Available",
    "prompt": "Debug",
    "photo_url": "https://example.com/profile.jpg",
    "links": [],
}
response = requests.post(
    f"{BASE_URL}/api/identity", json=face_data, cookies=auth_cookies
)
if response.status_code != 200:
    print(f"FAIL - Face creation: {response.status_code} - {response.text}")
    exit(1)
print(f"OK - Face created: {handle}")

# 4. Enable rules engine
rule_json = json.dumps(
    {
        "id": "test_rule",
        "name": "Reject Quick Sync",
        "description": "Reject messages with quick sync",
        "condition": "message contains 'quick sync'",
        "action": "reject",
        "reason": "No quick sync allowed",
        "enabled": True,
    }
)
update_data = {"rules_engine": {"enabled": True, "rules": [rule_json]}}
response = requests.put(
    f"{BASE_URL}/api/modules", json=update_data, cookies=auth_cookies
)
if response.status_code != 200:
    print(f"FAIL - Enable rules engine: {response.status_code} - {response.text}")
    exit(1)
print("OK - Rules engine enabled")

# 5. Send message with "quick sync"
message_data = {
    "message": "Let's have a quick sync meeting tomorrow.",
    "intent": "meeting",
    "sender_email": "sender@example.com",
    "sender_name": "Test Sender",
}
response = requests.post(f"{BASE_URL}/api/reach/{handle}/message", json=message_data)
if response.status_code != 200:
    print(f"FAIL - Message submission: {response.status_code} - {response.text}")
    exit(1)
result = response.json()
attempt_id = result.get("attempt_id")
print(f"OK - Message submitted, attempt ID: {attempt_id}")

# 6. Check attempts
time.sleep(1)
response = requests.get(f"{BASE_URL}/api/attempts", cookies=auth_cookies)
if response.status_code != 200:
    print(f"FAIL - Get attempts: {response.status_code}")
    exit(1)
attempts = response.json()
print(f"Found {len(attempts)} attempts")
if attempts:
    attempt = attempts[0]
    print("\nAttempt fields:")
    for key, value in attempt.items():
        print(f"  {key}: {value}")

    print(f"\nDecision field: {attempt.get('decision')}")
    print(f"AI classification: {attempt.get('ai_classification')}")

    if attempt.get("decision") == "reject":
        print("SUCCESS - Message auto-rejected!")
    else:
        print(f"FAIL - Decision is {attempt.get('decision')}, expected 'reject'")
else:
    print("No attempts found")
