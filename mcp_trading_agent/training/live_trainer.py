"""
Live Training Interface
=======================

Interactive training system that allows users to train agents through live chart interaction.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import json
import uuid

logger = logging.getLogger(__name__)

class TrainingMode(Enum):
    OBSERVATION = "observation"        # Agent observes user actions
    SIMULATION = "simulation"          # Agent makes decisions, user provides feedback
    COLLABORATIVE = "collaborative"   # User and agent work together
    EVALUATION = "evaluation"         # Test agent performance

class EventType(Enum):
    CHART_ANNOTATION = "chart_annotation"
    TRADE_SIGNAL = "trade_signal"
    MARKET_ANALYSIS = "market_analysis"
    FEEDBACK = "feedback"
    CORRECTION = "correction"
    QUESTION = "question"

@dataclass
class TrainingEvent:
    event_id: str
    event_type: EventType
    timestamp: datetime
    symbol: str
    timeframe: str
    data: Dict[str, Any]
    user_id: str
    agent_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_id': self.event_id,
            'event_type': self.event_type.value,
            'timestamp': self.timestamp.isoformat(),
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'data': self.data,
            'user_id': self.user_id,
            'agent_id': self.agent_id
        }

@dataclass
class TrainingSession:
    session_id: str
    agent_id: str
    user_id: str
    mode: TrainingMode
    symbol: str
    timeframe: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    events: List[TrainingEvent] = None
    metrics: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.events is None:
            self.events = []
        if self.metrics is None:
            self.metrics = {}

class LiveTrainingInterface:
    """
    Interactive training interface for trading agents.
    
    Provides:
    - Live chart interaction
    - Real-time feedback collection
    - Agent behavior observation
    - Performance tracking
    - Learning from user actions
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.training_config = config.get('training', {})
        
        # Active training sessions
        self.active_sessions: Dict[str, TrainingSession] = {}
        
        # Event handlers
        self.event_handlers: Dict[EventType, List[Callable]] = {
            event_type: [] for event_type in EventType
        }
        
        # Training data storage
        self.training_data: Dict[str, List[TrainingEvent]] = {}
        
        # WebSocket connections for real-time updates
        self.websocket_connections: Dict[str, Any] = {}
        
        # Agent references
        self.agents: Dict[str, Any] = {}
        
    async def initialize(self, agent_controller: Any):
        """Initialize the training interface."""
        self.agent_controller = agent_controller
        
        # Set up event handlers
        self._setup_default_handlers()
        
        logger.info("Live training interface initialized")
        
    async def start_training_session(
        self,
        agent_id: str,
        user_id: str,
        mode: TrainingMode,
        symbol: str = "NQ=F",
        timeframe: str = "15m"
    ) -> TrainingSession:
        """Start a new training session."""
        
        session_id = str(uuid.uuid4())
        
        session = TrainingSession(
            session_id=session_id,
            agent_id=agent_id,
            user_id=user_id,
            mode=mode,
            symbol=symbol,
            timeframe=timeframe,
            started_at=datetime.now()
        )
        
        self.active_sessions[session_id] = session
        
        # Initialize training data for agent if not exists
        if agent_id not in self.training_data:
            self.training_data[agent_id] = []
            
        # Get agent reference
        if agent_id in self.agent_controller.agents:
            agent_instance = self.agent_controller.agents[agent_id]
            self.agents[session_id] = agent_instance.agent
            
            # Set agent to training mode
            agent_instance.agent.status = agent_instance.agent.status.TRAINING
            
        logger.info(f"Started training session {session_id} for agent {agent_id} in {mode.value} mode")
        
        return session
        
    async def end_training_session(self, session_id: str) -> Dict[str, Any]:
        """End a training session and return summary."""
        
        if session_id not in self.active_sessions:
            raise ValueError(f"Training session {session_id} not found")
            
        session = self.active_sessions[session_id]
        session.ended_at = datetime.now()
        
        # Calculate session metrics
        session.metrics = await self._calculate_session_metrics(session)
        
        # Save training data
        self.training_data[session.agent_id].extend(session.events)
        
        # Reset agent status
        if session_id in self.agents:
            agent = self.agents[session_id]
            if hasattr(agent, 'status'):
                agent.status = agent.status.ACTIVE
            del self.agents[session_id]
            
        # Remove from active sessions
        completed_session = self.active_sessions.pop(session_id)
        
        logger.info(f"Ended training session {session_id}, processed {len(session.events)} events")
        
        return {
            'session_summary': asdict(completed_session),
            'metrics': session.metrics,
            'duration_minutes': (session.ended_at - session.started_at).total_seconds() / 60
        }
        
    async def record_training_event(self, session_id: str, event_data: Dict[str, Any]) -> TrainingEvent:
        """Record a training event."""
        
        if session_id not in self.active_sessions:
            raise ValueError(f"Training session {session_id} not found")
            
        session = self.active_sessions[session_id]
        
        event = TrainingEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType(event_data['event_type']),
            timestamp=datetime.now(),
            symbol=event_data.get('symbol', session.symbol),
            timeframe=event_data.get('timeframe', session.timeframe),
            data=event_data.get('data', {}),
            user_id=session.user_id,
            agent_id=session.agent_id
        )
        
        # Add to session
        session.events.append(event)
        
        # Process event
        await self._process_training_event(session, event)
        
        # Notify handlers
        await self._notify_event_handlers(event)
        
        # Send real-time update
        await self._send_realtime_update(session_id, event)
        
        return event
        
    async def record_chart_annotation(
        self,
        session_id: str,
        annotation_data: Dict[str, Any]
    ) -> TrainingEvent:
        """Record a chart annotation event."""
        
        event_data = {
            'event_type': 'chart_annotation',
            'data': {
                'annotation_type': annotation_data.get('type', 'note'),
                'x_coordinate': annotation_data.get('x', 0),
                'y_coordinate': annotation_data.get('y', 0),
                'price_level': annotation_data.get('price', None),
                'timestamp_chart': annotation_data.get('chart_time', None),
                'text': annotation_data.get('text', ''),
                'color': annotation_data.get('color', '#FF0000'),
                'shape': annotation_data.get('shape', 'circle'),
                'metadata': annotation_data.get('metadata', {})
            }
        }
        
        return await self.record_training_event(session_id, event_data)
        
    async def record_trade_signal(
        self,
        session_id: str,
        signal_data: Dict[str, Any]
    ) -> TrainingEvent:
        """Record a trade signal event."""
        
        event_data = {
            'event_type': 'trade_signal',
            'data': {
                'signal_type': signal_data.get('signal', 'buy'),  # buy, sell, hold
                'confidence': signal_data.get('confidence', 0.5),
                'price': signal_data.get('price', None),
                'quantity': signal_data.get('quantity', 1),
                'stop_loss': signal_data.get('stop_loss', None),
                'take_profit': signal_data.get('take_profit', None),
                'reasoning': signal_data.get('reasoning', ''),
                'timeframe': signal_data.get('timeframe', session_id),
                'indicators': signal_data.get('indicators', {}),
                'metadata': signal_data.get('metadata', {})
            }
        }
        
        return await self.record_training_event(session_id, event_data)
        
    async def record_feedback(
        self,
        session_id: str,
        feedback_data: Dict[str, Any]
    ) -> TrainingEvent:
        """Record user feedback on agent decisions."""
        
        event_data = {
            'event_type': 'feedback',
            'data': {
                'feedback_type': feedback_data.get('type', 'general'),  # positive, negative, correction, suggestion
                'target_event_id': feedback_data.get('target_event_id', None),
                'rating': feedback_data.get('rating', None),  # 1-5 scale
                'comment': feedback_data.get('comment', ''),
                'correction': feedback_data.get('correction', {}),
                'explanation': feedback_data.get('explanation', ''),
                'metadata': feedback_data.get('metadata', {})
            }
        }
        
        return await self.record_training_event(session_id, event_data)
        
    async def ask_agent_question(
        self,
        session_id: str,
        question: str,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Ask the agent a question about market conditions."""
        
        if session_id not in self.active_sessions:
            raise ValueError(f"Training session {session_id} not found")
            
        session = self.active_sessions[session_id]
        agent = self.agents.get(session_id)
        
        if not agent:
            return {'error': 'Agent not available'}
            
        # Record question event
        await self.record_training_event(session_id, {
            'event_type': 'question',
            'data': {
                'question': question,
                'context': context or {},
                'timestamp': datetime.now().isoformat()
            }
        })
        
        try:
            # Get agent's response
            if hasattr(agent, 'analyze_with_llm'):
                response = await agent.analyze_with_llm(
                    prompt=f"Training Question: {question}",
                    context=context or {}
                )
            else:
                response = f"Agent analysis not available for question: {question}"
                
            # Record agent's response
            await self.record_training_event(session_id, {
                'event_type': 'market_analysis',
                'data': {
                    'question': question,
                    'response': response,
                    'confidence': 0.5,
                    'reasoning': 'Response to training question',
                    'metadata': {'question_response': True}
                }
            })
            
            return {
                'question': question,
                'response': response,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting agent response: {e}")
            return {'error': str(e)}
            
    async def get_agent_analysis(
        self,
        session_id: str,
        symbol: str = None,
        timeframe: str = None
    ) -> Dict[str, Any]:
        """Get agent's analysis of current market conditions."""
        
        if session_id not in self.active_sessions:
            raise ValueError(f"Training session {session_id} not found")
            
        session = self.active_sessions[session_id]
        agent = self.agents.get(session_id)
        
        if not agent:
            return {'error': 'Agent not available'}
            
        symbol = symbol or session.symbol
        timeframe = timeframe or session.timeframe
        
        try:
            # Get agent's market analysis
            if hasattr(agent, 'analyze_market_comprehensive'):
                decision = await agent.analyze_market_comprehensive(symbol, timeframe)
                
                # Record the analysis
                await self.record_training_event(session_id, {
                    'event_type': 'market_analysis',
                    'data': {
                        'action': decision.action,
                        'confidence': decision.confidence,
                        'reasoning': decision.reasoning,
                        'recommended_quantity': decision.recommended_quantity,
                        'recommended_price': decision.recommended_price,
                        'stop_loss': decision.stop_loss,
                        'take_profit': decision.take_profit,
                        'risk_factors': decision.risk_factors,
                        'metadata': decision.metadata
                    }
                })
                
                return {
                    'analysis': {
                        'action': decision.action,
                        'confidence': decision.confidence,
                        'reasoning': decision.reasoning,
                        'recommended_quantity': decision.recommended_quantity,
                        'recommended_price': decision.recommended_price,
                        'stop_loss': decision.stop_loss,
                        'take_profit': decision.take_profit
                    },
                    'timestamp': datetime.now().isoformat()
                }
                
            else:
                return {'error': 'Agent analysis not available'}
                
        except Exception as e:
            logger.error(f"Error getting agent analysis: {e}")
            return {'error': str(e)}
            
    async def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get current training session status."""
        
        if session_id not in self.active_sessions:
            return {'error': 'Session not found'}
            
        session = self.active_sessions[session_id]
        
        return {
            'session_id': session_id,
            'agent_id': session.agent_id,
            'user_id': session.user_id,
            'mode': session.mode.value,
            'symbol': session.symbol,
            'timeframe': session.timeframe,
            'started_at': session.started_at.isoformat(),
            'duration_minutes': (datetime.now() - session.started_at).total_seconds() / 60,
            'events_count': len(session.events),
            'recent_events': [
                event.to_dict() for event in session.events[-5:]  # Last 5 events
            ]
        }
        
    async def get_training_history(self, agent_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get training history for an agent."""
        
        if agent_id not in self.training_data:
            return []
            
        events = self.training_data[agent_id][-limit:]
        return [event.to_dict() for event in events]
        
    async def generate_training_insights(self, agent_id: str) -> Dict[str, Any]:
        """Generate insights from training data."""
        
        if agent_id not in self.training_data:
            return {'insights': [], 'statistics': {}}
            
        events = self.training_data[agent_id]
        
        insights = []
        statistics = {
            'total_events': len(events),
            'event_types': {},
            'feedback_summary': {},
            'learning_progress': {}
        }
        
        # Analyze event types
        for event in events:
            event_type = event.event_type.value
            statistics['event_types'][event_type] = statistics['event_types'].get(event_type, 0) + 1
            
        # Analyze feedback
        feedback_events = [e for e in events if e.event_type == EventType.FEEDBACK]
        positive_feedback = len([e for e in feedback_events if e.data.get('rating', 0) >= 4])
        negative_feedback = len([e for e in feedback_events if e.data.get('rating', 0) <= 2])
        
        statistics['feedback_summary'] = {
            'total_feedback': len(feedback_events),
            'positive_feedback': positive_feedback,
            'negative_feedback': negative_feedback,
            'feedback_ratio': positive_feedback / max(len(feedback_events), 1)
        }
        
        # Generate insights
        if len(events) > 10:
            insights.append("Agent has sufficient training data for analysis")
            
        if statistics['feedback_summary']['feedback_ratio'] > 0.7:
            insights.append("Agent is receiving mostly positive feedback")
        elif statistics['feedback_summary']['feedback_ratio'] < 0.3:
            insights.append("Agent needs improvement based on negative feedback")
            
        most_common_event = max(statistics['event_types'], key=statistics['event_types'].get)
        insights.append(f"Most common training activity: {most_common_event}")
        
        return {
            'insights': insights,
            'statistics': statistics,
            'recommendations': await self._generate_training_recommendations(agent_id, events)
        }
        
    def add_event_handler(self, event_type: EventType, handler: Callable):
        """Add an event handler for training events."""
        self.event_handlers[event_type].append(handler)
        
    async def connect_websocket(self, session_id: str, websocket: Any):
        """Connect WebSocket for real-time updates."""
        self.websocket_connections[session_id] = websocket
        logger.info(f"WebSocket connected for session {session_id}")
        
    async def disconnect_websocket(self, session_id: str):
        """Disconnect WebSocket."""
        if session_id in self.websocket_connections:
            del self.websocket_connections[session_id]
            logger.info(f"WebSocket disconnected for session {session_id}")
            
    def _setup_default_handlers(self):
        """Setup default event handlers."""
        
        async def log_event_handler(event: TrainingEvent):
            logger.info(f"Training event: {event.event_type.value} for agent {event.agent_id}")
            
        # Add logging handler for all event types
        for event_type in EventType:
            self.add_event_handler(event_type, log_event_handler)
            
    async def _process_training_event(self, session: TrainingSession, event: TrainingEvent):
        """Process a training event and update agent learning."""
        
        agent = self.agents.get(session.session_id)
        if not agent:
            return
            
        # Process different event types
        if event.event_type == EventType.FEEDBACK:
            # Apply feedback to agent
            await self._apply_feedback_to_agent(agent, event)
            
        elif event.event_type == EventType.TRADE_SIGNAL:
            # Learn from user trade signals
            await self._learn_from_trade_signal(agent, event)
            
        elif event.event_type == EventType.CHART_ANNOTATION:
            # Learn from chart annotations
            await self._learn_from_annotation(agent, event)
            
    async def _apply_feedback_to_agent(self, agent: Any, event: TrainingEvent):
        """Apply user feedback to agent learning."""
        
        if hasattr(agent, 'receive_feedback'):
            feedback_data = {
                'event_id': event.event_id,
                'feedback_type': event.data.get('feedback_type', 'general'),
                'rating': event.data.get('rating', None),
                'comment': event.data.get('comment', ''),
                'correction': event.data.get('correction', {}),
                'outcome': 'positive' if event.data.get('rating', 0) >= 4 else 'negative'
            }
            
            await agent.receive_feedback(event.event_id, feedback_data)
            
    async def _learn_from_trade_signal(self, agent: Any, event: TrainingEvent):
        """Learn from user trade signals."""
        
        # This could update agent's decision-making based on user signals
        # For now, we'll just log the learning opportunity
        logger.info(f"Learning opportunity from trade signal: {event.data.get('signal_type')}")
        
    async def _learn_from_annotation(self, agent: Any, event: TrainingEvent):
        """Learn from chart annotations."""
        
        # This could teach the agent about important chart patterns
        logger.info(f"Learning opportunity from annotation: {event.data.get('annotation_type')}")
        
    async def _notify_event_handlers(self, event: TrainingEvent):
        """Notify all event handlers."""
        
        handlers = self.event_handlers.get(event.event_type, [])
        
        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error(f"Error in event handler: {e}")
                
    async def _send_realtime_update(self, session_id: str, event: TrainingEvent):
        """Send real-time update via WebSocket."""
        
        if session_id in self.websocket_connections:
            websocket = self.websocket_connections[session_id]
            
            try:
                update = {
                    'type': 'training_event',
                    'session_id': session_id,
                    'event': event.to_dict()
                }
                
                await websocket.send_text(json.dumps(update))
                
            except Exception as e:
                logger.error(f"Error sending WebSocket update: {e}")
                
    async def _calculate_session_metrics(self, session: TrainingSession) -> Dict[str, Any]:
        """Calculate metrics for a training session."""
        
        metrics = {
            'duration_minutes': (session.ended_at - session.started_at).total_seconds() / 60,
            'total_events': len(session.events),
            'events_per_minute': len(session.events) / max((session.ended_at - session.started_at).total_seconds() / 60, 1),
            'event_breakdown': {},
            'feedback_metrics': {},
            'learning_score': 0.0
        }
        
        # Event breakdown
        for event in session.events:
            event_type = event.event_type.value
            metrics['event_breakdown'][event_type] = metrics['event_breakdown'].get(event_type, 0) + 1
            
        # Feedback metrics
        feedback_events = [e for e in session.events if e.event_type == EventType.FEEDBACK]
        if feedback_events:
            ratings = [e.data.get('rating', 0) for e in feedback_events if e.data.get('rating')]
            if ratings:
                metrics['feedback_metrics'] = {
                    'average_rating': sum(ratings) / len(ratings),
                    'total_feedback': len(feedback_events),
                    'positive_feedback': len([r for r in ratings if r >= 4]),
                    'negative_feedback': len([r for r in ratings if r <= 2])
                }
                
        # Calculate learning score (0-1)
        interaction_score = min(len(session.events) / 20, 1.0)  # Up to 20 events = full score
        feedback_score = metrics['feedback_metrics'].get('average_rating', 3) / 5.0 if feedback_events else 0.5
        duration_score = min(metrics['duration_minutes'] / 30, 1.0)  # Up to 30 minutes = full score
        
        metrics['learning_score'] = (interaction_score + feedback_score + duration_score) / 3
        
        return metrics
        
    async def _generate_training_recommendations(self, agent_id: str, events: List[TrainingEvent]) -> List[str]:
        """Generate training recommendations based on event history."""
        
        recommendations = []
        
        # Analyze recent events
        recent_events = events[-50:] if len(events) > 50 else events
        
        # Check for feedback patterns
        feedback_events = [e for e in recent_events if e.event_type == EventType.FEEDBACK]
        if len(feedback_events) < 5:
            recommendations.append("Provide more feedback to help the agent learn")
            
        # Check for interaction variety
        event_types = set(e.event_type for e in recent_events)
        if len(event_types) < 3:
            recommendations.append("Try different types of interactions (annotations, signals, questions)")
            
        # Check for recent activity
        if recent_events:
            last_event_time = recent_events[-1].timestamp
            hours_since_last = (datetime.now() - last_event_time).total_seconds() / 3600
            if hours_since_last > 24:
                recommendations.append("Continue regular training sessions to maintain learning progress")
                
        if not recommendations:
            recommendations.append("Training is progressing well, keep up the good work!")
            
        return recommendations
        
    async def cleanup(self):
        """Cleanup training interface resources."""
        
        # End all active sessions
        for session_id in list(self.active_sessions.keys()):
            try:
                await self.end_training_session(session_id)
            except Exception as e:
                logger.error(f"Error ending training session {session_id}: {e}")
                
        # Clear data
        self.active_sessions.clear()
        self.agents.clear()
        self.websocket_connections.clear()
        
        logger.info("Live training interface cleanup complete")