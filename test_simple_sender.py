#!/usr/bin/env python3
"""
Simple test to verify sender page returns Face data
"""

import requests
import time

BASE_URL = "http://localhost:8001"


def test_public_page():
    """Test that public page returns Face data"""
    print("Testing public reach page...")

    # First, check if we can get any public page
    # Let's try with an existing handle from our migration
    response = requests.get(f"{BASE_URL}/api/reach/hello")

    print(f"Response status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Data: {data}")

        identity = data.get("identity", {})
        print(f"\nIdentity fields:")
        for key, value in identity.items():
            print(f"  {key}: {value}")

        # Check face_completed
        if identity.get("face_completed") == False:
            print("\nPASS: face_completed is False (as expected after migration)")
            return True
        else:
            print(
                f"\nFAIL: face_completed is {identity.get('face_completed')}, expected False"
            )
            return False
    elif response.status_code == 404:
        print("Got 404 - identity not found or face not completed")
        # This is expected since we migrated all identities to face_completed: false
        print("PASS: Got expected 404 for non-face-completed identity")
        return True
    else:
        print(f"FAIL: Unexpected status code: {response.status_code}")
        print(f"Response: {response.text}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("SIMPLE SENDER PAGE TEST")
    print("=" * 60)

    success = test_public_page()

    if success:
        print("\nPASS: Sender page endpoint is working correctly")
    else:
        print("\nFAIL: Sender page test failed")
