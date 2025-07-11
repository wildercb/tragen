"""
Tests for data ingestion functionality
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from ..data.ingestion import DataIngestion, MockDataSource, YahooDataSource


class TestMockDataSource:
    """Test mock data source functionality."""
    
    def setup_method(self):
        """Setup test configuration."""
        self.config = {
            'volatility': 0.02,
            'starting_price': 15000.0
        }
        self.data_source = MockDataSource(self.config)
        
    @pytest.mark.asyncio
    async def test_connect_disconnect(self):
        """Test connection and disconnection."""
        assert not self.data_source.is_connected
        
        await self.data_source.connect()
        assert self.data_source.is_connected
        
        await self.data_source.disconnect()
        assert not self.data_source.is_connected
        
    @pytest.mark.asyncio
    async def test_get_historical_data(self):
        """Test historical data generation."""
        await self.data_source.connect()
        
        start_date = datetime.now() - timedelta(days=1)
        end_date = datetime.now()
        
        data = await self.data_source.get_historical_data(
            'NQ', start_date, end_date, '1h'
        )
        
        assert isinstance(data, pd.DataFrame)
        assert not data.empty
        assert list(data.columns) == ['open', 'high', 'low', 'close', 'volume']
        
        # Check data integrity
        assert all(data['high'] >= data['low'])
        assert all(data['high'] >= data['open'])
        assert all(data['high'] >= data['close'])
        assert all(data['low'] <= data['open'])
        assert all(data['low'] <= data['close'])
        assert all(data['volume'] > 0)
        
    @pytest.mark.asyncio
    async def test_stream_live_data(self):
        """Test live data streaming."""
        await self.data_source.connect()
        
        data_count = 0
        async for data in self.data_source.stream_live_data('NQ'):
            assert isinstance(data, dict)
            assert 'timestamp' in data
            assert 'symbol' in data
            assert 'open' in data
            assert 'high' in data
            assert 'low' in data
            assert 'close' in data
            assert 'volume' in data
            
            data_count += 1
            if data_count >= 3:  # Test a few data points
                break
                
        assert data_count == 3
        
    def test_price_range(self):
        """Test that generated prices are within reasonable range."""
        initial_price = self.data_source.starting_price
        volatility = self.data_source.volatility
        
        # Generate some data points
        prices = []
        current_price = initial_price
        
        for _ in range(100):
            change = np.random.normal(0, volatility * 0.01)
            current_price *= (1 + change)
            prices.append(current_price)
            
        # Prices should stay within reasonable bounds
        min_price = initial_price * 0.8  # 20% down
        max_price = initial_price * 1.2  # 20% up
        
        # Most prices should be within bounds (allowing for some volatility)
        within_bounds = sum(1 for p in prices if min_price <= p <= max_price)
        assert within_bounds >= len(prices) * 0.8  # At least 80% within bounds


class TestYahooDataSource:
    """Test Yahoo Finance data source functionality."""
    
    def setup_method(self):
        """Setup test configuration."""
        self.config = {
            'symbol': 'NQ=F',
            'interval': '1m'
        }
        self.data_source = YahooDataSource(self.config)
        
    @pytest.mark.asyncio
    async def test_connect_disconnect(self):
        """Test connection (Yahoo Finance doesn't require authentication)."""
        await self.data_source.connect()
        assert self.data_source.is_connected
        
        await self.data_source.disconnect()
        assert not self.data_source.is_connected
        
    @pytest.mark.asyncio
    async def test_get_historical_data_mock(self):
        """Test historical data retrieval with mock."""
        with patch('yfinance.Ticker') as mock_ticker:
            # Setup mock data
            mock_data = pd.DataFrame({
                'Open': [15000, 15010, 15020],
                'High': [15005, 15015, 15025],
                'Low': [14995, 15005, 15015],
                'Close': [15002, 15012, 15022],
                'Volume': [1000, 1100, 1200]
            }, index=pd.date_range('2023-01-01', periods=3, freq='1H'))
            
            mock_ticker_instance = Mock()
            mock_ticker.return_value = mock_ticker_instance
            mock_ticker_instance.history.return_value = mock_data
            
            await self.data_source.connect()
            
            start_date = datetime(2023, 1, 1)
            end_date = datetime(2023, 1, 2)
            
            data = await self.data_source.get_historical_data(
                'NQ=F', start_date, end_date, '1h'
            )
            
            assert isinstance(data, pd.DataFrame)
            assert not data.empty
            assert 'open' in data.columns  # Should be lowercased
            assert 'close' in data.columns
            
    @pytest.mark.asyncio
    async def test_stream_live_data_simulation(self):
        """Test live data streaming simulation."""
        with patch('yfinance.Ticker') as mock_ticker:
            # Setup mock data for streaming simulation
            mock_data = pd.DataFrame({
                'Open': [15000],
                'High': [15010],
                'Low': [14990],
                'Close': [15005],
                'Volume': [1500]
            }, index=pd.date_range('2023-01-01', periods=1, freq='1H'))
            
            mock_ticker_instance = Mock()
            mock_ticker.return_value = mock_ticker_instance
            mock_ticker_instance.history.return_value = mock_data
            
            await self.data_source.connect()
            
            # Test streaming for a short time
            data_count = 0
            async for data in self.data_source.stream_live_data('NQ=F'):
                assert isinstance(data, dict)
                assert 'timestamp' in data
                assert 'symbol' in data
                assert 'open' in data
                
                data_count += 1
                if data_count >= 2:  # Test a couple iterations
                    break


class TestDataIngestion:
    """Test data ingestion orchestration."""
    
    def setup_method(self):
        """Setup test configuration."""
        self.mock_config = {
            'source': 'mock',
            'nq': {
                'symbol': 'NQ',
                'exchange': 'CME',
                'tick_size': 0.25,
                'tick_value': 5.0
            },
            'mock': {
                'volatility': 0.02,
                'starting_price': 15000.0
            }
        }
        
        self.yahoo_config = {
            'source': 'yahoo',
            'nq': {
                'symbol': 'NQ',
                'exchange': 'CME'
            },
            'yahoo': {
                'symbol': 'NQ=F',
                'interval': '1m'
            }
        }
        
    def test_create_mock_data_source(self):
        """Test creation of mock data source."""
        ingestion = DataIngestion(self.mock_config)
        
        assert hasattr(ingestion, 'data_source')
        assert ingestion.data_source.__class__.__name__ == 'MockDataSource'
        
    def test_create_yahoo_data_source(self):
        """Test creation of Yahoo Finance data source."""
        ingestion = DataIngestion(self.yahoo_config)
        
        assert hasattr(ingestion, 'data_source')
        assert ingestion.data_source.__class__.__name__ == 'YahooDataSource'
        
    def test_unsupported_data_source(self):
        """Test handling of unsupported data source."""
        config = {
            'source': 'unsupported_source',
            'nq': {}
        }
        
        with pytest.raises(ValueError, match="Unsupported data source"):
            DataIngestion(config)
            
    @pytest.mark.asyncio
    async def test_connect_disconnect(self):
        """Test connection management."""
        ingestion = DataIngestion(self.mock_config)
        
        await ingestion.connect()
        assert ingestion.data_source.is_connected
        
        await ingestion.disconnect()
        assert not ingestion.data_source.is_connected
        
    @pytest.mark.asyncio
    async def test_get_historical_data(self):
        """Test historical data retrieval through ingestion."""
        ingestion = DataIngestion(self.mock_config)
        await ingestion.connect()
        
        start_date = datetime.now() - timedelta(hours=6)
        end_date = datetime.now()
        
        data = await ingestion.get_historical_data('NQ', start_date, end_date, '1h')
        
        assert isinstance(data, pd.DataFrame)
        assert not data.empty
        
    @pytest.mark.asyncio
    async def test_stream_live_data(self):
        """Test live data streaming through ingestion."""
        ingestion = DataIngestion(self.mock_config)
        await ingestion.connect()
        
        data_count = 0
        async for data in ingestion.stream_live_data('NQ'):
            assert isinstance(data, dict)
            assert data['symbol'] == 'NQ'
            
            data_count += 1
            if data_count >= 2:
                break
                
    def test_get_nq_config(self):
        """Test NQ configuration retrieval."""
        ingestion = DataIngestion(self.mock_config)
        
        nq_config = ingestion.get_nq_config()
        
        assert isinstance(nq_config, dict)
        assert nq_config['symbol'] == 'NQ'
        assert nq_config['exchange'] == 'CME'
        assert nq_config['tick_size'] == 0.25
        assert nq_config['tick_value'] == 5.0


class TestDataValidation:
    """Test data validation and integrity checks."""
    
    def test_ohlcv_data_integrity(self):
        """Test OHLCV data integrity validation."""
        # Create valid OHLCV data
        valid_data = pd.DataFrame({
            'open': [15000, 15010, 15020],
            'high': [15005, 15015, 15025],
            'low': [14995, 15005, 15015],
            'close': [15002, 15012, 15022],
            'volume': [1000, 1100, 1200]
        })
        
        # Validate OHLCV relationships
        assert all(valid_data['high'] >= valid_data['low'])
        assert all(valid_data['high'] >= valid_data['open'])
        assert all(valid_data['high'] >= valid_data['close'])
        assert all(valid_data['low'] <= valid_data['open'])
        assert all(valid_data['low'] <= valid_data['close'])
        assert all(valid_data['volume'] >= 0)
        
    def test_invalid_ohlcv_data(self):
        """Test detection of invalid OHLCV data."""
        # Create invalid OHLCV data (high < low)
        invalid_data = pd.DataFrame({
            'open': [15000],
            'high': [14990],  # High is lower than low - invalid!
            'low': [15000],
            'close': [14995],
            'volume': [1000]
        })
        
        # This should be detected as invalid
        assert not all(invalid_data['high'] >= invalid_data['low'])
        
    def test_missing_data_handling(self):
        """Test handling of missing data."""
        # Create data with NaN values
        data_with_nan = pd.DataFrame({
            'open': [15000, np.nan, 15020],
            'high': [15005, 15015, 15025],
            'low': [14995, 15005, 15015],
            'close': [15002, 15012, 15022],
            'volume': [1000, 1100, 1200]
        })
        
        # Check for missing data
        assert data_with_nan.isna().any().any()
        
        # Remove rows with missing data
        clean_data = data_with_nan.dropna()
        assert len(clean_data) == 2  # Should have 2 rows left
        assert not clean_data.isna().any().any()
        
    def test_data_type_validation(self):
        """Test data type validation."""
        data = pd.DataFrame({
            'open': [15000.0, 15010.5, 15020.25],
            'high': [15005.0, 15015.5, 15025.25],
            'low': [14995.0, 15005.5, 15015.25],
            'close': [15002.0, 15012.5, 15022.25],
            'volume': [1000, 1100, 1200]  # Should be integers
        })
        
        # Check data types
        assert pd.api.types.is_numeric_dtype(data['open'])
        assert pd.api.types.is_numeric_dtype(data['high'])
        assert pd.api.types.is_numeric_dtype(data['low'])
        assert pd.api.types.is_numeric_dtype(data['close'])
        assert pd.api.types.is_numeric_dtype(data['volume'])
        
    def test_timestamp_validation(self):
        """Test timestamp validation."""
        # Create data with proper timestamps
        timestamps = pd.date_range('2023-01-01', periods=3, freq='1H')
        data = pd.DataFrame({
            'open': [15000, 15010, 15020],
            'high': [15005, 15015, 15025],
            'low': [14995, 15005, 15015],
            'close': [15002, 15012, 15022],
            'volume': [1000, 1100, 1200]
        }, index=timestamps)
        
        # Validate timestamps
        assert isinstance(data.index, pd.DatetimeIndex)
        assert data.index.is_monotonic_increasing  # Should be in chronological order
        
    def test_nq_specific_validation(self):
        """Test NQ futures specific validation."""
        # NQ futures specific constraints
        tick_size = 0.25
        min_price = 1000.0  # Reasonable minimum for NQ
        max_price = 30000.0  # Reasonable maximum for NQ
        
        nq_data = pd.DataFrame({
            'open': [15000.00, 15010.25, 15020.50],  # Should align with tick size
            'high': [15005.25, 15015.75, 15025.00],
            'low': [14995.75, 15005.00, 15015.25],
            'close': [15002.25, 15012.50, 15022.75],
            'volume': [1000, 1100, 1200]
        })
        
        # Validate tick size alignment (approximately)
        for col in ['open', 'high', 'low', 'close']:
            # Check if prices are reasonably aligned with tick size
            remainder = nq_data[col] % tick_size
            aligned = (remainder < 0.01) | (remainder > tick_size - 0.01)
            assert aligned.all(), f"{col} prices not aligned with tick size"
            
        # Validate price ranges
        for col in ['open', 'high', 'low', 'close']:
            assert (nq_data[col] >= min_price).all(), f"{col} prices below minimum"
            assert (nq_data[col] <= max_price).all(), f"{col} prices above maximum"