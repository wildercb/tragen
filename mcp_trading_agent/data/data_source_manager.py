"""
Production Data Source Manager
=============================

Multi-source data aggregation with consensus validation and quality scoring.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import aiohttp
import yfinance as yf
import pandas as pd
from decimal import Decimal

logger = logging.getLogger(__name__)

class DataSourceType(Enum):
    INTERACTIVE_BROKERS = "interactive_brokers"
    TRADINGVIEW = "tradingview"
    ALPHA_VANTAGE = "alpha_vantage"
    YAHOO_FINANCE = "yahoo_finance"
    BLOOMBERG = "bloomberg"
    POLYGON = "polygon"

@dataclass
class DataSourceConfig:
    source_type: DataSourceType
    priority: int  # 1 = highest priority
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    rate_limit: int = 100  # requests per minute
    timeout: int = 30
    enabled: bool = True
    backup_only: bool = False

@dataclass
class MarketDataPoint:
    symbol: str
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    source: DataSourceType
    quality_score: float
    latency_ms: int

@dataclass
class ConsensusData:
    symbol: str
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    quality_score: float
    source_count: int
    consensus_confidence: float
    sources_used: List[DataSourceType]

class DataSourceManager:
    """
    Production-grade data source manager with multi-source consensus.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.sources: Dict[DataSourceType, DataSourceConfig] = {}
        self.sessions: Dict[DataSourceType, aiohttp.ClientSession] = {}
        self.last_requests: Dict[DataSourceType, datetime] = {}
        self.error_counts: Dict[DataSourceType, int] = {}
        
        # Initialize data sources
        self._initialize_sources()
        
        # Cache for consensus data
        self.consensus_cache: Dict[str, ConsensusData] = {}
        self.cache_ttl = timedelta(seconds=30)
        
    def _initialize_sources(self):
        """Initialize all configured data sources."""
        source_configs = self.config.get('data_sources', {})
        
        # Interactive Brokers (highest priority for production)
        if source_configs.get('interactive_brokers', {}).get('enabled', False):
            self.sources[DataSourceType.INTERACTIVE_BROKERS] = DataSourceConfig(
                source_type=DataSourceType.INTERACTIVE_BROKERS,
                priority=1,
                api_key=source_configs['interactive_brokers'].get('api_key'),
                base_url=source_configs['interactive_brokers'].get('base_url'),
                rate_limit=200,
                timeout=10
            )
            
        # TradingView (second priority)
        if source_configs.get('tradingview', {}).get('enabled', False):
            self.sources[DataSourceType.TRADINGVIEW] = DataSourceConfig(
                source_type=DataSourceType.TRADINGVIEW,
                priority=2,
                api_key=source_configs['tradingview'].get('api_key'),
                base_url=source_configs['tradingview'].get('base_url'),
                rate_limit=100,
                timeout=15
            )
            
        # Alpha Vantage (backup)
        if source_configs.get('alpha_vantage', {}).get('enabled', False):
            self.sources[DataSourceType.ALPHA_VANTAGE] = DataSourceConfig(
                source_type=DataSourceType.ALPHA_VANTAGE,
                priority=3,
                api_key=source_configs['alpha_vantage'].get('api_key'),
                base_url="https://www.alphavantage.co/query",
                rate_limit=5,  # Free tier limit
                timeout=30
            )
            
        # Yahoo Finance (fallback only)
        self.sources[DataSourceType.YAHOO_FINANCE] = DataSourceConfig(
            source_type=DataSourceType.YAHOO_FINANCE,
            priority=9,
            rate_limit=2,  # Very conservative
            timeout=30,
            backup_only=True
        )
        
        logger.info(f"Initialized {len(self.sources)} data sources")
        
    async def get_consensus_data(
        self, 
        symbol: str, 
        timeframe: str = '1m',
        max_sources: int = 3
    ) -> ConsensusData:
        """
        Get consensus market data from multiple sources.
        
        Args:
            symbol: Trading symbol (e.g., 'NQ=F')
            timeframe: Data timeframe ('1m', '5m', '1h', '1d')
            max_sources: Maximum number of sources to query
            
        Returns:
            ConsensusData with validated, consensus market data
        """
        cache_key = f"{symbol}_{timeframe}_{max_sources}"
        
        # Check cache first
        if cache_key in self.consensus_cache:
            cached = self.consensus_cache[cache_key]
            if datetime.now() - cached.timestamp < self.cache_ttl:
                logger.debug(f"Returning cached consensus data for {symbol}")
                return cached
                
        # Get data from multiple sources
        data_points = await self._fetch_from_multiple_sources(
            symbol, timeframe, max_sources
        )
        
        if not data_points:
            raise ValueError(f"No valid data sources available for {symbol}")
            
        # Calculate consensus
        consensus = self._calculate_consensus(data_points)
        
        # Cache result
        self.consensus_cache[cache_key] = consensus
        
        logger.info(
            f"Generated consensus data for {symbol} from {len(data_points)} sources "
            f"(confidence: {consensus.consensus_confidence:.2f})"
        )
        
        return consensus
        
    async def _fetch_from_multiple_sources(
        self, 
        symbol: str, 
        timeframe: str, 
        max_sources: int
    ) -> List[MarketDataPoint]:
        """Fetch data from multiple sources in parallel."""
        
        # Sort sources by priority
        sorted_sources = sorted(
            [(source_type, config) for source_type, config in self.sources.items()
             if config.enabled and not (config.backup_only and max_sources > 1)],
            key=lambda x: x[1].priority
        )
        
        # Select top sources
        selected_sources = sorted_sources[:max_sources]
        
        # Fetch data in parallel
        tasks = []
        for source_type, config in selected_sources:
            if self._can_make_request(source_type):
                task = self._fetch_from_source(source_type, symbol, timeframe)
                tasks.append(task)
                
        if not tasks:
            logger.error(f"No sources available for {symbol} due to rate limits")
            return []
            
        # Execute requests
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter successful results
        valid_data_points = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                source_type = selected_sources[i][0]
                self._record_error(source_type, result)
                logger.error(f"Error fetching from {source_type}: {result}")
            elif result:
                valid_data_points.append(result)
                
        return valid_data_points
        
    async def _fetch_from_source(
        self, 
        source_type: DataSourceType, 
        symbol: str, 
        timeframe: str
    ) -> Optional[MarketDataPoint]:
        """Fetch data from a specific source."""
        
        start_time = datetime.now()
        
        try:
            if source_type == DataSourceType.YAHOO_FINANCE:
                data = await self._fetch_yahoo_finance(symbol, timeframe)
            elif source_type == DataSourceType.ALPHA_VANTAGE:
                data = await self._fetch_alpha_vantage(symbol, timeframe)
            elif source_type == DataSourceType.INTERACTIVE_BROKERS:
                data = await self._fetch_interactive_brokers(symbol, timeframe)
            elif source_type == DataSourceType.TRADINGVIEW:
                data = await self._fetch_tradingview(symbol, timeframe)
            else:
                logger.warning(f"Unsupported source type: {source_type}")
                return None
                
            if data:
                latency_ms = int((datetime.now() - start_time).total_seconds() * 1000)
                data.latency_ms = latency_ms
                data.source = source_type
                
                # Calculate quality score based on latency and source reliability
                data.quality_score = self._calculate_quality_score(data, source_type)
                
                self._record_successful_request(source_type)
                
                logger.debug(
                    f"Fetched data from {source_type} for {symbol} "
                    f"(latency: {latency_ms}ms, quality: {data.quality_score:.2f})"
                )
                
                return data
                
        except Exception as e:
            self._record_error(source_type, e)
            logger.error(f"Error fetching from {source_type} for {symbol}: {e}")
            
        return None
        
    async def _fetch_yahoo_finance(self, symbol: str, timeframe: str) -> Optional[MarketDataPoint]:
        """Fetch data from Yahoo Finance."""
        try:
            # Map our timeframe to yfinance period/interval
            period_map = {
                '1m': ('1d', '1m'),
                '5m': ('5d', '5m'),
                '15m': ('60d', '15m'),
                '1h': ('730d', '1h'),
                '1d': ('max', '1d')
            }
            
            period, interval = period_map.get(timeframe, ('1d', '1m'))
            
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period, interval=interval)
            
            if hist.empty:
                return None
                
            latest = hist.iloc[-1]
            
            return MarketDataPoint(
                symbol=symbol,
                timestamp=latest.name.to_pydatetime(),
                open=Decimal(str(latest['Open'])),
                high=Decimal(str(latest['High'])),
                low=Decimal(str(latest['Low'])),
                close=Decimal(str(latest['Close'])),
                volume=int(latest['Volume']),
                source=DataSourceType.YAHOO_FINANCE,
                quality_score=0.0,  # Will be calculated later
                latency_ms=0
            )
            
        except Exception as e:
            logger.error(f"Yahoo Finance error for {symbol}: {e}")
            return None
            
    async def _fetch_alpha_vantage(self, symbol: str, timeframe: str) -> Optional[MarketDataPoint]:
        """Fetch data from Alpha Vantage."""
        config = self.sources[DataSourceType.ALPHA_VANTAGE]
        
        if not config.api_key:
            logger.error("Alpha Vantage API key not configured")
            return None
            
        try:
            # Map timeframe to Alpha Vantage function
            function_map = {
                '1m': 'TIME_SERIES_INTRADAY',
                '5m': 'TIME_SERIES_INTRADAY',
                '15m': 'TIME_SERIES_INTRADAY',
                '1h': 'TIME_SERIES_INTRADAY',
                '1d': 'TIME_SERIES_DAILY'
            }
            
            function = function_map.get(timeframe, 'TIME_SERIES_INTRADAY')
            
            params = {
                'function': function,
                'symbol': symbol,
                'apikey': config.api_key,
                'outputsize': 'compact'
            }
            
            if function == 'TIME_SERIES_INTRADAY':
                params['interval'] = timeframe
                
            async with aiohttp.ClientSession() as session:
                async with session.get(config.base_url, params=params, timeout=config.timeout) as response:
                    if response.status != 200:
                        return None
                        
                    data = await response.json()
                    
                    # Parse Alpha Vantage response
                    if function == 'TIME_SERIES_INTRADAY':
                        time_series_key = f'Time Series ({timeframe})'
                    else:
                        time_series_key = 'Time Series (Daily)'
                        
                    if time_series_key not in data:
                        logger.error(f"Invalid Alpha Vantage response for {symbol}")
                        return None
                        
                    time_series = data[time_series_key]
                    latest_time = max(time_series.keys())
                    latest_data = time_series[latest_time]
                    
                    return MarketDataPoint(
                        symbol=symbol,
                        timestamp=datetime.fromisoformat(latest_time),
                        open=Decimal(latest_data['1. open']),
                        high=Decimal(latest_data['2. high']),
                        low=Decimal(latest_data['3. low']),
                        close=Decimal(latest_data['4. close']),
                        volume=int(latest_data['5. volume']),
                        source=DataSourceType.ALPHA_VANTAGE,
                        quality_score=0.0,
                        latency_ms=0
                    )
                    
        except Exception as e:
            logger.error(f"Alpha Vantage error for {symbol}: {e}")
            return None
            
    async def _fetch_interactive_brokers(self, symbol: str, timeframe: str) -> Optional[MarketDataPoint]:
        """Fetch data from Interactive Brokers (placeholder for IB API integration)."""
        # This would integrate with Interactive Brokers API
        # For now, return None to indicate not implemented
        logger.debug(f"Interactive Brokers integration not yet implemented for {symbol}")
        return None
        
    async def _fetch_tradingview(self, symbol: str, timeframe: str) -> Optional[MarketDataPoint]:
        """Fetch data from TradingView (placeholder for TradingView API integration)."""
        # This would integrate with TradingView's real-time data API
        # For now, return None to indicate not implemented
        logger.debug(f"TradingView integration not yet implemented for {symbol}")
        return None
        
    def _calculate_consensus(self, data_points: List[MarketDataPoint]) -> ConsensusData:
        """Calculate consensus from multiple data points."""
        if not data_points:
            raise ValueError("No data points to calculate consensus")
            
        if len(data_points) == 1:
            # Single source - use as is but lower confidence
            dp = data_points[0]
            return ConsensusData(
                symbol=dp.symbol,
                timestamp=dp.timestamp,
                open=dp.open,
                high=dp.high,
                low=dp.low,
                close=dp.close,
                volume=dp.volume,
                quality_score=dp.quality_score,
                source_count=1,
                consensus_confidence=0.7,  # Lower confidence for single source
                sources_used=[dp.source]
            )
            
        # Multiple sources - calculate weighted consensus
        total_weight = sum(dp.quality_score for dp in data_points)
        
        if total_weight == 0:
            # All sources have zero quality - use simple average
            weights = [1.0 / len(data_points)] * len(data_points)
        else:
            weights = [dp.quality_score / total_weight for dp in data_points]
            
        # Calculate weighted averages
        consensus_open = sum(float(dp.open) * w for dp, w in zip(data_points, weights))
        consensus_high = sum(float(dp.high) * w for dp, w in zip(data_points, weights))
        consensus_low = sum(float(dp.low) * w for dp, w in zip(data_points, weights))
        consensus_close = sum(float(dp.close) * w for dp, w in zip(data_points, weights))
        consensus_volume = sum(dp.volume * w for dp, w in zip(data_points, weights))
        
        # Calculate consensus confidence based on data point agreement
        consensus_confidence = self._calculate_consensus_confidence(data_points)
        
        # Use most recent timestamp
        latest_timestamp = max(dp.timestamp for dp in data_points)
        
        # Average quality score
        avg_quality = sum(dp.quality_score for dp in data_points) / len(data_points)
        
        return ConsensusData(
            symbol=data_points[0].symbol,
            timestamp=latest_timestamp,
            open=Decimal(str(round(consensus_open, 4))),
            high=Decimal(str(round(consensus_high, 4))),
            low=Decimal(str(round(consensus_low, 4))),
            close=Decimal(str(round(consensus_close, 4))),
            volume=int(consensus_volume),
            quality_score=avg_quality,
            source_count=len(data_points),
            consensus_confidence=consensus_confidence,
            sources_used=[dp.source for dp in data_points]
        )
        
    def _calculate_consensus_confidence(self, data_points: List[MarketDataPoint]) -> float:
        """Calculate confidence in consensus based on data point agreement."""
        if len(data_points) < 2:
            return 0.7
            
        # Calculate coefficient of variation for close prices
        closes = [float(dp.close) for dp in data_points]
        mean_close = sum(closes) / len(closes)
        
        if mean_close == 0:
            return 0.5
            
        variance = sum((close - mean_close) ** 2 for close in closes) / len(closes)
        std_dev = variance ** 0.5
        coefficient_of_variation = std_dev / mean_close
        
        # Convert to confidence (lower variation = higher confidence)
        confidence = max(0.5, 1.0 - (coefficient_of_variation * 10))
        
        # Bonus for more sources
        source_bonus = min(0.2, len(data_points) * 0.05)
        
        return min(1.0, confidence + source_bonus)
        
    def _calculate_quality_score(self, data: MarketDataPoint, source_type: DataSourceType) -> float:
        """Calculate quality score for a data point."""
        base_scores = {
            DataSourceType.INTERACTIVE_BROKERS: 1.0,
            DataSourceType.TRADINGVIEW: 0.9,
            DataSourceType.ALPHA_VANTAGE: 0.8,
            DataSourceType.YAHOO_FINANCE: 0.6,
            DataSourceType.BLOOMBERG: 1.0,
            DataSourceType.POLYGON: 0.8
        }
        
        base_score = base_scores.get(source_type, 0.5)
        
        # Adjust for latency (lower latency = higher quality)
        latency_factor = max(0.5, 1.0 - (data.latency_ms / 10000))  # Penalize >10s latency
        
        # Adjust for data freshness
        data_age = (datetime.now() - data.timestamp).total_seconds()
        freshness_factor = max(0.5, 1.0 - (data_age / 300))  # Penalize >5min old data
        
        # Adjust for error rate
        error_count = self.error_counts.get(source_type, 0)
        error_factor = max(0.5, 1.0 - (error_count / 100))  # Penalize high error rates
        
        return base_score * latency_factor * freshness_factor * error_factor
        
    def _can_make_request(self, source_type: DataSourceType) -> bool:
        """Check if we can make a request to this source (rate limiting)."""
        config = self.sources.get(source_type)
        if not config or not config.enabled:
            return False
            
        last_request = self.last_requests.get(source_type)
        if not last_request:
            return True
            
        time_since_last = (datetime.now() - last_request).total_seconds()
        min_interval = 60.0 / config.rate_limit  # Convert rate limit to minimum interval
        
        return time_since_last >= min_interval
        
    def _record_successful_request(self, source_type: DataSourceType):
        """Record a successful request for rate limiting and error tracking."""
        self.last_requests[source_type] = datetime.now()
        
        # Reset error count on successful request
        if source_type in self.error_counts:
            self.error_counts[source_type] = max(0, self.error_counts[source_type] - 1)
            
    def _record_error(self, source_type: DataSourceType, error: Exception):
        """Record an error for this source."""
        self.error_counts[source_type] = self.error_counts.get(source_type, 0) + 1
        
        # Disable source if too many errors
        if self.error_counts[source_type] > 10:
            self.sources[source_type].enabled = False
            logger.error(f"Disabled {source_type} due to excessive errors")
            
    def get_source_status(self) -> Dict[str, Any]:
        """Get status of all data sources."""
        status = {}
        
        for source_type, config in self.sources.items():
            last_request = self.last_requests.get(source_type)
            error_count = self.error_counts.get(source_type, 0)
            
            status[source_type.value] = {
                'enabled': config.enabled,
                'priority': config.priority,
                'backup_only': config.backup_only,
                'rate_limit': config.rate_limit,
                'last_request': last_request.isoformat() if last_request else None,
                'error_count': error_count,
                'can_make_request': self._can_make_request(source_type)
            }
            
        return status
        
    async def cleanup(self):
        """Cleanup resources."""
        for session in self.sessions.values():
            await session.close()
            
        self.sessions.clear()
        self.consensus_cache.clear()
        
        logger.info("DataSourceManager cleanup complete")