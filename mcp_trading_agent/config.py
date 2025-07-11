"""
Configuration Management for MCP Trading Agent
==============================================

Centralized configuration handling for the MCP-based trading system.
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class TradingConfig:
    """
    Configuration manager for the MCP Trading Agent.
    
    Handles:
    - YAML configuration loading
    - Environment variable substitution
    - Provider-specific configurations
    - Agent configurations
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration."""
        if config_path is None:
            config_path = self._find_config_file()
        
        self.config_path = Path(config_path)
        self._config = self._load_config()
        
        # Extract major sections
        self.llm = self._config.get('llm', {})
        self.data = self._config.get('data', {})
        self.trading = self._config.get('trading', {})
        self.mcp = self._config.get('mcp', {})
        self.ui = self._config.get('ui', {})
        
        logger.info(f"Configuration loaded from {self.config_path}")
    
    def _find_config_file(self) -> str:
        """Find the configuration file."""
        possible_paths = [
            "mcp_trading_agent/config/config.yaml",
            "config/config.yaml", 
            "config.yaml"
        ]
        
        for path in possible_paths:
            if Path(path).exists():
                return path
        
        raise FileNotFoundError("Could not find configuration file")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Substitute environment variables
            return self._substitute_env_vars(config)
            
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            raise
    
    def _substitute_env_vars(self, obj: Any) -> Any:
        """Recursively substitute environment variables in configuration."""
        if isinstance(obj, dict):
            return {k: self._substitute_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._substitute_env_vars(item) for item in obj]
        elif isinstance(obj, str) and obj.startswith('${') and obj.endswith('}'):
            env_var = obj[2:-1]
            return os.getenv(env_var, obj)
        else:
            return obj
    
    def get_provider_config(self, provider_name: str) -> Dict[str, Any]:
        """Get configuration for a specific LLM provider."""
        return self.llm.get(provider_name, {})
    
    def get_tool_config(self, tool_name: str) -> Dict[str, Any]:
        """Get configuration for a specific tool."""
        return self._config.get('tools', {}).get(tool_name, {})
    
    def get_agent_config(self, agent_type: str) -> Dict[str, Any]:
        """Get configuration for a specific agent type."""
        return self._config.get('agents', {}).get(agent_type, {})
    
    def update_config(self, updates: Dict[str, Any]) -> None:
        """Update configuration values."""
        def deep_update(base_dict, update_dict):
            for key, value in update_dict.items():
                if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                    deep_update(base_dict[key], value)
                else:
                    base_dict[key] = value
        
        deep_update(self._config, updates)
        
        # Refresh major sections
        self.llm = self._config.get('llm', {})
        self.data = self._config.get('data', {})
        self.trading = self._config.get('trading', {})
        self.mcp = self._config.get('mcp', {})
        self.ui = self._config.get('ui', {})
        
        logger.info("Configuration updated")
    
    def save_config(self, path: Optional[str] = None) -> None:
        """Save current configuration to file."""
        save_path = path or self.config_path
        
        with open(save_path, 'w') as f:
            yaml.dump(self._config, f, default_flow_style=False, indent=2)
        
        logger.info(f"Configuration saved to {save_path}")
    
    def get_all(self) -> Dict[str, Any]:
        """Get the complete configuration."""
        return self._config.copy()