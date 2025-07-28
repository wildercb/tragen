"""
Professional Chart Data Manager for Trading Platform
===================================================

Advanced chart data management with multiple data sources, real-time streaming,
intelligent caching, and professional-grade data processing.
"""

import asyncio
import logging
import json
import time
from typing import Dict, List, Any, Optional, Set, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import aiohttp
import pandas as pd
import numpy as np
from collections import defaultdict, deque
import yfinance as yf
import redis.asyncio as redis
from .websocket import EnhancedWebSocketManager, MessagePriority, ConnectionType

logger = logging.getLogger(__name__)

class DataSource(Enum):
    YAHOO_FINANCE = "yahoo_finance"
    ALPHA_VANTAGE = "alpha_vantage"
    POLYGON_IO = "polygon_io"
    TRADINGVIEW = "tradingview"
    BINANCE = "binance"
    MOCK = "mock"
    CACHE = "cache"

class DataQuality(Enum):
    EXCELLENT = "excellent"  # < 100ms latency, < 0.1% missing data
    GOOD = "good"           # < 500ms latency, < 1% missing data
    FAIR = "fair"           # < 2s latency, < 5% missing data
    POOR = "poor"           # > 2s latency, > 5% missing data

@dataclass
class MarketData:
    """Professional market data structure"""
    symbol: str
    timeframe: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    source: DataSource
    quality: DataQuality
    latency_ms: float
    indicators: Optional[Dict[str, float]] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class DataStream:
    """Real-time data stream configuration"""
    symbol: str
    timeframe: str
    source: DataSource
    update_interval: float  # seconds
    is_active: bool
    last_update: datetime
    error_count: int
    quality_score: float

class ChartDataManager:
    """
    Professional-grade chart data manager for high-frequency trading platform.
    
    Features:
    - Multiple data source integration with automatic failover
    - Real-time data streaming with sub-second updates
    - Intelligent caching and data validation
    - Quality monitoring and source selection
    - WebSocket integration for live updates
    - Professional technical indicators
    """
    
    def __init__(self, websocket_manager: EnhancedWebSocketManager, 
                 redis_client: Optional[redis.Redis] = None):
        self.ws_manager = websocket_manager
        self.redis_client = redis_client
        
        # Data source configuration
        self.data_sources = {
            DataSource.YAHOO_FINANCE: {
                'enabled': True,
                'priority': 1,
                'rate_limit': 200,  # requests per minute
                'quality_score': 0.8,
                'supports_realtime': True
            },
            DataSource.ALPHA_VANTAGE: {
                'enabled': False,  # Requires API key
                'priority': 2,
                'rate_limit': 500,
                'quality_score': 0.9,
                'supports_realtime': True
            },
            DataSource.POLYGON_IO: {
                'enabled': False,  # Requires API key
                'priority': 3,
                'rate_limit': 1000,
                'quality_score': 0.95,
                'supports_realtime': True
            },
            DataSource.TRADINGVIEW: {
                'enabled': False,  # Requires special setup
                'priority': 4,
                'rate_limit': 100,
                'quality_score': 0.99,
                'supports_realtime': True
            }
        }
        
        # Active data streams
        self.active_streams: Dict[str, DataStream] = {}
        self.stream_tasks: Dict[str, asyncio.Task] = {}
        
        # Data storage and caching
        self.live_data: Dict[str, deque] = defaultdict(lambda: deque(maxlen=5000))
        self.indicators_cache: Dict[str, Dict[str, Any]] = {}
        
        # Quality monitoring
        self.source_metrics: Dict[DataSource, Dict[str, float]] = defaultdict(dict)
        self.data_validators: List[Callable] = []
        
        # Rate limiting
        self.source_rate_limits: Dict[DataSource, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Background tasks
        self.background_tasks: Set[asyncio.Task] = set()
        self.is_running = False
        
        logger.info("Chart Data Manager initialized")
    
    async def start(self):
        """Start the chart data manager."""
        if self.is_running:
            return
        
        self.is_running = True
        
        # Start background tasks
        quality_task = asyncio.create_task(self._monitor_data_quality())
        self.background_tasks.add(quality_task)
        quality_task.add_done_callback(self.background_tasks.discard)
        
        cache_task = asyncio.create_task(self._cache_cleanup_loop())
        self.background_tasks.add(cache_task)
        cache_task.add_done_callback(self.background_tasks.discard)
        
        logger.info("Chart Data Manager started")
    
    async def stop(self):
        """Stop the chart data manager."""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # Stop all data streams
        for stream_key in list(self.stream_tasks.keys()):
            await self.stop_data_stream(stream_key)
        
        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()
        
        if self.background_tasks:
            await asyncio.gather(*self.background_tasks, return_exceptions=True)
        
        self.background_tasks.clear()
        logger.info("Chart Data Manager stopped")
    
    async def get_chart_data(self, symbol: str, timeframe: str, 
                           period: str = "1d", 
                           include_indicators: bool = True,
                           preferred_source: Optional[DataSource] = None) -> Optional[Dict[str, Any]]:
        """Get chart data with intelligent source selection."""
        try:
            start_time = time.time()
            
            # Try cache first
            cache_key = f"chart:{symbol}:{timeframe}:{period}"
            cached_data = await self._get_cached_data(cache_key)
            
            if cached_data and self._is_cache_valid(cached_data, timeframe):
                logger.info(f"Cache hit for {symbol} {timeframe}")
                cached_data['source'] = DataSource.CACHE.value
                return cached_data
            
            # Select best available data source
            source = preferred_source or await self._select_best_source(symbol, timeframe)
            
            # Fetch data from selected source
            data = await self._fetch_from_source(source, symbol, timeframe, period)
            
            if not data:
                # Try fallback sources
                for fallback_source in self._get_fallback_sources(source):
                    data = await self._fetch_from_source(fallback_source, symbol, timeframe, period)
                    if data:
                        source = fallback_source
                        break
            
            if not data:
                logger.error(f"Failed to fetch data for {symbol} from all sources")
                return None
            
            # Process and validate data
            processed_data = await self._process_raw_data(data, symbol, timeframe, source)
            
            # Add technical indicators if requested
            if include_indicators and processed_data:
                processed_data['indicators'] = await self._calculate_indicators(processed_data['data'])
            
            # Cache the result
            if processed_data:
                await self._cache_data(cache_key, processed_data)
            
            # Update metrics
            latency = (time.time() - start_time) * 1000
            self._update_source_metrics(source, latency, len(processed_data.get('data', [])))
            
            return processed_data
            
        except Exception as e:
            logger.error(f"Error getting chart data for {symbol}: {e}")
            return None
    
    async def start_real_time_stream(self, symbol: str, timeframe: str, 
                                   update_interval: float = 1.0,
                                   preferred_source: Optional[DataSource] = None) -> str:
        """Start real-time data streaming for a symbol."""
        try:
            stream_key = f"{symbol}:{timeframe}"
            
            if stream_key in self.active_streams:
                logger.info(f"Stream already active for {stream_key}")
                return stream_key
            
            # Select best source for real-time data
            source = preferred_source or await self._select_best_realtime_source(symbol)
            
            # Create stream configuration
            stream = DataStream(
                symbol=symbol,
                timeframe=timeframe,
                source=source,
                update_interval=update_interval,
                is_active=True,
                last_update=datetime.now(),
                error_count=0,
                quality_score=0.0
            )
            
            self.active_streams[stream_key] = stream
            
            # Start streaming task
            task = asyncio.create_task(self._stream_data(stream_key))
            self.stream_tasks[stream_key] = task
            task.add_done_callback(lambda t: self.stream_tasks.pop(stream_key, None))
            
            logger.info(f"Started real-time stream for {stream_key} using {source.value}")
            return stream_key
            
        except Exception as e:
            logger.error(f"Failed to start stream for {symbol}: {e}")
            return None
    
    async def stop_data_stream(self, stream_key: str):
        """Stop a real-time data stream."""
        try:
            if stream_key in self.active_streams:
                self.active_streams[stream_key].is_active = False
                del self.active_streams[stream_key]
            
            if stream_key in self.stream_tasks:
                self.stream_tasks[stream_key].cancel()
                del self.stream_tasks[stream_key]
            
            logger.info(f"Stopped data stream: {stream_key}")
            
        except Exception as e:
            logger.error(f"Error stopping stream {stream_key}: {e}")
    
    async def _stream_data(self, stream_key: str):
        """Internal method to continuously stream data."""
        try:
            stream = self.active_streams[stream_key]
            
            while stream.is_active and self.is_running:
                try:
                    start_time = time.time()
                    
                    # Fetch latest data point
                    latest_data = await self._fetch_realtime_data(
                        stream.source, stream.symbol, stream.timeframe
                    )
                    
                    if latest_data:
                        # Store in live data buffer
                        self.live_data[stream_key].append(latest_data)
                        
                        # Broadcast to connected clients
                        await self.ws_manager.broadcast_json({
                            'type': 'market_data_update',
                            'stream_key': stream_key,
                            'symbol': stream.symbol,
                            'timeframe': stream.timeframe,
                            'data': asdict(latest_data),
                            'timestamp': datetime.now().isoformat()
                        }, subscription_type='market_data', priority=MessagePriority.HIGH)
                        
                        # Update stream metrics
                        latency = (time.time() - start_time) * 1000
                        stream.quality_score = self._calculate_quality_score(latency, latest_data)
                        stream.last_update = datetime.now()
                        stream.error_count = 0
                    else:
                        stream.error_count += 1
                        if stream.error_count > 5:
                            logger.warning(f"Too many errors for stream {stream_key}, considering source switch")
                    
                    # Wait for next update
                    await asyncio.sleep(stream.update_interval)
                    
                except Exception as e:
                    logger.error(f"Streaming error for {stream_key}: {e}")
                    stream.error_count += 1
                    await asyncio.sleep(stream.update_interval * 2)  # Back off on error
                    
        except asyncio.CancelledError:
            logger.info(f"Stream cancelled: {stream_key}")
        except Exception as e:
            logger.error(f"Fatal streaming error for {stream_key}: {e}")
    
    async def _fetch_from_source(self, source: DataSource, symbol: str, 
                               timeframe: str, period: str) -> Optional[List[Dict[str, Any]]]:
        """Fetch data from a specific source."""
        try:
            # Check rate limits
            if not await self._check_rate_limit(source):
                logger.warning(f"Rate limit exceeded for {source.value}")
                return None
            
            if source == DataSource.YAHOO_FINANCE:
                return await self._fetch_yahoo_finance(symbol, timeframe, period)
            elif source == DataSource.ALPHA_VANTAGE:
                return await self._fetch_alpha_vantage(symbol, timeframe, period)
            elif source == DataSource.POLYGON_IO:
                return await self._fetch_polygon_io(symbol, timeframe, period)
            elif source == DataSource.MOCK:
                return await self._generate_mock_data(symbol, timeframe, period)
            else:
                logger.warning(f"Unsupported data source: {source.value}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching from {source.value}: {e}")
            return None
    
    async def _fetch_yahoo_finance(self, symbol: str, timeframe: str, period: str) -> List[Dict[str, Any]]:
        """Fetch data from Yahoo Finance."""
        try:
            # Convert timeframe to Yahoo Finance format
            interval_map = {
                '1m': '1m', '3m': '3m', '5m': '5m', '15m': '15m', '30m': '30m',
                '1h': '1h', '2h': '2h', '4h': '4h', '6h': '6h', '12h': '12h',
                '1d': '1d', '1wk': '1wk', '1mo': '1mo'
            }
            
            yf_interval = interval_map.get(timeframe, '5m')
            
            # Fetch data
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period, interval=yf_interval)
            
            if hist.empty:
                return []
            
            # Convert to our format
            data = []
            for timestamp, row in hist.iterrows():
                data.append({
                    'date': timestamp.isoformat(),
                    'open': float(row['Open']),
                    'high': float(row['High']),
                    'low': float(row['Low']),
                    'close': float(row['Close']),
                    'volume': float(row['Volume'])
                })
            
            return data
            
        except Exception as e:
            logger.error(f"Yahoo Finance fetch error: {e}")
            return []
    
    async def _fetch_realtime_data(self, source: DataSource, symbol: str, 
                                 timeframe: str) -> Optional[MarketData]:
        """Fetch single real-time data point."""
        try:
            if source == DataSource.YAHOO_FINANCE:
                ticker = yf.Ticker(symbol)
                info = ticker.history(period='1d', interval='1m').iloc[-1]
                
                return MarketData(
                    symbol=symbol,
                    timeframe=timeframe,
                    timestamp=datetime.now(),
                    open=float(info['Open']),
                    high=float(info['High']),
                    low=float(info['Low']),
                    close=float(info['Close']),
                    volume=float(info['Volume']),
                    source=source,
                    quality=DataQuality.GOOD,
                    latency_ms=0.0
                )
            else:
                # Mock data for unsupported sources
                return await self._generate_mock_realtime_data(symbol, timeframe, source)
                
        except Exception as e:
            logger.error(f"Error fetching real-time data: {e}")
            return None
    
    async def _generate_mock_data(self, symbol: str, timeframe: str, period: str) -> List[Dict[str, Any]]:
        """Generate realistic mock data for testing."""
        try:
            # Determine number of data points based on timeframe and period
            timeframe_minutes = {
                '1m': 1, '3m': 3, '5m': 5, '15m': 15, '30m': 30,
                '1h': 60, '2h': 120, '4h': 240, '6h': 360, '12h': 720,
                '1d': 1440, '1wk': 10080, '1mo': 43200
            }
            
            period_days = {
                '1d': 1, '5d': 5, '1wk': 7, '1mo': 30, '3mo': 90,
                '6mo': 180, '1y': 365, '2y': 730, '5y': 1825, 'max': 3650
            }
            
            tf_minutes = timeframe_minutes.get(timeframe, 5)
            p_days = period_days.get(period, 1)
            
            total_minutes = p_days * 24 * 60
            num_points = min(total_minutes // tf_minutes, 2000)
            
            # Generate mock price data with realistic movements
            base_price = 23000.0 if 'NQ' in symbol else 100.0
            volatility = 0.02
            
            data = []
            current_price = base_price
            current_time = datetime.now() - timedelta(minutes=num_points * tf_minutes)
            
            for i in range(num_points):
                # Random walk with mean reversion
                change = np.random.normal(0, volatility) * current_price
                current_price = max(current_price + change, current_price * 0.95)
                
                # Generate OHLC
                high = current_price * (1 + abs(np.random.normal(0, 0.005)))
                low = current_price * (1 - abs(np.random.normal(0, 0.005)))
                open_price = current_price + np.random.normal(0, current_price * 0.001)
                
                data.append({
                    'date': current_time.isoformat(),
                    'open': round(open_price, 2),
                    'high': round(high, 2),
                    'low': round(low, 2),
                    'close': round(current_price, 2),
                    'volume': int(np.random.exponential(1000) + 100)
                })
                
                current_time += timedelta(minutes=tf_minutes)
            
            return data
            
        except Exception as e:
            logger.error(f"Error generating mock data: {e}")
            return []
    
    async def _generate_mock_realtime_data(self, symbol: str, timeframe: str, 
                                         source: DataSource) -> MarketData:
        """Generate mock real-time data point."""
        base_price = 23000.0 if 'NQ' in symbol else 100.0
        volatility = 0.001
        
        # Get last price from live data or use base
        stream_key = f"{symbol}:{timeframe}"
        if stream_key in self.live_data and self.live_data[stream_key]:
            last_data = self.live_data[stream_key][-1]
            base_price = last_data.close
        
        # Generate new price
        change = np.random.normal(0, volatility) * base_price
        new_price = base_price + change
        
        return MarketData(
            symbol=symbol,
            timeframe=timeframe,
            timestamp=datetime.now(),
            open=round(new_price + np.random.normal(0, new_price * 0.0001), 2),
            high=round(new_price * (1 + abs(np.random.normal(0, 0.0005))), 2),
            low=round(new_price * (1 - abs(np.random.normal(0, 0.0005))), 2),
            close=round(new_price, 2),
            volume=int(np.random.exponential(100) + 10),
            source=source,
            quality=DataQuality.GOOD,
            latency_ms=50.0
        )
    
    async def _process_raw_data(self, raw_data: List[Dict[str, Any]], 
                              symbol: str, timeframe: str, source: DataSource) -> Dict[str, Any]:
        """Process and validate raw data."""
        try:
            if not raw_data:
                return None
            
            # Validate data integrity
            valid_data = []
            for item in raw_data:
                if self._validate_ohlc_data(item):
                    valid_data.append(item)
            
            if not valid_data:
                logger.warning(f"No valid data points for {symbol}")
                return None
            
            # Calculate data quality
            quality = self._assess_data_quality(valid_data, timeframe)
            
            return {
                'symbol': symbol,
                'timeframe': timeframe,
                'source': source.value,
                'quality': quality.value,
                'data': valid_data,
                'timestamp': datetime.now().isoformat(),
                'count': len(valid_data)
            }
            
        except Exception as e:
            logger.error(f"Error processing raw data: {e}")
            return None
    
    def _validate_ohlc_data(self, data: Dict[str, Any]) -> bool:
        """Validate OHLC data integrity."""
        try:
            required_fields = ['open', 'high', 'low', 'close', 'volume']
            for field in required_fields:
                if field not in data or data[field] is None:
                    return False
            
            o, h, l, c, v = data['open'], data['high'], data['low'], data['close'], data['volume']
            
            # Basic OHLC validation
            if not (h >= max(o, c) and l <= min(o, c) and h >= l and v >= 0):
                return False
            
            # Check for reasonable values
            if any(x <= 0 for x in [o, h, l, c]):
                return False
            
            return True
            
        except Exception:
            return False
    
    def _assess_data_quality(self, data: List[Dict[str, Any]], timeframe: str) -> DataQuality:
        """Assess data quality based on completeness and consistency."""
        try:
            if len(data) < 10:
                return DataQuality.POOR
            
            # Check for missing data points
            expected_points = self._calculate_expected_points(timeframe, len(data))
            completeness = len(data) / expected_points if expected_points > 0 else 1.0
            
            # Check for price anomalies
            prices = [item['close'] for item in data]
            price_changes = [abs(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
            anomaly_threshold = 0.1  # 10% price change threshold
            anomalies = sum(1 for change in price_changes if change > anomaly_threshold)
            anomaly_rate = anomalies / len(price_changes) if price_changes else 0
            
            # Determine quality
            if completeness >= 0.99 and anomaly_rate <= 0.01:
                return DataQuality.EXCELLENT
            elif completeness >= 0.95 and anomaly_rate <= 0.05:
                return DataQuality.GOOD
            elif completeness >= 0.90 and anomaly_rate <= 0.10:
                return DataQuality.FAIR
            else:
                return DataQuality.POOR
                
        except Exception:
            return DataQuality.POOR
    
    def _calculate_expected_points(self, timeframe: str, actual_points: int) -> int:
        """Calculate expected number of data points for quality assessment."""
        # Simplified calculation - in production, this would consider market hours
        return actual_points  # Assume actual is expected for now
    
    async def _calculate_indicators(self, data: List[Dict[str, Any]]) -> Dict[str, List[float]]:
        """Calculate technical indicators for chart data."""
        try:
            if len(data) < 50:  # Need sufficient data for indicators
                return {}
            
            # Convert to pandas DataFrame for easier calculation
            df = pd.DataFrame(data)
            df['close'] = pd.to_numeric(df['close'])
            df['high'] = pd.to_numeric(df['high'])
            df['low'] = pd.to_numeric(df['low'])
            df['volume'] = pd.to_numeric(df['volume'])
            
            indicators = {}
            
            # Simple Moving Averages
            indicators['sma_20'] = df['close'].rolling(window=20).mean().fillna(0).tolist()
            indicators['sma_50'] = df['close'].rolling(window=50).mean().fillna(0).tolist()
            
            # Exponential Moving Averages
            indicators['ema_12'] = df['close'].ewm(span=12).mean().fillna(0).tolist()
            indicators['ema_26'] = df['close'].ewm(span=26).mean().fillna(0).tolist()
            
            # RSI
            indicators['rsi'] = self._calculate_rsi(df['close']).tolist()
            
            # MACD
            macd_line, signal_line, histogram = self._calculate_macd(df['close'])
            indicators['macd'] = macd_line.tolist()
            indicators['macd_signal'] = signal_line.tolist()
            indicators['macd_histogram'] = histogram.tolist()
            
            # Bollinger Bands
            bb_upper, bb_middle, bb_lower = self._calculate_bollinger_bands(df['close'])
            indicators['bb_upper'] = bb_upper.tolist()
            indicators['bb_middle'] = bb_middle.tolist()
            indicators['bb_lower'] = bb_lower.tolist()
            
            return indicators
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            return {}
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.fillna(50)
    
    def _calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
        """Calculate MACD indicator."""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line
        return macd_line.fillna(0), signal_line.fillna(0), histogram.fillna(0)
    
    def _calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std: float = 2):
        """Calculate Bollinger Bands."""
        middle = prices.rolling(window=period).mean()
        std_dev = prices.rolling(window=period).std()
        upper = middle + (std_dev * std)
        lower = middle - (std_dev * std)
        return upper.fillna(0), middle.fillna(0), lower.fillna(0)
    
    async def _select_best_source(self, symbol: str, timeframe: str) -> DataSource:
        """Select the best available data source based on quality and availability."""
        available_sources = [
            source for source, config in self.data_sources.items() 
            if config['enabled']
        ]
        
        if not available_sources:
            return DataSource.MOCK
        
        # Sort by priority and quality score
        available_sources.sort(
            key=lambda s: (self.data_sources[s]['priority'], -self.data_sources[s]['quality_score'])
        )
        
        return available_sources[0]
    
    async def _select_best_realtime_source(self, symbol: str) -> DataSource:
        """Select best source for real-time data."""
        realtime_sources = [
            source for source, config in self.data_sources.items()
            if config['enabled'] and config['supports_realtime']
        ]
        
        if not realtime_sources:
            return DataSource.MOCK
        
        return realtime_sources[0]
    
    def _get_fallback_sources(self, primary_source: DataSource) -> List[DataSource]:
        """Get fallback sources when primary fails."""
        all_sources = [s for s, config in self.data_sources.items() if config['enabled']]
        return [s for s in all_sources if s != primary_source]
    
    async def _check_rate_limit(self, source: DataSource) -> bool:
        """Check if source is within rate limits."""
        current_time = time.time()
        rate_limiter = self.source_rate_limits[source]
        config = self.data_sources.get(source, {})
        rate_limit = config.get('rate_limit', 100)
        
        # Clean old entries (last 60 seconds)
        minute_ago = current_time - 60
        while rate_limiter and rate_limiter[0] < minute_ago:
            rate_limiter.popleft()
        
        # Check rate limit
        if len(rate_limiter) >= rate_limit:
            return False
        
        rate_limiter.append(current_time)
        return True
    
    def _calculate_quality_score(self, latency_ms: float, data: MarketData) -> float:
        """Calculate quality score for real-time data."""
        # Base score
        score = 1.0
        
        # Penalize high latency
        if latency_ms > 100:
            score -= 0.1
        if latency_ms > 500:
            score -= 0.2
        if latency_ms > 1000:
            score -= 0.3
        
        # Check data validity
        if not self._validate_ohlc_data(asdict(data)):
            score -= 0.5
        
        return max(0.0, score)
    
    def _update_source_metrics(self, source: DataSource, latency_ms: float, data_points: int):
        """Update metrics for data source performance."""
        metrics = self.source_metrics[source]
        
        # Update moving averages
        metrics['avg_latency'] = metrics.get('avg_latency', 0) * 0.9 + latency_ms * 0.1
        metrics['total_requests'] = metrics.get('total_requests', 0) + 1
        metrics['total_data_points'] = metrics.get('total_data_points', 0) + data_points
        metrics['last_request'] = time.time()
    
    async def _get_cached_data(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get data from cache if available."""
        if not self.redis_client:
            return None
        
        try:
            cached = await self.redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.error(f"Cache read error: {e}")
        
        return None
    
    async def _cache_data(self, cache_key: str, data: Dict[str, Any], ttl: int = 300):
        """Cache data with TTL."""
        if not self.redis_client:
            return
        
        try:
            await self.redis_client.setex(
                cache_key, ttl, json.dumps(data, default=str)
            )
        except Exception as e:
            logger.error(f"Cache write error: {e}")
    
    def _is_cache_valid(self, cached_data: Dict[str, Any], timeframe: str) -> bool:
        """Check if cached data is still valid."""
        try:
            cached_time = datetime.fromisoformat(cached_data['timestamp'])
            now = datetime.now()
            
            # Cache validity based on timeframe
            validity_map = {
                '1m': 30,    # 30 seconds for 1-minute data
                '5m': 60,    # 1 minute for 5-minute data
                '15m': 300,  # 5 minutes for 15-minute data
                '1h': 900,   # 15 minutes for hourly data
                '1d': 3600   # 1 hour for daily data
            }
            
            max_age = validity_map.get(timeframe, 300)
            age = (now - cached_time).total_seconds()
            
            return age < max_age
            
        except Exception:
            return False
    
    async def _monitor_data_quality(self):
        """Background task to monitor data quality."""
        while self.is_running:
            try:
                # Check source health
                for source, metrics in self.source_metrics.items():
                    avg_latency = metrics.get('avg_latency', 0)
                    last_request = metrics.get('last_request', 0)
                    
                    # Disable source if too slow or inactive
                    if avg_latency > 5000:  # 5 seconds
                        self.data_sources[source]['enabled'] = False
                        logger.warning(f"Disabled {source.value} due to high latency: {avg_latency}ms")
                    elif time.time() - last_request > 3600:  # 1 hour inactive
                        # Re-enable for retry
                        self.data_sources[source]['enabled'] = True
                
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Quality monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def _cache_cleanup_loop(self):
        """Background task to clean up old cache entries."""
        while self.is_running:
            try:
                # Clean up live data buffers
                for stream_key in list(self.live_data.keys()):
                    # Keep only last 1000 points per stream
                    if len(self.live_data[stream_key]) > 1000:
                        # Remove oldest half
                        for _ in range(len(self.live_data[stream_key]) // 2):
                            self.live_data[stream_key].popleft()
                
                await asyncio.sleep(300)  # Clean every 5 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cache cleanup error: {e}")
                await asyncio.sleep(300)
    
    def get_stream_status(self) -> Dict[str, Any]:
        """Get status of all active streams."""
        return {
            'active_streams': len(self.active_streams),
            'streams': {
                key: {
                    'symbol': stream.symbol,
                    'timeframe': stream.timeframe,
                    'source': stream.source.value,
                    'update_interval': stream.update_interval,
                    'last_update': stream.last_update.isoformat(),
                    'error_count': stream.error_count,
                    'quality_score': stream.quality_score
                }
                for key, stream in self.active_streams.items()
            }
        }
    
    def get_source_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for all data sources."""
        return {
            source.value: metrics
            for source, metrics in self.source_metrics.items()
        }