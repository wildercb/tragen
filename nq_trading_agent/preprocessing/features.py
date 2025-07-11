"""
Feature extraction module for NQ futures trading
"""

import pandas as pd
import numpy as np
import pandas_ta as ta
from typing import Dict, Any, List, Optional, Tuple
import logging

try:
    import talib
    TALIB_AVAILABLE = True
except ImportError:
    TALIB_AVAILABLE = False
    logging.warning("TA-Lib not available. Some features may be limited.")

logger = logging.getLogger(__name__)


class FeatureExtractor:
    """
    Extract trading features from NQ futures data including patterns, levels, and signals.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize feature extractor.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.indicators_config = config.get('indicators', {})
        self.patterns_config = config.get('patterns', {})
        
    def extract_all_features(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Extract all features from the data.
        
        Args:
            data: OHLCV DataFrame
            
        Returns:
            Dictionary containing all extracted features
        """
        features = {}
        
        # Technical indicators
        features.update(self.extract_technical_indicators(data))
        
        # Pattern recognition
        features.update(self.extract_patterns(data))
        
        # Liquidity analysis
        features.update(self.extract_liquidity_features(data))
        
        # Statistical levels
        features.update(self.extract_statistical_levels(data))
        
        # Momentum and thrust signals
        features.update(self.extract_momentum_signals(data))
        
        # Volume analysis
        features.update(self.extract_volume_features(data))
        
        return features
        
    def extract_technical_indicators(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Extract technical indicators.
        
        Args:
            data: OHLCV DataFrame
            
        Returns:
            Dictionary of technical indicators
        """
        indicators = {}
        
        try:
            # Simple Moving Averages
            sma_periods = self.indicators_config.get('sma', [20, 50, 200])
            for period in sma_periods:
                if len(data) >= period:
                    indicators[f'sma_{period}'] = ta.sma(data['close'], length=period).iloc[-1]
                    
            # Exponential Moving Averages
            ema_periods = self.indicators_config.get('ema', [12, 26])
            for period in ema_periods:
                if len(data) >= period:
                    indicators[f'ema_{period}'] = ta.ema(data['close'], length=period).iloc[-1]
                    
            # RSI
            rsi_periods = self.indicators_config.get('rsi', [14])
            for period in rsi_periods:
                if len(data) >= period:
                    indicators[f'rsi_{period}'] = ta.rsi(data['close'], length=period).iloc[-1]
                    
            # MACD
            macd_config = self.indicators_config.get('macd', [12, 26, 9])
            if len(data) >= max(macd_config):
                macd = ta.macd(data['close'], fast=macd_config[0], slow=macd_config[1], signal=macd_config[2])
                indicators['macd'] = macd['MACD_12_26_9'].iloc[-1]
                indicators['macd_signal'] = macd['MACDs_12_26_9'].iloc[-1]
                indicators['macd_histogram'] = macd['MACDh_12_26_9'].iloc[-1]
                
            # Bollinger Bands
            bb_config = self.indicators_config.get('bollinger', [20, 2])
            if len(data) >= bb_config[0]:
                bb = ta.bbands(data['close'], length=bb_config[0], std=bb_config[1])
                indicators['bb_upper'] = bb[f'BBU_{bb_config[0]}_{bb_config[1]}'].iloc[-1]
                indicators['bb_middle'] = bb[f'BBM_{bb_config[0]}_{bb_config[1]}'].iloc[-1]
                indicators['bb_lower'] = bb[f'BBL_{bb_config[0]}_{bb_config[1]}'].iloc[-1]
                indicators['bb_width'] = (indicators['bb_upper'] - indicators['bb_lower']) / indicators['bb_middle']
                
            # ATR
            atr_periods = self.indicators_config.get('atr', [14])
            for period in atr_periods:
                if len(data) >= period:
                    indicators[f'atr_{period}'] = ta.atr(data['high'], data['low'], data['close'], length=period).iloc[-1]
                    
            # Volume SMA
            vol_sma_periods = self.indicators_config.get('volume_sma', [20])
            for period in vol_sma_periods:
                if len(data) >= period:
                    indicators[f'volume_sma_{period}'] = ta.sma(data['volume'], length=period).iloc[-1]
                    
        except Exception as e:
            logger.error(f"Error extracting technical indicators: {e}")
            
        return indicators
        
    def extract_patterns(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Extract chart patterns.
        
        Args:
            data: OHLCV DataFrame
            
        Returns:
            Dictionary of pattern features
        """
        patterns = {}
        
        try:
            lookback = self.patterns_config.get('lookback_periods', 50)
            min_strength = self.patterns_config.get('min_pattern_strength', 0.7)
            
            if len(data) >= lookback:
                recent_data = data.tail(lookback)
                
                # Head and Shoulders
                patterns['head_shoulders'] = self._detect_head_shoulders(recent_data)
                
                # Flags and Pennants
                patterns['flag'] = self._detect_flag(recent_data)
                
                # Triangles
                patterns['triangle'] = self._detect_triangle(recent_data)
                
                # Double Top/Bottom
                patterns['double_top'] = self._detect_double_top(recent_data)
                patterns['double_bottom'] = self._detect_double_bottom(recent_data)
                
                # Wedges
                patterns['wedge'] = self._detect_wedge(recent_data)
                
        except Exception as e:
            logger.error(f"Error extracting patterns: {e}")
            
        return patterns
        
    def extract_liquidity_features(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Extract liquidity-based features.
        
        Args:
            data: OHLCV DataFrame
            
        Returns:
            Dictionary of liquidity features
        """
        liquidity = {}
        
        try:
            # Fair Value Gaps
            liquidity['fair_value_gaps'] = self._detect_fair_value_gaps(data)
            
            # Liquidity Grabs
            liquidity['liquidity_grabs'] = self._detect_liquidity_grabs(data)
            
            # Order Blocks
            liquidity['order_blocks'] = self._detect_order_blocks(data)
            
            # Imbalances
            liquidity['imbalances'] = self._detect_imbalances(data)
            
        except Exception as e:
            logger.error(f"Error extracting liquidity features: {e}")
            
        return liquidity
        
    def extract_statistical_levels(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Extract statistical support/resistance levels.
        
        Args:
            data: OHLCV DataFrame
            
        Returns:
            Dictionary of statistical levels
        """
        levels = {}
        
        try:
            # Support and Resistance
            levels['support_resistance'] = self._calculate_support_resistance(data)
            
            # Pivot Points
            levels['pivot_points'] = self._calculate_pivot_points(data)
            
            # VWAP
            levels['vwap'] = self._calculate_vwap(data)
            
            # Volume Profile
            levels['volume_profile'] = self._calculate_volume_profile(data)
            
        except Exception as e:
            logger.error(f"Error extracting statistical levels: {e}")
            
        return levels
        
    def extract_momentum_signals(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Extract momentum and thrust signals.
        
        Args:
            data: OHLCV DataFrame
            
        Returns:
            Dictionary of momentum signals
        """
        momentum = {}
        
        try:
            # Price momentum
            momentum['price_momentum'] = self._calculate_price_momentum(data)
            
            # Volume momentum
            momentum['volume_momentum'] = self._calculate_volume_momentum(data)
            
            # Thrust signals
            momentum['thrust_signals'] = self._detect_thrust_signals(data)
            
            # Breakout signals
            momentum['breakout_signals'] = self._detect_breakout_signals(data)
            
        except Exception as e:
            logger.error(f"Error extracting momentum signals: {e}")
            
        return momentum
        
    def extract_volume_features(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Extract volume-based features.
        
        Args:
            data: OHLCV DataFrame
            
        Returns:
            Dictionary of volume features
        """
        volume = {}
        
        try:
            # Volume spikes
            volume['volume_spikes'] = self._detect_volume_spikes(data)
            
            # Volume trend
            volume['volume_trend'] = self._calculate_volume_trend(data)
            
            # On-Balance Volume
            volume['obv'] = ta.obv(data['close'], data['volume']).iloc[-1]
            
            # Volume Rate of Change
            volume['vroc'] = ta.roc(data['volume'], length=10).iloc[-1]
            
        except Exception as e:
            logger.error(f"Error extracting volume features: {e}")
            
        return volume
        
    def _detect_head_shoulders(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Detect head and shoulders pattern."""
        try:
            highs = data['high'].values
            lows = data['low'].values
            
            # Find peaks and troughs
            peaks = self._find_peaks(highs)
            troughs = self._find_troughs(lows)
            
            # Look for head and shoulders structure
            if len(peaks) >= 3:
                # Check if middle peak is highest (head)
                if peaks[-2][1] > peaks[-3][1] and peaks[-2][1] > peaks[-1][1]:
                    return {
                        'detected': True,
                        'confidence': 0.8,
                        'neckline': np.mean([troughs[-2][1], troughs[-1][1]]) if len(troughs) >= 2 else None,
                        'head_price': peaks[-2][1],
                        'type': 'head_shoulders'
                    }
                    
            return {'detected': False, 'confidence': 0.0}
            
        except Exception as e:
            logger.error(f"Error detecting head and shoulders: {e}")
            return {'detected': False, 'confidence': 0.0}
            
    def _detect_flag(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Detect flag pattern."""
        try:
            # Calculate trend before flag
            trend_slope = self._calculate_trend_slope(data['close'].values[-20:])
            
            # Check for consolidation after trend
            recent_range = data['high'].iloc[-10:].max() - data['low'].iloc[-10:].min()
            avg_range = (data['high'] - data['low']).mean()
            
            if abs(trend_slope) > 0.001 and recent_range < avg_range * 0.5:
                return {
                    'detected': True,
                    'confidence': 0.7,
                    'trend_direction': 'up' if trend_slope > 0 else 'down',
                    'flag_range': recent_range
                }
                
            return {'detected': False, 'confidence': 0.0}
            
        except Exception as e:
            logger.error(f"Error detecting flag: {e}")
            return {'detected': False, 'confidence': 0.0}
            
    def _detect_triangle(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Detect triangle pattern."""
        try:
            highs = data['high'].values
            lows = data['low'].values
            
            # Find trend lines
            high_trend = self._calculate_trend_slope(highs[-20:])
            low_trend = self._calculate_trend_slope(lows[-20:])
            
            # Check for converging trend lines
            if abs(high_trend - low_trend) > 0.001:
                triangle_type = 'ascending' if low_trend > 0 else 'descending' if high_trend < 0 else 'symmetrical'
                
                return {
                    'detected': True,
                    'confidence': 0.6,
                    'type': triangle_type,
                    'upper_slope': high_trend,
                    'lower_slope': low_trend
                }
                
            return {'detected': False, 'confidence': 0.0}
            
        except Exception as e:
            logger.error(f"Error detecting triangle: {e}")
            return {'detected': False, 'confidence': 0.0}
            
    def _detect_double_top(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Detect double top pattern."""
        try:
            highs = data['high'].values
            peaks = self._find_peaks(highs)
            
            if len(peaks) >= 2:
                # Check if last two peaks are similar
                peak1, peak2 = peaks[-2][1], peaks[-1][1]
                if abs(peak1 - peak2) / peak1 < 0.02:  # Within 2%
                    return {
                        'detected': True,
                        'confidence': 0.75,
                        'peaks': [peak1, peak2],
                        'type': 'double_top'
                    }
                    
            return {'detected': False, 'confidence': 0.0}
            
        except Exception as e:
            logger.error(f"Error detecting double top: {e}")
            return {'detected': False, 'confidence': 0.0}
            
    def _detect_double_bottom(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Detect double bottom pattern."""
        try:
            lows = data['low'].values
            troughs = self._find_troughs(lows)
            
            if len(troughs) >= 2:
                # Check if last two troughs are similar
                trough1, trough2 = troughs[-2][1], troughs[-1][1]
                if abs(trough1 - trough2) / trough1 < 0.02:  # Within 2%
                    return {
                        'detected': True,
                        'confidence': 0.75,
                        'troughs': [trough1, trough2],
                        'type': 'double_bottom'
                    }
                    
            return {'detected': False, 'confidence': 0.0}
            
        except Exception as e:
            logger.error(f"Error detecting double bottom: {e}")
            return {'detected': False, 'confidence': 0.0}
            
    def _detect_wedge(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Detect wedge pattern."""
        try:
            highs = data['high'].values
            lows = data['low'].values
            
            high_trend = self._calculate_trend_slope(highs[-20:])
            low_trend = self._calculate_trend_slope(lows[-20:])
            
            # Check for converging trend lines in same direction
            if (high_trend > 0 and low_trend > 0 and high_trend < low_trend) or \
               (high_trend < 0 and low_trend < 0 and high_trend > low_trend):
                
                wedge_type = 'rising' if high_trend > 0 else 'falling'
                
                return {
                    'detected': True,
                    'confidence': 0.6,
                    'type': wedge_type,
                    'upper_slope': high_trend,
                    'lower_slope': low_trend
                }
                
            return {'detected': False, 'confidence': 0.0}
            
        except Exception as e:
            logger.error(f"Error detecting wedge: {e}")
            return {'detected': False, 'confidence': 0.0}
            
    def _detect_fair_value_gaps(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect fair value gaps."""
        gaps = []
        
        try:
            for i in range(2, len(data)):
                # Bullish FVG: high[i-2] < low[i]
                if data['high'].iloc[i-2] < data['low'].iloc[i]:
                    gaps.append({
                        'type': 'bullish_fvg',
                        'start_price': data['high'].iloc[i-2],
                        'end_price': data['low'].iloc[i],
                        'index': i
                    })
                    
                # Bearish FVG: low[i-2] > high[i]
                elif data['low'].iloc[i-2] > data['high'].iloc[i]:
                    gaps.append({
                        'type': 'bearish_fvg',
                        'start_price': data['low'].iloc[i-2],
                        'end_price': data['high'].iloc[i],
                        'index': i
                    })
                    
        except Exception as e:
            logger.error(f"Error detecting fair value gaps: {e}")
            
        return gaps
        
    def _detect_liquidity_grabs(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect liquidity grabs."""
        grabs = []
        
        try:
            # Look for stop hunt patterns
            for i in range(1, len(data)):
                # Bullish liquidity grab: break below recent low then reverse
                if data['low'].iloc[i] < data['low'].iloc[i-1] and \
                   data['close'].iloc[i] > data['low'].iloc[i-1]:
                    grabs.append({
                        'type': 'bullish_grab',
                        'grab_price': data['low'].iloc[i],
                        'reversal_price': data['close'].iloc[i],
                        'index': i
                    })
                    
                # Bearish liquidity grab: break above recent high then reverse
                elif data['high'].iloc[i] > data['high'].iloc[i-1] and \
                     data['close'].iloc[i] < data['high'].iloc[i-1]:
                    grabs.append({
                        'type': 'bearish_grab',
                        'grab_price': data['high'].iloc[i],
                        'reversal_price': data['close'].iloc[i],
                        'index': i
                    })
                    
        except Exception as e:
            logger.error(f"Error detecting liquidity grabs: {e}")
            
        return grabs
        
    def _detect_order_blocks(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect order blocks."""
        blocks = []
        
        try:
            # Look for significant price moves after consolidation
            for i in range(5, len(data)):
                recent_data = data.iloc[i-5:i]
                
                # Check for consolidation
                consolidation_range = recent_data['high'].max() - recent_data['low'].min()
                avg_range = (data['high'] - data['low']).mean()
                
                if consolidation_range < avg_range * 0.5:
                    # Check for breakout
                    if data['close'].iloc[i] > recent_data['high'].max():
                        blocks.append({
                            'type': 'bullish_order_block',
                            'block_high': recent_data['high'].max(),
                            'block_low': recent_data['low'].min(),
                            'index': i
                        })
                    elif data['close'].iloc[i] < recent_data['low'].min():
                        blocks.append({
                            'type': 'bearish_order_block',
                            'block_high': recent_data['high'].max(),
                            'block_low': recent_data['low'].min(),
                            'index': i
                        })
                        
        except Exception as e:
            logger.error(f"Error detecting order blocks: {e}")
            
        return blocks
        
    def _detect_imbalances(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect price imbalances."""
        imbalances = []
        
        try:
            # Look for gaps between candles
            for i in range(1, len(data)):
                # Bullish imbalance: previous high < current low
                if data['high'].iloc[i-1] < data['low'].iloc[i]:
                    imbalances.append({
                        'type': 'bullish_imbalance',
                        'gap_start': data['high'].iloc[i-1],
                        'gap_end': data['low'].iloc[i],
                        'index': i
                    })
                    
                # Bearish imbalance: previous low > current high
                elif data['low'].iloc[i-1] > data['high'].iloc[i]:
                    imbalances.append({
                        'type': 'bearish_imbalance',
                        'gap_start': data['low'].iloc[i-1],
                        'gap_end': data['high'].iloc[i],
                        'index': i
                    })
                    
        except Exception as e:
            logger.error(f"Error detecting imbalances: {e}")
            
        return imbalances
        
    def _calculate_support_resistance(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate support and resistance levels."""
        try:
            # Find significant highs and lows
            highs = data['high'].values
            lows = data['low'].values
            
            peaks = self._find_peaks(highs)
            troughs = self._find_troughs(lows)
            
            # Calculate resistance levels
            resistance_levels = [peak[1] for peak in peaks[-5:]]  # Last 5 peaks
            
            # Calculate support levels
            support_levels = [trough[1] for trough in troughs[-5:]]  # Last 5 troughs
            
            return {
                'resistance_levels': resistance_levels,
                'support_levels': support_levels,
                'current_price': data['close'].iloc[-1],
                'nearest_resistance': min(resistance_levels, key=lambda x: abs(x - data['close'].iloc[-1])) if resistance_levels else None,
                'nearest_support': min(support_levels, key=lambda x: abs(x - data['close'].iloc[-1])) if support_levels else None
            }
            
        except Exception as e:
            logger.error(f"Error calculating support/resistance: {e}")
            return {}
            
    def _calculate_pivot_points(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate pivot points."""
        try:
            # Use previous day's data for pivot calculation
            prev_high = data['high'].iloc[-2]
            prev_low = data['low'].iloc[-2]
            prev_close = data['close'].iloc[-2]
            
            # Standard pivot points
            pivot = (prev_high + prev_low + prev_close) / 3
            
            # Resistance levels
            r1 = 2 * pivot - prev_low
            r2 = pivot + (prev_high - prev_low)
            r3 = r1 + (prev_high - prev_low)
            
            # Support levels
            s1 = 2 * pivot - prev_high
            s2 = pivot - (prev_high - prev_low)
            s3 = s1 - (prev_high - prev_low)
            
            return {
                'pivot': pivot,
                'r1': r1, 'r2': r2, 'r3': r3,
                's1': s1, 's2': s2, 's3': s3
            }
            
        except Exception as e:
            logger.error(f"Error calculating pivot points: {e}")
            return {}
            
    def _calculate_vwap(self, data: pd.DataFrame) -> float:
        """Calculate VWAP."""
        try:
            typical_price = (data['high'] + data['low'] + data['close']) / 3
            return (typical_price * data['volume']).sum() / data['volume'].sum()
        except Exception as e:
            logger.error(f"Error calculating VWAP: {e}")
            return 0.0
            
    def _calculate_volume_profile(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate volume profile."""
        try:
            # Create price bins
            price_min = data['low'].min()
            price_max = data['high'].max()
            price_bins = np.linspace(price_min, price_max, 50)
            
            # Calculate volume for each price level
            volume_profile = {}
            for i, price in enumerate(price_bins[:-1]):
                price_range = (price_bins[i], price_bins[i+1])
                volume_in_range = data[
                    (data['low'] <= price_range[1]) & 
                    (data['high'] >= price_range[0])
                ]['volume'].sum()
                volume_profile[price] = volume_in_range
                
            # Find POC (Point of Control)
            poc_price = max(volume_profile, key=volume_profile.get)
            
            return {
                'volume_profile': volume_profile,
                'poc': poc_price,
                'value_area_high': None,  # Would need more complex calculation
                'value_area_low': None
            }
            
        except Exception as e:
            logger.error(f"Error calculating volume profile: {e}")
            return {}
            
    def _calculate_price_momentum(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate price momentum."""
        try:
            # Rate of change
            roc_5 = ta.roc(data['close'], length=5).iloc[-1]
            roc_10 = ta.roc(data['close'], length=10).iloc[-1]
            
            # Momentum
            momentum = ta.mom(data['close'], length=10).iloc[-1]
            
            return {
                'roc_5': roc_5,
                'roc_10': roc_10,
                'momentum': momentum,
                'trend_strength': abs(roc_10)
            }
            
        except Exception as e:
            logger.error(f"Error calculating price momentum: {e}")
            return {}
            
    def _calculate_volume_momentum(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate volume momentum."""
        try:
            # Volume rate of change
            vroc = ta.roc(data['volume'], length=10).iloc[-1]
            
            # Volume momentum
            volume_momentum = data['volume'].iloc[-1] / data['volume'].rolling(10).mean().iloc[-1]
            
            return {
                'vroc': vroc,
                'volume_momentum': volume_momentum,
                'volume_trend': 'increasing' if vroc > 0 else 'decreasing'
            }
            
        except Exception as e:
            logger.error(f"Error calculating volume momentum: {e}")
            return {}
            
    def _detect_thrust_signals(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect thrust signals."""
        signals = []
        
        try:
            # Look for sudden price moves with volume
            for i in range(1, len(data)):
                price_change = abs(data['close'].iloc[i] - data['close'].iloc[i-1]) / data['close'].iloc[i-1]
                volume_ratio = data['volume'].iloc[i] / data['volume'].rolling(20).mean().iloc[i]
                
                if price_change > 0.003 and volume_ratio > 2.0:  # 0.3% price move with 2x volume
                    direction = 'bullish' if data['close'].iloc[i] > data['close'].iloc[i-1] else 'bearish'
                    signals.append({
                        'type': 'thrust_signal',
                        'direction': direction,
                        'price_change': price_change,
                        'volume_ratio': volume_ratio,
                        'index': i
                    })
                    
        except Exception as e:
            logger.error(f"Error detecting thrust signals: {e}")
            
        return signals
        
    def _detect_breakout_signals(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect breakout signals."""
        signals = []
        
        try:
            # Look for breakouts from consolidation
            for i in range(20, len(data)):
                recent_data = data.iloc[i-20:i]
                current_price = data['close'].iloc[i]
                
                # Check if breaking out of recent range
                resistance = recent_data['high'].max()
                support = recent_data['low'].min()
                
                if current_price > resistance:
                    signals.append({
                        'type': 'bullish_breakout',
                        'breakout_price': current_price,
                        'resistance_level': resistance,
                        'index': i
                    })
                elif current_price < support:
                    signals.append({
                        'type': 'bearish_breakout',
                        'breakout_price': current_price,
                        'support_level': support,
                        'index': i
                    })
                    
        except Exception as e:
            logger.error(f"Error detecting breakout signals: {e}")
            
        return signals
        
    def _detect_volume_spikes(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect volume spikes."""
        spikes = []
        
        try:
            volume_sma = data['volume'].rolling(20).mean()
            
            for i in range(len(data)):
                if data['volume'].iloc[i] > volume_sma.iloc[i] * 3:  # 3x average volume
                    spikes.append({
                        'type': 'volume_spike',
                        'volume': data['volume'].iloc[i],
                        'average_volume': volume_sma.iloc[i],
                        'ratio': data['volume'].iloc[i] / volume_sma.iloc[i],
                        'index': i
                    })
                    
        except Exception as e:
            logger.error(f"Error detecting volume spikes: {e}")
            
        return spikes
        
    def _calculate_volume_trend(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate volume trend."""
        try:
            # Volume trend using linear regression
            volume_trend = self._calculate_trend_slope(data['volume'].values[-20:])
            
            return {
                'volume_trend_slope': volume_trend,
                'volume_trend_direction': 'increasing' if volume_trend > 0 else 'decreasing',
                'current_volume': data['volume'].iloc[-1],
                'average_volume': data['volume'].rolling(20).mean().iloc[-1]
            }
            
        except Exception as e:
            logger.error(f"Error calculating volume trend: {e}")
            return {}
            
    def _find_peaks(self, data: np.ndarray, min_distance: int = 5) -> List[Tuple[int, float]]:
        """Find peaks in data."""
        peaks = []
        
        for i in range(min_distance, len(data) - min_distance):
            is_peak = True
            for j in range(i - min_distance, i + min_distance + 1):
                if j != i and data[j] >= data[i]:
                    is_peak = False
                    break
            if is_peak:
                peaks.append((i, data[i]))
                
        return peaks
        
    def _find_troughs(self, data: np.ndarray, min_distance: int = 5) -> List[Tuple[int, float]]:
        """Find troughs in data."""
        troughs = []
        
        for i in range(min_distance, len(data) - min_distance):
            is_trough = True
            for j in range(i - min_distance, i + min_distance + 1):
                if j != i and data[j] <= data[i]:
                    is_trough = False
                    break
            if is_trough:
                troughs.append((i, data[i]))
                
        return troughs
        
    def _calculate_trend_slope(self, data: np.ndarray) -> float:
        """Calculate trend slope using linear regression."""
        if len(data) < 2:
            return 0.0
            
        x = np.arange(len(data))
        slope = np.polyfit(x, data, 1)[0]
        return slope