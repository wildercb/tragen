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

def create_agent(agent_type: str, config: dict, mcp_server, provider_manager):
    """Factory function to create agents."""
    agent_classes = {
        'analysis': AnalysisAgent,
        'execution': ExecutionAgent,
        'risk': RiskAgent
    }
    
    agent_class = agent_classes.get(agent_type)
    if not agent_class:
        raise ValueError(f"Unknown agent type: {agent_type}")
    
    return agent_class(config, mcp_server, provider_manager)

__all__ = [
    "BaseAgent",
    "AnalysisAgent", 
    "ExecutionAgent",
    "RiskAgent",
    "AgentManager",
    "create_agent"
]