"""
Execution Agent
==============

Specialized agent for trade execution and order management.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

class ExecutionAgent(BaseAgent):
    """Agent specialized in trade execution and order management."""
    
    def __init__(self, config: Dict[str, Any], mcp_server, provider_manager):
        super().__init__(config, mcp_server, provider_manager)
        self.agent_type = "execution"
        self.capabilities = [
            "order_placement",
            "position_monitoring",
            "risk_management",
            "execution_optimization"
        ]
    
    def get_capabilities(self) -> List[str]:
        """Get list of agent capabilities."""
        return self.capabilities
    
    async def place_order(self, order_params: Dict[str, Any]) -> Dict[str, Any]:
        """Place a trading order."""
        try:
            # Validate order parameters
            required_params = ["action", "quantity", "symbol"]
            for param in required_params:
                if param not in order_params:
                    return {"error": f"Missing required parameter: {param}"}
            
            # Get current market data for validation
            market_data = await self.mcp_server.use_tool("get_nq_price")
            
            # Place order using MCP tool
            order_result = await self.mcp_server.use_tool(
                "place_order",
                **order_params
            )
            
            result = {
                "order_id": order_result.get("order_id"),
                "status": order_result.get("status", "pending"),
                "order_params": order_params,
                "market_price": market_data.get("current_price"),
                "timestamp": datetime.now().isoformat(),
                "agent_id": self.agent_id
            }
            
            # Store in memory
            self._add_to_memory("order_execution", result)
            
            return result
            
        except Exception as e:
            logger.error(f"Order placement failed: {e}")
            return {"error": str(e), "order_params": order_params}
    
    async def monitor_position(self, symbol: str = "NQ=F") -> Dict[str, Any]:
        """Monitor current position."""
        try:
            # Get position information
            position_data = await self.mcp_server.use_tool(
                "get_position_info",
                symbol=symbol
            )
            
            # Get current market data
            market_data = await self.mcp_server.use_tool("get_nq_price")
            
            # Calculate P&L
            if position_data.get("quantity", 0) != 0:
                entry_price = position_data.get("entry_price", 0)
                current_price = market_data.get("current_price", 0)
                quantity = position_data.get("quantity", 0)
                
                pnl = (current_price - entry_price) * quantity
                pnl_pct = ((current_price - entry_price) / entry_price) * 100 if entry_price > 0 else 0
            else:
                pnl = 0
                pnl_pct = 0
            
            result = {
                "symbol": symbol,
                "position": position_data,
                "market_price": market_data.get("current_price"),
                "pnl": pnl,
                "pnl_percentage": pnl_pct,
                "timestamp": datetime.now().isoformat(),
                "agent_id": self.agent_id
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Position monitoring failed: {e}")
            return {"error": str(e), "symbol": symbol}
    
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific execution task."""
        task_type = task.get("type", "place_order")
        parameters = task.get("parameters", {})
        
        if task_type == "place_order":
            return await self.place_order(parameters)
        
        elif task_type == "monitor_position":
            return await self.monitor_position(
                symbol=parameters.get("symbol", "NQ=F")
            )
        
        else:
            return {"error": f"Unknown task type: {task_type}"}
    
    async def get_execution_summary(self, days: int = 1) -> Dict[str, Any]:
        """Get a summary of recent executions."""
        try:
            recent_executions = self.get_memory_by_type("order_execution", 10)
            
            if not recent_executions:
                return {"message": "No recent executions found"}
            
            # Calculate summary statistics
            total_orders = len(recent_executions)
            successful_orders = sum(1 for order in recent_executions if order.get("status") == "filled")
            success_rate = (successful_orders / total_orders) * 100 if total_orders > 0 else 0
            
            return {
                "total_orders": total_orders,
                "successful_orders": successful_orders,
                "success_rate": success_rate,
                "recent_executions": recent_executions,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Execution summary failed: {e}")
            return {"error": str(e)} 