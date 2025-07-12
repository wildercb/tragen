"""
OpenAI Provider
==============

LLM provider for OpenAI API.
"""

import logging
import os
from typing import Dict, Any, List, Optional, AsyncGenerator

from .base import BaseLLMProvider

logger = logging.getLogger(__name__)

class OpenAIProvider(BaseLLMProvider):
    """OpenAI provider for cloud-based models."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.api_key = config.get('api_key') or os.getenv('OPENAI_API_KEY')
        self.client = None
        
    async def initialize(self):
        """Initialize the OpenAI provider."""
        if not self.api_key:
            raise ValueError("OpenAI API key not provided")
        
        try:
            # Import here to avoid dependency issues if not installed
            import openai
            self.client = openai.AsyncOpenAI(api_key=self.api_key)
            logger.info("OpenAI provider initialized")
        except ImportError:
            logger.error("OpenAI package not installed. Install with: pip install openai")
            raise
    
    async def generate_response(
        self,
        prompt: str,
        model: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate a response using OpenAI."""
        if not self.client:
            await self.initialize()
        
        model_name = model or self.config.get('default_model', 'gpt-4o-mini')
        
        try:
            response = await self.client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=kwargs.get('temperature', 0.1),
                max_tokens=kwargs.get('max_tokens', 2000),
                top_p=kwargs.get('top_p', 0.9),
            )
            
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"OpenAI generation error: {e}")
            raise
    
    async def stream_response(
        self,
        prompt: str,
        model: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream a response using OpenAI."""
        if not self.client:
            await self.initialize()
        
        model_name = model or self.config.get('default_model', 'gpt-4o-mini')
        
        try:
            stream = await self.client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=kwargs.get('temperature', 0.1),
                max_tokens=kwargs.get('max_tokens', 2000),
                top_p=kwargs.get('top_p', 0.9),
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"OpenAI streaming error: {e}")
            raise
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get available models from configuration."""
        models = self.config.get('models', [])
        return [
            {
                'name': model.get('name', 'unknown'),
                'context_length': model.get('context_length', 16384),
                'capabilities': model.get('capabilities', ['chat', 'function_calling'])
            }
            for model in models
        ]
    
    async def health_check(self) -> bool:
        """Check if OpenAI is healthy."""
        if not self.client:
            try:
                await self.initialize()
            except Exception:
                return False
        
        try:
            # Simple test request
            await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
            )
            return True
        except Exception:
            return False
    
    async def cleanup(self):
        """Clean up resources."""
        if self.client:
            await self.client.close() 