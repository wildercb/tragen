"""
Enhanced WebSocket Manager for Professional Trading Platform
===========================================================

Handles WebSocket connections for real-time communication with sub-second updates,
agent integration, and professional trading features.
"""

import asyncio
import logging
import json
import time
import uuid
from typing import Dict, List, Any, Set, Optional, Callable
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ConnectionType(Enum):
    CHART_CLIENT = "chart_client"
    TRADING_AGENT = "trading_agent"
    DASHBOARD = "dashboard"
    API_CLIENT = "api_client"

class MessagePriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class ConnectionInfo:
    """Enhanced connection metadata"""
    websocket: WebSocket
    client_id: str
    connection_type: ConnectionType
    subscriptions: Set[str]
    symbols: Set[str]
    agent_id: Optional[str]
    connected_at: datetime
    last_activity: datetime
    message_count: int
    latency_ms: float
    is_authenticated: bool
    permissions: Set[str]

@dataclass
class QueuedMessage:
    """Message queue item with priority"""
    message: str
    priority: MessagePriority
    target_connection: Optional[WebSocket]
    subscription_type: Optional[str]
    timestamp: datetime
    retry_count: int = 0

class EnhancedWebSocketManager:
    """
    Professional-grade WebSocket manager for high-frequency trading platform.
    
    Features:
    - Sub-second update capabilities
    - Agent-specific channels
    - Message prioritization
    - Connection health monitoring
    - Automatic reconnection support
    - Rate limiting and backpressure handling
    """
    
    def __init__(self, max_connections: int = 1000, max_message_rate: int = 1000):
        # Connection management
        self.active_connections: Dict[WebSocket, ConnectionInfo] = {}
        self.connections_by_type: Dict[ConnectionType, Set[WebSocket]] = defaultdict(set)
        self.connections_by_agent: Dict[str, WebSocket] = {}
        self.connections_by_symbol: Dict[str, Set[WebSocket]] = defaultdict(set)
        
        # Message queue and processing
        self.message_queue: deque = deque(maxlen=10000)
        self.message_processors: Dict[str, Callable] = {}
        self.broadcast_intervals: Dict[str, float] = {
            'price_update': 0.1,  # 100ms for price updates
            'chart_data': 0.5,    # 500ms for chart data
            'agent_signal': 0.05, # 50ms for agent signals (highest priority)
            'system_status': 5.0  # 5s for system status
        }
        
        # Performance monitoring
        self.connection_metrics: Dict[str, Any] = {
            'total_connections': 0,
            'active_connections': 0,
            'messages_sent': 0,
            'messages_failed': 0,
            'avg_latency_ms': 0.0,
            'peak_connections': 0,
            'uptime_start': datetime.now()
        }
        
        # Rate limiting
        self.max_connections = max_connections
        self.max_message_rate = max_message_rate
        self.rate_limiters: Dict[WebSocket, deque] = defaultdict(lambda: deque(maxlen=100))
        
        # Background tasks
        self.background_tasks: Set[asyncio.Task] = set()
        self.is_running = False
        
        # Health monitoring
        self.health_check_interval = 30.0  # 30 seconds
        self.last_health_check = time.time()
        
        logger.info("Enhanced WebSocket Manager initialized")
    
    async def connect(self, websocket: WebSocket, 
                     client_id: str = None, 
                     connection_type: ConnectionType = ConnectionType.CHART_CLIENT,
                     agent_id: str = None,
                     permissions: Set[str] = None) -> str:
        """Accept a WebSocket connection with enhanced metadata."""
        try:
            # Check connection limits
            if len(self.active_connections) >= self.max_connections:
                await websocket.close(code=1013, reason="Server at capacity")
                logger.warning(f"Connection rejected - at capacity: {len(self.active_connections)}")
                return None
            
            await websocket.accept()
            
            # Generate client ID if not provided
            if not client_id:
                client_id = f"{connection_type.value}_{uuid.uuid4().hex[:8]}"
            
            # Create connection info
            connection_info = ConnectionInfo(
                websocket=websocket,
                client_id=client_id,
                connection_type=connection_type,
                subscriptions=set(),
                symbols=set(),
                agent_id=agent_id,
                connected_at=datetime.now(),
                last_activity=datetime.now(),
                message_count=0,
                latency_ms=0.0,
                is_authenticated=True,  # TODO: Implement proper auth
                permissions=permissions or set()
            )
            
            # Store connection
            self.active_connections[websocket] = connection_info
            self.connections_by_type[connection_type].add(websocket)
            
            if agent_id:
                self.connections_by_agent[agent_id] = websocket
            
            # Update metrics
            self.connection_metrics['total_connections'] += 1
            self.connection_metrics['active_connections'] = len(self.active_connections)
            self.connection_metrics['peak_connections'] = max(
                self.connection_metrics['peak_connections'],
                len(self.active_connections)
            )
            
            # Start background tasks if first connection
            if not self.is_running and len(self.active_connections) == 1:
                await self.start_background_tasks()
            
            logger.info(f"WebSocket connected: {client_id} ({connection_type.value})")
            
            # Send welcome message
            await self.send_personal_message(json.dumps({
                'type': 'connection_established',
                'client_id': client_id,
                'server_time': datetime.now().isoformat(),
                'capabilities': ['real_time_data', 'agent_signals', 'chart_interaction']
            }), websocket)
            
            return client_id
            
        except Exception as e:
            logger.error(f"Failed to establish WebSocket connection: {e}")
            return None
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection with enhanced cleanup."""
        if websocket not in self.active_connections:
            return
        
        try:
            connection_info = self.active_connections[websocket]
            client_id = connection_info.client_id
            connection_type = connection_info.connection_type
            agent_id = connection_info.agent_id
            
            # Remove from all tracking structures
            del self.active_connections[websocket]
            self.connections_by_type[connection_type].discard(websocket)
            
            if agent_id and agent_id in self.connections_by_agent:
                del self.connections_by_agent[agent_id]
            
            # Remove from symbol subscriptions
            for symbol_connections in self.connections_by_symbol.values():
                symbol_connections.discard(websocket)
            
            # Update metrics
            self.connection_metrics['active_connections'] = len(self.active_connections)
            
            # Clean up rate limiter
            if websocket in self.rate_limiters:
                del self.rate_limiters[websocket]
            
            # Stop background tasks if no connections remain
            if len(self.active_connections) == 0:
                asyncio.create_task(self.stop_background_tasks())
            
            logger.info(f"WebSocket disconnected: {client_id} ({connection_type.value})")
            
        except Exception as e:
            logger.error(f"Error during disconnect cleanup: {e}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket, 
                                   priority: MessagePriority = MessagePriority.NORMAL) -> bool:
        """Send a message to a specific WebSocket connection with priority handling."""
        try:
            # Check if connection is still active
            if websocket not in self.active_connections:
                logger.debug("Attempting to send to disconnected WebSocket")
                return False
            
            connection_info = self.active_connections[websocket]
            
            # Rate limiting check
            if not self._check_rate_limit(websocket):
                logger.warning(f"Rate limit exceeded for {connection_info.client_id}")
                return False
            
            # Measure latency
            start_time = time.time()
            
            # Send message
            await websocket.send_text(message)
            
            # Update metrics
            latency = (time.time() - start_time) * 1000  # Convert to ms
            connection_info.latency_ms = latency * 0.1 + connection_info.latency_ms * 0.9  # EMA
            connection_info.message_count += 1
            connection_info.last_activity = datetime.now()
            
            self.connection_metrics['messages_sent'] += 1
            self.connection_metrics['avg_latency_ms'] = (
                self.connection_metrics['avg_latency_ms'] * 0.9 + latency * 0.1
            )
            
            return True
            
        except WebSocketDisconnect:
            logger.debug(f"WebSocket disconnected during send: {connection_info.client_id}")
            self.disconnect(websocket)
            return False
        except Exception as e:
            logger.error(f"Failed to send personal message: {e}")
            self.connection_metrics['messages_failed'] += 1
            # Remove from active connections if send fails
            if websocket in self.active_connections:
                self.disconnect(websocket)
            return False
    
    async def broadcast(self, message: str, subscription_type: str = None, 
                       priority: MessagePriority = MessagePriority.NORMAL,
                       target_symbols: Set[str] = None,
                       target_types: Set[ConnectionType] = None) -> int:
        """Enhanced broadcast with filtering and priority."""
        successful_sends = 0
        disconnected = []
        
        for websocket, connection_info in self.active_connections.items():
            try:
                # Filter by connection type
                if target_types and connection_info.connection_type not in target_types:
                    continue
                
                # Filter by subscription
                if subscription_type and subscription_type not in connection_info.subscriptions:
                    continue
                
                # Filter by symbols
                if target_symbols and not connection_info.symbols.intersection(target_symbols):
                    continue
                
                # Send message
                if await self.send_personal_message(message, websocket, priority):
                    successful_sends += 1
                else:
                    disconnected.append(websocket)
                    
            except Exception as e:
                logger.error(f"Broadcast error to {connection_info.client_id}: {e}")
                disconnected.append(websocket)
        
        # Clean up disconnected clients
        for websocket in disconnected:
            self.disconnect(websocket)
        
        return successful_sends
    
    async def broadcast_json(self, data: Dict[str, Any], 
                           subscription_type: str = None,
                           priority: MessagePriority = MessagePriority.NORMAL,
                           target_symbols: Set[str] = None,
                           target_types: Set[ConnectionType] = None) -> int:
        """Broadcast JSON data with enhanced filtering."""
        message = json.dumps(data, default=str)
        return await self.broadcast(
            message, subscription_type, priority, target_symbols, target_types
        )
    
    async def send_to_agent(self, agent_id: str, data: Dict[str, Any]) -> bool:
        """Send data directly to a specific agent."""
        if agent_id not in self.connections_by_agent:
            logger.warning(f"Agent {agent_id} not connected")
            return False
        
        websocket = self.connections_by_agent[agent_id]
        message = json.dumps(data, default=str)
        
        return await self.send_personal_message(
            message, websocket, MessagePriority.HIGH
        )
    
    async def broadcast_to_agents(self, data: Dict[str, Any], 
                                 agent_ids: Optional[Set[str]] = None) -> int:
        """Broadcast data to all or specific agents."""
        successful_sends = 0
        
        for agent_id, websocket in self.connections_by_agent.items():
            if agent_ids and agent_id not in agent_ids:
                continue
            
            message = json.dumps(data, default=str)
            if await self.send_personal_message(message, websocket, MessagePriority.HIGH):
                successful_sends += 1
        
        return successful_sends
    
    def subscribe(self, websocket: WebSocket, subscription_type: str, 
                 symbols: Optional[Set[str]] = None):
        """Subscribe a client to specific updates with symbol filtering."""
        if websocket not in self.active_connections:
            return False
        
        connection_info = self.active_connections[websocket]
        connection_info.subscriptions.add(subscription_type)
        
        if symbols:
            connection_info.symbols.update(symbols)
            for symbol in symbols:
                self.connections_by_symbol[symbol].add(websocket)
        
        logger.info(f"Client {connection_info.client_id} subscribed to {subscription_type}")
        return True
    
    def unsubscribe(self, websocket: WebSocket, subscription_type: str):
        """Unsubscribe a client from specific updates."""
        if websocket not in self.active_connections:
            return False
        
        connection_info = self.active_connections[websocket]
        connection_info.subscriptions.discard(subscription_type)
        
        logger.info(f"Client {connection_info.client_id} unsubscribed from {subscription_type}")
        return True
    
    def _check_rate_limit(self, websocket: WebSocket) -> bool:
        """Check if connection is within rate limits."""
        current_time = time.time()
        rate_limiter = self.rate_limiters[websocket]
        
        # Clean old entries (last 60 seconds)
        minute_ago = current_time - 60
        while rate_limiter and rate_limiter[0] < minute_ago:
            rate_limiter.popleft()
        
        # Check rate limit
        if len(rate_limiter) >= self.max_message_rate:
            return False
        
        rate_limiter.append(current_time)
        return True
    
    async def start_background_tasks(self):
        """Start background maintenance tasks."""
        if self.is_running:
            return
        
        self.is_running = True
        
        # Health check task
        health_task = asyncio.create_task(self._health_check_loop())
        self.background_tasks.add(health_task)
        health_task.add_done_callback(self.background_tasks.discard)
        
        # Message queue processor
        queue_task = asyncio.create_task(self._process_message_queue())
        self.background_tasks.add(queue_task)
        queue_task.add_done_callback(self.background_tasks.discard)
        
        logger.info("WebSocket background tasks started")
    
    async def stop_background_tasks(self):
        """Stop all background tasks."""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # Cancel all background tasks
        for task in self.background_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self.background_tasks:
            await asyncio.gather(*self.background_tasks, return_exceptions=True)
        
        self.background_tasks.clear()
        logger.info("WebSocket background tasks stopped")
    
    async def _health_check_loop(self):
        """Background health check for connections."""
        while self.is_running:
            try:
                current_time = time.time()
                if current_time - self.last_health_check >= self.health_check_interval:
                    await self._perform_health_check()
                    self.last_health_check = current_time
                
                await asyncio.sleep(5.0)  # Check every 5 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")
                await asyncio.sleep(5.0)
    
    async def _perform_health_check(self):
        """Perform health check on all connections."""
        disconnected = []
        current_time = datetime.now()
        
        for websocket, connection_info in self.active_connections.items():
            try:
                # Check for stale connections (no activity in 5 minutes)
                if (current_time - connection_info.last_activity).total_seconds() > 300:
                    logger.info(f"Disconnecting stale connection: {connection_info.client_id}")
                    disconnected.append(websocket)
                    continue
                
                # Send ping
                await websocket.ping()
                
            except Exception as e:
                logger.warning(f"Health check failed for {connection_info.client_id}: {e}")
                disconnected.append(websocket)
        
        # Clean up disconnected connections
        for websocket in disconnected:
            self.disconnect(websocket)
    
    async def _process_message_queue(self):
        """Process queued messages with priority."""
        while self.is_running:
            try:
                if not self.message_queue:
                    await asyncio.sleep(0.01)  # 10ms check interval
                    continue
                
                # Process messages by priority
                messages_to_process = []
                for _ in range(min(100, len(self.message_queue))):  # Process up to 100 at a time
                    if self.message_queue:
                        messages_to_process.append(self.message_queue.popleft())
                
                # Sort by priority
                messages_to_process.sort(key=lambda x: x.priority.value, reverse=True)
                
                for message in messages_to_process:
                    try:
                        if message.target_connection:
                            await self.send_personal_message(
                                message.message, message.target_connection, message.priority
                            )
                        else:
                            await self.broadcast(
                                message.message, message.subscription_type, message.priority
                            )
                    except Exception as e:
                        logger.error(f"Failed to process queued message: {e}")
                
                await asyncio.sleep(0.001)  # 1ms between batches
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Message queue processing error: {e}")
                await asyncio.sleep(0.1)
    
    def queue_message(self, message: str, 
                     priority: MessagePriority = MessagePriority.NORMAL,
                     target_connection: Optional[WebSocket] = None,
                     subscription_type: Optional[str] = None):
        """Queue a message for processing."""
        queued_message = QueuedMessage(
            message=message,
            priority=priority,
            target_connection=target_connection,
            subscription_type=subscription_type,
            timestamp=datetime.now()
        )
        
        self.message_queue.append(queued_message)
    
    def get_connection_count(self) -> int:
        """Get the number of active connections."""
        return len(self.active_connections)
    
    def get_connection_info(self) -> List[Dict[str, Any]]:
        """Get detailed information about all active connections."""
        return [
            {
                "client_id": info.client_id,
                "connection_type": info.connection_type.value,
                "agent_id": info.agent_id,
                "subscriptions": list(info.subscriptions),
                "symbols": list(info.symbols),
                "connected_at": info.connected_at.isoformat(),
                "last_activity": info.last_activity.isoformat(),
                "message_count": info.message_count,
                "latency_ms": round(info.latency_ms, 2),
                "is_authenticated": info.is_authenticated
            }
            for info in self.active_connections.values()
        ]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive WebSocket metrics."""
        uptime = (datetime.now() - self.connection_metrics['uptime_start']).total_seconds()
        
        return {
            **self.connection_metrics,
            'uptime_seconds': uptime,
            'connections_by_type': {
                conn_type.value: len(connections)
                for conn_type, connections in self.connections_by_type.items()
            },
            'active_agents': len(self.connections_by_agent),
            'queued_messages': len(self.message_queue),
            'background_tasks': len(self.background_tasks)
        }
    
    async def cleanup(self):
        """Cleanup all WebSocket resources."""
        try:
            # Disconnect all connections
            for websocket in list(self.active_connections.keys()):
                try:
                    await websocket.close()
                except:
                    pass
                self.disconnect(websocket)
            
            # Stop background tasks
            await self.stop_background_tasks()
            
            logger.info("WebSocket manager cleanup completed")
            
        except Exception as e:
            logger.error(f"WebSocket cleanup error: {e}")

# Maintain backward compatibility
WebSocketManager = EnhancedWebSocketManager 