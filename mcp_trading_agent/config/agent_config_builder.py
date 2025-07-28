"""
Agent Configuration Builder
===========================

Easy-to-use configuration system for creating and managing trading agents.
"""

import json
import yaml
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""
    pass

class TradingStyle(Enum):
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"
    SCALPER = "scalper"
    SWING_TRADER = "swing_trader"

class RiskLevel(Enum):
    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"

@dataclass
class PersonalityConfig:
    """User-friendly personality configuration."""
    name: str
    trading_style: TradingStyle
    risk_level: RiskLevel
    max_trades_per_day: int = 10
    confidence_required: float = 0.6  # 0-1 scale
    preferred_timeframes: List[str] = None
    market_focus: List[str] = None
    
    def __post_init__(self):
        if self.preferred_timeframes is None:
            self.preferred_timeframes = ["15m", "1h"]
        if self.market_focus is None:
            self.market_focus = ["NQ"]

@dataclass
class RiskConfig:
    """User-friendly risk management configuration."""
    max_loss_per_trade_percent: float = 1.0  # 1% default
    max_daily_loss_percent: float = 3.0      # 3% default
    stop_loss_percent: float = 0.5           # 0.5% default
    take_profit_ratio: float = 2.0           # 2:1 reward:risk
    position_sizing_method: str = "fixed_percentage"
    
@dataclass
class AnalysisConfig:
    """Analysis method configuration."""
    use_technical_analysis: bool = True
    use_sentiment_analysis: bool = False
    use_fundamental_analysis: bool = False
    use_ai_analysis: bool = True
    technical_weight: float = 0.6
    ai_weight: float = 0.4
    sentiment_weight: float = 0.0
    fundamental_weight: float = 0.0

@dataclass
class TradingConfig:
    """Trading behavior configuration."""
    paper_trading_only: bool = True
    auto_trading_enabled: bool = False
    trading_hours_start: str = "09:30"
    trading_hours_end: str = "16:00"
    trade_weekends: bool = False
    max_position_value: float = 50000
    
@dataclass
class SimpleAgentConfig:
    """Complete agent configuration in user-friendly format."""
    agent_name: str
    personality: PersonalityConfig
    risk_management: RiskConfig
    analysis_methods: AnalysisConfig
    trading_settings: TradingConfig
    data_sources: List[str] = None
    prompts_and_guides: Dict[str, str] = None
    
    def __post_init__(self):
        if self.data_sources is None:
            self.data_sources = ["yahoo_finance", "tradingview"]
        if self.prompts_and_guides is None:
            self.prompts_and_guides = {}

class AgentConfigBuilder:
    """
    Builder class for creating agent configurations with validation and templates.
    """
    
    def __init__(self):
        self.risk_level_mappings = {
            RiskLevel.VERY_LOW: {
                'risk_tolerance': 1.0,
                'max_loss_per_trade': 0.005,
                'max_daily_loss': 0.01,
                'stop_loss_percentage': 0.002,
                'confidence_threshold': 0.9
            },
            RiskLevel.LOW: {
                'risk_tolerance': 2.5,
                'max_loss_per_trade': 0.01,
                'max_daily_loss': 0.02,
                'stop_loss_percentage': 0.005,
                'confidence_threshold': 0.8
            },
            RiskLevel.MODERATE: {
                'risk_tolerance': 5.0,
                'max_loss_per_trade': 0.015,
                'max_daily_loss': 0.04,
                'stop_loss_percentage': 0.01,
                'confidence_threshold': 0.6
            },
            RiskLevel.HIGH: {
                'risk_tolerance': 7.5,
                'max_loss_per_trade': 0.025,
                'max_daily_loss': 0.06,
                'stop_loss_percentage': 0.015,
                'confidence_threshold': 0.5
            },
            RiskLevel.VERY_HIGH: {
                'risk_tolerance': 9.0,
                'max_loss_per_trade': 0.04,
                'max_daily_loss': 0.10,
                'stop_loss_percentage': 0.02,
                'confidence_threshold': 0.4
            }
        }
        
        self.style_mappings = {
            TradingStyle.CONSERVATIVE: {
                'analysis_style': 'conservative',
                'time_horizon': 'swing',
                'max_trades_per_day': 3,
                'preferred_timeframes': ['1h', '4h', '1d']
            },
            TradingStyle.BALANCED: {
                'analysis_style': 'balanced',
                'time_horizon': 'day',
                'max_trades_per_day': 8,
                'preferred_timeframes': ['15m', '1h', '4h']
            },
            TradingStyle.AGGRESSIVE: {
                'analysis_style': 'aggressive',
                'time_horizon': 'day',
                'max_trades_per_day': 15,
                'preferred_timeframes': ['5m', '15m', '1h']
            },
            TradingStyle.SCALPER: {
                'analysis_style': 'scalper',
                'time_horizon': 'scalping',
                'max_trades_per_day': 50,
                'preferred_timeframes': ['1m', '5m']
            },
            TradingStyle.SWING_TRADER: {
                'analysis_style': 'swing_trader',
                'time_horizon': 'swing',
                'max_trades_per_day': 2,
                'preferred_timeframes': ['4h', '1d', '1w']
            }
        }
        
    def create_quick_config(
        self,
        agent_name: str,
        trading_style: Union[str, TradingStyle],
        risk_level: Union[str, RiskLevel],
        **kwargs
    ) -> SimpleAgentConfig:
        """Create a quick configuration with sensible defaults."""
        
        # Convert strings to enums if needed
        if isinstance(trading_style, str):
            trading_style = TradingStyle(trading_style.lower())
        if isinstance(risk_level, str):
            risk_level = RiskLevel(risk_level.lower())
            
        # Get style defaults
        style_defaults = self.style_mappings[trading_style]
        risk_defaults = self.risk_level_mappings[risk_level]
        
        # Create personality config
        personality = PersonalityConfig(
            name=agent_name,
            trading_style=trading_style,
            risk_level=risk_level,
            max_trades_per_day=kwargs.get('max_trades_per_day', style_defaults['max_trades_per_day']),
            confidence_required=kwargs.get('confidence_required', risk_defaults['confidence_threshold']),
            preferred_timeframes=kwargs.get('preferred_timeframes', style_defaults['preferred_timeframes']),
            market_focus=kwargs.get('market_focus', ['NQ'])
        )
        
        # Create risk config
        risk_config = RiskConfig(
            max_loss_per_trade_percent=kwargs.get('max_loss_per_trade_percent', risk_defaults['max_loss_per_trade'] * 100),
            max_daily_loss_percent=kwargs.get('max_daily_loss_percent', risk_defaults['max_daily_loss'] * 100),
            stop_loss_percent=kwargs.get('stop_loss_percent', risk_defaults['stop_loss_percentage'] * 100),
            take_profit_ratio=kwargs.get('take_profit_ratio', 2.0)
        )
        
        # Create analysis config
        analysis_config = AnalysisConfig(
            use_technical_analysis=kwargs.get('use_technical_analysis', True),
            use_ai_analysis=kwargs.get('use_ai_analysis', True),
            technical_weight=kwargs.get('technical_weight', 0.6),
            ai_weight=kwargs.get('ai_weight', 0.4)
        )
        
        # Create trading config
        trading_config = TradingConfig(
            paper_trading_only=kwargs.get('paper_trading_only', True),
            auto_trading_enabled=kwargs.get('auto_trading_enabled', False),
            max_position_value=kwargs.get('max_position_value', 50000)
        )
        
        return SimpleAgentConfig(
            agent_name=agent_name,
            personality=personality,
            risk_management=risk_config,
            analysis_methods=analysis_config,
            trading_settings=trading_config
        )
        
    def convert_to_production_config(self, simple_config: SimpleAgentConfig) -> Dict[str, Any]:
        """Convert simple config to production agent configuration."""
        
        # Get risk and style mappings
        risk_mapping = self.risk_level_mappings[simple_config.personality.risk_level]
        style_mapping = self.style_mappings[simple_config.personality.trading_style]
        
        # Build production config
        production_config = {
            'agent_id': simple_config.agent_name.lower().replace(' ', '_'),
            'personality': {
                'name': simple_config.personality.name,
                'risk_tolerance': risk_mapping['risk_tolerance'],
                'analysis_style': style_mapping['analysis_style'],
                'time_horizon': style_mapping['time_horizon'],
                'market_focus': simple_config.personality.market_focus,
                'confidence_threshold': simple_config.personality.confidence_required,
                'max_trades_per_day': simple_config.personality.max_trades_per_day,
                'max_position_size': simple_config.trading_settings.max_position_value,
                'preferred_timeframes': simple_config.personality.preferred_timeframes
            },
            'risk_profile': {
                'max_loss_per_trade': simple_config.risk_management.max_loss_per_trade_percent / 100,
                'max_daily_loss': simple_config.risk_management.max_daily_loss_percent / 100,
                'max_drawdown': simple_config.risk_management.max_daily_loss_percent / 100 * 2,
                'stop_loss_percentage': simple_config.risk_management.stop_loss_percent / 100,
                'take_profit_ratio': simple_config.risk_management.take_profit_ratio,
                'position_sizing_method': simple_config.risk_management.position_sizing_method,
                'risk_adjustment_factor': 1.0
            },
            'decision_engine': {
                'analysis_models': self._get_analysis_models(simple_config.analysis_methods),
                'ensemble_method': 'weighted_average',
                'model_weights': self._get_model_weights(simple_config.analysis_methods)
            },
            'trading_enabled': not simple_config.trading_settings.paper_trading_only,
            'auto_trading': simple_config.trading_settings.auto_trading_enabled,
            'paper_trading': simple_config.trading_settings.paper_trading_only,
            'learning_enabled': True,
            'data_sources': simple_config.data_sources,
            'loaded_prompts': simple_config.prompts_and_guides,
            'loaded_guides': {}
        }
        
        return production_config
        
    def _get_analysis_models(self, analysis_config: AnalysisConfig) -> List[str]:
        """Get list of analysis models based on configuration."""
        models = []
        
        if analysis_config.use_technical_analysis:
            models.append('technical')
        if analysis_config.use_sentiment_analysis:
            models.append('sentiment')
        if analysis_config.use_fundamental_analysis:
            models.append('fundamental')
        if analysis_config.use_ai_analysis:
            models.append('ai_model')
            
        return models if models else ['technical']  # Always have at least one
        
    def _get_model_weights(self, analysis_config: AnalysisConfig) -> Dict[str, float]:
        """Get model weights based on configuration."""
        weights = {}
        
        if analysis_config.use_technical_analysis:
            weights['technical'] = analysis_config.technical_weight
        if analysis_config.use_sentiment_analysis:
            weights['sentiment'] = analysis_config.sentiment_weight
        if analysis_config.use_fundamental_analysis:
            weights['fundamental'] = analysis_config.fundamental_weight
        if analysis_config.use_ai_analysis:
            weights['ai_model'] = analysis_config.ai_weight
            
        # Normalize weights
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {k: v / total_weight for k, v in weights.items()}
        else:
            weights = {'technical': 1.0}
            
        return weights
        
    def validate_config(self, config: SimpleAgentConfig) -> List[str]:
        """Validate configuration and return list of issues."""
        issues = []
        
        # Validate personality
        if not config.personality.name or len(config.personality.name.strip()) == 0:
            issues.append("Agent name is required")
            
        if config.personality.confidence_required < 0 or config.personality.confidence_required > 1:
            issues.append("Confidence required must be between 0 and 1")
            
        if config.personality.max_trades_per_day < 1:
            issues.append("Max trades per day must be at least 1")
            
        # Validate risk management
        if config.risk_management.max_loss_per_trade_percent <= 0:
            issues.append("Max loss per trade must be positive")
            
        if config.risk_management.max_daily_loss_percent <= 0:
            issues.append("Max daily loss must be positive")
            
        if config.risk_management.stop_loss_percent <= 0:
            issues.append("Stop loss percentage must be positive")
            
        if config.risk_management.take_profit_ratio <= 0:
            issues.append("Take profit ratio must be positive")
            
        # Validate analysis methods
        total_analysis_weight = (
            config.analysis_methods.technical_weight +
            config.analysis_methods.ai_weight +
            config.analysis_methods.sentiment_weight +
            config.analysis_methods.fundamental_weight
        )
        
        if total_analysis_weight == 0:
            issues.append("At least one analysis method must be enabled")
            
        # Validate trading settings
        if config.trading_settings.max_position_value <= 0:
            issues.append("Max position value must be positive")
            
        return issues
        
    def save_config(self, config: SimpleAgentConfig, file_path: Union[str, Path], format: str = 'yaml'):
        """Save configuration to file."""
        
        file_path = Path(file_path)
        
        # Validate config first
        issues = self.validate_config(config)
        if issues:
            raise ConfigValidationError(f"Configuration validation failed: {', '.join(issues)}")
            
        # Convert to dictionary
        config_dict = asdict(config)
        
        # Convert enums to strings
        config_dict['personality']['trading_style'] = config.personality.trading_style.value
        config_dict['personality']['risk_level'] = config.personality.risk_level.value
        
        # Save file
        try:
            if format.lower() == 'json':
                with open(file_path, 'w') as f:
                    json.dump(config_dict, f, indent=2, default=str)
            else:  # yaml
                with open(file_path, 'w') as f:
                    yaml.dump(config_dict, f, default_flow_style=False)
                    
            logger.info(f"Configuration saved to {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            raise
            
    def load_config(self, file_path: Union[str, Path]) -> SimpleAgentConfig:
        """Load configuration from file."""
        
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
            
        try:
            # Load file
            with open(file_path, 'r') as f:
                if file_path.suffix.lower() == '.json':
                    config_dict = json.load(f)
                else:  # yaml
                    config_dict = yaml.safe_load(f)
                    
            # Convert back to objects
            personality_dict = config_dict['personality']
            personality_dict['trading_style'] = TradingStyle(personality_dict['trading_style'])
            personality_dict['risk_level'] = RiskLevel(personality_dict['risk_level'])
            
            personality = PersonalityConfig(**personality_dict)
            risk_management = RiskConfig(**config_dict['risk_management'])
            analysis_methods = AnalysisConfig(**config_dict['analysis_methods'])
            trading_settings = TradingConfig(**config_dict['trading_settings'])
            
            config = SimpleAgentConfig(
                agent_name=config_dict['agent_name'],
                personality=personality,
                risk_management=risk_management,
                analysis_methods=analysis_methods,
                trading_settings=trading_settings,
                data_sources=config_dict.get('data_sources', []),
                prompts_and_guides=config_dict.get('prompts_and_guides', {})
            )
            
            logger.info(f"Configuration loaded from {file_path}")
            return config
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise
            
    def get_preset_configs(self) -> Dict[str, SimpleAgentConfig]:
        """Get predefined configuration presets."""
        
        presets = {}
        
        # Conservative Day Trader
        presets['conservative_day_trader'] = self.create_quick_config(
            agent_name="Conservative Day Trader",
            trading_style=TradingStyle.CONSERVATIVE,
            risk_level=RiskLevel.LOW,
            max_trades_per_day=5,
            confidence_required=0.8,
            paper_trading_only=True
        )
        
        # Balanced Swing Trader
        presets['balanced_swing_trader'] = self.create_quick_config(
            agent_name="Balanced Swing Trader",
            trading_style=TradingStyle.SWING_TRADER,
            risk_level=RiskLevel.MODERATE,
            max_trades_per_day=3,
            confidence_required=0.6,
            paper_trading_only=True
        )
        
        # Aggressive Scalper
        presets['aggressive_scalper'] = self.create_quick_config(
            agent_name="Aggressive Scalper",
            trading_style=TradingStyle.SCALPER,
            risk_level=RiskLevel.HIGH,
            max_trades_per_day=30,
            confidence_required=0.5,
            paper_trading_only=True
        )
        
        # AI-Focused Trader
        presets['ai_focused_trader'] = self.create_quick_config(
            agent_name="AI-Focused Trader",
            trading_style=TradingStyle.BALANCED,
            risk_level=RiskLevel.MODERATE,
            use_technical_analysis=True,
            use_ai_analysis=True,
            technical_weight=0.3,
            ai_weight=0.7,
            paper_trading_only=True
        )
        
        return presets
        
    def create_config_wizard(self) -> Dict[str, Any]:
        """Create a configuration wizard structure for UI."""
        
        return {
            'steps': [
                {
                    'id': 'basic_info',
                    'title': 'Basic Information',
                    'description': 'Set up your agent\'s basic information',
                    'fields': [
                        {
                            'name': 'agent_name',
                            'label': 'Agent Name',
                            'type': 'text',
                            'required': True,
                            'placeholder': 'My Trading Agent'
                        }
                    ]
                },
                {
                    'id': 'trading_style',
                    'title': 'Trading Style',
                    'description': 'Choose your preferred trading approach',
                    'fields': [
                        {
                            'name': 'trading_style',
                            'label': 'Trading Style',
                            'type': 'select',
                            'required': True,
                            'options': [
                                {'value': 'conservative', 'label': 'Conservative - Steady, low-risk approach'},
                                {'value': 'balanced', 'label': 'Balanced - Moderate risk and reward'},
                                {'value': 'aggressive', 'label': 'Aggressive - Higher risk for higher rewards'},
                                {'value': 'scalper', 'label': 'Scalper - Quick, frequent trades'},
                                {'value': 'swing_trader', 'label': 'Swing Trader - Hold positions for days/weeks'}
                            ]
                        },
                        {
                            'name': 'risk_level',
                            'label': 'Risk Level',
                            'type': 'select',
                            'required': True,
                            'options': [
                                {'value': 'very_low', 'label': 'Very Low - Maximum safety'},
                                {'value': 'low', 'label': 'Low - Conservative approach'},
                                {'value': 'moderate', 'label': 'Moderate - Balanced risk'},
                                {'value': 'high', 'label': 'High - Aggressive trading'},
                                {'value': 'very_high', 'label': 'Very High - Maximum risk'}
                            ]
                        }
                    ]
                },
                {
                    'id': 'risk_management',
                    'title': 'Risk Management',
                    'description': 'Configure your risk tolerance and safety limits',
                    'fields': [
                        {
                            'name': 'max_loss_per_trade_percent',
                            'label': 'Maximum Loss Per Trade (%)',
                            'type': 'number',
                            'min': 0.1,
                            'max': 10.0,
                            'step': 0.1,
                            'default': 1.0
                        },
                        {
                            'name': 'max_daily_loss_percent',
                            'label': 'Maximum Daily Loss (%)',
                            'type': 'number',
                            'min': 0.5,
                            'max': 20.0,
                            'step': 0.5,
                            'default': 3.0
                        },
                        {
                            'name': 'confidence_required',
                            'label': 'Minimum Confidence Required',
                            'type': 'slider',
                            'min': 0.3,
                            'max': 0.9,
                            'step': 0.1,
                            'default': 0.6
                        }
                    ]
                },
                {
                    'id': 'analysis_methods',
                    'title': 'Analysis Methods',
                    'description': 'Choose how your agent analyzes the market',
                    'fields': [
                        {
                            'name': 'use_technical_analysis',
                            'label': 'Use Technical Analysis',
                            'type': 'checkbox',
                            'default': True
                        },
                        {
                            'name': 'use_ai_analysis',
                            'label': 'Use AI Analysis',
                            'type': 'checkbox',
                            'default': True
                        },
                        {
                            'name': 'technical_weight',
                            'label': 'Technical Analysis Weight',
                            'type': 'slider',
                            'min': 0.0,
                            'max': 1.0,
                            'step': 0.1,
                            'default': 0.6,
                            'conditional': 'use_technical_analysis'
                        },
                        {
                            'name': 'ai_weight',
                            'label': 'AI Analysis Weight',
                            'type': 'slider',
                            'min': 0.0,
                            'max': 1.0,
                            'step': 0.1,
                            'default': 0.4,
                            'conditional': 'use_ai_analysis'
                        }
                    ]
                },
                {
                    'id': 'trading_settings',
                    'title': 'Trading Settings',
                    'description': 'Configure trading behavior and safety settings',
                    'fields': [
                        {
                            'name': 'paper_trading_only',
                            'label': 'Paper Trading Only (Recommended)',
                            'type': 'checkbox',
                            'default': True,
                            'description': 'Trade with virtual money only'
                        },
                        {
                            'name': 'max_trades_per_day',
                            'label': 'Maximum Trades Per Day',
                            'type': 'number',
                            'min': 1,
                            'max': 100,
                            'default': 10
                        },
                        {
                            'name': 'max_position_value',
                            'label': 'Maximum Position Value ($)',
                            'type': 'number',
                            'min': 1000,
                            'max': 1000000,
                            'step': 1000,
                            'default': 50000
                        }
                    ]
                }
            ],
            'presets': list(self.get_preset_configs().keys()),
            'validation_rules': {
                'agent_name': 'required|min:1|max:50',
                'trading_style': 'required|in:conservative,balanced,aggressive,scalper,swing_trader',
                'risk_level': 'required|in:very_low,low,moderate,high,very_high',
                'max_loss_per_trade_percent': 'required|numeric|min:0.1|max:10',
                'max_daily_loss_percent': 'required|numeric|min:0.5|max:20',
                'confidence_required': 'required|numeric|min:0.3|max:0.9',
                'max_trades_per_day': 'required|integer|min:1|max:100',
                'max_position_value': 'required|numeric|min:1000|max:1000000'
            }
        }

def create_sample_configs():
    """Create sample configuration files."""
    
    builder = AgentConfigBuilder()
    config_dir = Path("configs/agents")
    config_dir.mkdir(parents=True, exist_ok=True)
    
    # Create preset configs
    presets = builder.get_preset_configs()
    
    for name, config in presets.items():
        file_path = config_dir / f"{name}.yaml"
        builder.save_config(config, file_path)
        
    logger.info(f"Created {len(presets)} sample configurations in {config_dir}")

if __name__ == "__main__":
    # Create sample configurations
    create_sample_configs()