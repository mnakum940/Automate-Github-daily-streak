"""
AI Provider Abstraction Layer
Supports multiple LLM providers (OpenAI, Ollama) with unified interface.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from enum import Enum
import os


class AIProvider(str, Enum):
    """Supported AI providers."""
    OPENAI = "openai"
    OLLAMA = "ollama"


class Message:
    """Represents a chat message."""
    
    def __init__(self, role: str, content: str):
        """
        Initialize a message.
        
        Args:
            role: Message role ("system", "user", "assistant")
            content: Message content
        """
        self.role = role
        self.content = content
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary format."""
        return {"role": self.role, "content": self.content}


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def generate(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """
        Generate text based on messages.
        
        Args:
            messages: List of conversation messages
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text response
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available and configured."""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider implementation."""
    
    def __init__(self, api_key: str, model: str = "gpt-4"):
        """
        Initialize OpenAI provider.
        
        Args:
            api_key: OpenAI API key
            model: Model name (e.g., "gpt-4", "gpt-3.5-turbo")
        """
        self.api_key = api_key
        self.model = model
        self._client = None
    
    def _get_client(self):
        """Lazy initialization of OpenAI client."""
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
            except ImportError:
                raise ImportError(
                    "OpenAI library not installed. "
                    "Install with: pip install openai"
                )
        return self._client
    
    def generate(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """Generate text using OpenAI API."""
        client = self._get_client()
        
        # Convert messages to OpenAI format
        message_dicts = [msg.to_dict() for msg in messages]
        
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=message_dicts,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {e}")
    
    def is_available(self) -> bool:
        """Check if OpenAI is available."""
        try:
            self._get_client()
            return bool(self.api_key)
        except Exception:
            return False


class OllamaProvider(LLMProvider):
    """Ollama local LLM provider implementation."""
    
    def __init__(self, model: str = "llama3", base_url: str = "http://localhost:11434"):
        """
        Initialize Ollama provider.
        
        Args:
            model: Model name (e.g., "llama3", "codellama")
            base_url: Ollama server URL
        """
        self.model = model
        self.base_url = base_url
    
    def generate(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """Generate text using Ollama chat API."""
        import requests
        
        # Convert messages to Ollama chat format
        chat_messages = [{"role": msg.role, "content": msg.content} for msg in messages]
        
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": chat_messages,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens
                    }
                },
                timeout=300  # 5 minute timeout for generation
            )
            
            response.raise_for_status()
            result = response.json()
            
            return result.get("message", {}).get("content", "")
        
        except requests.exceptions.RequestException as e:
            raise RuntimeError(
                f"Ollama API error: {e}\n"
                f"Make sure Ollama is running at {self.base_url} and model '{self.model}' is pulled."
            )
    
    def is_available(self) -> bool:
        """Check if Ollama is available."""
        import requests
        
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False


class AIClient:
    """Unified AI client that works with multiple providers."""
    
    def __init__(self, provider: AIProvider, **kwargs):
        """
        Initialize AI client.
        
        Args:
            provider: AI provider to use
            **kwargs: Provider-specific configuration
        """
        self.provider_type = provider
        
        if provider == AIProvider.OPENAI:
            api_key = kwargs.get('api_key') or os.getenv('OPENAI_API_KEY')
            model = kwargs.get('model', 'gpt-4')
            
            if not api_key:
                raise ValueError("OpenAI API key not provided")
            
            self.provider = OpenAIProvider(api_key=api_key, model=model)
        
        elif provider == AIProvider.OLLAMA:
            model = kwargs.get('model', 'llama3')
            base_url = kwargs.get('base_url', 'http://localhost:11434')
            
            self.provider = OllamaProvider(model=model, base_url=base_url)
        
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    def generate(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """
        Generate text from a prompt.
        
        Args:
            prompt: User prompt
            system_message: Optional system message for context
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text
        """
        messages = []
        
        if system_message:
            messages.append(Message("system", system_message))
        
        messages.append(Message("user", prompt))
        
        return self.provider.generate(messages, temperature, max_tokens)
    
    def is_available(self) -> bool:
        """Check if the configured provider is available."""
        return self.provider.is_available()
    
    @classmethod
    def from_config(cls, config):
        """
        Create AI client from configuration object.
        
        Args:
            config: Configuration object with ai settings
            
        Returns:
            AIClient instance
        """
        provider = AIProvider(config.ai.provider)
        
        kwargs = {
            'model': config.ai.model,
        }
        
        if provider == AIProvider.OPENAI:
            kwargs['api_key'] = config.ai.api_key
        elif provider == AIProvider.OLLAMA:
            # Ollama might have custom base_url in config
            if hasattr(config.ai, 'base_url'):
                kwargs['base_url'] = config.ai.base_url
        
        return cls(provider, **kwargs)


# Singleton instance
_ai_client_instance: Optional[AIClient] = None


def get_ai_client(config=None) -> AIClient:
    """
    Get singleton AI client instance.
    
    Args:
        config: Configuration object (required on first call)
        
    Returns:
        AIClient instance
    """
    global _ai_client_instance
    
    if _ai_client_instance is None:
        if config is None:
            raise RuntimeError("Config required for first AI client initialization")
        _ai_client_instance = AIClient.from_config(config)
    
    return _ai_client_instance
