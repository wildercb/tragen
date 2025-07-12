"""
Groq Provider
============

LLM provider for Groq API.
"""

import logging
import os
from typing import Dict, Any, List, Optional, AsyncGenerator

from .base import BaseLLMProvider

logger = logging.getLogger(__name__)

class GroqProvider(BaseLLMProvider):
    """Groq provider for fast inference models."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.api_key = config.get('api_key') or os.getenv('GROQ_API_KEY')
        self.client = None
        
    async def initialize(self):
        """Initialize the Groq provider."""
        if not self.api_key:
            raise ValueError("Groq API key not provided")
        
        try:
            # Import here to avoid dependency issues if not installed
            import groq
            self.client = groq.AsyncGroq(api_key=self.api_key)
            logger.info("Groq provider initialized")
        except ImportError:
            logger.error("Groq package not installed. Install with: pip install groq")
            raise
    
    async def generate_response(
        self,
        prompt: str,
        model: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate a response using Groq."""
        if not self.client:
            await self.initialize()
        
        model_name = model or self.config.get('default_model', 'llama3-70b-8192')
        
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
            logger.error(f"Groq generation error: {e}")
            raise
    
    async def stream_response(
        self,
        prompt: str,
        model: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream a response using Groq."""
        if not self.client:
            await self.initialize()
        
        model_name = model or self.config.get('default_model', 'llama3-70b-8192')
        
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
            logger.error(f"Groq streaming error: {e}")
            raise
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get available models from configuration."""
        models = self.config.get('models', [])
        return [
            {
                'name': model.get('name', 'unknown'),
                'context_length': model.get('context_length', 8192),
                'capabilities': model.get('capabilities', ['chat'])
            }
            for model in models
        ]
    
    async def health_check(self) -> bool:
        """Check if Groq is healthy."""
        if not self.client:
            try:
                await self.initialize()
            except Exception:
                return False
        
        try:
            # Simple test request
            await self.client.chat.completions.create(
                model="llama3-70b-8192",
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