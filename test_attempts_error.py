import asyncio
import httpx
import json


async def test_attempts_error():
    base_url = "http://localhost:8000"

    # Register a new user
    async with httpx.AsyncClient() as client:
        # Register
        register_data = {
            "email": f"test_error_{int(asyncio.get_event_loop().time())}@example.com",
            "password": "TestPassword123!",
            "name": "Test Error User",
        }
        register_response = await client.post(
            f"{base_url}/api/auth/register", json=register_data
        )
        print(f"Register status: {register_response.status_code}")

        # Login
        login_data = {
            "email": register_data["email"],
            "password": register_data["password"],
        }
        login_response = await client.post(
            f"{base_url}/api/auth/login", json=login_data
        )
        print(f"Login status: {login_response.status_code}")

        # Create a Face (Identity)
        face_data = {
            "handle": f"testerror{int(asyncio.get_event_loop().time())}",
            "display_name": "Test Error User",
            "headline": "Test Headline",
            "current_focus": "Testing",
            "availability_signal": "Available",
            "prompt": "Test prompt",
        }
        face_response = await client.post(f"{base_url}/api/identity", json=face_data)
        print(f"Face creation status: {face_response.status_code}")

        # Submit a message to the Face
        face_handle = json.loads(face_response.text)["handle"]
        message_data = {
            "message": "Test message for error debugging",
            "intent_category": "collaboration",
            "time_requirement": "async",
            "challenge_answer": "",
        }
        message_response = await client.post(
            f"{base_url}/api/reach/{face_handle}/message", json=message_data
        )
        print(f"Message submission status: {message_response.status_code}")

        # Try to get attempts with error details
        attempts_response = await client.get(f"{base_url}/api/attempts")
        print(f"\nAttempts status: {attempts_response.status_code}")
        print(f"Attempts response text: {attempts_response.text}")

        # Also try to get the error from server logs by making a request that might show more details
        print("\nTrying to get server error details...")

        # Enable modules and rules engine
        modules_data = {
            "challenge_question": {"enabled": False},
            "time_signal": {"enabled": True},
            "waiting_period": {"enabled": False},
            "deposit": {"enabled": False},
            "intent_categories": {
                "enabled": True,
                "categories": ["Collaboration", "Question", "Feedback", "Opportunity"],
            },
            "capacity_controls": {"enabled": False},
            "rules_engine": {
                "enabled": True,
                "rules": [
                    {
                        "name": "Reject quick sync requests",
                        "condition": "message contains 'quick sync'",
                        "action": "auto_reject",
                        "suggested_response": "I don't do quick sync calls.",
                    }
                ],
            },
        }

        modules_response = await client.put(
            f"{base_url}/api/modules", json=modules_data
        )
        print(f"Modules update status: {modules_response.status_code}")

        # Submit another message with "quick sync" to test rules engine
        message_data2 = {
            "message": "Can we do a quick sync tomorrow?",
            "intent_category": "collaboration",
            "time_requirement": "sync",
            "challenge_answer": "",
        }
        message_response2 = await client.post(
            f"{base_url}/api/reach/{face_handle}/message", json=message_data2
        )
        print(f"Quick sync message status: {message_response2.status_code}")
        print(f"Quick sync response: {message_response2.text}")

        # Try attempts again
        attempts_response2 = await client.get(f"{base_url}/api/attempts")
        print(f"\nAttempts after quick sync status: {attempts_response2.status_code}")
        print(f"Attempts after quick sync: {attempts_response2.text}")


if __name__ == "__main__":
    asyncio.run(test_attempts_error())
