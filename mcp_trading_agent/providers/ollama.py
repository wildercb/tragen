"""
Ollama Provider
==============

LLM provider for Ollama local models.
"""

import logging
import aiohttp
import json
from typing import Dict, Any, List, Optional, AsyncGenerator

from .base import BaseLLMProvider

logger = logging.getLogger(__name__)

class OllamaProvider(BaseLLMProvider):
    """Ollama provider for local LLM models."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.host = config.get('host', 'http://localhost:11434')
        self.session = None
        
    async def initialize(self):
        """Initialize the Ollama provider."""
        self.session = aiohttp.ClientSession()
        
        # Test connection
        try:
            await self.health_check()
            logger.info(f"Ollama provider initialized at {self.host}")
        except Exception as e:
            logger.error(f"Failed to initialize Ollama provider: {e}")
            raise
    
    async def generate_response(
        self,
        prompt: str,
        model: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate a response using Ollama."""
        if not self.session:
            await self.initialize()
        
        model_name = model or self.config.get('default_model', 'phi3:mini')
        
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": kwargs.get('temperature', 0.1),
                "top_p": kwargs.get('top_p', 0.9),
                "top_k": kwargs.get('top_k', 40),
            }
        }
        
        try:
            async with self.session.post(
                f"{self.host}/api/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get('response', '')
                else:
                    error_text = await response.text()
                    raise Exception(f"Ollama API error {response.status}: {error_text}")
        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            raise
    
    async def stream_response(
        self,
        prompt: str,
        model: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream a response using Ollama."""
        if not self.session:
            await self.initialize()
        
        model_name = model or self.config.get('default_model', 'phi3:mini')
        
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": kwargs.get('temperature', 0.1),
                "top_p": kwargs.get('top_p', 0.9),
                "top_k": kwargs.get('top_k', 40),
            }
        }
        
        try:
            async with self.session.post(
                f"{self.host}/api/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=300)
            ) as response:
                if response.status == 200:
                    async for line in response.content:
                        if line:
                            try:
                                chunk = json.loads(line.decode('utf-8'))
                                if 'response' in chunk:
                                    yield chunk['response']
                                if chunk.get('done', False):
                                    break
                            except json.JSONDecodeError:
                                continue
                else:
                    error_text = await response.text()
                    raise Exception(f"Ollama API error {response.status}: {error_text}")
        except Exception as e:
            logger.error(f"Ollama streaming error: {e}")
            raise
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get available models from configuration."""
        models = self.config.get('models', [])
        return [
            {
                'name': model.get('name', 'unknown'),
                'context_length': model.get('context_length', 4096),
                'capabilities': model.get('capabilities', ['chat'])
            }
            for model in models
        ]
    
    async def health_check(self) -> bool:
        """Check if Ollama is healthy."""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        try:
            async with self.session.get(
                f"{self.host}/api/tags",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                return response.status == 200
        except Exception:
            return False
    
    async def cleanup(self):
        """Clean up resources."""
        if self.session:
            await self.session.close() 