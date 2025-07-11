"""
LLM Factory for creating different LLM providers
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, AsyncGenerator
import asyncio
import logging

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the LLM provider.
        
        Args:
            config: Provider-specific configuration
        """
        self.config = config
        
    @abstractmethod
    async def generate_response(self, prompt: str, **kwargs) -> str:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: The input prompt
            **kwargs: Additional parameters
            
        Returns:
            Generated response
        """
        pass
        
    @abstractmethod
    async def stream_response(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """
        Stream response from the LLM.
        
        Args:
            prompt: The input prompt
            **kwargs: Additional parameters
            
        Yields:
            Response chunks
        """
        pass


class OpenAIProvider(LLMProvider):
    """
    OpenAI LLM provider.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        try:
            import openai
            self.client = openai.AsyncOpenAI(api_key=config.get('api_key'))
        except ImportError:
            raise ImportError("OpenAI library not installed. Run: pip install openai")
            
    async def generate_response(self, prompt: str, **kwargs) -> str:
        """
        Generate response using OpenAI API.
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.config.get('model', 'gpt-4o-mini'),
                messages=[{"role": "user", "content": prompt}],
                temperature=self.config.get('temperature', 0.1),
                max_tokens=self.config.get('max_tokens', 1000),
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
            
    async def stream_response(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """
        Stream response using OpenAI API.
        """
        try:
            stream = await self.client.chat.completions.create(
                model=self.config.get('model', 'gpt-4o-mini'),
                messages=[{"role": "user", "content": prompt}],
                temperature=self.config.get('temperature', 0.1),
                max_tokens=self.config.get('max_tokens', 1000),
                stream=True,
                **kwargs
            )
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"OpenAI streaming error: {e}")
            raise


class GroqProvider(LLMProvider):
    """
    Groq LLM provider.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        try:
            import groq
            self.client = groq.AsyncGroq(api_key=config.get('api_key'))
        except ImportError:
            raise ImportError("Groq library not installed. Run: pip install groq")
            
    async def generate_response(self, prompt: str, **kwargs) -> str:
        """
        Generate response using Groq API.
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.config.get('model', 'llama3-70b-8192'),
                messages=[{"role": "user", "content": prompt}],
                temperature=self.config.get('temperature', 0.1),
                max_tokens=self.config.get('max_tokens', 1000),
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise
            
    async def stream_response(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """
        Stream response using Groq API.
        """
        try:
            stream = await self.client.chat.completions.create(
                model=self.config.get('model', 'llama3-70b-8192'),
                messages=[{"role": "user", "content": prompt}],
                temperature=self.config.get('temperature', 0.1),
                max_tokens=self.config.get('max_tokens', 1000),
                stream=True,
                **kwargs
            )
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"Groq streaming error: {e}")
            raise


class OpenRouterProvider(LLMProvider):
    """
    OpenRouter LLM provider.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        try:
            import aiohttp
            self.session = None
        except ImportError:
            raise ImportError("aiohttp library not installed. Run: pip install aiohttp")
            
    async def _get_session(self):
        """Get or create aiohttp session."""
        if self.session is None:
            import aiohttp
            self.session = aiohttp.ClientSession()
        return self.session
            
    async def generate_response(self, prompt: str, **kwargs) -> str:
        """
        Generate response using OpenRouter API.
        """
        try:
            session = await self._get_session()
            
            headers = {
                "Authorization": f"Bearer {self.config.get('api_key')}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.config.get('model', 'anthropic/claude-3-haiku'),
                "messages": [{"role": "user", "content": prompt}],
                "temperature": self.config.get('temperature', 0.1),
                "max_tokens": self.config.get('max_tokens', 1000),
                **kwargs
            }
            
            async with session.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=data
            ) as response:
                result = await response.json()
                return result["choices"][0]["message"]["content"]
                
        except Exception as e:
            logger.error(f"OpenRouter API error: {e}")
            raise
            
    async def stream_response(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """
        Stream response using OpenRouter API.
        """
        try:
            session = await self._get_session()
            
            headers = {
                "Authorization": f"Bearer {self.config.get('api_key')}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.config.get('model', 'anthropic/claude-3-haiku'),
                "messages": [{"role": "user", "content": prompt}],
                "temperature": self.config.get('temperature', 0.1),
                "max_tokens": self.config.get('max_tokens', 1000),
                "stream": True,
                **kwargs
            }
            
            async with session.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=data
            ) as response:
                async for line in response.content:
                    if line:
                        line = line.decode('utf-8').strip()
                        if line.startswith('data: '):
                            data = line[6:]
                            if data != '[DONE]':
                                import json
                                try:
                                    chunk = json.loads(data)
                                    if chunk.get('choices') and chunk['choices'][0].get('delta', {}).get('content'):
                                        yield chunk['choices'][0]['delta']['content']
                                except json.JSONDecodeError:
                                    continue
                                    
        except Exception as e:
            logger.error(f"OpenRouter streaming error: {e}")
            raise
            
    async def close(self):
        """Close the session."""
        if self.session:
            await self.session.close()


class OllamaProvider(LLMProvider):
    """
    Ollama LLM provider.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        try:
            import ollama
            self.client = ollama.AsyncClient(host=config.get('host', 'http://localhost:11434'))
        except ImportError:
            raise ImportError("Ollama library not installed. Run: pip install ollama")
            
    async def generate_response(self, prompt: str, **kwargs) -> str:
        """
        Generate response using Ollama API.
        """
        try:
            response = await self.client.generate(
                model=self.config.get('model', 'phi3:mini'),
                prompt=prompt,
                options={
                    'temperature': self.config.get('temperature', 0.1),
                    'num_predict': self.config.get('max_tokens', 1000),
                    **kwargs
                }
            )
            return response['response']
        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            raise
            
    async def stream_response(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """
        Stream response using Ollama API.
        """
        try:
            stream = await self.client.generate(
                model=self.config.get('model', 'phi3:mini'),
                prompt=prompt,
                stream=True,
                options={
                    'temperature': self.config.get('temperature', 0.1),
                    'num_predict': self.config.get('max_tokens', 1000),
                    **kwargs
                }
            )
            async for chunk in stream:
                if chunk.get('response'):
                    yield chunk['response']
        except Exception as e:
            logger.error(f"Ollama streaming error: {e}")
            raise


class LLMFactory:
    """
    Factory class for creating LLM providers.
    """
    
    _providers = {
        'openai': OpenAIProvider,
        'groq': GroqProvider,
        'openrouter': OpenRouterProvider,
        'ollama': OllamaProvider
    }
    
    @classmethod
    def create_provider(cls, config: Dict[str, Any]) -> LLMProvider:
        """
        Create an LLM provider based on configuration.
        
        Args:
            config: Configuration dictionary with provider and settings
            
        Returns:
            LLM provider instance
            
        Raises:
            ValueError: If provider is not supported
        """
        provider_name = config.get('provider')
        if provider_name not in cls._providers:
            raise ValueError(f"Unsupported LLM provider: {provider_name}")
            
        provider_class = cls._providers[provider_name]
        return provider_class(config)
        
    @classmethod
    def get_supported_providers(cls) -> list:
        """
        Get list of supported providers.
        
        Returns:
            List of supported provider names
        """
        return list(cls._providers.keys())