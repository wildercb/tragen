"""
Agent Configuration System
==========================

Enhanced configuration management for trading agents with live updates
and market-aware behavior.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
import yaml
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class AgentPersonality(BaseModel):
    """Define agent personality and behavior traits."""
    
    name: str = Field(description="Agent name/identifier")
    risk_tolerance: float = Field(default=0.5, ge=0.0, le=1.0, description="Risk tolerance (0=conservative, 1=aggressive)")
    confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum confidence for signals")
    analysis_style: str = Field(default="balanced", description="Analysis style: conservative, balanced, aggressive")
    trading_frequency: str = Field(default="medium", description="Trading frequency: low, medium, high")
    
    # Market focus areas
    focus_areas: List[str] = Field(default=["price_action", "volume", "momentum"], description="Key analysis areas")
    
    # Trading preferences
    preferred_timeframes: List[str] = Field(default=["5m", "15m", "1h"], description="Preferred analysis timeframes")
    max_position_size: float = Field(default=1.0, ge=0.1, le=5.0, description="Maximum position size multiplier")
    
    # Behavioral traits
    contrarian_tendency: float = Field(default=0.2, ge=0.0, le=1.0, description="Tendency to go against crowd")
    trend_following: float = Field(default=0.8, ge=0.0, le=1.0, description="Trend following vs mean reversion")
    
class AgentStrategy(BaseModel):
    """Define agent trading strategy parameters."""
    
    strategy_name: str = Field(description="Strategy identifier")
    enabled: bool = Field(default=True, description="Whether strategy is active")
    
    # Entry conditions
    entry_conditions: Dict[str, Any] = Field(default_factory=dict, description="Entry signal conditions")
    exit_conditions: Dict[str, Any] = Field(default_factory=dict, description="Exit signal conditions")
    
    # Risk management
    stop_loss_pct: float = Field(default=0.5, ge=0.1, le=5.0, description="Stop loss percentage")
    take_profit_pct: float = Field(default=1.5, ge=0.1, le=10.0, description="Take profit percentage")
    
    # Timing
    min_signal_gap_minutes: int = Field(default=15, ge=1, le=240, description="Minimum time between signals")
    market_hours_only: bool = Field(default=True, description="Only trade during market hours")
    
class AgentConfig(BaseModel):
    """Complete agent configuration."""
    
    # Basic info
    agent_id: str = Field(description="Unique agent identifier")
    agent_type: str = Field(description="Agent type: analysis, execution, risk")
    created_at: datetime = Field(default_factory=datetime.now)
    
    # Personality and behavior
    personality: AgentPersonality = Field(default_factory=AgentPersonality)
    
    # Strategies
    strategies: List[AgentStrategy] = Field(default_factory=list)
    
    # LLM configuration
    llm_config: Dict[str, Any] = Field(default_factory=dict)
    
    # Market settings
    symbols: List[str] = Field(default=["NQ=F"], description="Symbols to trade")
    active_hours: Dict[str, Any] = Field(default_factory=dict, description="Custom active hours")
    
    # Performance tracking
    performance_stats: Dict[str, Any] = Field(default_factory=dict)
    
    # Custom instructions
    custom_instructions: str = Field(default="", description="Custom trading instructions")
    
    def to_prompt_context(self) -> str:
        """Generate context for LLM prompts based on configuration."""
        context_parts = [
            f"Agent Name: {self.personality.name}",
            f"Trading Style: {self.personality.analysis_style}",
            f"Risk Tolerance: {self.personality.risk_tolerance:.1f}/1.0",
            f"Confidence Threshold: {self.personality.confidence_threshold:.1f}",
            f"Focus Areas: {', '.join(self.personality.focus_areas)}",
            f"Preferred Timeframes: {', '.join(self.personality.preferred_timeframes)}",
        ]
        
        if self.custom_instructions:
            context_parts.append(f"Special Instructions: {self.custom_instructions}")
        
        return "\n".join(context_parts)

class AgentConfigManager:
    """Manages agent configurations with live updates."""
    
    def __init__(self, config_dir: str = None):
        self.config_dir = Path(config_dir) if config_dir else Path(__file__).parent
        self.configs_file = self.config_dir / "agent_configs.yaml"
        self.active_configs: Dict[str, AgentConfig] = {}
        self._load_configs()
    
    def _load_configs(self):
        """Load agent configurations from file."""
        if self.configs_file.exists():
            try:
                with open(self.configs_file, 'r') as f:
                    data = yaml.safe_load(f)
                    
                for agent_id, config_data in data.get('agents', {}).items():
                    self.active_configs[agent_id] = AgentConfig(**config_data)
                    
                logger.info(f"Loaded {len(self.active_configs)} agent configurations")
            except Exception as e:
                logger.error(f"Failed to load agent configs: {e}")
    
    def save_configs(self):
        """Save current configurations to file."""
        try:
            data = {
                'agents': {
                    agent_id: config.dict() 
                    for agent_id, config in self.active_configs.items()
                }
            }
            
            with open(self.configs_file, 'w') as f:
                yaml.dump(data, f, default_flow_style=False, indent=2)
                
            logger.info(f"Saved {len(self.active_configs)} agent configurations")
        except Exception as e:
            logger.error(f"Failed to save agent configs: {e}")
    
    def create_agent_config(
        self, 
        agent_type: str, 
        name: str = None, 
        custom_settings: Dict[str, Any] = None
    ) -> AgentConfig:
        """Create a new agent configuration."""
        agent_id = f"{agent_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Default personality based on agent type
        personality_defaults = {
            "analysis": {
                "risk_tolerance": 0.3,
                "analysis_style": "conservative",
                "focus_areas": ["technical_indicators", "pattern_recognition", "volume_analysis"]
            },
            "execution": {
                "risk_tolerance": 0.6,
                "analysis_style": "balanced", 
                "focus_areas": ["price_action", "momentum", "market_structure"]
            },
            "risk": {
                "risk_tolerance": 0.1,
                "analysis_style": "conservative",
                "focus_areas": ["risk_metrics", "position_sizing", "drawdown_control"]
            }
        }
        
        personality_config = personality_defaults.get(agent_type, {})
        if name:
            personality_config["name"] = name
        
        personality = AgentPersonality(**personality_config)
        
        # Default strategies based on agent type
        strategies = []
        if agent_type == "analysis":
            strategies.append(AgentStrategy(
                strategy_name="technical_analysis",
                entry_conditions={"rsi_oversold": 30, "volume_spike": 1.5},
                exit_conditions={"rsi_overbought": 70, "profit_target": 1.5}
            ))
        
        config = AgentConfig(
            agent_id=agent_id,
            agent_type=agent_type,
            personality=personality,
            strategies=strategies
        )
        
        # Apply custom settings
        if custom_settings:
            for key, value in custom_settings.items():
                if hasattr(config, key):
                    setattr(config, key, value)
        
        self.active_configs[agent_id] = config
        self.save_configs()
        
        return config
    
    def update_agent_config(self, agent_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing agent configuration."""
        if agent_id not in self.active_configs:
            return False
        
        config = self.active_configs[agent_id]
        
        try:
            # Handle nested updates
            for key, value in updates.items():
                if key == "personality" and isinstance(value, dict):
                    for p_key, p_value in value.items():
                        setattr(config.personality, p_key, p_value)
                elif hasattr(config, key):
                    setattr(config, key, value)
            
            self.save_configs()
            logger.info(f"Updated configuration for agent {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update agent config: {e}")
            return False
    
    def get_agent_config(self, agent_id: str) -> Optional[AgentConfig]:
        """Get configuration for a specific agent."""
        return self.active_configs.get(agent_id)
    
    def list_agent_configs(self) -> Dict[str, AgentConfig]:
        """Get all agent configurations."""
        return self.active_configs.copy()
    
    def delete_agent_config(self, agent_id: str) -> bool:
        """Delete an agent configuration."""
        if agent_id in self.active_configs:
            del self.active_configs[agent_id]
            self.save_configs()
            return True
        return False
    
    def get_presets(self) -> Dict[str, Dict[str, Any]]:
        """Get preset configurations for quick agent creation."""
        return {
            "conservative_analyzer": {
                "agent_type": "analysis",
                "personality": {
                    "name": "Conservative Analyzer",
                    "risk_tolerance": 0.2,
                    "analysis_style": "conservative",
                    "confidence_threshold": 0.8,
                    "focus_areas": ["support_resistance", "trend_analysis", "volume_confirmation"]
                },
                "custom_instructions": "Focus on high-probability setups with strong confirmation signals. Prioritize capital preservation over frequent trading."
            },
            "momentum_trader": {
                "agent_type": "execution",
                "personality": {
                    "name": "Momentum Trader",
                    "risk_tolerance": 0.7,
                    "analysis_style": "aggressive",
                    "confidence_threshold": 0.6,
                    "focus_areas": ["momentum", "breakouts", "volume_spikes"]
                },
                "custom_instructions": "Look for strong momentum breakouts with high volume. Quick entries and exits on trend continuation patterns."
            },
            "mean_reversion": {
                "agent_type": "analysis", 
                "personality": {
                    "name": "Mean Reversion Specialist",
                    "risk_tolerance": 0.4,
                    "analysis_style": "balanced",
                    "contrarian_tendency": 0.8,
                    "trend_following": 0.3,
                    "focus_areas": ["rsi", "bollinger_bands", "oversold_conditions"]
                },
                "custom_instructions": "Identify oversold/overbought conditions for mean reversion trades. Wait for extreme readings and reversal confirmation."
            },
            "risk_guardian": {
                "agent_type": "risk",
                "personality": {
                    "name": "Risk Guardian",
                    "risk_tolerance": 0.1,
                    "analysis_style": "conservative",
                    "confidence_threshold": 0.9,
                    "focus_areas": ["position_sizing", "correlation", "drawdown"]
                },
                "custom_instructions": "Monitor all positions for risk limits. Alert on excessive exposure or correlation. Prioritize capital preservation above all else."
            }
        }