"""
AI module for the Blog Writer SDK.

This module provides AI-powered content generation capabilities with
support for multiple providers and intelligent fallback mechanisms.
"""

from .base_provider import (
    BaseAIProvider,
    AIProviderManager,
    AIProviderType,
    AIRequest,
    AIResponse,
    AIGenerationConfig,
    ContentType,
    AIProviderError,
    AIProviderRateLimitError,
    AIProviderAuthenticationError,
    AIProviderQuotaExceededError,
    AIProviderConfig
)

from .openai_provider import OpenAIProvider, AzureOpenAIProvider
from .anthropic_provider import AnthropicProvider
from .ai_content_generator import AIContentGenerator, ContentTemplate

__all__ = [
    # Base classes and interfaces
    'BaseAIProvider',
    'AIProviderManager',
    'AIProviderType',
    'AIRequest',
    'AIResponse',
    'AIGenerationConfig',
    'ContentType',
    'AIProviderConfig',
    
    # Exceptions
    'AIProviderError',
    'AIProviderRateLimitError',
    'AIProviderAuthenticationError',
    'AIProviderQuotaExceededError',
    
    # Provider implementations
    'OpenAIProvider',
    'AzureOpenAIProvider',
    'AnthropicProvider',
    
    # Main AI generator
    'AIContentGenerator',
    'ContentTemplate',
]
