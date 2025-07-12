"""
Agent Factory
=============

Factory functions for creating agents without circular imports.
"""

from typing import Dict, Any
from .analysis_agent import AnalysisAgent
from .execution_agent import ExecutionAgent
from .risk_agent import RiskAgent

def create_agent(agent_type: str, config: Dict[str, Any], mcp_server, provider_manager):
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