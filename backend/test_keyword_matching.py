#!/usr/bin/env python3
"""
Test keyword matching rules engine.
"""

import json
import pytest
from server import evaluate_rules_simple_keyword_matching


@pytest.mark.asyncio
async def test_keyword_matching_basic():
    """Test basic keyword matching."""
    rules = [
        json.dumps({
            "condition": "message contains 'urgent'",
            "action": "auto_approve",
            "reason": "Urgent requests get priority",
            "enabled": True
        }),
        json.dumps({
            "condition": "message contains 'spam'",
            "action": "reject",
            "reason": "Spam messages are rejected",
            "enabled": True
        })
    ]
    
    # Test urgent message
    submission_data = {"message": "This is an urgent request"}
    result = await evaluate_rules_simple_keyword_matching(rules, submission_data, "test-user")
    
    assert result["final_decision"] == "auto_approve"
    assert len(result["triggered_rules"]) == 1
    assert result["triggered_rules"][0]["action"] == "auto_approve"
    assert "urgent" in result["triggered_rules"][0]["reasoning"]
    assert result["llm_failed"] is True
    
    # Test spam message
    submission_data = {"message": "This is spam content"}
    result = await evaluate_rules_simple_keyword_matching(rules, submission_data, "test-user")
    
    assert result["final_decision"] == "auto_reject"
    assert len(result["triggered_rules"]) == 1
    assert result["triggered_rules"][0]["action"] == "reject"
    assert "spam" in result["triggered_rules"][0]["reasoning"]
    
    # Test no match
    submission_data = {"message": "Regular message"}
    result = await evaluate_rules_simple_keyword_matching(rules, submission_data, "test-user")
    
    assert result["final_decision"] == "queue_for_review"
    assert len(result["triggered_rules"]) == 0
    assert "No rules triggered" in result["reasoning_summary"]


@pytest.mark.asyncio
async def test_keyword_matching_case_insensitive():
    """Test that keyword matching is case-insensitive."""
    rules = [
        json.dumps({
            "condition": "message contains 'URGENT'",
            "action": "auto_approve",
            "reason": "Urgent requests",
            "enabled": True
        })
    ]
    
    # Test lowercase message with uppercase keyword in rule
    submission_data = {"message": "this is urgent"}
    result = await evaluate_rules_simple_keyword_matching(rules, submission_data, "test-user")
    
    assert result["final_decision"] == "auto_approve"
    assert len(result["triggered_rules"]) == 1
    
    # Test uppercase message with uppercase keyword in rule
    submission_data = {"message": "THIS IS URGENT"}
    result = await evaluate_rules_simple_keyword_matching(rules, submission_data, "test-user")
    
    assert result["final_decision"] == "auto_approve"
    assert len(result["triggered_rules"]) == 1


@pytest.mark.async
async def test_keyword_matching_disabled_rules():
    """Test that disabled rules are ignored."""
    rules = [
        json.dumps({
            "condition": "message contains 'urgent'",
            "action": "auto_approve",
            "reason": "Urgent requests",
            "enabled": False  # Disabled!
        }),
        json.dumps({
            "condition": "message contains 'important'",
            "action": "auto_approve",
            "reason": "Important requests",
            "enabled": True
        })
    ]
    
    # Test with urgent (disabled rule)
    submission_data = {"message": "This is urgent"}
    result = await evaluate_rules_simple_keyword_matching(rules, submission_data, "test-user")
    
    assert result["final_decision"] == "queue_for_review"  # Should not trigger
    assert len(result["triggered_rules"]) == 0
    
    # Test with important (enabled rule)
    submission_data = {"message": "This is important"}
    result = await evaluate_rules_simple_keyword_matching(rules, submission_data, "test-user")
    
    assert result["final_decision"] == "auto_approve"
    assert len(result["triggered_rules"]) == 1


@pytest.mark.async
async def test_keyword_matching_multiple_rules():
    """Test conflict resolution with multiple rules."""
    rules = [
        json.dumps({
            "condition": "message contains 'urgent'",
            "action": "auto_approve",
            "reason": "Urgent requests",
            "enabled": True
        }),
        json.dumps({
            "condition": "message contains 'spam'",
            "action": "reject",
            "reason": "Spam messages",
            "enabled": True
        }),
        json.dumps({
            "condition": "message contains 'question'",
            "action": "ask_for_more_context",
            "reason": "Questions need more context",
            "enabled": True
        })
    ]
    
    # Test reject priority (highest)
    submission_data = {"message": "This is urgent spam"}
    result = await evaluate_rules_simple_keyword_matching(rules, submission_data, "test-user")
    
    assert result["final_decision"] == "auto_reject"  # reject > auto_approve
    assert len(result["triggered_rules"]) == 2
    
    # Test ask_for_more_context priority (middle)
    submission_data = {"message": "This is an urgent question"}
    result = await evaluate_rules_simple_keyword_matching(rules, submission_data, "test-user")
    
    assert result["final_decision"] == "ask_for_more_context"  # ask > auto_approve
    assert len(result["triggered_rules"]) == 2


@pytest.mark.async
async def test_keyword_matching_malformed_rules():
    """Test handling of malformed rules."""
    rules = [
        "not valid json",  # Invalid JSON
        json.dumps({"wrong": "structure"}),  # Missing required fields
        json.dumps({
            "condition": "message contains 'test'",
            "action": "auto_approve",
            "reason": "Test rule",
            "enabled": True
        })
    ]
    
    submission_data = {"message": "This is a test message"}
    result = await evaluate_rules_simple_keyword_matching(rules, submission_data, "test-user")
    
    # Should still work with the valid rule
    assert result["final_decision"] == "auto_approve"
    assert len(result["triggered_rules"]) == 1


@pytest.mark.async
async def test_evaluate_rules_with_llm_fallback():
    """Test that evaluate_rules_with_llm uses keyword matching."""
    from server import evaluate_rules_with_llm
    
    rules = [
        json.dumps({
            "condition": "message contains 'test'",
            "action": "auto_approve",
            "reason": "Test rule",
            "enabled": True
        })
    ]
    
    submission_data = {"message": "This is a test"}
    result = await evaluate_rules_with_llm(rules, submission_data, "test-user")
    
    # Should use keyword matching (llm_failed should be True)
    assert result["final_decision"] == "auto_approve"
    assert result["llm_failed"] is True


if __name__ == "__main__":
    # Run tests
    import sys
    sys.exit(pytest.main([__file__, "-v"]))