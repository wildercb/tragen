"""
Market Context Analyzer for AI Trading Models
===========================================

Provides comprehensive market structure analysis including:
- Trading session highs/lows (Asia, London, New York)
- Fair Value Gaps (FVG) and Inverse Fair Value Gaps (IFVG)
- Order blocks and liquidity zones
- Market structure breaks and key levels
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import pytz

logger = logging.getLogger(__name__)

@dataclass
class TradingSession:
    name: str
    start_hour: int
    end_hour: int
    timezone: str
    high: Optional[float] = None
    low: Optional[float] = None
    open: Optional[float] = None
    close: Optional[float] = None
    volume: Optional[int] = None
    active: bool = False

@dataclass
class FairValueGap:
    type: str  # 'bullish' or 'bearish'
    start_time: datetime
    end_time: Optional[datetime]
    high: float
    low: float
    gap_size: float
    filled: bool = False
    filled_time: Optional[datetime] = None
    strength: float = 1.0  # 1.0 = normal, 2.0 = strong, 0.5 = weak

@dataclass
class OrderBlock:
    type: str  # 'bullish' or 'bearish'
    time: datetime
    high: float
    low: float
    volume: int
    strength: float
    tested: bool = False
    tested_times: int = 0

@dataclass
class LiquidityZone:
    type: str  # 'buy_side' or 'sell_side'
    price: float
    time: datetime
    strength: float
    hit_count: int = 0
    active: bool = True

class MarketContextAnalyzer:
    """Analyzes market structure and provides trading context for AI models."""
    
    def __init__(self):
        self.sessions = self._initialize_sessions()
        self.fair_value_gaps: List[FairValueGap] = []
        self.order_blocks: List[OrderBlock] = []
        self.liquidity_zones: List[LiquidityZone] = []
        self.market_structure = {
            'trend': 'neutral',
            'structure_break': None,
            'key_levels': [],
            'last_high': None,
            'last_low': None
        }
        
    def _initialize_sessions(self) -> Dict[str, TradingSession]:
        """Initialize trading sessions with their time ranges."""
        return {
            'asia': TradingSession(
                name='Asia',
                start_hour=20,  # 8 PM EST (previous day)
                end_hour=2,     # 2 AM EST
                timezone='US/Eastern'
            ),
            'london': TradingSession(
                name='London',
                start_hour=3,   # 3 AM EST
                end_hour=12,    # 12 PM EST
                timezone='US/Eastern'
            ),
            'new_york': TradingSession(
                name='New York',
                start_hour=9,   # 9 AM EST
                end_hour=17,    # 5 PM EST
                timezone='US/Eastern'
            )
        }
    
    def analyze_market_context(self, ohlcv_data: List[Dict]) -> Dict[str, Any]:
        """
        Analyze comprehensive market context from OHLCV data.
        
        Args:
            ohlcv_data: List of OHLCV candles with 'time', 'open', 'high', 'low', 'close', 'volume'
            
        Returns:
            Dict containing all market context information
        """
        if not ohlcv_data or len(ohlcv_data) < 10:
            return self._empty_context()
        
        # Convert to DataFrame for easier analysis
        df = pd.DataFrame(ohlcv_data)
        df['datetime'] = pd.to_datetime(df['time'], unit='s')
        df = df.sort_values('datetime')
        
        # Analyze different market structure components
        self._analyze_trading_sessions(df)
        self._detect_fair_value_gaps(df)
        self._detect_order_blocks(df)
        self._identify_liquidity_zones(df)
        self._analyze_market_structure(df)
        
        return self._compile_context()
    
    def _analyze_trading_sessions(self, df: pd.DataFrame):
        """Analyze trading sessions and their key levels."""
        est = pytz.timezone('US/Eastern')
        current_time = datetime.now(est)
        
        # Ensure datetime column is timezone-aware
        if df['datetime'].dt.tz is None:
            df['datetime'] = df['datetime'].dt.tz_localize('UTC').dt.tz_convert(est)
        
        # Get data for the last 24 hours
        recent_data = df[df['datetime'] >= current_time - timedelta(hours=24)]
        
        if recent_data.empty:
            return
            
        for session_name, session in self.sessions.items():
            # Find candles within session hours
            session_candles = self._filter_session_candles(recent_data, session)
            
            if not session_candles.empty:
                session.high = session_candles['high'].max()
                session.low = session_candles['low'].min()
                session.open = session_candles.iloc[0]['open']
                session.close = session_candles.iloc[-1]['close']
                session.volume = int(session_candles['volume'].sum())
                
                # Check if session is currently active
                current_hour = current_time.hour
                if session.start_hour <= session.end_hour:
                    session.active = session.start_hour <= current_hour <= session.end_hour
                else:  # Overnight session (like Asia)
                    session.active = current_hour >= session.start_hour or current_hour <= session.end_hour
    
    def _filter_session_candles(self, df: pd.DataFrame, session: TradingSession) -> pd.DataFrame:
        """Filter candles for a specific trading session."""
        est = pytz.timezone('US/Eastern')
        
        # Convert to EST if not already
        if df['datetime'].dt.tz is None:
            df['datetime'] = df['datetime'].dt.tz_localize('UTC').dt.tz_convert(est)
        
        # Extract hour
        df['hour'] = df['datetime'].dt.hour
        
        if session.start_hour <= session.end_hour:
            # Normal session (London, New York)
            mask = (df['hour'] >= session.start_hour) & (df['hour'] <= session.end_hour)
        else:
            # Overnight session (Asia)
            mask = (df['hour'] >= session.start_hour) | (df['hour'] <= session.end_hour)
        
        return df[mask]
    
    def _detect_fair_value_gaps(self, df: pd.DataFrame):
        """Detect Fair Value Gaps and Inverse Fair Value Gaps."""
        if len(df) < 3:
            return
            
        # Clear old gaps that are too old (older than 7 days)
        cutoff_time = datetime.now() - timedelta(days=7)
        self.fair_value_gaps = [gap for gap in self.fair_value_gaps 
                               if gap.start_time > cutoff_time]
        
        # Look for FVG patterns in recent data
        for i in range(2, len(df)):
            candle1 = df.iloc[i-2]
            candle2 = df.iloc[i-1]  # Gap candle
            candle3 = df.iloc[i]
            
            # Bullish FVG: gap between candle1 high and candle3 low
            if (candle1['high'] < candle3['low'] and 
                candle2['high'] > candle1['high'] and 
                candle2['low'] < candle3['low']):
                
                gap_size = candle3['low'] - candle1['high']
                if gap_size > 0:  # Valid gap
                    fvg = FairValueGap(
                        type='bullish',
                        start_time=candle2['datetime'],
                        end_time=None,
                        high=candle3['low'],
                        low=candle1['high'],
                        gap_size=gap_size,
                        strength=self._calculate_gap_strength(candle2, gap_size)
                    )
                    self.fair_value_gaps.append(fvg)
            
            # Bearish FVG: gap between candle1 low and candle3 high
            elif (candle1['low'] > candle3['high'] and 
                  candle2['low'] < candle1['low'] and 
                  candle2['high'] > candle3['high']):
                
                gap_size = candle1['low'] - candle3['high']
                if gap_size > 0:  # Valid gap
                    fvg = FairValueGap(
                        type='bearish',
                        start_time=candle2['datetime'],
                        end_time=None,
                        high=candle1['low'],
                        low=candle3['high'],
                        gap_size=gap_size,
                        strength=self._calculate_gap_strength(candle2, gap_size)
                    )
                    self.fair_value_gaps.append(fvg)
        
        # Check if any gaps have been filled
        self._check_gap_fills(df)
    
    def _calculate_gap_strength(self, gap_candle: pd.Series, gap_size: float) -> float:
        """Calculate the strength of a Fair Value Gap."""
        volume = gap_candle.get('volume', 0)
        candle_range = gap_candle['high'] - gap_candle['low']
        
        # Base strength on volume and gap size relative to candle range
        volume_strength = min(volume / 10000, 2.0)  # Normalize volume
        size_strength = min(gap_size / candle_range, 2.0) if candle_range > 0 else 1.0
        
        return (volume_strength + size_strength) / 2
    
    def _check_gap_fills(self, df: pd.DataFrame):
        """Check if any existing gaps have been filled."""
        if df.empty:
            return
            
        current_candle = df.iloc[-1]
        current_time = current_candle['datetime']
        
        # Ensure we have timezone-aware datetime for comparison
        if hasattr(current_time, 'tz') and current_time.tz is None:
            current_time = current_time.tz_localize('UTC')
        
        for gap in self.fair_value_gaps:
            if gap.filled:
                continue
                
            if gap.type == 'bullish':
                # Bullish gap filled when price touches gap low
                if current_candle['low'] <= gap.low:
                    gap.filled = True
                    gap.filled_time = current_time
            else:
                # Bearish gap filled when price touches gap high
                if current_candle['high'] >= gap.high:
                    gap.filled = True
                    gap.filled_time = current_time
    
    def _detect_order_blocks(self, df: pd.DataFrame):
        """Detect institutional order blocks."""
        if len(df) < 5:
            return
            
        # Clear old order blocks (older than 3 days)
        cutoff_time = datetime.now() - timedelta(days=3)
        self.order_blocks = [ob for ob in self.order_blocks 
                            if ob.time > cutoff_time]
        
        # Look for order block patterns
        for i in range(3, len(df)-1):
            candle = df.iloc[i]
            prev_candles = df.iloc[i-3:i]
            next_candle = df.iloc[i+1]
            
            # Bullish order block: strong buying after consolidation
            if (candle['close'] > candle['open'] and  # Green candle
                (candle['high'] - candle['low']) > prev_candles['high'].max() - prev_candles['low'].min() and
                candle['volume'] > prev_candles['volume'].mean() * 1.5 and
                next_candle['low'] > candle['low']):  # Next candle respects the low
                
                strength = self._calculate_order_block_strength(candle, prev_candles)
                
                order_block = OrderBlock(
                    type='bullish',
                    time=candle['datetime'],
                    high=candle['high'],
                    low=candle['low'],
                    volume=int(candle['volume']),
                    strength=strength
                )
                self.order_blocks.append(order_block)
            
            # Bearish order block: strong selling after consolidation
            elif (candle['close'] < candle['open'] and  # Red candle
                  (candle['high'] - candle['low']) > prev_candles['high'].max() - prev_candles['low'].min() and
                  candle['volume'] > prev_candles['volume'].mean() * 1.5 and
                  next_candle['high'] < candle['high']):  # Next candle respects the high
                
                strength = self._calculate_order_block_strength(candle, prev_candles)
                
                order_block = OrderBlock(
                    type='bearish',
                    time=candle['datetime'],
                    high=candle['high'],
                    low=candle['low'],
                    volume=int(candle['volume']),
                    strength=strength
                )
                self.order_blocks.append(order_block)
    
    def _calculate_order_block_strength(self, candle: pd.Series, prev_candles: pd.DataFrame) -> float:
        """Calculate order block strength based on volume and price action."""
        volume_ratio = candle['volume'] / prev_candles['volume'].mean() if prev_candles['volume'].mean() > 0 else 1
        range_ratio = (candle['high'] - candle['low']) / prev_candles['high'].max() - prev_candles['low'].min()
        
        return min((volume_ratio + range_ratio) / 2, 3.0)
    
    def _identify_liquidity_zones(self, df: pd.DataFrame):
        """Identify liquidity zones where price tends to react."""
        if len(df) < 20:
            return
            
        # Clear old liquidity zones (older than 5 days)
        cutoff_time = datetime.now() - timedelta(days=5)
        self.liquidity_zones = [lz for lz in self.liquidity_zones 
                               if lz.time > cutoff_time]
        
        # Find recent highs and lows that could be liquidity zones
        recent_data = df.tail(100)  # Last 100 candles
        
        # Find local highs and lows
        highs = self._find_local_extremes(recent_data, 'high', lookback=5)
        lows = self._find_local_extremes(recent_data, 'low', lookback=5)
        
        # Create liquidity zones from these levels
        for high_idx, high_price in highs:
            candle = recent_data.iloc[high_idx]
            
            # Check if this level has been tested multiple times
            tests = self._count_level_tests(recent_data, high_price, tolerance=0.001)
            
            if tests >= 2:  # At least 2 tests make it a liquidity zone
                liquidity_zone = LiquidityZone(
                    type='sell_side',
                    price=high_price,
                    time=candle['datetime'],
                    strength=min(tests / 2, 3.0),
                    hit_count=tests
                )
                self.liquidity_zones.append(liquidity_zone)
        
        for low_idx, low_price in lows:
            candle = recent_data.iloc[low_idx]
            
            # Check if this level has been tested multiple times
            tests = self._count_level_tests(recent_data, low_price, tolerance=0.001)
            
            if tests >= 2:  # At least 2 tests make it a liquidity zone
                liquidity_zone = LiquidityZone(
                    type='buy_side',
                    price=low_price,
                    time=candle['datetime'],
                    strength=min(tests / 2, 3.0),
                    hit_count=tests
                )
                self.liquidity_zones.append(liquidity_zone)
    
    def _find_local_extremes(self, df: pd.DataFrame, column: str, lookback: int) -> List[Tuple[int, float]]:
        """Find local highs or lows in the data."""
        extremes = []
        
        for i in range(lookback, len(df) - lookback):
            current_value = df.iloc[i][column]
            
            if column == 'high':
                # Check if this is a local high
                is_extreme = all(current_value >= df.iloc[j]['high'] 
                               for j in range(i - lookback, i + lookback + 1))
            else:  # low
                # Check if this is a local low
                is_extreme = all(current_value <= df.iloc[j]['low'] 
                               for j in range(i - lookback, i + lookback + 1))
            
            if is_extreme:
                extremes.append((i, current_value))
        
        return extremes
    
    def _count_level_tests(self, df: pd.DataFrame, level: float, tolerance: float = 0.001) -> int:
        """Count how many times a price level has been tested."""
        tests = 0
        for _, candle in df.iterrows():
            if abs(candle['high'] - level) / level <= tolerance or abs(candle['low'] - level) / level <= tolerance:
                tests += 1
        return tests
    
    def _analyze_market_structure(self, df: pd.DataFrame):
        """Analyze overall market structure and trend."""
        if len(df) < 20:
            return
            
        recent_data = df.tail(50)
        
        # Calculate trend using moving averages
        if len(recent_data) >= 20:
            ma_20 = recent_data['close'].rolling(20).mean().iloc[-1]
            current_price = recent_data['close'].iloc[-1]
            
            if current_price > ma_20 * 1.002:
                self.market_structure['trend'] = 'bullish'
            elif current_price < ma_20 * 0.998:
                self.market_structure['trend'] = 'bearish'
            else:
                self.market_structure['trend'] = 'neutral'
        
        # Find recent swing highs and lows
        highs = self._find_local_extremes(recent_data, 'high', lookback=3)
        lows = self._find_local_extremes(recent_data, 'low', lookback=3)
        
        if highs:
            self.market_structure['last_high'] = {
                'price': highs[-1][1],
                'time': recent_data.iloc[highs[-1][0]]['datetime']
            }
        
        if lows:
            self.market_structure['last_low'] = {
                'price': lows[-1][1],
                'time': recent_data.iloc[lows[-1][0]]['datetime']
            }
    
    def _compile_context(self) -> Dict[str, Any]:
        """Compile all market context into a structured format for AI models."""
        
        # Active Fair Value Gaps
        active_fvgs = [gap for gap in self.fair_value_gaps if not gap.filled]
        
        # Strong Order Blocks
        strong_order_blocks = [ob for ob in self.order_blocks if ob.strength > 1.5]
        
        # Active Liquidity Zones
        active_liquidity = [lz for lz in self.liquidity_zones if lz.active]
        
        context = {
            'timestamp': datetime.now().isoformat(),
            'trading_sessions': {
                session_name: {
                    'name': session.name,
                    'active': session.active,
                    'high': session.high,
                    'low': session.low,
                    'open': session.open,
                    'close': session.close,
                    'volume': session.volume
                }
                for session_name, session in self.sessions.items()
                if session.high is not None
            },
            'fair_value_gaps': {
                'bullish': [
                    {
                        'start_time': gap.start_time.isoformat(),
                        'high': gap.high,
                        'low': gap.low,
                        'gap_size': gap.gap_size,
                        'strength': gap.strength
                    }
                    for gap in active_fvgs if gap.type == 'bullish'
                ],
                'bearish': [
                    {
                        'start_time': gap.start_time.isoformat(),
                        'high': gap.high,
                        'low': gap.low,
                        'gap_size': gap.gap_size,
                        'strength': gap.strength
                    }
                    for gap in active_fvgs if gap.type == 'bearish'
                ]
            },
            'order_blocks': {
                'bullish': [
                    {
                        'time': ob.time.isoformat(),
                        'high': ob.high,
                        'low': ob.low,
                        'volume': ob.volume,
                        'strength': ob.strength,
                        'tested': ob.tested
                    }
                    for ob in strong_order_blocks if ob.type == 'bullish'
                ],
                'bearish': [
                    {
                        'time': ob.time.isoformat(),
                        'high': ob.high,
                        'low': ob.low,
                        'volume': ob.volume,
                        'strength': ob.strength,
                        'tested': ob.tested
                    }
                    for ob in strong_order_blocks if ob.type == 'bearish'
                ]
            },
            'liquidity_zones': {
                'buy_side': [
                    {
                        'price': lz.price,
                        'time': lz.time.isoformat(),
                        'strength': lz.strength,
                        'hit_count': lz.hit_count
                    }
                    for lz in active_liquidity if lz.type == 'buy_side'
                ],
                'sell_side': [
                    {
                        'price': lz.price,
                        'time': lz.time.isoformat(),
                        'strength': lz.strength,
                        'hit_count': lz.hit_count
                    }
                    for lz in active_liquidity if lz.type == 'sell_side'
                ]
            },
            'market_structure': self.market_structure
        }
        
        return context
    
    def _empty_context(self) -> Dict[str, Any]:
        """Return empty context when insufficient data."""
        return {
            'timestamp': datetime.now().isoformat(),
            'trading_sessions': {},
            'fair_value_gaps': {'bullish': [], 'bearish': []},
            'order_blocks': {'bullish': [], 'bearish': []},
            'liquidity_zones': {'buy_side': [], 'sell_side': []},
            'market_structure': {
                'trend': 'unknown',
                'structure_break': None,
                'key_levels': [],
                'last_high': None,
                'last_low': None
            }
        }
    
    def format_context_for_ai(self, context: Dict[str, Any]) -> str:
        """Format market context into a readable string for AI models."""
        if not context or not context.get('trading_sessions'):
            return "Market context: Insufficient data for analysis."
        
        formatted = ["=== MARKET CONTEXT ANALYSIS ===\n"]
        
        # Trading Sessions
        formatted.append("📈 TRADING SESSIONS:")
        for session_name, session_data in context['trading_sessions'].items():
            status = "🟢 ACTIVE" if session_data['active'] else "🔴 CLOSED"
            formatted.append(f"  {session_data['name']} Session {status}:")
            formatted.append(f"    High: ${session_data['high']:.2f}")
            formatted.append(f"    Low: ${session_data['low']:.2f}")
            formatted.append(f"    Range: ${session_data['high'] - session_data['low']:.2f}")
        
        # Fair Value Gaps
        fvgs = context['fair_value_gaps']
        if fvgs['bullish'] or fvgs['bearish']:
            formatted.append("\n📊 FAIR VALUE GAPS:")
            for gap in fvgs['bullish'][:3]:  # Top 3 bullish
                formatted.append(f"  🟢 BULLISH FVG: ${gap['low']:.2f} - ${gap['high']:.2f} (Gap: ${gap['gap_size']:.2f}, Strength: {gap['strength']:.1f})")
            for gap in fvgs['bearish'][:3]:  # Top 3 bearish
                formatted.append(f"  🔴 BEARISH FVG: ${gap['low']:.2f} - ${gap['high']:.2f} (Gap: ${gap['gap_size']:.2f}, Strength: {gap['strength']:.1f})")
        
        # Order Blocks
        obs = context['order_blocks']
        if obs['bullish'] or obs['bearish']:
            formatted.append("\n🏛️ ORDER BLOCKS:")
            for ob in obs['bullish'][:2]:  # Top 2 bullish
                status = "✅ TESTED" if ob['tested'] else "🎯 UNTESTED"
                formatted.append(f"  🟢 BULLISH OB: ${ob['low']:.2f} - ${ob['high']:.2f} (Strength: {ob['strength']:.1f}) {status}")
            for ob in obs['bearish'][:2]:  # Top 2 bearish
                status = "✅ TESTED" if ob['tested'] else "🎯 UNTESTED"
                formatted.append(f"  🔴 BEARISH OB: ${ob['low']:.2f} - ${ob['high']:.2f} (Strength: {ob['strength']:.1f}) {status}")
        
        # Liquidity Zones
        liquidity = context['liquidity_zones']
        if liquidity['buy_side'] or liquidity['sell_side']:
            formatted.append("\n💧 LIQUIDITY ZONES:")
            for lz in liquidity['buy_side'][:3]:  # Top 3 buy side
                formatted.append(f"  🟢 BUY LIQUIDITY: ${lz['price']:.2f} (Strength: {lz['strength']:.1f}, Hits: {lz['hit_count']})")
            for lz in liquidity['sell_side'][:3]:  # Top 3 sell side
                formatted.append(f"  🔴 SELL LIQUIDITY: ${lz['price']:.2f} (Strength: {lz['strength']:.1f}, Hits: {lz['hit_count']})")
        
        # Market Structure
        structure = context['market_structure']
        formatted.append(f"\n🏗️ MARKET STRUCTURE:")
        formatted.append(f"  Trend: {structure['trend'].upper()}")
        if structure['last_high']:
            formatted.append(f"  Last High: ${structure['last_high']['price']:.2f}")
        if structure['last_low']:
            formatted.append(f"  Last Low: ${structure['last_low']['price']:.2f}")
        
        return "\n".join(formatted)

# Global instance for use across the application
market_analyzer = MarketContextAnalyzer()