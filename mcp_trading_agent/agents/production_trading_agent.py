"""
Production Trading Agent
=======================

Enhanced agent framework for production trading with safety controls and monitoring.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import asyncio
import json

from .base_agent import BaseAgent
from ..production.production_controller import TradingDecision
from ..data.data_source_manager import DataSourceManager
from ..risk.risk_manager import RiskLevel

logger = logging.getLogger(__name__)

class AgentStatus(Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    DISABLED = "disabled"
    ERROR = "error"
    TRAINING = "training"

class PersonalityType(Enum):
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"
    SCALPER = "scalper"
    SWING_TRADER = "swing_trader"
    POSITION_TRADER = "position_trader"

@dataclass
class TradingPersonality:
    name: str
    risk_tolerance: float  # 1-10 scale
    analysis_style: PersonalityType
    time_horizon: str  # 'scalping', 'day', 'swing', 'position'
    market_focus: List[str]  # ['NQ', 'ES', 'YM', 'RTY']
    confidence_threshold: float = 0.6  # Minimum confidence to trade
    max_trades_per_day: int = 50
    max_position_size: float = 100000
    preferred_timeframes: List[str] = None
    
    def __post_init__(self):
        if self.preferred_timeframes is None:
            self.preferred_timeframes = ['5m', '15m', '1h']

@dataclass
class RiskProfile:
    max_loss_per_trade: float = 0.02  # 2% of account
    max_daily_loss: float = 0.05  # 5% of account
    max_drawdown: float = 0.15  # 15% max drawdown
    stop_loss_percentage: float = 0.005  # 0.5% stop loss
    take_profit_ratio: float = 2.0  # 2:1 reward:risk
    position_sizing_method: str = "fixed_percentage"  # 'fixed', 'kelly', 'volatility'
    risk_adjustment_factor: float = 1.0  # Multiplier for position sizing

@dataclass
class DecisionEngine:
    analysis_models: List[str]
    ensemble_method: str = "weighted_average"  # 'majority_vote', 'weighted_average', 'confidence_weighted'
    model_weights: Dict[str, float] = None
    
    def __post_init__(self):
        if self.model_weights is None:
            # Equal weights by default
            self.model_weights = {model: 1.0 for model in self.analysis_models}

class ProductionTradingAgent(BaseAgent):
    """
    Production-ready trading agent with enhanced safety and monitoring.
    """
    
    def __init__(self, config: Dict[str, Any], mcp_server, provider_manager):
        super().__init__(config, mcp_server, provider_manager)
        
        # Enhanced configuration
        self.personality = self._load_personality(config.get('personality', {}))
        self.risk_profile = self._load_risk_profile(config.get('risk_profile', {}))
        self.decision_engine = self._load_decision_engine(config.get('decision_engine', {}))
        
        # Production controls
        self.status = AgentStatus.ACTIVE
        self.trading_enabled = config.get('trading_enabled', True)
        self.auto_trading = config.get('auto_trading', False)
        self.paper_trading = config.get('paper_trading', True)
        
        # Performance tracking
        self.trade_history: List[Dict[str, Any]] = []
        self.performance_metrics = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_pnl': 0.0,
            'max_drawdown': 0.0,
            'sharpe_ratio': 0.0,
            'win_rate': 0.0,
            'avg_win': 0.0,
            'avg_loss': 0.0,
            'profit_factor': 0.0
        }
        
        # Market data integration
        self.data_sources = config.get('data_sources', ['yahoo_finance'])
        self.data_source_manager = None  # Will be set by production controller
        
        # Training and adaptation
        self.learning_enabled = config.get('learning_enabled', False)
        self.feedback_history: List[Dict[str, Any]] = []
        self.model_updates = 0
        
        # Safety limits
        self.daily_trade_count = 0
        self.daily_pnl = 0.0
        self.last_trade_time = None
        self.consecutive_losses = 0
        
        # Prompts and guides (loaded from files)
        self.loaded_prompts = config.get('loaded_prompts', {})
        self.loaded_guides = config.get('loaded_guides', {})
        
        logger.info(f"Initialized ProductionTradingAgent: {self.agent_id}")
        
    def _load_personality(self, personality_config: Dict[str, Any]) -> TradingPersonality:
        """Load trading personality configuration."""
        return TradingPersonality(
            name=personality_config.get('name', 'Default Trader'),
            risk_tolerance=personality_config.get('risk_tolerance', 5.0),
            analysis_style=PersonalityType(personality_config.get('analysis_style', 'balanced')),
            time_horizon=personality_config.get('time_horizon', 'day'),
            market_focus=personality_config.get('market_focus', ['NQ']),
            confidence_threshold=personality_config.get('confidence_threshold', 0.6),
            max_trades_per_day=personality_config.get('max_trades_per_day', 50),
            max_position_size=personality_config.get('max_position_size', 100000),
            preferred_timeframes=personality_config.get('preferred_timeframes', ['5m', '15m', '1h'])
        )
        
    def _load_risk_profile(self, risk_config: Dict[str, Any]) -> RiskProfile:
        """Load risk profile configuration."""
        return RiskProfile(
            max_loss_per_trade=risk_config.get('max_loss_per_trade', 0.02),
            max_daily_loss=risk_config.get('max_daily_loss', 0.05),
            max_drawdown=risk_config.get('max_drawdown', 0.15),
            stop_loss_percentage=risk_config.get('stop_loss_percentage', 0.005),
            take_profit_ratio=risk_config.get('take_profit_ratio', 2.0),
            position_sizing_method=risk_config.get('position_sizing_method', 'fixed_percentage'),
            risk_adjustment_factor=risk_config.get('risk_adjustment_factor', 1.0)
        )
        
    def _load_decision_engine(self, engine_config: Dict[str, Any]) -> DecisionEngine:
        """Load decision engine configuration."""
        return DecisionEngine(
            analysis_models=engine_config.get('analysis_models', ['technical', 'sentiment']),
            ensemble_method=engine_config.get('ensemble_method', 'weighted_average'),
            model_weights=engine_config.get('model_weights')
        )
        
    async def analyze_market_comprehensive(
        self, 
        symbol: str, 
        timeframe: str = '15m'
    ) -> TradingDecision:
        """
        Comprehensive market analysis with production safety checks.
        """
        if not self._can_trade():
            return self._create_no_trade_decision(symbol, "Agent cannot trade at this time")
            
        try:
            # Get market data from multiple sources
            market_data = await self._get_consensus_market_data(symbol, timeframe)
            if not market_data:
                return self._create_no_trade_decision(symbol, "Insufficient market data quality")
                
            # Perform multi-model analysis
            analysis_results = await self._perform_ensemble_analysis(symbol, market_data, timeframe)
            
            # Calculate confidence and risk
            confidence = self._calculate_confidence(analysis_results)
            risk_assessment = self._assess_trade_risk(symbol, analysis_results, market_data)
            
            # Generate decision
            decision = await self._generate_trading_decision(
                symbol, analysis_results, confidence, risk_assessment, market_data
            )
            
            # Add to decision history
            self._record_decision(decision)
            
            return decision
            
        except Exception as e:
            logger.error(f"Error in comprehensive market analysis for {symbol}: {e}")
            return self._create_no_trade_decision(symbol, f"Analysis error: {e}")
            
    async def _get_consensus_market_data(
        self, 
        symbol: str, 
        timeframe: str
    ) -> Optional[Dict[str, Any]]:
        """Get consensus market data from multiple sources."""
        if not self.data_source_manager:
            # Fallback to basic data if no data source manager
            return await self._get_basic_market_data(symbol)
            
        try:
            consensus_data = await self.data_source_manager.get_consensus_data(
                symbol, timeframe, max_sources=3
            )
            
            return {
                'symbol': symbol,
                'price': float(consensus_data.close),
                'open': float(consensus_data.open),
                'high': float(consensus_data.high),
                'low': float(consensus_data.low),
                'volume': consensus_data.volume,
                'timestamp': consensus_data.timestamp,
                'quality_score': consensus_data.quality_score,
                'sources_used': [source.value for source in consensus_data.sources_used]
            }
            
        except Exception as e:
            logger.error(f"Error getting consensus data for {symbol}: {e}")
            return await self._get_basic_market_data(symbol)
            
    async def _get_basic_market_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fallback to basic market data."""
        try:
            # Use MCP tools for basic data
            price_data = await self.mcp_server.use_tool("get_nq_price")
            
            return {
                'symbol': symbol,
                'price': price_data.get('current_price', 0),
                'open': price_data.get('current_price', 0),
                'high': price_data.get('session_high', 0),
                'low': price_data.get('session_low', 0),
                'volume': price_data.get('volume', 0),
                'timestamp': datetime.now(),
                'quality_score': 0.7,  # Assume reasonable quality
                'sources_used': ['yahoo_finance']
            }
            
        except Exception as e:
            logger.error(f"Error getting basic market data for {symbol}: {e}")
            return None
            
    async def _perform_ensemble_analysis(
        self, 
        symbol: str, 
        market_data: Dict[str, Any], 
        timeframe: str
    ) -> Dict[str, Any]:
        """Perform analysis using multiple models."""
        analysis_results = {}
        
        # Technical analysis
        if 'technical' in self.decision_engine.analysis_models:
            analysis_results['technical'] = await self._technical_analysis(
                symbol, market_data, timeframe
            )
            
        # Sentiment analysis
        if 'sentiment' in self.decision_engine.analysis_models:
            analysis_results['sentiment'] = await self._sentiment_analysis(
                symbol, market_data, timeframe
            )
            
        # Fundamental analysis
        if 'fundamental' in self.decision_engine.analysis_models:
            analysis_results['fundamental'] = await self._fundamental_analysis(
                symbol, market_data, timeframe
            )
            
        # AI/ML analysis
        if 'ai_model' in self.decision_engine.analysis_models:
            analysis_results['ai_model'] = await self._ai_model_analysis(
                symbol, market_data, timeframe
            )
            
        return analysis_results
        
    async def _technical_analysis(
        self, 
        symbol: str, 
        market_data: Dict[str, Any], 
        timeframe: str
    ) -> Dict[str, Any]:
        """Perform technical analysis."""
        try:
            # Get historical data
            historical_data = await self.mcp_server.use_tool(
                "get_historical_data",
                symbol=symbol,
                period="1d",
                interval=timeframe
            )
            
            # Calculate technical indicators
            indicators = await self.mcp_server.use_tool(
                "calculate_technical_indicators",
                data=historical_data,
                indicators=["sma_20", "rsi_14", "macd", "bollinger_bands"]
            )
            
            # Analyze indicators
            signal_strength = self._analyze_technical_indicators(indicators)
            
            return {
                'signal': signal_strength['signal'],
                'confidence': signal_strength['confidence'],
                'indicators': indicators,
                'reasoning': signal_strength['reasoning']
            }
            
        except Exception as e:
            logger.error(f"Technical analysis error for {symbol}: {e}")
            return {'signal': 'hold', 'confidence': 0.0, 'reasoning': f'Technical analysis failed: {e}'}
            
    async def _sentiment_analysis(
        self, 
        symbol: str, 
        market_data: Dict[str, Any], 
        timeframe: str
    ) -> Dict[str, Any]:
        """Perform sentiment analysis."""
        # Placeholder for sentiment analysis
        # This would integrate with news APIs, social media sentiment, etc.
        return {
            'signal': 'neutral',
            'confidence': 0.5,
            'sentiment_score': 0.0,
            'reasoning': 'Sentiment analysis not yet implemented'
        }
        
    async def _fundamental_analysis(
        self, 
        symbol: str, 
        market_data: Dict[str, Any], 
        timeframe: str
    ) -> Dict[str, Any]:
        """Perform fundamental analysis."""
        # Placeholder for fundamental analysis
        # This would analyze economic indicators, earnings, etc.
        return {
            'signal': 'neutral',
            'confidence': 0.5,
            'reasoning': 'Fundamental analysis not yet implemented'
        }
        
    async def _ai_model_analysis(
        self, 
        symbol: str, 
        market_data: Dict[str, Any], 
        timeframe: str
    ) -> Dict[str, Any]:
        """Perform AI/ML model analysis."""
        try:
            # Prepare context with personality and guides
            context = self._build_ai_context(symbol, market_data, timeframe)
            
            # Generate analysis using LLM
            analysis = await self.analyze_with_llm(
                prompt=context['prompt'],
                context=context['context']
            )
            
            # Parse AI response
            parsed_analysis = self._parse_ai_analysis(analysis)
            
            return parsed_analysis
            
        except Exception as e:
            logger.error(f"AI model analysis error for {symbol}: {e}")
            return {'signal': 'hold', 'confidence': 0.0, 'reasoning': f'AI analysis failed: {e}'}
            
    def _build_ai_context(
        self, 
        symbol: str, 
        market_data: Dict[str, Any], 
        timeframe: str
    ) -> Dict[str, Any]:
        """Build context for AI analysis."""
        
        # Load relevant prompts
        base_prompt = self.loaded_prompts.get('analysis_prompt.txt', '')
        personality_prompt = self._generate_personality_prompt()
        
        # Load relevant guides
        strategy_guide = self.loaded_guides.get('strategy_guide.yaml', '')
        chart_guide = self.loaded_guides.get('chart_guide.md', '')
        
        prompt = f"""
        {base_prompt}
        
        PERSONALITY CONTEXT:
        {personality_prompt}
        
        STRATEGY GUIDE:
        {strategy_guide}
        
        CHART ANALYSIS GUIDE:
        {chart_guide}
        
        CURRENT MARKET DATA:
        Symbol: {symbol}
        Price: ${market_data['price']:.2f}
        Volume: {market_data['volume']:,}
        Quality Score: {market_data['quality_score']:.2f}
        Data Sources: {', '.join(market_data['sources_used'])}
        
        ANALYSIS REQUEST:
        Analyze {symbol} on {timeframe} timeframe and provide:
        1. Trading signal (buy/sell/hold)
        2. Confidence level (0-1)
        3. Detailed reasoning
        4. Risk assessment
        5. Suggested position size
        6. Stop loss and take profit levels
        
        Consider my personality, risk tolerance, and current market conditions.
        """
        
        return {
            'prompt': prompt,
            'context': {
                'symbol': symbol,
                'timeframe': timeframe,
                'personality': self.personality.name,
                'risk_tolerance': self.personality.risk_tolerance
            }
        }
        
    def _generate_personality_prompt(self) -> str:
        """Generate personality-specific prompt context."""
        return f"""
        TRADING PERSONALITY: {self.personality.name}
        Risk Tolerance: {self.personality.risk_tolerance}/10
        Analysis Style: {self.personality.analysis_style.value}
        Time Horizon: {self.personality.time_horizon}
        Market Focus: {', '.join(self.personality.market_focus)}
        Confidence Threshold: {self.personality.confidence_threshold}
        Max Trades/Day: {self.personality.max_trades_per_day}
        Max Position Size: ${self.personality.max_position_size:,.2f}
        Preferred Timeframes: {', '.join(self.personality.preferred_timeframes)}
        
        RISK PROFILE:
        Max Loss Per Trade: {self.risk_profile.max_loss_per_trade:.1%}
        Max Daily Loss: {self.risk_profile.max_daily_loss:.1%}
        Stop Loss %: {self.risk_profile.stop_loss_percentage:.2%}
        Take Profit Ratio: {self.risk_profile.take_profit_ratio}:1
        Position Sizing: {self.risk_profile.position_sizing_method}
        """
        
    def _parse_ai_analysis(self, analysis: str) -> Dict[str, Any]:
        """Parse AI analysis response."""
        # Simple parsing logic - in production, this would be more sophisticated
        try:
            lines = analysis.lower().split('\\n')
            
            signal = 'hold'
            confidence = 0.5
            reasoning = analysis
            
            # Look for signal keywords
            for line in lines:
                if 'buy' in line and ('signal' in line or 'recommend' in line):
                    signal = 'buy'
                elif 'sell' in line and ('signal' in line or 'recommend' in line):
                    signal = 'sell'
                    
            # Look for confidence
            for line in lines:
                if 'confidence' in line:
                    # Extract number between 0 and 1
                    import re
                    match = re.search(r'(\\d+(?:\\.\\d+)?)', line)
                    if match:
                        num = float(match.group(1))
                        if num <= 1.0:
                            confidence = num
                        elif num <= 100:
                            confidence = num / 100
                            
            return {
                'signal': signal,
                'confidence': confidence,
                'reasoning': reasoning[:500],  # Limit reasoning length
                'raw_analysis': analysis
            }
            
        except Exception as e:
            logger.error(f"Error parsing AI analysis: {e}")
            return {
                'signal': 'hold',
                'confidence': 0.0,
                'reasoning': f'Failed to parse analysis: {e}',
                'raw_analysis': analysis
            }
            
    def _calculate_confidence(self, analysis_results: Dict[str, Any]) -> float:
        """Calculate overall confidence from ensemble results."""
        if self.decision_engine.ensemble_method == 'weighted_average':
            total_weight = 0
            weighted_confidence = 0
            
            for model, result in analysis_results.items():
                weight = self.decision_engine.model_weights.get(model, 1.0)
                confidence = result.get('confidence', 0.0)
                
                weighted_confidence += confidence * weight
                total_weight += weight
                
            return weighted_confidence / total_weight if total_weight > 0 else 0.0
            
        elif self.decision_engine.ensemble_method == 'majority_vote':
            confidences = [result.get('confidence', 0.0) for result in analysis_results.values()]
            return sum(confidences) / len(confidences) if confidences else 0.0
            
        else:
            # Default to average
            confidences = [result.get('confidence', 0.0) for result in analysis_results.values()]
            return sum(confidences) / len(confidences) if confidences else 0.0
            
    def _assess_trade_risk(
        self, 
        symbol: str, 
        analysis_results: Dict[str, Any], 
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess risk for the trade."""
        risk_factors = {}
        
        # Data quality risk
        risk_factors['data_quality'] = 1.0 - market_data.get('quality_score', 0.5)
        
        # Model agreement risk
        signals = [result.get('signal', 'hold') for result in analysis_results.values()]
        signal_agreement = len(set(signals)) / len(signals) if signals else 1.0
        risk_factors['model_disagreement'] = signal_agreement
        
        # Volatility risk (placeholder)
        risk_factors['volatility'] = 0.5
        
        # Time-based risk
        risk_factors['time_of_day'] = self._calculate_time_risk()
        
        # Calculate overall risk score
        overall_risk = sum(risk_factors.values()) / len(risk_factors)
        
        return {
            'overall_risk': overall_risk,
            'risk_factors': risk_factors,
            'risk_level': self._categorize_risk(overall_risk)
        }
        
    def _calculate_time_risk(self) -> float:
        """Calculate risk based on time of day."""
        # Higher risk during market open/close, lower during normal hours
        current_hour = datetime.now().hour
        
        if current_hour in [9, 10, 15, 16]:  # Market open/close hours
            return 0.8
        elif current_hour in [11, 12, 13, 14]:  # Normal trading hours
            return 0.3
        else:  # After hours
            return 0.9
            
    def _categorize_risk(self, risk_score: float) -> RiskLevel:
        """Categorize risk score into risk level."""
        if risk_score >= 0.8:
            return RiskLevel.CRITICAL
        elif risk_score >= 0.6:
            return RiskLevel.HIGH
        elif risk_score >= 0.4:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
            
    async def _generate_trading_decision(
        self,
        symbol: str,
        analysis_results: Dict[str, Any],
        confidence: float,
        risk_assessment: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> TradingDecision:
        """Generate final trading decision."""
        
        # Determine action based on ensemble results
        action = self._determine_action(analysis_results, confidence)
        
        # Check if confidence meets threshold
        if confidence < self.personality.confidence_threshold:
            action = 'hold'
            
        # Calculate position size
        position_size = self._calculate_position_size(
            symbol, action, confidence, risk_assessment, market_data
        )
        
        # Calculate stop loss and take profit
        current_price = market_data['price']
        stop_loss, take_profit = self._calculate_levels(action, current_price)
        
        # Generate reasoning
        reasoning = self._generate_reasoning(analysis_results, confidence, risk_assessment)
        
        return TradingDecision(
            agent_id=self.agent_id,
            symbol=symbol,
            action=action,
            confidence=confidence,
            reasoning=reasoning,
            recommended_quantity=position_size,
            recommended_price=current_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            risk_factors=risk_assessment['risk_factors'],
            metadata={
                'analysis_results': analysis_results,
                'risk_assessment': risk_assessment,
                'market_data_quality': market_data.get('quality_score', 0.0),
                'personality': self.personality.name,
                'timeframe': 'default'
            }
        )
        
    def _determine_action(self, analysis_results: Dict[str, Any], confidence: float) -> str:
        """Determine trading action from analysis results."""
        if self.decision_engine.ensemble_method == 'majority_vote':
            signals = [result.get('signal', 'hold') for result in analysis_results.values()]
            # Count votes
            signal_counts = {}
            for signal in signals:
                signal_counts[signal] = signal_counts.get(signal, 0) + 1
                
            # Return signal with most votes
            return max(signal_counts, key=signal_counts.get)
            
        elif self.decision_engine.ensemble_method == 'weighted_average':
            signal_scores = {'buy': 0, 'sell': 0, 'hold': 0}
            
            for model, result in analysis_results.items():
                weight = self.decision_engine.model_weights.get(model, 1.0)
                signal = result.get('signal', 'hold')
                model_confidence = result.get('confidence', 0.0)
                
                signal_scores[signal] += weight * model_confidence
                
            # Return signal with highest weighted score
            return max(signal_scores, key=signal_scores.get)
            
        else:
            # Default to first available signal
            for result in analysis_results.values():
                return result.get('signal', 'hold')
            return 'hold'
            
    def _calculate_position_size(
        self,
        symbol: str,
        action: str,
        confidence: float,
        risk_assessment: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> int:
        """Calculate position size based on risk management."""
        if action == 'hold':
            return 0
            
        base_size = 1  # Base position size (1 contract for futures)
        
        # Adjust for confidence
        confidence_multiplier = min(confidence * 2, 1.0)  # Max 1.0 multiplier
        
        # Adjust for risk
        risk_multiplier = max(0.1, 1.0 - risk_assessment['overall_risk'])
        
        # Adjust for personality risk tolerance
        personality_multiplier = self.personality.risk_tolerance / 10.0
        
        # Calculate final size
        position_size = int(base_size * confidence_multiplier * risk_multiplier * personality_multiplier)
        
        # Apply limits
        max_size = min(
            self.personality.max_position_size // market_data['price'],
            self.personality.max_trades_per_day - self.daily_trade_count
        )
        
        return max(0, min(position_size, max_size))
        
    def _calculate_levels(self, action: str, current_price: float) -> Tuple[Optional[float], Optional[float]]:
        """Calculate stop loss and take profit levels."""
        if action == 'hold':
            return None, None
            
        stop_loss_pct = self.risk_profile.stop_loss_percentage
        take_profit_ratio = self.risk_profile.take_profit_ratio
        
        if action == 'buy':
            stop_loss = current_price * (1 - stop_loss_pct)
            take_profit = current_price * (1 + stop_loss_pct * take_profit_ratio)
        else:  # sell
            stop_loss = current_price * (1 + stop_loss_pct)
            take_profit = current_price * (1 - stop_loss_pct * take_profit_ratio)
            
        return stop_loss, take_profit
        
    def _generate_reasoning(
        self,
        analysis_results: Dict[str, Any],
        confidence: float,
        risk_assessment: Dict[str, Any]
    ) -> str:
        """Generate human-readable reasoning for the decision."""
        reasons = []
        
        # Add analysis insights
        for model, result in analysis_results.items():
            if result.get('reasoning'):
                reasons.append(f"{model.title()}: {result['reasoning'][:100]}")
                
        # Add confidence note
        reasons.append(f"Overall confidence: {confidence:.1%}")
        
        # Add risk assessment
        risk_level = risk_assessment['risk_level']
        reasons.append(f"Risk level: {risk_level.value}")
        
        return " | ".join(reasons)
        
    def _can_trade(self) -> bool:
        """Check if agent can trade based on current conditions."""
        if self.status != AgentStatus.ACTIVE:
            return False
            
        if not self.trading_enabled:
            return False
            
        # Check daily limits
        if self.daily_trade_count >= self.personality.max_trades_per_day:
            return False
            
        # Check daily loss limit
        if self.daily_pnl < -self.risk_profile.max_daily_loss:
            return False
            
        # Check consecutive losses
        if self.consecutive_losses >= 5:  # Safety limit
            return False
            
        return True
        
    def _create_no_trade_decision(self, symbol: str, reason: str) -> TradingDecision:
        """Create a no-trade decision with reason."""
        return TradingDecision(
            agent_id=self.agent_id,
            symbol=symbol,
            action='hold',
            confidence=0.0,
            reasoning=reason,
            recommended_quantity=0,
            recommended_price=None,
            stop_loss=None,
            take_profit=None,
            risk_factors={},
            metadata={'no_trade_reason': reason}
        )
        
    def _record_decision(self, decision: TradingDecision):
        """Record decision for tracking and learning."""
        decision_record = {
            'timestamp': decision.timestamp,
            'symbol': decision.symbol,
            'action': decision.action,
            'confidence': decision.confidence,
            'quantity': decision.recommended_quantity,
            'reasoning': decision.reasoning
        }
        
        # Add to memory
        self._add_to_memory("trading_decision", decision_record)
        
        # Update daily counters
        if decision.action in ['buy', 'sell']:
            self.daily_trade_count += 1
            
    def _analyze_technical_indicators(self, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze technical indicators and generate signal."""
        # Simplified technical analysis
        signals = []
        reasoning_parts = []
        
        # Example analysis (would be more sophisticated in production)
        if 'sma_20' in indicators and 'rsi_14' in indicators:
            # Simple moving average signal
            if indicators.get('price', 0) > indicators.get('sma_20', 0):
                signals.append('buy')
                reasoning_parts.append("Price above SMA20")
            else:
                signals.append('sell')
                reasoning_parts.append("Price below SMA20")
                
            # RSI signal
            rsi = indicators.get('rsi_14', 50)
            if rsi < 30:
                signals.append('buy')
                reasoning_parts.append(f"RSI oversold ({rsi:.1f})")
            elif rsi > 70:
                signals.append('sell')
                reasoning_parts.append(f"RSI overbought ({rsi:.1f})")
            else:
                signals.append('hold')
                reasoning_parts.append(f"RSI neutral ({rsi:.1f})")
                
        # Determine final signal
        buy_votes = signals.count('buy')
        sell_votes = signals.count('sell')
        hold_votes = signals.count('hold')
        
        if buy_votes > sell_votes and buy_votes > hold_votes:
            final_signal = 'buy'
            confidence = buy_votes / len(signals)
        elif sell_votes > buy_votes and sell_votes > hold_votes:
            final_signal = 'sell'
            confidence = sell_votes / len(signals)
        else:
            final_signal = 'hold'
            confidence = 0.5
            
        return {
            'signal': final_signal,
            'confidence': confidence,
            'reasoning': '; '.join(reasoning_parts)
        }
        
    async def receive_feedback(self, decision_id: str, feedback: Dict[str, Any]):
        """Receive feedback on a trading decision for learning."""
        if not self.learning_enabled:
            return
            
        feedback_record = {
            'timestamp': datetime.now(),
            'decision_id': decision_id,
            'feedback': feedback,
            'agent_id': self.agent_id
        }
        
        self.feedback_history.append(feedback_record)
        
        # Keep only recent feedback
        if len(self.feedback_history) > 100:
            self.feedback_history = self.feedback_history[-100:]
            
        # Update performance metrics based on feedback
        if feedback.get('outcome') == 'profit':
            self.performance_metrics['winning_trades'] += 1
        elif feedback.get('outcome') == 'loss':
            self.performance_metrics['losing_trades'] += 1
            
        self.performance_metrics['total_trades'] += 1
        
        # Recalculate metrics
        self._update_performance_metrics()
        
        logger.info(f"Received feedback for decision {decision_id}: {feedback.get('outcome', 'unknown')}")
        
    def _update_performance_metrics(self):
        """Update performance metrics."""
        total = self.performance_metrics['total_trades']
        if total > 0:
            self.performance_metrics['win_rate'] = (
                self.performance_metrics['winning_trades'] / total
            )
            
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific task."""
        task_type = task.get("type", "market_analysis")
        parameters = task.get("parameters", {})
        
        if task_type == "market_analysis":
            decision = await self.analyze_market_comprehensive(
                symbol=parameters.get("symbol", "NQ=F"),
                timeframe=parameters.get("timeframe", "15m")
            )
            
            return {
                "decision": {
                    "action": decision.action,
                    "confidence": decision.confidence,
                    "reasoning": decision.reasoning,
                    "quantity": decision.recommended_quantity,
                    "price": decision.recommended_price,
                    "stop_loss": decision.stop_loss,
                    "take_profit": decision.take_profit
                },
                "agent_id": self.agent_id,
                "timestamp": decision.timestamp.isoformat()
            }
            
        else:
            return {"error": f"Unknown task type: {task_type}"}
            
    def get_capabilities(self) -> List[str]:
        """Get agent capabilities."""
        return [
            "market_analysis",
            "technical_analysis",
            "risk_assessment",
            "position_sizing",
            "ensemble_analysis",
            "personality_based_trading",
            "continuous_learning"
        ]
        
    def get_status_info(self) -> Dict[str, Any]:
        """Get detailed agent status."""
        base_status = super().get_status()
        
        production_status = {
            'agent_status': self.status.value,
            'trading_enabled': self.trading_enabled,
            'auto_trading': self.auto_trading,
            'paper_trading': self.paper_trading,
            'personality': {
                'name': self.personality.name,
                'risk_tolerance': self.personality.risk_tolerance,
                'analysis_style': self.personality.analysis_style.value,
                'time_horizon': self.personality.time_horizon
            },
            'performance': self.performance_metrics.copy(),
            'daily_stats': {
                'trade_count': self.daily_trade_count,
                'daily_pnl': self.daily_pnl,
                'consecutive_losses': self.consecutive_losses
            },
            'data_sources': self.data_sources,
            'learning_enabled': self.learning_enabled,
            'model_updates': self.model_updates
        }
        
        return {**base_status, **production_status}