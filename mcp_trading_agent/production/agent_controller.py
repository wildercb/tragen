"""
Production Agent Controller
===========================

Centralized management system for trading agents in production.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Type
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json
import importlib
import inspect

from ..agents.production_trading_agent import ProductionTradingAgent, AgentStatus, TradingPersonality, RiskProfile
from .audit_logger import AuditLogger

logger = logging.getLogger(__name__)

class AgentType(Enum):
    PRODUCTION_TRADING = "production_trading"
    SCALPING = "scalping"
    SWING_TRADING = "swing_trading"
    ARBITRAGE = "arbitrage"
    CUSTOM = "custom"

@dataclass
class AgentInstance:
    agent_id: str
    agent_type: AgentType
    agent: ProductionTradingAgent
    config: Dict[str, Any]
    created_at: datetime
    last_activity: datetime
    status: AgentStatus
    performance_metrics: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.performance_metrics is None:
            self.performance_metrics = {}

@dataclass
class AgentTemplate:
    name: str
    description: str
    agent_type: AgentType
    default_config: Dict[str, Any]
    personality_presets: List[Dict[str, Any]]
    risk_presets: List[Dict[str, Any]]
    
class AgentFactory:
    """Factory for creating different types of trading agents."""
    
    def __init__(self):
        self.agent_classes: Dict[AgentType, Type] = {
            AgentType.PRODUCTION_TRADING: ProductionTradingAgent
        }
        
        # Register built-in agent types
        self._register_builtin_agents()
        
    def register_agent_type(self, agent_type: AgentType, agent_class: Type):
        """Register a custom agent type."""
        self.agent_classes[agent_type] = agent_class
        
    def create_agent(
        self, 
        agent_type: AgentType, 
        agent_id: str, 
        config: Dict[str, Any],
        mcp_server: Any,
        provider_manager: Any
    ) -> ProductionTradingAgent:
        """Create an agent instance."""
        
        if agent_type not in self.agent_classes:
            raise ValueError(f"Unknown agent type: {agent_type}")
            
        agent_class = self.agent_classes[agent_type]
        
        # Add agent_id to config
        agent_config = config.copy()
        agent_config['agent_id'] = agent_id
        
        return agent_class(agent_config, mcp_server, provider_manager)
        
    def _register_builtin_agents(self):
        """Register built-in agent types with specialized configurations."""
        
        # Scalping agent configuration
        scalping_config = {
            'personality': {
                'name': 'Scalper',
                'risk_tolerance': 3.0,
                'analysis_style': 'scalper',
                'time_horizon': 'scalping',
                'confidence_threshold': 0.7,
                'max_trades_per_day': 200,
                'preferred_timeframes': ['1m', '5m']
            },
            'risk_profile': {
                'max_loss_per_trade': 0.005,  # 0.5%
                'max_daily_loss': 0.02,       # 2%
                'stop_loss_percentage': 0.002, # 0.2%
                'take_profit_ratio': 1.5
            },
            'decision_engine': {
                'analysis_models': ['technical', 'ai_model'],
                'ensemble_method': 'weighted_average',
                'model_weights': {'technical': 0.7, 'ai_model': 0.3}
            }
        }
        
        # Swing trading agent configuration
        swing_config = {
            'personality': {
                'name': 'Swing Trader',
                'risk_tolerance': 6.0,
                'analysis_style': 'swing_trader',
                'time_horizon': 'swing',
                'confidence_threshold': 0.6,
                'max_trades_per_day': 10,
                'preferred_timeframes': ['1h', '4h', '1d']
            },
            'risk_profile': {
                'max_loss_per_trade': 0.02,   # 2%
                'max_daily_loss': 0.05,       # 5%
                'stop_loss_percentage': 0.01, # 1%
                'take_profit_ratio': 3.0
            },
            'decision_engine': {
                'analysis_models': ['technical', 'fundamental', 'ai_model'],
                'ensemble_method': 'weighted_average',
                'model_weights': {'technical': 0.4, 'fundamental': 0.3, 'ai_model': 0.3}
            }
        }
        
        # Register specialized configurations
        self.agent_configs = {
            AgentType.SCALPING: scalping_config,
            AgentType.SWING_TRADING: swing_config
        }

class ProductionAgentController:
    """
    Centralized controller for managing trading agents in production.
    
    Provides:
    - Agent lifecycle management
    - Performance monitoring
    - Configuration management
    - Resource allocation
    - Safety controls
    """
    
    def __init__(self, config: Dict[str, Any], mcp_server: Any, provider_manager: Any):
        self.config = config
        self.agent_config = config.get('agents', {})
        self.mcp_server = mcp_server
        self.provider_manager = provider_manager
        
        # Core components
        self.agent_factory = AgentFactory()
        self.audit_logger: Optional[AuditLogger] = None
        
        # Agent management
        self.agents: Dict[str, AgentInstance] = {}
        self.agent_templates: Dict[str, AgentTemplate] = {}
        
        # Performance tracking
        self.performance_tracker = {}
        self.resource_monitor = {}
        
        # Load built-in templates
        self._load_builtin_templates()
        
        # Background tasks
        self.monitoring_task: Optional[asyncio.Task] = None
        self.cleanup_task: Optional[asyncio.Task] = None
        
    async def initialize(self, audit_logger: AuditLogger):
        """Initialize the agent controller."""
        self.audit_logger = audit_logger
        
        # Start background tasks
        self.monitoring_task = asyncio.create_task(self._agent_monitoring_loop())
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        # Load any persistent agent configurations
        await self._load_persistent_agents()
        
        logger.info(f"Agent controller initialized with {len(self.agents)} active agents")
        
    async def create_agent(
        self, 
        agent_id: str, 
        agent_type: AgentType, 
        config: Dict[str, Any],
        auto_start: bool = True
    ) -> AgentInstance:
        """Create a new trading agent."""
        
        if agent_id in self.agents:
            raise ValueError(f"Agent {agent_id} already exists")
            
        try:
            # Merge with template defaults if available
            final_config = self._merge_with_template(agent_type, config)
            
            # Create agent instance
            agent = self.agent_factory.create_agent(
                agent_type, agent_id, final_config, self.mcp_server, self.provider_manager
            )
            
            # Create agent instance record
            agent_instance = AgentInstance(
                agent_id=agent_id,
                agent_type=agent_type,
                agent=agent,
                config=final_config,
                created_at=datetime.now(),
                last_activity=datetime.now(),
                status=AgentStatus.ACTIVE if auto_start else AgentStatus.PAUSED
            )
            
            self.agents[agent_id] = agent_instance
            
            # Initialize performance tracking
            self.performance_tracker[agent_id] = {
                'trades_executed': 0,
                'successful_trades': 0,
                'failed_trades': 0,
                'total_pnl': 0.0,
                'win_rate': 0.0,
                'avg_confidence': 0.0,
                'created_at': datetime.now()
            }
            
            # Set agent status
            if not auto_start:
                agent.status = AgentStatus.PAUSED
                
            # Log agent creation
            if self.audit_logger:
                await self.audit_logger.log_agent_event(
                    agent_id, 
                    "CREATED", 
                    {
                        'agent_type': agent_type.value,
                        'config_summary': self._get_config_summary(final_config),
                        'auto_start': auto_start
                    }
                )
                
            logger.info(f"Created agent {agent_id} of type {agent_type.value}")
            
            return agent_instance
            
        except Exception as e:
            logger.error(f"Failed to create agent {agent_id}: {e}")
            raise
            
    async def remove_agent(self, agent_id: str, reason: str = ""):
        """Remove a trading agent."""
        
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not found")
            
        agent_instance = self.agents[agent_id]
        
        try:
            # Stop agent if running
            if agent_instance.status == AgentStatus.ACTIVE:
                await self.stop_agent(agent_id)
                
            # Clean up agent resources
            if hasattr(agent_instance.agent, 'cleanup'):
                await agent_instance.agent.cleanup()
                
            # Remove from tracking
            self.agents.pop(agent_id)
            self.performance_tracker.pop(agent_id, None)
            
            # Log removal
            if self.audit_logger:
                await self.audit_logger.log_agent_event(
                    agent_id, 
                    "REMOVED", 
                    {'reason': reason}
                )
                
            logger.info(f"Removed agent {agent_id}: {reason}")
            
        except Exception as e:
            logger.error(f"Failed to remove agent {agent_id}: {e}")
            raise
            
    async def start_agent(self, agent_id: str):
        """Start a trading agent."""
        
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not found")
            
        agent_instance = self.agents[agent_id]
        
        if agent_instance.status == AgentStatus.ACTIVE:
            logger.warning(f"Agent {agent_id} is already active")
            return
            
        # Update status
        agent_instance.status = AgentStatus.ACTIVE
        agent_instance.agent.status = AgentStatus.ACTIVE
        agent_instance.last_activity = datetime.now()
        
        # Log start
        if self.audit_logger:
            await self.audit_logger.log_agent_event(agent_id, "STARTED", {})
            
        logger.info(f"Started agent {agent_id}")
        
    async def stop_agent(self, agent_id: str):
        """Stop a trading agent."""
        
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not found")
            
        agent_instance = self.agents[agent_id]
        
        # Update status
        agent_instance.status = AgentStatus.PAUSED
        agent_instance.agent.status = AgentStatus.PAUSED
        
        # Log stop
        if self.audit_logger:
            await self.audit_logger.log_agent_event(agent_id, "STOPPED", {})
            
        logger.info(f"Stopped agent {agent_id}")
        
    async def pause_agent(self, agent_id: str):
        """Pause a trading agent temporarily."""
        await self.stop_agent(agent_id)
        
    async def update_agent_config(self, agent_id: str, config_updates: Dict[str, Any]):
        """Update agent configuration."""
        
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not found")
            
        agent_instance = self.agents[agent_id]
        
        try:
            # Merge updates with existing config
            updated_config = agent_instance.config.copy()
            self._deep_merge_dict(updated_config, config_updates)
            
            # Update agent configuration
            agent_instance.config = updated_config
            
            # Apply updates to agent
            await self._apply_config_updates(agent_instance.agent, config_updates)
            
            # Log update
            if self.audit_logger:
                await self.audit_logger.log_agent_event(
                    agent_id, 
                    "CONFIG_UPDATED", 
                    {'updates': config_updates}
                )
                
            logger.info(f"Updated configuration for agent {agent_id}")
            
        except Exception as e:
            logger.error(f"Failed to update agent {agent_id} configuration: {e}")
            raise
            
    async def get_agent_performance(self, agent_id: str) -> Dict[str, Any]:
        """Get agent performance metrics."""
        
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not found")
            
        agent_instance = self.agents[agent_id]
        base_performance = self.performance_tracker.get(agent_id, {})
        
        # Get real-time performance from agent
        if hasattr(agent_instance.agent, 'performance_metrics'):
            agent_performance = agent_instance.agent.performance_metrics
        else:
            agent_performance = {}
            
        # Combine metrics
        combined_performance = {
            **base_performance,
            **agent_performance,
            'uptime_seconds': (datetime.now() - agent_instance.created_at).total_seconds(),
            'status': agent_instance.status.value,
            'last_activity': agent_instance.last_activity.isoformat()
        }
        
        return combined_performance
        
    async def get_all_agents_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all agents."""
        
        status_data = {}
        
        for agent_id, agent_instance in self.agents.items():
            try:
                performance = await self.get_agent_performance(agent_id)
                
                status_data[agent_id] = {
                    'agent_type': agent_instance.agent_type.value,
                    'status': agent_instance.status.value,
                    'created_at': agent_instance.created_at.isoformat(),
                    'last_activity': agent_instance.last_activity.isoformat(),
                    'performance': performance,
                    'config_summary': self._get_config_summary(agent_instance.config)
                }
                
            except Exception as e:
                logger.error(f"Error getting status for agent {agent_id}: {e}")
                status_data[agent_id] = {
                    'status': 'error',
                    'error': str(e)
                }
                
        return status_data
        
    async def execute_agent_task(self, agent_id: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task on a specific agent."""
        
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not found")
            
        agent_instance = self.agents[agent_id]
        
        if agent_instance.status != AgentStatus.ACTIVE:
            raise ValueError(f"Agent {agent_id} is not active")
            
        try:
            # Update last activity
            agent_instance.last_activity = datetime.now()
            
            # Execute task
            result = await agent_instance.agent.execute_task(task)
            
            # Update performance tracking
            await self._update_agent_performance(agent_id, task, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Task execution failed for agent {agent_id}: {e}")
            
            # Log error
            if self.audit_logger:
                await self.audit_logger.log_agent_event(
                    agent_id, 
                    "TASK_ERROR", 
                    {'task': task, 'error': str(e)}
                )
                
            raise
            
    def get_agent_templates(self) -> Dict[str, Dict[str, Any]]:
        """Get available agent templates."""
        
        templates = {}
        for name, template in self.agent_templates.items():
            templates[name] = {
                'name': template.name,
                'description': template.description,
                'agent_type': template.agent_type.value,
                'personality_presets': template.personality_presets,
                'risk_presets': template.risk_presets
            }
            
        return templates
        
    def create_agent_from_template(
        self, 
        template_name: str, 
        agent_id: str, 
        customizations: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Create agent configuration from template."""
        
        if template_name not in self.agent_templates:
            raise ValueError(f"Template {template_name} not found")
            
        template = self.agent_templates[template_name]
        
        # Start with template defaults
        config = template.default_config.copy()
        
        # Apply customizations
        if customizations:
            self._deep_merge_dict(config, customizations)
            
        return {
            'agent_id': agent_id,
            'agent_type': template.agent_type,
            'config': config,
            'template_used': template_name
        }
        
    async def bulk_operation(self, operation: str, agent_ids: List[str], **kwargs) -> Dict[str, Any]:
        """Perform bulk operations on multiple agents."""
        
        results = {}
        
        for agent_id in agent_ids:
            try:
                if operation == 'start':
                    await self.start_agent(agent_id)
                    results[agent_id] = {'success': True}
                elif operation == 'stop':
                    await self.stop_agent(agent_id)
                    results[agent_id] = {'success': True}
                elif operation == 'remove':
                    await self.remove_agent(agent_id, kwargs.get('reason', 'Bulk removal'))
                    results[agent_id] = {'success': True}
                elif operation == 'update_config':
                    await self.update_agent_config(agent_id, kwargs.get('config_updates', {}))
                    results[agent_id] = {'success': True}
                else:
                    results[agent_id] = {'success': False, 'error': f'Unknown operation: {operation}'}
                    
            except Exception as e:
                results[agent_id] = {'success': False, 'error': str(e)}
                
        return results
        
    def _load_builtin_templates(self):
        """Load built-in agent templates."""
        
        # Conservative Trader Template
        self.agent_templates['conservative_trader'] = AgentTemplate(
            name="Conservative Trader",
            description="Low-risk, steady trading approach",
            agent_type=AgentType.PRODUCTION_TRADING,
            default_config={
                'personality': {
                    'name': 'Conservative Trader',
                    'risk_tolerance': 3.0,
                    'analysis_style': 'conservative',
                    'time_horizon': 'swing',
                    'confidence_threshold': 0.8,
                    'max_trades_per_day': 5
                },
                'risk_profile': {
                    'max_loss_per_trade': 0.01,
                    'max_daily_loss': 0.02,
                    'stop_loss_percentage': 0.005,
                    'take_profit_ratio': 2.0
                }
            },
            personality_presets=[
                {'name': 'Ultra Conservative', 'risk_tolerance': 2.0, 'confidence_threshold': 0.9},
                {'name': 'Moderate Conservative', 'risk_tolerance': 4.0, 'confidence_threshold': 0.7}
            ],
            risk_presets=[
                {'name': 'Very Low Risk', 'max_loss_per_trade': 0.005, 'max_daily_loss': 0.01},
                {'name': 'Low Risk', 'max_loss_per_trade': 0.01, 'max_daily_loss': 0.02}
            ]
        )
        
        # Aggressive Trader Template
        self.agent_templates['aggressive_trader'] = AgentTemplate(
            name="Aggressive Trader",
            description="High-risk, high-reward trading approach",
            agent_type=AgentType.PRODUCTION_TRADING,
            default_config={
                'personality': {
                    'name': 'Aggressive Trader',
                    'risk_tolerance': 8.0,
                    'analysis_style': 'aggressive',
                    'time_horizon': 'day',
                    'confidence_threshold': 0.5,
                    'max_trades_per_day': 20
                },
                'risk_profile': {
                    'max_loss_per_trade': 0.03,
                    'max_daily_loss': 0.08,
                    'stop_loss_percentage': 0.02,
                    'take_profit_ratio': 1.5
                }
            },
            personality_presets=[
                {'name': 'Moderate Aggressive', 'risk_tolerance': 7.0, 'confidence_threshold': 0.6},
                {'name': 'Very Aggressive', 'risk_tolerance': 9.0, 'confidence_threshold': 0.4}
            ],
            risk_presets=[
                {'name': 'High Risk', 'max_loss_per_trade': 0.02, 'max_daily_loss': 0.05},
                {'name': 'Very High Risk', 'max_loss_per_trade': 0.05, 'max_daily_loss': 0.10}
            ]
        )
        
        # Balanced Trader Template
        self.agent_templates['balanced_trader'] = AgentTemplate(
            name="Balanced Trader",
            description="Moderate risk, balanced trading approach",
            agent_type=AgentType.PRODUCTION_TRADING,
            default_config={
                'personality': {
                    'name': 'Balanced Trader',
                    'risk_tolerance': 5.0,
                    'analysis_style': 'balanced',
                    'time_horizon': 'day',
                    'confidence_threshold': 0.6,
                    'max_trades_per_day': 10
                },
                'risk_profile': {
                    'max_loss_per_trade': 0.015,
                    'max_daily_loss': 0.04,
                    'stop_loss_percentage': 0.01,
                    'take_profit_ratio': 2.0
                }
            },
            personality_presets=[
                {'name': 'Conservative Balanced', 'risk_tolerance': 4.0, 'confidence_threshold': 0.7},
                {'name': 'Aggressive Balanced', 'risk_tolerance': 6.0, 'confidence_threshold': 0.5}
            ],
            risk_presets=[
                {'name': 'Moderate Risk', 'max_loss_per_trade': 0.015, 'max_daily_loss': 0.04},
                {'name': 'Adaptive Risk', 'max_loss_per_trade': 0.02, 'max_daily_loss': 0.05}
            ]
        )
        
    def _merge_with_template(self, agent_type: AgentType, config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge config with agent type defaults."""
        
        # Start with base production config
        base_config = {
            'trading_enabled': True,
            'auto_trading': False,
            'paper_trading': True,
            'learning_enabled': True
        }
        
        # Add agent type specific defaults
        if agent_type in self.agent_factory.agent_configs:
            type_config = self.agent_factory.agent_configs[agent_type]
            self._deep_merge_dict(base_config, type_config)
            
        # Apply user config
        self._deep_merge_dict(base_config, config)
        
        return base_config
        
    def _deep_merge_dict(self, target: Dict[str, Any], source: Dict[str, Any]):
        """Deep merge source dictionary into target."""
        
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_merge_dict(target[key], value)
            else:
                target[key] = value
                
    async def _apply_config_updates(self, agent: ProductionTradingAgent, updates: Dict[str, Any]):
        """Apply configuration updates to an agent."""
        
        # Update personality
        if 'personality' in updates:
            personality_updates = updates['personality']
            for key, value in personality_updates.items():
                if hasattr(agent.personality, key):
                    setattr(agent.personality, key, value)
                    
        # Update risk profile
        if 'risk_profile' in updates:
            risk_updates = updates['risk_profile']
            for key, value in risk_updates.items():
                if hasattr(agent.risk_profile, key):
                    setattr(agent.risk_profile, key, value)
                    
        # Update trading controls
        if 'trading_enabled' in updates:
            agent.trading_enabled = updates['trading_enabled']
        if 'auto_trading' in updates:
            agent.auto_trading = updates['auto_trading']
        if 'paper_trading' in updates:
            agent.paper_trading = updates['paper_trading']
            
    def _get_config_summary(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Get a summary of agent configuration."""
        
        summary = {}
        
        if 'personality' in config:
            personality = config['personality']
            summary['personality'] = {
                'name': personality.get('name', 'Unknown'),
                'risk_tolerance': personality.get('risk_tolerance', 0),
                'analysis_style': personality.get('analysis_style', 'unknown')
            }
            
        if 'risk_profile' in config:
            risk = config['risk_profile']
            summary['risk_profile'] = {
                'max_loss_per_trade': risk.get('max_loss_per_trade', 0),
                'max_daily_loss': risk.get('max_daily_loss', 0)
            }
            
        summary['trading_settings'] = {
            'trading_enabled': config.get('trading_enabled', False),
            'auto_trading': config.get('auto_trading', False),
            'paper_trading': config.get('paper_trading', True)
        }
        
        return summary
        
    async def _update_agent_performance(self, agent_id: str, task: Dict[str, Any], result: Dict[str, Any]):
        """Update agent performance metrics."""
        
        if agent_id not in self.performance_tracker:
            return
            
        tracker = self.performance_tracker[agent_id]
        
        # Update based on task type and result
        if task.get('type') == 'market_analysis':
            if 'decision' in result:
                decision = result['decision']
                
                tracker['trades_executed'] += 1
                
                # Track confidence
                confidence = decision.get('confidence', 0)
                current_avg = tracker.get('avg_confidence', 0)
                count = tracker['trades_executed']
                tracker['avg_confidence'] = ((current_avg * (count - 1)) + confidence) / count
                
        # Update last activity
        self.agents[agent_id].last_activity = datetime.now()
        
    async def _agent_monitoring_loop(self):
        """Background task for monitoring agents."""
        
        while True:
            try:
                # Monitor agent health
                for agent_id, agent_instance in self.agents.items():
                    # Check for inactive agents
                    inactive_threshold = timedelta(minutes=30)
                    if datetime.now() - agent_instance.last_activity > inactive_threshold:
                        if agent_instance.status == AgentStatus.ACTIVE:
                            logger.warning(f"Agent {agent_id} appears inactive")
                            
                            if self.audit_logger:
                                await self.audit_logger.log_agent_event(
                                    agent_id, 
                                    "INACTIVE_WARNING", 
                                    {'last_activity': agent_instance.last_activity.isoformat()}
                                )
                                
                # Sleep for monitoring interval
                await asyncio.sleep(300)  # 5 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in agent monitoring loop: {e}")
                await asyncio.sleep(60)
                
    async def _cleanup_loop(self):
        """Background task for cleanup operations."""
        
        while True:
            try:
                # Clean up old performance data
                cutoff_date = datetime.now() - timedelta(days=7)
                
                for agent_id in list(self.performance_tracker.keys()):
                    if agent_id not in self.agents:
                        # Remove tracking for deleted agents
                        self.performance_tracker.pop(agent_id, None)
                        
                # Sleep for cleanup interval
                await asyncio.sleep(3600)  # 1 hour
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(600)
                
    async def _load_persistent_agents(self):
        """Load any persistent agent configurations."""
        # This would load from database or configuration files
        # For now, we'll skip this implementation
        pass
        
    async def cleanup(self):
        """Cleanup resources."""
        
        # Cancel background tasks
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
                
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
                
        # Cleanup all agents
        for agent_id in list(self.agents.keys()):
            try:
                await self.remove_agent(agent_id, "System shutdown")
            except Exception as e:
                logger.error(f"Error cleaning up agent {agent_id}: {e}")
                
        # Clear data
        self.agents.clear()
        self.performance_tracker.clear()
        
        logger.info("Agent controller cleanup complete")