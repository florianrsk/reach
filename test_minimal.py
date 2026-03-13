import requests
import time

BASE_URL = "http://localhost:8000"

# Start server if not running
try:
    response = requests.get(f"{BASE_URL}/api/health", timeout=2)
    print(f"Server health: {response.status_code}")
except:
    print("Server not running, starting...")
    import subprocess
    import sys
    import os

    backend_dir = os.path.join(os.path.dirname(__file__), "Reach-main", "backend")
    subprocess.Popen(
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
    time.sleep(3)

# Simple test
print("1. Testing health endpoint...")
try:
    response = requests.get(f"{BASE_URL}/api/health", timeout=5)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print("   OK - Health check OK")
    else:
        print(f"   FAIL - Health check failed: {response.text}")
except Exception as e:
    print(f"   ERROR - Health check error: {e}")

print("\n2. Testing registration...")
email = f"minimal_{int(time.time())}@example.com"
password = "TestPassword123!"

register_data = {"email": email, "password": password, "name": "Minimal Test"}

try:
    response = requests.post(
        f"{BASE_URL}/api/auth/register", json=register_data, timeout=5
    )
    print(f"   Register status: {response.status_code}")
    if response.status_code == 200:
        print("   ✓ Registration OK")
    else:
        print(f"   ✗ Registration failed: {response.text}")
except Exception as e:
    print(f"   ✗ Registration error: {e}")

print("\n3. Testing login...")
try:
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": email, "password": password},
        timeout=5,
    )
    print(f"   Login status: {response.status_code}")
    if response.status_code == 200:
        print("   ✓ Login OK")
        cookies = response.cookies
        print(f"   Cookies: {list(cookies.keys())}")

        # Test attempts endpoint
        print("\n4. Testing attempts endpoint...")
        response = requests.get(f"{BASE_URL}/api/attempts", cookies=cookies, timeout=5)
        print(f"   Attempts status: {response.status_code}")
        print(f"   Attempts response: {response.text[:100]}...")

        if response.status_code == 200:
            print("   ✓ Attempts endpoint works")
        else:
            print("   ✗ Attempts endpoint failed")
    else:
        print(f"   ✗ Login failed: {response.text}")
except Exception as e:
    print(f"   ✗ Error: {e}")
