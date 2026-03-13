#!/usr/bin/env python3
"""
Test the function directly by importing it
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))


# Mock the database
class MockDB:
    def __init__(self):
        self.identities = {
            "hello": {
                "handle": "hello",
                "type": "person",
                "bio": "hello",
                "face_completed": False,
                "display_name": None,
                "headline": None,
                "current_focus": None,
                "availability_signal": None,
                "prompt": None,
                "photo_url": None,
                "links": [],
            }
        }

    async def find_one(self, query, projection):
        handle = query.get("handle")
        if handle in self.identities:
            return self.identities[handle]
        return None


# Mock db
db = MockDB()

# Now import the function
from server import get_public_reach_page


async def test():
    print("Testing get_public_reach_page directly...")

    try:
        result = await get_public_reach_page("hello")
        print(f"Result: {result}")
    except Exception as e:
        print(f"Exception: {e}")


if __name__ == "__main__":
    asyncio.run(test())
