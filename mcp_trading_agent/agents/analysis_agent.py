"""
Analysis Agent
=============

Specialized agent for technical and fundamental analysis.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from .base_agent import BaseAgent

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
    
    def get_capabilities(self) -> List[str]:
        """Get list of agent capabilities."""
        return self.capabilities
    
    async def analyze_market(self, symbol: str = "NQ=F", timeframe: str = "1h") -> Dict[str, Any]:
        """Perform comprehensive market analysis."""
        try:
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
            
            # Generate AI analysis
            prompt = f"""
            Analyze the current market conditions for {symbol}:
            
            Current Price: ${market_data.get('current_price', 'N/A')}
            Session High: ${market_data.get('session_high', 'N/A')}
            Session Low: ${market_data.get('session_low', 'N/A')}
            Volume: {market_data.get('volume', 'N/A')}
            
            Technical Indicators:
            {indicators}
            
            Provide a concise analysis including:
            1. Current trend direction
            2. Key support/resistance levels
            3. Momentum assessment
            4. Trading recommendation (1-10 confidence)
            """
            
            analysis = await self.provider_manager.generate_response(
                prompt=prompt,
                provider=self.config.get('provider', 'ollama'),
                model=self.config.get('model'),
                temperature=0.1
            )
            
            result = {
                "symbol": symbol,
                "timeframe": timeframe,
                "market_data": market_data,
                "technical_indicators": indicators,
                "analysis": analysis,
                "timestamp": datetime.now().isoformat(),
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