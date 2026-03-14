#!/usr/bin/env python3
"""
Test WebSocket functionality for real-time notifications.
"""

import asyncio
import json
import pytest
from datetime import datetime, timezone
from websocket_manager import websocket_manager


class MockWebSocket:
    """Mock WebSocket connection for testing."""
    
    def __init__(self):
        self.sent_messages = []
        self.closed = False
        self.close_code = None
        self.close_reason = None
    
    async def send_text(self, message):
        self.sent_messages.append(message)
    
    def close(self, code=1000, reason=""):
        self.closed = True
        self.close_code = code
        self.close_reason = reason


@pytest.mark.asyncio
async def test_websocket_manager_connection():
    """Test WebSocket manager connection handling."""
    # Reset connections for clean test
    websocket_manager.connections.clear()
    
    # Create mock WebSocket
    ws1 = MockWebSocket()
    ws2 = MockWebSocket()
    
    # Connect first WebSocket
    await websocket_manager.connect(ws1, "user-123")
    assert "user-123" in websocket_manager.connections
    assert len(websocket_manager.connections["user-123"]) == 1
    assert len(ws1.sent_messages) == 1
    
    # Verify connection message
    connection_msg = json.loads(ws1.sent_messages[0])
    assert connection_msg["type"] == "connection_established"
    
    # Connect second WebSocket for same user
    await websocket_manager.connect(ws2, "user-123")
    assert len(websocket_manager.connections["user-123"]) == 2
    
    # Connect WebSocket for different user
    ws3 = MockWebSocket()
    await websocket_manager.connect(ws3, "user-456")
    assert "user-456" in websocket_manager.connections
    assert len(websocket_manager.connections["user-456"]) == 1
    
    # Test disconnection
    await websocket_manager.disconnect(ws1, "user-123")
    assert len(websocket_manager.connections["user-123"]) == 1
    
    await websocket_manager.disconnect(ws2, "user-123")
    assert "user-123" not in websocket_manager.connections
    
    await websocket_manager.disconnect(ws3, "user-456")
    assert "user-456" not in websocket_manager.connections


@pytest.mark.asyncio
async def test_websocket_manager_send_to_user():
    """Test sending messages to specific users."""
    # Reset connections for clean test
    websocket_manager.connections.clear()
    
    # Create mock WebSockets
    ws1 = MockWebSocket()
    ws2 = MockWebSocket()
    
    # Connect WebSockets
    await websocket_manager.connect(ws1, "user-123")
    await websocket_manager.connect(ws2, "user-456")
    
    # Send message to user-123
    message = {"type": "test", "message": "Hello user-123"}
    success = await websocket_manager.send_to_user("user-123", message)
    assert success is True
    assert len(ws1.sent_messages) == 2  # Connection message + test message
    assert len(ws2.sent_messages) == 1  # Only connection message
    
    # Verify test message
    test_msg = json.loads(ws1.sent_messages[1])
    assert test_msg["type"] == "test"
    assert test_msg["message"] == "Hello user-123"
    
    # Send message to non-existent user
    success = await websocket_manager.send_to_user("user-999", message)
    assert success is False
    
    # Clean up
    await websocket_manager.disconnect(ws1, "user-123")
    await websocket_manager.disconnect(ws2, "user-456")


@pytest.mark.asyncio
async def test_websocket_manager_broadcast_new_attempt():
    """Test broadcasting new reach attempt notifications."""
    # Reset connections for clean test
    websocket_manager.connections.clear()
    
    # Create mock WebSocket
    ws = MockWebSocket()
    await websocket_manager.connect(ws, "user-123")
    
    # Create test attempt data
    attempt_data = {
        "id": "attempt-123",
        "sender_context": {"email": "sender@example.com"},
        "payload": {"reason": "Test message"},
        "intent_category": "collaboration",
        "decision": "queued",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Broadcast new attempt notification
    success = await websocket_manager.broadcast_new_attempt(
        identity_id="identity-123",
        user_id="user-123",
        attempt_data=attempt_data
    )
    
    assert success is True
    assert len(ws.sent_messages) == 2  # Connection message + notification
    
    # Verify notification
    notification = json.loads(ws.sent_messages[1])
    assert notification["type"] == "new_attempt"
    assert notification["attempt"]["id"] == "attempt-123"
    assert notification["attempt"]["sender_email"] == "sender@example.com"
    assert notification["message"] == "New request from sender@example.com"
    
    # Clean up
    await websocket_manager.disconnect(ws, "user-123")


@pytest.mark.asyncio
async def test_websocket_manager_broadcast_attempt_decision():
    """Test broadcasting attempt decision notifications."""
    # Reset connections for clean test
    websocket_manager.connections.clear()
    
    # Create mock WebSocket
    ws = MockWebSocket()
    await websocket_manager.connect(ws, "user-123")
    
    # Broadcast decision notification
    success = await websocket_manager.broadcast_attempt_decision(
        user_id="user-123",
        attempt_id="attempt-123",
        decision="deliver_to_human"
    )
    
    assert success is True
    assert len(ws.sent_messages) == 2  # Connection message + notification
    
    # Verify notification
    notification = json.loads(ws.sent_messages[1])
    assert notification["type"] == "attempt_decision"
    assert notification["attempt_id"] == "attempt-123"
    assert notification["decision"] == "deliver_to_human"
    assert notification["message"] == "Request deliver to human"
    
    # Clean up
    await websocket_manager.disconnect(ws, "user-123")


def test_websocket_manager_connection_count():
    """Test connection count methods."""
    # Reset connections for clean test
    websocket_manager.connections.clear()
    
    # Test with no connections
    assert websocket_manager.get_connection_count() == 0
    assert websocket_manager.get_connection_count("user-123") == 0
    assert websocket_manager.get_user_ids() == []
    
    # Manually add connections for testing
    websocket_manager.connections["user-123"] = {MockWebSocket(), MockWebSocket()}
    websocket_manager.connections["user-456"] = {MockWebSocket()}
    
    # Test counts
    assert websocket_manager.get_connection_count() == 3
    assert websocket_manager.get_connection_count("user-123") == 2
    assert websocket_manager.get_connection_count("user-456") == 1
    assert set(websocket_manager.get_user_ids()) == {"user-123", "user-456"}
    
    # Clean up
    websocket_manager.connections.clear()


if __name__ == "__main__":
    # Run tests
    import sys
    sys.exit(pytest.main([__file__, "-v"]))