#!/usr/bin/env python3
"""
Simple test for rules engine implementation
"""

import sys
import asyncio
import json

sys.path.insert(0, "backend")
from server import evaluate_rules_with_llm


async def test_rules_engine():
    """Test the rules engine function"""
    print("Testing rules engine implementation...")

    # Test case 1: Quick sync message should trigger auto_reject
    rules = [
        "If message mentions quick sync - reject automatically",
        "If message is under 30 words - ask for more context",
        "If sender mentions collaboration - auto-approve",
    ]

    submission_data = {
        "message": "Hey, I'd love to schedule a quick sync to discuss collaboration opportunities.",
        "module_data": {},
    }

    print(f"\nTest 1: Quick sync message")
    print(f"Rules: {rules}")
    print(f"Message: {submission_data['message']}")

    try:
        result = await evaluate_rules_with_llm(rules, submission_data, "test_identity")
        print(f"Result: {json.dumps(result, indent=2)}")

        # Check if LLM failed (expected since we don't have LLM integration in test)
        if result.get("llm_failed"):
            print(
                "LLM failure handled correctly - submission would go to queue_for_review"
            )
        else:
            print(f"Rules evaluated: {result.get('final_decision', 'unknown')}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()

    # Test case 2: Empty message should be handled before rules engine
    print("\n\nTest 2: Empty message check")
    print("Note: Empty messages should be rejected before rules engine runs")
    print("This is handled in submit_face_reach_attempt() function")

    # Test case 3: Module integration
    print("\n\nTest 3: Module integration")
    rules_with_modules = [
        "If time requirement is a conversation - require deposit",
        "If intent category is Press - auto-approve",
        "If challenge answer is under 10 words - ask for more context",
    ]

    submission_with_modules = {
        "message": "I'm a journalist writing about your work.",
        "module_data": {
            "time_requirement": "conversation",
            "intent_category": "Press",
            "challenge_answer": "Short answer",
        },
    }

    print(f"Rules with modules: {rules_with_modules}")
    print(f"Module data: {submission_with_modules['module_data']}")

    try:
        result = await evaluate_rules_with_llm(
            rules_with_modules, submission_with_modules, "test_identity"
        )
        print(f"Result: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_rules_engine())
