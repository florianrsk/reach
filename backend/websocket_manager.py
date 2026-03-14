#!/usr/bin/env python3
"""
WebSocket manager for real-time notifications.
Manages connections and sends notifications to identity owners.
"""

import asyncio
import json
import logging
from typing import Dict, Set, Any
from datetime import datetime, timezone
import jwt

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections for real-time notifications."""
    
    def __init__(self):
        # user_id -> set of WebSocket connections
        self.connections: Dict[str, Set[Any]] = {}
        # JWT secret for authentication
        self.jwt_secret = None
        
    def set_jwt_secret(self, secret: str):
        """Set JWT secret for authentication."""
        self.jwt_secret = secret
    
    async def connect(self, websocket, user_id: str):
        """Register a new WebSocket connection for a user."""
        if user_id not in self.connections:
            self.connections[user_id] = set()
        
        self.connections[user_id].add(websocket)
        logger.info(f"WebSocket connected for user {user_id}. Total connections: {len(self.connections[user_id])}")
        
        # Send initial connection confirmation
        await self.send_to_user(user_id, {
            "type": "connection_established",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": "WebSocket connected"
        })
    
    async def disconnect(self, websocket, user_id: str):
        """Remove a WebSocket connection for a user."""
        if user_id in self.connections:
            self.connections[user_id].discard(websocket)
            if not self.connections[user_id]:
                del self.connections[user_id]
            logger.info(f"WebSocket disconnected for user {user_id}")
    
    async def send_to_user(self, user_id: str, message: Dict[str, Any]):
        """Send a message to all connections for a specific user."""
        if user_id not in self.connections:
            return False
        
        message_json = json.dumps(message)
        tasks = []
        
        for websocket in list(self.connections[user_id]):
            try:
                tasks.append(websocket.send_text(message_json))
            except Exception as e:
                logger.error(f"Error sending to WebSocket for user {user_id}: {e}")
                # Remove broken connection
                self.connections[user_id].discard(websocket)
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            return True
        
        return False
    
    async def broadcast_new_attempt(self, identity_id: str, user_id: str, attempt_data: Dict[str, Any]):
        """Broadcast a new reach attempt notification to the identity owner."""
        notification = {
            "type": "new_attempt",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "attempt": {
                "id": attempt_data.get("id"),
                "sender_email": attempt_data.get("sender_context", {}).get("email", "Anonymous"),
                "reason": attempt_data.get("payload", {}).get("reason", ""),
                "intent_category": attempt_data.get("intent_category"),
                "decision": attempt_data.get("decision", "queued"),
                "created_at": attempt_data.get("created_at"),
            },
            "identity_id": identity_id,
            "message": f"New request from {attempt_data.get('sender_context', {}).get('email', 'Anonymous')}"
        }
        
        success = await self.send_to_user(user_id, notification)
        if success:
            logger.info(f"Sent new attempt notification to user {user_id} for attempt {attempt_data.get('id')}")
        else:
            logger.info(f"No active WebSocket connections for user {user_id}")
        
        return success
    
    async def broadcast_attempt_decision(self, user_id: str, attempt_id: str, decision: str):
        """Broadcast when an attempt decision is made."""
        notification = {
            "type": "attempt_decision",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "attempt_id": attempt_id,
            "decision": decision,
            "message": f"Request {decision.replace('_', ' ')}"
        }
        
        return await self.send_to_user(user_id, notification)
    
    async def broadcast_stats_update(self, user_id: str, stats: Dict[str, Any]):
        """Broadcast updated stats to user."""
        notification = {
            "type": "stats_update",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "stats": stats,
            "message": "Stats updated"
        }
        
        return await self.send_to_user(user_id, notification)
    
    def get_connection_count(self, user_id: str = None) -> int:
        """Get number of active connections."""
        if user_id:
            return len(self.connections.get(user_id, []))
        return sum(len(conns) for conns in self.connections.values())
    
    def get_user_ids(self) -> list:
        """Get list of user IDs with active connections."""
        return list(self.connections.keys())


# Global WebSocket manager instance
websocket_manager = WebSocketManager()


async def authenticate_websocket(websocket, token: str) -> Dict[str, Any]:
    """
    Authenticate WebSocket connection using JWT token.
    
    Args:
        websocket: WebSocket connection
        token: JWT token from query parameter
        
    Returns:
        Dictionary with user information if authenticated, None otherwise
    """
    if not websocket_manager.jwt_secret:
        logger.error("JWT secret not set in WebSocket manager")
        return None
    
    try:
        # Decode JWT token
        payload = jwt.decode(
            token, 
            websocket_manager.jwt_secret, 
            algorithms=["HS256"]
        )
        
        # Extract user information
        user_info = {
            "id": payload.get("sub"),
            "email": payload.get("email"),
            "name": payload.get("name")
        }
        
        logger.info(f"WebSocket authenticated for user {user_info['id']}")
        return user_info
        
    except jwt.ExpiredSignatureError:
        logger.warning("WebSocket authentication failed: Token expired")
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": "Authentication token expired"
        }))
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"WebSocket authentication failed: Invalid token - {e}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": "Invalid authentication token"
        }))
        return None
    except Exception as e:
        logger.error(f"WebSocket authentication error: {e}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": "Authentication error"
        }))
        return None


async def handle_websocket_connection(websocket, user_id: str):
    """
    Handle a WebSocket connection lifecycle.
    
    Args:
        websocket: WebSocket connection
        user_id: Authenticated user ID
    """
    try:
        # Register connection
        await websocket_manager.connect(websocket, user_id)
        
        # Keep connection alive and handle messages
        while True:
            # Wait for messages (client can send pings or commands)
            try:
                message = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                
                # Handle ping/pong
                if message == "ping":
                    await websocket.send_text("pong")
                else:
                    # Handle other messages if needed
                    try:
                        data = json.loads(message)
                        if data.get("type") == "subscribe":
                            # Client can subscribe to specific channels
                            await websocket.send_text(json.dumps({
                                "type": "subscribed",
                                "channels": data.get("channels", [])
                            }))
                    except json.JSONDecodeError:
                        logger.debug(f"Invalid JSON from WebSocket: {message}")
                        
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                await websocket.send_text(json.dumps({
                    "type": "ping",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }))
                
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
    finally:
        # Clean up connection
        await websocket_manager.disconnect(websocket, user_id)