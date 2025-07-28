"""
Chart Agent Interface for Real-Time Trading Integration
=====================================================

Professional-grade interface for AI agents to interact with live trading charts.
Provides real-time data streaming, signal processing, and multi-agent coordination.
"""

import asyncio
import logging
import json
import time
from typing import Dict, List, Any, Optional, Callable, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
from collections import defaultdict, deque
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

class SignalType(Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    STRONG_BUY = "strong_buy"
    STRONG_SELL = "strong_sell"

class SignalSource(Enum):
    TECHNICAL = "technical"
    FUNDAMENTAL = "fundamental"
    SENTIMENT = "sentiment"
    PATTERN = "pattern"
    CUSTOM = "custom"

@dataclass
class TradingSignal:
    """Professional trading signal with comprehensive metadata"""
    id: str
    agent_id: str
    symbol: str
    signal_type: SignalType
    price: float
    confidence: float  # 0.0 to 1.0
    timestamp: datetime
    timeframe: str
    source: SignalSource
    rationale: str
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    position_size: Optional[float] = None
    risk_reward_ratio: Optional[float] = None
    technical_indicators: Optional[Dict[str, float]] = None
    pattern_detected: Optional[str] = None
    market_condition: Optional[str] = None
    expiry_time: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert signal to dictionary for JSON serialization"""
        data = asdict(self)
        data['signal_type'] = self.signal_type.value
        data['source'] = self.source.value
        data['timestamp'] = self.timestamp.isoformat()
        if self.expiry_time:
            data['expiry_time'] = self.expiry_time.isoformat()
        return data

@dataclass
class ChartData:
    """Comprehensive chart data structure"""
    symbol: str
    timeframe: str
    data: List[Dict[str, Any]]
    indicators: Dict[str, List[float]]
    volume_profile: Optional[Dict[str, Any]] = None
    market_structure: Optional[Dict[str, Any]] = None
    patterns: Optional[List[Dict[str, Any]]] = None
    support_resistance: Optional[Dict[str, List[float]]] = None

@dataclass
class AgentRegistration:
    """Agent registration configuration"""
    agent_id: str
    name: str
    agent_type: str
    permissions: List[str]
    subscribed_symbols: Set[str]
    timeframes: Set[str]
    indicators: Set[str]
    max_signals_per_hour: int
    risk_tolerance: float
    strategy_description: str
    performance_metrics: Dict[str, float]
    last_activity: datetime
    is_active: bool

class ChartAgentInterface:
    """
    Production-grade interface for AI agents to interact with live trading charts.
    
    Features:
    - Real-time chart data streaming
    - Signal processing and validation
    - Multi-agent coordination
    - Performance tracking
    - Risk management
    - Pattern recognition integration
    """
    
    def __init__(self, websocket_manager, chart_data_manager):
        self.ws_manager = websocket_manager
        self.chart_data_manager = chart_data_manager
        
        # Agent management
        self.registered_agents: Dict[str, AgentRegistration] = {}
        self.agent_connections: Dict[str, Any] = {}  # WebSocket connections
        self.agent_signals: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.agent_performance: Dict[str, Dict[str, float]] = defaultdict(dict)
        
        # Signal coordination
        self.active_signals: Dict[str, List[TradingSignal]] = defaultdict(list)
        self.signal_history: deque = deque(maxlen=10000)
        self.signal_validators: List[Callable] = []
        
        # Data streaming
        self.data_streams: Dict[str, asyncio.Task] = {}
        self.streaming_agents: Dict[str, Set[str]] = defaultdict(set)  # symbol -> agent_ids
        
        # Performance monitoring
        self.metrics = {
            'total_signals': 0,
            'successful_signals': 0,
            'active_agents': 0,
            'data_streams': 0,
            'avg_response_time': 0.0
        }
        
        # Rate limiting
        self.agent_rate_limits: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        
        logger.info("ChartAgentInterface initialized")
    
    async def register_agent(self, agent_config: Dict[str, Any]) -> str:
        """Register an AI agent for chart interaction"""
        try:
            agent_id = agent_config.get('agent_id') or str(uuid.uuid4())
            
            # Validate agent configuration
            required_fields = ['name', 'agent_type', 'permissions']
            for field in required_fields:
                if field not in agent_config:
                    raise ValueError(f"Missing required field: {field}")
            
            # Create agent registration
            registration = AgentRegistration(
                agent_id=agent_id,
                name=agent_config['name'],
                agent_type=agent_config['agent_type'],
                permissions=agent_config['permissions'],
                subscribed_symbols=set(agent_config.get('symbols', [])),
                timeframes=set(agent_config.get('timeframes', ['5m'])),
                indicators=set(agent_config.get('indicators', [])),
                max_signals_per_hour=agent_config.get('max_signals_per_hour', 100),
                risk_tolerance=agent_config.get('risk_tolerance', 0.02),
                strategy_description=agent_config.get('strategy_description', ''),
                performance_metrics={
                    'total_signals': 0,
                    'profitable_signals': 0,
                    'win_rate': 0.0,
                    'avg_return': 0.0,
                    'sharpe_ratio': 0.0,
                    'max_drawdown': 0.0
                },
                last_activity=datetime.now(),
                is_active=True
            )
            
            self.registered_agents[agent_id] = registration
            self.metrics['active_agents'] = len([a for a in self.registered_agents.values() if a.is_active])
            
            logger.info(f"Agent registered: {agent_id} ({registration.name})")
            
            # Notify all clients about new agent
            await self.ws_manager.broadcast_json({
                'type': 'agent_registered',
                'agent_id': agent_id,
                'agent_info': {
                    'name': registration.name,
                    'type': registration.agent_type,
                    'strategy': registration.strategy_description
                }
            })
            
            return agent_id
            
        except Exception as e:
            logger.error(f"Failed to register agent: {e}")
            raise
    
    async def unregister_agent(self, agent_id: str):
        """Unregister an AI agent"""
        try:
            if agent_id not in self.registered_agents:
                logger.warning(f"Attempted to unregister unknown agent: {agent_id}")
                return
            
            # Stop data streams for this agent
            await self.stop_data_stream(agent_id)
            
            # Remove from all symbol subscriptions
            for symbol_agents in self.streaming_agents.values():
                symbol_agents.discard(agent_id)
            
            # Archive performance data
            agent = self.registered_agents[agent_id]
            logger.info(f"Unregistering agent {agent_id} ({agent.name}) - "
                       f"Performance: {agent.performance_metrics}")
            
            # Remove agent
            del self.registered_agents[agent_id]
            if agent_id in self.agent_connections:
                del self.agent_connections[agent_id]
            
            self.metrics['active_agents'] = len([a for a in self.registered_agents.values() if a.is_active])
            
            # Notify all clients
            await self.ws_manager.broadcast_json({
                'type': 'agent_unregistered',
                'agent_id': agent_id
            })
            
        except Exception as e:
            logger.error(f"Failed to unregister agent {agent_id}: {e}")
    
    async def stream_chart_data(self, agent_id: str, symbols: List[str], 
                               timeframes: Optional[List[str]] = None) -> bool:
        """Start streaming real-time chart data to an agent"""
        try:
            if agent_id not in self.registered_agents:
                raise ValueError(f"Agent {agent_id} not registered")
            
            agent = self.registered_agents[agent_id]
            
            # Validate permissions
            if 'read_data' not in agent.permissions:
                raise PermissionError(f"Agent {agent_id} lacks read_data permission")
            
            # Default timeframes
            if not timeframes:
                timeframes = list(agent.timeframes) or ['5m']
            
            # Subscribe agent to symbols
            for symbol in symbols:
                self.streaming_agents[symbol].add(agent_id)
                agent.subscribed_symbols.add(symbol)
            
            # Start data streaming task if not already running
            stream_key = f"{agent_id}_{'-'.join(symbols)}"
            if stream_key not in self.data_streams:
                self.data_streams[stream_key] = asyncio.create_task(
                    self._stream_data_to_agent(agent_id, symbols, timeframes)
                )
            
            agent.last_activity = datetime.now()
            self.metrics['data_streams'] = len(self.data_streams)
            
            logger.info(f"Started data stream for agent {agent_id}: {symbols}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start data stream for agent {agent_id}: {e}")
            return False
    
    async def _stream_data_to_agent(self, agent_id: str, symbols: List[str], 
                                   timeframes: List[str]):
        """Internal method to continuously stream data to an agent"""
        try:
            while agent_id in self.registered_agents and self.registered_agents[agent_id].is_active:
                for symbol in symbols:
                    for timeframe in timeframes:
                        try:
                            # Get latest chart data
                            chart_data = await self.chart_data_manager.get_chart_data(
                                symbol, timeframe, include_indicators=True
                            )
                            
                            if chart_data:
                                # Send to agent via WebSocket
                                await self._send_data_to_agent(agent_id, {
                                    'type': 'chart_data_update',
                                    'symbol': symbol,
                                    'timeframe': timeframe,
                                    'data': chart_data,
                                    'timestamp': datetime.now().isoformat()
                                })
                            
                        except Exception as e:
                            logger.error(f"Error streaming {symbol} to agent {agent_id}: {e}")
                
                # Update frequency: 500ms for high-frequency agents, 1s for others
                agent = self.registered_agents[agent_id]
                interval = 0.5 if 'high_frequency' in agent.permissions else 1.0
                await asyncio.sleep(interval)
                
        except asyncio.CancelledError:
            logger.info(f"Data stream cancelled for agent {agent_id}")
        except Exception as e:
            logger.error(f"Data streaming error for agent {agent_id}: {e}")
    
    async def receive_trading_signal(self, agent_id: str, signal_data: Dict[str, Any]) -> bool:
        """Process a trading signal from an AI agent"""
        try:
            start_time = time.time()
            
            # Validate agent
            if agent_id not in self.registered_agents:
                raise ValueError(f"Unknown agent: {agent_id}")
            
            agent = self.registered_agents[agent_id]
            
            # Check permissions
            if 'send_signals' not in agent.permissions:
                raise PermissionError(f"Agent {agent_id} lacks send_signals permission")
            
            # Rate limiting
            current_time = time.time()
            self.agent_rate_limits[agent_id].append(current_time)
            
            # Check hourly rate limit
            hour_ago = current_time - 3600
            recent_signals = len([t for t in self.agent_rate_limits[agent_id] if t > hour_ago])
            if recent_signals > agent.max_signals_per_hour:
                logger.warning(f"Rate limit exceeded for agent {agent_id}: {recent_signals} signals/hour")
                return False
            
            # Create trading signal
            signal = TradingSignal(
                id=str(uuid.uuid4()),
                agent_id=agent_id,
                symbol=signal_data['symbol'],
                signal_type=SignalType(signal_data['signal_type']),
                price=float(signal_data['price']),
                confidence=float(signal_data['confidence']),
                timestamp=datetime.now(),
                timeframe=signal_data.get('timeframe', '5m'),
                source=SignalSource(signal_data.get('source', 'technical')),
                rationale=signal_data.get('rationale', ''),
                stop_loss=signal_data.get('stop_loss'),
                take_profit=signal_data.get('take_profit'),
                position_size=signal_data.get('position_size'),
                risk_reward_ratio=signal_data.get('risk_reward_ratio'),
                technical_indicators=signal_data.get('technical_indicators'),
                pattern_detected=signal_data.get('pattern_detected'),
                market_condition=signal_data.get('market_condition'),
                expiry_time=datetime.fromisoformat(signal_data['expiry_time']) if signal_data.get('expiry_time') else None
            )
            
            # Validate signal
            is_valid = await self._validate_signal(signal)
            if not is_valid:
                logger.warning(f"Invalid signal rejected from agent {agent_id}")
                return False
            
            # Store signal
            self.agent_signals[agent_id].append(signal)
            self.active_signals[signal.symbol].append(signal)
            self.signal_history.append(signal)
            
            # Update metrics
            self.metrics['total_signals'] += 1
            agent.performance_metrics['total_signals'] += 1
            agent.last_activity = datetime.now()
            
            # Process signal coordination
            await self._coordinate_signals(signal)
            
            # Broadcast signal to all clients
            await self.ws_manager.broadcast_json({
                'type': 'trading_signal',
                'signal': signal.to_dict(),
                'agent_name': agent.name
            })
            
            # Update response time metric
            response_time = time.time() - start_time
            self.metrics['avg_response_time'] = (
                self.metrics['avg_response_time'] * 0.9 + response_time * 0.1
            )
            
            logger.info(f"Signal processed from agent {agent_id}: {signal.signal_type.value} "
                       f"{signal.symbol} @ {signal.price} (confidence: {signal.confidence:.2f})")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to process signal from agent {agent_id}: {e}")
            return False
    
    async def _validate_signal(self, signal: TradingSignal) -> bool:
        """Validate a trading signal before processing"""
        try:
            # Basic validation
            if signal.confidence < 0.0 or signal.confidence > 1.0:
                return False
            
            if signal.price <= 0:
                return False
            
            # Check if signal is not too old
            if (datetime.now() - signal.timestamp).total_seconds() > 60:
                return False
            
            # Custom validators
            for validator in self.signal_validators:
                if not await validator(signal):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Signal validation error: {e}")
            return False
    
    async def _coordinate_signals(self, new_signal: TradingSignal):
        """Coordinate multiple agent signals for the same symbol"""
        try:
            symbol_signals = self.active_signals[new_signal.symbol]
            
            # Remove expired signals
            current_time = datetime.now()
            symbol_signals[:] = [
                s for s in symbol_signals 
                if not s.expiry_time or s.expiry_time > current_time
            ]
            
            # Analyze signal consensus
            if len(symbol_signals) > 1:
                buy_signals = [s for s in symbol_signals if s.signal_type in [SignalType.BUY, SignalType.STRONG_BUY]]
                sell_signals = [s for s in symbol_signals if s.signal_type in [SignalType.SELL, SignalType.STRONG_SELL]]
                
                # Calculate weighted consensus
                buy_weight = sum(s.confidence for s in buy_signals)
                sell_weight = sum(s.confidence for s in sell_signals)
                
                consensus_data = {
                    'symbol': new_signal.symbol,
                    'total_signals': len(symbol_signals),
                    'buy_signals': len(buy_signals),
                    'sell_signals': len(sell_signals),
                    'buy_weight': buy_weight,
                    'sell_weight': sell_weight,
                    'consensus': 'buy' if buy_weight > sell_weight else 'sell' if sell_weight > buy_weight else 'neutral',
                    'strength': abs(buy_weight - sell_weight) / max(buy_weight + sell_weight, 1)
                }
                
                # Broadcast consensus update
                await self.ws_manager.broadcast_json({
                    'type': 'signal_consensus',
                    'data': consensus_data
                })
                
        except Exception as e:
            logger.error(f"Signal coordination error: {e}")
    
    async def request_analysis(self, agent_id: str, chart_data: ChartData, 
                              analysis_type: str) -> Optional[Dict[str, Any]]:
        """Request agent analysis of chart patterns"""
        try:
            if agent_id not in self.registered_agents:
                raise ValueError(f"Unknown agent: {agent_id}")
            
            agent = self.registered_agents[agent_id]
            
            if 'analyze_data' not in agent.permissions:
                raise PermissionError(f"Agent {agent_id} lacks analyze_data permission")
            
            # Send analysis request to agent
            request_id = str(uuid.uuid4())
            await self._send_data_to_agent(agent_id, {
                'type': 'analysis_request',
                'request_id': request_id,
                'analysis_type': analysis_type,
                'chart_data': asdict(chart_data),
                'timestamp': datetime.now().isoformat()
            })
            
            # Note: In a real implementation, this would wait for the agent's response
            # For now, we'll return a placeholder
            return {
                'request_id': request_id,
                'status': 'pending',
                'agent_id': agent_id
            }
            
        except Exception as e:
            logger.error(f"Analysis request failed for agent {agent_id}: {e}")
            return None
    
    async def update_agent_indicators(self, agent_id: str, indicators: Dict[str, Any]):
        """Update custom agent indicators on chart"""
        try:
            if agent_id not in self.registered_agents:
                raise ValueError(f"Unknown agent: {agent_id}")
            
            # Broadcast indicator updates to all clients
            await self.ws_manager.broadcast_json({
                'type': 'agent_indicators',
                'agent_id': agent_id,
                'indicators': indicators,
                'timestamp': datetime.now().isoformat()
            })
            
            logger.info(f"Updated indicators for agent {agent_id}")
            
        except Exception as e:
            logger.error(f"Failed to update indicators for agent {agent_id}: {e}")
    
    async def _send_data_to_agent(self, agent_id: str, data: Dict[str, Any]):
        """Send data to a specific agent via WebSocket"""
        try:
            if agent_id in self.agent_connections:
                connection = self.agent_connections[agent_id]
                await connection.send_text(json.dumps(data))
            else:
                # Broadcast to all connections for now (agent will filter by ID)
                await self.ws_manager.broadcast_json({
                    'target_agent': agent_id,
                    **data
                })
                
        except Exception as e:
            logger.error(f"Failed to send data to agent {agent_id}: {e}")
    
    async def stop_data_stream(self, agent_id: str):
        """Stop data streaming for an agent"""
        try:
            # Cancel streaming tasks
            tasks_to_cancel = [
                task for key, task in self.data_streams.items() 
                if key.startswith(agent_id)
            ]
            
            for task in tasks_to_cancel:
                task.cancel()
            
            # Remove from data_streams
            self.data_streams = {
                key: task for key, task in self.data_streams.items()
                if not key.startswith(agent_id)
            }
            
            self.metrics['data_streams'] = len(self.data_streams)
            
            logger.info(f"Stopped data streaming for agent {agent_id}")
            
        except Exception as e:
            logger.error(f"Failed to stop data stream for agent {agent_id}: {e}")
    
    def get_agent_performance(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get performance metrics for an agent"""
        if agent_id not in self.registered_agents:
            return None
        
        agent = self.registered_agents[agent_id]
        signals = list(self.agent_signals[agent_id])
        
        # Calculate additional metrics
        recent_signals = [s for s in signals if (datetime.now() - s.timestamp).days <= 7]
        
        return {
            'agent_id': agent_id,
            'name': agent.name,
            'type': agent.agent_type,
            'performance_metrics': agent.performance_metrics,
            'total_signals': len(signals),
            'recent_signals': len(recent_signals),
            'last_activity': agent.last_activity.isoformat(),
            'is_active': agent.is_active,
            'subscribed_symbols': list(agent.subscribed_symbols),
            'avg_confidence': np.mean([s.confidence for s in signals]) if signals else 0.0
        }
    
    def get_all_agents_status(self) -> Dict[str, Any]:
        """Get status of all registered agents"""
        return {
            'agents': {
                agent_id: self.get_agent_performance(agent_id)
                for agent_id in self.registered_agents
            },
            'metrics': self.metrics,
            'active_signals': {
                symbol: len(signals) 
                for symbol, signals in self.active_signals.items()
            }
        }
    
    def add_signal_validator(self, validator: Callable):
        """Add a custom signal validator function"""
        self.signal_validators.append(validator)
    
    async def cleanup(self):
        """Cleanup resources"""
        try:
            # Cancel all streaming tasks
            for task in self.data_streams.values():
                task.cancel()
            
            # Wait for tasks to complete
            if self.data_streams:
                await asyncio.gather(*self.data_streams.values(), return_exceptions=True)
            
            logger.info("ChartAgentInterface cleanup completed")
            
        except Exception as e:
            logger.error(f"Cleanup error: {e}")