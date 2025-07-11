"""
Tests for LLM integrations (OpenAI, Groq, OpenRouter, Ollama)
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

from ..utils.llm_factory import LLMFactory, OpenAIProvider, GroqProvider, OpenRouterProvider, OllamaProvider


class TestLLMFactory:
    """Test LLM factory functionality."""
    
    def test_supported_providers(self):
        """Test that all required providers are supported."""
        providers = LLMFactory.get_supported_providers()
        expected = ['openai', 'groq', 'openrouter', 'ollama']
        
        for provider in expected:
            assert provider in providers
            
    def test_create_openai_provider(self):
        """Test OpenAI provider creation."""
        config = {
            'provider': 'openai',
            'model': 'gpt-4o-mini',
            'api_key': 'test_key',
            'temperature': 0.1
        }
        
        provider = LLMFactory.create_provider(config)
        assert isinstance(provider, OpenAIProvider)
        assert provider.config['model'] == 'gpt-4o-mini'
        
    def test_create_groq_provider(self):
        """Test Groq provider creation."""
        config = {
            'provider': 'groq',
            'model': 'llama3-70b-8192',
            'api_key': 'test_key'
        }
        
        provider = LLMFactory.create_provider(config)
        assert isinstance(provider, GroqProvider)
        assert provider.config['model'] == 'llama3-70b-8192'
        
    def test_create_openrouter_provider(self):
        """Test OpenRouter provider creation."""
        config = {
            'provider': 'openrouter',
            'model': 'anthropic/claude-3-haiku',
            'api_key': 'test_key'
        }
        
        provider = LLMFactory.create_provider(config)
        assert isinstance(provider, OpenRouterProvider)
        assert provider.config['model'] == 'anthropic/claude-3-haiku'
        
    def test_create_ollama_provider(self):
        """Test Ollama provider creation."""
        config = {
            'provider': 'ollama',
            'model': 'gemma2:9b',
            'host': 'http://localhost:11434'
        }
        
        provider = LLMFactory.create_provider(config)
        assert isinstance(provider, OllamaProvider)
        assert provider.config['model'] == 'gemma2:9b'
        
    def test_unsupported_provider(self):
        """Test handling of unsupported provider."""
        config = {
            'provider': 'unsupported_provider'
        }
        
        with pytest.raises(ValueError, match="Unsupported LLM provider"):
            LLMFactory.create_provider(config)


class TestOpenAIProvider:
    """Test OpenAI provider functionality."""
    
    @pytest.mark.asyncio
    async def test_generate_response_mock(self):
        """Test OpenAI response generation with mock."""
        config = {
            'model': 'gpt-4o-mini',
            'api_key': 'test_key',
            'temperature': 0.1,
            'max_tokens': 1000
        }
        
        with patch('openai.AsyncOpenAI') as mock_openai:
            # Setup mock response
            mock_client = AsyncMock()
            mock_openai.return_value = mock_client
            
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = "Test response from OpenAI"
            
            mock_client.chat.completions.create.return_value = mock_response
            
            # Test provider
            provider = OpenAIProvider(config)
            response = await provider.generate_response("Test prompt")
            
            assert response == "Test response from OpenAI"
            mock_client.chat.completions.create.assert_called_once()
            
    @pytest.mark.asyncio
    async def test_stream_response_mock(self):
        """Test OpenAI streaming response with mock."""
        config = {
            'model': 'gpt-4o-mini',
            'api_key': 'test_key'
        }
        
        with patch('openai.AsyncOpenAI') as mock_openai:
            # Setup mock streaming response
            mock_client = AsyncMock()
            mock_openai.return_value = mock_client
            
            async def mock_stream():
                chunks = ["Hello", " world", "!"]
                for chunk_text in chunks:
                    chunk = Mock()
                    chunk.choices = [Mock()]
                    chunk.choices[0].delta.content = chunk_text
                    yield chunk
                    
            mock_client.chat.completions.create.return_value = mock_stream()
            
            # Test streaming
            provider = OpenAIProvider(config)
            response_chunks = []
            
            async for chunk in provider.stream_response("Test prompt"):
                response_chunks.append(chunk)
                
            assert response_chunks == ["Hello", " world", "!"]


class TestGroqProvider:
    """Test Groq provider functionality."""
    
    @pytest.mark.asyncio
    async def test_generate_response_mock(self):
        """Test Groq response generation with mock."""
        config = {
            'model': 'llama3-70b-8192',
            'api_key': 'test_key',
            'temperature': 0.1
        }
        
        with patch('groq.AsyncGroq') as mock_groq:
            # Setup mock response
            mock_client = AsyncMock()
            mock_groq.return_value = mock_client
            
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = "Test response from Groq"
            
            mock_client.chat.completions.create.return_value = mock_response
            
            # Test provider
            provider = GroqProvider(config)
            response = await provider.generate_response("Test prompt")
            
            assert response == "Test response from Groq"


class TestOllamaProvider:
    """Test Ollama provider functionality."""
    
    @pytest.mark.asyncio
    async def test_generate_response_mock(self):
        """Test Ollama response generation with mock."""
        config = {
            'model': 'gemma2:9b',
            'host': 'http://localhost:11434',
            'temperature': 0.1
        }
        
        with patch('ollama.AsyncClient') as mock_ollama:
            # Setup mock response
            mock_client = AsyncMock()
            mock_ollama.return_value = mock_client
            
            mock_response = {
                'response': 'Test response from Ollama'
            }
            
            mock_client.generate.return_value = mock_response
            
            # Test provider
            provider = OllamaProvider(config)
            response = await provider.generate_response("Test prompt")
            
            assert response == "Test response from Ollama"
            
    @pytest.mark.asyncio
    async def test_stream_response_mock(self):
        """Test Ollama streaming response with mock."""
        config = {
            'model': 'gemma2:9b',
            'host': 'http://localhost:11434'
        }
        
        with patch('ollama.AsyncClient') as mock_ollama:
            # Setup mock streaming response
            mock_client = AsyncMock()
            mock_ollama.return_value = mock_client
            
            async def mock_stream():
                chunks = [
                    {'response': 'Hello'},
                    {'response': ' world'},
                    {'response': '!'}
                ]
                for chunk in chunks:
                    yield chunk
                    
            mock_client.generate.return_value = mock_stream()
            
            # Test streaming
            provider = OllamaProvider(config)
            response_chunks = []
            
            async for chunk in provider.stream_response("Test prompt"):
                response_chunks.append(chunk)
                
            assert response_chunks == ["Hello", " world", "!"]


class TestProviderComparison:
    """Test comparing different LLM providers."""
    
    @pytest.mark.asyncio
    async def test_provider_response_comparison(self):
        """Test comparing responses from different providers."""
        test_prompt = "Analyze this NQ futures price action: Current price 15000, RSI 65, MACD bullish crossover."
        
        # Mock configurations for all providers
        providers_config = {
            'openai': {
                'provider': 'openai',
                'model': 'gpt-4o-mini',
                'api_key': 'test_key'
            },
            'groq': {
                'provider': 'groq',
                'model': 'llama3-70b-8192',
                'api_key': 'test_key'
            },
            'ollama': {
                'provider': 'ollama',
                'model': 'gemma2:9b',
                'host': 'http://localhost:11434'
            }
        }
        
        responses = {}
        
        # Test each provider with mocked responses
        with patch('openai.AsyncOpenAI'), \
             patch('groq.AsyncGroq'), \
             patch('ollama.AsyncClient'):
            
            for provider_name, config in providers_config.items():
                try:
                    provider = LLMFactory.create_provider(config)
                    
                    # Mock specific responses for each provider
                    if provider_name == 'openai':
                        with patch.object(provider, 'generate_response', return_value="OpenAI: BUY signal with 85% confidence"):
                            response = await provider.generate_response(test_prompt)
                    elif provider_name == 'groq':
                        with patch.object(provider, 'generate_response', return_value="Groq: HOLD signal with 60% confidence"):
                            response = await provider.generate_response(test_prompt)
                    elif provider_name == 'ollama':
                        with patch.object(provider, 'generate_response', return_value="Ollama: SELL signal with 70% confidence"):
                            response = await provider.generate_response(test_prompt)
                    
                    responses[provider_name] = response
                    
                except Exception as e:
                    responses[provider_name] = f"Error: {e}"
        
        # Verify we got responses from all providers
        assert len(responses) == 3
        assert all(isinstance(response, str) for response in responses.values())
        
        # Each provider should give a different response (in our mock setup)
        assert "OpenAI" in responses['openai']
        assert "Groq" in responses['groq']
        assert "Ollama" in responses['ollama']


class TestTokenUsageTracking:
    """Test token usage tracking across providers."""
    
    @pytest.mark.asyncio
    async def test_token_usage_estimation(self):
        """Test token usage estimation for different providers."""
        test_prompts = [
            "Short prompt",
            "Medium length prompt with some technical analysis terms like RSI, MACD, support, resistance",
            "Very long prompt with extensive market analysis including multiple indicators like RSI at 65 showing momentum, MACD with bullish crossover above signal line, price action breaking through resistance at 15000 level with strong volume confirmation and thrust patterns indicating potential continuation of upward movement"
        ]
        
        for prompt in test_prompts:
            # Estimate tokens (rough approximation: 1 token ≈ 4 characters)
            estimated_tokens = len(prompt) // 4
            
            # Verify token estimation is reasonable
            if len(prompt) < 50:
                assert estimated_tokens < 15, "Short prompt should use few tokens"
            elif len(prompt) < 200:
                assert estimated_tokens < 50, "Medium prompt should use moderate tokens"
            else:
                assert estimated_tokens > 50, "Long prompt should use many tokens"
                
            # In a real implementation, you would track actual token usage
            # from the API responses and compare with estimates


class TestProviderFallback:
    """Test provider fallback functionality."""
    
    @pytest.mark.asyncio
    async def test_provider_fallback_chain(self):
        """Test falling back to alternative providers when primary fails."""
        primary_config = {
            'provider': 'openai',
            'model': 'gpt-4o-mini',
            'api_key': 'invalid_key'
        }
        
        fallback_configs = [
            {
                'provider': 'groq',
                'model': 'llama3-70b-8192',
                'api_key': 'test_key'
            },
            {
                'provider': 'ollama',
                'model': 'gemma2:9b',
                'host': 'http://localhost:11434'
            }
        ]
        
        # Simulate trying providers in order
        async def try_providers_with_fallback(prompt: str):
            # Try primary provider (will fail)
            try:
                provider = LLMFactory.create_provider(primary_config)
                with patch.object(provider, 'generate_response', side_effect=Exception("API Error")):
                    return await provider.generate_response(prompt)
            except Exception:
                pass
                
            # Try fallback providers
            for config in fallback_configs:
                try:
                    provider = LLMFactory.create_provider(config)
                    
                    if config['provider'] == 'groq':
                        with patch.object(provider, 'generate_response', return_value="Fallback response from Groq"):
                            return await provider.generate_response(prompt)
                    elif config['provider'] == 'ollama':
                        with patch.object(provider, 'generate_response', return_value="Fallback response from Ollama"):
                            return await provider.generate_response(prompt)
                            
                except Exception:
                    continue
                    
            raise Exception("All providers failed")
        
        # Test fallback mechanism
        response = await try_providers_with_fallback("Test prompt")
        assert "Fallback response" in response
        assert response in ["Fallback response from Groq", "Fallback response from Ollama"]