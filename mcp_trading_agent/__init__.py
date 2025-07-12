"""
NQ Trading Agent - MCP-Based Architecture
=====================================

A comprehensive trading agent framework built on Model Context Protocol (MCP)
using FastMCP for flexible agent, tool, and provider management.

Core Components:
- MCP Server with FastMCP
- Pluggable LLM providers (Ollama, OpenAI, Groq, External GPUs)
- Trading-specific MCP tools
- Agent framework with context management
- Web UI for interaction and customization
"""

__version__ = "2.0.0"
__author__ = "NQ Trading Agent Team"

from .server import TradingMCPServer
from .agents import AnalysisAgent, ExecutionAgent, RiskAgent
from .providers import LLMProviderManager
from .tools import register_all_tools

__all__ = [
    "TradingMCPServer",
    "AnalysisAgent",
    "ExecutionAgent", 
    "RiskAgent",
    "LLMProviderManager",
    "register_all_tools"
]