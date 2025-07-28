"""
Production Trading Controller
============================

Master controller for production trading with comprehensive safety and monitoring.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json

from ..risk.risk_manager import RiskManager, TradeRequest, RiskAssessment, RiskDecision
from ..risk.circuit_breaker import CircuitBreakerSystem
from ..data.data_source_manager import DataSourceManager
from ..data.data_quality_manager import DataQualityManager
from .audit_logger import AuditLogger
from .monitoring import ProductionMonitor

logger = logging.getLogger(__name__)

class TradingMode(Enum):
    PAPER = "paper"
    LIVE_MINIMAL = "live_minimal"  # Small positions
    LIVE_NORMAL = "live_normal"    # Normal positions
    LIVE_AGGRESSIVE = "live_aggressive"  # Large positions
    EMERGENCY_ONLY = "emergency_only"  # Only emergency actions
    HALTED = "halted"  # No trading

class SystemStatus(Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    OFFLINE = "offline"

@dataclass
class TradingDecision:
    agent_id: str
    symbol: str
    action: str  # 'buy', 'sell', 'hold'
    confidence: float
    reasoning: str
    recommended_quantity: int
    recommended_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    risk_factors: Dict[str, float] = None
    metadata: Dict[str, Any] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.risk_factors is None:
            self.risk_factors = {}
        if self.metadata is None:
            self.metadata = {}

@dataclass
class ExecutionResult:
    decision_id: str
    symbol: str
    action: str
    requested_quantity: int
    executed_quantity: int
    requested_price: Optional[float]
    executed_price: Optional[float]
    execution_status: str  # 'executed', 'partial', 'rejected', 'cancelled'
    execution_time: datetime
    fees: float = 0.0
    slippage: float = 0.0
    error_message: str = ""
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class ProductionTradingController:
    """
    Master controller for production trading operations.
    
    Provides:
    - Centralized decision validation and execution
    - Multi-layer risk management
    - Circuit breaker integration
    - Comprehensive audit logging
    - Real-time monitoring
    - Emergency controls
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.production_config = config.get('production', {})
        
        # Trading mode and status
        self.trading_mode = TradingMode(self.production_config.get('trading_mode', 'paper'))
        self.system_status = SystemStatus.OFFLINE
        
        # Core components
        self.risk_manager = RiskManager(config)
        self.circuit_breaker = CircuitBreakerSystem(config)
        self.data_source_manager = DataSourceManager(config)
        self.data_quality_manager = DataQualityManager(config)
        self.audit_logger = AuditLogger(config)
        self.monitor = ProductionMonitor(config)
        
        # Trading state
        self.active_agents: Dict[str, Any] = {}
        self.pending_decisions: Dict[str, TradingDecision] = {}
        self.execution_queue: List[TradeRequest] = []
        self.position_tracker: Dict[str, Any] = {}
        
        # Performance tracking
        self.daily_stats = {
            'trades_executed': 0,
            'trades_rejected': 0,
            'total_pnl': 0.0,
            'max_drawdown': 0.0,
            'start_balance': 0.0,
            'current_balance': 0.0
        }
        
        # Safety limits
        self.safety_limits = {
            'max_trades_per_minute': self.production_config.get('max_trades_per_minute', 10),
            'max_daily_trades': self.production_config.get('max_daily_trades', 100),
            'max_position_value': self.production_config.get('max_position_value', 100000),
            'max_daily_loss': self.production_config.get('max_daily_loss', 0.05),  # 5%
            'emergency_stop_loss': self.production_config.get('emergency_stop_loss', 0.15)  # 15%
        }
        
        # Setup callbacks
        self._setup_circuit_breaker_callbacks()
        
    async def initialize(self):
        """Initialize the production controller."""
        logger.info("Initializing Production Trading Controller...")
        
        try:
            # Initialize components
            await self.data_source_manager.initialize()
            await self.audit_logger.initialize()
            await self.monitor.initialize()
            
            # Setup risk manager with position manager reference
            # self.risk_manager.position_manager = self.position_tracker
            
            # Load initial state
            await self._load_initial_state()
            
            # Start monitoring
            await self.monitor.start_monitoring()
            
            self.system_status = SystemStatus.HEALTHY
            
            logger.info(f"Production controller initialized in {self.trading_mode.value} mode")
            
        except Exception as e:
            logger.error(f"Failed to initialize production controller: {e}")
            self.system_status = SystemStatus.CRITICAL
            raise
            
    async def execute_trading_decision(
        self, 
        agent_id: str, 
        decision: TradingDecision
    ) -> ExecutionResult:
        """
        Execute a trading decision with full safety checks.
        
        Args:
            agent_id: ID of the agent making the decision
            decision: Trading decision to execute
            
        Returns:
            ExecutionResult with execution details
        """
        decision_id = f"{agent_id}_{decision.symbol}_{datetime.now().timestamp()}"
        
        try:
            # Log decision
            await self.audit_logger.log_trading_decision(agent_id, decision)
            
            # Check system status
            if self.system_status in [SystemStatus.CRITICAL, SystemStatus.OFFLINE]:
                return ExecutionResult(
                    decision_id=decision_id,
                    symbol=decision.symbol,
                    action=decision.action,
                    requested_quantity=decision.recommended_quantity,
                    executed_quantity=0,
                    requested_price=decision.recommended_price,
                    executed_price=None,
                    execution_status='rejected',
                    execution_time=datetime.now(),
                    error_message=f"System status: {self.system_status.value}"
                )
                
            # Check circuit breakers
            should_halt, halt_reason = await self.circuit_breaker.should_halt_trading()
            if should_halt:
                return ExecutionResult(
                    decision_id=decision_id,
                    symbol=decision.symbol,
                    action=decision.action,
                    requested_quantity=decision.recommended_quantity,
                    executed_quantity=0,
                    requested_price=decision.recommended_price,
                    executed_price=None,
                    execution_status='rejected',
                    execution_time=datetime.now(),
                    error_message=f"Circuit breaker halt: {halt_reason}"
                )
                
            # Check trading mode
            if self.trading_mode == TradingMode.HALTED:
                return ExecutionResult(
                    decision_id=decision_id,
                    symbol=decision.symbol,
                    action=decision.action,
                    requested_quantity=decision.recommended_quantity,
                    executed_quantity=0,
                    requested_price=decision.recommended_price,
                    executed_price=None,
                    execution_status='rejected',
                    execution_time=datetime.now(),
                    error_message="Trading is halted"
                )
                
            # Validate market data quality
            market_data = await self._get_validated_market_data(decision.symbol)
            if not market_data:
                return ExecutionResult(
                    decision_id=decision_id,
                    symbol=decision.symbol,
                    action=decision.action,
                    requested_quantity=decision.recommended_quantity,
                    executed_quantity=0,
                    requested_price=decision.recommended_price,
                    executed_price=None,
                    execution_status='rejected',
                    execution_time=datetime.now(),
                    error_message="Market data quality insufficient"
                )
                
            # Create trade request
            trade_request = TradeRequest(
                symbol=decision.symbol,
                action=decision.action,
                quantity=decision.recommended_quantity,
                price=decision.recommended_price,
                stop_loss=decision.stop_loss,
                take_profit=decision.take_profit,
                agent_id=agent_id,
                confidence=decision.confidence,
                reasoning=decision.reasoning
            )
            
            # Risk assessment
            risk_context = await self._build_risk_context(decision.symbol)
            risk_assessment = await self.risk_manager.assess_trade(trade_request, risk_context)
            
            # Log risk assessment
            await self.audit_logger.log_risk_assessment(decision_id, risk_assessment)
            
            # Handle risk decision
            if risk_assessment.decision == RiskDecision.REJECTED:
                self.daily_stats['trades_rejected'] += 1
                return ExecutionResult(
                    decision_id=decision_id,
                    symbol=decision.symbol,
                    action=decision.action,
                    requested_quantity=decision.recommended_quantity,
                    executed_quantity=0,
                    requested_price=decision.recommended_price,
                    executed_price=None,
                    execution_status='rejected',
                    execution_time=datetime.now(),
                    error_message=f"Risk management rejection: {risk_assessment.reason}"
                )
                
            # Use modified request if risk manager modified it
            final_request = risk_assessment.modified_request or trade_request
            
            # Execute the trade
            execution_result = await self._execute_trade(decision_id, final_request, market_data)
            
            # Update statistics
            if execution_result.execution_status == 'executed':
                self.daily_stats['trades_executed'] += 1
                await self._update_positions(execution_result)
                
            # Log execution
            await self.audit_logger.log_execution(decision_id, execution_result)
            
            # Update circuit breakers
            await self._update_circuit_breakers(execution_result)
            
            # Monitor execution
            await self.monitor.record_execution(execution_result)
            
            return execution_result
            
        except Exception as e:
            logger.error(f"Error executing trading decision {decision_id}: {e}")
            
            # Log error
            await self.audit_logger.log_error(decision_id, str(e))
            
            return ExecutionResult(
                decision_id=decision_id,
                symbol=decision.symbol,
                action=decision.action,
                requested_quantity=decision.recommended_quantity,
                executed_quantity=0,
                requested_price=decision.recommended_price,
                executed_price=None,
                execution_status='error',
                execution_time=datetime.now(),
                error_message=str(e)
            )
            
    async def emergency_halt(self, reason: str):
        """Trigger emergency halt of all trading."""
        logger.critical(f"EMERGENCY HALT TRIGGERED: {reason}")
        
        # Update trading mode
        self.trading_mode = TradingMode.HALTED
        self.system_status = SystemStatus.CRITICAL
        
        # Trigger circuit breakers
        await self.circuit_breaker.trigger_emergency_halt(reason)
        
        # Cancel pending orders
        await self._cancel_all_pending_orders()
        
        # Log emergency halt
        await self.audit_logger.log_emergency_event("EMERGENCY_HALT", reason)
        
        # Alert monitoring
        await self.monitor.alert_emergency_halt(reason)
        
    async def emergency_close_all_positions(self, reason: str):
        """Emergency close all open positions."""
        logger.critical(f"EMERGENCY POSITION CLOSURE: {reason}")
        
        # Log emergency action
        await self.audit_logger.log_emergency_event("EMERGENCY_CLOSE_ALL", reason)
        
        # Close all positions
        closed_positions = []
        for symbol, position in self.position_tracker.items():
            if position.get('quantity', 0) != 0:
                try:
                    close_result = await self._emergency_close_position(symbol, position)
                    closed_positions.append(close_result)
                except Exception as e:
                    logger.error(f"Failed to close position {symbol}: {e}")
                    
        # Alert monitoring
        await self.monitor.alert_emergency_closure(reason, closed_positions)
        
        return closed_positions
        
    async def set_trading_mode(self, mode: TradingMode, reason: str = ""):
        """Change trading mode."""
        old_mode = self.trading_mode
        self.trading_mode = mode
        
        logger.info(f"Trading mode changed: {old_mode.value} -> {mode.value} ({reason})")
        
        # Log mode change
        await self.audit_logger.log_system_event(
            "TRADING_MODE_CHANGE",
            {
                'old_mode': old_mode.value,
                'new_mode': mode.value,
                'reason': reason
            }
        )
        
        # Alert monitoring
        await self.monitor.alert_mode_change(old_mode, mode, reason)
        
    async def register_agent(self, agent_id: str, agent_config: Dict[str, Any]):
        """Register a trading agent."""
        self.active_agents[agent_id] = {
            'config': agent_config,
            'registered_at': datetime.now(),
            'status': 'active',
            'trade_count': 0,
            'success_rate': 0.0,
            'last_activity': datetime.now()
        }
        
        logger.info(f"Registered trading agent: {agent_id}")
        
        # Log agent registration
        await self.audit_logger.log_agent_event(agent_id, "REGISTERED", agent_config)
        
    async def deregister_agent(self, agent_id: str, reason: str = ""):
        """Deregister a trading agent."""
        if agent_id in self.active_agents:
            agent_info = self.active_agents.pop(agent_id)
            
            logger.info(f"Deregistered trading agent: {agent_id} ({reason})")
            
            # Log agent deregistration
            await self.audit_logger.log_agent_event(agent_id, "DEREGISTERED", {'reason': reason})
            
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        # Check circuit breakers
        breaker_status = await self.circuit_breaker.get_system_status()
        
        # Get risk statistics
        risk_stats = self.risk_manager.get_risk_statistics()
        
        # Get data source status
        data_source_status = self.data_source_manager.get_source_status()
        
        # Calculate account metrics
        total_position_value = sum(
            abs(pos.get('quantity', 0) * pos.get('current_price', 0))
            for pos in self.position_tracker.values()
        )
        
        return {
            'system_status': self.system_status.value,
            'trading_mode': self.trading_mode.value,
            'active_agents': len(self.active_agents),
            'daily_stats': self.daily_stats.copy(),
            'positions': {
                'count': len([p for p in self.position_tracker.values() if p.get('quantity', 0) != 0]),
                'total_value': total_position_value
            },
            'circuit_breakers': breaker_status,
            'risk_management': risk_stats,
            'data_sources': data_source_status,
            'safety_limits': self.safety_limits.copy(),
            'last_update': datetime.now().isoformat()
        }
        
    async def _get_validated_market_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get validated market data for trading decisions."""
        try:
            # Get consensus data from multiple sources
            consensus_data = await self.data_source_manager.get_consensus_data(symbol)
            
            # Validate data quality
            quality_report = await self.data_quality_manager.validate_market_data({
                'symbol': symbol,
                'open': float(consensus_data.open),
                'high': float(consensus_data.high),
                'low': float(consensus_data.low),
                'close': float(consensus_data.close),
                'volume': consensus_data.volume,
                'timestamp': consensus_data.timestamp
            })
            
            # Check if data is acceptable
            if quality_report.recommendation != 'ACCEPT':
                logger.warning(f"Market data quality issue for {symbol}: {quality_report.recommendation}")
                
                # Only reject if critical issues
                if quality_report.overall_score < 0.5:
                    return None
                    
            return {
                'symbol': symbol,
                'price': float(consensus_data.close),
                'open': float(consensus_data.open),
                'high': float(consensus_data.high),
                'low': float(consensus_data.low),
                'volume': consensus_data.volume,
                'timestamp': consensus_data.timestamp,
                'quality_score': quality_report.overall_score,
                'sources_used': consensus_data.sources_used
            }
            
        except Exception as e:
            logger.error(f"Failed to get validated market data for {symbol}: {e}")
            return None
            
    async def _build_risk_context(self, symbol: str) -> Dict[str, Any]:
        """Build risk context for assessment."""
        return {
            'account_value': self.daily_stats.get('current_balance', 1000000),
            'peak_account_value': self.daily_stats.get('start_balance', 1000000),
            'daily_pnl': self.daily_stats.get('total_pnl', 0),
            'positions': self.position_tracker,
            'current_price': self.position_tracker.get(symbol, {}).get('current_price', 0),
            'symbol_volatility': {},  # Would be calculated from historical data
            'market_volatility': 0.05  # Would be calculated from market data
        }
        
    async def _execute_trade(
        self, 
        decision_id: str, 
        request: TradeRequest, 
        market_data: Dict[str, Any]
    ) -> ExecutionResult:
        """Execute the actual trade."""
        
        # In paper trading mode, simulate execution
        if self.trading_mode == TradingMode.PAPER:
            return await self._simulate_execution(decision_id, request, market_data)
            
        # In live trading, execute through broker API
        # This would integrate with actual broker APIs (Interactive Brokers, etc.)
        logger.info(f"Live execution not implemented yet for {request.symbol}")
        
        # For now, simulate even in live mode
        return await self._simulate_execution(decision_id, request, market_data)
        
    async def _simulate_execution(
        self, 
        decision_id: str, 
        request: TradeRequest, 
        market_data: Dict[str, Any]
    ) -> ExecutionResult:
        """Simulate trade execution for paper trading."""
        
        # Simulate execution price with slippage
        market_price = market_data['price']
        slippage = 0.001  # 0.1% slippage
        
        if request.action == 'buy':
            execution_price = market_price * (1 + slippage)
        else:
            execution_price = market_price * (1 - slippage)
            
        # Simulate fees
        fees = request.quantity * 2.50  # $2.50 per contract
        
        return ExecutionResult(
            decision_id=decision_id,
            symbol=request.symbol,
            action=request.action,
            requested_quantity=request.quantity,
            executed_quantity=request.quantity,
            requested_price=float(request.price) if request.price else None,
            executed_price=execution_price,
            execution_status='executed',
            execution_time=datetime.now(),
            fees=fees,
            slippage=slippage * market_price * request.quantity,
            metadata={
                'simulation': True,
                'market_price': market_price,
                'data_sources': market_data.get('sources_used', []),
                'data_quality': market_data.get('quality_score', 0.0)
            }
        )
        
    async def _update_positions(self, execution: ExecutionResult):
        """Update position tracking after execution."""
        symbol = execution.symbol
        
        if symbol not in self.position_tracker:
            self.position_tracker[symbol] = {
                'quantity': 0,
                'average_price': 0.0,
                'unrealized_pnl': 0.0,
                'realized_pnl': 0.0,
                'last_update': datetime.now()
            }
            
        position = self.position_tracker[symbol]
        
        if execution.action == 'buy':
            # Calculate new average price
            total_cost = (position['quantity'] * position['average_price'] + 
                         execution.executed_quantity * execution.executed_price)
            total_quantity = position['quantity'] + execution.executed_quantity
            
            if total_quantity > 0:
                position['average_price'] = total_cost / total_quantity
                
            position['quantity'] += execution.executed_quantity
            
        elif execution.action == 'sell':
            # Calculate realized P&L
            if position['quantity'] > 0:
                realized_pnl = ((execution.executed_price - position['average_price']) * 
                               min(execution.executed_quantity, position['quantity']))
                position['realized_pnl'] += realized_pnl
                self.daily_stats['total_pnl'] += realized_pnl
                
            position['quantity'] -= execution.executed_quantity
            
        position['last_update'] = datetime.now()
        
        # Update current balance
        self.daily_stats['current_balance'] += (execution.executed_price * execution.executed_quantity * 
                                               (1 if execution.action == 'sell' else -1)) - execution.fees
        
    async def _update_circuit_breakers(self, execution: ExecutionResult):
        """Update circuit breakers after execution."""
        # Record trade result for consecutive loss tracking
        is_loss = False  # Would be calculated based on actual P&L
        await self.circuit_breaker.record_trade_result(is_loss)
        
        # Check daily loss
        await self.circuit_breaker.check_daily_loss(
            self.daily_stats['total_pnl'],
            self.daily_stats['current_balance']
        )
        
    async def _cancel_all_pending_orders(self):
        """Cancel all pending orders during emergency halt."""
        # This would integrate with broker APIs to cancel orders
        logger.info("Cancelling all pending orders")
        
    async def _emergency_close_position(self, symbol: str, position: Dict[str, Any]) -> Dict[str, Any]:
        """Emergency close a specific position."""
        # This would execute market orders to close positions
        logger.info(f"Emergency closing position: {symbol}")
        
        return {
            'symbol': symbol,
            'quantity_closed': position.get('quantity', 0),
            'close_price': 0.0,  # Would be actual execution price
            'timestamp': datetime.now()
        }
        
    async def _load_initial_state(self):
        """Load initial system state."""
        # Load from persistent storage
        self.daily_stats['start_balance'] = 1000000  # Would be loaded from account
        self.daily_stats['current_balance'] = self.daily_stats['start_balance']
        
    def _setup_circuit_breaker_callbacks(self):
        """Setup circuit breaker callbacks."""
        
        async def on_breaker_triggered(event):
            logger.critical(f"Circuit breaker triggered: {event.breaker_type.value}")
            await self.emergency_halt(f"Circuit breaker: {event.message}")
            
        async def on_breaker_reset(breaker_type):
            logger.info(f"Circuit breaker reset: {breaker_type}")
            
        self.circuit_breaker.add_global_trigger_callback(on_breaker_triggered)
        self.circuit_breaker.add_global_reset_callback(on_breaker_reset)
        
    async def cleanup(self):
        """Cleanup resources."""
        logger.info("Cleaning up production controller...")
        
        # Cleanup components
        await self.data_source_manager.cleanup()
        await self.audit_logger.cleanup()
        await self.monitor.cleanup()
        await self.circuit_breaker.cleanup()
        
        # Clear state
        self.active_agents.clear()
        self.pending_decisions.clear()
        self.execution_queue.clear()
        self.position_tracker.clear()
        
        self.system_status = SystemStatus.OFFLINE
        
        logger.info("Production controller cleanup complete")