import requests
import time

BASE_URL = "http://localhost:8000"

# Test public Face page
handle = "facetest1773411859"
print(f"Testing public Face page for handle: {handle}")

try:
    response = requests.get(f"{BASE_URL}/api/reach/{handle}", timeout=5)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Success! Got Face data:")
        print(f"  Handle: {data.get('identity', {}).get('handle')}")
        print(f"  Display name: {data.get('identity', {}).get('display_name')}")
        print(f"  Face completed: {data.get('identity', {}).get('face_completed')}")
    else:
        print(f"Error {response.status_code}: {response.text}")
except Exception as e:
    print(f"Request failed: {e}")

# Also test with a handle that doesn't exist
print(f"\nTesting with non-existent handle: nonexistent")
try:
    response = requests.get(f"{BASE_URL}/api/reach/nonexistent", timeout=5)
    print(f"Status: {response.status_code}")
    if response.status_code == 404:
        print("Correctly returns 404 for non-existent handle")
    else:
        print(f"Unexpected: {response.status_code} - {response.text}")
except Exception as e:
    print(f"Request failed: {e}")
