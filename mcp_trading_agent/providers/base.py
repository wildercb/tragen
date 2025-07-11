"""
Base LLM Provider Interface
===========================

Abstract base class for all LLM providers in the MCP trading system.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, AsyncGenerator
import logging

logger = logging.getLogger(__name__)

class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    
    Defines the interface that all providers must implement for:
    - Model management
    - Response generation
    - Streaming
    - Health monitoring
    """
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """Initialize the provider."""
        self.name = name
        self.config = config
        self.models = config.get('models', [])
        self.default_model = config.get('default_model')
        self.is_initialized = False
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the provider (connect, authenticate, etc.)."""
        pass
    
    @abstractmethod
    async def generate_response(
        self, 
        prompt: str, 
        model: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: Input prompt
            model: Specific model to use (optional)
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
        
        Returns:
            Generated response text
        """
        pass
    
    @abstractmethod
    async def stream_response(
        self,
        prompt: str,
        model: Optional[str] = None, 
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Stream a response from the LLM.
        
        Args:
            prompt: Input prompt
            model: Specific model to use (optional)
            **kwargs: Additional parameters
            
        Yields:
            Response chunks as they arrive
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the provider is healthy and responsive.
        
        Returns:
            True if healthy, False otherwise
        """
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[Dict[str, Any]]:
        """
        Get list of available models.
        
        Returns:
            List of model info dictionaries
        """
        pass
    
    async def cleanup(self) -> None:
        """Cleanup resources (optional, can be overridden)."""
        logger.info(f"Cleaning up provider {self.name}")
        self.is_initialized = False
    
    def _get_model_name(self, model: Optional[str] = None) -> str:
        """Get the model name to use (provided or default)."""
        return model or self.default_model or (self.models[0]['name'] if self.models else 'default')
    
    def _validate_model(self, model: str) -> bool:
        """Validate that a model is available."""
        available_models = [m['name'] for m in self.models]
        return model in available_models
    
    def _prepare_generation_params(self, **kwargs) -> Dict[str, Any]:
        """Prepare parameters for generation, applying defaults."""
        params = {}
        
        # Common parameters with defaults
        params['temperature'] = kwargs.get('temperature', 0.1)
        params['max_tokens'] = kwargs.get('max_tokens', 1000)
        params['top_p'] = kwargs.get('top_p', 0.9)
        params['frequency_penalty'] = kwargs.get('frequency_penalty', 0.0)
        params['presence_penalty'] = kwargs.get('presence_penalty', 0.0)
        
        return params
    
    def get_model_info(self, model: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific model."""
        for model_info in self.models:
            if model_info['name'] == model:
                return model_info
        return None
    
    def supports_capability(self, model: str, capability: str) -> bool:
        """Check if a model supports a specific capability."""
        model_info = self.get_model_info(model)
        if not model_info:
            return False
        
        capabilities = model_info.get('capabilities', [])
        return capability in capabilities
    
    def get_context_length(self, model: str) -> int:
        """Get the context length for a model."""
        model_info = self.get_model_info(model)
        if not model_info:
            return 4096  # Default context length
        
        return model_info.get('context_length', 4096)
    
    def __str__(self) -> str:
        """String representation of the provider."""
        return f"{self.__class__.__name__}(name={self.name}, models={len(self.models)})"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"{self.__class__.__name__}(name='{self.name}', config={self.config})"