"""
WebSocket Manager for MCP Trading Agent
======================================

Handles WebSocket connections for real-time communication.
"""

import logging
import json
from typing import Dict, List, Any
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

class WebSocketManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_data: Dict[WebSocket, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str = None):
        """Accept a WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_data[websocket] = {
            "client_id": client_id,
            "subscriptions": []
        }
        logger.info(f"WebSocket connected: {client_id}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            client_id = self.connection_data.get(websocket, {}).get("client_id")
            if websocket in self.connection_data:
                del self.connection_data[websocket]
            logger.info(f"WebSocket disconnected: {client_id}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific WebSocket connection."""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Failed to send personal message: {e}")
    
    async def broadcast(self, message: str, subscription_type: str = None):
        """Broadcast a message to all connected clients or those subscribed to a type."""
        disconnected = []
        
        for websocket in self.active_connections:
            try:
                # Check if client is subscribed to this type of message
                if subscription_type:
                    subscriptions = self.connection_data.get(websocket, {}).get("subscriptions", [])
                    if subscription_type not in subscriptions:
                        continue
                
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"Failed to broadcast message: {e}")
                disconnected.append(websocket)
        
        # Clean up disconnected clients
        for websocket in disconnected:
            self.disconnect(websocket)
    
    async def broadcast_json(self, data: Dict[str, Any], subscription_type: str = None):
        """Broadcast JSON data to connected clients."""
        message = json.dumps(data)
        await self.broadcast(message, subscription_type)
    
    def subscribe(self, websocket: WebSocket, subscription_type: str):
        """Subscribe a client to a specific type of updates."""
        if websocket in self.connection_data:
            subscriptions = self.connection_data[websocket].get("subscriptions", [])
            if subscription_type not in subscriptions:
                subscriptions.append(subscription_type)
                self.connection_data[websocket]["subscriptions"] = subscriptions
                logger.info(f"Client subscribed to {subscription_type}")
    
    def unsubscribe(self, websocket: WebSocket, subscription_type: str):
        """Unsubscribe a client from a specific type of updates."""
        if websocket in self.connection_data:
            subscriptions = self.connection_data[websocket].get("subscriptions", [])
            if subscription_type in subscriptions:
                subscriptions.remove(subscription_type)
                self.connection_data[websocket]["subscriptions"] = subscriptions
                logger.info(f"Client unsubscribed from {subscription_type}")
    
    def get_connection_count(self) -> int:
        """Get the number of active connections."""
        return len(self.active_connections)
    
    def get_connection_info(self) -> List[Dict[str, Any]]:
        """Get information about all active connections."""
        return [
            {
                "client_id": data.get("client_id"),
                "subscriptions": data.get("subscriptions", [])
            }
            for data in self.connection_data.values()
        ] 