"""
Data ingestion module for NQ futures trading data
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, AsyncGenerator
import pandas as pd
import numpy as np
import websockets
import aiohttp
import yfinance as yf

logger = logging.getLogger(__name__)


class DataSource(ABC):
    """
    Abstract base class for data sources.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the data source.
        
        Args:
            config: Data source configuration
        """
        self.config = config
        self.is_connected = False
        
    @abstractmethod
    async def connect(self) -> None:
        """Connect to the data source."""
        pass
        
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the data source."""
        pass
        
    @abstractmethod
    async def get_historical_data(
        self, 
        symbol: str, 
        start_date: datetime, 
        end_date: datetime,
        interval: str = "1m"
    ) -> pd.DataFrame:
        """
        Get historical data for a symbol.
        
        Args:
            symbol: Trading symbol
            start_date: Start date
            end_date: End date
            interval: Data interval
            
        Returns:
            DataFrame with OHLCV data
        """
        pass
        
    @abstractmethod
    async def stream_live_data(self, symbol: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream live data for a symbol.
        
        Args:
            symbol: Trading symbol
            
        Yields:
            Live data updates
        """
        pass


class TradovateDataSource(DataSource):
    """
    Tradovate data source for NQ futures data.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get('api_key')
        self.api_secret = config.get('api_secret')
        self.account_id = config.get('account_id')
        self.demo = config.get('demo', True)
        self.rest_url = config.get('rest_url', 'https://demo.tradovateapi.com/v1')
        self.websocket_url = config.get('websocket_url', 'wss://demo.tradovateapi.com/v1/websocket')
        self.session = None
        self.websocket = None
        self.access_token = None
        
    async def connect(self) -> None:
        """Connect to Tradovate API."""
        try:
            # Create HTTP session
            self.session = aiohttp.ClientSession()
            
            # Authenticate
            await self._authenticate()
            
            self.is_connected = True
            logger.info("Connected to Tradovate API")
            
        except Exception as e:
            logger.error(f"Failed to connect to Tradovate: {e}")
            raise
            
    async def disconnect(self) -> None:
        """Disconnect from Tradovate API."""
        if self.websocket:
            await self.websocket.close()
            
        if self.session:
            await self.session.close()
            
        self.is_connected = False
        logger.info("Disconnected from Tradovate API")
        
    async def _authenticate(self) -> None:
        """Authenticate with Tradovate API."""
        auth_data = {
            "name": self.api_key,
            "password": self.api_secret,
            "appId": "NQTradingAgent",
            "appVersion": "1.0.0",
            "cid": 1
        }
        
        async with self.session.post(
            f"{self.rest_url}/auth/accesstokenrequest",
            json=auth_data
        ) as response:
            if response.status == 200:
                result = await response.json()
                self.access_token = result.get('accessToken')
                logger.info("Authenticated with Tradovate API")
            else:
                raise Exception(f"Authentication failed: {response.status}")
                
    async def get_historical_data(
        self, 
        symbol: str, 
        start_date: datetime, 
        end_date: datetime,
        interval: str = "1m"
    ) -> pd.DataFrame:
        """
        Get historical data from Tradovate.
        """
        if not self.is_connected:
            await self.connect()
            
        # Convert interval to Tradovate format
        interval_map = {
            "1m": "1min",
            "5m": "5min",
            "15m": "15min",
            "1h": "1hour",
            "1d": "1day"
        }
        
        tradovate_interval = interval_map.get(interval, "1min")
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        params = {
            "symbol": symbol,
            "chartDescription": {
                "underlyingType": "Future",
                "elementSize": tradovate_interval,
                "elementSizeUnit": "UnderlyingUnits"
            },
            "timeRange": {
                "asMuchAsElements": 1000,
                "closestTimestamp": int(end_date.timestamp() * 1000)
            }
        }
        
        try:
            async with self.session.post(
                f"{self.rest_url}/md/getchart",
                headers=headers,
                json=params
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._process_chart_data(data)
                else:
                    raise Exception(f"Failed to get historical data: {response.status}")
                    
        except Exception as e:
            logger.error(f"Error getting historical data: {e}")
            raise
            
    def _process_chart_data(self, data: Dict[str, Any]) -> pd.DataFrame:
        """Process Tradovate chart data into DataFrame."""
        bars = data.get('bars', [])
        
        if not bars:
            return pd.DataFrame()
            
        df_data = []
        for bar in bars:
            df_data.append({
                'timestamp': pd.to_datetime(bar['timestamp'], unit='ms'),
                'open': bar['open'],
                'high': bar['high'],
                'low': bar['low'],
                'close': bar['close'],
                'volume': bar['upVolume'] + bar['downVolume']
            })
            
        df = pd.DataFrame(df_data)
        df.set_index('timestamp', inplace=True)
        return df
        
    async def stream_live_data(self, symbol: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream live data from Tradovate WebSocket.
        """
        if not self.is_connected:
            await self.connect()
            
        try:
            self.websocket = await websockets.connect(self.websocket_url)
            
            # Subscribe to real-time data
            subscribe_msg = {
                "url": f"md/subscribeQuote",
                "body": {
                    "symbol": symbol
                }
            }
            
            await self.websocket.send(json.dumps(subscribe_msg))
            
            async for message in self.websocket:
                data = json.loads(message)
                if data.get('e') == 'md' and data.get('d'):
                    yield self._process_quote_data(data['d'])
                    
        except Exception as e:
            logger.error(f"Error streaming live data: {e}")
            raise
            
    def _process_quote_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process Tradovate quote data."""
        return {
            'timestamp': pd.to_datetime(data['timestamp'], unit='ms'),
            'symbol': data['symbol'],
            'bid': data.get('bid'),
            'ask': data.get('ask'),
            'last': data.get('last'),
            'volume': data.get('totalVolume')
        }


class YahooDataSource(DataSource):
    """
    Yahoo Finance data source for NQ futures data.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.symbol = config.get('symbol', 'NQ=F')
        self.interval = config.get('interval', '1m')
        
    async def connect(self) -> None:
        """Connect to Yahoo Finance (no authentication needed)."""
        self.is_connected = True
        logger.info("Connected to Yahoo Finance")
        
    async def disconnect(self) -> None:
        """Disconnect from Yahoo Finance."""
        self.is_connected = False
        logger.info("Disconnected from Yahoo Finance")
        
    async def get_historical_data(
        self, 
        symbol: str, 
        start_date: datetime, 
        end_date: datetime,
        interval: str = "1m"
    ) -> pd.DataFrame:
        """
        Get historical data from Yahoo Finance.
        """
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(
                start=start_date,
                end=end_date,
                interval=interval
            )
            
            # Rename columns to match our standard format
            data.columns = data.columns.str.lower()
            
            # Yahoo Finance data already has DatetimeIndex, just ensure it's named 'timestamp'
            if data.index.name != 'timestamp':
                data.index.name = 'timestamp'
            
            return data
            
        except Exception as e:
            logger.error(f"Error getting Yahoo Finance data: {e}")
            raise
            
    async def stream_live_data(self, symbol: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Simulate live data streaming from Yahoo Finance.
        """
        # Yahoo Finance doesn't provide real-time streaming
        # This is a simulation for testing purposes
        while True:
            try:
                # Get latest data
                ticker = yf.Ticker(symbol)
                data = ticker.history(period="1d", interval="1m")
                
                if not data.empty:
                    latest = data.iloc[-1]
                    yield {
                        'timestamp': pd.Timestamp.now(),
                        'symbol': symbol,
                        'open': latest['Open'],
                        'high': latest['High'],
                        'low': latest['Low'],
                        'close': latest['Close'],
                        'volume': latest['Volume']
                    }
                    
                await asyncio.sleep(60)  # Update every minute
                
            except Exception as e:
                logger.error(f"Error streaming Yahoo data: {e}")
                await asyncio.sleep(60)


class MockDataSource(DataSource):
    """
    Mock data source for testing.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.volatility = config.get('volatility', 0.02)
        self.starting_price = config.get('starting_price', 15000.0)
        self.current_price = self.starting_price
        
    async def connect(self) -> None:
        """Connect to mock data source."""
        self.is_connected = True
        logger.info("Connected to mock data source")
        
    async def disconnect(self) -> None:
        """Disconnect from mock data source."""
        self.is_connected = False
        logger.info("Disconnected from mock data source")
        
    async def get_historical_data(
        self, 
        symbol: str, 
        start_date: datetime, 
        end_date: datetime,
        interval: str = "1m"
    ) -> pd.DataFrame:
        """
        Generate mock historical data.
        """
        # Calculate number of periods
        if interval == "1m":
            delta = timedelta(minutes=1)
        elif interval == "5m":
            delta = timedelta(minutes=5)
        elif interval == "15m":
            delta = timedelta(minutes=15)
        elif interval == "1h":
            delta = timedelta(hours=1)
        elif interval == "1d":
            delta = timedelta(days=1)
        else:
            delta = timedelta(minutes=1)
            
        periods = int((end_date - start_date) / delta)
        
        # Generate random walk data
        np.random.seed(42)  # For reproducible results
        returns = np.random.normal(0, self.volatility / np.sqrt(periods), periods)
        prices = [self.starting_price]
        
        for i in range(1, periods):
            prices.append(prices[-1] * (1 + returns[i]))
            
        # Create OHLCV data
        timestamps = pd.date_range(start=start_date, end=end_date, freq=delta)[:periods]
        
        data = []
        for i, (timestamp, price) in enumerate(zip(timestamps, prices)):
            # Add some randomness to OHLC
            noise = np.random.normal(0, self.volatility * 0.1)
            high = price * (1 + abs(noise))
            low = price * (1 - abs(noise))
            
            data.append({
                'timestamp': timestamp,
                'open': price,
                'high': high,
                'low': low,
                'close': price,
                'volume': np.random.randint(1000, 10000)
            })
            
        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        return df
        
    async def stream_live_data(self, symbol: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generate mock live data stream.
        """
        while True:
            try:
                # Generate random price movement
                change = np.random.normal(0, self.volatility * 0.01)
                self.current_price *= (1 + change)
                
                # Add some noise for OHLC
                noise = np.random.normal(0, self.volatility * 0.001)
                high = self.current_price * (1 + abs(noise))
                low = self.current_price * (1 - abs(noise))
                
                yield {
                    'timestamp': pd.Timestamp.now(),
                    'symbol': symbol,
                    'open': self.current_price,
                    'high': high,
                    'low': low,
                    'close': self.current_price,
                    'volume': np.random.randint(100, 1000)
                }
                
                await asyncio.sleep(1)  # Update every second
                
            except Exception as e:
                logger.error(f"Error generating mock data: {e}")
                await asyncio.sleep(1)


class DataIngestion:
    """
    Main data ingestion class that manages different data sources.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize data ingestion.
        
        Args:
            config: Data configuration
        """
        self.config = config
        self.data_source = self._create_data_source()
        
    def _create_data_source(self) -> DataSource:
        """Create the appropriate data source based on configuration."""
        source_type = self.config.get('source', 'mock')
        
        if source_type == 'tradovate':
            return TradovateDataSource(self.config.get('tradovate', {}))
        elif source_type == 'yahoo':
            return YahooDataSource(self.config.get('yahoo', {}))
        elif source_type == 'mock':
            return MockDataSource(self.config.get('mock', {}))
        else:
            raise ValueError(f"Unsupported data source: {source_type}")
            
    async def connect(self) -> None:
        """Connect to the data source."""
        await self.data_source.connect()
        
    async def disconnect(self) -> None:
        """Disconnect from the data source."""
        await self.data_source.disconnect()
        
    async def get_historical_data(
        self, 
        symbol: str, 
        start_date: datetime, 
        end_date: datetime,
        interval: str = "1m"
    ) -> pd.DataFrame:
        """
        Get historical data.
        
        Args:
            symbol: Trading symbol
            start_date: Start date
            end_date: End date
            interval: Data interval
            
        Returns:
            DataFrame with OHLCV data
        """
        return await self.data_source.get_historical_data(
            symbol, start_date, end_date, interval
        )
        
    async def stream_live_data(self, symbol: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream live data.
        
        Args:
            symbol: Trading symbol
            
        Yields:
            Live data updates
        """
        async for data in self.data_source.stream_live_data(symbol):
            yield data
            
    def get_nq_config(self) -> Dict[str, Any]:
        """Get NQ contract configuration."""
        return self.config.get('nq', {
            'symbol': 'NQ',
            'exchange': 'CME',
            'tick_size': 0.25,
            'tick_value': 5.0,
            'contract_size': 20,
            'margin_requirement': 16500
        })