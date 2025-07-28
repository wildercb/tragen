#!/usr/bin/env python3
"""
REAL Market Data Service - NO FAKE DATA ALLOWED
==============================================
Only provides actual market data from real sources
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
import yfinance as yf
import aiohttp
import websockets

logger = logging.getLogger(__name__)

class RealMarketDataService:
    """REAL market data service - NO FAKE DATA EVER"""
    
    def __init__(self):
        self.subscribers = {}
        self.last_real_data = {}
        self.data_sources = ['yahoo', 'tradingview', 'alpha_vantage']
        
    async def get_real_current_price(self, symbol: str) -> Dict:
        """Get REAL current price from Yahoo Finance"""
        try:
            ticker = yf.Ticker(symbol)
            
            # Get the most recent real data
            recent_data = ticker.history(period="1d", interval="1m")
            
            if recent_data.empty:
                # Try 5-minute data if 1-minute fails
                recent_data = ticker.history(period="5d", interval="5m")
            
            if recent_data.empty:
                raise Exception(f"No real data available for {symbol}")
            
            latest = recent_data.iloc[-1]
            latest_time = recent_data.index[-1]
            
            # Extract REAL market data
            real_data = {
                "symbol": symbol,
                "current_price": float(latest['Close']),
                "open": float(latest['Open']),
                "high": float(latest['High']),
                "low": float(latest['Low']),
                "volume": int(latest['Volume']) if not pd.isna(latest['Volume']) else 0,
                "timestamp": datetime.now().isoformat(),
                "data_time": latest_time.isoformat(),
                "source": "yahoo_finance_real_data"
            }
            
            self.last_real_data[symbol] = real_data
            return real_data
            
        except Exception as e:
            logger.error(f"Failed to get real data for {symbol}: {e}")
            raise Exception(f"Cannot provide fake data. Real data unavailable: {e}")
    
    async def get_real_historical_data(self, symbol: str, period: str = "1y") -> List[Dict]:
        """Get REAL historical data from Yahoo Finance"""
        try:
            ticker = yf.Ticker(symbol)
            
            # Get real historical data
            hist_data = ticker.history(period=period, interval="1d")
            
            if hist_data.empty:
                raise Exception(f"No real historical data available for {symbol}")
            
            real_historical = []
            for timestamp, row in hist_data.iterrows():
                real_historical.append({
                    "date": timestamp.isoformat(),
                    "open": float(row['Open']),
                    "high": float(row['High']),
                    "low": float(row['Low']),
                    "close": float(row['Close']),
                    "volume": int(row['Volume']) if not pd.isna(row['Volume']) else 0,
                    "real_data": True,
                    "source": "yahoo_finance_historical"
                })
            
            logger.info(f"Retrieved {len(real_historical)} real data points for {symbol}")
            return real_historical
            
        except Exception as e:
            logger.error(f"Failed to get real historical data for {symbol}: {e}")
            raise Exception(f"Cannot provide fake data. Real historical data unavailable: {e}")
    
    async def start_real_data_feed(self, symbol: str):
        """Start real data feed - updates every 5 seconds with REAL data only"""
        logger.info(f"Starting REAL data feed for {symbol} - 5 second updates")
        
        while True:
            try:
                # Get fresh real data
                real_price_data = await self.get_real_current_price(symbol)
                
                # Format for WebSocket
                update = {
                    "type": "price_update",
                    "symbol": symbol,
                    "open": real_price_data["open"],
                    "high": real_price_data["high"],
                    "low": real_price_data["low"],
                    "close": real_price_data["current_price"],
                    "volume": real_price_data["volume"],
                    "timestamp": real_price_data["timestamp"],
                    "candle_time": int(time.time()),
                    "current_time": int(time.time()),
                    "real_data": True,
                    "source": "real_market_feed",
                    "data_age": "live"
                }
                
                # Send to subscribers
                if symbol in self.subscribers:
                    for callback in self.subscribers[symbol]:
                        try:
                            await callback(update)
                        except Exception as e:
                            logger.error(f"Error sending real data to subscriber: {e}")
                
                logger.info(f"REAL {symbol}: ${real_price_data['current_price']:.2f}")
                
                # Wait 5 seconds for next real data update
                await asyncio.sleep(5.0)
                
            except Exception as e:
                logger.error(f"Error getting real data for {symbol}: {e}")
                # DO NOT provide fake data - just wait and retry
                await asyncio.sleep(10.0)
    
    async def subscribe_to_real_updates(self, symbol: str, callback: Callable):
        """Subscribe to real data updates only"""
        if symbol not in self.subscribers:
            self.subscribers[symbol] = []
        self.subscribers[symbol].append(callback)
        logger.info(f"Subscribed to REAL data updates for {symbol}")

# Global real market data service
real_market_service = RealMarketDataService()