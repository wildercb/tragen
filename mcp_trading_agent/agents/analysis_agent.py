"""
Analysis Agent
=============

Specialized agent for technical and fundamental analysis with market-aware behavior.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from .base_agent import BaseAgent
from ..utils.market_hours import MarketHours
from ..config.agent_config import AgentConfig, AgentConfigManager

logger = logging.getLogger(__name__)

class AnalysisAgent(BaseAgent):
    """Agent specialized in market analysis and technical indicators."""
    
    def __init__(self, config: Dict[str, Any], mcp_server, provider_manager):
        super().__init__(config, mcp_server, provider_manager)
        self.agent_type = "analysis"
        self.capabilities = [
            "technical_analysis",
            "pattern_recognition", 
            "market_sentiment",
            "fundamental_analysis"
        ]
        
        # Initialize configuration manager
        self.config_manager = AgentConfigManager()
        
        # Set up agent configuration
        agent_config_data = config.get('agent_config', {})
        if 'agent_id' not in agent_config_data:
            agent_config_data['agent_id'] = self.agent_id
        if 'agent_type' not in agent_config_data:
            agent_config_data['agent_type'] = self.agent_type
            
        self.agent_config = AgentConfig(**agent_config_data)
        
        # Track last signal time for rate limiting
        self.last_signal_time = None
    
    def get_capabilities(self) -> List[str]:
        """Get list of agent capabilities."""
        return self.capabilities
    
    def should_generate_signals(self, current_time: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Check if agent should generate trading signals based on market hours and configuration.
        
        Args:
            current_time: Time to check (defaults to current time)
            
        Returns:
            Dict with should_trade boolean and reason
        """
        if current_time is None:
            current_time = datetime.now()
            
        # Check market hours
        if not MarketHours.should_agents_trade(current_time):
            market_status = MarketHours.get_market_status(current_time)
            return {
                "should_trade": False,
                "reason": f"Market is {market_status['session_status']}",
                "market_status": market_status
            }
        
        # Check agent configuration for market hours only setting
        if self.agent_config.strategies:
            for strategy in self.agent_config.strategies:
                if strategy.enabled and strategy.market_hours_only:
                    if not MarketHours.is_market_open(current_time):
                        return {
                            "should_trade": False,
                            "reason": "Strategy requires market hours only",
                            "market_status": MarketHours.get_market_status(current_time)
                        }
        
        # Check signal rate limiting
        if self.last_signal_time and self.agent_config.strategies:
            for strategy in self.agent_config.strategies:
                if strategy.enabled:
                    min_gap = timedelta(minutes=strategy.min_signal_gap_minutes)
                    if current_time - self.last_signal_time < min_gap:
                        return {
                            "should_trade": False,
                            "reason": f"Rate limited - minimum {strategy.min_signal_gap_minutes} minutes between signals",
                            "time_until_next": (self.last_signal_time + min_gap - current_time).total_seconds() / 60
                        }
        
        return {
            "should_trade": True,
            "reason": "All conditions met for signal generation",
            "market_status": MarketHours.get_market_status(current_time)
        }
    
    async def analyze_market(self, symbol: str = "NQ=F", timeframe: str = "1h") -> Dict[str, Any]:
        """Perform comprehensive market analysis with market hours awareness."""
        analysis_time = datetime.now()
        
        try:
            # Check if we should generate signals
            signal_check = self.should_generate_signals(analysis_time)
            
            # Get current market data
            market_data = await self.mcp_server.use_tool("get_nq_price")
            
            # Get historical data for technical analysis
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
            
            # Generate AI analysis with agent personality context
            agent_context = self.agent_config.to_prompt_context()
            
            prompt = f"""
            {agent_context}
            
            MARKET STATUS: {signal_check['reason']}
            Signal Generation: {'ENABLED' if signal_check['should_trade'] else 'DISABLED'}
            
            Analyze the current market conditions for {symbol}:
            
            Current Price: ${market_data.get('current_price', 'N/A')}
            Session High: ${market_data.get('session_high', 'N/A')}
            Session Low: ${market_data.get('session_low', 'N/A')}
            Volume: {market_data.get('volume', 'N/A')}
            
            Technical Indicators:
            {indicators}
            
            Based on your trading personality and the current market status, provide:
            1. Current trend direction and strength
            2. Key support/resistance levels
            3. Momentum assessment
            4. Trading recommendation (1-10 confidence) - ONLY if signal generation is ENABLED
            5. Risk assessment for current conditions
            
            Remember: {"Generate actionable signals" if signal_check['should_trade'] else "Analysis only - do not generate trading signals due to market conditions"}
            """
            
            analysis = await self.provider_manager.generate_response(
                prompt=prompt,
                provider=self.config.get('provider', 'ollama'),
                model=self.config.get('model'),
                temperature=0.1
            )
            
            # Update last signal time if signal was generated
            if signal_check['should_trade']:
                self.last_signal_time = analysis_time
            
            result = {
                "symbol": symbol,
                "timeframe": timeframe,
                "market_data": market_data,
                "technical_indicators": indicators,
                "analysis": analysis,
                "signal_status": signal_check,
                "agent_config": {
                    "name": self.agent_config.personality.name,
                    "risk_tolerance": self.agent_config.personality.risk_tolerance,
                    "analysis_style": self.agent_config.personality.analysis_style
                },
                "timestamp": analysis_time.isoformat(),
                "agent_id": self.agent_id
            }
            
            # Store in memory
            self._add_to_memory("market_analysis", result)
            
            return result
            
        except Exception as e:
            logger.error(f"Market analysis failed: {e}")
            return {
                "error": str(e),
                "symbol": symbol,
                "timeframe": timeframe,
                "timestamp": datetime.now().isoformat()
            }
    
    async def detect_patterns(self, symbol: str = "NQ=F", period: str = "1d") -> Dict[str, Any]:
        """Detect chart patterns in market data."""
        try:
            # Get historical data
            historical_data = await self.mcp_server.use_tool(
                "get_historical_data",
                symbol=symbol,
                period=period,
                interval="15m"
            )
            
            # Detect patterns using AI
            prompt = f"""
            Analyze the following price data for chart patterns:
            
            {historical_data}
            
            Identify any of these patterns:
            - Head and shoulders
            - Double top/bottom
            - Triangles (ascending, descending, symmetrical)
            - Flags and pennants
            - Cup and handle
            - Wedges
            
            For each pattern found, provide:
            1. Pattern type
            2. Confidence level (1-10)
            3. Potential price target
            4. Entry/exit points
            """
            
            pattern_analysis = await self.provider_manager.generate_response(
                prompt=prompt,
                provider=self.config.get('provider', 'ollama'),
                temperature=0.1
            )
            
            result = {
                "symbol": symbol,
                "period": period,
                "patterns": pattern_analysis,
                "timestamp": datetime.now().isoformat(),
                "agent_id": self.agent_id
            }
            
            self._add_to_memory("pattern_analysis", result)
            return result
            
        except Exception as e:
            logger.error(f"Pattern detection failed: {e}")
            return {"error": str(e), "symbol": symbol}
    
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific analysis task."""
        task_type = task.get("type", "market_analysis")
        parameters = task.get("parameters", {})
        
        if task_type == "market_analysis":
            return await self.analyze_market(
                symbol=parameters.get("symbol", "NQ=F"),
                timeframe=parameters.get("timeframe", "1h")
            )
        
        elif task_type == "pattern_detection":
            return await self.detect_patterns(
                symbol=parameters.get("symbol", "NQ=F"),
                period=parameters.get("period", "1d")
            )
        
        else:
            return {"error": f"Unknown task type: {task_type}"}
    
    async def get_analysis_summary(self, days: int = 1) -> Dict[str, Any]:
        """Get a summary of recent analyses."""
        try:
            recent_analyses = self.get_memory_by_type("market_analysis", 10)
            
            if not recent_analyses:
                return {"message": "No recent analyses found"}
            
            # Generate summary using AI
            prompt = f"""
            Summarize the following recent market analyses:
            
            {recent_analyses}
            
            Provide:
            1. Overall market trend
            2. Key observations
            3. Consistency of signals
            4. Current market sentiment
            """
            
            summary = await self.provider_manager.generate_response(
                prompt=prompt,
                provider=self.config.get('provider', 'ollama'),
                temperature=0.1
            )
            
            return {
                "summary": summary,
                "analysis_count": len(recent_analyses),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Analysis summary failed: {e}")
            return {"error": str(e)} 