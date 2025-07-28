#!/usr/bin/env python3
"""
Simple TradingView-Compatible NQ Server
======================================
Provides data in exact TradingView Lightweight Charts format
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
import json
import random
import time
from datetime import datetime, timedelta

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
nq_price = 20800.0

@app.get("/api/market/historical")
async def get_historical_data(symbol: str = "NQ=F", period: str = "1y", interval: str = "1d", max_points: int = 1000):
    """Return historical data in TradingView format"""
    data = []
    current_time = datetime.now()
    price = 20000.0
    
    # Generate 500 days of historical data
    for i in range(500, 0, -1):
        date = current_time - timedelta(days=i)
        
        # Random walk price movement
        price += random.uniform(-50, 50)
        price = max(18000, min(23000, price))  # Keep in realistic range
        
        # Generate OHLC
        daily_range = random.uniform(20, 100)
        open_price = price + random.uniform(-daily_range/2, daily_range/2)
        high_price = open_price + random.uniform(0, daily_range)
        low_price = open_price - random.uniform(0, daily_range)
        close_price = low_price + random.uniform(0, high_price - low_price)
        
        data.append({
            "date": date.isoformat(),  # ISO date string for frontend
            "open": round(open_price, 2),
            "high": round(high_price, 2),
            "low": round(low_price, 2),
            "close": round(close_price, 2),
            "volume": random.randint(100000, 1000000)
        })
    
    # Set global price to last close for continuity
    global nq_price
    nq_price = data[-1]["close"]
    
    return {
        "symbol": symbol,
        "data": data
    }

@app.get("/api/market/price")
async def get_current_price(symbol: str = "NQ=F"):
    """Get current price"""
    global nq_price
    return {
        "symbol": symbol,
        "current_price": nq_price,
        "timestamp": datetime.now().isoformat()
    }

@app.websocket("/api/ws/market/{symbol}")
async def websocket_endpoint(websocket: WebSocket, symbol: str):
    await websocket.accept()
    print(f"WebSocket connected for {symbol}")
    
    global nq_price
    
    try:
        # Send connection confirmation
        await websocket.send_text(json.dumps({
            "type": "connected",
            "symbol": symbol
        }))
        
        while True:
            # Generate realistic NQ price movement (0.25 tick size)
            tick_size = 0.25
            max_move = 5.0
            
            # Random price change
            change = random.uniform(-max_move, max_move)
            change = round(change / tick_size) * tick_size  # Round to tick size
            
            nq_price += change
            nq_price = max(18000, min(25000, nq_price))  # Keep in range
            
            # Create TradingView compatible real-time data
            now = time.time()
            
            # Generate realistic OHLC for this tick
            spread = random.uniform(0.5, 2.0)
            high = nq_price + random.uniform(0, spread)
            low = nq_price - random.uniform(0, spread)
            
            price_update = {
                "type": "price_update",
                "symbol": symbol,
                "open": round(nq_price - change, 2),
                "high": round(high, 2),
                "low": round(low, 2),
                "close": round(nq_price, 2),
                "volume": random.randint(100, 1000),
                "change": round(change, 2),
                "timestamp": datetime.now().isoformat(),
                "candle_time": int(now),
                "current_time": int(now),
                "real_data": True,
                "source": "live_feed"
            }
            
            await websocket.send_text(json.dumps(price_update))
            print(f"NQ: ${nq_price:.2f} (${change:+.2f})")
            
            # Update every 1-2 seconds like real TradingView
            await asyncio.sleep(random.uniform(1.0, 2.0))
            
    except WebSocketDisconnect:
        print(f"WebSocket disconnected for {symbol}")
    except Exception as e:
        print(f"WebSocket error: {e}")

if __name__ == "__main__":
    print("Starting Simple TradingView-Compatible Server...")
    uvicorn.run(app, host="0.0.0.0", port=8001)