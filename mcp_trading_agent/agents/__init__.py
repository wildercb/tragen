"""
Agent Framework for MCP Trading Agent
====================================

Modular agent system with specialized trading agents:
- Analysis Agent: Technical and fundamental analysis
- Execution Agent: Trade execution and monitoring
- Risk Agent: Risk management and position sizing
- Research Agent: Market research and news analysis
"""

from .base_agent import BaseAgent
from .analysis_agent import AnalysisAgent
from .execution_agent import ExecutionAgent
from .risk_agent import RiskAgent
from .agent_manager import AgentManager
from .factory import create_agent

__all__ = [
    "BaseAgent",
    "AnalysisAgent", 
    "ExecutionAgent",
    "RiskAgent",
    "AgentManager",
    "create_agent"
]