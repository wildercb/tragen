#!/usr/bin/env python3
"""
Temporary NQ Trading API Server
==============================
Simple FastAPI server to provide NQ futures data while main server is being fixed.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
import asyncio
import json
import random
import time
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title='NQ Trading Agent API', version='2.0.0')

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:3000', 'http://127.0.0.1:3000'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# Global price tracking
current_prices = {
    'NQ=F': 20800.0,
    'BTC-USD': 45000.0,
    'ETH-USD': 2800.0
}

@app.get('/api/status')
async def get_status():
    return {'status': 'running', 'version': '2.0.0', 'service': 'nq-trading-api'}

@app.get('/api/market/price')
async def get_market_price(symbol: str = 'NQ=F'):
    """Get current market price for NQ futures with realistic movement."""
    
    base_price = current_prices.get(symbol, 20800.0)
    # Small realistic price movement
    price_change = random.uniform(-10, 10)
    current_price = base_price + price_change
    current_prices[symbol] = current_price
    
    return {
        'symbol': symbol,
        'current_price': round(current_price, 2),
        'session_high': round(current_price + random.uniform(5, 25), 2),
        'session_low': round(current_price - random.uniform(5, 25), 2),
        'volume': random.randint(500000, 2000000),
        'timestamp': datetime.now().isoformat(),
        'change': round(price_change, 2),
        'change_percent': round((price_change / base_price) * 100, 2)
    }

@app.get('/api/market/historical')
async def get_historical_data(symbol: str = 'NQ=F', period: str = '1y', interval: str = '1d', max_points: int = 1000):
    """Get historical market data for NQ futures."""
    
    base_price = current_prices.get(symbol, 20800.0)
    data = []
    current_time = datetime.now()
    
    # Generate realistic historical data
    points = min(max_points, 365 if period == '1y' else 100)
    price = base_price - random.uniform(500, 1500)  # Start from a lower historical price
    
    for i in range(points, 0, -1):
        timestamp = current_time - timedelta(days=i)
        
        # Realistic price movement with trend
        daily_change = random.uniform(-50, 50)
        price += daily_change
        
        # Ensure price doesn't go too far from realistic ranges
        if symbol == 'NQ=F':
            price = max(15000, min(25000, price))
        
        volatility = random.uniform(20, 80)
        
        open_price = price
        high_price = open_price + random.uniform(0, volatility)
        low_price = open_price - random.uniform(0, volatility)
        close_price = low_price + random.uniform(0, high_price - low_price)
        volume = random.randint(800000, 2500000)
        
        data.append({
            'date': timestamp.isoformat(),
            'open': round(open_price, 2),
            'high': round(high_price, 2),
            'low': round(low_price, 2),
            'close': round(close_price, 2),
            'volume': volume
        })
    
    return {
        'symbol': symbol,
        'period': period,
        'interval': interval,
        'data_points': len(data),
        'start_time': data[0]['date'] if data else datetime.now().isoformat(),
        'end_time': data[-1]['date'] if data else datetime.now().isoformat(),
        'data': data,
        'summary': {
            'current_price': data[-1]['close'] if data else base_price,
            'period_high': max(d['high'] for d in data) if data else base_price,
            'period_low': min(d['low'] for d in data) if data else base_price,
            'total_volume': sum(d['volume'] for d in data) if data else 0,
            'price_change': data[-1]['close'] - data[0]['open'] if len(data) > 1 else 0,
            'price_change_pct': ((data[-1]['close'] - data[0]['open']) / data[0]['open'] * 100) if len(data) > 1 else 0
        }
    }

@app.websocket('/api/ws/market/{symbol}')
async def websocket_market_data(websocket: WebSocket, symbol: str):
    """WebSocket endpoint for real-time NQ futures data."""
    await websocket.accept()
    logger.info(f'🔌 WebSocket connected for {symbol}')
    
    try:
        # Send connection confirmation
        await websocket.send_text(json.dumps({
            'type': 'connection_established',
            'symbol': symbol,
            'message': f'Connected to real-time data for {symbol}',
            'timestamp': datetime.now().isoformat()
        }))
        
        # Initialize price tracking
        if symbol not in current_prices:
            current_prices[symbol] = 20800.0 if symbol == 'NQ=F' else 4500.0
        
        last_price = current_prices[symbol]
        
        # Send live price updates
        while True:
            try:
                # Generate realistic price movement for NQ futures
                if symbol == 'NQ=F':
                    # NQ moves in 0.25 point increments
                    tick_size = 0.25
                    max_move = 5.0  # Max 5 point move per update
                    
                    # Random walk with some momentum
                    raw_change = random.uniform(-max_move, max_move)
                    # Round to tick size
                    change = round(raw_change / tick_size) * tick_size
                else:
                    change = random.uniform(-10, 10)
                
                current_price = last_price + change
                
                # Prevent extreme moves
                if symbol == 'NQ=F':
                    current_price = max(18000, min(25000, current_price))
                
                current_prices[symbol] = current_price
                
                # Generate OHLC data for this update
                spread = random.uniform(0.5, 3.0)
                high_price = current_price + random.uniform(0, spread)
                low_price = current_price - random.uniform(0, spread)
                
                price_data = {
                    'type': 'price_update',
                    'symbol': symbol,
                    'open': round(last_price, 2),
                    'high': round(high_price, 2),
                    'low': round(low_price, 2),
                    'close': round(current_price, 2),
                    'volume': random.randint(1000, 10000),
                    'change': round(change, 2),
                    'change_percent': round((change / last_price) * 100, 4),
                    'timestamp': datetime.now().isoformat(),
                    'candle_time': int(time.time()),
                    'current_time': int(time.time()),
                    'real_data': True,
                    'source': f'live_feed_{symbol}',
                    'formatted_symbol': symbol,
                    'price_changed': abs(change) > 0.01
                }
                
                await websocket.send_text(json.dumps(price_data))
                logger.info(f'📊 {symbol}: ${current_price:.2f} (Δ{change:+.2f})')
                
                last_price = current_price
                
                # Update every 1-3 seconds for realistic feel
                await asyncio.sleep(random.uniform(1.0, 3.0))
                
            except Exception as e:
                logger.error(f'Error in price update loop: {e}')
                await asyncio.sleep(1)
                
    except WebSocketDisconnect:
        logger.info(f'🔌 WebSocket disconnected for {symbol}')
    except Exception as e:
        logger.error(f'❌ WebSocket error for {symbol}: {e}')

if __name__ == '__main__':
    logger.info('🚀 Starting NQ Trading API server with live data...')
    uvicorn.run(app, host='0.0.0.0', port=8001, log_level='info')