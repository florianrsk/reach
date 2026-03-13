import requests
import time
import json

BASE_URL = "http://localhost:8000"

print("Testing server fixes...")
print("=" * 60)

# 1. Test health
print("1. Testing health endpoint...")
try:
    response = requests.get(f"{BASE_URL}/api/health", timeout=5)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print("   OK - Health check passed")
    else:
        print(f"   FAIL - Health check: {response.text}")
except Exception as e:
    print(f"   ERROR - Health check: {e}")
    exit(1)

# 2. Create user
print("\n2. Creating test user...")
email = f"test_{int(time.time())}@example.com"
password = "TestPassword123!"

register_data = {"email": email, "password": password, "name": "Test User"}

response = requests.post(f"{BASE_URL}/api/auth/register", json=register_data)
if response.status_code != 200:
    print(f"   FAIL - Register: {response.status_code} - {response.text}")
    exit(1)
print("   OK - User created")

# 3. Login
print("\n3. Logging in...")
login_data = {"email": email, "password": password}
response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
if response.status_code != 200:
    print(f"   FAIL - Login: {response.status_code} - {response.text}")
    exit(1)

auth_cookies = response.cookies
print("   OK - Logged in")

# 4. Create Face
print("\n4. Creating Face...")
handle = f"testface_{int(time.time())}"

face_data = {
    "handle": handle,
    "display_name": "Test User",
    "headline": "Software Developer with backend experience",
    "current_focus": "Currently working on testing the rules engine and decision surface functionality for automated message processing.",
    "availability_signal": "I check messages daily and respond within 24 hours",
    "prompt": "What brings you to my page today? Please share your project.",
    "photo_url": "https://example.com/profile.jpg",
    "links": [],
}

response = requests.post(
    f"{BASE_URL}/api/identity", json=face_data, cookies=auth_cookies
)
if response.status_code != 200:
    print(f"   FAIL - Face creation: {response.status_code} - {response.text}")
    exit(1)
print(f"   OK - Face created: {handle}")

# 5. Test attempts endpoint (should return empty list, not 404)
print("\n5. Testing attempts endpoint...")
response = requests.get(f"{BASE_URL}/api/attempts", cookies=auth_cookies)
if response.status_code != 200:
    print(f"   FAIL - Attempts endpoint: {response.status_code} - {response.text}")
    # Check if it's 404 "Identity not found"
    if response.status_code == 404 and "Identity not found" in response.text:
        print(
            "   ERROR - Attempts endpoint returns 'Identity not found' - this is the bug we need to fix!"
        )
    exit(1)

attempts = response.json()
print(f"   OK - Attempts endpoint returned {len(attempts)} attempts")

# 6. Enable rules engine
print("\n6. Enabling rules engine...")
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
    print(f"   FAIL - Enable rules engine: {response.status_code} - {response.text}")
    exit(1)
print("   OK - Rules engine enabled")

# 7. Send message with "quick sync"
print("\n7. Testing auto-rejection...")
message_data = {
    "message": "Let's have a quick sync meeting tomorrow.",
    "intent": "meeting",
    "sender_email": "sender@example.com",
    "sender_name": "Test Sender",
}

response = requests.post(f"{BASE_URL}/api/reach/{handle}/message", json=message_data)
if response.status_code != 200:
    print(f"   FAIL - Message submission: {response.status_code} - {response.text}")
    exit(1)

result = response.json()
attempt_id = result.get("attempt_id")
print(f"   OK - Message submitted, attempt ID: {attempt_id}")

# 8. Check if auto-rejected
print("\n8. Checking auto-rejection...")
time.sleep(2)

response = requests.get(f"{BASE_URL}/api/attempts", cookies=auth_cookies)
if response.status_code != 200:
    print(f"   FAIL - Get attempts: {response.status_code}")
    exit(1)

attempts = response.json()
print(f"   Found {len(attempts)} attempts")

# Find our attempt
attempt = None
for a in attempts:
    if a.get("id") == attempt_id:
        attempt = a
        break

if not attempt:
    print("   FAIL - Could not find attempt")
    exit(1)

print(f"   Attempt decision: {attempt.get('decision')}")
if attempt.get("decision") == "reject":
    print("   OK - Message was auto-rejected!")
else:
    print(f"   FAIL - Message not auto-rejected. Decision: {attempt.get('decision')}")
    exit(1)

print("\n" + "=" * 60)
print("ALL TESTS PASSED!")
print("=" * 60)
print("\nSummary:")
print("1. Server health - OK")
print("2. User registration - OK")
print("3. Login - OK")
print("4. Face creation - OK")
print("5. Attempts endpoint - OK (no 404 error)")
print("6. Rules engine enabled - OK")
print("7. Message submission - OK")
print("8. Auto-rejection - OK")
print("\nAll fixes are working!")
