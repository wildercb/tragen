#!/usr/bin/env python3
"""
REAL Market Data Server - NO FAKE DATA
=====================================
Only serves actual market data from real sources
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
import json
import logging
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="REAL Market Data API", description="Only real market data - NO FAKE DATA")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RealDataProvider:
    """Provides ONLY real market data"""
    
    def __init__(self):
        self.subscribers = {}
        
    async def get_real_price(self, symbol: str) -> dict:
        """Get REAL current price from Yahoo Finance"""
        try:
            ticker = yf.Ticker(symbol)
            
            # Get real recent data
            recent_data = ticker.history(period="1d", interval="1m")
            if recent_data.empty:
                recent_data = ticker.history(period="5d", interval="5m")
            if recent_data.empty:
                recent_data = ticker.history(period="5d", interval="1d")
                
            if recent_data.empty:
                raise Exception(f"No real data available for {symbol}")
            
            latest = recent_data.iloc[-1]
            
            return {
                "symbol": symbol,
                "current_price": float(latest['Close']),
                "session_high": float(recent_data['High'].max()),
                "session_low": float(recent_data['Low'].min()),
                "volume": int(latest['Volume']) if not pd.isna(latest['Volume']) else 0,
                "timestamp": datetime.now().isoformat(),
                "real_data": True,
                "source": "yahoo_finance"
            }
            
        except Exception as e:
            logger.error(f"Cannot get real data for {symbol}: {e}")
            raise Exception(f"Real data unavailable for {symbol}")
    
    async def get_real_historical(self, symbol: str, period: str = "1y") -> dict:
        """Get REAL historical data"""
        try:
            ticker = yf.Ticker(symbol)
            hist_data = ticker.history(period=period, interval="1d")
            
            if hist_data.empty:
                raise Exception(f"No real historical data for {symbol}")
            
            data = []
            for timestamp, row in hist_data.iterrows():
                data.append({
                    "date": timestamp.isoformat(),
                    "open": float(row['Open']),
                    "high": float(row['High']),
                    "low": float(row['Low']),
                    "close": float(row['Close']),
                    "volume": int(row['Volume']) if not pd.isna(row['Volume']) else 0
                })
            
            return {
                "symbol": symbol,
                "data": data,
                "real_data": True,
                "source": "yahoo_finance_historical"
            }
            
        except Exception as e:
            logger.error(f"Cannot get real historical data for {symbol}: {e}")
            raise Exception(f"Real historical data unavailable for {symbol}")

# Global real data provider
real_provider = RealDataProvider()

@app.get("/api/market/price")
async def get_real_market_price(symbol: str = "NQ=F"):
    """Get REAL current market price - NO FAKE DATA"""
    try:
        real_data = await real_provider.get_real_price(symbol)
        logger.info(f"Serving REAL price for {symbol}: ${real_data['current_price']:.2f}")
        return real_data
    except Exception as e:
        logger.error(f"Failed to get real price: {e}")
        return {"error": f"Real data unavailable: {str(e)}"}

@app.get("/api/market/historical")
async def get_real_historical_data(symbol: str = "NQ=F", period: str = "1y", interval: str = "1d", max_points: int = 1000):
    """Get REAL historical market data - NO FAKE DATA"""
    try:
        real_data = await real_provider.get_real_historical(symbol, period)
        logger.info(f"Serving REAL historical data for {symbol}: {len(real_data['data'])} points")
        return real_data
    except Exception as e:
        logger.error(f"Failed to get real historical data: {e}")
        return {"error": f"Real historical data unavailable: {str(e)}"}

@app.websocket("/api/ws/market/{symbol}")
async def real_websocket_feed(websocket: WebSocket, symbol: str):
    """WebSocket for REAL market data updates every 5 seconds"""
    await websocket.accept()
    logger.info(f"WebSocket connected for REAL data: {symbol}")
    
    try:
        # Send connection confirmation
        await websocket.send_text(json.dumps({
            "type": "connected",
            "symbol": symbol,
            "message": f"Connected to REAL data feed for {symbol}",
            "real_data_only": True
        }))
        
        while True:
            try:
                # Get fresh REAL data
                real_price_data = await real_provider.get_real_price(symbol)
                
                # Format for chart
                update = {
                    "type": "price_update",
                    "symbol": symbol,
                    "open": real_price_data["current_price"],  # Use current as open for 5-sec updates
                    "high": real_price_data["current_price"],
                    "low": real_price_data["current_price"],
                    "close": real_price_data["current_price"],
                    "volume": real_price_data["volume"],
                    "timestamp": real_price_data["timestamp"],
                    "candle_time": int(datetime.now().timestamp()),
                    "current_time": int(datetime.now().timestamp()),
                    "real_data": True,
                    "source": "real_yahoo_feed"
                }
                
                await websocket.send_text(json.dumps(update))
                logger.info(f"REAL {symbol} update: ${real_price_data['current_price']:.2f}")
                
                # Update every 5 seconds with REAL data
                await asyncio.sleep(5.0)
                
            except Exception as e:
                logger.error(f"Error getting real data: {e}")
                # Don't send fake data - just wait longer and retry
                await asyncio.sleep(10.0)
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for {symbol}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")

@app.get("/api/status")
async def status():
    return {
        "status": "REAL DATA ONLY",
        "fake_data": "NEVER",
        "sources": ["yahoo_finance"],
        "update_interval": "5_seconds"
    }

if __name__ == "__main__":
    logger.info("🔥 Starting REAL MARKET DATA SERVER - NO FAKE DATA ALLOWED")
    uvicorn.run(app, host="0.0.0.0", port=8001)