import requests
import time

BASE_URL = "http://localhost:8000"

# Test public Face page
handle = "facetest1773411859"
print(f"Testing public Face page for handle: {handle}")

response = requests.get(f"{BASE_URL}/api/reach/{handle}")
print(f"Status: {response.status_code}")
if response.status_code == 200:
    print(f"Response: {response.json()}")
else:
    print(f"Error: {response.text}")

# Also test with uppercase
print(f"\nTesting with uppercase handle: {handle.upper()}")
response = requests.get(f"{BASE_URL}/api/reach/{handle.upper()}")
print(f"Status: {response.status_code}")
if response.status_code == 200:
    print(f"Response: {response.json()}")
else:
    print(f"Error: {response.text}")

# Test identity endpoint
print(f"\nTesting identity endpoint for same handle...")
response = requests.get(f"{BASE_URL}/api/identity", cookies={"session": "test"})
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Identity handle: {data.get('handle')}")
    print(f"Face completed: {data.get('face_completed')}")
