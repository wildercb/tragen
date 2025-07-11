"""
Base Agent Class
================

Abstract base class for all trading agents in the MCP system.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import uuid

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """
    Abstract base class for all trading agents.
    
    Provides:
    - Common agent lifecycle management
    - Context and memory management  
    - Tool access through MCP server
    - LLM provider integration
    - Logging and monitoring
    """
    
    def __init__(self, config: Dict[str, Any], mcp_server, provider_manager):
        """Initialize the base agent."""
        self.agent_id = str(uuid.uuid4())
        self.config = config
        self.mcp_server = mcp_server
        self.provider_manager = provider_manager
        
        # Agent metadata
        self.agent_type = self.__class__.__name__.lower().replace('agent', '')
        self.created_at = datetime.now()
        self.status = "initialized"
        self.last_activity = datetime.now()
        
        # Context and memory
        self.context = {}
        self.memory = []
        self.max_memory_items = config.get('max_memory_items', 100)
        
        # LLM configuration
        self.llm_provider = config.get('provider', 'ollama')
        self.llm_model = config.get('model', 'phi3:mini')
        self.temperature = config.get('temperature', 0.1)
        self.max_tokens = config.get('max_tokens', 1000)
        
        logger.info(f"Initialized {self.agent_type} agent {self.agent_id}")
    
    @abstractmethod
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a specific task.
        
        Args:
            task: Task specification with type, parameters, etc.
            
        Returns:
            Task execution result
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """
        Get list of agent capabilities.
        
        Returns:
            List of capability strings
        """
        pass
    
    async def analyze_with_llm(
        self, 
        prompt: str, 
        context: Optional[Dict[str, Any]] = None,
        tools: Optional[List[str]] = None
    ) -> str:
        """
        Analyze data using LLM with optional tool access.
        
        Args:
            prompt: Analysis prompt
            context: Additional context
            tools: MCP tools to make available
            
        Returns:
            LLM analysis result
        """
        try:
            # Prepare full prompt with context
            full_prompt = self._prepare_prompt(prompt, context)
            
            # Generate response using provider manager
            response = await self.provider_manager.generate_response(
                prompt=full_prompt,
                provider=self.llm_provider,
                model=self.llm_model,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            # Update activity
            self.last_activity = datetime.now()
            self._add_to_memory("llm_analysis", {"prompt": prompt, "response": response})
            
            return response
            
        except Exception as e:
            logger.error(f"Error in LLM analysis for agent {self.agent_id}: {e}")
            raise
    
    async def use_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        Use an MCP tool.
        
        Args:
            tool_name: Name of the tool to use
            **kwargs: Tool parameters
            
        Returns:
            Tool execution result
        """
        try:
            # Access tool through MCP server
            tool_result = await self.mcp_server.mcp.call_tool(tool_name, **kwargs)
            
            self.last_activity = datetime.now()
            self._add_to_memory("tool_usage", {"tool": tool_name, "params": kwargs, "result": tool_result})
            
            return tool_result
            
        except Exception as e:
            logger.error(f"Error using tool {tool_name} in agent {self.agent_id}: {e}")
            raise
    
    def update_context(self, updates: Dict[str, Any]) -> None:
        """Update agent context."""
        self.context.update(updates)
        self.last_activity = datetime.now()
        logger.debug(f"Updated context for agent {self.agent_id}")
    
    def get_context(self, key: Optional[str] = None) -> Any:
        """Get context value or entire context."""
        if key:
            return self.context.get(key)
        return self.context.copy()
    
    def _prepare_prompt(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Prepare prompt with agent context and specialization."""
        parts = []
        
        # Agent specialization
        parts.append(f"You are a specialized {self.agent_type} agent for NQ futures trading.")
        
        # Add context
        if context:
            parts.append("Context:")
            for key, value in context.items():
                parts.append(f"- {key}: {value}")
        
        # Add current agent context
        if self.context:
            parts.append("Current Context:")
            for key, value in self.context.items():
                parts.append(f"- {key}: {value}")
        
        # Add recent memory for continuity
        recent_memory = self.get_recent_memory(3)
        if recent_memory:
            parts.append("Recent Activity:")
            for item in recent_memory:
                parts.append(f"- {item['type']}: {item['timestamp']}")
        
        # Add the actual prompt
        parts.append(f"Task: {prompt}")
        
        return "\\n\\n".join(parts)
    
    def _add_to_memory(self, memory_type: str, data: Dict[str, Any]) -> None:
        """Add item to agent memory."""
        memory_item = {
            "type": memory_type,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        
        self.memory.append(memory_item)
        
        # Trim memory if too large
        if len(self.memory) > self.max_memory_items:
            self.memory = self.memory[-self.max_memory_items:]
    
    def get_recent_memory(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent memory items."""
        return self.memory[-count:] if self.memory else []
    
    def get_memory_by_type(self, memory_type: str, count: int = 10) -> List[Dict[str, Any]]:
        """Get memory items of specific type."""
        filtered = [item for item in self.memory if item['type'] == memory_type]
        return filtered[-count:] if filtered else []
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status information."""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "capabilities": self.get_capabilities(),
            "context_items": len(self.context),
            "memory_items": len(self.memory),
            "llm_provider": self.llm_provider,
            "llm_model": self.llm_model
        }
    
    async def cleanup(self) -> None:
        """Cleanup agent resources."""
        logger.info(f"Cleaning up agent {self.agent_id}")
        self.status = "cleaned_up"
        # Override in subclasses for specific cleanup
    
    def __str__(self) -> str:
        """String representation of agent."""
        return f"{self.agent_type.title()}Agent({self.agent_id[:8]})"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"{self.__class__.__name__}(id='{self.agent_id}', status='{self.status}')"