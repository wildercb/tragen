"""
Tests for preprocessing functionality
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from ..preprocessing.features import FeatureExtractor
from ..preprocessing.summarizer import DataSummarizer


class TestFeatureExtractor:
    """Test feature extraction functionality."""
    
    def setup_method(self):
        """Setup test data and configuration."""
        self.config = {
            'indicators': {
                'sma': [20, 50],
                'ema': [12, 26],
                'rsi': [14],
                'macd': [12, 26, 9],
                'bollinger': [20, 2],
                'atr': [14],
                'volume_sma': [20]
            },
            'patterns': {
                'lookback_periods': 50,
                'min_pattern_strength': 0.7
            }
        }
        
        self.extractor = FeatureExtractor(self.config)
        
        # Create sample NQ futures data
        dates = pd.date_range(start='2023-01-01', periods=100, freq='1H')
        np.random.seed(42)  # For reproducible tests
        
        base_price = 15000
        price_changes = np.random.normal(0, 20, 100)
        prices = base_price + np.cumsum(price_changes)
        
        self.sample_data = pd.DataFrame({
            'open': prices + np.random.normal(0, 5, 100),
            'high': prices + np.abs(np.random.normal(10, 5, 100)),
            'low': prices - np.abs(np.random.normal(10, 5, 100)),
            'close': prices,
            'volume': np.random.randint(1000, 5000, 100)
        }, index=dates)
        
    def test_extract_technical_indicators(self):
        """Test technical indicator extraction."""
        indicators = self.extractor.extract_technical_indicators(self.sample_data)
        
        # Check that required indicators are present
        assert 'sma_20' in indicators
        assert 'sma_50' in indicators
        assert 'ema_12' in indicators
        assert 'ema_26' in indicators
        assert 'rsi_14' in indicators
        assert 'macd' in indicators
        assert 'macd_signal' in indicators
        assert 'bb_upper' in indicators
        assert 'bb_lower' in indicators
        assert 'atr_14' in indicators
        
        # Check that values are reasonable
        assert isinstance(indicators['sma_20'], (int, float))
        assert isinstance(indicators['rsi_14'], (int, float))
        assert 0 <= indicators['rsi_14'] <= 100  # RSI should be between 0 and 100
        assert indicators['atr_14'] > 0  # ATR should be positive
        
    def test_extract_patterns(self):
        """Test pattern extraction."""
        patterns = self.extractor.extract_patterns(self.sample_data)
        
        # Check that pattern detection runs without error
        assert isinstance(patterns, dict)
        
        # Check for expected pattern types
        expected_patterns = ['head_shoulders', 'flag', 'triangle', 'double_top', 'double_bottom', 'wedge']
        for pattern in expected_patterns:
            assert pattern in patterns
            assert isinstance(patterns[pattern], dict)
            assert 'detected' in patterns[pattern]
            assert 'confidence' in patterns[pattern]
            
    def test_extract_liquidity_features(self):
        """Test liquidity feature extraction."""
        liquidity = self.extractor.extract_liquidity_features(self.sample_data)
        
        assert isinstance(liquidity, dict)
        assert 'fair_value_gaps' in liquidity
        assert 'liquidity_grabs' in liquidity
        assert 'order_blocks' in liquidity
        assert 'imbalances' in liquidity
        
        # Check that features are lists
        assert isinstance(liquidity['fair_value_gaps'], list)
        assert isinstance(liquidity['liquidity_grabs'], list)
        
    def test_extract_statistical_levels(self):
        """Test statistical level extraction."""
        levels = self.extractor.extract_statistical_levels(self.sample_data)
        
        assert isinstance(levels, dict)
        assert 'support_resistance' in levels
        assert 'pivot_points' in levels
        assert 'vwap' in levels
        
        # Check VWAP calculation
        if 'vwap' in levels:
            assert isinstance(levels['vwap'], (int, float))
            assert levels['vwap'] > 0
            
    def test_extract_momentum_signals(self):
        """Test momentum signal extraction."""
        momentum = self.extractor.extract_momentum_signals(self.sample_data)
        
        assert isinstance(momentum, dict)
        assert 'price_momentum' in momentum
        assert 'volume_momentum' in momentum
        assert 'thrust_signals' in momentum
        assert 'breakout_signals' in momentum
        
    def test_extract_volume_features(self):
        """Test volume feature extraction."""
        volume = self.extractor.extract_volume_features(self.sample_data)
        
        assert isinstance(volume, dict)
        assert 'volume_spikes' in volume
        assert 'volume_trend' in volume
        assert 'obv' in volume
        
        # Check OBV calculation
        if 'obv' in volume:
            assert isinstance(volume['obv'], (int, float))
            
    def test_extract_all_features(self):
        """Test extraction of all features together."""
        features = self.extractor.extract_all_features(self.sample_data)
        
        assert isinstance(features, dict)
        
        # Check that all feature categories are present
        expected_categories = [
            'technical_indicators', 'patterns', 'liquidity', 
            'statistical_levels', 'momentum', 'volume'
        ]
        
        for category in expected_categories:
            assert category in features
            assert isinstance(features[category], dict)
            
    def test_insufficient_data(self):
        """Test handling of insufficient data."""
        # Create very small dataset
        small_data = self.sample_data.head(5)
        
        # Should not crash with insufficient data
        indicators = self.extractor.extract_technical_indicators(small_data)
        
        # Some indicators may not be available with insufficient data
        assert isinstance(indicators, dict)
        
    def test_missing_columns(self):
        """Test handling of missing columns."""
        # Create data with missing volume column
        incomplete_data = self.sample_data[['open', 'high', 'low', 'close']].copy()
        
        # Should handle missing volume gracefully
        with pytest.raises(KeyError):
            self.extractor.extract_volume_features(incomplete_data)


class TestDataSummarizer:
    """Test data summarization functionality."""
    
    def setup_method(self):
        """Setup test data and configuration."""
        self.config = {
            'max_tokens': 200,
            'include_volume': True,
            'include_volatility': True,
            'include_momentum': True
        }
        
        self.summarizer = DataSummarizer(self.config)
        
        # Create sample market data
        dates = pd.date_range(start='2023-01-01', periods=50, freq='1H')
        prices = 15000 + np.cumsum(np.random.normal(0, 10, 50))
        
        self.sample_data = pd.DataFrame({
            'open': prices + np.random.normal(0, 2, 50),
            'high': prices + np.abs(np.random.normal(5, 2, 50)),
            'low': prices - np.abs(np.random.normal(5, 2, 50)),
            'close': prices,
            'volume': np.random.randint(1000, 3000, 50)
        }, index=dates)
        
        # Create sample features
        self.sample_features = {
            'technical_indicators': {
                'sma_20': 15050.0,
                'rsi_14': 65.0,
                'macd': 5.2,
                'macd_signal': 3.1,
                'bb_width': 0.015
            },
            'patterns': {
                'head_shoulders': {'detected': True, 'confidence': 0.8, 'type': 'head_shoulders'},
                'flag': {'detected': False, 'confidence': 0.3}
            },
            'liquidity': {
                'fair_value_gaps': [
                    {'type': 'bullish_fvg', 'start_price': 15020, 'end_price': 15040}
                ],
                'liquidity_grabs': []
            },
            'statistical_levels': {
                'support_resistance': {
                    'nearest_resistance': 15100.0,
                    'nearest_support': 15000.0
                },
                'vwap': 15025.0
            },
            'momentum': {
                'thrust_signals': [
                    {'type': 'thrust_signal', 'direction': 'bullish', 'price_change': 0.008}
                ]
            },
            'volume': {
                'volume_spikes': [],
                'volume_trend': {'volume_trend_direction': 'increasing'}
            }
        }
        
    def test_summarize_features(self):
        """Test feature summarization."""
        summary = self.summarizer.summarize_features(self.sample_features, self.sample_data)
        
        assert isinstance(summary, str)
        assert len(summary) > 0
        
        # Check that key information is included
        assert 'NQ' in summary
        assert any(word in summary.lower() for word in ['bullish', 'bearish', 'neutral'])
        
    def test_summarize_market_context(self):
        """Test market context summarization."""
        context = self.summarizer._summarize_market_context(self.sample_data)
        
        assert isinstance(context, str)
        assert 'NQ' in context
        assert any(word in context for word in ['bullish', 'bearish', 'neutral'])
        
    def test_summarize_technical_indicators(self):
        """Test technical indicator summarization."""
        indicators = self.sample_features['technical_indicators']
        summary = self.summarizer._summarize_technical_indicators(indicators)
        
        assert isinstance(summary, str)
        if summary:  # May be empty if no indicators
            assert 'Technicals:' in summary
            
    def test_summarize_patterns(self):
        """Test pattern summarization."""
        patterns = self.sample_features['patterns']
        summary = self.summarizer._summarize_patterns(patterns)
        
        assert isinstance(summary, str)
        if any(p.get('detected', False) for p in patterns.values()):
            assert 'Patterns:' in summary
            
    def test_create_trading_prompt(self):
        """Test trading prompt creation."""
        summary = "NQ at 15050.0, bullish trend (+0.15%), daily range 0.8%. Technicals: RSI overbought."
        current_price = 15050.0
        nq_config = {
            'tick_size': 0.25,
            'tick_value': 5.0
        }
        
        prompt = self.summarizer.create_trading_prompt(summary, current_price, nq_config)
        
        assert isinstance(prompt, str)
        assert 'NQ Futures Trading Analysis' in prompt
        assert 'Market Summary:' in prompt
        assert 'Current NQ Price:' in prompt
        assert 'ACTION:' in prompt
        assert 'CONFIDENCE:' in prompt
        
    def test_parse_llm_response(self):
        """Test LLM response parsing."""
        sample_response = """
        ACTION: BUY
        CONFIDENCE: 8
        ENTRY: 15050.25
        STOP_LOSS: 15025.00
        TAKE_PROFIT: 15100.00
        SIZE: 2
        REASONING: Strong bullish momentum with RSI confirmation and volume support.
        """
        
        signal = self.summarizer.parse_llm_response(sample_response)
        
        assert isinstance(signal, dict)
        assert signal['action'] == 'BUY'
        assert signal['confidence'] == 8
        assert signal['entry_price'] == 15050.25
        assert signal['stop_loss'] == 15025.00
        assert signal['take_profit'] == 15100.00
        assert signal['position_size'] == 2
        assert 'bullish momentum' in signal['reasoning'].lower()
        
    def test_parse_invalid_llm_response(self):
        """Test parsing of invalid LLM response."""
        invalid_response = "This is not a valid trading signal format."
        
        signal = self.summarizer.parse_llm_response(invalid_response)
        
        assert isinstance(signal, dict)
        assert signal['action'] == 'HOLD'
        assert signal['confidence'] == 0
        assert signal['entry_price'] is None
        
    def test_truncate_summary(self):
        """Test summary truncation."""
        # Create a very long summary
        long_summary = "This is a very long summary. " * 100
        
        truncated = self.summarizer._truncate_summary(long_summary)
        
        # Should be shorter than original
        assert len(truncated) < len(long_summary)
        
        # Should not exceed token limit (roughly)
        max_chars = self.config['max_tokens'] * 4
        assert len(truncated) <= max_chars + 10  # Small buffer for truncation logic
        
    def test_empty_features(self):
        """Test handling of empty features."""
        empty_features = {
            'technical_indicators': {},
            'patterns': {},
            'liquidity': {},
            'statistical_levels': {},
            'momentum': {},
            'volume': {}
        }
        
        summary = self.summarizer.summarize_features(empty_features, self.sample_data)
        
        assert isinstance(summary, str)
        assert len(summary) > 0  # Should at least have market context
        
    def test_token_efficiency(self):
        """Test that summaries are token-efficient."""
        summary = self.summarizer.summarize_features(self.sample_features, self.sample_data)
        
        # Estimate token count (rough approximation)
        estimated_tokens = len(summary) // 4
        
        # Should be within configured limit
        assert estimated_tokens <= self.config['max_tokens']
        
        # Should contain essential information efficiently
        assert 'NQ' in summary
        assert any(char.isdigit() for char in summary)  # Should contain numbers/prices