"""
Production Audit Logger
======================

Comprehensive audit logging for production trading operations.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import aiofiles
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class EventType(Enum):
    TRADING_DECISION = "trading_decision"
    RISK_ASSESSMENT = "risk_assessment"
    EXECUTION = "execution"
    SYSTEM_EVENT = "system_event"
    AGENT_EVENT = "agent_event"
    EMERGENCY_EVENT = "emergency_event"
    ERROR = "error"
    CIRCUIT_BREAKER = "circuit_breaker"
    DATA_QUALITY = "data_quality"

@dataclass
class AuditEvent:
    event_id: str
    event_type: EventType
    timestamp: datetime
    agent_id: Optional[str]
    symbol: Optional[str]
    event_data: Dict[str, Any]
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'event_id': self.event_id,
            'event_type': self.event_type.value,
            'timestamp': self.timestamp.isoformat(),
            'agent_id': self.agent_id,
            'symbol': self.symbol,
            'event_data': self.event_data,
            'metadata': self.metadata
        }

class AuditLogger:
    """
    Production-grade audit logger with structured logging and retention.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.audit_config = config.get('audit', {})
        
        # Logging configuration
        self.log_directory = Path(self.audit_config.get('log_directory', 'logs/audit'))
        self.max_file_size = self.audit_config.get('max_file_size', 100 * 1024 * 1024)  # 100MB
        self.retention_days = self.audit_config.get('retention_days', 90)
        self.compress_old_logs = self.audit_config.get('compress_old_logs', True)
        
        # Current log file
        self.current_log_file = None
        self.current_file_size = 0
        
        # Event buffer for batch writing
        self.event_buffer: List[AuditEvent] = []
        self.buffer_size = self.audit_config.get('buffer_size', 100)
        self.flush_interval = self.audit_config.get('flush_interval', 10)  # seconds
        
        # Statistics
        self.events_logged = 0
        self.last_flush_time = datetime.now()
        
        # Background tasks
        self.flush_task = None
        self.cleanup_task = None
        
    async def initialize(self):
        """Initialize the audit logger."""
        # Create log directory
        self.log_directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize current log file
        await self._initialize_log_file()
        
        # Start background tasks
        self.flush_task = asyncio.create_task(self._periodic_flush())
        self.cleanup_task = asyncio.create_task(self._periodic_cleanup())
        
        logger.info(f"Audit logger initialized: {self.log_directory}")
        
    async def log_trading_decision(self, agent_id: str, decision: Any):
        """Log a trading decision."""
        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type=EventType.TRADING_DECISION,
            timestamp=datetime.now(),
            agent_id=agent_id,
            symbol=getattr(decision, 'symbol', None),
            event_data={
                'symbol': getattr(decision, 'symbol', None),
                'action': getattr(decision, 'action', None),
                'confidence': getattr(decision, 'confidence', None),
                'reasoning': getattr(decision, 'reasoning', None),
                'recommended_quantity': getattr(decision, 'recommended_quantity', None),
                'recommended_price': getattr(decision, 'recommended_price', None),
                'stop_loss': getattr(decision, 'stop_loss', None),
                'take_profit': getattr(decision, 'take_profit', None),
                'risk_factors': getattr(decision, 'risk_factors', {}),
            },
            metadata={
                'agent_id': agent_id,
                'decision_timestamp': getattr(decision, 'timestamp', datetime.now()).isoformat()
            }
        )
        
        await self._add_event(event)
        
    async def log_risk_assessment(self, decision_id: str, assessment: Any):
        """Log a risk assessment."""
        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type=EventType.RISK_ASSESSMENT,
            timestamp=datetime.now(),
            agent_id=None,
            symbol=None,
            event_data={
                'decision_id': decision_id,
                'decision': getattr(assessment, 'decision', None),
                'risk_level': getattr(assessment, 'risk_level', None),
                'reason': getattr(assessment, 'reason', None),
                'risk_score': getattr(assessment, 'risk_score', None),
                'risk_factors': getattr(assessment, 'risk_factors', {}),
                'recommendations': getattr(assessment, 'recommendations', []),
                'modified_request': getattr(assessment, 'modified_request', None) is not None
            },
            metadata={
                'decision_id': decision_id
            }
        )
        
        await self._add_event(event)
        
    async def log_execution(self, decision_id: str, execution: Any):
        """Log a trade execution."""
        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type=EventType.EXECUTION,
            timestamp=datetime.now(),
            agent_id=None,
            symbol=getattr(execution, 'symbol', None),
            event_data={
                'decision_id': decision_id,
                'symbol': getattr(execution, 'symbol', None),
                'action': getattr(execution, 'action', None),
                'requested_quantity': getattr(execution, 'requested_quantity', None),
                'executed_quantity': getattr(execution, 'executed_quantity', None),
                'requested_price': getattr(execution, 'requested_price', None),
                'executed_price': getattr(execution, 'executed_price', None),
                'execution_status': getattr(execution, 'execution_status', None),
                'fees': getattr(execution, 'fees', None),
                'slippage': getattr(execution, 'slippage', None),
                'error_message': getattr(execution, 'error_message', None)
            },
            metadata={
                'decision_id': decision_id,
                'execution_timestamp': getattr(execution, 'execution_time', datetime.now()).isoformat(),
                'execution_metadata': getattr(execution, 'metadata', {})
            }
        )
        
        await self._add_event(event)
        
    async def log_system_event(self, event_name: str, event_data: Dict[str, Any]):
        """Log a system event."""
        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type=EventType.SYSTEM_EVENT,
            timestamp=datetime.now(),
            agent_id=None,
            symbol=None,
            event_data={
                'event_name': event_name,
                **event_data
            },
            metadata={
                'system_component': 'production_controller'
            }
        )
        
        await self._add_event(event)
        
    async def log_agent_event(self, agent_id: str, event_name: str, event_data: Dict[str, Any]):
        """Log an agent-related event."""
        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type=EventType.AGENT_EVENT,
            timestamp=datetime.now(),
            agent_id=agent_id,
            symbol=None,
            event_data={
                'event_name': event_name,
                **event_data
            },
            metadata={
                'agent_id': agent_id
            }
        )
        
        await self._add_event(event)
        
    async def log_emergency_event(self, event_name: str, reason: str, metadata: Dict[str, Any] = None):
        """Log an emergency event."""
        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type=EventType.EMERGENCY_EVENT,
            timestamp=datetime.now(),
            agent_id=None,
            symbol=None,
            event_data={
                'event_name': event_name,
                'reason': reason,
                'severity': 'CRITICAL'
            },
            metadata=metadata or {}
        )
        
        await self._add_event(event)
        
        # Immediately flush emergency events
        await self._flush_buffer()
        
    async def log_error(self, context: str, error_message: str, metadata: Dict[str, Any] = None):
        """Log an error event."""
        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type=EventType.ERROR,
            timestamp=datetime.now(),
            agent_id=None,
            symbol=None,
            event_data={
                'context': context,
                'error_message': error_message,
                'severity': 'ERROR'
            },
            metadata=metadata or {}
        )
        
        await self._add_event(event)
        
    async def log_circuit_breaker_event(self, breaker_type: str, event_data: Dict[str, Any]):
        """Log a circuit breaker event."""
        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type=EventType.CIRCUIT_BREAKER,
            timestamp=datetime.now(),
            agent_id=None,
            symbol=None,
            event_data={
                'breaker_type': breaker_type,
                **event_data
            },
            metadata={
                'system_component': 'circuit_breaker'
            }
        )
        
        await self._add_event(event)
        
    async def log_data_quality_event(self, symbol: str, quality_data: Dict[str, Any]):
        """Log a data quality event."""
        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type=EventType.DATA_QUALITY,
            timestamp=datetime.now(),
            agent_id=None,
            symbol=symbol,
            event_data={
                'symbol': symbol,
                **quality_data
            },
            metadata={
                'system_component': 'data_quality_manager'
            }
        )
        
        await self._add_event(event)
        
    async def query_events(
        self,
        event_type: Optional[EventType] = None,
        agent_id: Optional[str] = None,
        symbol: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Query audit events with filters."""
        # This is a simplified implementation
        # In production, you'd want to use a proper database or search index
        
        events = []
        log_files = list(self.log_directory.glob("audit_*.jsonl"))
        log_files.sort(reverse=True)  # Most recent first
        
        for log_file in log_files:
            if len(events) >= limit:
                break
                
            try:
                async with aiofiles.open(log_file, 'r') as f:
                    async for line in f:
                        try:
                            event_data = json.loads(line.strip())
                            
                            # Apply filters
                            if event_type and event_data.get('event_type') != event_type.value:
                                continue
                                
                            if agent_id and event_data.get('agent_id') != agent_id:
                                continue
                                
                            if symbol and event_data.get('symbol') != symbol:
                                continue
                                
                            if start_time:
                                event_time = datetime.fromisoformat(event_data['timestamp'])
                                if event_time < start_time:
                                    continue
                                    
                            if end_time:
                                event_time = datetime.fromisoformat(event_data['timestamp'])
                                if event_time > end_time:
                                    continue
                                    
                            events.append(event_data)
                            
                            if len(events) >= limit:
                                break
                                
                        except json.JSONDecodeError:
                            continue
                            
            except Exception as e:
                logger.error(f"Error reading log file {log_file}: {e}")
                continue
                
        return events[:limit]
        
    async def get_statistics(self) -> Dict[str, Any]:
        """Get audit logging statistics."""
        return {
            'total_events_logged': self.events_logged,
            'current_buffer_size': len(self.event_buffer),
            'last_flush_time': self.last_flush_time.isoformat(),
            'current_log_file': str(self.current_log_file) if self.current_log_file else None,
            'current_file_size': self.current_file_size,
            'log_directory': str(self.log_directory),
            'retention_days': self.retention_days
        }
        
    async def _add_event(self, event: AuditEvent):
        """Add event to buffer."""
        self.event_buffer.append(event)
        self.events_logged += 1
        
        # Flush if buffer is full
        if len(self.event_buffer) >= self.buffer_size:
            await self._flush_buffer()
            
    async def _flush_buffer(self):
        """Flush event buffer to disk."""
        if not self.event_buffer:
            return
            
        # Ensure log file exists
        if not self.current_log_file:
            await self._initialize_log_file()
            
        # Check if we need to rotate log file
        if self.current_file_size > self.max_file_size:
            await self._rotate_log_file()
            
        try:
            # Write events to file
            async with aiofiles.open(self.current_log_file, 'a') as f:
                for event in self.event_buffer:
                    line = json.dumps(event.to_dict(), default=str) + '\\n'
                    await f.write(line)
                    self.current_file_size += len(line.encode('utf-8'))
                    
            # Clear buffer
            self.event_buffer.clear()
            self.last_flush_time = datetime.now()
            
        except Exception as e:
            logger.error(f"Error flushing audit log: {e}")
            
    async def _initialize_log_file(self):
        """Initialize current log file."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.current_log_file = self.log_directory / f"audit_{timestamp}.jsonl"
        self.current_file_size = 0
        
        # Create file if it doesn't exist
        if not self.current_log_file.exists():
            async with aiofiles.open(self.current_log_file, 'w') as f:
                pass
                
    async def _rotate_log_file(self):
        """Rotate to a new log file."""
        logger.info(f"Rotating log file: {self.current_log_file}")
        await self._initialize_log_file()
        
    async def _periodic_flush(self):
        """Periodic buffer flush task."""
        while True:
            try:
                await asyncio.sleep(self.flush_interval)
                await self._flush_buffer()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic flush: {e}")
                
    async def _periodic_cleanup(self):
        """Periodic log cleanup task."""
        while True:
            try:
                # Run cleanup every hour
                await asyncio.sleep(3600)
                await self._cleanup_old_logs()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}")
                
    async def _cleanup_old_logs(self):
        """Clean up old log files."""
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        
        log_files = list(self.log_directory.glob("audit_*.jsonl*"))
        
        for log_file in log_files:
            try:
                # Extract timestamp from filename
                file_timestamp_str = log_file.stem.split('_', 1)[1]
                file_timestamp = datetime.strptime(file_timestamp_str, '%Y%m%d_%H%M%S')
                
                if file_timestamp < cutoff_date:
                    if self.compress_old_logs and not log_file.name.endswith('.gz'):
                        # Compress old log
                        await self._compress_log_file(log_file)
                    elif file_timestamp < cutoff_date - timedelta(days=30):
                        # Delete very old logs (even compressed ones)
                        log_file.unlink()
                        logger.info(f"Deleted old log file: {log_file}")
                        
            except Exception as e:
                logger.error(f"Error processing log file {log_file}: {e}")
                
    async def _compress_log_file(self, log_file: Path):
        """Compress a log file."""
        try:
            import gzip
            
            compressed_file = log_file.with_suffix(log_file.suffix + '.gz')
            
            with open(log_file, 'rb') as f_in:
                with gzip.open(compressed_file, 'wb') as f_out:
                    f_out.writelines(f_in)
                    
            # Remove original file
            log_file.unlink()
            
            logger.info(f"Compressed log file: {log_file} -> {compressed_file}")
            
        except Exception as e:
            logger.error(f"Error compressing log file {log_file}: {e}")
            
    def _generate_event_id(self) -> str:
        """Generate unique event ID."""
        import uuid
        return str(uuid.uuid4())
        
    async def cleanup(self):
        """Cleanup audit logger."""
        # Cancel background tasks
        if self.flush_task:
            self.flush_task.cancel()
            try:
                await self.flush_task
            except asyncio.CancelledError:
                pass
                
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
                
        # Final flush
        await self._flush_buffer()
        
        logger.info("Audit logger cleanup complete")