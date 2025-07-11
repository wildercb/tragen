"""
LLM Provider Manager
===================

Manages multiple LLM providers and handles routing, failover, and load balancing.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import datetime

from .base import BaseLLMProvider
from .ollama import OllamaProvider
from .openai import OpenAIProvider
from .groq import GroqProvider
from .external import ExternalGPUProvider

logger = logging.getLogger(__name__)

class LLMProviderManager:
    """
    Manages multiple LLM providers with automatic failover and load balancing.
    
    Features:
    - Dynamic provider switching
    - Health monitoring
    - Automatic failover
    - Load balancing
    - Model capability matching
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the provider manager."""
        self.config = config
        self.providers: Dict[str, BaseLLMProvider] = {}
        self.default_provider = config.get('default_provider', 'ollama')
        self.health_status: Dict[str, Dict[str, Any]] = {}
        
    async def initialize(self):
        """Initialize all enabled providers."""
        logger.info("Initializing LLM providers...")
        
        provider_configs = self.config.get('providers', {})
        
        # Initialize each enabled provider
        for provider_name, provider_config in provider_configs.items():
            if not provider_config.get('enabled', False):
                continue
                
            try:
                provider = self._create_provider(provider_name, provider_config)
                await provider.initialize()
                self.providers[provider_name] = provider
                logger.info(f"Provider {provider_name} initialized successfully")
                
            except Exception as e:
                logger.error(f"Failed to initialize provider {provider_name}: {e}")
        
        # Start health monitoring
        asyncio.create_task(self._monitor_health())
        
        logger.info(f"Provider manager initialized with {len(self.providers)} providers")
    
    def _create_provider(self, name: str, config: Dict[str, Any]) -> BaseLLMProvider:
        """Create a provider instance based on type."""
        provider_classes = {
            'ollama': OllamaProvider,
            'openai': OpenAIProvider,
            'groq': GroqProvider,
            'external_gpu': ExternalGPUProvider
        }
        
        provider_class = provider_classes.get(name)
        if not provider_class:
            raise ValueError(f"Unknown provider type: {name}")
        
        return provider_class(name, config)
    
    async def generate_response(
        self,
        prompt: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate a response using the specified or best available provider."""
        target_provider = provider or self.default_provider
        
        # Try primary provider first
        if target_provider in self.providers:
            try:
                provider_instance = self.providers[target_provider]
                return await provider_instance.generate_response(prompt, model=model, **kwargs)
            except Exception as e:
                logger.warning(f"Provider {target_provider} failed: {e}")
        
        # Fallback to other healthy providers
        for provider_name, provider_instance in self.providers.items():
            if provider_name == target_provider:
                continue
                
            if self._is_provider_healthy(provider_name):
                try:
                    logger.info(f"Using fallback provider: {provider_name}")
                    return await provider_instance.generate_response(prompt, model=model, **kwargs)
                except Exception as e:
                    logger.warning(f"Fallback provider {provider_name} failed: {e}")
        
        raise Exception("All providers failed")
    
    async def stream_response(
        self,
        prompt: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream a response using the specified or best available provider."""
        target_provider = provider or self.default_provider
        
        if target_provider not in self.providers:
            raise ValueError(f"Provider {target_provider} not available")
        
        provider_instance = self.providers[target_provider]
        async for chunk in provider_instance.stream_response(prompt, model=model, **kwargs):
            yield chunk
    
    def get_available_models(self, provider: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get available models from a provider or all providers."""
        if provider:
            if provider in self.providers:
                return self.providers[provider].get_available_models()
            else:
                return []
        
        # Get models from all providers
        all_models = []
        for provider_name, provider_instance in self.providers.items():
            models = provider_instance.get_available_models()
            for model in models:
                model['provider'] = provider_name
                all_models.append(model)
        
        return all_models
    
    def get_best_model_for_task(self, task_type: str) -> Dict[str, Any]:
        """Get the best model for a specific task type."""
        all_models = self.get_available_models()
        
        # Filter models by capability
        suitable_models = []
        for model in all_models:
            capabilities = model.get('capabilities', [])
            if task_type in capabilities or 'general' in capabilities:
                suitable_models.append(model)
        
        if not suitable_models:
            # Return default model if no specific match
            return {
                'provider': self.default_provider,
                'model': self._get_default_model(self.default_provider)
            }
        
        # Sort by context length (prefer larger context for complex tasks)
        suitable_models.sort(key=lambda x: x.get('context_length', 0), reverse=True)
        
        best_model = suitable_models[0]
        return {
            'provider': best_model['provider'],
            'model': best_model['name']
        }
    
    def _get_default_model(self, provider: str) -> str:
        """Get the default model for a provider."""
        provider_config = self.config.get('providers', {}).get(provider, {})
        return provider_config.get('default_model', 'default')
    
    def _is_provider_healthy(self, provider: str) -> bool:
        """Check if a provider is healthy."""
        status = self.health_status.get(provider, {})
        return status.get('healthy', False)
    
    async def _monitor_health(self):
        """Monitor provider health periodically."""
        while True:
            for provider_name, provider_instance in self.providers.items():
                try:
                    health = await provider_instance.health_check()
                    self.health_status[provider_name] = {
                        'healthy': health,
                        'last_check': datetime.now(),
                        'status': 'healthy' if health else 'unhealthy'
                    }
                except Exception as e:
                    self.health_status[provider_name] = {
                        'healthy': False,
                        'last_check': datetime.now(),
                        'status': f'error: {str(e)}'
                    }
            
            # Wait 30 seconds before next health check
            await asyncio.sleep(30)
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of all providers."""
        return {
            'providers': {
                name: {
                    'enabled': True,
                    'health': self.health_status.get(name, {}),
                    'models': provider.get_available_models()
                }
                for name, provider in self.providers.items()
            },
            'default_provider': self.default_provider,
            'total_providers': len(self.providers),
            'healthy_providers': sum(1 for status in self.health_status.values() if status.get('healthy', False))
        }
    
    async def cleanup(self):
        """Cleanup all providers."""
        logger.info("Cleaning up providers...")
        for provider in self.providers.values():
            try:
                await provider.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up provider: {e}")
        
        self.providers.clear()
        logger.info("Provider cleanup complete")