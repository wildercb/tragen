"""
Technical Analysis MCP Tools
============================

MCP tools for technical analysis and pattern recognition on NQ futures data.
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
import json

logger = logging.getLogger(__name__)

def register_analysis_tools(mcp_server, config):
    """Register technical analysis tools with the MCP server."""
    
    @mcp_server.tool()
    async def calculate_technical_indicators(
        data: str,  # JSON string of OHLCV data
        indicators: List[str] = ["sma_20", "rsi_14", "atr_14"]
    ) -> Dict[str, Any]:
        """
        Calculate technical indicators for given OHLCV data.
        
        Args:
            data: JSON string containing OHLCV data
            indicators: List of indicators to calculate
            
        Returns:
            Dictionary of calculated indicator values
        """
        try:
            # Parse the JSON data
            ohlcv_data = json.loads(data)
            
            if not ohlcv_data or 'data' not in ohlcv_data:
                return {"error": "Invalid data format"}
            
            # Convert to DataFrame
            df = pd.DataFrame(ohlcv_data['data'])
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            
            results = {}
            
            for indicator in indicators:
                try:
                    if indicator.startswith('sma_'):
                        period = int(indicator.split('_')[1])
                        results[indicator] = float(df['close'].rolling(window=period).mean().iloc[-1])
                        
                    elif indicator.startswith('ema_'):
                        period = int(indicator.split('_')[1])
                        results[indicator] = float(df['close'].ewm(span=period).mean().iloc[-1])
                        
                    elif indicator.startswith('rsi_'):
                        period = int(indicator.split('_')[1])
                        rsi = calculate_rsi(df['close'], period)
                        results[indicator] = float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else None
                        
                    elif indicator.startswith('atr_'):
                        period = int(indicator.split('_')[1])
                        atr = calculate_atr(df, period)
                        results[indicator] = float(atr.iloc[-1]) if not pd.isna(atr.iloc[-1]) else None
                        
                    elif indicator == 'macd':
                        macd_line, signal_line, histogram = calculate_macd(df['close'])
                        results['macd'] = float(macd_line.iloc[-1]) if not pd.isna(macd_line.iloc[-1]) else None
                        results['macd_signal'] = float(signal_line.iloc[-1]) if not pd.isna(signal_line.iloc[-1]) else None
                        results['macd_histogram'] = float(histogram.iloc[-1]) if not pd.isna(histogram.iloc[-1]) else None
                        
                    elif indicator.startswith('bb_'):
                        # Bollinger Bands
                        period = 20
                        std_dev = 2
                        if '_' in indicator:
                            parts = indicator.split('_')
                            if len(parts) >= 2:
                                period = int(parts[1])
                            if len(parts) >= 3:
                                std_dev = int(parts[2])
                        
                        upper, lower, middle = calculate_bollinger_bands(df['close'], period, std_dev)
                        results['bb_upper'] = float(upper.iloc[-1]) if not pd.isna(upper.iloc[-1]) else None
                        results['bb_lower'] = float(lower.iloc[-1]) if not pd.isna(lower.iloc[-1]) else None
                        results['bb_middle'] = float(middle.iloc[-1]) if not pd.isna(middle.iloc[-1]) else None
                        
                except Exception as e:
                    logger.warning(f"Error calculating {indicator}: {e}")
                    results[indicator] = None
            
            return {
                "indicators": results,
                "data_points": len(df),
                "calculation_time": df.index[-1].isoformat(),
                "current_price": float(df['close'].iloc[-1])
            }
            
        except Exception as e:
            logger.error(f"Error calculating technical indicators: {e}")
            return {"error": str(e)}
    
    @mcp_server.tool()
    async def detect_patterns(
        data: str,  # JSON string of OHLCV data
        patterns: List[str] = ["head_shoulders", "double_top", "triangle"]
    ) -> Dict[str, Any]:
        """
        Detect chart patterns in OHLCV data.
        
        Args:
            data: JSON string containing OHLCV data
            patterns: List of patterns to detect
            
        Returns:
            Dictionary of detected patterns with confidence scores
        """
        try:
            # Parse the JSON data
            ohlcv_data = json.loads(data)
            df = pd.DataFrame(ohlcv_data['data'])
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            
            detected_patterns = {}
            
            for pattern in patterns:
                try:
                    if pattern == "head_shoulders":
                        result = detect_head_shoulders(df)
                        detected_patterns[pattern] = result
                        
                    elif pattern == "double_top":
                        result = detect_double_top(df)
                        detected_patterns[pattern] = result
                        
                    elif pattern == "triangle":
                        result = detect_triangle(df)
                        detected_patterns[pattern] = result
                        
                    elif pattern == "support_resistance":
                        result = find_support_resistance(df)
                        detected_patterns[pattern] = result
                        
                except Exception as e:
                    logger.warning(f"Error detecting {pattern}: {e}")
                    detected_patterns[pattern] = {"detected": False, "error": str(e)}
            
            return {
                "patterns": detected_patterns,
                "data_points": len(df),
                "analysis_time": df.index[-1].isoformat(),
                "price_range": {
                    "high": float(df['high'].max()),
                    "low": float(df['low'].min()),
                    "current": float(df['close'].iloc[-1])
                }
            }
            
        except Exception as e:
            logger.error(f"Error detecting patterns: {e}")
            return {"error": str(e)}
    
    @mcp_server.tool()
    async def analyze_momentum(data: str) -> Dict[str, Any]:
        """
        Analyze price momentum and volume characteristics.
        
        Args:
            data: JSON string containing OHLCV data
            
        Returns:
            Momentum analysis with trend strength and direction
        """
        try:
            ohlcv_data = json.loads(data)
            df = pd.DataFrame(ohlcv_data['data'])
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            
            # Calculate momentum indicators
            price_change = df['close'].iloc[-1] - df['close'].iloc[0]
            price_change_pct = (price_change / df['close'].iloc[0]) * 100
            
            # Rate of change
            roc_5 = ((df['close'].iloc[-1] / df['close'].iloc[-6]) - 1) * 100 if len(df) > 5 else 0
            roc_10 = ((df['close'].iloc[-1] / df['close'].iloc[-11]) - 1) * 100 if len(df) > 10 else 0
            
            # Volume analysis
            avg_volume = df['volume'].mean()
            recent_volume = df['volume'].tail(5).mean()
            volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1
            
            # Volatility (ATR-based)
            atr = calculate_atr(df, 14)
            current_atr = float(atr.iloc[-1]) if not pd.isna(atr.iloc[-1]) else 0
            volatility_pct = (current_atr / df['close'].iloc[-1]) * 100
            
            # Trend strength (based on consecutive moves)
            consecutive_moves = calculate_consecutive_moves(df['close'])
            
            return {
                "momentum": {
                    "price_change": float(price_change),
                    "price_change_pct": float(price_change_pct),
                    "roc_5_periods": float(roc_5),
                    "roc_10_periods": float(roc_10),
                    "direction": "bullish" if price_change > 0 else "bearish" if price_change < 0 else "neutral"
                },
                "volume": {
                    "average_volume": int(avg_volume),
                    "recent_volume": int(recent_volume),
                    "volume_ratio": float(volume_ratio),
                    "volume_trend": "increasing" if volume_ratio > 1.2 else "decreasing" if volume_ratio < 0.8 else "normal"
                },
                "volatility": {
                    "atr": float(current_atr),
                    "volatility_pct": float(volatility_pct),
                    "volatility_level": "high" if volatility_pct > 1.0 else "normal" if volatility_pct > 0.5 else "low"
                },
                "trend": {
                    "consecutive_moves": consecutive_moves,
                    "trend_strength": "strong" if abs(consecutive_moves) > 3 else "moderate" if abs(consecutive_moves) > 1 else "weak"
                },
                "analysis_timestamp": df.index[-1].isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing momentum: {e}")
            return {"error": str(e)}

# Helper functions for technical analysis

def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """Calculate RSI (Relative Strength Index)."""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate ATR (Average True Range)."""
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = true_range.rolling(window=period).mean()
    return atr

def calculate_macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    """Calculate MACD."""
    ema_fast = prices.ewm(span=fast).mean()
    ema_slow = prices.ewm(span=slow).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def calculate_bollinger_bands(prices: pd.Series, period: int = 20, std_dev: int = 2):
    """Calculate Bollinger Bands."""
    middle = prices.rolling(window=period).mean()
    std = prices.rolling(window=period).std()
    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)
    return upper, lower, middle

def detect_head_shoulders(df: pd.DataFrame) -> Dict[str, Any]:
    """Detect head and shoulders pattern."""
    if len(df) < 20:
        return {"detected": False, "reason": "Insufficient data"}
    
    # Simple head and shoulders detection
    highs = df['high'].rolling(window=3, center=True).max()
    peaks = df['high'] == highs
    
    peak_indices = df[peaks].index
    if len(peak_indices) < 3:
        return {"detected": False, "confidence": 0.0}
    
    # Very basic pattern matching - would need more sophisticated algorithm
    return {"detected": False, "confidence": 0.3, "note": "Basic detection - needs enhancement"}

def detect_double_top(df: pd.DataFrame) -> Dict[str, Any]:
    """Detect double top pattern."""
    if len(df) < 10:
        return {"detected": False, "reason": "Insufficient data"}
    
    # Basic double top detection
    recent_high = df['high'].tail(10).max()
    previous_high = df['high'].head(-10).max() if len(df) > 10 else 0
    
    if abs(recent_high - previous_high) / recent_high < 0.02:  # Within 2%
        return {"detected": True, "confidence": 0.6, "levels": [float(recent_high), float(previous_high)]}
    
    return {"detected": False, "confidence": 0.2}

def detect_triangle(df: pd.DataFrame) -> Dict[str, Any]:
    """Detect triangle pattern."""
    if len(df) < 15:
        return {"detected": False, "reason": "Insufficient data"}
    
    # Basic triangle detection - converging highs and lows
    recent_highs = df['high'].tail(10)
    recent_lows = df['low'].tail(10)
    
    # Check if range is contracting
    early_range = recent_highs.head(5).max() - recent_lows.head(5).min()
    late_range = recent_highs.tail(5).max() - recent_lows.tail(5).min()
    
    if late_range < early_range * 0.8:  # Range contracted by 20%
        return {"detected": True, "confidence": 0.5, "type": "contracting_triangle"}
    
    return {"detected": False, "confidence": 0.1}

def find_support_resistance(df: pd.DataFrame) -> Dict[str, Any]:
    """Find support and resistance levels."""
    if len(df) < 10:
        return {"levels": [], "reason": "Insufficient data"}
    
    # Simple support/resistance based on recent highs and lows
    support_level = df['low'].tail(20).min()
    resistance_level = df['high'].tail(20).max()
    
    return {
        "support": float(support_level),
        "resistance": float(resistance_level),
        "current_price": float(df['close'].iloc[-1]),
        "distance_to_support": float(df['close'].iloc[-1] - support_level),
        "distance_to_resistance": float(resistance_level - df['close'].iloc[-1])
    }

def calculate_consecutive_moves(prices: pd.Series) -> int:
    """Calculate consecutive moves in same direction."""
    if len(prices) < 2:
        return 0
    
    moves = prices.diff().dropna()
    if len(moves) == 0:
        return 0
    
    consecutive = 0
    current_direction = 1 if moves.iloc[-1] > 0 else -1 if moves.iloc[-1] < 0 else 0
    
    for i in range(len(moves) - 1, -1, -1):
        move_direction = 1 if moves.iloc[i] > 0 else -1 if moves.iloc[i] < 0 else 0
        if move_direction == current_direction and move_direction != 0:
            consecutive += 1
        else:
            break
    
    return consecutive * current_direction

logger.info("Technical analysis tools registered with MCP server")