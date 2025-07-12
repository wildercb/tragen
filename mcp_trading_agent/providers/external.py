"""
External GPU Provider
====================

LLM provider for external GPU servers.
"""

import logging
import aiohttp
import json
from typing import Dict, Any, List, Optional, AsyncGenerator

from .base import BaseLLMProvider

logger = logging.getLogger(__name__)

class ExternalGPUProvider(BaseLLMProvider):
    """External GPU provider for remote GPU servers."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.endpoints = config.get('endpoints', [])
        self.session = None
        
    async def initialize(self):
        """Initialize the External GPU provider."""
        self.session = aiohttp.ClientSession()
        
        # Test connection to first endpoint
        if self.endpoints:
            try:
                await self.health_check()
                logger.info(f"External GPU provider initialized with {len(self.endpoints)} endpoints")
            except Exception as e:
                logger.error(f"Failed to initialize External GPU provider: {e}")
                raise
    
    async def generate_response(
        self,
        prompt: str,
        model: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate a response using external GPU server."""
        if not self.session:
            await self.initialize()
        
        if not self.endpoints:
            raise ValueError("No external GPU endpoints configured")
        
        # Try each endpoint until one works
        for endpoint in self.endpoints:
            try:
                return await self._generate_with_endpoint(endpoint, prompt, model, **kwargs)
            except Exception as e:
                logger.warning(f"Endpoint {endpoint['name']} failed: {e}")
                continue
        
        raise Exception("All external GPU endpoints failed")
    
    async def _generate_with_endpoint(
        self,
        endpoint: Dict[str, Any],
        prompt: str,
        model: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate response using a specific endpoint."""
        url = endpoint['url']
        api_key = endpoint.get('api_key')
        model_name = model or endpoint.get('models', ['default'])[0]
        
        headers = {}
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'
        
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": kwargs.get('temperature', 0.1),
            "max_tokens": kwargs.get('max_tokens', 2000),
            "top_p": kwargs.get('top_p', 0.9),
        }
        
        async with self.session.post(
            f"{url}/chat/completions",
            json=payload,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=120)
        ) as response:
            if response.status == 200:
                result = await response.json()
                return result['choices'][0]['message']['content']
            else:
                error_text = await response.text()
                raise Exception(f"External GPU API error {response.status}: {error_text}")
    
    async def stream_response(
        self,
        prompt: str,
        model: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream a response using external GPU server."""
        if not self.session:
            await self.initialize()
        
        if not self.endpoints:
            raise ValueError("No external GPU endpoints configured")
        
        # Use first available endpoint for streaming
        endpoint = self.endpoints[0]
        url = endpoint['url']
        api_key = endpoint.get('api_key')
        model_name = model or endpoint.get('models', ['default'])[0]
        
        headers = {}
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'
        
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": kwargs.get('temperature', 0.1),
            "max_tokens": kwargs.get('max_tokens', 2000),
            "top_p": kwargs.get('top_p', 0.9),
            "stream": True
        }
        
        async with self.session.post(
            f"{url}/chat/completions",
            json=payload,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=300)
        ) as response:
            if response.status == 200:
                async for line in response.content:
                    if line:
                        try:
                            line_str = line.decode('utf-8').strip()
                            if line_str.startswith('data: '):
                                data = line_str[6:]
                                if data == '[DONE]':
                                    break
                                chunk = json.loads(data)
                                if chunk['choices'][0]['delta'].get('content'):
                                    yield chunk['choices'][0]['delta']['content']
                        except (json.JSONDecodeError, KeyError):
                            continue
            else:
                error_text = await response.text()
                raise Exception(f"External GPU API error {response.status}: {error_text}")
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get available models from all endpoints."""
        all_models = []
        for endpoint in self.endpoints:
            models = endpoint.get('models', [])
            for model in models:
                all_models.append({
                    'name': model,
                    'context_length': 8192,  # Default context length
                    'capabilities': ['chat'],
                    'endpoint': endpoint['name']
                })
        return all_models
    
    async def health_check(self) -> bool:
        """Check if at least one endpoint is healthy."""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        for endpoint in self.endpoints:
            try:
                url = endpoint['url']
                api_key = endpoint.get('api_key')
                
                headers = {}
                if api_key:
                    headers['Authorization'] = f'Bearer {api_key}'
                
                async with self.session.get(
                    f"{url}/models",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        return True
            except Exception:
                continue
        
        return False
    
    async def cleanup(self):
        """Clean up resources."""
        if self.session:
            await self.session.close() 