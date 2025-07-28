"""
Chart Interaction Manager
=========================

Manages chart-based interactions for training agents with live market data visualization.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import json
import uuid

logger = logging.getLogger(__name__)

class AnnotationType(Enum):
    NOTE = "note"
    SUPPORT_LEVEL = "support_level"
    RESISTANCE_LEVEL = "resistance_level"
    TREND_LINE = "trend_line"
    PATTERN_HIGHLIGHT = "pattern_highlight"
    ENTRY_POINT = "entry_point"
    EXIT_POINT = "exit_point"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    VOLUME_SPIKE = "volume_spike"
    BREAKOUT = "breakout"
    REVERSAL = "reversal"

class ChartTimeframe(Enum):
    ONE_MINUTE = "1m"
    FIVE_MINUTES = "5m"
    FIFTEEN_MINUTES = "15m"
    THIRTY_MINUTES = "30m"
    ONE_HOUR = "1h"
    FOUR_HOURS = "4h"
    ONE_DAY = "1d"
    ONE_WEEK = "1w"

@dataclass
class ChartAnnotation:
    annotation_id: str
    annotation_type: AnnotationType
    symbol: str
    timeframe: ChartTimeframe
    price_level: float
    timestamp_chart: datetime
    timestamp_created: datetime
    x_coordinate: float
    y_coordinate: float
    text: str = ""
    color: str = "#FF0000"
    shape: str = "circle"
    size: int = 10
    metadata: Dict[str, Any] = None
    user_id: str = ""
    agent_id: Optional[str] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class ChartPattern:
    pattern_id: str
    pattern_type: str
    symbol: str
    timeframe: ChartTimeframe
    start_time: datetime
    end_time: datetime
    confidence: float
    coordinates: List[Tuple[float, float]]
    description: str
    identified_by: str  # 'user' or 'agent'
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class ChartInteractionManager:
    """
    Manages chart-based interactions for training trading agents.
    
    Provides:
    - Chart annotation management
    - Pattern identification
    - Real-time chart updates
    - Interactive training elements
    - Market data visualization
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.chart_config = config.get('chart', {})
        
        # Chart state management
        self.annotations: Dict[str, ChartAnnotation] = {}
        self.patterns: Dict[str, ChartPattern] = {}
        
        # Active chart sessions
        self.chart_sessions: Dict[str, Dict[str, Any]] = {}
        
        # Real-time data connections
        self.data_streams: Dict[str, Any] = {}
        
        # Chart interaction callbacks
        self.interaction_callbacks: List[callable] = []
        
    async def initialize_chart_session(
        self,
        session_id: str,
        symbol: str,
        timeframe: ChartTimeframe,
        user_id: str,
        agent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Initialize a new chart session."""
        
        chart_session = {
            'session_id': session_id,
            'symbol': symbol,
            'timeframe': timeframe,
            'user_id': user_id,
            'agent_id': agent_id,
            'created_at': datetime.now(),
            'last_update': datetime.now(),
            'annotations': [],
            'patterns': [],
            'chart_data': None,
            'indicators': {},
            'active': True
        }
        
        self.chart_sessions[session_id] = chart_session
        
        # Start real-time data stream
        await self._start_data_stream(session_id, symbol, timeframe)
        
        # Load initial chart data
        chart_data = await self._load_chart_data(symbol, timeframe)
        chart_session['chart_data'] = chart_data
        
        logger.info(f"Initialized chart session {session_id} for {symbol} on {timeframe.value}")
        
        return {
            'session_id': session_id,
            'symbol': symbol,
            'timeframe': timeframe.value,
            'chart_data': chart_data,
            'status': 'initialized'
        }
        
    async def add_annotation(
        self,
        session_id: str,
        annotation_data: Dict[str, Any]
    ) -> ChartAnnotation:
        """Add an annotation to the chart."""
        
        if session_id not in self.chart_sessions:
            raise ValueError(f"Chart session {session_id} not found")
            
        session = self.chart_sessions[session_id]
        
        annotation = ChartAnnotation(
            annotation_id=str(uuid.uuid4()),
            annotation_type=AnnotationType(annotation_data['type']),
            symbol=session['symbol'],
            timeframe=ChartTimeframe(session['timeframe'].value),
            price_level=annotation_data['price_level'],
            timestamp_chart=datetime.fromisoformat(annotation_data['chart_timestamp']),
            timestamp_created=datetime.now(),
            x_coordinate=annotation_data['x'],
            y_coordinate=annotation_data['y'],
            text=annotation_data.get('text', ''),
            color=annotation_data.get('color', '#FF0000'),
            shape=annotation_data.get('shape', 'circle'),
            size=annotation_data.get('size', 10),
            user_id=session['user_id'],
            agent_id=session.get('agent_id'),
            metadata=annotation_data.get('metadata', {})
        )
        
        # Store annotation
        self.annotations[annotation.annotation_id] = annotation
        session['annotations'].append(annotation.annotation_id)
        session['last_update'] = datetime.now()
        
        # Notify callbacks
        await self._notify_interaction_callbacks('annotation_added', {
            'session_id': session_id,
            'annotation': asdict(annotation)
        })
        
        logger.info(f"Added {annotation.annotation_type.value} annotation to session {session_id}")
        
        return annotation
        
    async def update_annotation(
        self,
        annotation_id: str,
        updates: Dict[str, Any]
    ) -> ChartAnnotation:
        """Update an existing annotation."""
        
        if annotation_id not in self.annotations:
            raise ValueError(f"Annotation {annotation_id} not found")
            
        annotation = self.annotations[annotation_id]
        
        # Update fields
        for field, value in updates.items():
            if hasattr(annotation, field):
                setattr(annotation, field, value)
                
        # Update timestamp
        annotation.timestamp_created = datetime.now()
        
        # Notify callbacks
        await self._notify_interaction_callbacks('annotation_updated', {
            'annotation_id': annotation_id,
            'annotation': asdict(annotation),
            'updates': updates
        })
        
        return annotation
        
    async def remove_annotation(self, annotation_id: str) -> bool:
        """Remove an annotation."""
        
        if annotation_id not in self.annotations:
            return False
            
        annotation = self.annotations.pop(annotation_id)
        
        # Remove from all sessions
        for session in self.chart_sessions.values():
            if annotation_id in session['annotations']:
                session['annotations'].remove(annotation_id)
                session['last_update'] = datetime.now()
                
        # Notify callbacks
        await self._notify_interaction_callbacks('annotation_removed', {
            'annotation_id': annotation_id,
            'annotation': asdict(annotation)
        })
        
        return True
        
    async def identify_pattern(
        self,
        session_id: str,
        pattern_data: Dict[str, Any],
        identified_by: str = 'user'
    ) -> ChartPattern:
        """Identify a chart pattern."""
        
        if session_id not in self.chart_sessions:
            raise ValueError(f"Chart session {session_id} not found")
            
        session = self.chart_sessions[session_id]
        
        pattern = ChartPattern(
            pattern_id=str(uuid.uuid4()),
            pattern_type=pattern_data['pattern_type'],
            symbol=session['symbol'],
            timeframe=ChartTimeframe(session['timeframe'].value),
            start_time=datetime.fromisoformat(pattern_data['start_time']),
            end_time=datetime.fromisoformat(pattern_data['end_time']),
            confidence=pattern_data.get('confidence', 0.5),
            coordinates=pattern_data['coordinates'],
            description=pattern_data.get('description', ''),
            identified_by=identified_by,
            metadata=pattern_data.get('metadata', {})
        )
        
        # Store pattern
        self.patterns[pattern.pattern_id] = pattern
        session['patterns'].append(pattern.pattern_id)
        session['last_update'] = datetime.now()
        
        # Notify callbacks
        await self._notify_interaction_callbacks('pattern_identified', {
            'session_id': session_id,
            'pattern': asdict(pattern),
            'identified_by': identified_by
        })
        
        logger.info(f"Identified {pattern.pattern_type} pattern in session {session_id}")
        
        return pattern
        
    async def get_chart_data(
        self,
        session_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        include_indicators: bool = True
    ) -> Dict[str, Any]:
        """Get chart data for a session."""
        
        if session_id not in self.chart_sessions:
            raise ValueError(f"Chart session {session_id} not found")
            
        session = self.chart_sessions[session_id]
        
        # Get base chart data
        chart_data = session.get('chart_data', {})
        
        # Filter by time range if specified
        if start_time or end_time:
            chart_data = await self._filter_chart_data(chart_data, start_time, end_time)
            
        # Add indicators if requested
        if include_indicators:
            indicators = await self._calculate_indicators(session['symbol'], session['timeframe'])
            chart_data['indicators'] = indicators
            
        # Add annotations and patterns
        chart_data['annotations'] = [
            asdict(self.annotations[ann_id]) 
            for ann_id in session['annotations'] 
            if ann_id in self.annotations
        ]
        
        chart_data['patterns'] = [
            asdict(self.patterns[pat_id]) 
            for pat_id in session['patterns'] 
            if pat_id in self.patterns
        ]
        
        return chart_data
        
    async def get_real_time_update(self, session_id: str) -> Dict[str, Any]:
        """Get real-time chart update."""
        
        if session_id not in self.chart_sessions:
            raise ValueError(f"Chart session {session_id} not found")
            
        session = self.chart_sessions[session_id]
        
        # Get latest price data
        latest_data = await self._get_latest_price_data(session['symbol'])
        
        # Calculate real-time indicators
        real_time_indicators = await self._calculate_real_time_indicators(
            session['symbol'], 
            session['timeframe']
        )
        
        return {
            'session_id': session_id,
            'timestamp': datetime.now().isoformat(),
            'latest_price': latest_data,
            'indicators': real_time_indicators,
            'volume': latest_data.get('volume', 0),
            'change': latest_data.get('change', 0),
            'change_percent': latest_data.get('change_percent', 0)
        }
        
    async def add_technical_indicator(
        self,
        session_id: str,
        indicator_name: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Add a technical indicator to the chart."""
        
        if session_id not in self.chart_sessions:
            raise ValueError(f"Chart session {session_id} not found")
            
        session = self.chart_sessions[session_id]
        
        # Calculate indicator values
        indicator_data = await self._calculate_specific_indicator(
            session['symbol'],
            session['timeframe'],
            indicator_name,
            parameters
        )
        
        # Store in session
        session['indicators'][indicator_name] = {
            'parameters': parameters,
            'data': indicator_data,
            'added_at': datetime.now().isoformat()
        }
        
        session['last_update'] = datetime.now()
        
        # Notify callbacks
        await self._notify_interaction_callbacks('indicator_added', {
            'session_id': session_id,
            'indicator_name': indicator_name,
            'parameters': parameters
        })
        
        return {
            'indicator_name': indicator_name,
            'data': indicator_data,
            'status': 'added'
        }
        
    async def remove_technical_indicator(self, session_id: str, indicator_name: str) -> bool:
        """Remove a technical indicator from the chart."""
        
        if session_id not in self.chart_sessions:
            return False
            
        session = self.chart_sessions[session_id]
        
        if indicator_name in session['indicators']:
            del session['indicators'][indicator_name]
            session['last_update'] = datetime.now()
            
            # Notify callbacks
            await self._notify_interaction_callbacks('indicator_removed', {
                'session_id': session_id,
                'indicator_name': indicator_name
            })
            
            return True
            
        return False
        
    async def get_session_annotations(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all annotations for a session."""
        
        if session_id not in self.chart_sessions:
            return []
            
        session = self.chart_sessions[session_id]
        
        return [
            asdict(self.annotations[ann_id])
            for ann_id in session['annotations']
            if ann_id in self.annotations
        ]
        
    async def get_session_patterns(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all patterns for a session."""
        
        if session_id not in self.chart_sessions:
            return []
            
        session = self.chart_sessions[session_id]
        
        return [
            asdict(self.patterns[pat_id])
            for pat_id in session['patterns']
            if pat_id in self.patterns
        ]
        
    async def suggest_annotations(
        self,
        session_id: str,
        agent_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate annotation suggestions based on agent analysis."""
        
        if session_id not in self.chart_sessions:
            return []
            
        session = self.chart_sessions[session_id]
        suggestions = []
        
        # Analyze agent's reasoning and suggest annotations
        reasoning = agent_analysis.get('reasoning', '')
        action = agent_analysis.get('action', 'hold')
        confidence = agent_analysis.get('confidence', 0.5)
        
        # Suggest entry point if agent recommends buy/sell
        if action in ['buy', 'sell'] and confidence > 0.6:
            current_price = agent_analysis.get('recommended_price', 0)
            if current_price > 0:
                suggestions.append({
                    'type': 'entry_point',
                    'price_level': current_price,
                    'text': f"Agent suggests {action} at ${current_price:.2f}",
                    'confidence': confidence,
                    'reasoning': reasoning[:100]
                })
                
        # Suggest stop loss if provided
        stop_loss = agent_analysis.get('stop_loss')
        if stop_loss:
            suggestions.append({
                'type': 'stop_loss',
                'price_level': stop_loss,
                'text': f"Agent suggests stop loss at ${stop_loss:.2f}",
                'color': '#FF0000'
            })
            
        # Suggest take profit if provided
        take_profit = agent_analysis.get('take_profit')
        if take_profit:
            suggestions.append({
                'type': 'take_profit',
                'price_level': take_profit,
                'text': f"Agent suggests take profit at ${take_profit:.2f}",
                'color': '#00FF00'
            })
            
        return suggestions
        
    def add_interaction_callback(self, callback: callable):
        """Add a callback for chart interactions."""
        self.interaction_callbacks.append(callback)
        
    async def close_chart_session(self, session_id: str) -> Dict[str, Any]:
        """Close a chart session."""
        
        if session_id not in self.chart_sessions:
            return {'error': 'Session not found'}
            
        session = self.chart_sessions[session_id]
        session['active'] = False
        session['closed_at'] = datetime.now()
        
        # Stop data stream
        await self._stop_data_stream(session_id)
        
        # Create session summary
        summary = {
            'session_id': session_id,
            'duration_minutes': (datetime.now() - session['created_at']).total_seconds() / 60,
            'annotations_created': len(session['annotations']),
            'patterns_identified': len(session['patterns']),
            'indicators_used': list(session['indicators'].keys()),
            'symbol': session['symbol'],
            'timeframe': session['timeframe'].value
        }
        
        # Remove from active sessions
        del self.chart_sessions[session_id]
        
        logger.info(f"Closed chart session {session_id}")
        
        return summary
        
    async def _start_data_stream(self, session_id: str, symbol: str, timeframe: ChartTimeframe):
        """Start real-time data stream for a chart session."""
        
        # This would integrate with real data providers
        # For now, we'll create a placeholder
        self.data_streams[session_id] = {
            'symbol': symbol,
            'timeframe': timeframe,
            'active': True,
            'last_update': datetime.now()
        }
        
        logger.info(f"Started data stream for {symbol} on {timeframe.value}")
        
    async def _stop_data_stream(self, session_id: str):
        """Stop real-time data stream."""
        
        if session_id in self.data_streams:
            self.data_streams[session_id]['active'] = False
            del self.data_streams[session_id]
            
    async def _load_chart_data(self, symbol: str, timeframe: ChartTimeframe) -> Dict[str, Any]:
        """Load historical chart data."""
        
        # This would integrate with actual data providers
        # For now, return sample structure
        return {
            'symbol': symbol,
            'timeframe': timeframe.value,
            'data': [],  # OHLCV data
            'last_update': datetime.now().isoformat(),
            'data_quality': 'good'
        }
        
    async def _filter_chart_data(
        self,
        chart_data: Dict[str, Any],
        start_time: Optional[datetime],
        end_time: Optional[datetime]
    ) -> Dict[str, Any]:
        """Filter chart data by time range."""
        
        # Implementation would filter the actual data
        filtered_data = chart_data.copy()
        filtered_data['filtered'] = True
        filtered_data['filter_start'] = start_time.isoformat() if start_time else None
        filtered_data['filter_end'] = end_time.isoformat() if end_time else None
        
        return filtered_data
        
    async def _calculate_indicators(self, symbol: str, timeframe: ChartTimeframe) -> Dict[str, Any]:
        """Calculate technical indicators."""
        
        # This would calculate actual technical indicators
        return {
            'sma_20': [],
            'sma_50': [],
            'rsi_14': [],
            'macd': [],
            'bollinger_bands': [],
            'calculated_at': datetime.now().isoformat()
        }
        
    async def _calculate_specific_indicator(
        self,
        symbol: str,
        timeframe: ChartTimeframe,
        indicator_name: str,
        parameters: Dict[str, Any]
    ) -> List[float]:
        """Calculate a specific technical indicator."""
        
        # This would calculate the actual indicator
        return []
        
    async def _calculate_real_time_indicators(self, symbol: str, timeframe: ChartTimeframe) -> Dict[str, Any]:
        """Calculate real-time indicator values."""
        
        return {
            'current_sma_20': 0.0,
            'current_rsi': 50.0,
            'current_macd': 0.0,
            'timestamp': datetime.now().isoformat()
        }
        
    async def _get_latest_price_data(self, symbol: str) -> Dict[str, Any]:
        """Get latest price data."""
        
        return {
            'symbol': symbol,
            'price': 0.0,
            'volume': 0,
            'change': 0.0,
            'change_percent': 0.0,
            'timestamp': datetime.now().isoformat()
        }
        
    async def _notify_interaction_callbacks(self, event_type: str, data: Dict[str, Any]):
        """Notify all interaction callbacks."""
        
        for callback in self.interaction_callbacks:
            try:
                await callback(event_type, data)
            except Exception as e:
                logger.error(f"Error in interaction callback: {e}")
                
    async def cleanup(self):
        """Cleanup chart interaction resources."""
        
        # Close all active sessions
        for session_id in list(self.chart_sessions.keys()):
            try:
                await self.close_chart_session(session_id)
            except Exception as e:
                logger.error(f"Error closing chart session {session_id}: {e}")
                
        # Clear data
        self.annotations.clear()
        self.patterns.clear()
        self.data_streams.clear()
        
        logger.info("Chart interaction manager cleanup complete")