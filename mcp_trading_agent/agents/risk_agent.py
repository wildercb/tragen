"""
Risk Agent
==========

Specialized agent for risk management and position sizing.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

class RiskAgent(BaseAgent):
    """Agent specialized in risk management and position sizing."""
    
    def __init__(self, config: Dict[str, Any], mcp_server, provider_manager):
        super().__init__(config, mcp_server, provider_manager)
        self.agent_type = "risk"
        self.capabilities = [
            "risk_assessment",
            "position_sizing",
            "portfolio_analysis",
            "drawdown_monitoring"
        ]
    
    def get_capabilities(self) -> List[str]:
        """Get list of agent capabilities."""
        return self.capabilities
    
    async def assess_trade_risk(self, trade_params: Dict[str, Any]) -> Dict[str, Any]:
        """Assess the risk of a proposed trade."""
        try:
            # Get current market data
            market_data = await self.mcp_server.use_tool("get_nq_price")
            
            # Calculate position size based on risk parameters
            account_balance = trade_params.get("account_balance", 100000)
            risk_per_trade = trade_params.get("risk_per_trade", 0.02)  # 2% default
            entry_price = trade_params.get("entry_price", market_data.get("current_price", 0))
            stop_loss = trade_params.get("stop_loss", 0)
            
            if stop_loss == 0:
                return {"error": "Stop loss is required for risk assessment"}
            
            # Calculate risk per share
            risk_per_share = abs(entry_price - stop_loss)
            
            # Calculate position size
            max_risk_amount = account_balance * risk_per_trade
            position_size = int(max_risk_amount / risk_per_share) if risk_per_share > 0 else 0
            
            # Calculate risk metrics
            total_risk = position_size * risk_per_share
            risk_percentage = (total_risk / account_balance) * 100
            
            # Risk assessment using AI
            prompt = f"""
            Assess the risk of this trade:
            
            Entry Price: ${entry_price}
            Stop Loss: ${stop_loss}
            Position Size: {position_size}
            Risk per Share: ${risk_per_share}
            Total Risk: ${total_risk}
            Risk Percentage: {risk_percentage:.2f}%
            
            Market Conditions:
            Current Price: ${market_data.get('current_price', 'N/A')}
            Session High: ${market_data.get('session_high', 'N/A')}
            Session Low: ${market_data.get('session_low', 'N/A')}
            
            Provide risk assessment (1-10 scale, 1=low risk, 10=high risk) and recommendation.
            """
            
            risk_analysis = await self.provider_manager.generate_response(
                prompt=prompt,
                provider=self.config.get('provider', 'ollama'),
                temperature=0.1
            )
            
            result = {
                "trade_params": trade_params,
                "calculated_position_size": position_size,
                "risk_per_share": risk_per_share,
                "total_risk": total_risk,
                "risk_percentage": risk_percentage,
                "risk_analysis": risk_analysis,
                "approved": risk_percentage <= 5.0,  # Approve if risk <= 5%
                "timestamp": datetime.now().isoformat(),
                "agent_id": self.agent_id
            }
            
            # Store in memory
            self._add_to_memory("risk_assessment", result)
            
            return result
            
        except Exception as e:
            logger.error(f"Risk assessment failed: {e}")
            return {"error": str(e), "trade_params": trade_params}
    
    async def monitor_portfolio_risk(self) -> Dict[str, Any]:
        """Monitor overall portfolio risk."""
        try:
            # Get portfolio information
            portfolio_data = await self.mcp_server.use_tool("get_portfolio_info")
            
            # Calculate portfolio metrics
            total_value = portfolio_data.get("total_value", 0)
            total_pnl = portfolio_data.get("total_pnl", 0)
            positions = portfolio_data.get("positions", [])
            
            # Calculate risk metrics
            total_risk = sum(pos.get("risk", 0) for pos in positions)
            risk_percentage = (total_risk / total_value) * 100 if total_value > 0 else 0
            
            # Portfolio risk assessment
            prompt = f"""
            Assess the overall portfolio risk:
            
            Total Portfolio Value: ${total_value}
            Total P&L: ${total_pnl}
            Total Risk: ${total_risk}
            Risk Percentage: {risk_percentage:.2f}%
            Number of Positions: {len(positions)}
            
            Positions:
            {positions}
            
            Provide overall risk assessment and recommendations for portfolio management.
            """
            
            risk_analysis = await self.provider_manager.generate_response(
                prompt=prompt,
                provider=self.config.get('provider', 'ollama'),
                temperature=0.1
            )
            
            result = {
                "portfolio_value": total_value,
                "total_pnl": total_pnl,
                "total_risk": total_risk,
                "risk_percentage": risk_percentage,
                "position_count": len(positions),
                "risk_analysis": risk_analysis,
                "timestamp": datetime.now().isoformat(),
                "agent_id": self.agent_id
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Portfolio risk monitoring failed: {e}")
            return {"error": str(e)}
    
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific risk management task."""
        task_type = task.get("type", "assess_risk")
        parameters = task.get("parameters", {})
        
        if task_type == "assess_risk":
            return await self.assess_trade_risk(parameters)
        
        elif task_type == "monitor_portfolio":
            return await self.monitor_portfolio_risk()
        
        else:
            return {"error": f"Unknown task type: {task_type}"}
    
    async def get_risk_summary(self, days: int = 1) -> Dict[str, Any]:
        """Get a summary of recent risk assessments."""
        try:
            recent_assessments = self.get_memory_by_type("risk_assessment", 10)
            
            if not recent_assessments:
                return {"message": "No recent risk assessments found"}
            
            # Calculate summary statistics
            total_assessments = len(recent_assessments)
            approved_trades = sum(1 for assessment in recent_assessments if assessment.get("approved"))
            approval_rate = (approved_trades / total_assessments) * 100 if total_assessments > 0 else 0
            
            avg_risk_pct = sum(assessment.get("risk_percentage", 0) for assessment in recent_assessments) / total_assessments if total_assessments > 0 else 0
            
            return {
                "total_assessments": total_assessments,
                "approved_trades": approved_trades,
                "approval_rate": approval_rate,
                "average_risk_percentage": avg_risk_pct,
                "recent_assessments": recent_assessments,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Risk summary failed: {e}")
            return {"error": str(e)} 