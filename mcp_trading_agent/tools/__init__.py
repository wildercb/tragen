"""
MCP Tools for NQ Trading Agent
==============================

Trading-specific tools that extend FastMCP capabilities:
- Data ingestion tools
- Technical analysis tools
- AI analysis tools
- Trade execution tools
- Risk management tools
- Backtesting tools
"""

from .data_tools import register_data_tools
from .analysis_tools import register_analysis_tools
from .groupchat_feed import register_groupchat_feed_tool

def register_all_tools(mcp_server, config):
    """Register all trading tools with the MCP server."""
    print("Registering all tools...")
    try:
        register_data_tools(mcp_server, config)
        print("Data tools registered")
    except Exception as e:
        print(f"Error registering data tools: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        register_analysis_tools(mcp_server, config)
        print("Analysis tools registered")
    except Exception as e:
        print(f"Error registering analysis tools: {e}")
    
    # register_execution_tools(mcp_server, config)
    # register_risk_tools(mcp_server, config)
    # register_backtest_tools(mcp_server, config)
    
    try:
        register_groupchat_feed_tool(mcp_server, config)  # New live feed tool
        print("Groupchat feed tool registered")
    except Exception as e:
        print(f"Error registering groupchat feed tool: {e}")

__all__ = [
    "register_all_tools",
    "register_data_tools",
    "register_analysis_tools", 
    "register_execution_tools",
    "register_risk_tools",
    "register_backtest_tools"
]