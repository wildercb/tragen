"""
Production Trading Server
=========================

Enhanced server integration with all production trading components.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import json

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Import production components
from .production.production_controller import ProductionTradingController, TradingMode
from .production.agent_controller import ProductionAgentController, AgentType
from .production.monitoring import ProductionMonitor
from .production.audit_logger import AuditLogger
from .config.agent_config_builder import AgentConfigBuilder, SimpleAgentConfig
from .training.live_trainer import LiveTrainingInterface, TrainingMode as TrainingModeEnum
from .training.chart_interaction import ChartInteractionManager
from .training.feedback_system import FeedbackCollector
from .server import TradingMCPServer
from .providers import LLMProviderManager
from .config import TradingConfig

logger = logging.getLogger(__name__)

# Pydantic models for API
class AgentCreateRequest(BaseModel):
    agent_name: str
    agent_type: str = "production_trading"
    config: Dict[str, Any]
    auto_start: bool = True

class TrainingSessionRequest(BaseModel):
    agent_id: str
    mode: str
    symbol: str = "NQ=F"
    timeframe: str = "15m"

class FeedbackRequest(BaseModel):
    feedback_type: str = "rating"
    category: str = "general" 
    rating: Optional[int] = None
    comment: str = ""
    target_event_id: Optional[str] = None

class ProductionTradingServer:
    """
    Production-ready trading server with comprehensive agent management,
    real-time monitoring, and interactive training capabilities.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = TradingConfig(config_path)
        
        # Initialize FastAPI app
        self.app = FastAPI(
            title="Tragen Production Trading API",
            description="Production trading system with AI agents",
            version="1.0.0"
        )
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure appropriately for production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Core components
        self.mcp_server = TradingMCPServer(config_path)
        self.production_controller = ProductionTradingController(self.config.to_dict())
        self.agent_controller = ProductionAgentController(
            self.config.to_dict(), 
            self.mcp_server, 
            self.mcp_server.provider_manager
        )
        self.monitor = ProductionMonitor(self.config.to_dict())
        self.audit_logger = AuditLogger(self.config.to_dict())
        
        # Training components
        self.training_interface = LiveTrainingInterface(self.config.to_dict())
        self.chart_manager = ChartInteractionManager(self.config.to_dict())
        self.feedback_collector = FeedbackCollector(self.config.to_dict())
        
        # Configuration tools
        self.config_builder = AgentConfigBuilder()
        
        # WebSocket connections
        self.websocket_connections: Dict[str, WebSocket] = {}
        
        # Setup routes
        self._setup_routes()
        
    async def initialize(self):
        """Initialize all production components."""
        logger.info("Initializing production trading server...")
        
        try:
            # Initialize core components
            await self.production_controller.initialize()
            await self.agent_controller.initialize(self.audit_logger)
            await self.monitor.initialize()
            await self.audit_logger.initialize()
            
            # Initialize training components
            await self.training_interface.initialize(self.agent_controller)
            
            # Register production controller with agent controller
            for agent_id, agent_instance in self.agent_controller.agents.items():
                agent_instance.agent.data_source_manager = self.production_controller.data_source_manager
                
            logger.info("Production trading server initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize production server: {e}")
            raise
            
    def _setup_routes(self):
        """Setup FastAPI routes."""
        
        # Health check
        @self.app.get("/health")
        async def health_check():
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}
            
        # System status
        @self.app.get("/api/system/status")
        async def get_system_status():
            return await self.production_controller.get_system_status()
            
        # Monitoring dashboard
        @self.app.get("/api/monitoring/dashboard")
        async def get_monitoring_dashboard():
            return await self.monitor.get_monitoring_dashboard()
            
        # Agent management routes
        @self.app.post("/api/agents/create")
        async def create_agent(request: AgentCreateRequest):
            try:
                # Convert simple config if needed
                if 'agent_name' in request.config:
                    # This is a simple config from the UI
                    simple_config = SimpleAgentConfig(
                        agent_name=request.config['agent_name'],
                        personality=request.config.get('personality', {}),
                        risk_management=request.config.get('risk_management', {}),
                        analysis_methods=request.config.get('analysis_methods', {}),
                        trading_settings=request.config.get('trading_settings', {})
                    )
                    production_config = self.config_builder.convert_to_production_config(simple_config)
                else:
                    production_config = request.config
                    
                agent_instance = await self.agent_controller.create_agent(
                    request.agent_name,
                    AgentType(request.agent_type),
                    production_config,
                    request.auto_start
                )
                
                # Register with production controller
                await self.production_controller.register_agent(
                    request.agent_name,
                    production_config
                )
                
                return {
                    "success": True,
                    "agent_id": agent_instance.agent_id,
                    "message": f"Agent {request.agent_name} created successfully"
                }
                
            except Exception as e:
                logger.error(f"Failed to create agent: {e}")
                raise HTTPException(status_code=400, detail=str(e))
                
        @self.app.get("/api/agents/status")
        async def get_agents_status():
            return await self.agent_controller.get_all_agents_status()
            
        @self.app.get("/api/agents/templates")
        async def get_agent_templates():
            return self.agent_controller.get_agent_templates()
            
        @self.app.post("/api/agents/{agent_id}/start")
        async def start_agent(agent_id: str):
            try:
                await self.agent_controller.start_agent(agent_id)
                return {"success": True, "message": f"Agent {agent_id} started"}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
                
        @self.app.post("/api/agents/{agent_id}/stop")
        async def stop_agent(agent_id: str):
            try:
                await self.agent_controller.stop_agent(agent_id)
                return {"success": True, "message": f"Agent {agent_id} stopped"}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
                
        @self.app.post("/api/agents/{agent_id}/pause")
        async def pause_agent(agent_id: str):
            try:
                await self.agent_controller.pause_agent(agent_id)
                return {"success": True, "message": f"Agent {agent_id} paused"}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
                
        @self.app.put("/api/agents/{agent_id}/config")
        async def update_agent_config(agent_id: str, config_updates: Dict[str, Any]):
            try:
                await self.agent_controller.update_agent_config(agent_id, config_updates)
                return {"success": True, "message": f"Agent {agent_id} configuration updated"}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
                
        @self.app.delete("/api/agents/{agent_id}")
        async def remove_agent(agent_id: str, reason: str = "User request"):
            try:
                await self.agent_controller.remove_agent(agent_id, reason)
                await self.production_controller.deregister_agent(agent_id, reason)
                return {"success": True, "message": f"Agent {agent_id} removed"}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
                
        @self.app.get("/api/agents/{agent_id}/performance")
        async def get_agent_performance(agent_id: str):
            try:
                return await self.agent_controller.get_agent_performance(agent_id)
            except Exception as e:
                raise HTTPException(status_code=404, detail=str(e))
                
        @self.app.post("/api/agents/{agent_id}/task")
        async def execute_agent_task(agent_id: str, task: Dict[str, Any]):
            try:
                result = await self.agent_controller.execute_agent_task(agent_id, task)
                
                # Record execution in monitoring
                if 'decision' in result:
                    decision = result['decision']
                    # Create a mock execution result for monitoring
                    execution_result = type('obj', (object,), {
                        'symbol': task.get('parameters', {}).get('symbol', 'NQ=F'),
                        'action': decision.get('action', 'hold'),
                        'execution_status': 'simulated',
                        'recommended_quantity': decision.get('quantity', 0),
                        'fees': 0.0,
                        'slippage': 0.0
                    })()
                    
                    await self.monitor.record_execution(execution_result)
                
                return result
                
            except Exception as e:
                logger.error(f"Task execution failed: {e}")
                raise HTTPException(status_code=400, detail=str(e))
                
        # Trading execution routes
        @self.app.post("/api/trading/execute")
        async def execute_trading_decision(decision_data: Dict[str, Any]):
            try:
                from .production.production_controller import TradingDecision
                
                decision = TradingDecision(
                    agent_id=decision_data['agent_id'],
                    symbol=decision_data['symbol'],
                    action=decision_data['action'],
                    confidence=decision_data['confidence'],
                    reasoning=decision_data['reasoning'],
                    recommended_quantity=decision_data['recommended_quantity'],
                    recommended_price=decision_data.get('recommended_price'),
                    stop_loss=decision_data.get('stop_loss'),
                    take_profit=decision_data.get('take_profit'),
                    risk_factors=decision_data.get('risk_factors', {}),
                    metadata=decision_data.get('metadata', {})
                )
                
                result = await self.production_controller.execute_trading_decision(
                    decision_data['agent_id'],
                    decision
                )
                
                return {
                    "success": result.execution_status == 'executed',
                    "execution_result": {
                        "decision_id": result.decision_id,
                        "symbol": result.symbol,
                        "action": result.action,
                        "executed_quantity": result.executed_quantity,
                        "executed_price": result.executed_price,
                        "execution_status": result.execution_status,
                        "error_message": result.error_message
                    }
                }
                
            except Exception as e:
                logger.error(f"Trading execution failed: {e}")
                raise HTTPException(status_code=400, detail=str(e))
                
        # Emergency controls
        @self.app.post("/api/emergency/halt")
        async def emergency_halt(reason: str = "Manual emergency halt"):
            try:
                await self.production_controller.emergency_halt(reason)
                return {"success": True, "message": f"Emergency halt activated: {reason}"}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
                
        @self.app.post("/api/emergency/close-all")
        async def emergency_close_all_positions(reason: str = "Manual position closure"):
            try:
                closed_positions = await self.production_controller.emergency_close_all_positions(reason)
                return {
                    "success": True,
                    "message": f"All positions closed: {reason}",
                    "closed_positions": closed_positions
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
                
        @self.app.post("/api/trading/mode")
        async def set_trading_mode(mode: str, reason: str = "Mode change request"):
            try:
                trading_mode = TradingMode(mode)
                await self.production_controller.set_trading_mode(trading_mode, reason)
                return {"success": True, "message": f"Trading mode set to {mode}"}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
                
        # Training routes
        @self.app.post("/api/training/start")
        async def start_training_session(request: TrainingSessionRequest):
            try:
                session = await self.training_interface.start_training_session(
                    request.agent_id,
                    "user",  # Would get from auth
                    TrainingModeEnum(request.mode),
                    request.symbol,
                    request.timeframe
                )
                return {
                    "success": True,
                    "session_id": session.session_id,
                    "message": "Training session started"
                }
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
                
        @self.app.post("/api/training/end/{session_id}")
        async def end_training_session(session_id: str):
            try:
                summary = await self.training_interface.end_training_session(session_id)
                return {"success": True, "summary": summary}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
                
        @self.app.post("/api/training/annotate/{session_id}")
        async def add_chart_annotation(session_id: str, annotation_data: Dict[str, Any]):
            try:
                event = await self.training_interface.record_chart_annotation(
                    session_id, annotation_data
                )
                return {"success": True, "event_id": event.event_id}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
                
        @self.app.post("/api/training/feedback/{session_id}")
        async def submit_training_feedback(session_id: str, feedback: FeedbackRequest):
            try:
                event = await self.training_interface.record_feedback(
                    session_id, feedback.dict()
                )
                return {"success": True, "event_id": event.event_id}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
                
        @self.app.post("/api/training/question/{session_id}")
        async def ask_agent_question(session_id: str, question_data: Dict[str, Any]):
            try:
                result = await self.training_interface.ask_agent_question(
                    session_id, 
                    question_data['question'],
                    question_data.get('context', {})
                )
                return result
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
                
        @self.app.post("/api/training/analysis/{session_id}")
        async def get_agent_analysis(session_id: str, request_data: Dict[str, Any]):
            try:
                result = await self.training_interface.get_agent_analysis(
                    session_id,
                    request_data.get('symbol'),
                    request_data.get('timeframe')
                )
                return result
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
                
        @self.app.get("/api/training/status/{session_id}")
        async def get_training_session_status(session_id: str):
            try:
                return await self.training_interface.get_session_status(session_id)
            except Exception as e:
                raise HTTPException(status_code=404, detail=str(e))
                
        # Configuration routes
        @self.app.get("/api/config/wizard")
        async def get_config_wizard():
            return self.config_builder.create_config_wizard()
            
        @self.app.get("/api/config/presets")
        async def get_config_presets():
            presets = self.config_builder.get_preset_configs()
            return {name: config.__dict__ for name, config in presets.items()}
            
        @self.app.post("/api/config/validate")
        async def validate_agent_config(config_data: Dict[str, Any]):
            try:
                # Create SimpleAgentConfig from data
                simple_config = SimpleAgentConfig(**config_data)
                issues = self.config_builder.validate_config(simple_config)
                
                return {
                    "valid": len(issues) == 0,
                    "issues": issues
                }
            except Exception as e:
                return {
                    "valid": False,
                    "issues": [str(e)]
                }
                
        # WebSocket for real-time updates
        @self.app.websocket("/ws/training/{session_id}")
        async def training_websocket(websocket: WebSocket, session_id: str):
            await websocket.accept()
            self.websocket_connections[session_id] = websocket
            
            try:
                await self.training_interface.connect_websocket(session_id, websocket)
                
                while True:
                    # Keep connection alive and handle any client messages
                    message = await websocket.receive_text()
                    data = json.loads(message)
                    
                    # Handle different message types
                    if data.get('type') == 'ping':
                        await websocket.send_text(json.dumps({"type": "pong"}))
                        
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for session {session_id}")
            finally:
                await self.training_interface.disconnect_websocket(session_id)
                self.websocket_connections.pop(session_id, None)
                
        @self.app.websocket("/ws/monitoring")
        async def monitoring_websocket(websocket: WebSocket):
            await websocket.accept()
            
            try:
                while True:
                    # Send periodic monitoring updates
                    dashboard_data = await self.monitor.get_monitoring_dashboard()
                    await websocket.send_text(json.dumps({
                        "type": "monitoring_update",
                        "data": dashboard_data
                    }))
                    
                    await asyncio.sleep(5)  # Update every 5 seconds
                    
            except WebSocketDisconnect:
                logger.info("Monitoring WebSocket disconnected")
                
    async def start(self, host: str = "0.0.0.0", port: int = 8000):
        """Start the production server."""
        logger.info(f"Starting production trading server on {host}:{port}")
        
        await self.initialize()
        
        # Start monitoring
        await self.monitor.start_monitoring()
        
        # Start the FastAPI server
        config = uvicorn.Config(
            self.app,
            host=host,
            port=port,
            log_level="info",
            reload=False  # Disable for production
        )
        
        server = uvicorn.Server(config)
        await server.serve()
        
    async def cleanup(self):
        """Cleanup all resources."""
        logger.info("Cleaning up production server...")
        
        try:
            # Stop monitoring
            await self.monitor.stop_monitoring()
            
            # Cleanup components
            await self.production_controller.cleanup()
            await self.agent_controller.cleanup()
            await self.training_interface.cleanup()
            await self.chart_manager.cleanup()
            await self.feedback_collector.cleanup()
            await self.audit_logger.cleanup()
            await self.monitor.cleanup()
            
            # Close WebSocket connections
            for websocket in self.websocket_connections.values():
                try:
                    await websocket.close()
                except:
                    pass
                    
            logger.info("Production server cleanup complete")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

# Main entry point
async def main():
    """Main entry point for the production server."""
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="Tragen Production Trading Server")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and start server
    server = ProductionTradingServer(args.config)
    
    try:
        await server.start(args.host, args.port)
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    finally:
        await server.cleanup()

if __name__ == "__main__":
    asyncio.run(main())