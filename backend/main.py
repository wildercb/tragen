#!/usr/bin/env python3
"""
Main entry point for the MCP Trading Agent Backend
=================================================

FastAPI server that provides:
- MCP server with trading tools
- REST API for frontend communication
- WebSocket support for real-time updates
- Agent management and orchestration
"""

import asyncio
import logging
import os
import signal
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from mcp_trading_agent.server import TradingMCPServer
from mcp_trading_agent.api import create_api_router
from mcp_trading_agent.websocket import WebSocketManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global variables for graceful shutdown
mcp_server = None
ws_manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    global mcp_server, ws_manager
    
    logger.info("Starting MCP Trading Agent Backend...")
    
    # Initialize MCP server
    config_path = os.getenv("CONFIG_PATH", "mcp_trading_agent/config/config.yaml")
    mcp_server = TradingMCPServer(config_path)
    
    # Initialize WebSocket manager
    ws_manager = WebSocketManager()
    
    # Initialize provider manager (don't start the MCP server as it conflicts with FastAPI)
    try:
        await mcp_server.provider_manager.initialize()
        logger.info("MCP Trading Agent Backend started successfully")
        
        # Store in app state for access by routes
        app.state.mcp_server = mcp_server
        app.state.ws_manager = ws_manager
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to start MCP server: {e}")
        raise
    finally:
        # Cleanup
        logger.info("Shutting down MCP Trading Agent Backend...")
        if mcp_server:
            await mcp_server.provider_manager.cleanup()
        logger.info("Shutdown complete")

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(
        title="NQ Trading Agent API",
        description="Advanced NQ futures trading with AI analysis - Backend API",
        version="2.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        lifespan=lifespan
    )
    
    # CORS middleware for frontend communication
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://localhost:3001",
            "http://frontend:3000",
            "http://localhost",
            "https://localhost"
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint for Docker."""
        return {
            "status": "healthy",
            "service": "mcp-trading-agent-backend",
            "version": "2.0.0"
        }
    
    # Include API router (includes WebSocket endpoints)
    app.include_router(create_api_router(), prefix="/api")
    
    # Add WebSocket support for chart data
    @app.websocket("/ws/market/{symbol}")
    async def websocket_market_endpoint(websocket, symbol: str):
        """WebSocket endpoint for real-time market data."""
        # This will be handled by the API router
        pass
    
    return app

def setup_signal_handlers():
    """Setup signal handlers for graceful shutdown."""
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        # The lifespan context manager will handle cleanup
        
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

async def main():
    """Main entry point."""
    setup_signal_handlers()
    
    # Get configuration from environment
    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", "8000"))
    
    # Create application
    app = create_app()
    
    # Configure uvicorn
    config = uvicorn.Config(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=True,
        reload=False  # Set to True for development
    )
    
    # Start server
    server = uvicorn.Server(config)
    
    try:
        await server.serve()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())