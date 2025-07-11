"""
Data summarizer for converting extracted features into LLM-friendly text
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class DataSummarizer:
    """
    Convert extracted features into concise text summaries for LLM analysis.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize data summarizer.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.max_tokens = config.get('max_tokens', 200)
        self.include_volume = config.get('include_volume', True)
        self.include_volatility = config.get('include_volatility', True)
        self.include_momentum = config.get('include_momentum', True)
        
    def summarize_features(self, features: Dict[str, Any], current_data: pd.DataFrame) -> str:
        """
        Summarize all features into a concise text description.
        
        Args:
            features: Dictionary of extracted features
            current_data: Current market data
            
        Returns:
            Concise text summary
        """
        summary_parts = []
        
        # Market context
        summary_parts.append(self._summarize_market_context(current_data))
        
        # Technical indicators
        if 'technical_indicators' in features:
            summary_parts.append(self._summarize_technical_indicators(features['technical_indicators']))
        
        # Patterns
        if 'patterns' in features:
            summary_parts.append(self._summarize_patterns(features['patterns']))
        
        # Liquidity features
        if 'liquidity' in features:
            summary_parts.append(self._summarize_liquidity(features['liquidity']))
        
        # Statistical levels
        if 'statistical_levels' in features:
            summary_parts.append(self._summarize_levels(features['statistical_levels']))
        
        # Momentum signals
        if 'momentum' in features:
            summary_parts.append(self._summarize_momentum(features['momentum']))
        
        # Volume analysis
        if 'volume' in features and self.include_volume:
            summary_parts.append(self._summarize_volume(features['volume']))
        
        # Combine all parts
        full_summary = " ".join(filter(None, summary_parts))
        
        # Truncate if too long
        return self._truncate_summary(full_summary)
        
    def _summarize_market_context(self, data: pd.DataFrame) -> str:
        """Summarize current market context."""
        try:
            current_price = data['close'].iloc[-1]
            prev_price = data['close'].iloc[-2] if len(data) > 1 else current_price
            price_change = (current_price - prev_price) / prev_price * 100
            
            # Calculate daily range
            daily_high = data['high'].iloc[-1]
            daily_low = data['low'].iloc[-1]
            daily_range = (daily_high - daily_low) / current_price * 100
            
            # Determine trend
            if price_change > 0.1:
                trend = "bullish"
            elif price_change < -0.1:
                trend = "bearish"
            else:
                trend = "neutral"
                
            return f"NQ at {current_price:.2f}, {trend} trend ({price_change:+.2f}%), daily range {daily_range:.2f}%."
            
        except Exception as e:
            logger.error(f"Error summarizing market context: {e}")
            return "Market context unavailable."
            
    def _summarize_technical_indicators(self, indicators: Dict[str, Any]) -> str:
        """Summarize technical indicators."""
        try:
            parts = []
            
            # Moving averages
            if 'sma_20' in indicators and 'sma_50' in indicators:
                if indicators['sma_20'] > indicators['sma_50']:
                    parts.append("Short-term MA above long-term")
                else:
                    parts.append("Short-term MA below long-term")
                    
            # RSI
            if 'rsi_14' in indicators:
                rsi = indicators['rsi_14']
                if rsi > 70:
                    parts.append("RSI overbought")
                elif rsi < 30:
                    parts.append("RSI oversold")
                else:
                    parts.append(f"RSI neutral ({rsi:.1f})")
                    
            # MACD
            if 'macd' in indicators and 'macd_signal' in indicators:
                if indicators['macd'] > indicators['macd_signal']:
                    parts.append("MACD bullish")
                else:
                    parts.append("MACD bearish")
                    
            # Bollinger Bands
            if 'bb_width' in indicators:
                if indicators['bb_width'] > 0.02:
                    parts.append("High volatility")
                else:
                    parts.append("Low volatility")
                    
            return "Technicals: " + ", ".join(parts) + "." if parts else ""
            
        except Exception as e:
            logger.error(f"Error summarizing technical indicators: {e}")
            return ""
            
    def _summarize_patterns(self, patterns: Dict[str, Any]) -> str:
        """Summarize detected patterns."""
        try:
            detected_patterns = []
            
            for pattern_name, pattern_data in patterns.items():
                if isinstance(pattern_data, dict) and pattern_data.get('detected'):
                    confidence = pattern_data.get('confidence', 0)
                    if confidence > 0.5:
                        pattern_type = pattern_data.get('type', pattern_name)
                        detected_patterns.append(f"{pattern_type} ({confidence:.1f})")
                        
            if detected_patterns:
                return f"Patterns: {', '.join(detected_patterns)}."
            else:
                return "No significant patterns detected."
                
        except Exception as e:
            logger.error(f"Error summarizing patterns: {e}")
            return ""
            
    def _summarize_liquidity(self, liquidity: Dict[str, Any]) -> str:
        """Summarize liquidity features."""
        try:
            parts = []
            
            # Fair value gaps
            if 'fair_value_gaps' in liquidity:
                fvgs = liquidity['fair_value_gaps']
                if fvgs:
                    bullish_fvgs = sum(1 for fvg in fvgs if fvg['type'] == 'bullish_fvg')
                    bearish_fvgs = sum(1 for fvg in fvgs if fvg['type'] == 'bearish_fvg')
                    if bullish_fvgs > bearish_fvgs:
                        parts.append("Bullish FVGs dominate")
                    elif bearish_fvgs > bullish_fvgs:
                        parts.append("Bearish FVGs dominate")
                        
            # Liquidity grabs
            if 'liquidity_grabs' in liquidity:
                grabs = liquidity['liquidity_grabs']
                if grabs:
                    recent_grabs = [g for g in grabs if g['index'] > len(grabs) - 5]
                    if recent_grabs:
                        grab_type = recent_grabs[-1]['type']
                        parts.append(f"Recent {grab_type.replace('_', ' ')}")
                        
            # Order blocks
            if 'order_blocks' in liquidity:
                blocks = liquidity['order_blocks']
                if blocks:
                    recent_blocks = [b for b in blocks if b['index'] > len(blocks) - 3]
                    if recent_blocks:
                        block_type = recent_blocks[-1]['type'].replace('_', ' ')
                        parts.append(f"Active {block_type}")
                        
            return "Liquidity: " + ", ".join(parts) + "." if parts else ""
            
        except Exception as e:
            logger.error(f"Error summarizing liquidity: {e}")
            return ""
            
    def _summarize_levels(self, levels: Dict[str, Any]) -> str:
        """Summarize statistical levels."""
        try:
            parts = []
            
            # Support and resistance
            if 'support_resistance' in levels:
                sr = levels['support_resistance']
                if 'nearest_resistance' in sr and sr['nearest_resistance']:
                    parts.append(f"Resistance at {sr['nearest_resistance']:.2f}")
                if 'nearest_support' in sr and sr['nearest_support']:
                    parts.append(f"Support at {sr['nearest_support']:.2f}")
                    
            # Pivot points
            if 'pivot_points' in levels:
                pp = levels['pivot_points']
                if 'pivot' in pp:
                    parts.append(f"Pivot {pp['pivot']:.2f}")
                    
            # VWAP
            if 'vwap' in levels:
                parts.append(f"VWAP {levels['vwap']:.2f}")
                
            return "Levels: " + ", ".join(parts) + "." if parts else ""
            
        except Exception as e:
            logger.error(f"Error summarizing levels: {e}")
            return ""
            
    def _summarize_momentum(self, momentum: Dict[str, Any]) -> str:
        """Summarize momentum signals."""
        try:
            parts = []
            
            # Price momentum
            if 'price_momentum' in momentum:
                pm = momentum['price_momentum']
                if 'trend_strength' in pm:
                    strength = pm['trend_strength']
                    if strength > 0.01:
                        parts.append("Strong momentum")
                    elif strength > 0.005:
                        parts.append("Moderate momentum")
                    else:
                        parts.append("Weak momentum")
                        
            # Thrust signals
            if 'thrust_signals' in momentum:
                thrusts = momentum['thrust_signals']
                if thrusts:
                    recent_thrusts = [t for t in thrusts if t['index'] > len(thrusts) - 3]
                    if recent_thrusts:
                        thrust_direction = recent_thrusts[-1]['direction']
                        parts.append(f"Recent {thrust_direction} thrust")
                        
            # Breakout signals
            if 'breakout_signals' in momentum:
                breakouts = momentum['breakout_signals']
                if breakouts:
                    recent_breakouts = [b for b in breakouts if b['index'] > len(breakouts) - 3]
                    if recent_breakouts:
                        breakout_type = recent_breakouts[-1]['type'].replace('_', ' ')
                        parts.append(f"Recent {breakout_type}")
                        
            return "Momentum: " + ", ".join(parts) + "." if parts else ""
            
        except Exception as e:
            logger.error(f"Error summarizing momentum: {e}")
            return ""
            
    def _summarize_volume(self, volume: Dict[str, Any]) -> str:
        """Summarize volume analysis."""
        try:
            parts = []
            
            # Volume spikes
            if 'volume_spikes' in volume:
                spikes = volume['volume_spikes']
                if spikes:
                    recent_spikes = [s for s in spikes if s['index'] > len(spikes) - 3]
                    if recent_spikes:
                        max_ratio = max(s['ratio'] for s in recent_spikes)
                        parts.append(f"Volume spike {max_ratio:.1f}x")
                        
            # Volume trend
            if 'volume_trend' in volume:
                vt = volume['volume_trend']
                if 'volume_trend_direction' in vt:
                    direction = vt['volume_trend_direction']
                    parts.append(f"Volume {direction}")
                    
            # OBV
            if 'obv' in volume:
                parts.append("OBV confirming" if volume['obv'] > 0 else "OBV diverging")
                
            return "Volume: " + ", ".join(parts) + "." if parts else ""
            
        except Exception as e:
            logger.error(f"Error summarizing volume: {e}")
            return ""
            
    def _truncate_summary(self, summary: str) -> str:
        """Truncate summary to fit token limit."""
        # Rough estimation: 1 token ≈ 4 characters
        max_chars = self.max_tokens * 4
        
        if len(summary) <= max_chars:
            return summary
            
        # Truncate at sentence boundary
        truncated = summary[:max_chars]
        last_period = truncated.rfind('.')
        
        if last_period > max_chars * 0.8:  # If we can keep most of the content
            return truncated[:last_period + 1]
        else:
            return truncated + "..."
            
    def create_trading_prompt(self, summary: str, current_price: float, nq_config: Dict[str, Any]) -> str:
        """
        Create a trading prompt for the LLM.
        
        Args:
            summary: Market summary
            current_price: Current NQ price
            nq_config: NQ contract configuration
            
        Returns:
            Trading prompt for LLM
        """
        try:
            tick_size = nq_config.get('tick_size', 0.25)
            tick_value = nq_config.get('tick_value', 5.0)
            
            prompt = f"""
NQ Futures Trading Analysis

Market Summary: {summary}

Current NQ Price: {current_price:.2f}
Tick Size: {tick_size}
Tick Value: ${tick_value}

Based on the market analysis above, provide your trading recommendation:

1. Action: BUY, SELL, or HOLD
2. Confidence: 1-10 (10 being highest)
3. Entry Price: Specific price level
4. Stop Loss: Risk management level
5. Take Profit: Target price level
6. Position Size: Recommended contracts (1-3)
7. Reasoning: Brief explanation of your decision

Focus on:
- Pattern confirmation and breakout potential
- Momentum and thrust signals
- Liquidity levels and fair value gaps
- Risk-reward ratio
- Market structure

Respond in the following format:
ACTION: [BUY/SELL/HOLD]
CONFIDENCE: [1-10]
ENTRY: [price]
STOP_LOSS: [price]
TAKE_PROFIT: [price]
SIZE: [contracts]
REASONING: [brief explanation]
"""
            
            return prompt.strip()
            
        except Exception as e:
            logger.error(f"Error creating trading prompt: {e}")
            return f"Error creating prompt: {e}"
            
    def parse_llm_response(self, response: str) -> Dict[str, Any]:
        """
        Parse LLM response into structured trading signal.
        
        Args:
            response: LLM response text
            
        Returns:
            Structured trading signal
        """
        try:
            signal = {
                'action': 'HOLD',
                'confidence': 0,
                'entry_price': None,
                'stop_loss': None,
                'take_profit': None,
                'position_size': 1,
                'reasoning': ''
            }
            
            lines = response.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                if line.startswith('ACTION:'):
                    signal['action'] = line.split(':', 1)[1].strip().upper()
                elif line.startswith('CONFIDENCE:'):
                    try:
                        signal['confidence'] = int(line.split(':', 1)[1].strip())
                    except:
                        signal['confidence'] = 0
                elif line.startswith('ENTRY:'):
                    try:
                        signal['entry_price'] = float(line.split(':', 1)[1].strip())
                    except:
                        signal['entry_price'] = None
                elif line.startswith('STOP_LOSS:'):
                    try:
                        signal['stop_loss'] = float(line.split(':', 1)[1].strip())
                    except:
                        signal['stop_loss'] = None
                elif line.startswith('TAKE_PROFIT:'):
                    try:
                        signal['take_profit'] = float(line.split(':', 1)[1].strip())
                    except:
                        signal['take_profit'] = None
                elif line.startswith('SIZE:'):
                    try:
                        signal['position_size'] = int(line.split(':', 1)[1].strip())
                    except:
                        signal['position_size'] = 1
                elif line.startswith('REASONING:'):
                    signal['reasoning'] = line.split(':', 1)[1].strip()
                    
            return signal
            
        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
            return {
                'action': 'HOLD',
                'confidence': 0,
                'entry_price': None,
                'stop_loss': None,
                'take_profit': None,
                'position_size': 1,
                'reasoning': f'Error parsing response: {e}'
            }