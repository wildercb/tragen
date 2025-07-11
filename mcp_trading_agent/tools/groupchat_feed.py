"""
Groupchat Feed Tool
===================

MCP tool for fetching live feeds from trading groupchats (e.g., Slack/Discord).
"""

import logging
from typing import Dict, Any, List
import asyncio  # For async fetching

logger = logging.getLogger(__name__)

def register_groupchat_feed_tool(mcp_server, config):
    @mcp_server.tool()
    async def fetch_groupchat_feed(channel: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch recent messages from a trading groupchat.
        
        Args:
            channel: Groupchat channel name (e.g., 'nq-traders')
            limit: Max messages to fetch
        
        Returns:
            List of messages with timestamp, user, content
        """
        try:
            # TODO: Replace with real API integration (e.g., Slack API)
            # Mock data for now
            mock_messages = [
                {'timestamp': '2023-10-01T12:00:00', 'user': 'Trader1', 'content': 'NQ breaking resistance at 15000!'},
                {'timestamp': '2023-10-01T12:05:00', 'user': 'Trader2', 'content': 'Watch for pullback to MA50'}
            ] * (limit // 2)  # Repeat for mock limit
            return mock_messages[:limit]
        except Exception as e:
            logger.error(f"Error fetching groupchat feed: {e}")
            return [{'error': str(e)}]
    
    logger.info("Groupchat feed tool registered") 