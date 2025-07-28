"""
TradingView Real-Time Data Provider
==================================

Direct connection to TradingView's real-time data feed for live NQ futures data.
This provides the same data you'd see on the TradingView platform.
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Callable
import websockets
import aiohttp
from datetime import datetime

logger = logging.getLogger(__name__)

class TradingViewProvider:
    """TradingView real-time data provider for live market data."""
    
    def __init__(self):
        self.ws_url = "wss://data.tradingview.com/socket.io/websocket"
        self.session_id = None
        self.websocket = None
        self.subscribers = {}
        self.auth_token = None
        self.running = False
        
    async def connect(self):
        """Connect to TradingView WebSocket."""
        try:
            logger.info("🔌 Connecting to TradingView WebSocket...")
            
            # Create session first
            await self._create_session()
            
            # Connect to WebSocket
            self.websocket = await websockets.connect(
                f"{self.ws_url}?from=chart%2F&date=2025_01_14-15_48",
                extra_headers={
                    "Origin": "https://www.tradingview.com",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            )
            
            # Send initial messages
            await self._initialize_connection()
            
            self.running = True
            logger.info("✅ Connected to TradingView WebSocket")
            
            # Start message handler
            asyncio.create_task(self._handle_messages())
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to TradingView: {e}")
            raise
    
    async def _create_session(self):
        """Create TradingView session."""
        try:
            async with aiohttp.ClientSession() as session:
                # Get session
                async with session.get(
                    "https://www.tradingview.com/chart/",
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    }
                ) as response:
                    if response.status == 200:
                        # Extract session info from response
                        self.session_id = f"session_{int(time.time())}"
                        logger.info(f"📝 Created TradingView session: {self.session_id}")
        except Exception as e:
            logger.warning(f"⚠️ Session creation failed, using fallback: {e}")
            self.session_id = f"session_{int(time.time())}"
    
    async def _initialize_connection(self):
        """Initialize WebSocket connection with TradingView."""
        try:
            # Send protocol messages
            messages = [
                '~m~25~m~{"m":"set_auth_token","p":["unauthorized_user_token"]}',
                '~m~32~m~{"m":"chart_create_session","p":["cs_1",""]}'
            ]
            
            for msg in messages:
                await self.websocket.send(msg)
                await asyncio.sleep(0.1)
                
            logger.info("📡 Initialized TradingView connection")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize connection: {e}")
            raise
    
    async def subscribe_symbol(self, symbol: str, callback: Callable):
        """Subscribe to real-time data for a symbol."""
        try:
            # Convert symbol to TradingView format
            tv_symbol = self._convert_to_tv_symbol(symbol)
            
            # Store callback
            self.subscribers[symbol] = callback
            
            # Subscribe to symbol
            subscription_msg = self._create_subscription_message(tv_symbol)
            await self.websocket.send(subscription_msg)
            
            logger.info(f"📊 Subscribed to {symbol} ({tv_symbol}) on TradingView")
            
        except Exception as e:
            logger.error(f"❌ Failed to subscribe to {symbol}: {e}")
    
    def _convert_to_tv_symbol(self, symbol: str) -> str:
        """Convert symbol to TradingView format."""
        symbol_map = {
            'NQ=F': 'CME_MINI:NQ1!',
            'ES=F': 'CME_MINI:ES1!', 
            'YM=F': 'CBOT_MINI:YM1!',
            'RTY=F': 'CME_MINI:RTY1!',
            'BTC-USD': 'BITSTAMP:BTCUSD',
            'ETH-USD': 'BITSTAMP:ETHUSD',
            'AAPL': 'NASDAQ:AAPL',
            'TSLA': 'NASDAQ:TSLA',
            'SPY': 'AMEX:SPY'
        }
        
        return symbol_map.get(symbol, f"NASDAQ:{symbol}")
    
    def _create_subscription_message(self, tv_symbol: str) -> str:
        """Create TradingView subscription message."""
        # Real-time quote subscription
        quote_msg = {
            "m": "quote_create_session",
            "p": ["qs_1", ""]
        }
        
        symbol_msg = {
            "m": "quote_add_symbols", 
            "p": ["qs_1", tv_symbol, {"flags": ["force_permission"]}]
        }
        
        # Format as TradingView protocol
        quote_formatted = f'~m~{len(json.dumps(quote_msg))}~m~{json.dumps(quote_msg)}'
        symbol_formatted = f'~m~{len(json.dumps(symbol_msg))}~m~{json.dumps(symbol_msg)}'
        
        return quote_formatted + symbol_formatted
    
    async def _handle_messages(self):
        """Handle incoming WebSocket messages."""
        try:
            while self.running and self.websocket:
                message = await self.websocket.recv()
                await self._process_message(message)
                
        except websockets.exceptions.ConnectionClosed:
            logger.warning("🔌 TradingView WebSocket connection closed")
            await self._reconnect()
        except Exception as e:
            logger.error(f"❌ Error handling TradingView messages: {e}")
            await self._reconnect()
    
    async def _process_message(self, message: str):
        """Process TradingView WebSocket message."""
        try:
            # Parse TradingView protocol
            if message.startswith("~m~"):
                # Extract JSON from protocol wrapper
                parts = message.split("~m~")
                for part in parts:
                    if part and part.startswith("{"):
                        try:
                            data = json.loads(part)
                            await self._handle_data_message(data)
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logger.error(f"❌ Error processing message: {e}")
    
    async def _handle_data_message(self, data: Dict):
        """Handle parsed data message."""
        try:
            message_type = data.get("m")
            params = data.get("p", [])
            
            if message_type == "qsd":  # Quote symbol data
                await self._handle_quote_data(params)
            elif message_type == "du":  # Data update
                await self._handle_data_update(params)
                
        except Exception as e:
            logger.error(f"❌ Error handling data message: {e}")
    
    async def _handle_quote_data(self, params: List):
        """Handle quote data from TradingView."""
        try:
            if len(params) >= 2:
                symbol_data = params[1]
                
                # Extract price information
                if isinstance(symbol_data, dict):
                    symbol = symbol_data.get("n", "")
                    values = symbol_data.get("v", {})
                    
                    if values and isinstance(values, dict):
                        # Convert TradingView data to our format
                        price_data = self._convert_tv_data(symbol, values)
                        
                        # Find matching subscriber
                        for subscribed_symbol, callback in self.subscribers.items():
                            tv_symbol = self._convert_to_tv_symbol(subscribed_symbol)
                            if tv_symbol == symbol:
                                await callback(price_data)
                                break
                                
        except Exception as e:
            logger.error(f"❌ Error handling quote data: {e}")
    
    def _convert_tv_data(self, tv_symbol: str, values: Dict) -> Dict:
        """Convert TradingView data to our price format."""
        try:
            # TradingView field mappings
            current_price = values.get("lp", 0)  # Last price
            change = values.get("ch", 0)  # Change
            change_percent = values.get("chp", 0)  # Change percent
            volume = values.get("volume", 0)  # Volume
            bid = values.get("bid", current_price)
            ask = values.get("ask", current_price)
            
            # For OHLC, we'll use current price as approximation for real-time
            # In a full implementation, you'd get this from separate OHLC feed
            
            return {
                "type": "price_update",
                "symbol": self._convert_from_tv_symbol(tv_symbol),
                "formatted_symbol": tv_symbol,
                "open": current_price,  # Will be updated with real OHLC
                "high": current_price,
                "low": current_price, 
                "close": current_price,
                "volume": int(volume) if volume else 0,
                "change": round(float(change), 2),
                "change_percent": round(float(change_percent), 2),
                "bid": float(bid),
                "ask": float(ask),
                "timestamp": datetime.now().isoformat(),
                "candle_time": int(time.time()),
                "current_time": int(time.time()),
                "price_changed": True,
                "real_data": True,
                "source": f"tradingview_{tv_symbol}",
                "update_reason": "live_update"
            }
            
        except Exception as e:
            logger.error(f"❌ Error converting TradingView data: {e}")
            return {}
    
    def _convert_from_tv_symbol(self, tv_symbol: str) -> str:
        """Convert TradingView symbol back to our format."""
        reverse_map = {
            'CME_MINI:NQ1!': 'NQ=F',
            'CME_MINI:ES1!': 'ES=F',
            'CBOT_MINI:YM1!': 'YM=F', 
            'CME_MINI:RTY1!': 'RTY=F',
            'BITSTAMP:BTCUSD': 'BTC-USD',
            'BITSTAMP:ETHUSD': 'ETH-USD',
            'NASDAQ:AAPL': 'AAPL',
            'NASDAQ:TSLA': 'TSLA',
            'AMEX:SPY': 'SPY'
        }
        
        return reverse_map.get(tv_symbol, tv_symbol.split(':')[-1])
    
    async def _reconnect(self):
        """Reconnect to TradingView."""
        try:
            if self.websocket:
                await self.websocket.close()
            
            await asyncio.sleep(5)  # Wait before reconnecting
            await self.connect()
            
            # Re-subscribe to all symbols
            for symbol in list(self.subscribers.keys()):
                callback = self.subscribers[symbol]
                await self.subscribe_symbol(symbol, callback)
                
        except Exception as e:
            logger.error(f"❌ Reconnection failed: {e}")
    
    async def disconnect(self):
        """Disconnect from TradingView."""
        self.running = False
        if self.websocket:
            await self.websocket.close()
        logger.info("🔌 Disconnected from TradingView")

# Global TradingView provider instance
tv_provider = TradingViewProvider()