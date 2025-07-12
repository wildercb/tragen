"""
Agent Manager for MCP Trading Agent
===================================

Handles creation, execution, and listing of agents in a modular way.
"""

import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime
import os
from pathlib import Path

from typing import TYPE_CHECKING
from ..providers import LLMProviderManager
from .factory import create_agent  # Import from factory module

if TYPE_CHECKING:
    from ..server import TradingMCPServer

logger = logging.getLogger(__name__)

class AgentManager:
    """
    Manages trading agents for the MCP server.
    """
    
    def __init__(self, server: "TradingMCPServer", provider_manager: LLMProviderManager):
        self.server = server
        self.provider_manager = provider_manager
        self.agents: Dict[str, Any] = {}
    
    async def create_agent(self, agent_type: str, config: Dict[str, Any]) -> str:
        """Create a new agent instance with dynamic prompt/guide loading."""
        # Load prompts and guides if specified in config
        prompts = self._load_files(config.get('prompt_files', []), 'prompts')
        guides = self._load_files(config.get('guide_files', []), 'guides')
        
        # Inject into config for the agent
        config['loaded_prompts'] = prompts
        config['loaded_guides'] = guides
        
        agent_id = f"{agent_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        agent = create_agent(
            agent_type=agent_type,
            config=config,
            mcp_server=self.server,
            provider_manager=self.provider_manager
        )
        self.agents[agent_id] = agent
        logger.info(f"Created agent {agent_id} of type {agent_type} with {len(prompts)} prompts and {len(guides)} guides")
        return agent_id
    
    async def execute_agent_task(self, agent_id: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task using a specific agent."""
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not found")
        agent = self.agents[agent_id]
        return await agent.execute_task(task)
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """List all active agents."""
        return [
            {
                "id": agent_id,
                "type": agent.agent_type,
                "status": agent.status,
                "created": agent.created_at.isoformat()
            }
            for agent_id, agent in self.agents.items()
        ] 

    def _load_files(self, file_list: List[str], subdir: str) -> Dict[str, str]:
        """Load content from files in a subdirectory."""
        loaded = {}
        base_path = Path(__file__).parent.parent / subdir
        for filename in file_list:
            file_path = base_path / filename
            if file_path.exists():
                with open(file_path, 'r') as f:
                    loaded[filename] = f.read()
            else:
                logger.warning(f"File {file_path} not found")
        return loaded 