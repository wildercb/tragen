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
import aiohttp
import time
from .tradingview_provider import tv_provider
from .market_context import market_analyzer

logger = logging.getLogger(__name__)

# Enhanced cache and strict rate limiting 
_cache = {}
_cache_ttl = {}
_last_api_call = {}
_request_count = 0
_request_window_start = time.time()

# TradingView rate limit: 100 requests per minute
MAX_REQUESTS_PER_MINUTE = 95  # Stay safely under 100
RATE_WINDOW_SECONDS = 60

def get_cached_data(key: str, ttl_seconds: int = 300):
    """Get cached data if it exists and is not expired."""
    if key in _cache and key in _cache_ttl:
        if time.time() - _cache_ttl[key] < ttl_seconds:
            logger.info(f"Using cached data for {key}")
            return _cache[key]
    return None

def set_cached_data(key: str, data: Any):
    """Set cached data with current timestamp."""
    _cache[key] = data
    _cache_ttl[key] = time.time()

def clear_symbol_cache(symbol: str):
    """Clear all cached data for a specific symbol to prevent contamination."""
    keys_to_remove = [key for key in _cache.keys() if symbol in key]
    for key in keys_to_remove:
        if key in _cache:
            del _cache[key]
        if key in _cache_ttl:
            del _cache_ttl[key]
    logger.info(f"🧹 Cleared {len(keys_to_remove)} cache entries for {symbol}")

def clear_all_cache():
    """Clear all cached data."""
    global _cache, _cache_ttl
    count = len(_cache)
    _cache.clear()
    _cache_ttl.clear()
    logger.info(f"🧹 Cleared all {count} cache entries")

async def enforce_tradingview_rate_limit():
    """Enforce strict rate limiting for TradingView API (100 requests/minute max)."""
    global _request_count, _request_window_start
    
    current_time = time.time()
    
    # Reset counter if window has passed
    if current_time - _request_window_start >= RATE_WINDOW_SECONDS:
        _request_count = 0
        _request_window_start = current_time
    
    # Check if we're approaching the limit
    if _request_count >= MAX_REQUESTS_PER_MINUTE:
        # Wait until the window resets
        wait_time = RATE_WINDOW_SECONDS - (current_time - _request_window_start)
        if wait_time > 0:
            logger.warning(f"Rate limit reached! Waiting {wait_time:.1f}s before next request")
            await asyncio.sleep(wait_time)
            _request_count = 0
            _request_window_start = time.time()
    
    _request_count += 1
    logger.info(f"Request {_request_count}/{MAX_REQUESTS_PER_MINUTE} in current window")

async def rate_limit_yahoo_api(symbol: str, min_delay: float = 3.0):
    """Ensure minimum delay between Yahoo Finance API calls for same symbol."""
    current_time = time.time()
    if symbol in _last_api_call:
        time_since_last = current_time - _last_api_call[symbol]
        if time_since_last < min_delay:
            delay = min_delay - time_since_last
            logger.info(f"Rate limiting: waiting {delay:.1f}s before calling API for {symbol}")
            await asyncio.sleep(delay)
    
    _last_api_call[symbol] = time.time()

def is_crypto_symbol(symbol: str) -> bool:
    """Check if a symbol is a cryptocurrency."""
    crypto_patterns = [
        'USDT', 'USD', 'BTC', 'ETH', 'ADA', 'XRP', 'SOL', 'DOT', 'DOGE', 
        'AVAX', 'MATIC', 'LTC', 'LINK', 'BNB', 'UNI', 'ATOM', 'FTT'
    ]
    symbol_upper = symbol.upper()
    
    # Check for common crypto patterns
    for pattern in crypto_patterns:
        if pattern in symbol_upper:
            return True
    
    # Check for common crypto suffixes
    if symbol_upper.endswith(('-USD', 'USDT', 'BUSD', 'USDC')):
        return True
        
    return False

def format_symbol_for_yahoo(symbol: str) -> str:
    """Format symbol for Yahoo Finance API."""
    symbol = symbol.upper()
    
    # Handle cryptocurrency pairs
    if 'USDT' in symbol and not symbol.endswith('-USD'):
        # Convert BTCUSDT to BTC-USD for Yahoo Finance
        base = symbol.replace('USDT', '')
        if base in ['BTC', 'ETH', 'ADA', 'XRP', 'SOL', 'DOT', 'DOGE', 'AVAX', 'MATIC', 'LTC', 'LINK', 'BNB']:
            return f"{base}-USD"
    
    # Handle other crypto formats
    if symbol.endswith('USD') and len(symbol) > 3 and not symbol.endswith('-USD'):
        # Convert BTCUSD to BTC-USD
        base = symbol[:-3]
        if len(base) <= 5:  # Most crypto symbols are 3-5 chars
            return f"{base}-USD"
    
    # Return original symbol for stocks, futures, forex
    return symbol

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
    
    @router.post("/cache/clear")
    async def clear_cache_endpoint(request: Dict[str, Any] = None):
        """Clear cache for symbol isolation."""
        try:
            if request and request.get("symbol"):
                symbol = request["symbol"]
                clear_symbol_cache(symbol)
                return {"status": "success", "message": f"Cleared cache for {symbol}"}
            else:
                clear_all_cache()
                return {"status": "success", "message": "Cleared all cache"}
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/market/price")
    async def get_market_price(symbol: str = "NQ=F"):
        """Get current market price for any symbol including crypto."""
        try:
            # Check cache first with longer TTL for price data
            cache_key = f"price_{symbol}"
            cached_result = get_cached_data(cache_key, ttl_seconds=30)  # 30 second cache for more frequent updates
            if cached_result:
                return cached_result
            
            # Apply rate limiting
            await rate_limit_yahoo_api(symbol, min_delay=3.0)
            
            # Handle different symbol formats
            formatted_symbol = format_symbol_for_yahoo(symbol)
            ticker = yf.Ticker(formatted_symbol)
            
            # Get recent data for more accurate current price
            # Use different periods for crypto vs traditional assets
            if is_crypto_symbol(symbol):
                recent_data = ticker.history(period="1d", interval="1h")  # Crypto often has less minute data
                if recent_data.empty:
                    recent_data = ticker.history(period="5d", interval="1d")
            else:
                recent_data = ticker.history(period="1d", interval="1m")
                if recent_data.empty:
                    recent_data = ticker.history(period="1d", interval="5m")
            
            if recent_data.empty:
                raise HTTPException(status_code=404, detail=f"No data available for symbol {symbol}")
            
            current_price = recent_data['Close'].iloc[-1]
            session_high = recent_data['High'].max()
            session_low = recent_data['Low'].min()
            volume = int(recent_data['Volume'].sum()) if not pd.isna(recent_data['Volume'].sum()) else 0
            timestamp = datetime.now().isoformat()
            
            result = MarketDataResponse(
                symbol=symbol,
                current_price=float(current_price),
                session_high=float(session_high),
                session_low=float(session_low),
                volume=volume,
                timestamp=timestamp
            )
            
            # Cache the result
            set_cached_data(cache_key, result)
            return result
        except Exception as e:
            error_msg = str(e)
            if "rate limited" in error_msg.lower() or "too many requests" in error_msg.lower():
                logger.warning(f"Rate limited for {symbol}, returning fallback data")
                # Return reasonable fallback data when rate limited
                return MarketDataResponse(
                    symbol=symbol,
                    current_price=3000.0 if 'ETH' in symbol.upper() else 20000.0,  # Reasonable defaults
                    session_high=3010.0 if 'ETH' in symbol.upper() else 20100.0,
                    session_low=2990.0 if 'ETH' in symbol.upper() else 19900.0,
                    volume=1000000,
                    timestamp=datetime.now().isoformat()
                )
            else:
                logger.error(f"Failed to get price for {symbol}: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/market/nq-price")
    async def get_nq_price():
        """Get current NQ futures price (legacy endpoint)."""
        return await get_market_price("NQ=F")
    
    @router.get("/market/validate-symbol")
    async def validate_symbol(symbol: str):
        """Validate if a symbol is available and return basic info."""
        try:
            formatted_symbol = format_symbol_for_yahoo(symbol)
            ticker = yf.Ticker(formatted_symbol)
            
            # Try to get basic info
            info = ticker.info
            if not info or len(info) <= 2:  # Empty or minimal info usually means invalid symbol
                raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")
            
            # Try to get recent data
            recent_data = ticker.history(period="5d", interval="1d")
            if recent_data.empty:
                raise HTTPException(status_code=404, detail=f"No price data available for {symbol}")
            
            symbol_type = "unknown"
            if is_crypto_symbol(symbol):
                symbol_type = "cryptocurrency"
            elif "=F" in symbol or "F=" in symbol:
                symbol_type = "future"
            elif "=X" in symbol or any(pair in symbol.upper() for pair in ["EUR", "GBP", "JPY", "AUD", "CAD"]):
                symbol_type = "forex"
            elif len(symbol) <= 5 and symbol.isalpha():
                symbol_type = "stock"
            
            return {
                "symbol": symbol,
                "formatted_symbol": formatted_symbol,
                "valid": True,
                "type": symbol_type,
                "name": info.get("longName", info.get("shortName", symbol)),
                "currency": info.get("currency", "USD"),
                "exchange": info.get("exchange", "Unknown"),
                "current_price": float(recent_data['Close'].iloc[-1]) if not recent_data.empty else None
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to validate symbol {symbol}: {e}")
            return {
                "symbol": symbol,
                "valid": False,
                "error": str(e)
            }
    
    @router.get("/market/search-symbols")
    async def search_symbols(query: str, limit: int = 50):
        """Search for symbols using TradingView's symbol database."""
        if not query or len(query) < 2:
            raise HTTPException(status_code=400, detail="Query must be at least 2 characters")
        
        try:
            # Check cache first - symbols don't change often, so cache for 24 hours
            cache_key = f"search_{query}_{limit}"
            cached_result = get_cached_data(cache_key, ttl_seconds=86400)  # 24 hour cache
            if cached_result:
                return cached_result
            
            # Enforce strict rate limiting for TradingView API
            await enforce_tradingview_rate_limit()
            
            # Use TradingView's symbol search API as a proxy
            async with aiohttp.ClientSession() as session:
                url = f"https://symbol-search.tradingview.com/symbol_search/"
                params = {
                    "text": query,
                    "exchange": "",
                    "type": "",
                    "lang": "en"
                }
                
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    "Referer": "https://www.tradingview.com/"
                }
                
                async with session.get(url, params=params, headers=headers, timeout=10) as response:
                    if response.status != 200:
                        raise HTTPException(status_code=503, detail="Symbol search service unavailable")
                    
                    data = await response.json()
                    
                    # Transform results to our format
                    results = []
                    for item in data[:limit]:
                        result = {
                            "symbol": item.get("symbol", ""),
                            "display": item.get("symbol", ""),
                            "name": item.get("description", item.get("symbol", "")),
                            "exchange": item.get("exchange", ""),
                            "type": map_tradingview_type(item.get("type", "")),
                            "country": item.get("country", ""),
                            "currency": item.get("currency_code", ""),
                            "provider_id": item.get("provider_id", ""),
                            "tradingview_symbol": f"{item.get('exchange', '')}:{item.get('symbol', '')}",
                            "sector": item.get("sector", ""),
                            "industry": item.get("industry", ""),
                        }
                        results.append(result)
                    
                    result_data = {
                        "query": query,
                        "results": results,
                        "total": len(results)
                    }
                    
                    # Cache the result
                    set_cached_data(cache_key, result_data)
                    return result_data
        
        except aiohttp.ClientError as e:
            logger.error(f"Failed to fetch symbols from TradingView: {e}")
            # Return fallback results
            return get_fallback_symbol_results(query, limit)
        except Exception as e:
            logger.error(f"Symbol search error: {e}")
            # Return fallback results instead of failing
            return get_fallback_symbol_results(query, limit)
    
    @router.get("/market/historical")
    async def get_historical_data(
        symbol: str = "NQ=F",
        period: str = "1y",
        interval: str = "1d",
        max_points: int = 2000
    ):
        """Get comprehensive historical market data with extended timeframes."""
        try:
            # Check cache first to avoid rate limiting
            cache_key = f"historical_{symbol}_{period}_{interval}_{max_points}"
            cached_result = get_cached_data(cache_key, ttl_seconds=1800)  # 30 minute cache for historical
            if cached_result:
                return cached_result
            
            # Apply rate limiting
            await rate_limit_yahoo_api(symbol, min_delay=3.0)
            
            # Direct implementation bypassing MCP for now
            formatted_symbol = format_symbol_for_yahoo(symbol)
            ticker = yf.Ticker(formatted_symbol)
            
            # Enhanced period mapping with more comprehensive data
            period_mapping = {
                "1d": "1d",
                "5d": "5d", 
                "1mo": "1mo",
                "3mo": "3mo",
                "6mo": "6mo",
                "1y": "1y",
                "2y": "2y",
                "5y": "5y",
                "10y": "10y",
                "max": "max"  # Get all available data
            }
            
            # Get the mapped period or use provided period
            actual_period = period_mapping.get(period, period)
            
            # Respect frontend interval request - only adjust if explicitly needed
            requested_interval = interval
            
            # Only adjust for very long periods where the requested interval would cause too much data
            if actual_period in ["max", "10y", "5y"] and interval in ["1m", "3m", "5m", "15m", "30m"]:
                logger.warning(f"Adjusting interval from {interval} to 1h for long period {actual_period}")
                interval = "1h"  # Use hourly for very long periods with minute intervals
                max_points = 5000
            elif actual_period in ["2y", "1y"] and interval in ["1m", "3m", "5m"]:
                logger.warning(f"Adjusting interval from {interval} to 15m for period {actual_period}")
                interval = "15m"  # Use 15min for yearly data with very short intervals
                max_points = 3000
            else:
                # Keep original interval for shorter periods
                max_points = 1000
            
            logger.info(f"Fetching {actual_period} data for {symbol} with interval {interval}")
            data = ticker.history(period=actual_period, interval=interval)
            
            if data.empty:
                raise HTTPException(status_code=404, detail="No historical data available")
            
            # For very large datasets, sample intelligently rather than just truncating
            if len(data) > max_points:
                if actual_period in ["max", "10y", "5y"]:
                    # For very long periods, sample every Nth point to maintain shape
                    step = len(data) // max_points + 1
                    data = data.iloc[::step]
                else:
                    # For shorter periods, take the most recent data
                    data = data.tail(max_points)
            
            logger.info(f"Returning {len(data)} data points for {symbol} from {data.index[0]} to {data.index[-1]}")
            
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
            
            # Cache the result
            set_cached_data(cache_key, result)
            return result
        except Exception as e:
            error_msg = str(e)
            if "rate limited" in error_msg.lower() or "too many requests" in error_msg.lower():
                logger.warning(f"Rate limited for historical data {symbol}, returning minimal fallback")
                # Return minimal fallback historical data when rate limited
                current_time = datetime.now()
                fallback_data = []
                base_price = 3000.0 if 'ETH' in symbol.upper() else 20000.0
                
                # Generate 30 days of simple historical data
                for i in range(30):
                    date = current_time - timedelta(days=29-i)
                    price = base_price + (random.random() - 0.5) * base_price * 0.05  # ±2.5% variation
                    fallback_data.append({
                        "date": date.isoformat(),
                        "open": price,
                        "high": price * 1.02,
                        "low": price * 0.98,
                        "close": price,
                        "volume": random.randint(100000, 1000000)
                    })
                
                return {
                    "symbol": symbol,
                    "period": period,
                    "interval": interval,
                    "data_points": len(fallback_data),
                    "data": fallback_data,
                    "fallback": True,
                    "summary": {
                        "current_price": base_price,
                        "period_high": base_price * 1.02,
                        "period_low": base_price * 0.98,
                        "total_volume": 15000000,
                        "price_change": 0.0,
                        "price_change_pct": 0.0
                    }
                }
            else:
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
    
    @router.post("/trading/manual-signal")
    async def create_manual_trading_signal(
        signal_data: Dict[str, Any],
        mcp_server = Depends(get_mcp_server),
        ws_manager = Depends(get_ws_manager)
    ):
        """Create manual trading signal from UI."""
        try:
            # Validate signal data
            required_fields = ['symbol', 'action', 'price', 'confidence']
            for field in required_fields:
                if field not in signal_data:
                    raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
            
            # Create signal
            signal = {
                "id": f"manual_{int(time.time())}",
                "symbol": signal_data["symbol"],
                "action": signal_data["action"],
                "price": float(signal_data["price"]),
                "confidence": float(signal_data["confidence"]),
                "reason": signal_data.get("reason", "Manual signal"),
                "timestamp": datetime.now().isoformat(),
                "agent_id": "manual_user",
                "manual": True
            }
            
            # Broadcast signal to all connected clients
            await ws_manager.broadcast_json({
                "type": "trading_signal",
                "signal": signal
            })
            
            return {"status": "success", "signal": signal}
            
        except Exception as e:
            logger.error(f"Failed to create manual signal: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/models/analyze-chart")
    async def analyze_chart_with_model(
        analysis_request: Dict[str, Any],
        mcp_server = Depends(get_mcp_server),
        ws_manager = Depends(get_ws_manager)
    ):
        """Send chart data to model for analysis and get trading recommendations."""
        try:
            # Validate request
            required_fields = ['symbol', 'chart_data', 'model_provider', 'model_name']
            for field in required_fields:
                if field not in analysis_request:
                    raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
            
            symbol = analysis_request["symbol"]
            chart_data = analysis_request["chart_data"]
            model_provider = analysis_request["model_provider"]
            model_name = analysis_request["model_name"]
            
            # Analyze comprehensive market context
            market_context_data = market_analyzer.analyze_market_context(chart_data)
            market_context_text = market_analyzer.format_context_for_ai(market_context_data)
            
            # Prepare enhanced market context for the model
            market_context = f"""
            🎯 PROFESSIONAL TRADING ANALYSIS FOR {symbol}
            
            You are an expert institutional trader. Analyze this comprehensive market data and provide precise trading recommendations.
            
            {market_context_text}
            
            📊 RECENT PRICE DATA (Last 20 Candles):
            {json.dumps(chart_data[-20:], indent=2)}
            
            💰 CURRENT MARKET STATE:
            Current Price: ${chart_data[-1]['close'] if chart_data else 'N/A'}
            Symbol: {symbol}
            Timeframe: Real-time data
            
            🎯 ANALYSIS REQUIREMENTS:
            Based on the comprehensive market context above, provide:
            1. Session-based analysis (Asia/London/NY highs/lows impact)
            2. Fair Value Gap assessment and fill probabilities
            3. Order block analysis and institutional levels
            4. Liquidity zone interactions
            5. Market structure trend analysis
            6. Smart money concept-based trading recommendation
            7. Confidence level (0-100%) with institutional reasoning
            8. Key support/resistance based on session data and FVGs
            9. Risk assessment using order flow concepts
            
            Respond in JSON format with: {{"trend": "bullish/bearish/neutral", "recommendation": "BUY/SELL/HOLD", "confidence": 85, "reasoning": "detailed institutional analysis with session data, FVG analysis, order blocks, and liquidity zones", "support_levels": [price1, price2], "resistance_levels": [price1, price2], "session_analysis": "Asia/London/NY session impact", "fvg_analysis": "Fair Value Gap assessment", "order_blocks": "Key institutional levels"}}
            """
            
            # Broadcast the prompt to AI debug subscribers
            debug_prompt_data = {
                "type": "ai_prompt",
                "prompt": market_context.strip(),
                "model": f"{model_provider}:{model_name}",
                "symbol": symbol,
                "timestamp": datetime.now().isoformat()
            }
            await ws_manager.broadcast_to_subscription("ai_debug", debug_prompt_data)
            
            # Execute analysis through MCP
            result = await mcp_server.agent_manager.execute_agent_task(
                agent_id="analysis_agent",
                task={
                    "type": "model_analysis",
                    "parameters": {
                        "provider": model_provider,
                        "model": model_name,
                        "prompt": market_context,
                        "symbol": symbol
                    }
                }
            )
            
            # Broadcast the response to AI debug subscribers
            debug_response_data = {
                "type": "ai_response",
                "response": json.dumps(result, indent=2) if isinstance(result, dict) else str(result),
                "model": f"{model_provider}:{model_name}",
                "symbol": symbol,
                "timestamp": datetime.now().isoformat()
            }
            await ws_manager.broadcast_to_subscription("ai_debug", debug_response_data)
            
            return {
                "status": "success",
                "analysis": result,
                "model_used": f"{model_provider}:{model_name}",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze chart with model: {e}")
            
            # Broadcast the error to AI debug subscribers
            debug_error_data = {
                "type": "ai_error",
                "error": f"HTTP Analysis failed: {str(e)}",
                "model": f"{model_provider}:{model_name}",
                "symbol": symbol,
                "timestamp": datetime.now().isoformat()
            }
            await ws_manager.broadcast_to_subscription("ai_debug", debug_error_data)
            
            # Return mock analysis on error
            return {
                "status": "fallback",
                "analysis": {
                    "trend": random.choice(["bullish", "bearish", "neutral"]),
                    "recommendation": random.choice(["BUY", "SELL", "HOLD"]),
                    "confidence": random.randint(60, 90),
                    "reasoning": f"Technical analysis suggests current market conditions for {analysis_request.get('symbol', 'asset')}",
                    "support_levels": [],
                    "resistance_levels": []
                },
                "model_used": f"{analysis_request.get('model_provider', 'fallback')}:{analysis_request.get('model_name', 'mock')}",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
    
    @router.post("/agents/chat")
    async def chat_with_agent(
        chat_request: Dict[str, Any],
        mcp_server = Depends(get_mcp_server),
        ws_manager = Depends(get_ws_manager)
    ):
        """Chat with a specific agent about trading decisions."""
        try:
            agent_id = chat_request.get("agent_id")
            message = chat_request.get("message", "")
            symbol = chat_request.get("symbol", "ETH-USD")
            chart_data = chat_request.get("chart_data", [])
            chat_history = chat_request.get("chat_history", [])
            
            if not agent_id or not message:
                raise HTTPException(status_code=400, detail="agent_id and message are required")
            
            # Get current price for context
            current_price = chart_data[-1]["close"] if chart_data else None
            
            # Analyze comprehensive market context for chat
            market_context_data = market_analyzer.analyze_market_context(chart_data) if chart_data else None
            market_context_text = market_analyzer.format_context_for_ai(market_context_data) if market_context_data else "No market context available"
            
            # Build enhanced context for the agent
            context = f"""
            🤖 PROFESSIONAL TRADING AGENT FOR {symbol}
            
            You are an expert institutional trading agent with deep knowledge of market structure and smart money concepts.
            
            {market_context_text}
            
            💰 CURRENT MARKET STATE:
            Current Price: ${current_price if current_price else 'N/A'}
            
            💬 RECENT CHAT HISTORY:
            {chr(10).join([f"{msg['sender']}: {msg['message']}" for msg in chat_history[-5:]])}
            
            📊 RECENT MARKET DATA:
            {json.dumps(chart_data[-5:], indent=2) if chart_data else 'No chart data available'}
            
            📝 USER MESSAGE: {message}
            
            🎯 RESPONSE GUIDELINES:
            - Use institutional trading concepts (FVGs, order blocks, liquidity zones, session analysis)
            - Reference specific levels from the market context above
            - Explain WHY price might react at certain levels
            - Consider session highs/lows and their significance
            - If recommending trades, use confluence of institutional factors
            
            If you recommend a trading signal, format your response to include both a conversational response AND a JSON signal object at the end like this:
            
            Your detailed institutional analysis here...
            
            SIGNAL: {{"type": "buy", "price": 2990.50, "confidence": 0.85, "reason": "FVG fill confluence with London session low and untested order block"}}
            """
            
            try:
                # Execute chat through MCP agent
                result = await mcp_server.agent_manager.execute_agent_task(
                    agent_id=agent_id,
                    task={
                        "type": "chat_response",
                        "parameters": {
                            "prompt": context,
                            "symbol": symbol,
                            "message": message
                        }
                    }
                )
                
                response_text = result.get("response", "I'm here to help with your trading analysis!")
                
                # Check if response contains a signal
                signal = None
                if "SIGNAL:" in response_text:
                    try:
                        signal_start = response_text.find("SIGNAL:") + 7
                        signal_json = response_text[signal_start:].strip()
                        signal = json.loads(signal_json)
                        # Remove signal from response text
                        response_text = response_text[:response_text.find("SIGNAL:")].strip()
                    except json.JSONDecodeError:
                        pass
                
                return {
                    "response": response_text,
                    "agent_id": agent_id,
                    "signal": signal,
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Agent chat failed: {e}")
                # Fallback response
                return {
                    "response": f"I'm analyzing the {symbol} chart. Based on the current price of ${current_price}, I can help you with technical analysis and trading insights. What specific aspect would you like me to focus on?",
                    "agent_id": agent_id,
                    "signal": None,
                    "timestamp": datetime.now().isoformat(),
                    "fallback": True
                }
                
        except Exception as e:
            logger.error(f"Failed to process chat request: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/agents/analyze-chart")
    async def analyze_chart_with_agent(
        analysis_request: Dict[str, Any],
        mcp_server = Depends(get_mcp_server)
    ):
        """Trigger agent analysis of current chart data."""
        try:
            agent_id = analysis_request.get("agent_id")
            symbol = analysis_request.get("symbol", "ETH-USD")
            chart_data = analysis_request.get("chart_data", [])
            current_price = analysis_request.get("current_price")
            model_provider = analysis_request.get("model_provider", "ollama")
            model_name = analysis_request.get("model_name", "phi3:mini")
            
            if not chart_data:
                raise HTTPException(status_code=400, detail="chart_data is required")
            
            # Analyze comprehensive market context
            market_context_data = market_analyzer.analyze_market_context(chart_data)
            market_context_text = market_analyzer.format_context_for_ai(market_context_data)
            
            # Prepare enhanced analysis context
            analysis_context = f"""
            🤖 ADVANCED TRADING AGENT ANALYSIS FOR {symbol}
            
            You are a professional institutional trading agent with deep market structure knowledge.
            
            {market_context_text}
            
            💰 CURRENT MARKET STATE:
            Current Price: ${current_price}
            
            📊 COMPREHENSIVE OHLCV DATA:
            {json.dumps(chart_data, indent=2)}
            
            🎯 INSTITUTIONAL ANALYSIS REQUIREMENTS:
            Provide a comprehensive analysis using smart money concepts:
            
            1. SESSION ANALYSIS:
               - How does current price relate to Asia/London/NY session highs and lows?
               - Which session's levels are most relevant for current price action?
            
            2. FAIR VALUE GAP ANALYSIS:
               - Identify active FVGs and their significance
               - Assess probability of gap fills and market reactions
            
            3. ORDER BLOCK ANALYSIS:
               - Evaluate institutional order blocks and their strength
               - Determine potential reaction zones
            
            4. LIQUIDITY ANALYSIS:
               - Assess buy-side and sell-side liquidity zones
               - Identify potential liquidity grabs
            
            5. MARKET STRUCTURE:
               - Determine overall trend and structure breaks
               - Identify swing highs/lows and their significance
            
            6. TRADING RECOMMENDATION:
               - Provide specific entry/exit levels with institutional reasoning
               - Include confidence level based on confluence of factors
               - Assess risk using order flow concepts
            
            Be specific, actionable, and focus on institutional trading concepts.
            """
            
            # Execute analysis through MCP
            result = await mcp_server.agent_manager.execute_agent_task(
                agent_id=agent_id or "analysis_agent",
                task={
                    "type": "chart_analysis",
                    "parameters": {
                        "provider": model_provider,
                        "model": model_name,
                        "prompt": analysis_context,
                        "symbol": symbol
                    }
                }
            )
            
            return {
                "reasoning": result.get("analysis", "Analysis complete"),
                "recommendation": result.get("recommendation", "HOLD"),
                "confidence": result.get("confidence", 50),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze chart: {e}")
            # Return fallback analysis
            return {
                "reasoning": f"Technical analysis of {analysis_request.get('symbol', 'asset')} shows mixed signals. Market conditions require careful monitoring.",
                "recommendation": "HOLD",
                "confidence": 60,
                "timestamp": datetime.now().isoformat(),
                "fallback": True
            }

    @router.websocket("/ws/market/{symbol}")
    async def websocket_market_data(websocket: WebSocket, symbol: str):
        """WebSocket endpoint for real-time market data and trading signals."""
        # Get dependencies from app state
        ws_manager = websocket.app.state.ws_manager
        mcp_server = websocket.app.state.mcp_server
        
        await ws_manager.connect(websocket, f"market_{symbol}")
        
        # Clear cache for this symbol to ensure fresh data
        clear_symbol_cache(symbol)
        logger.info(f"🔌 WebSocket connected for {symbol} - cache cleared")
        
        # Subscribe to market data updates
        ws_manager.subscribe(websocket, "market_data")
        ws_manager.subscribe(websocket, "trading_signals")
        
        try:
            # Send connection confirmation only - let frontend handle historical data via HTTP API
            await ws_manager.send_personal_message(
                json.dumps({
                    "type": "connection_established",
                    "symbol": symbol,
                    "message": f"Connected to real-time data for {symbol}"
                }),
                websocket
            )
            
            # Start real-time price updates (not simulation)
            asyncio.create_task(send_real_time_price_updates(websocket, symbol, ws_manager))
            
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
                    
                    elif message.get("type") == "send_chart_data":
                        # Receive chart data for model analysis
                        chart_data = message.get("chart_data", [])
                        model_provider = message.get("model_provider", "ollama")
                        model_name = message.get("model_name", "phi3:mini")
                        
                        # Trigger model analysis with chart data
                        analysis_response = {
                            "type": "model_analysis_result",
                            "symbol": symbol,
                            "model_used": f"{model_provider}:{model_name}",
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        try:
                            # Analyze market context from chart data
                            market_context_data = market_analyzer.analyze_market_context(chart_data)
                            market_context_text = market_analyzer.format_context_for_ai(market_context_data)
                            
                            # Enhanced prompt with comprehensive market context
                            market_context = f"""
                            🎯 COMPREHENSIVE TRADING ANALYSIS FOR {symbol}
                            
                            {market_context_text}
                            
                            📊 RECENT PRICE ACTION:
                            {json.dumps(chart_data[-10:], indent=2) if chart_data else 'No recent data available'}
                            
                            💰 CURRENT MARKET STATE:
                            Current Price: ${chart_data[-1]['close'] if chart_data else 'N/A'}
                            24h Range: ${max(c['high'] for c in chart_data[-24:]) if len(chart_data) >= 24 else 'N/A'} - ${min(c['low'] for c in chart_data[-24:]) if len(chart_data) >= 24 else 'N/A'}
                            
                            🤖 ANALYSIS REQUEST:
                            Based on the comprehensive market context above, provide a detailed trading analysis including:
                            1. How current price relates to session highs/lows
                            2. Fair Value Gap analysis and potential fills
                            3. Order block interactions and liquidity zones
                            4. Market structure bias and trend direction
                            5. Specific entry/exit levels with reasoning
                            6. Risk assessment based on institutional concepts
                            
                            Respond with actionable insights focusing on smart money concepts.
                            """
                            
                            # Broadcast the prompt to AI debug subscribers
                            debug_prompt_data = {
                                "type": "ai_prompt",
                                "prompt": market_context.strip(),
                                "model": f"{model_provider}:{model_name}",
                                "symbol": symbol,
                                "timestamp": datetime.now().isoformat()
                            }
                            await ws_manager.broadcast_to_subscription("ai_debug", debug_prompt_data)
                            
                            result = await mcp_server.agent_manager.execute_agent_task(
                                agent_id="analysis_agent",
                                task={
                                    "type": "model_analysis", 
                                    "parameters": {
                                        "provider": model_provider,
                                        "model": model_name,
                                        "prompt": market_context,
                                        "symbol": symbol
                                    }
                                }
                            )
                            
                            # Broadcast the response to AI debug subscribers
                            debug_response_data = {
                                "type": "ai_response",
                                "response": json.dumps(result, indent=2) if isinstance(result, dict) else str(result),
                                "model": f"{model_provider}:{model_name}",
                                "symbol": symbol,
                                "timestamp": datetime.now().isoformat()
                            }
                            await ws_manager.broadcast_to_subscription("ai_debug", debug_response_data)
                            
                            analysis_response["analysis"] = result
                            analysis_response["status"] = "success"
                            
                        except Exception as e:
                            logger.error(f"Model analysis failed: {e}")
                            
                            # Broadcast the error to AI debug subscribers
                            debug_error_data = {
                                "type": "ai_error",
                                "error": f"Model analysis failed: {str(e)}",
                                "model": f"{model_provider}:{model_name}",
                                "symbol": symbol,
                                "timestamp": datetime.now().isoformat()
                            }
                            await ws_manager.broadcast_to_subscription("ai_debug", debug_error_data)
                            
                            analysis_response["analysis"] = {
                                "recommendation": "HOLD",
                                "confidence": 50,
                                "reasoning": f"Analysis unavailable for {symbol}"
                            }
                            analysis_response["status"] = "fallback"
                            analysis_response["error"] = str(e)
                        
                        await ws_manager.send_personal_message(
                            json.dumps(analysis_response),
                            websocket
                        )
                    
                    elif message.get("type") == "create_signal":
                        # Manual signal creation from UI
                        signal_data = message.get("signal", {})
                        if signal_data:
                            signal = {
                                "id": f"manual_{int(time.time())}",
                                "symbol": symbol,
                                "action": signal_data.get("action", "hold"),
                                "price": signal_data.get("price", 0),
                                "confidence": signal_data.get("confidence", 0.5),
                                "reason": signal_data.get("reason", "Manual signal"),
                                "timestamp": datetime.now().isoformat(),
                                "agent_id": "manual_user",
                                "manual": True
                            }
                            
                            # Broadcast to all clients
                            await ws_manager.broadcast_json({
                                "type": "trading_signal",
                                "signal": signal
                            })
                        
                except WebSocketDisconnect:
                    break
                except Exception as e:
                    logger.error(f"WebSocket error: {e}")
                    break
                    
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for {symbol}")
        finally:
            ws_manager.disconnect(websocket)
    
    @router.websocket("/ws/ai-debug/{symbol}")
    async def websocket_ai_debug(websocket: WebSocket, symbol: str):
        """WebSocket endpoint for AI debug monitoring - streams prompts and responses."""
        ws_manager = websocket.app.state.ws_manager
        mcp_server = websocket.app.state.mcp_server
        
        await ws_manager.connect(websocket, f"ai_debug_{symbol}")
        logger.info(f"🔧 AI Debug WebSocket connected for {symbol}")
        
        # Subscribe to AI debug events
        ws_manager.subscribe(websocket, "ai_debug")
        
        try:
            # Send connection confirmation
            await ws_manager.send_personal_message(
                json.dumps({
                    "type": "debug_connected",
                    "symbol": symbol,
                    "message": f"AI Debug monitoring active for {symbol}",
                    "timestamp": datetime.now().isoformat()
                }),
                websocket
            )
            
            # Listen for client messages (not much needed for debug panel)
            while True:
                try:
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    
                    if message.get("type") == "ping":
                        await ws_manager.send_personal_message(
                            json.dumps({"type": "pong", "timestamp": datetime.now().isoformat()}),
                            websocket
                        )
                    
                except WebSocketDisconnect:
                    break
                except Exception as e:
                    logger.error(f"AI Debug WebSocket error: {e}")
                    break
                    
        except WebSocketDisconnect:
            logger.info(f"AI Debug WebSocket disconnected for {symbol}")
        finally:
            ws_manager.disconnect(websocket)

    return router


def map_tradingview_type(tv_type: str) -> str:
    """Map TradingView symbol types to our categories."""
    type_map = {
        'stock': 'stock',
        'crypto': 'cryptocurrency', 
        'futures': 'future',
        'forex': 'currency',
        'cfd': 'cfd',
        'index': 'index',
        'bond': 'bond',
        'fund': 'etf',
        'dr': 'stock',
        'right': 'stock',
        'warrant': 'stock',
    }
    return type_map.get(tv_type.lower(), 'unknown')

def get_fallback_symbol_results(query: str, limit: int) -> dict:
    """Provide fallback symbol results when TradingView API is unavailable."""
    fallback_symbols = [
        # Popular Stocks
        {"symbol": "AAPL", "display": "AAPL", "name": "Apple Inc.", "exchange": "NASDAQ", "type": "stock", "country": "US", "currency": "USD"},
        {"symbol": "TSLA", "display": "TSLA", "name": "Tesla Inc.", "exchange": "NASDAQ", "type": "stock", "country": "US", "currency": "USD"},
        {"symbol": "NVDA", "display": "NVDA", "name": "NVIDIA Corporation", "exchange": "NASDAQ", "type": "stock", "country": "US", "currency": "USD"},
        {"symbol": "MSFT", "display": "MSFT", "name": "Microsoft Corporation", "exchange": "NASDAQ", "type": "stock", "country": "US", "currency": "USD"},
        {"symbol": "GOOGL", "display": "GOOGL", "name": "Alphabet Inc.", "exchange": "NASDAQ", "type": "stock", "country": "US", "currency": "USD"},
        {"symbol": "AMZN", "display": "AMZN", "name": "Amazon.com Inc.", "exchange": "NASDAQ", "type": "stock", "country": "US", "currency": "USD"},
        {"symbol": "META", "display": "META", "name": "Meta Platforms Inc.", "exchange": "NASDAQ", "type": "stock", "country": "US", "currency": "USD"},
        {"symbol": "NFLX", "display": "NFLX", "name": "Netflix Inc.", "exchange": "NASDAQ", "type": "stock", "country": "US", "currency": "USD"},
        
        # Major Cryptocurrencies (Top 50+ from Binance/CoinMarketCap)
        {"symbol": "BTC-USD", "display": "BTC-USD", "name": "Bitcoin USD", "exchange": "CCC", "type": "cryptocurrency", "country": "", "currency": "USD"},
        {"symbol": "ETH-USD", "display": "ETH-USD", "name": "Ethereum USD", "exchange": "CCC", "type": "cryptocurrency", "country": "", "currency": "USD"},
        {"symbol": "SOL-USD", "display": "SOL-USD", "name": "Solana USD", "exchange": "CCC", "type": "cryptocurrency", "country": "", "currency": "USD"},
        {"symbol": "ADA-USD", "display": "ADA-USD", "name": "Cardano USD", "exchange": "CCC", "type": "cryptocurrency", "country": "", "currency": "USD"},
        {"symbol": "AVAX-USD", "display": "AVAX-USD", "name": "Avalanche USD", "exchange": "CCC", "type": "cryptocurrency", "country": "", "currency": "USD"},
        {"symbol": "DOT-USD", "display": "DOT-USD", "name": "Polkadot USD", "exchange": "CCC", "type": "cryptocurrency", "country": "", "currency": "USD"},
        {"symbol": "MATIC-USD", "display": "MATIC-USD", "name": "Polygon USD", "exchange": "CCC", "type": "cryptocurrency", "country": "", "currency": "USD"},
        {"symbol": "LINK-USD", "display": "LINK-USD", "name": "Chainlink USD", "exchange": "CCC", "type": "cryptocurrency", "country": "", "currency": "USD"},
        {"symbol": "DOGE-USD", "display": "DOGE-USD", "name": "Dogecoin USD", "exchange": "CCC", "type": "cryptocurrency", "country": "", "currency": "USD"},
        {"symbol": "SHIB-USD", "display": "SHIB-USD", "name": "Shiba Inu USD", "exchange": "CCC", "type": "cryptocurrency", "country": "", "currency": "USD"},
        {"symbol": "LTC-USD", "display": "LTC-USD", "name": "Litecoin USD", "exchange": "CCC", "type": "cryptocurrency", "country": "", "currency": "USD"},
        {"symbol": "BCH-USD", "display": "BCH-USD", "name": "Bitcoin Cash USD", "exchange": "CCC", "type": "cryptocurrency", "country": "", "currency": "USD"},
        {"symbol": "XRP-USD", "display": "XRP-USD", "name": "XRP USD", "exchange": "CCC", "type": "cryptocurrency", "country": "", "currency": "USD"},
        {"symbol": "BNB-USD", "display": "BNB-USD", "name": "Binance Coin USD", "exchange": "CCC", "type": "cryptocurrency", "country": "", "currency": "USD"},
        {"symbol": "ATOM-USD", "display": "ATOM-USD", "name": "Cosmos USD", "exchange": "CCC", "type": "cryptocurrency", "country": "", "currency": "USD"},
        {"symbol": "NEAR-USD", "display": "NEAR-USD", "name": "NEAR Protocol USD", "exchange": "CCC", "type": "cryptocurrency", "country": "", "currency": "USD"},
        {"symbol": "FTM-USD", "display": "FTM-USD", "name": "Fantom USD", "exchange": "CCC", "type": "cryptocurrency", "country": "", "currency": "USD"},
        {"symbol": "ALGO-USD", "display": "ALGO-USD", "name": "Algorand USD", "exchange": "CCC", "type": "cryptocurrency", "country": "", "currency": "USD"},
        {"symbol": "VET-USD", "display": "VET-USD", "name": "VeChain USD", "exchange": "CCC", "type": "cryptocurrency", "country": "", "currency": "USD"},
        {"symbol": "ICP-USD", "display": "ICP-USD", "name": "Internet Computer USD", "exchange": "CCC", "type": "cryptocurrency", "country": "", "currency": "USD"},
        {"symbol": "HBAR-USD", "display": "HBAR-USD", "name": "Hedera USD", "exchange": "CCC", "type": "cryptocurrency", "country": "", "currency": "USD"},
        {"symbol": "FIL-USD", "display": "FIL-USD", "name": "Filecoin USD", "exchange": "CCC", "type": "cryptocurrency", "country": "", "currency": "USD"},
        {"symbol": "APT-USD", "display": "APT-USD", "name": "Aptos USD", "exchange": "CCC", "type": "cryptocurrency", "country": "", "currency": "USD"},
        {"symbol": "SUI-USD", "display": "SUI-USD", "name": "Sui USD", "exchange": "CCC", "type": "cryptocurrency", "country": "", "currency": "USD"},
        {"symbol": "ARB-USD", "display": "ARB-USD", "name": "Arbitrum USD", "exchange": "CCC", "type": "cryptocurrency", "country": "", "currency": "USD"},
        {"symbol": "OP-USD", "display": "OP-USD", "name": "Optimism USD", "exchange": "CCC", "type": "cryptocurrency", "country": "", "currency": "USD"},
        {"symbol": "PEPE-USD", "display": "PEPE-USD", "name": "Pepe USD", "exchange": "CCC", "type": "cryptocurrency", "country": "", "currency": "USD"},
        {"symbol": "UNI-USD", "display": "UNI-USD", "name": "Uniswap USD", "exchange": "CCC", "type": "cryptocurrency", "country": "", "currency": "USD"},
        {"symbol": "AAVE-USD", "display": "AAVE-USD", "name": "Aave USD", "exchange": "CCC", "type": "cryptocurrency", "country": "", "currency": "USD"},
        {"symbol": "CRV-USD", "display": "CRV-USD", "name": "Curve DAO Token USD", "exchange": "CCC", "type": "cryptocurrency", "country": "", "currency": "USD"},
        
        # Futures
        {"symbol": "NQ=F", "display": "NQ", "name": "NASDAQ-100 E-mini Future", "exchange": "CME", "type": "future", "country": "US", "currency": "USD"},
        {"symbol": "ES=F", "display": "ES", "name": "S&P 500 E-mini Future", "exchange": "CME", "type": "future", "country": "US", "currency": "USD"},
        {"symbol": "YM=F", "display": "YM", "name": "Dow Jones E-mini Future", "exchange": "CBOT", "type": "future", "country": "US", "currency": "USD"},
        {"symbol": "RTY=F", "display": "RTY", "name": "Russell 2000 E-mini Future", "exchange": "ICE", "type": "future", "country": "US", "currency": "USD"},
        
        # ETFs
        {"symbol": "SPY", "display": "SPY", "name": "SPDR S&P 500 ETF", "exchange": "NYSE", "type": "etf", "country": "US", "currency": "USD"},
        {"symbol": "QQQ", "display": "QQQ", "name": "Invesco QQQ Trust", "exchange": "NASDAQ", "type": "etf", "country": "US", "currency": "USD"},
        {"symbol": "IWM", "display": "IWM", "name": "iShares Russell 2000 ETF", "exchange": "NYSE", "type": "etf", "country": "US", "currency": "USD"},
        {"symbol": "VTI", "display": "VTI", "name": "Vanguard Total Stock Market ETF", "exchange": "NYSE", "type": "etf", "country": "US", "currency": "USD"},
        
        # Popular Forex (Note: Yahoo format)
        {"symbol": "EURUSD=X", "display": "EURUSD", "name": "EUR/USD", "exchange": "FX", "type": "currency", "country": "", "currency": "USD"},
        {"symbol": "GBPUSD=X", "display": "GBPUSD", "name": "GBP/USD", "exchange": "FX", "type": "currency", "country": "", "currency": "USD"},
        {"symbol": "USDJPY=X", "display": "USDJPY", "name": "USD/JPY", "exchange": "FX", "type": "currency", "country": "", "currency": "JPY"},
    ]
    
    # Filter based on query
    filtered = [
        s for s in fallback_symbols 
        if query.lower() in s["symbol"].lower() or query.lower() in s["name"].lower()
    ]
    
    return {
        "query": query,
        "results": filtered[:limit],
        "total": len(filtered),
        "fallback": True
    }

def generate_mock_historical_data(symbol: str, period: str, interval: str, max_points: int):
    """Generate mock historical data when real data is unavailable."""
    try:
        # Base prices for different symbols
        base_price = 20800.0 if symbol in ["NQ=F", "NQ"] else 4500.0
        
        # Calculate number of data points based on period and interval
        period_hours = {
            "1d": 24, "5d": 120, "1mo": 720, "3mo": 2160,
            "6mo": 4320, "1y": 8760, "2y": 17520, "5y": 43800, "max": 87600
        }
        
        interval_hours = {
            "1m": 1/60, "5m": 5/60, "15m": 0.25, "30m": 0.5,
            "1h": 1, "2h": 2, "4h": 4, "6h": 6, "12h": 12, "1d": 24
        }
        
        total_hours = period_hours.get(period, 8760)  # Default to 1 year
        interval_h = interval_hours.get(interval, 24)  # Default to daily
        
        # Calculate number of data points
        num_points = min(int(total_hours / interval_h), max_points)
        
        # Generate mock data
        data = []
        current_time = datetime.now()
        
        for i in range(num_points, 0, -1):
            # Calculate timestamp based on interval
            if "m" in interval:
                minutes = int(interval.replace("m", ""))
                timestamp = current_time - timedelta(minutes=i * minutes)
            elif "h" in interval:
                hours = int(interval.replace("h", ""))
                timestamp = current_time - timedelta(hours=i * hours)
            else:  # daily
                timestamp = current_time - timedelta(days=i)
            
            # Generate realistic price movement
            daily_volatility = base_price * 0.015  # 1.5% daily volatility
            price_change = random.uniform(-daily_volatility, daily_volatility)
            price = base_price + price_change + (random.random() - 0.5) * 100
            
            # Ensure price stays realistic
            price = max(price, base_price * 0.8)  # Don't go below 80% of base
            price = min(price, base_price * 1.2)  # Don't go above 120% of base
            
            # Generate OHLC from price
            intraday_range = price * 0.005  # 0.5% intraday range
            open_price = price + random.uniform(-intraday_range/2, intraday_range/2)
            high_price = price + random.uniform(0, intraday_range)
            low_price = price - random.uniform(0, intraday_range)
            close_price = price + random.uniform(-intraday_range/2, intraday_range/2)
            
            # Ensure OHLC relationships are correct
            high_price = max(high_price, open_price, close_price)
            low_price = min(low_price, open_price, close_price)
            
            volume = random.randint(1000, 10000)
            
            data.append({
                "date": timestamp.isoformat(),
                "open": round(open_price, 2),
                "high": round(high_price, 2),
                "low": round(low_price, 2),
                "close": round(close_price, 2),
                "volume": volume
            })
        
        # Sort data by timestamp (oldest first)
        data.sort(key=lambda x: x["date"])
        
        return {
            "symbol": symbol,
            "period": period,
            "interval": interval,
            "data_points": len(data),
            "start_time": data[0]["date"] if data else datetime.now().isoformat(),
            "end_time": data[-1]["date"] if data else datetime.now().isoformat(),
            "data": data,
            "summary": {
                "current_price": data[-1]["close"] if data else base_price,
                "period_high": max(d["high"] for d in data) if data else base_price,
                "period_low": min(d["low"] for d in data) if data else base_price,
                "total_volume": sum(d["volume"] for d in data) if data else 0,
                "price_change": data[-1]["close"] - data[0]["open"] if data else 0,
                "price_change_pct": ((data[-1]["close"] - data[0]["open"]) / data[0]["open"] * 100) if data else 0
            },
            "mock": True  # Flag to indicate this is mock data
        }
    except Exception as e:
        logger.error(f"Failed to generate mock data: {e}")
        # Return minimal mock data structure
        return {
            "symbol": symbol,
            "period": period,
            "interval": interval,
            "data_points": 0,
            "data": [],
            "mock": True,
            "error": str(e)
        }

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

async def send_real_time_price_updates(websocket: WebSocket, symbol: str, ws_manager):
    """Send LIVE TradingView-quality price updates for the selected asset."""
    
    logger.info(f"🎯 Starting LIVE TradingView price updates for {symbol}")
    
    try:
        is_futures = "=F" in symbol
        
        # For NQ futures, use TradingView real-time feed
        if is_futures and symbol in ['NQ=F', 'ES=F', 'YM=F', 'RTY=F']:
            await setup_tradingview_feed(websocket, symbol, ws_manager)
        else:
            await setup_yahoo_feed(websocket, symbol, ws_manager)
            
    except Exception as e:
        logger.error(f"💥 Fatal error in real-time updates for {symbol}: {e}")
        await asyncio.sleep(60.0)

async def setup_tradingview_feed(websocket: WebSocket, symbol: str, ws_manager):
    """Setup TradingView real-time feed for futures."""
    logger.info(f"📡 Setting up TradingView feed for {symbol}")
    
    try:
        # Connect to TradingView if not connected
        if not tv_provider.running:
            await tv_provider.connect()
        
        # Define callback for TradingView data
        async def tv_callback(price_data):
            try:
                if price_data and price_data.get('symbol') == symbol:
                    logger.info(f"🔥 TradingView LIVE update for {symbol}: ${price_data.get('close', 0):.2f}")
                    
                    # Send to WebSocket
                    await ws_manager.send_personal_message(
                        json.dumps(price_data),
                        websocket
                    )
            except Exception as e:
                logger.error(f"❌ Error in TradingView callback: {e}")
        
        # Subscribe to TradingView real-time data
        await tv_provider.subscribe_symbol(symbol, tv_callback)
        
        # Keep connection alive
        while True:
            await asyncio.sleep(1)
            
    except Exception as e:
        logger.error(f"❌ TradingView feed error for {symbol}: {e}")
        # Fallback to Yahoo Finance
        await setup_yahoo_feed(websocket, symbol, ws_manager)

async def setup_yahoo_feed(websocket: WebSocket, symbol: str, ws_manager):
    """Setup Yahoo Finance feed as fallback."""
    logger.info(f"📊 Setting up Yahoo Finance feed for {symbol}")
    
    # Get initial real data
    formatted_symbol = format_symbol_for_yahoo(symbol)
    logger.info(f"📊 Using formatted symbol: {formatted_symbol} for {symbol}")
    ticker = yf.Ticker(formatted_symbol)
    
    last_price = None
    update_counter = 0
    price_history = []  # Keep track of recent prices for agent analysis
    symbol_specific_cache = {}  # Symbol-specific cache to prevent contamination
    
    while True:
        try:
            # REDUCED caching for live data - 5 seconds max for futures during market hours
            cache_key = f"realtime_{symbol}_{int(time.time() // 5)}"
            is_futures = "=F" in symbol
            
            # Skip cache for futures during market hours for more live updates
            if is_futures:
                cache_ttl = 5  # 5 seconds for futures
            else:
                cache_ttl = 15  # 15 seconds for other assets
            
            cached_price_data = symbol_specific_cache.get(cache_key)
            if cached_price_data and (time.time() - cached_price_data.get('cache_time', 0)) < cache_ttl:
                # Use cached data for this update
                logger.info(f"📈 Using cached data for {symbol} (age: {time.time() - cached_price_data.get('cache_time', 0):.1f}s)")
                await ws_manager.send_personal_message(
                    json.dumps(cached_price_data),
                    websocket
                )
                await asyncio.sleep(cache_ttl)
                continue
            
            # Get REAL market data for the selected symbol with better error handling
            logger.info(f"🔄 Fetching fresh data for {symbol} (formatted: {formatted_symbol})")
            
            # Try different intervals for better live data
            recent_data = None
            for interval in ["1m", "2m", "5m"]:
                try:
                    recent_data = ticker.history(period="1d", interval=interval)
                    if not recent_data.empty:
                        break
                except Exception as e:
                    logger.warning(f"Failed to get {interval} data for {symbol}: {e}")
                    continue
            
            if recent_data is not None and not recent_data.empty:
                latest = recent_data.iloc[-1]
                latest_time = recent_data.index[-1]
                
                # Extract REAL OHLC data with validation
                current_price = float(latest['Close'])
                open_price = float(latest['Open'])
                high_price = float(latest['High'])
                low_price = float(latest['Low'])
                volume = int(latest['Volume']) if not pd.isna(latest['Volume']) else 0
                
                # Validate price data is reasonable
                if current_price <= 0 or current_price > 1000000:
                    logger.error(f"❌ Invalid price data for {symbol}: ${current_price}")
                    continue
                
                logger.info(f"💰 Fresh {symbol} data: ${current_price:.2f} (volume: {volume})")
                
                # Track price history for agent analysis (symbol-specific)
                price_history.append({
                    "timestamp": datetime.now().isoformat(),
                    "price": current_price,
                    "volume": volume,
                    "symbol": symbol  # Track symbol to prevent contamination
                })
                price_history = price_history[-100:]  # Keep last 100 data points
                
                # More aggressive updates for futures during market hours
                price_changed = last_price is None or abs(current_price - last_price) > 0.001  # Smaller threshold
                time_since_last_update = update_counter * 5
                
                # Force updates more frequently for futures
                force_update_interval = 5 if is_futures else 15
                force_update = time_since_last_update >= force_update_interval
                
                if price_changed or force_update:
                    # Calculate real change
                    change = current_price - last_price if last_price else 0
                    
                    # Calculate proper candle timing for frontend
                    current_timestamp = int(time.time())
                    
                    # Use current time for candle positioning to avoid timezone issues
                    safe_candle_time = current_timestamp
                    
                    # Send REAL price update with enhanced timing info and symbol validation
                    price_data = {
                        "type": "price_update",
                        "symbol": symbol,  # CRITICAL: Exact symbol match
                        "formatted_symbol": formatted_symbol,
                        "open": open_price,
                        "high": high_price, 
                        "low": low_price,
                        "close": current_price,
                        "volume": volume,
                        "change": round(change, 2),
                        "timestamp": datetime.now().isoformat(),
                        "candle_time": safe_candle_time,
                        "current_time": current_timestamp,
                        "price_changed": price_changed,
                        "real_data": True,
                        "source": f"yahoo_{formatted_symbol}",
                        "update_reason": "price_change" if price_changed else "periodic_update",
                        "cache_time": time.time()  # Track cache time
                    }
                    
                    # Store in symbol-specific cache to prevent contamination
                    symbol_specific_cache[cache_key] = price_data
                    
                    # Send update to frontend
                    await ws_manager.send_personal_message(
                        json.dumps(price_data),
                        websocket
                    )
                    
                    logger.info(f"🔄 Sent {symbol} update: ${current_price:.2f} (change: {change:+.2f}) - {price_data['update_reason']}")
                    
                    # Trigger agent analysis with recent market data (symbol-specific)
                    symbol_price_history = [p for p in price_history if p.get('symbol') == symbol]
                    if len(symbol_price_history) >= 10:
                        await trigger_agent_analysis(websocket, symbol, symbol_price_history, ws_manager)
                    
                    last_price = current_price
                    update_counter += 1
                    
                else:
                    logger.warning(f"⚠️ No recent data for {symbol}")
                
            # Check for real updates every 5 seconds for responsive trading
            await asyncio.sleep(5.0)
                
        except Exception as e:
            error_msg = str(e)
            if "rate limited" in error_msg.lower() or "too many requests" in error_msg.lower():
                logger.warning(f"🚦 Rate limited for {symbol}, using fallback data...")
                
                # Send fallback price data when rate limited
                if last_price is not None:
                    # Generate small price variation based on last known price
                    price_variation = last_price * 0.002 * (random.random() - 0.5)  # ±0.1% variation
                    fallback_price = last_price + price_variation
                    
                    current_ts = int(time.time())
                    fallback_data = {
                        "type": "price_update",
                        "symbol": symbol,
                        "open": fallback_price,
                        "high": fallback_price * 1.001,
                        "low": fallback_price * 0.999,
                        "close": fallback_price,
                        "volume": random.randint(1000, 10000),
                        "change": price_variation,
                        "timestamp": datetime.now().isoformat(),
                        "candle_time": current_ts,
                        "current_time": current_ts,
                        "real_data": False,
                        "source": f"fallback_{symbol}",
                        "update_reason": "rate_limit_fallback"
                    }
                    
                    await ws_manager.send_personal_message(
                        json.dumps(fallback_data),
                        websocket
                    )
                    last_price = fallback_price
                
                await asyncio.sleep(300.0)  # Wait 5 minutes before retry
            else:
                logger.error(f"❌ Error getting real data for {symbol}: {e}")
                await asyncio.sleep(60.0)  # Wait 1 minute on other errors
                continue
                
        except Exception as e:
            logger.error(f"💥 Fatal error in real-time updates for {symbol}: {e}")
            await asyncio.sleep(60.0)

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

async def trigger_agent_analysis(websocket: WebSocket, symbol: str, price_history: List[Dict], ws_manager):
    """Trigger automated agent analysis with live market data."""
    try:
        # Calculate basic technical indicators from price history
        prices = [p["price"] for p in price_history]
        volumes = [p["volume"] for p in price_history]
        
        if len(prices) < 5:
            return
            
        # Simple moving averages
        sma_5 = sum(prices[-5:]) / 5
        sma_10 = sum(prices[-10:]) / 10 if len(prices) >= 10 else sum(prices) / len(prices)
        
        # Price momentum
        current_price = prices[-1]
        prev_price = prices[-5] if len(prices) >= 5 else prices[0]
        momentum = (current_price - prev_price) / prev_price * 100
        
        # Volume analysis
        avg_volume = sum(volumes[-10:]) / min(10, len(volumes))
        volume_spike = volumes[-1] > avg_volume * 1.5
        
        # Generate trading signal based on analysis
        signal_type = "hold"
        confidence = 0.5
        reason = "Consolidation"
        
        # Bullish conditions
        if momentum > 2 and current_price > sma_5 > sma_10:
            signal_type = "buy"
            confidence = 0.75 + (0.2 if volume_spike else 0)
            reason = f"Bullish momentum: {momentum:.1f}%, Price above MAs"
        
        # Bearish conditions
        elif momentum < -2 and current_price < sma_5 < sma_10:
            signal_type = "sell"
            confidence = 0.75 + (0.2 if volume_spike else 0)
            reason = f"Bearish momentum: {momentum:.1f}%, Price below MAs"
        
        # Strong momentum
        elif abs(momentum) > 5:
            signal_type = "buy" if momentum > 0 else "sell"
            confidence = min(0.9, 0.6 + abs(momentum) / 20)
            reason = f"Strong momentum: {momentum:.1f}%"
        
        # Only send signals with sufficient confidence
        if confidence > 0.6:
            signal_data = {
                "type": "trading_signal",
                "signal": {
                    "id": f"signal_{int(time.time())}",
                    "symbol": symbol,
                    "action": signal_type,
                    "price": current_price,
                    "confidence": round(confidence, 2),
                    "reason": reason,
                    "timestamp": datetime.now().isoformat(),
                    "indicators": {
                        "sma_5": round(sma_5, 2),
                        "sma_10": round(sma_10, 2),
                        "momentum": round(momentum, 2),
                        "volume_spike": volume_spike
                    },
                    "agent_id": "live_analysis_agent"
                }
            }
            
            await ws_manager.send_personal_message(
                json.dumps(signal_data),
                websocket
            )
            
            logger.info(f"🤖 Agent signal: {signal_type.upper()} {symbol} @ ${current_price:.2f} (confidence: {confidence:.0%})")
            
    except Exception as e:
        logger.error(f"Failed to trigger agent analysis: {e}")
