"""
Circuit Breaker System
=====================

Emergency halt system for production trading with multiple trigger conditions.
"""

import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)

class CircuitBreakerType(Enum):
    DAILY_LOSS = "daily_loss"
    CONSECUTIVE_LOSS = "consecutive_loss"
    VOLATILITY = "volatility"
    SYSTEM_ERROR = "system_error"
    DATA_QUALITY = "data_quality"
    MANUAL = "manual"
    POSITION_LIMIT = "position_limit"
    DRAWDOWN = "drawdown"

class BreakerStatus(Enum):
    NORMAL = "normal"
    WARNING = "warning"
    TRIGGERED = "triggered"
    COOLING_DOWN = "cooling_down"

@dataclass
class BreakerEvent:
    breaker_type: CircuitBreakerType
    status: BreakerStatus
    trigger_value: float
    threshold: float
    message: str
    timestamp: datetime
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class BreakerConfig:
    breaker_type: CircuitBreakerType
    threshold: float
    warning_threshold: Optional[float] = None
    cooldown_minutes: int = 30
    enabled: bool = True
    auto_reset: bool = False
    require_manual_reset: bool = True

class CircuitBreaker:
    """Base circuit breaker implementation."""
    
    def __init__(self, config: BreakerConfig):
        self.config = config
        self.status = BreakerStatus.NORMAL
        self.trigger_time: Optional[datetime] = None
        self.trigger_value: Optional[float] = None
        self.event_history: List[BreakerEvent] = []
        
        # Callbacks
        self.on_trigger_callbacks: List[Callable] = []
        self.on_reset_callbacks: List[Callable] = []
        
    def is_triggered(self) -> bool:
        """Check if circuit breaker is triggered."""
        return self.status == BreakerStatus.TRIGGERED
        
    def is_cooling_down(self) -> bool:
        """Check if circuit breaker is in cooldown."""
        return self.status == BreakerStatus.COOLING_DOWN
        
    def should_halt_trading(self) -> bool:
        """Check if trading should be halted."""
        return self.status in [BreakerStatus.TRIGGERED, BreakerStatus.COOLING_DOWN]
        
    async def check(self, current_value: float, metadata: Dict[str, Any] = None) -> BreakerEvent:
        """Check current value against thresholds."""
        if not self.config.enabled:
            return None
            
        event = None
        
        # Check if already triggered and should reset
        if self.status == BreakerStatus.TRIGGERED:
            if self._should_auto_reset():
                await self.reset()
                
        # Check warning threshold
        if (self.config.warning_threshold and 
            current_value >= self.config.warning_threshold and 
            self.status == BreakerStatus.NORMAL):
            
            self.status = BreakerStatus.WARNING
            event = BreakerEvent(
                breaker_type=self.config.breaker_type,
                status=BreakerStatus.WARNING,
                trigger_value=current_value,
                threshold=self.config.warning_threshold,
                message=self._get_warning_message(current_value),
                timestamp=datetime.now(),
                metadata=metadata or {}
            )
            
        # Check trigger threshold
        if (current_value >= self.config.threshold and 
            self.status != BreakerStatus.TRIGGERED):
            
            await self.trigger(current_value, metadata)
            event = BreakerEvent(
                breaker_type=self.config.breaker_type,
                status=BreakerStatus.TRIGGERED,
                trigger_value=current_value,
                threshold=self.config.threshold,
                message=self._get_trigger_message(current_value),
                timestamp=datetime.now(),
                metadata=metadata or {}
            )
            
        if event:
            self.event_history.append(event)
            # Keep only recent events
            if len(self.event_history) > 100:
                self.event_history = self.event_history[-100:]
                
        return event
        
    async def trigger(self, value: float, metadata: Dict[str, Any] = None):
        """Trigger the circuit breaker."""
        if self.status == BreakerStatus.TRIGGERED:
            return  # Already triggered
            
        self.status = BreakerStatus.TRIGGERED
        self.trigger_time = datetime.now()
        self.trigger_value = value
        
        logger.critical(
            f"CIRCUIT BREAKER TRIGGERED: {self.config.breaker_type.value} "
            f"(value: {value}, threshold: {self.config.threshold})"
        )
        
        # Execute callbacks
        for callback in self.on_trigger_callbacks:
            try:
                await callback(self, value, metadata)
            except Exception as e:
                logger.error(f"Error in circuit breaker trigger callback: {e}")
                
    async def reset(self, manual: bool = False):
        """Reset the circuit breaker."""
        if self.status == BreakerStatus.NORMAL:
            return  # Already normal
            
        if self.config.require_manual_reset and not manual:
            logger.warning(f"Circuit breaker {self.config.breaker_type.value} requires manual reset")
            return
            
        old_status = self.status
        self.status = BreakerStatus.NORMAL
        self.trigger_time = None
        self.trigger_value = None
        
        logger.info(f"Circuit breaker reset: {self.config.breaker_type.value}")
        
        # Execute callbacks
        for callback in self.on_reset_callbacks:
            try:
                await callback(self, old_status)
            except Exception as e:
                logger.error(f"Error in circuit breaker reset callback: {e}")
                
    def _should_auto_reset(self) -> bool:
        """Check if breaker should auto-reset."""
        if not self.config.auto_reset or not self.trigger_time:
            return False
            
        cooldown_time = timedelta(minutes=self.config.cooldown_minutes)
        return datetime.now() - self.trigger_time >= cooldown_time
        
    def _get_warning_message(self, value: float) -> str:
        """Get warning message."""
        return f"{self.config.breaker_type.value} warning: {value} >= {self.config.warning_threshold}"
        
    def _get_trigger_message(self, value: float) -> str:
        """Get trigger message."""
        return f"{self.config.breaker_type.value} triggered: {value} >= {self.config.threshold}"
        
    def add_trigger_callback(self, callback: Callable):
        """Add callback for trigger events."""
        self.on_trigger_callbacks.append(callback)
        
    def add_reset_callback(self, callback: Callable):
        """Add callback for reset events."""
        self.on_reset_callbacks.append(callback)
        
    def get_status_info(self) -> Dict[str, Any]:
        """Get detailed status information."""
        return {
            'type': self.config.breaker_type.value,
            'status': self.status.value,
            'enabled': self.config.enabled,
            'threshold': self.config.threshold,
            'warning_threshold': self.config.warning_threshold,
            'trigger_time': self.trigger_time.isoformat() if self.trigger_time else None,
            'trigger_value': self.trigger_value,
            'cooldown_minutes': self.config.cooldown_minutes,
            'auto_reset': self.config.auto_reset,
            'require_manual_reset': self.config.require_manual_reset,
            'event_count': len(self.event_history)
        }

class DailyLossBreaker(CircuitBreaker):
    """Circuit breaker for daily loss limits."""
    
    def __init__(self, config: Dict[str, Any]):
        breaker_config = BreakerConfig(
            breaker_type=CircuitBreakerType.DAILY_LOSS,
            threshold=config.get('threshold', 0.05),  # 5% daily loss
            warning_threshold=config.get('warning_threshold', 0.03),  # 3% warning
            cooldown_minutes=config.get('cooldown_minutes', 60),  # 1 hour cooldown
            enabled=config.get('enabled', True),
            auto_reset=config.get('auto_reset', True),  # Reset at market open
            require_manual_reset=config.get('require_manual_reset', False)
        )
        super().__init__(breaker_config)
        
    async def check_daily_loss(self, daily_pnl: float, account_value: float) -> BreakerEvent:
        """Check daily loss percentage."""
        if account_value <= 0:
            return None
            
        loss_percentage = abs(daily_pnl) / account_value if daily_pnl < 0 else 0
        
        return await self.check(
            loss_percentage,
            metadata={
                'daily_pnl': daily_pnl,
                'account_value': account_value,
                'loss_percentage': loss_percentage
            }
        )

class ConsecutiveLossBreaker(CircuitBreaker):
    """Circuit breaker for consecutive losses."""
    
    def __init__(self, config: Dict[str, Any]):
        breaker_config = BreakerConfig(
            breaker_type=CircuitBreakerType.CONSECUTIVE_LOSS,
            threshold=config.get('threshold', 5),  # 5 consecutive losses
            warning_threshold=config.get('warning_threshold', 3),  # 3 losses warning
            cooldown_minutes=config.get('cooldown_minutes', 30),
            enabled=config.get('enabled', True),
            auto_reset=config.get('auto_reset', False),
            require_manual_reset=config.get('require_manual_reset', True)
        )
        super().__init__(breaker_config)
        self.consecutive_losses = 0
        self.loss_history: List[datetime] = []
        
    async def record_trade_result(self, is_loss: bool) -> BreakerEvent:
        """Record trade result and check for consecutive losses."""
        if is_loss:
            self.consecutive_losses += 1
            self.loss_history.append(datetime.now())
        else:
            self.consecutive_losses = 0  # Reset on profit
            
        # Keep only recent history
        if len(self.loss_history) > 20:
            self.loss_history = self.loss_history[-20:]
            
        return await self.check(
            self.consecutive_losses,
            metadata={
                'consecutive_losses': self.consecutive_losses,
                'recent_losses': len(self.loss_history)
            }
        )

class VolatilityBreaker(CircuitBreaker):
    """Circuit breaker for high market volatility."""
    
    def __init__(self, config: Dict[str, Any]):
        breaker_config = BreakerConfig(
            breaker_type=CircuitBreakerType.VOLATILITY,
            threshold=config.get('threshold', 0.15),  # 15% volatility
            warning_threshold=config.get('warning_threshold', 0.10),  # 10% warning
            cooldown_minutes=config.get('cooldown_minutes', 15),  # 15 minutes
            enabled=config.get('enabled', True),
            auto_reset=config.get('auto_reset', True),
            require_manual_reset=config.get('require_manual_reset', False)
        )
        super().__init__(breaker_config)
        
    async def check_volatility(self, current_volatility: float, symbol: str = None) -> BreakerEvent:
        """Check current market volatility."""
        return await self.check(
            current_volatility,
            metadata={
                'volatility': current_volatility,
                'symbol': symbol
            }
        )

class SystemErrorBreaker(CircuitBreaker):
    """Circuit breaker for system errors."""
    
    def __init__(self, config: Dict[str, Any]):
        breaker_config = BreakerConfig(
            breaker_type=CircuitBreakerType.SYSTEM_ERROR,
            threshold=config.get('threshold', 0.10),  # 10% error rate
            warning_threshold=config.get('warning_threshold', 0.05),  # 5% warning
            cooldown_minutes=config.get('cooldown_minutes', 60),
            enabled=config.get('enabled', True),
            auto_reset=config.get('auto_reset', False),
            require_manual_reset=config.get('require_manual_reset', True)
        )
        super().__init__(breaker_config)
        self.error_count = 0
        self.total_requests = 0
        self.error_history: List[Tuple[datetime, str]] = []
        
    async def record_error(self, error_message: str) -> BreakerEvent:
        """Record a system error."""
        self.error_count += 1
        self.total_requests += 1
        self.error_history.append((datetime.now(), error_message))
        
        # Clean old errors (older than 1 hour)
        cutoff_time = datetime.now() - timedelta(hours=1)
        self.error_history = [
            (timestamp, msg) for timestamp, msg in self.error_history
            if timestamp > cutoff_time
        ]
        
        error_rate = self.error_count / self.total_requests if self.total_requests > 0 else 0
        
        return await self.check(
            error_rate,
            metadata={
                'error_count': self.error_count,
                'total_requests': self.total_requests,
                'error_rate': error_rate,
                'recent_error': error_message
            }
        )
        
    async def record_success(self):
        """Record a successful operation."""
        self.total_requests += 1

class CircuitBreakerSystem:
    """
    Comprehensive circuit breaker system for production trading.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.breaker_config = config.get('circuit_breakers', {})
        
        # Initialize breakers
        self.breakers: Dict[CircuitBreakerType, CircuitBreaker] = {}
        self._initialize_breakers()
        
        # Global callbacks
        self.global_trigger_callbacks: List[Callable] = []
        self.global_reset_callbacks: List[Callable] = []
        
        # Emergency halt state
        self.emergency_halt = False
        self.halt_reason = ""
        self.halt_time: Optional[datetime] = None
        
        # Event log
        self.event_log: List[BreakerEvent] = []
        
    def _initialize_breakers(self):
        """Initialize all circuit breakers."""
        
        # Daily loss breaker
        if self.breaker_config.get('daily_loss', {}).get('enabled', True):
            self.breakers[CircuitBreakerType.DAILY_LOSS] = DailyLossBreaker(
                self.breaker_config.get('daily_loss', {})
            )
            
        # Consecutive loss breaker
        if self.breaker_config.get('consecutive_loss', {}).get('enabled', True):
            self.breakers[CircuitBreakerType.CONSECUTIVE_LOSS] = ConsecutiveLossBreaker(
                self.breaker_config.get('consecutive_loss', {})
            )
            
        # Volatility breaker
        if self.breaker_config.get('volatility', {}).get('enabled', True):
            self.breakers[CircuitBreakerType.VOLATILITY] = VolatilityBreaker(
                self.breaker_config.get('volatility', {})
            )
            
        # System error breaker
        if self.breaker_config.get('system_error', {}).get('enabled', True):
            self.breakers[CircuitBreakerType.SYSTEM_ERROR] = SystemErrorBreaker(
                self.breaker_config.get('system_error', {})
            )
            
        # Add trigger callbacks to all breakers
        for breaker in self.breakers.values():
            breaker.add_trigger_callback(self._on_breaker_triggered)
            breaker.add_reset_callback(self._on_breaker_reset)
            
        logger.info(f"Initialized {len(self.breakers)} circuit breakers")
        
    async def should_halt_trading(self) -> Tuple[bool, str]:
        """Check if trading should be halted."""
        if self.emergency_halt:
            return True, f"Emergency halt: {self.halt_reason}"
            
        # Check all breakers
        triggered_breakers = []
        for breaker_type, breaker in self.breakers.items():
            if breaker.should_halt_trading():
                triggered_breakers.append(breaker_type.value)
                
        if triggered_breakers:
            reason = f"Circuit breakers triggered: {', '.join(triggered_breakers)}"
            return True, reason
            
        return False, ""
        
    async def check_daily_loss(self, daily_pnl: float, account_value: float) -> Optional[BreakerEvent]:
        """Check daily loss circuit breaker."""
        breaker = self.breakers.get(CircuitBreakerType.DAILY_LOSS)
        if breaker:
            event = await breaker.check_daily_loss(daily_pnl, account_value)
            if event:
                self.event_log.append(event)
            return event
        return None
        
    async def record_trade_result(self, is_loss: bool) -> Optional[BreakerEvent]:
        """Record trade result for consecutive loss tracking."""
        breaker = self.breakers.get(CircuitBreakerType.CONSECUTIVE_LOSS)
        if breaker:
            event = await breaker.record_trade_result(is_loss)
            if event:
                self.event_log.append(event)
            return event
        return None
        
    async def check_volatility(self, volatility: float, symbol: str = None) -> Optional[BreakerEvent]:
        """Check volatility circuit breaker."""
        breaker = self.breakers.get(CircuitBreakerType.VOLATILITY)
        if breaker:
            event = await breaker.check_volatility(volatility, symbol)
            if event:
                self.event_log.append(event)
            return event
        return None
        
    async def record_system_error(self, error_message: str) -> Optional[BreakerEvent]:
        """Record system error."""
        breaker = self.breakers.get(CircuitBreakerType.SYSTEM_ERROR)
        if breaker:
            event = await breaker.record_error(error_message)
            if event:
                self.event_log.append(event)
            return event
        return None
        
    async def record_system_success(self):
        """Record successful system operation."""
        breaker = self.breakers.get(CircuitBreakerType.SYSTEM_ERROR)
        if breaker:
            await breaker.record_success()
            
    async def trigger_emergency_halt(self, reason: str):
        """Trigger emergency halt of all trading."""
        self.emergency_halt = True
        self.halt_reason = reason
        self.halt_time = datetime.now()
        
        logger.critical(f"EMERGENCY HALT TRIGGERED: {reason}")
        
        # Create manual breaker event
        event = BreakerEvent(
            breaker_type=CircuitBreakerType.MANUAL,
            status=BreakerStatus.TRIGGERED,
            trigger_value=1.0,
            threshold=1.0,
            message=f"Manual emergency halt: {reason}",
            timestamp=datetime.now(),
            metadata={'reason': reason}
        )
        
        self.event_log.append(event)
        
        # Execute global callbacks
        for callback in self.global_trigger_callbacks:
            try:
                await callback(event)
            except Exception as e:
                logger.error(f"Error in global trigger callback: {e}")
                
    async def reset_emergency_halt(self):
        """Reset emergency halt."""
        if not self.emergency_halt:
            return
            
        self.emergency_halt = False
        old_reason = self.halt_reason
        self.halt_reason = ""
        self.halt_time = None
        
        logger.info("Emergency halt reset")
        
        # Execute global callbacks
        for callback in self.global_reset_callbacks:
            try:
                await callback(old_reason)
            except Exception as e:
                logger.error(f"Error in global reset callback: {e}")
                
    async def reset_breaker(self, breaker_type: CircuitBreakerType, manual: bool = True):
        """Reset a specific circuit breaker."""
        breaker = self.breakers.get(breaker_type)
        if breaker:
            await breaker.reset(manual=manual)
            
    async def reset_all_breakers(self, manual: bool = True):
        """Reset all circuit breakers."""
        for breaker in self.breakers.values():
            await breaker.reset(manual=manual)
            
        if self.emergency_halt:
            await self.reset_emergency_halt()
            
    def add_global_trigger_callback(self, callback: Callable):
        """Add global trigger callback."""
        self.global_trigger_callbacks.append(callback)
        
    def add_global_reset_callback(self, callback: Callable):
        """Add global reset callback."""
        self.global_reset_callbacks.append(callback)
        
    async def _on_breaker_triggered(self, breaker: CircuitBreaker, value: float, metadata: Dict[str, Any]):
        """Handle breaker trigger."""
        event = BreakerEvent(
            breaker_type=breaker.config.breaker_type,
            status=BreakerStatus.TRIGGERED,
            trigger_value=value,
            threshold=breaker.config.threshold,
            message=f"{breaker.config.breaker_type.value} circuit breaker triggered",
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        
        self.event_log.append(event)
        
        # Execute global callbacks
        for callback in self.global_trigger_callbacks:
            try:
                await callback(event)
            except Exception as e:
                logger.error(f"Error in global trigger callback: {e}")
                
    async def _on_breaker_reset(self, breaker: CircuitBreaker, old_status: BreakerStatus):
        """Handle breaker reset."""
        logger.info(f"Circuit breaker reset: {breaker.config.breaker_type.value}")
        
        # Execute global callbacks
        for callback in self.global_reset_callbacks:
            try:
                await callback(breaker.config.breaker_type.value)
            except Exception as e:
                logger.error(f"Error in global reset callback: {e}")
                
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        triggered_breakers = []
        warning_breakers = []
        
        for breaker_type, breaker in self.breakers.items():
            if breaker.status == BreakerStatus.TRIGGERED:
                triggered_breakers.append(breaker_type.value)
            elif breaker.status == BreakerStatus.WARNING:
                warning_breakers.append(breaker_type.value)
                
        should_halt, halt_reason = await self.should_halt_trading()
        
        return {
            'should_halt_trading': should_halt,
            'halt_reason': halt_reason,
            'emergency_halt': self.emergency_halt,
            'emergency_halt_reason': self.halt_reason,
            'emergency_halt_time': self.halt_time.isoformat() if self.halt_time else None,
            'triggered_breakers': triggered_breakers,
            'warning_breakers': warning_breakers,
            'total_breakers': len(self.breakers),
            'active_breakers': len([b for b in self.breakers.values() if b.config.enabled]),
            'recent_events': len(self.event_log[-10:]),
            'breaker_details': {
                breaker_type.value: breaker.get_status_info()
                for breaker_type, breaker in self.breakers.items()
            }
        }
        
    def get_recent_events(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent circuit breaker events."""
        recent_events = self.event_log[-limit:] if self.event_log else []
        
        return [
            {
                'type': event.breaker_type.value,
                'status': event.status.value,
                'trigger_value': event.trigger_value,
                'threshold': event.threshold,
                'message': event.message,
                'timestamp': event.timestamp.isoformat(),
                'metadata': event.metadata
            }
            for event in recent_events
        ]
        
    def enable_breaker(self, breaker_type: CircuitBreakerType):
        """Enable a circuit breaker."""
        breaker = self.breakers.get(breaker_type)
        if breaker:
            breaker.config.enabled = True
            logger.info(f"Enabled circuit breaker: {breaker_type.value}")
            
    def disable_breaker(self, breaker_type: CircuitBreakerType):
        """Disable a circuit breaker."""
        breaker = self.breakers.get(breaker_type)
        if breaker:
            breaker.config.enabled = False
            logger.info(f"Disabled circuit breaker: {breaker_type.value}")
            
    def update_breaker_threshold(self, breaker_type: CircuitBreakerType, threshold: float):
        """Update circuit breaker threshold."""
        breaker = self.breakers.get(breaker_type)
        if breaker:
            breaker.config.threshold = threshold
            logger.info(f"Updated {breaker_type.value} threshold to {threshold}")
            
    async def cleanup(self):
        """Cleanup resources."""
        # Clear event logs
        self.event_log.clear()
        
        # Reset all breakers
        for breaker in self.breakers.values():
            breaker.event_history.clear()
            
        logger.info("Circuit breaker system cleanup complete")