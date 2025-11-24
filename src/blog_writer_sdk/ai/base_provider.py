"""
Base AI provider interface and abstract classes.

This module defines the abstract base classes for AI providers,
enabling easy switching between different AI services.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from pydantic import BaseModel, Field
from dataclasses import dataclass


class AIProviderType(str, Enum):
    """Supported AI provider types."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    COHERE = "cohere"
    HUGGINGFACE = "huggingface"
    DATAFORSEO = "dataforseo"


class ContentType(str, Enum):
    """Types of content that can be generated."""
    BLOG_POST = "blog_post"
    INTRODUCTION = "introduction"
    CONCLUSION = "conclusion"
    SECTION = "section"
    TITLE = "title"
    META_DESCRIPTION = "meta_description"
    FAQ = "faq"
    SUMMARY = "summary"


@dataclass
class AIGenerationConfig:
    """Configuration for AI content generation."""
    max_tokens: int = 2000
    temperature: float = 0.7
    top_p: float = 0.9
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop_sequences: Optional[List[str]] = None
    model_specific_params: Optional[Dict[str, Any]] = None


class AIRequest(BaseModel):
    """Request model for AI content generation."""
    prompt: str = Field(..., description="The prompt for content generation")
    content_type: ContentType = Field(..., description="Type of content to generate")
    config: AIGenerationConfig = Field(default_factory=AIGenerationConfig)
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for generation")


class AIResponse(BaseModel):
    """Response model from AI content generation."""
    content: str = Field(..., description="Generated content")
    provider: str = Field(..., description="AI provider used")
    model: str = Field(..., description="Model used for generation")
    tokens_used: Optional[int] = Field(None, description="Number of tokens used")
    cost: Optional[float] = Field(None, description="Cost of the generation")
    generation_time: Optional[float] = Field(None, description="Time taken for generation")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class AIProviderError(Exception):
    """Base exception for AI provider errors."""
    def __init__(self, message: str, provider: str, error_code: Optional[str] = None):
        self.message = message
        self.provider = provider
        self.error_code = error_code
        super().__init__(f"[{provider}] {message}")


class AIProviderRateLimitError(AIProviderError):
    """Exception raised when rate limits are exceeded."""
    pass


class AIProviderAuthenticationError(AIProviderError):
    """Exception raised when authentication fails."""
    pass


class AIProviderQuotaExceededError(AIProviderError):
    """Exception raised when quota is exceeded."""
    pass


class BaseAIProvider(ABC):
    """
    Abstract base class for AI providers.
    
    This class defines the interface that all AI providers must implement,
    enabling easy switching between different AI services.
    """
    
    def __init__(self, api_key: str, **kwargs):
        """
        Initialize the AI provider.
        
        Args:
            api_key: API key for the provider
            **kwargs: Additional provider-specific configuration
        """
        self.api_key = api_key
        self.config = kwargs
        self._client = None
    
    @property
    @abstractmethod
    def provider_type(self) -> AIProviderType:
        """Return the provider type."""
        pass
    
    @property
    @abstractmethod
    def supported_models(self) -> List[str]:
        """Return list of supported models."""
        pass
    
    @property
    @abstractmethod
    def default_model(self) -> str:
        """Return the default model for this provider."""
        pass
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the provider client."""
        pass
    
    @abstractmethod
    async def generate_content(
        self, 
        request: AIRequest, 
        model: Optional[str] = None
    ) -> AIResponse:
        """
        Generate content using the AI provider.
        
        Args:
            request: AI generation request
            model: Optional model override
            
        Returns:
            AI response with generated content
        """
        pass
    
    @abstractmethod
    async def validate_api_key(self) -> bool:
        """
        Validate the API key.
        
        Returns:
            True if API key is valid, False otherwise
        """
        pass
    
    @abstractmethod
    def estimate_cost(self, tokens: int, model: Optional[str] = None) -> float:
        """
        Estimate the cost for a given number of tokens.
        
        Args:
            tokens: Number of tokens
            model: Model to use for cost estimation
            
        Returns:
            Estimated cost in USD
        """
        pass
    
    @abstractmethod
    def get_rate_limits(self) -> Dict[str, Any]:
        """
        Get rate limit information for the provider.
        
        Returns:
            Dictionary with rate limit information
        """
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the provider.
        
        Returns:
            Health check results
        """
        try:
            is_valid = await self.validate_api_key()
            return {
                "provider": self.provider_type.value,
                "status": "healthy" if is_valid else "unhealthy",
                "api_key_valid": is_valid,
                "rate_limits": self.get_rate_limits()
            }
        except Exception as e:
            return {
                "provider": self.provider_type.value,
                "status": "error",
                "error": str(e)
            }


class AIProviderConfig(BaseModel):
    """Configuration for AI providers."""
    provider_type: AIProviderType
    api_key: str
    default_model: Optional[str] = None
    max_retries: int = 3
    timeout: int = 30
    rate_limit_per_minute: Optional[int] = None
    custom_config: Optional[Dict[str, Any]] = None
    enabled: bool = True
    priority: int = 1  # Lower number = higher priority


class AIProviderManager:
    """
    Manager class for handling multiple AI providers with fallback support.
    """
    
    def __init__(self):
        self.providers: Dict[str, BaseAIProvider] = {}
        self.provider_configs: Dict[str, AIProviderConfig] = {}
        self.fallback_order: List[str] = []
    
    def add_provider(self, name: str, provider: BaseAIProvider, config: AIProviderConfig):
        """Add an AI provider to the manager."""
        self.providers[name] = provider
        self.provider_configs[name] = config
        self._update_fallback_order()
    
    def remove_provider(self, name: str):
        """Remove an AI provider from the manager."""
        if name in self.providers:
            del self.providers[name]
            del self.provider_configs[name]
            self._update_fallback_order()
    
    def _update_fallback_order(self):
        """Update the fallback order based on provider priorities."""
        enabled_providers = [
            (name, config) for name, config in self.provider_configs.items()
            if config.enabled
        ]
        self.fallback_order = [
            name for name, config in sorted(enabled_providers, key=lambda x: x[1].priority)
        ]
    
    async def generate_content(
        self, 
        request: AIRequest, 
        preferred_provider: Optional[str] = None,
        model: Optional[str] = None
    ) -> AIResponse:
        """
        Generate content using the specified provider or fallback chain.
        
        Args:
            request: AI generation request
            preferred_provider: Preferred provider name
            model: Optional model override
            
        Returns:
            AI response with generated content
        """
        providers_to_try = []
        
        # Add preferred provider first if specified and available
        if preferred_provider and preferred_provider in self.providers:
            if self.provider_configs[preferred_provider].enabled:
                providers_to_try.append(preferred_provider)
        
        # Add fallback providers
        for provider_name in self.fallback_order:
            if provider_name not in providers_to_try:
                providers_to_try.append(provider_name)
        
        if not providers_to_try:
            raise AIProviderError("No enabled AI providers available", "manager")
        
        last_error = None
        
        for provider_name in providers_to_try:
            try:
                provider = self.providers[provider_name]
                response = await provider.generate_content(request, model)
                return response
            
            except AIProviderRateLimitError as e:
                last_error = e
                continue  # Try next provider
            
            except AIProviderQuotaExceededError as e:
                last_error = e
                continue  # Try next provider
            
            except Exception as e:
                last_error = e
                continue  # Try next provider
        
        # If we get here, all providers failed
        raise AIProviderError(
            f"All AI providers failed. Last error: {str(last_error)}", 
            "manager"
        )
    
    async def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """Perform health checks on all providers."""
        results = {}
        for name, provider in self.providers.items():
            results[name] = await provider.health_check()
        return results
    
    def get_provider_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status information for all providers."""
        status = {}
        for name, config in self.provider_configs.items():
            provider = self.providers.get(name)
            status[name] = {
                "enabled": config.enabled,
                "priority": config.priority,
                "provider_type": config.provider_type.value,
                "default_model": config.default_model,
                "available": provider is not None
            }
        return status
