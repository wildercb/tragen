#!/usr/bin/env python3
"""
Production Server Startup Script
================================

Starts the Tragen production trading server with all components integrated.
"""

import asyncio
import logging
import sys
import signal
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from mcp_trading_agent.production_server import ProductionTradingServer

logger = logging.getLogger(__name__)

class ProductionServerRunner:
    """Production server runner with proper lifecycle management."""
    
    def __init__(self, config_path: str = None, host: str = "0.0.0.0", port: int = 8000):
        self.config_path = config_path
        self.host = host
        self.port = port
        self.server = None
        self.running = False
        
    async def start(self):
        """Start the production server."""
        logger.info("🚀 Starting Tragen Production Trading Server...")
        
        try:
            # Create server instance
            self.server = ProductionTradingServer(self.config_path)
            self.running = True
            
            # Setup signal handlers for graceful shutdown
            self._setup_signal_handlers()
            
            # Start the server
            await self.server.start(self.host, self.port)
            
        except Exception as e:
            logger.error(f"❌ Failed to start production server: {e}")
            raise
            
    async def stop(self):
        """Stop the production server gracefully."""
        if not self.running or not self.server:
            return
            
        logger.info("🛑 Shutting down production server...")
        self.running = False
        
        try:
            await self.server.cleanup()
            logger.info("✅ Production server shutdown complete")
        except Exception as e:
            logger.error(f"❌ Error during server shutdown: {e}")
            
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info(f"📡 Received signal {signum}, initiating graceful shutdown...")
            asyncio.create_task(self.stop())
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

def setup_logging(level: str = "INFO"):
    """Setup comprehensive logging."""
    log_format = (
        "%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s"
    )
    
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("logs/production.log") if Path("logs").exists() else logging.NullHandler()
        ]
    )
    
    # Set specific log levels for key components
    logging.getLogger("mcp_trading_agent.production").setLevel(logging.INFO)
    logging.getLogger("mcp_trading_agent.agents").setLevel(logging.INFO)
    logging.getLogger("mcp_trading_agent.training").setLevel(logging.INFO)
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)

def print_banner():
    """Print startup banner."""
    banner = """
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║    🏛️  TRAGEN PRODUCTION TRADING SYSTEM  🏛️              ║
    ║                                                          ║
    ║    Advanced AI Trading Agent Platform                    ║
    ║    Version: 1.0.0 Production                            ║
    ║                                                          ║
    ║    Features:                                             ║
    ║    • Multi-Agent Trading System                         ║
    ║    • Real-time Risk Management                          ║
    ║    • Live Training Interface                            ║
    ║    • Production Monitoring                              ║
    ║    • Emergency Controls                                 ║
    ║    • Comprehensive Audit Logging                       ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """
    print(banner)

def print_startup_info(host: str, port: int):
    """Print startup information."""
    info = f"""
    🌐 Server starting on: http://{host}:{port}
    
    📊 Key Endpoints:
    • Dashboard:           http://{host}:{port}/
    • API Documentation:   http://{host}:{port}/docs
    • System Status:       http://{host}:{port}/api/system/status
    • Agent Management:    http://{host}:{port}/api/agents/
    • Trading Interface:   http://{host}:{port}/api/trading/
    • Training Interface:  http://{host}:{port}/api/training/
    • Emergency Controls:  http://{host}:{port}/api/emergency/
    
    🔧 Configuration:
    • Trading Mode: Paper (Safe for testing)
    • Risk Management: Multi-layer protection
    • Circuit Breakers: Enabled
    • Audit Logging: Comprehensive
    • Real-time Monitoring: Active
    
    ⚠️  PRODUCTION NOTICE:
    This system is designed for real money trading.
    Ensure all safety systems are properly configured
    before enabling live trading mode.
    """
    print(info)

async def main():
    """Main entry point."""
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Tragen Production Trading Server",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--config", 
        help="Configuration file path",
        default=None
    )
    parser.add_argument(
        "--host", 
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8000,
        help="Port to bind to (default: 8000)"
    )
    parser.add_argument(
        "--log-level", 
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)"
    )
    parser.add_argument(
        "--dev-mode",
        action="store_true",
        help="Run in development mode with auto-reload"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    # Print banner
    print_banner()
    print_startup_info(args.host, args.port)
    
    # Create logs directory if it doesn't exist
    Path("logs").mkdir(exist_ok=True)
    
    # Create and run server
    runner = ProductionServerRunner(args.config, args.host, args.port)
    
    try:
        if args.dev_mode:
            logger.info("🔧 Running in development mode")
            # For development, you might want to use uvicorn with reload
            import uvicorn
            uvicorn.run(
                "mcp_trading_agent.production_server:ProductionTradingServer",
                host=args.host,
                port=args.port,
                reload=True,
                log_level=args.log_level.lower()
            )
        else:
            await runner.start()
            
    except KeyboardInterrupt:
        logger.info("👋 Shutdown requested by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)
    finally:
        await runner.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)