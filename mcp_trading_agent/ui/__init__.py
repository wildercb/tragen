"""
Web UI for MCP Trading Agent
============================

Modern web interface for interacting with and customizing the NQ trading agent:
- Real-time market data visualization
- Agent monitoring and control
- Configuration management
- Trading interface
- Backtesting tools
"""

from .app import create_app
from .websocket_manager import WebSocketManager

__all__ = [
    "create_app",
    "WebSocketManager"
]