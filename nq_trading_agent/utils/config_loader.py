"""
Configuration loader for NQ Trading Agent
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ConfigLoader:
    """
    Configuration loader that handles YAML config files with environment variable substitution.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the configuration loader.
        
        Args:
            config_path: Path to the configuration file. If None, uses default location.
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "config.yaml"
        
        self.config_path = Path(config_path)
        self._config = None
        
    def load_config(self) -> Dict[str, Any]:
        """
        Load configuration from YAML file with environment variable substitution.
        
        Returns:
            Dictionary containing the configuration
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If config file is invalid YAML
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
            
        try:
            with open(self.config_path, 'r') as f:
                config_text = f.read()
                
            # Substitute environment variables
            config_text = self._substitute_env_vars(config_text)
            
            # Parse YAML
            self._config = yaml.safe_load(config_text)
            
            # Validate configuration
            self._validate_config()
            
            logger.info(f"Configuration loaded from {self.config_path}")
            return self._config
            
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Invalid YAML in config file: {e}")
            
    def _substitute_env_vars(self, text: str) -> str:
        """
        Substitute environment variables in the format ${VAR_NAME} or ${VAR_NAME:default}
        
        Args:
            text: Text containing environment variable placeholders
            
        Returns:
            Text with environment variables substituted
        """
        import re
        
        def replace_env_var(match):
            var_expr = match.group(1)
            if ':' in var_expr:
                var_name, default_value = var_expr.split(':', 1)
                return os.getenv(var_name, default_value)
            else:
                return os.getenv(var_expr, '')
                
        return re.sub(r'\$\{([^}]+)\}', replace_env_var, text)
        
    def _validate_config(self) -> None:
        """
        Validate the loaded configuration.
        
        Raises:
            ValueError: If configuration is invalid
        """
        if not self._config:
            raise ValueError("Configuration is empty")
            
        # Check required sections
        required_sections = ['llm', 'data', 'trading', 'preprocessing', 'execution']
        for section in required_sections:
            if section not in self._config:
                raise ValueError(f"Missing required configuration section: {section}")
                
        # Validate LLM configuration
        llm_config = self._config.get('llm', {})
        provider = llm_config.get('provider')
        if not provider:
            raise ValueError("LLM provider not specified")
            
        if provider not in ['openai', 'groq', 'openrouter', 'ollama']:
            raise ValueError(f"Invalid LLM provider: {provider}")
            
        # Validate data source
        data_config = self._config.get('data', {})
        source = data_config.get('source')
        if source not in ['tradovate', 'yahoo', 'mock']:
            raise ValueError(f"Invalid data source: {source}")
            
        # Validate trading mode
        trading_config = self._config.get('trading', {})
        mode = trading_config.get('mode')
        if mode not in ['live', 'paper', 'backtest']:
            raise ValueError(f"Invalid trading mode: {mode}")
            
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.
        
        Args:
            key: Configuration key in dot notation (e.g., 'llm.provider')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        if not self._config:
            self.load_config()
            
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
                
        return value
        
    def get_llm_config(self) -> Dict[str, Any]:
        """
        Get the LLM configuration for the current provider.
        
        Returns:
            LLM configuration dictionary
        """
        if not self._config:
            self.load_config()
            
        llm_config = self._config.get('llm', {})
        provider = llm_config.get('provider')
        
        if provider not in llm_config:
            raise ValueError(f"No configuration found for LLM provider: {provider}")
            
        return {
            'provider': provider,
            **llm_config[provider]
        }
        
    def get_data_config(self) -> Dict[str, Any]:
        """
        Get the data configuration for the current source.
        
        Returns:
            Data configuration dictionary
        """
        if not self._config:
            self.load_config()
            
        data_config = self._config.get('data', {})
        source = data_config.get('source')
        
        config = {
            'source': source,
            'nq': data_config.get('nq', {})
        }
        
        if source in data_config:
            config.update(data_config[source])
            
        return config
        
    def get_trading_config(self) -> Dict[str, Any]:
        """
        Get the trading configuration.
        
        Returns:
            Trading configuration dictionary
        """
        if not self._config:
            self.load_config()
            
        return self._config.get('trading', {})