"""
MCP Server for NQ Trading Agent
==============================

FastMCP-based server that provides trading tools and agent capabilities
through the Model Context Protocol.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from fastmcp import FastMCP
from .tools import register_all_tools
from .providers import LLMProviderManager
from .config import TradingConfig
from .agents.agent_manager import AgentManager  # New import for modular agent management

logger = logging.getLogger(__name__)

class TradingMCPServer:
    """
    MCP Server for NQ Trading Agent operations.
    
    Provides:
    - Trading-specific MCP tools
    - Multi-provider LLM access
    - Agent orchestration (via AgentManager)
    - Context management
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the MCP server."""
        self.config = TradingConfig(config_path)
        self.mcp = FastMCP("NQ Trading Agent")
        self.provider_manager = LLMProviderManager(self.config.llm)
        self.agent_manager = AgentManager(self, self.provider_manager)  # Use new AgentManager
        self.tool_registry = {}  # Manual tool registry
        self._setup_server()
    
    def _setup_server(self):
        """Setup the MCP server with tools and capabilities."""
        logger.info("Setting up MCP server...")
        
        # Register all trading tools
        register_all_tools(self.mcp, self.config)
        
        # Setup server metadata
        self.mcp.server_info = {
            "name": "NQ Trading Agent",
            "version": "2.0.0",
            "description": "Advanced NQ futures trading with AI analysis",
            "capabilities": [
                "data_ingestion",
                "technical_analysis", 
                "ai_analysis",
                "trade_execution",
                "risk_management",
                "backtesting"
            ]
        }
        
        logger.info("MCP server setup complete")
    
    def register_tool(self, name: str, func):
        """Register a tool function manually."""
        self.tool_registry[name] = func
        logger.info(f"Registered tool: {name}")
    
    async def start(self, host: str = "localhost", port: int = 8000):
        """Start the MCP server."""
        logger.info(f"Starting MCP server on {host}:{port}")
        
        # Initialize provider manager
        await self.provider_manager.initialize()
        
        # Start the FastMCP server
        await self.mcp.run(host=host, port=port)
    
    async def stop(self):
        """Stop the MCP server and cleanup."""
        logger.info("Stopping MCP server...")
        await self.provider_manager.cleanup()
        logger.info("MCP server stopped")
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available MCP tools."""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters
            }
            for tool in self.mcp.list_tools()
        ]
    
    def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all LLM providers."""
        return self.provider_manager.get_status()
    
    async def create_agent(self, *args, **kwargs):
        return await self.agent_manager.create_agent(*args, **kwargs)
    
    async def execute_agent_task(self, *args, **kwargs):
        return await self.agent_manager.execute_agent_task(*args, **kwargs)
    
    def list_agents(self, *args, **kwargs):
        return self.agent_manager.list_agents(*args, **kwargs)
    
    async def use_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Execute an MCP tool by name."""
        try:
            # Check manual tool registry first
            if tool_name in self.tool_registry:
                tool_func = self.tool_registry[tool_name]
                result = await tool_func(**kwargs)
                return result
            
            # Debug: list available tools
            fastmcp_tools = list(getattr(self.mcp, 'tools', {}).keys())
            registry_tools = list(self.tool_registry.keys())
            logger.info(f"FastMCP tools: {fastmcp_tools}")
            logger.info(f"Registry tools: {registry_tools}")
            
            # Access the tool function directly from FastMCP
            if hasattr(self.mcp, 'tools') and tool_name in self.mcp.tools:
                tool_func = self.mcp.tools[tool_name]
                result = await tool_func(**kwargs)
                return result
            else:
                # Fallback - try to find tool by name in registered functions
                for name, func in self.mcp.__dict__.items():
                    if hasattr(func, '_tool_name') and func._tool_name == tool_name:
                        result = await func(**kwargs)
                        return result
                
                # Check if tool exists with slightly different registration
                tools = getattr(self.mcp, 'tools', {})
                logger.error(f"Tool '{tool_name}' not found. FastMCP tools: {list(tools.keys())}, Registry tools: {list(self.tool_registry.keys())}")
                raise ValueError(f"Tool '{tool_name}' not found")
        except Exception as e:
            logger.error(f"Failed to execute tool '{tool_name}': {e}")
            raise