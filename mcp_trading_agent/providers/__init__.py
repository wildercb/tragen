"""
LLM Provider Management for MCP Trading Agent
=============================================

Pluggable LLM provider system supporting multiple backends:
- Ollama (local models)
- OpenAI (cloud API)
- Groq (fast inference)
- External GPU servers
- Custom providers
"""

from .manager import LLMProviderManager
from .base import BaseLLMProvider
from .ollama import OllamaProvider
from .openai import OpenAIProvider
from .groq import GroqProvider
from .external import ExternalGPUProvider

__all__ = [
    "LLMProviderManager",
    "BaseLLMProvider", 
    "OllamaProvider",
    "OpenAIProvider",
    "GroqProvider",
    "ExternalGPUProvider"
]