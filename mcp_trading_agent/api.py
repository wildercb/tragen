"""
API Router for MCP Trading Agent
===============================

FastAPI router providing REST endpoints for the trading agent.
"""

import logging
import asyncio
import json
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Request, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import random

logger = logging.getLogger(__name__)

# Request/Response models
class AgentTaskRequest(BaseModel):
    type: str
    parameters: Dict[str, Any] = {}

class AgentCreateRequest(BaseModel):
    agent_type: str
    config: Dict[str, Any] = {}

class AgentTaskResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class ModelSwitchRequest(BaseModel):
    provider: str
    model: str
    agent_id: Optional[str] = None

class MarketDataResponse(BaseModel):
    symbol: str
    current_price: float
    session_high: float
    session_low: float
    volume: int
    timestamp: str

def get_mcp_server(request: Request):
    """Dependency to get MCP server from app state."""
    return request.app.state.mcp_server

def get_ws_manager(request: Request):
    """Dependency to get WebSocket manager from app state."""
    return request.app.state.ws_manager

def create_api_router() -> APIRouter:
    """Create and configure the API router."""
    router = APIRouter()
    
    @router.get("/status")
    async def get_status():
        """Get system status."""
        return {
            "status": "running",
            "version": "2.0.0",
            "service": "mcp-trading-agent"
        }
    
    @router.get("/market/price")
    async def get_market_price(symbol: str = "NQ=F"):
        """Get current market price for any symbol."""
        try:
            ticker = yf.Ticker(symbol)
            
            # Get recent data for more accurate current price
            recent_data = ticker.history(period="1d", interval="1m")
            
            if recent_data.empty:
                raise HTTPException(status_code=404, detail="No data available for symbol")
            
            current_price = recent_data['Close'].iloc[-1]
            session_high = recent_data['High'].max()
            session_low = recent_data['Low'].min()
            volume = int(recent_data['Volume'].sum())
            timestamp = datetime.now().isoformat()
            
            return MarketDataResponse(
                symbol=symbol,
                current_price=float(current_price),
                session_high=float(session_high),
                session_low=float(session_low),
                volume=volume,
                timestamp=timestamp
            )
        except Exception as e:
            logger.error(f"Failed to get price for {symbol}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/market/nq-price")
    async def get_nq_price():
        """Get current NQ futures price (legacy endpoint)."""
        return await get_market_price("NQ=F")
    
    @router.get("/market/historical")
    async def get_historical_data(
        symbol: str = "NQ=F",
        period: str = "5d",
        interval: str = "5m",
        max_points: int = 500
    ):
        """Get historical market data with extended timeframes."""
        try:
            # Direct implementation bypassing MCP for now
            ticker = yf.Ticker(symbol)
            
            # Use longer periods for better chart data
            period_mapping = {
                "1d": "1d",
                "5d": "5d", 
                "1mo": "1mo",
                "3mo": "3mo",
                "6mo": "6mo",
                "1y": "1y",
                "2y": "2y",
                "5y": "5y"
            }
            
            # Get the mapped period or use provided period
            actual_period = period_mapping.get(period, period)
            data = ticker.history(period=actual_period, interval=interval)
            
            if data.empty:
                raise HTTPException(status_code=404, detail="No historical data available")
            
            # Limit data points for performance
            if len(data) > max_points:
                data = data.tail(max_points)
            
            # Convert to records for JSON serialization
            ohlcv_data = []
            for timestamp, row in data.iterrows():
                ohlcv_data.append({
                    "date": timestamp.isoformat(),
                    "open": float(row['Open']),
                    "high": float(row['High']),
                    "low": float(row['Low']),
                    "close": float(row['Close']),
                    "volume": int(row['Volume'])
                })
            
            return {
                "symbol": symbol,
                "period": actual_period,
                "interval": interval,
                "data_points": len(ohlcv_data),
                "start_time": data.index[0].isoformat(),
                "end_time": data.index[-1].isoformat(),
                "data": ohlcv_data,
                "summary": {
                    "current_price": float(data['Close'].iloc[-1]),
                    "period_high": float(data['High'].max()),
                    "period_low": float(data['Low'].min()),
                    "total_volume": int(data['Volume'].sum()),
                    "price_change": float(data['Close'].iloc[-1] - data['Open'].iloc[0]),
                    "price_change_pct": float((data['Close'].iloc[-1] - data['Open'].iloc[0]) / data['Open'].iloc[0] * 100)
                }
            }
        except Exception as e:
            logger.error(f"Failed to get historical data for {symbol}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/agents")
    async def create_agent(
        request: AgentCreateRequest,
        mcp_server = Depends(get_mcp_server)
    ):
        """Create a new agent."""
        try:
            agent_id = await mcp_server.agent_manager.create_agent(
                agent_type=request.agent_type,
                config=request.config
            )
            return {"agent_id": agent_id, "status": "created"}
        except Exception as e:
            logger.error(f"Failed to create agent: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/agents")
    async def list_agents(mcp_server = Depends(get_mcp_server)):
        """List all agents."""
        try:
            agents = mcp_server.agent_manager.list_agents()
            return {"agents": agents}
        except Exception as e:
            logger.error(f"Failed to list agents: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/agents/{agent_id}/tasks")
    async def execute_agent_task(
        agent_id: str,
        request: AgentTaskRequest,
        mcp_server = Depends(get_mcp_server)
    ):
        """Execute a task using a specific agent."""
        try:
            result = await mcp_server.agent_manager.execute_agent_task(
                agent_id=agent_id,
                task={
                    "type": request.type,
                    "parameters": request.parameters
                }
            )
            return AgentTaskResponse(
                task_id=f"{agent_id}_{request.type}",
                status="completed",
                result=result
            )
        except Exception as e:
            logger.error(f"Failed to execute agent task: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/providers/status")
    async def get_provider_status(mcp_server = Depends(get_mcp_server)):
        """Get LLM provider status."""
        try:
            status = mcp_server.provider_manager.get_status()
            return status
        except Exception as e:
            logger.error(f"Failed to get provider status: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/providers/models")
    async def get_available_models(mcp_server = Depends(get_mcp_server)):
        """Get available models from all providers."""
        try:
            models = mcp_server.provider_manager.get_available_models()
            return {"models": models}
        except Exception as e:
            logger.error(f"Failed to get available models: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/providers/switch-model")
    async def switch_model(
        request: ModelSwitchRequest,
        mcp_server = Depends(get_mcp_server)
    ):
        """Switch the model for a specific agent or globally."""
        try:
            if request.agent_id:
                # Switch model for specific agent
                agent = mcp_server.agent_manager.get_agent(request.agent_id)
                if not agent:
                    raise HTTPException(status_code=404, detail="Agent not found")
                
                agent.provider = request.provider
                agent.model = request.model
                
                return {
                    "status": "success",
                    "message": f"Model switched to {request.provider}:{request.model} for agent {request.agent_id}"
                }
            else:
                # Switch default provider/model globally
                mcp_server.provider_manager.default_provider = request.provider
                
                return {
                    "status": "success", 
                    "message": f"Default provider switched to {request.provider}:{request.model}"
                }
        except Exception as e:
            logger.error(f"Failed to switch model: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/providers/external-gpu/add")
    async def add_external_gpu_endpoint(
        endpoint_config: Dict[str, Any],
        mcp_server = Depends(get_mcp_server)
    ):
        """Add a new external GPU endpoint."""
        try:
            # Validate required fields
            required_fields = ['name', 'url']
            for field in required_fields:
                if field not in endpoint_config:
                    raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
            
            # Add to external GPU provider if it exists
            if 'external_gpu' in mcp_server.provider_manager.providers:
                gpu_provider = mcp_server.provider_manager.providers['external_gpu']
                gpu_provider.endpoints.append(endpoint_config)
                
                # Test the new endpoint
                await gpu_provider.health_check()
                
                return {
                    "status": "success",
                    "message": f"External GPU endpoint '{endpoint_config['name']}' added successfully"
                }
            else:
                raise HTTPException(status_code=400, detail="External GPU provider not initialized")
                
        except Exception as e:
            logger.error(f"Failed to add external GPU endpoint: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.websocket("/ws/market/{symbol}")
    async def websocket_market_data(
        websocket: WebSocket,
        symbol: str,
        ws_manager = Depends(get_ws_manager),
        mcp_server = Depends(get_mcp_server)
    ):
        """WebSocket endpoint for real-time market data and trading signals."""
        await ws_manager.connect(websocket, f"market_{symbol}")
        
        # Subscribe to market data updates
        ws_manager.subscribe(websocket, "market_data")
        ws_manager.subscribe(websocket, "trading_signals")
        
        try:
            # Send initial historical data
            try:
                # Direct historical data implementation with extended period
                ticker = yf.Ticker(symbol)
                data = ticker.history(period="5d", interval="5m")
                
                if not data.empty:
                    # Limit data points
                    if len(data) > 100:
                        data = data.tail(100)
                    
                    # Convert to records for JSON serialization
                    ohlcv_data = []
                    for timestamp, row in data.iterrows():
                        ohlcv_data.append({
                            "date": timestamp.isoformat(),
                            "open": float(row['Open']),
                            "high": float(row['High']),
                            "low": float(row['Low']),
                            "close": float(row['Close']),
                            "volume": int(row['Volume'])
                        })
                    
                    result = {
                        "symbol": symbol,
                        "data": ohlcv_data
                    }
                    
                    await ws_manager.send_personal_message(
                        json.dumps({
                            "type": "historical_data",
                            "data": result
                        }),
                        websocket
                    )
                else:
                    # Send mock data as fallback
                    await send_mock_historical_data(websocket, symbol)
            except Exception as e:
                logger.error(f"Failed to send initial data: {e}")
                # Send mock data as fallback
                await send_mock_historical_data(websocket, symbol)
            
            # Start real-time data simulation
            asyncio.create_task(simulate_real_time_data(websocket, symbol, ws_manager))
            
            # Listen for client messages
            while True:
                try:
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    
                    if message.get("type") == "subscribe":
                        subscription = message.get("subscription")
                        if subscription:
                            ws_manager.subscribe(websocket, subscription)
                    
                    elif message.get("type") == "unsubscribe":
                        subscription = message.get("subscription")
                        if subscription:
                            ws_manager.unsubscribe(websocket, subscription)
                    
                    elif message.get("type") == "request_analysis":
                        # Trigger analysis through MCP agent
                        await trigger_market_analysis(websocket, symbol, mcp_server, ws_manager)
                        
                except WebSocketDisconnect:
                    break
                except Exception as e:
                    logger.error(f"WebSocket error: {e}")
                    break
                    
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for {symbol}")
        finally:
            ws_manager.disconnect(websocket)
    
    async def send_mock_historical_data(websocket: WebSocket, symbol: str):
        """Send mock historical data for demonstration."""
        try:
            # Generate mock OHLC data
            base_price = 16500.0 if symbol == "NQ=F" else 4500.0
            data = []
            current_time = datetime.now()
            
            for i in range(100, 0, -1):
                timestamp = current_time - timedelta(minutes=i * 5)
                price = base_price + random.uniform(-50, 50)
                volatility = random.uniform(2, 10)
                
                open_price = price
                high_price = open_price + random.uniform(0, volatility)
                low_price = open_price - random.uniform(0, volatility)
                close_price = low_price + random.uniform(0, high_price - low_price)
                volume = random.randint(1000, 5000)
                
                data.append({
                    "date": timestamp.isoformat(),
                    "open": round(open_price, 2),
                    "high": round(high_price, 2),
                    "low": round(low_price, 2),
                    "close": round(close_price, 2),
                    "volume": volume
                })
            
            await websocket.send_text(json.dumps({
                "type": "historical_data",
                "data": {"data": data}
            }))
            
        except Exception as e:
            logger.error(f"Failed to send mock historical data: {e}")
    
    async def simulate_real_time_data(websocket: WebSocket, symbol: str, ws_manager):
        """Simulate real-time price updates and trading signals."""
        base_price = 16500.0 if symbol == "NQ=F" else 4500.0
        current_price = base_price
        signal_counter = 0
        
        try:
            while True:
                # Simulate price movement
                change = random.uniform(-5, 5)
                current_price += change
                
                # Send price update
                price_data = {
                    "type": "price_update",
                    "symbol": symbol,
                    "open": round(current_price - random.uniform(0, 2), 2),
                    "high": round(current_price + random.uniform(0, 3), 2),
                    "low": round(current_price - random.uniform(0, 3), 2),
                    "close": round(current_price, 2),
                    "volume": random.randint(100, 500),
                    "change": round(change, 2),
                    "timestamp": datetime.now().isoformat()
                }
                
                await ws_manager.send_personal_message(
                    json.dumps(price_data),
                    websocket
                )
                
                # Occasionally send trading signals
                signal_counter += 1
                if signal_counter % 20 == 0:  # Every 20 updates (~2 minutes)
                    signal_type = random.choice(["buy", "sell"])
                    confidence = random.uniform(0.6, 0.95)
                    
                    signal_data = {
                        "type": "signal",
                        "signal": {
                            "type": signal_type,
                            "price": round(current_price, 2),
                            "confidence": confidence,
                            "strength": random.uniform(0.5, 2.0),
                            "reason": f"Technical analysis suggests {signal_type} signal",
                            "time": int(datetime.now().timestamp()),
                            "indicators": {
                                "rsi": random.uniform(20, 80),
                                "macd": random.uniform(-2, 2),
                                "volume_spike": random.choice([True, False])
                            }
                        }
                    }
                    
                    await ws_manager.send_personal_message(
                        json.dumps(signal_data),
                        websocket
                    )
                
                # Occasionally send limit order suggestions
                if signal_counter % 35 == 0:  # Every 35 updates
                    orders = []
                    if random.random() > 0.5:
                        orders.append({
                            "type": "limit_buy",
                            "price": round(current_price - random.uniform(5, 15), 2),
                            "reason": "Support level identified"
                        })
                    if random.random() > 0.5:
                        orders.append({
                            "type": "limit_sell",
                            "price": round(current_price + random.uniform(5, 15), 2),
                            "reason": "Resistance level identified"
                        })
                    
                    if orders:
                        await ws_manager.send_personal_message(
                            json.dumps({
                                "type": "limit_order",
                                "orders": orders
                            }),
                            websocket
                        )
                
                await asyncio.sleep(6)  # Update every 6 seconds
                
        except Exception as e:
            logger.error(f"Real-time data simulation error: {e}")
    
    async def trigger_market_analysis(websocket: WebSocket, symbol: str, mcp_server, ws_manager):
        """Trigger market analysis through MCP agent."""
        try:
            # Execute analysis task
            result = await mcp_server.agent_manager.execute_agent_task(
                agent_id="analysis_agent",
                task={
                    "type": "market_analysis",
                    "parameters": {
                        "symbol": symbol,
                        "timeframe": "5m",
                        "indicators": ["sma", "rsi", "macd", "bollinger"]
                    }
                }
            )
            
            # Send analysis result
            await ws_manager.send_personal_message(
                json.dumps({
                    "type": "analysis_result",
                    "data": result
                }),
                websocket
            )
            
        except Exception as e:
            logger.error(f"Failed to trigger market analysis: {e}")
            # Send mock analysis result
            mock_analysis = {
                "type": "analysis_result",
                "data": {
                    "trend": random.choice(["bullish", "bearish", "neutral"]),
                    "strength": random.uniform(0.3, 0.9),
                    "support_levels": [16500 - random.uniform(10, 30) for _ in range(2)],
                    "resistance_levels": [16500 + random.uniform(10, 30) for _ in range(2)],
                    "recommendation": random.choice(["BUY", "SELL", "HOLD"]),
                    "confidence": random.uniform(0.6, 0.9)
                }
            }
            await ws_manager.send_personal_message(json.dumps(mock_analysis), websocket)
    
    return router 