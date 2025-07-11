"""
Tests for configuration loading
"""

import pytest
import tempfile
import os
from pathlib import Path
import yaml

from ..utils.config_loader import ConfigLoader


class TestConfigLoader:
    """Test configuration loader."""
    
    def test_load_valid_config(self):
        """Test loading a valid configuration."""
        config_data = {
            'llm': {
                'provider': 'openai',
                'openai': {
                    'model': 'gpt-4o-mini',
                    'api_key': 'test-key'
                }
            },
            'data': {
                'source': 'mock'
            },
            'trading': {
                'mode': 'paper'
            },
            'preprocessing': {
                'max_tokens': 200
            },
            'execution': {
                'default_quantity': 1
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_config_path = f.name
            
        try:
            loader = ConfigLoader(temp_config_path)
            config = loader.load_config()
            
            assert config['llm']['provider'] == 'openai'
            assert config['data']['source'] == 'mock'
            assert config['trading']['mode'] == 'paper'
            
        finally:
            os.unlink(temp_config_path)
            
    def test_missing_config_file(self):
        """Test handling of missing config file."""
        loader = ConfigLoader('/nonexistent/config.yaml')
        
        with pytest.raises(FileNotFoundError):
            loader.load_config()
            
    def test_invalid_yaml(self):
        """Test handling of invalid YAML."""
        invalid_yaml = "invalid: yaml: content: ["
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(invalid_yaml)
            temp_config_path = f.name
            
        try:
            loader = ConfigLoader(temp_config_path)
            
            with pytest.raises(yaml.YAMLError):
                loader.load_config()
                
        finally:
            os.unlink(temp_config_path)
            
    def test_env_var_substitution(self):
        """Test environment variable substitution."""
        config_data = {
            'llm': {
                'provider': 'openai',
                'openai': {
                    'api_key': '${TEST_API_KEY}'
                }
            }
        }
        
        # Set environment variable
        os.environ['TEST_API_KEY'] = 'test-key-from-env'
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_config_path = f.name
            
        try:
            loader = ConfigLoader(temp_config_path)
            config = loader.load_config()
            
            assert config['llm']['openai']['api_key'] == 'test-key-from-env'
            
        finally:
            os.unlink(temp_config_path)
            del os.environ['TEST_API_KEY']
            
    def test_get_method(self):
        """Test get method with dot notation."""
        config_data = {
            'llm': {
                'provider': 'openai',
                'openai': {
                    'model': 'gpt-4o-mini'
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_config_path = f.name
            
        try:
            loader = ConfigLoader(temp_config_path)
            
            assert loader.get('llm.provider') == 'openai'
            assert loader.get('llm.openai.model') == 'gpt-4o-mini'
            assert loader.get('nonexistent.key', 'default') == 'default'
            
        finally:
            os.unlink(temp_config_path)
            
    def test_validation(self):
        """Test configuration validation."""
        # Missing required sections
        invalid_config = {
            'llm': {
                'provider': 'openai'
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(invalid_config, f)
            temp_config_path = f.name
            
        try:
            loader = ConfigLoader(temp_config_path)
            
            with pytest.raises(ValueError):
                loader.load_config()
                
        finally:
            os.unlink(temp_config_path)
            
    def test_get_llm_config(self):
        """Test getting LLM configuration."""
        config_data = {
            'llm': {
                'provider': 'openai',
                'openai': {
                    'model': 'gpt-4o-mini',
                    'api_key': 'test-key'
                }
            },
            'data': {'source': 'mock'},
            'trading': {'mode': 'paper'},
            'preprocessing': {'max_tokens': 200},
            'execution': {'default_quantity': 1}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_config_path = f.name
            
        try:
            loader = ConfigLoader(temp_config_path)
            loader.load_config()
            
            llm_config = loader.get_llm_config()
            
            assert llm_config['provider'] == 'openai'
            assert llm_config['model'] == 'gpt-4o-mini'
            assert llm_config['api_key'] == 'test-key'
            
        finally:
            os.unlink(temp_config_path)