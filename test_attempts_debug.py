import asyncio
import httpx
import json


async def test_attempts_debug():
    base_url = "http://localhost:8000"

    # Register a new user
    async with httpx.AsyncClient() as client:
        # Register
        register_data = {
            "email": f"test_attempts_{int(asyncio.get_event_loop().time())}@example.com",
            "password": "TestPassword123!",
            "name": "Test User",
        }
        register_response = await client.post(
            f"{base_url}/api/auth/register", json=register_data
        )
        print(f"Register status: {register_response.status_code}")
        print(f"Register response: {register_response.text}")

        # Login
        login_data = {
            "email": register_data["email"],
            "password": register_data["password"],
        }
        login_response = await client.post(
            f"{base_url}/api/auth/login", json=login_data
        )
        print(f"\nLogin status: {login_response.status_code}")

        # Create a Face (Identity)
        face_data = {
            "handle": f"testuser{int(asyncio.get_event_loop().time())}",
            "display_name": "Test User",
            "headline": "Test Headline for Debugging",
            "current_focus": "Testing the attempts endpoint debugging functionality",
            "availability_signal": "Available for testing and debugging",
            "prompt": "Please send me test messages for debugging",
        }
        face_response = await client.post(f"{base_url}/api/identity", json=face_data)
        print(f"\nFace creation status: {face_response.status_code}")
        print(f"Face response: {face_response.text}")

        # Get attempts before submission
        attempts_response = await client.get(f"{base_url}/api/attempts")
        print(f"\nAttempts before submission status: {attempts_response.status_code}")
        print(f"Attempts before submission: {attempts_response.text}")

        # Submit a message to the Face
        face_handle = json.loads(face_response.text)["handle"]
        message_data = {
            "message": "Test message for debugging attempts endpoint",
            "intent_category": "collaboration",
            "time_requirement": "async",
            "challenge_answer": "",
        }
        message_response = await client.post(
            f"{base_url}/api/reach/{face_handle}/message", json=message_data
        )
        print(f"\nMessage submission status: {message_response.status_code}")
        print(f"Message response: {message_response.text}")

        # Get attempts after submission
        attempts_response2 = await client.get(f"{base_url}/api/attempts")
        print(f"\nAttempts after submission status: {attempts_response2.status_code}")
        print(f"Attempts after submission: {attempts_response2.text}")

        # Try to get raw data from database via debug endpoint
        debug_response = await client.get(f"{base_url}/api/debug/attempts")
        print(f"\nDebug attempts status: {debug_response.status_code}")
        if debug_response.status_code == 200:
            print(f"Debug attempts: {debug_response.text}")


if __name__ == "__main__":
    asyncio.run(test_attempts_debug())
