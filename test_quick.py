import requests
import time

base_url = "http://localhost:8000"

# First check if we can get health
health = requests.get(f"{base_url}/api/health")
print(f"Health: {health.status_code}")

# Register
register_data = {
    "email": f"test_quick_{int(time.time())}@example.com",
    "password": "TestPassword123!",
    "name": "Test Quick",
}
register = requests.post(f"{base_url}/api/auth/register", json=register_data)
print(f"Register: {register.status_code}")

# Login
login = requests.post(
    f"{base_url}/api/auth/login",
    json={"email": register_data["email"], "password": register_data["password"]},
)
print(f"Login: {login.status_code}")

cookies = login.cookies

# Try to get attempts without creating identity
print("\nTrying to get attempts without identity...")
attempts = requests.get(f"{base_url}/api/attempts", cookies=cookies)
print(f"Attempts status: {attempts.status_code}")
print(f"Attempts text: {attempts.text}")
