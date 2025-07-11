"""
Context and Prompt Management System
===================================

Advanced context and prompt management for MCP trading agents:
- Context Templates
- Prompt Engineering  
- Dynamic Context Building
- Memory Management
- Multi-Agent Context Sharing
"""

from .context_manager import ContextManager
from .prompt_templates import PromptTemplateEngine
from .memory_manager import MemoryManager

__all__ = [
    "ContextManager",
    "PromptTemplateEngine", 
    "MemoryManager"
]