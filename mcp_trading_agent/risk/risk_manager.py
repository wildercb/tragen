"""
Production Risk Manager
======================

Multi-layer risk management system for production trading.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from decimal import Decimal
import asyncio

logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class RiskDecision(Enum):
    APPROVED = "approved"
    MODIFIED = "modified"
    REJECTED = "rejected"
    DELAYED = "delayed"

@dataclass
class TradeRequest:
    symbol: str
    action: str  # 'buy', 'sell'
    quantity: int
    price: Optional[Decimal] = None
    order_type: str = 'market'
    stop_loss: Optional[Decimal] = None
    take_profit: Optional[Decimal] = None
    agent_id: str = 'unknown'
    confidence: float = 0.5
    reasoning: str = ''
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class RiskAssessment:
    decision: RiskDecision
    risk_level: RiskLevel
    reason: str
    modified_request: Optional[TradeRequest] = None
    risk_score: float = 0.0
    risk_factors: Dict[str, float] = None
    recommendations: List[str] = None
    
    def __post_init__(self):
        if self.risk_factors is None:
            self.risk_factors = {}
        if self.recommendations is None:
            self.recommendations = []

@dataclass
class Position:
    symbol: str
    quantity: int  # Positive for long, negative for short
    entry_price: Decimal
    current_price: Decimal
    entry_time: datetime
    unrealized_pnl: Decimal = Decimal('0')
    realized_pnl: Decimal = Decimal('0')
    stop_loss: Optional[Decimal] = None
    take_profit: Optional[Decimal] = None
    
    def update_price(self, new_price: Decimal):
        """Update current price and calculate unrealized P&L."""
        self.current_price = new_price
        if self.quantity > 0:  # Long position
            self.unrealized_pnl = (new_price - self.entry_price) * self.quantity
        else:  # Short position
            self.unrealized_pnl = (self.entry_price - new_price) * abs(self.quantity)

class RiskLayer:
    """Base class for risk management layers."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.enabled = config.get('enabled', True)
        
    async def assess(self, request: TradeRequest, context: Dict[str, Any]) -> RiskAssessment:
        """Assess risk for a trade request."""
        raise NotImplementedError
        
class PositionSizeRiskLayer(RiskLayer):
    """Risk layer for position size limits."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("position_size", config)
        self.max_position_size = config.get('max_position_size', 100000)
        self.max_position_percent = config.get('max_position_percent', 0.10)  # 10% of account
        
    async def assess(self, request: TradeRequest, context: Dict[str, Any]) -> RiskAssessment:
        """Assess position size risk."""
        account_value = context.get('account_value', 1000000)  # Default $1M
        current_positions = context.get('positions', {})
        
        # Calculate position value
        price = request.price or context.get('current_price', Decimal('0'))
        if price == 0:
            return RiskAssessment(
                decision=RiskDecision.REJECTED,
                risk_level=RiskLevel.HIGH,
                reason="Cannot assess risk without price information"
            )
            
        position_value = float(price) * request.quantity
        
        # Check absolute position size
        if position_value > self.max_position_size:
            # Try to modify the request
            max_quantity = int(self.max_position_size / float(price))
            if max_quantity > 0:
                modified_request = TradeRequest(
                    symbol=request.symbol,
                    action=request.action,
                    quantity=max_quantity,
                    price=request.price,
                    order_type=request.order_type,
                    stop_loss=request.stop_loss,
                    take_profit=request.take_profit,
                    agent_id=request.agent_id,
                    confidence=request.confidence,
                    reasoning=request.reasoning
                )
                
                return RiskAssessment(
                    decision=RiskDecision.MODIFIED,
                    risk_level=RiskLevel.MEDIUM,
                    reason=f"Position size reduced from {request.quantity} to {max_quantity}",
                    modified_request=modified_request,
                    risk_factors={'position_size_limit': 1.0}
                )
            else:
                return RiskAssessment(
                    decision=RiskDecision.REJECTED,
                    risk_level=RiskLevel.HIGH,
                    reason=f"Position size ${position_value:,.2f} exceeds maximum ${self.max_position_size:,.2f}"
                )
                
        # Check percentage of account
        position_percent = position_value / account_value
        if position_percent > self.max_position_percent:
            # Try to modify the request
            max_quantity = int((account_value * self.max_position_percent) / float(price))
            if max_quantity > 0:
                modified_request = TradeRequest(
                    symbol=request.symbol,
                    action=request.action,
                    quantity=max_quantity,
                    price=request.price,
                    order_type=request.order_type,
                    stop_loss=request.stop_loss,
                    take_profit=request.take_profit,
                    agent_id=request.agent_id,
                    confidence=request.confidence,
                    reasoning=request.reasoning
                )
                
                return RiskAssessment(
                    decision=RiskDecision.MODIFIED,
                    risk_level=RiskLevel.MEDIUM,
                    reason=f"Position size reduced to stay within {self.max_position_percent:.1%} of account",
                    modified_request=modified_request,
                    risk_factors={'position_percent_limit': position_percent / self.max_position_percent}
                )
            else:
                return RiskAssessment(
                    decision=RiskDecision.REJECTED,
                    risk_level=RiskLevel.HIGH,
                    reason=f"Position would be {position_percent:.1%} of account (max: {self.max_position_percent:.1%})"
                )
                
        return RiskAssessment(
            decision=RiskDecision.APPROVED,
            risk_level=RiskLevel.LOW,
            reason="Position size within limits",
            risk_factors={'position_size_ratio': position_value / self.max_position_size}
        )

class PortfolioRiskLayer(RiskLayer):
    """Risk layer for portfolio-wide limits."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("portfolio", config)
        self.max_total_exposure = config.get('max_total_exposure', 500000)
        self.max_symbol_concentration = config.get('max_symbol_concentration', 0.25)  # 25%
        self.max_sector_concentration = config.get('max_sector_concentration', 0.40)  # 40%
        
    async def assess(self, request: TradeRequest, context: Dict[str, Any]) -> RiskAssessment:
        """Assess portfolio risk."""
        current_positions = context.get('positions', {})
        account_value = context.get('account_value', 1000000)
        
        # Calculate current exposure
        total_exposure = sum(
            abs(pos.quantity * float(pos.current_price)) 
            for pos in current_positions.values()
        )
        
        # Calculate new position value
        price = request.price or context.get('current_price', Decimal('0'))
        new_position_value = float(price) * request.quantity
        
        # Check total exposure
        new_total_exposure = total_exposure + new_position_value
        if new_total_exposure > self.max_total_exposure:
            return RiskAssessment(
                decision=RiskDecision.REJECTED,
                risk_level=RiskLevel.HIGH,
                reason=f"Total exposure would exceed limit: ${new_total_exposure:,.2f} > ${self.max_total_exposure:,.2f}",
                risk_factors={'total_exposure_ratio': new_total_exposure / self.max_total_exposure}
            )
            
        # Check symbol concentration
        current_symbol_exposure = 0
        if request.symbol in current_positions:
            pos = current_positions[request.symbol]
            current_symbol_exposure = abs(pos.quantity * float(pos.current_price))
            
        new_symbol_exposure = current_symbol_exposure + new_position_value
        symbol_concentration = new_symbol_exposure / account_value
        
        if symbol_concentration > self.max_symbol_concentration:
            return RiskAssessment(
                decision=RiskDecision.REJECTED,
                risk_level=RiskLevel.HIGH,
                reason=f"Symbol concentration would exceed limit: {symbol_concentration:.1%} > {self.max_symbol_concentration:.1%}",
                risk_factors={'symbol_concentration': symbol_concentration / self.max_symbol_concentration}
            )
            
        # Calculate risk score
        exposure_ratio = new_total_exposure / self.max_total_exposure
        concentration_ratio = symbol_concentration / self.max_symbol_concentration
        risk_score = max(exposure_ratio, concentration_ratio)
        
        if risk_score > 0.8:
            risk_level = RiskLevel.HIGH
        elif risk_score > 0.6:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW
            
        return RiskAssessment(
            decision=RiskDecision.APPROVED,
            risk_level=risk_level,
            reason="Portfolio risk within limits",
            risk_score=risk_score,
            risk_factors={
                'total_exposure_ratio': exposure_ratio,
                'symbol_concentration_ratio': concentration_ratio
            }
        )

class DrawdownRiskLayer(RiskLayer):
    """Risk layer for drawdown protection."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("drawdown", config)
        self.max_drawdown = config.get('max_drawdown', 0.15)  # 15%
        self.daily_loss_limit = config.get('daily_loss_limit', 0.05)  # 5%
        
    async def assess(self, request: TradeRequest, context: Dict[str, Any]) -> RiskAssessment:
        """Assess drawdown risk."""
        account_value = context.get('account_value', 1000000)
        peak_value = context.get('peak_account_value', account_value)
        daily_pnl = context.get('daily_pnl', 0)
        
        # Calculate current drawdown
        current_drawdown = (peak_value - account_value) / peak_value
        
        # Check maximum drawdown
        if current_drawdown > self.max_drawdown:
            return RiskAssessment(
                decision=RiskDecision.REJECTED,
                risk_level=RiskLevel.CRITICAL,
                reason=f"Maximum drawdown exceeded: {current_drawdown:.1%} > {self.max_drawdown:.1%}",
                risk_factors={'drawdown_ratio': current_drawdown / self.max_drawdown}
            )
            
        # Check daily loss limit
        daily_loss_pct = abs(daily_pnl) / account_value if daily_pnl < 0 else 0
        if daily_loss_pct > self.daily_loss_limit:
            return RiskAssessment(
                decision=RiskDecision.REJECTED,
                risk_level=RiskLevel.HIGH,
                reason=f"Daily loss limit exceeded: {daily_loss_pct:.1%} > {self.daily_loss_limit:.1%}",
                risk_factors={'daily_loss_ratio': daily_loss_pct / self.daily_loss_limit}
            )
            
        # Calculate risk score
        drawdown_ratio = current_drawdown / self.max_drawdown
        daily_loss_ratio = daily_loss_pct / self.daily_loss_limit
        risk_score = max(drawdown_ratio, daily_loss_ratio)
        
        if risk_score > 0.8:
            risk_level = RiskLevel.HIGH
        elif risk_score > 0.6:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW
            
        return RiskAssessment(
            decision=RiskDecision.APPROVED,
            risk_level=risk_level,
            reason="Drawdown risk within limits",
            risk_score=risk_score,
            risk_factors={
                'drawdown_ratio': drawdown_ratio,
                'daily_loss_ratio': daily_loss_ratio
            }
        )

class VolatilityRiskLayer(RiskLayer):
    """Risk layer for volatility-based risk management."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("volatility", config)
        self.max_volatility = config.get('max_volatility', 0.10)  # 10%
        self.volatility_lookback = config.get('volatility_lookback', 20)  # 20 periods
        
    async def assess(self, request: TradeRequest, context: Dict[str, Any]) -> RiskAssessment:
        """Assess volatility risk."""
        symbol_volatility = context.get('symbol_volatility', {}).get(request.symbol, 0.05)
        market_volatility = context.get('market_volatility', 0.03)
        
        # Use higher of symbol or market volatility
        current_volatility = max(symbol_volatility, market_volatility)
        
        # Check volatility threshold
        if current_volatility > self.max_volatility:
            # Reduce position size based on volatility
            volatility_ratio = current_volatility / self.max_volatility
            size_reduction = min(0.8, volatility_ratio - 1.0)  # Reduce by up to 80%
            
            new_quantity = int(request.quantity * (1.0 - size_reduction))
            
            if new_quantity > 0:
                modified_request = TradeRequest(
                    symbol=request.symbol,
                    action=request.action,
                    quantity=new_quantity,
                    price=request.price,
                    order_type=request.order_type,
                    stop_loss=request.stop_loss,
                    take_profit=request.take_profit,
                    agent_id=request.agent_id,
                    confidence=request.confidence,
                    reasoning=request.reasoning
                )
                
                return RiskAssessment(
                    decision=RiskDecision.MODIFIED,
                    risk_level=RiskLevel.HIGH,
                    reason=f"Position size reduced due to high volatility: {current_volatility:.1%}",
                    modified_request=modified_request,
                    risk_factors={'volatility_ratio': volatility_ratio}
                )
            else:
                return RiskAssessment(
                    decision=RiskDecision.REJECTED,
                    risk_level=RiskLevel.CRITICAL,
                    reason=f"Volatility too high for trading: {current_volatility:.1%} > {self.max_volatility:.1%}",
                    risk_factors={'volatility_ratio': volatility_ratio}
                )
                
        # Calculate risk score
        volatility_ratio = current_volatility / self.max_volatility
        
        if volatility_ratio > 0.8:
            risk_level = RiskLevel.HIGH
        elif volatility_ratio > 0.6:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW
            
        return RiskAssessment(
            decision=RiskDecision.APPROVED,
            risk_level=risk_level,
            reason="Volatility risk within limits",
            risk_score=volatility_ratio,
            risk_factors={'volatility_ratio': volatility_ratio}
        )

class RiskManager:
    """
    Production-grade risk manager with multiple protection layers.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.risk_config = config.get('risk_management', {})
        
        # Initialize risk layers
        self.layers = []
        self._initialize_layers()
        
        # Risk tracking
        self.risk_history: List[Tuple[datetime, TradeRequest, RiskAssessment]] = []
        self.position_manager = None  # Will be set externally
        
        # Risk statistics
        self.total_assessments = 0
        self.approved_count = 0
        self.rejected_count = 0
        self.modified_count = 0
        
    def _initialize_layers(self):
        """Initialize all risk layers."""
        layer_configs = self.risk_config.get('layers', {})
        
        # Position size layer
        if layer_configs.get('position_size', {}).get('enabled', True):
            self.layers.append(PositionSizeRiskLayer(layer_configs.get('position_size', {})))
            
        # Portfolio risk layer
        if layer_configs.get('portfolio', {}).get('enabled', True):
            self.layers.append(PortfolioRiskLayer(layer_configs.get('portfolio', {})))
            
        # Drawdown layer
        if layer_configs.get('drawdown', {}).get('enabled', True):
            self.layers.append(DrawdownRiskLayer(layer_configs.get('drawdown', {})))
            
        # Volatility layer
        if layer_configs.get('volatility', {}).get('enabled', True):
            self.layers.append(VolatilityRiskLayer(layer_configs.get('volatility', {})))
            
        logger.info(f"Initialized {len(self.layers)} risk layers")
        
    async def assess_trade(self, request: TradeRequest, context: Optional[Dict[str, Any]] = None) -> RiskAssessment:
        """
        Assess trade request through all risk layers.
        
        Args:
            request: Trade request to assess
            context: Market and portfolio context
            
        Returns:
            Final risk assessment
        """
        if context is None:
            context = {}
            
        self.total_assessments += 1
        
        # Run through all enabled layers
        current_request = request
        final_assessment = None
        layer_assessments = []
        
        for layer in self.layers:
            if not layer.enabled:
                continue
                
            try:
                assessment = await layer.assess(current_request, context)
                layer_assessments.append((layer.name, assessment))
                
                if assessment.decision == RiskDecision.REJECTED:
                    # Any layer can reject the trade
                    final_assessment = assessment
                    self.rejected_count += 1
                    break
                elif assessment.decision == RiskDecision.MODIFIED:
                    # Use modified request for subsequent layers
                    if assessment.modified_request:
                        current_request = assessment.modified_request
                        final_assessment = assessment
                        
            except Exception as e:
                logger.error(f"Error in risk layer {layer.name}: {e}")
                # Fail safe - reject on error
                final_assessment = RiskAssessment(
                    decision=RiskDecision.REJECTED,
                    risk_level=RiskLevel.CRITICAL,
                    reason=f"Risk assessment error in {layer.name}: {e}"
                )
                self.rejected_count += 1
                break
                
        # If no layer rejected or modified, approve
        if final_assessment is None:
            final_assessment = RiskAssessment(
                decision=RiskDecision.APPROVED,
                risk_level=RiskLevel.LOW,
                reason="All risk layers approved"
            )
            self.approved_count += 1
        elif final_assessment.decision == RiskDecision.MODIFIED:
            self.modified_count += 1
            
        # Combine risk factors from all layers
        combined_risk_factors = {}
        max_risk_score = 0
        highest_risk_level = RiskLevel.LOW
        
        for layer_name, assessment in layer_assessments:
            if assessment.risk_factors:
                for factor, score in assessment.risk_factors.items():
                    combined_risk_factors[f"{layer_name}_{factor}"] = score
                    
            if assessment.risk_score > max_risk_score:
                max_risk_score = assessment.risk_score
                
            if assessment.risk_level.value in ['critical', 'high', 'medium']:
                if assessment.risk_level == RiskLevel.CRITICAL:
                    highest_risk_level = RiskLevel.CRITICAL
                elif assessment.risk_level == RiskLevel.HIGH and highest_risk_level != RiskLevel.CRITICAL:
                    highest_risk_level = RiskLevel.HIGH
                elif assessment.risk_level == RiskLevel.MEDIUM and highest_risk_level == RiskLevel.LOW:
                    highest_risk_level = RiskLevel.MEDIUM
                    
        # Update final assessment with combined data
        final_assessment.risk_factors = combined_risk_factors
        final_assessment.risk_score = max_risk_score
        if final_assessment.decision != RiskDecision.REJECTED:
            final_assessment.risk_level = highest_risk_level
            
        # Store in history
        self.risk_history.append((datetime.now(), request, final_assessment))
        
        # Keep only recent history
        if len(self.risk_history) > 1000:
            self.risk_history = self.risk_history[-1000:]
            
        logger.info(
            f"Risk assessment for {request.symbol} {request.action}: "
            f"{final_assessment.decision.value} ({final_assessment.risk_level.value}) - "
            f"{final_assessment.reason}"
        )
        
        return final_assessment
        
    def get_risk_statistics(self) -> Dict[str, Any]:
        """Get risk management statistics."""
        approval_rate = self.approved_count / self.total_assessments if self.total_assessments > 0 else 0
        rejection_rate = self.rejected_count / self.total_assessments if self.total_assessments > 0 else 0
        modification_rate = self.modified_count / self.total_assessments if self.total_assessments > 0 else 0
        
        return {
            'total_assessments': self.total_assessments,
            'approved_count': self.approved_count,
            'rejected_count': self.rejected_count,
            'modified_count': self.modified_count,
            'approval_rate': approval_rate,
            'rejection_rate': rejection_rate,
            'modification_rate': modification_rate,
            'active_layers': len([layer for layer in self.layers if layer.enabled]),
            'total_layers': len(self.layers)
        }
        
    def get_recent_assessments(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent risk assessments."""
        recent = self.risk_history[-limit:] if self.risk_history else []
        
        return [
            {
                'timestamp': timestamp.isoformat(),
                'symbol': request.symbol,
                'action': request.action,
                'quantity': request.quantity,
                'agent_id': request.agent_id,
                'decision': assessment.decision.value,
                'risk_level': assessment.risk_level.value,
                'reason': assessment.reason,
                'risk_score': assessment.risk_score
            }
            for timestamp, request, assessment in recent
        ]
        
    def update_layer_config(self, layer_name: str, config: Dict[str, Any]):
        """Update configuration for a specific layer."""
        for layer in self.layers:
            if layer.name == layer_name:
                layer.config.update(config)
                logger.info(f"Updated configuration for risk layer: {layer_name}")
                return True
                
        logger.warning(f"Risk layer not found: {layer_name}")
        return False
        
    def enable_layer(self, layer_name: str):
        """Enable a risk layer."""
        for layer in self.layers:
            if layer.name == layer_name:
                layer.enabled = True
                logger.info(f"Enabled risk layer: {layer_name}")
                return True
                
        return False
        
    def disable_layer(self, layer_name: str):
        """Disable a risk layer."""
        for layer in self.layers:
            if layer.name == layer_name:
                layer.enabled = False
                logger.info(f"Disabled risk layer: {layer_name}")
                return True
                
        return False
        
    def get_layer_status(self) -> Dict[str, Any]:
        """Get status of all risk layers."""
        return {
            layer.name: {
                'enabled': layer.enabled,
                'config': layer.config
            }
            for layer in self.layers
        }