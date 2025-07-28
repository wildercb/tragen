#!/usr/bin/env python3
"""
Main entry point for the Tragen Trading Agent Backend
====================================================

FastAPI server that provides:
- Production trading system with AI agents
- REST API for frontend communication  
- WebSocket support for real-time updates
- Agent management and orchestration
- Live training interface
- Comprehensive monitoring and safety systems
"""

import asyncio
import logging
import os
import signal
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Import production server components
from mcp_trading_agent.production_server import ProductionTradingServer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global variables for graceful shutdown
production_server = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    global production_server
    
    logger.info("🚀 Starting Tragen Production Trading Backend...")
    
    # Initialize production server
    config_path = os.getenv("CONFIG_PATH", "mcp_trading_agent/config/config.yaml")
    production_server = ProductionTradingServer(config_path)
    
    try:
        # Initialize all production components
        await production_server.initialize()
        
        # Start monitoring
        await production_server.monitor.start_monitoring()
        
        logger.info("✅ Tragen Production Trading Backend started successfully")
        
        # Store in app state for access by routes
        app.state.production_server = production_server
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Failed to start production server: {e}")
        raise
    finally:
        # Cleanup
        logger.info("🛑 Shutting down Tragen Production Trading Backend...")
        if production_server:
            await production_server.cleanup()
        logger.info("✅ Shutdown complete")

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    # Create app with integrated production server
    production_server_instance = ProductionTradingServer()
    app = production_server_instance.app
    
    # Update app metadata
    app.title = "Tragen Production Trading API"
    app.description = "Production-ready AI trading agent platform with comprehensive safety systems"
    app.version = "1.0.0 Production"
    app.docs_url = "/api/docs"
    app.redoc_url = "/api/redoc"
    
    # Set lifespan
    app.router.lifespan_context = lifespan
    
    # Serve static files from frontend build (if available)
    frontend_build_path = Path(__file__).parent.parent / "frontend" / "build"
    if frontend_build_path.exists():
        app.mount("/static", StaticFiles(directory=str(frontend_build_path / "static")), name="static")
        
        # Serve React app
        @app.get("/")
        async def serve_react_app():
            """Serve the React frontend."""
            from fastapi.responses import FileResponse
            return FileResponse(str(frontend_build_path / "index.html"))
    
    # Health check endpoint  
    @app.get("/health")
    async def health_check():
        """Enhanced health check endpoint."""
        try:
            system_status = await production_server.get_system_status() if production_server else {}
            return {
                "status": "healthy",
                "service": "tragen-production-backend", 
                "version": "1.0.0",
                "system_status": system_status.get('system_status', 'unknown'),
                "active_agents": system_status.get('active_agents', 0),
                "trading_mode": system_status.get('trading_mode', 'unknown')
            }
        except Exception as e:
            return {
                "status": "degraded",
                "service": "tragen-production-backend",
                "version": "1.0.0", 
                "error": str(e)
            }
    
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
    host = os.getenv("TRAGEN_HOST", "0.0.0.0")
    port = int(os.getenv("TRAGEN_PORT", "8000"))
    
    logger.info(f"🌐 Starting Tragen server on {host}:{port}")
    
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
        logger.info("🎯 Tragen Production Trading System ready!")
        await server.serve()
    except KeyboardInterrupt:
        logger.info("👋 Received keyboard interrupt, shutting down gracefully...")
    except Exception as e:
        logger.error(f"❌ Server error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())