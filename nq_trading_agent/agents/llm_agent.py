"""
LLM Analysis Agent for NQ futures trading
"""

import asyncio
import logging
from typing import Dict, Any, Optional
import pandas as pd
from datetime import datetime

from ..utils.llm_factory import LLMFactory
from ..preprocessing.features import FeatureExtractor
from ..preprocessing.summarizer import DataSummarizer

logger = logging.getLogger(__name__)


class LLMAnalysisAgent:
    """
    LLM-based analysis agent for NQ futures trading decisions.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize LLM analysis agent.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.llm_config = config.get('llm', {})
        self.preprocessing_config = config.get('preprocessing', {})
        self.trading_config = config.get('trading', {})
        
        # Initialize components
        self.llm_provider = LLMFactory.create_provider(self.llm_config)
        self.feature_extractor = FeatureExtractor(self.preprocessing_config)
        self.data_summarizer = DataSummarizer(self.preprocessing_config.get('summarization', {}))
        
        # Analysis state
        self.last_analysis_time = None
        self.last_signal = None
        self.analysis_history = []
        
    async def analyze_market(self, data: pd.DataFrame, nq_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze market data and generate trading signal.
        
        Args:
            data: Market data DataFrame
            nq_config: NQ contract configuration
            
        Returns:
            Trading signal and analysis
        """
        try:
            start_time = datetime.now()
            
            # Extract features
            logger.info("Extracting features from market data")
            features = self.feature_extractor.extract_all_features(data)
            
            # Summarize features
            logger.info("Summarizing features for LLM")
            summary = self.data_summarizer.summarize_features(features, data)
            
            # Create trading prompt
            current_price = data['close'].iloc[-1]
            prompt = self.data_summarizer.create_trading_prompt(summary, current_price, nq_config)
            
            # Get LLM analysis
            logger.info("Querying LLM for trading decision")
            llm_response = await self.llm_provider.generate_response(prompt)
            
            # Parse response
            signal = self.data_summarizer.parse_llm_response(llm_response)
            
            # Add metadata
            analysis_result = {
                'timestamp': start_time,
                'signal': signal,
                'features': features,
                'summary': summary,
                'llm_response': llm_response,
                'current_price': current_price,
                'processing_time': (datetime.now() - start_time).total_seconds()
            }
            
            # Store analysis
            self.last_analysis_time = start_time
            self.last_signal = signal
            self.analysis_history.append(analysis_result)
            
            # Keep only last 100 analyses
            if len(self.analysis_history) > 100:
                self.analysis_history = self.analysis_history[-100:]
                
            logger.info(f"Analysis completed: {signal['action']} with confidence {signal['confidence']}")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error in market analysis: {e}")
            return {
                'timestamp': datetime.now(),
                'signal': {
                    'action': 'HOLD',
                    'confidence': 0,
                    'entry_price': None,
                    'stop_loss': None,
                    'take_profit': None,
                    'position_size': 1,
                    'reasoning': f'Analysis error: {e}'
                },
                'error': str(e)
            }
            
    async def stream_analysis(self, data_stream, nq_config: Dict[str, Any], analysis_interval: int = 60):
        """
        Stream continuous analysis of market data.
        
        Args:
            data_stream: Async generator of market data
            nq_config: NQ contract configuration
            analysis_interval: Analysis interval in seconds
            
        Yields:
            Analysis results
        """
        data_buffer = []
        last_analysis = datetime.now()
        
        try:
            async for market_data in data_stream:
                # Add to buffer
                data_buffer.append(market_data)
                
                # Keep only last 1000 data points
                if len(data_buffer) > 1000:
                    data_buffer = data_buffer[-1000:]
                    
                # Check if it's time for analysis
                now = datetime.now()
                if (now - last_analysis).total_seconds() >= analysis_interval:
                    if len(data_buffer) >= 50:  # Minimum data points for analysis
                        # Convert buffer to DataFrame
                        df = pd.DataFrame(data_buffer)
                        df['timestamp'] = pd.to_datetime(df['timestamp'])
                        df.set_index('timestamp', inplace=True)
                        
                        # Analyze
                        analysis = await self.analyze_market(df, nq_config)
                        yield analysis
                        
                        last_analysis = now
                        
        except Exception as e:
            logger.error(f"Error in streaming analysis: {e}")
            yield {
                'timestamp': datetime.now(),
                'signal': {
                    'action': 'HOLD',
                    'confidence': 0,
                    'entry_price': None,
                    'stop_loss': None,
                    'take_profit': None,
                    'position_size': 1,
                    'reasoning': f'Streaming error: {e}'
                },
                'error': str(e)
            }
            
    def should_analyze(self, trigger_conditions: Dict[str, Any]) -> bool:
        """
        Determine if analysis should be triggered based on conditions.
        
        Args:
            trigger_conditions: Conditions that might trigger analysis
            
        Returns:
            Whether to run analysis
        """
        try:
            # Always analyze if no previous analysis
            if self.last_analysis_time is None:
                return True
                
            # Check time-based triggers
            time_since_last = (datetime.now() - self.last_analysis_time).total_seconds()
            min_interval = trigger_conditions.get('min_analysis_interval', 60)
            
            if time_since_last < min_interval:
                return False
                
            # Check price movement triggers
            price_change_threshold = trigger_conditions.get('price_change_threshold', 0.005)
            if 'price_change' in trigger_conditions:
                if abs(trigger_conditions['price_change']) > price_change_threshold:
                    return True
                    
            # Check volume spike triggers
            volume_spike_threshold = trigger_conditions.get('volume_spike_threshold', 2.0)
            if 'volume_ratio' in trigger_conditions:
                if trigger_conditions['volume_ratio'] > volume_spike_threshold:
                    return True
                    
            # Check pattern triggers
            if trigger_conditions.get('pattern_detected', False):
                return True
                
            # Check breakout triggers
            if trigger_conditions.get('breakout_detected', False):
                return True
                
            # Default: analyze if enough time has passed
            return time_since_last >= trigger_conditions.get('max_analysis_interval', 300)
            
        except Exception as e:
            logger.error(f"Error checking analysis triggers: {e}")
            return True  # Default to analyzing when in doubt
            
    def get_analysis_summary(self) -> Dict[str, Any]:
        """
        Get summary of recent analysis activity.
        
        Returns:
            Analysis summary
        """
        try:
            if not self.analysis_history:
                return {
                    'total_analyses': 0,
                    'last_analysis': None,
                    'last_signal': None,
                    'signal_distribution': {},
                    'average_confidence': 0,
                    'average_processing_time': 0
                }
                
            # Calculate statistics
            total_analyses = len(self.analysis_history)
            recent_analyses = self.analysis_history[-20:]  # Last 20 analyses
            
            # Signal distribution
            signal_counts = {}
            confidences = []
            processing_times = []
            
            for analysis in recent_analyses:
                action = analysis['signal']['action']
                signal_counts[action] = signal_counts.get(action, 0) + 1
                confidences.append(analysis['signal']['confidence'])
                processing_times.append(analysis.get('processing_time', 0))
                
            return {
                'total_analyses': total_analyses,
                'last_analysis': self.analysis_history[-1]['timestamp'],
                'last_signal': self.last_signal,
                'signal_distribution': signal_counts,
                'average_confidence': sum(confidences) / len(confidences) if confidences else 0,
                'average_processing_time': sum(processing_times) / len(processing_times) if processing_times else 0,
                'recent_analyses_count': len(recent_analyses)
            }
            
        except Exception as e:
            logger.error(f"Error generating analysis summary: {e}")
            return {'error': str(e)}
            
    def validate_signal(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and potentially modify a trading signal.
        
        Args:
            signal: Trading signal to validate
            
        Returns:
            Validated signal
        """
        try:
            validated_signal = signal.copy()
            
            # Validate action
            if validated_signal['action'] not in ['BUY', 'SELL', 'HOLD']:
                validated_signal['action'] = 'HOLD'
                validated_signal['reasoning'] += " (Invalid action corrected)"
                
            # Validate confidence
            confidence = validated_signal['confidence']
            if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 10:
                validated_signal['confidence'] = 0
                validated_signal['reasoning'] += " (Invalid confidence corrected)"
                
            # Validate prices
            if validated_signal['entry_price'] is not None:
                if validated_signal['entry_price'] <= 0:
                    validated_signal['entry_price'] = None
                    validated_signal['reasoning'] += " (Invalid entry price removed)"
                    
            # Validate stop loss
            if validated_signal['stop_loss'] is not None:
                if validated_signal['stop_loss'] <= 0:
                    validated_signal['stop_loss'] = None
                    validated_signal['reasoning'] += " (Invalid stop loss removed)"
                    
            # Validate take profit
            if validated_signal['take_profit'] is not None:
                if validated_signal['take_profit'] <= 0:
                    validated_signal['take_profit'] = None
                    validated_signal['reasoning'] += " (Invalid take profit removed)"
                    
            # Validate position size
            position_size = validated_signal['position_size']
            if not isinstance(position_size, int) or position_size < 1 or position_size > 10:
                validated_signal['position_size'] = 1
                validated_signal['reasoning'] += " (Invalid position size corrected)"
                
            # Risk-reward validation
            if (validated_signal['entry_price'] and 
                validated_signal['stop_loss'] and 
                validated_signal['take_profit']):
                
                entry = validated_signal['entry_price']
                stop = validated_signal['stop_loss']
                target = validated_signal['take_profit']
                
                # Calculate risk-reward ratio
                if validated_signal['action'] == 'BUY':
                    risk = entry - stop
                    reward = target - entry
                else:  # SELL
                    risk = stop - entry
                    reward = entry - target
                    
                if risk > 0 and reward > 0:
                    risk_reward_ratio = reward / risk
                    if risk_reward_ratio < 1.0:  # Less than 1:1 risk-reward
                        validated_signal['confidence'] = max(0, validated_signal['confidence'] - 2)
                        validated_signal['reasoning'] += f" (Poor risk-reward {risk_reward_ratio:.2f})"
                        
            return validated_signal
            
        except Exception as e:
            logger.error(f"Error validating signal: {e}")
            return signal
            
    async def close(self):
        """Clean up resources."""
        try:
            # Close LLM provider connections
            if hasattr(self.llm_provider, 'close'):
                await self.llm_provider.close()
                
            logger.info("LLM Analysis Agent closed")
            
        except Exception as e:
            logger.error(f"Error closing LLM Analysis Agent: {e}")