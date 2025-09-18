"""
Azure OpenAI Provider Implementation

This module provides an implementation of the BaseAIProvider interface
for Azure OpenAI services, enabling integration with Azure-hosted OpenAI models.
"""

import os
import time
import logging
from typing import Dict, List, Optional, Any
from openai import AzureOpenAI
from openai.types.chat import ChatCompletion

from .base_provider import (
    BaseAIProvider,
    AIProviderType,
    AIRequest,
    AIResponse,
    AIProviderError,
    AIProviderRateLimitError,
    AIProviderAuthenticationError,
    AIProviderQuotaExceededError
)

logger = logging.getLogger(__name__)


class AzureOpenAIProvider(BaseAIProvider):
    """
    Azure OpenAI provider implementation.
    
    This provider integrates with Azure OpenAI services, providing access
    to OpenAI models hosted on Azure infrastructure.
    """
    
    def __init__(self, api_key: str, **kwargs):
        """
        Initialize Azure OpenAI provider.
        
        Args:
            api_key: Azure OpenAI API key
            **kwargs: Additional configuration including:
                - azure_endpoint: Azure OpenAI endpoint URL
                - api_version: API version (default: 2024-02-15-preview)
                - default_model: Default model to use
        """
        super().__init__(api_key, **kwargs)
        
        self.azure_endpoint = kwargs.get("azure_endpoint")
        self.api_version = kwargs.get("api_version", "2024-02-15-preview")
        self.default_model = kwargs.get("default_model", "gpt-4o-mini")
        
        if not self.azure_endpoint:
            raise ValueError("azure_endpoint is required for Azure OpenAI provider")
        
        self._client = None
    
    @property
    def provider_type(self) -> AIProviderType:
        """Return the provider type."""
        return AIProviderType.AZURE_OPENAI
    
    @property
    def supported_models(self) -> List[str]:
        """Return list of supported models."""
        return [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-4",
            "gpt-35-turbo",
            "gpt-35-turbo-16k"
        ]
    
    @property
    def default_model(self) -> str:
        """Return the default model for this provider."""
        return self.default_model
    
    async def initialize(self) -> None:
        """Initialize the Azure OpenAI client."""
        try:
            self._client = AzureOpenAI(
                api_key=self.api_key,
                api_version=self.api_version,
                azure_endpoint=self.azure_endpoint
            )
            logger.info(f"Azure OpenAI client initialized with endpoint: {self.azure_endpoint}")
        except Exception as e:
            logger.error(f"Failed to initialize Azure OpenAI client: {e}")
            raise AIProviderError(f"Failed to initialize client: {e}", self.provider_type.value)
    
    async def generate_content(
        self, 
        request: AIRequest, 
        model: Optional[str] = None
    ) -> AIResponse:
        """
        Generate content using Azure OpenAI.
        
        Args:
            request: AI generation request
            model: Optional model override
            
        Returns:
            AI response with generated content
        """
        if not self._client:
            await self.initialize()
        
        model_to_use = model or self.default_model
        start_time = time.time()
        
        try:
            # Prepare messages
            messages = [
                {"role": "system", "content": self._get_system_prompt(request)},
                {"role": "user", "content": request.prompt}
            ]
            
            # Prepare parameters
            params = {
                "model": model_to_use,
                "messages": messages,
                "max_tokens": request.config.max_tokens,
                "temperature": request.config.temperature,
                "top_p": request.config.top_p,
                "frequency_penalty": request.config.frequency_penalty,
                "presence_penalty": request.config.presence_penalty,
            }
            
            # Add stop sequences if provided
            if request.config.stop_sequences:
                params["stop"] = request.config.stop_sequences
            
            # Add model-specific parameters
            if request.config.model_specific_params:
                params.update(request.config.model_specific_params)
            
            # Make API call
            response: ChatCompletion = self._client.chat.completions.create(**params)
            
            generation_time = time.time() - start_time
            
            # Extract content
            content = response.choices[0].message.content or ""
            
            # Calculate tokens and cost
            tokens_used = response.usage.total_tokens if response.usage else 0
            cost = self.estimate_cost(tokens_used, model_to_use)
            
            return AIResponse(
                content=content,
                provider=self.provider_type.value,
                model=model_to_use,
                tokens_used=tokens_used,
                cost=cost,
                generation_time=generation_time,
                metadata={
                    "finish_reason": response.choices[0].finish_reason,
                    "azure_endpoint": self.azure_endpoint,
                    "api_version": self.api_version
                }
            )
            
        except Exception as e:
            generation_time = time.time() - start_time
            error_msg = str(e)
            
            # Handle specific error types
            if "rate_limit" in error_msg.lower() or "429" in error_msg:
                raise AIProviderRateLimitError(error_msg, self.provider_type.value)
            elif "unauthorized" in error_msg.lower() or "401" in error_msg:
                raise AIProviderAuthenticationError(error_msg, self.provider_type.value)
            elif "quota" in error_msg.lower() or "insufficient" in error_msg.lower():
                raise AIProviderQuotaExceededError(error_msg, self.provider_type.value)
            else:
                raise AIProviderError(error_msg, self.provider_type.value)
    
    async def validate_api_key(self) -> bool:
        """
        Validate the Azure OpenAI API key.
        
        Returns:
            True if API key is valid, False otherwise
        """
        try:
            if not self._client:
                await self.initialize()
            
            # Make a simple API call to validate the key
            response = self._client.chat.completions.create(
                model=self.default_model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=1
            )
            
            return response.choices[0].message.content is not None
            
        except Exception as e:
            logger.error(f"API key validation failed for Azure OpenAI: {e}")
            return False
    
    def estimate_cost(self, tokens: int, model: Optional[str] = None) -> float:
        """
        Estimate the cost for a given number of tokens.
        
        Args:
            tokens: Number of tokens
            model: Model to use for cost estimation
            
        Returns:
            Estimated cost in USD
        """
        model_to_use = model or self.default_model
        
        # Azure OpenAI pricing (as of 2024, may need updates)
        pricing = {
            "gpt-4o": {"input": 0.005, "output": 0.015},  # per 1K tokens
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-35-turbo": {"input": 0.0015, "output": 0.002},
            "gpt-35-turbo-16k": {"input": 0.003, "output": 0.004}
        }
        
        if model_to_use not in pricing:
            # Default to GPT-4 pricing if model not found
            model_to_use = "gpt-4"
        
        # Estimate 70% input, 30% output tokens
        input_tokens = int(tokens * 0.7)
        output_tokens = int(tokens * 0.3)
        
        input_cost = (input_tokens / 1000) * pricing[model_to_use]["input"]
        output_cost = (output_tokens / 1000) * pricing[model_to_use]["output"]
        
        return input_cost + output_cost
    
    def get_rate_limits(self) -> Dict[str, Any]:
        """
        Get rate limit information for the provider.
        
        Returns:
            Dictionary with rate limit information
        """
        # Azure OpenAI rate limits vary by deployment
        # These are general guidelines
        return {
            "requests_per_minute": 60,
            "tokens_per_minute": 150000,
            "requests_per_day": 10000,
            "tokens_per_day": 1000000,
            "concurrent_requests": 10
        }
    
    def _get_system_prompt(self, request: AIRequest) -> str:
        """Generate system prompt based on content type and context."""
        base_prompts = {
            "blog_post": "You are an expert content writer specializing in creating engaging, SEO-optimized blog posts. Write in a professional yet accessible tone.",
            "introduction": "You are an expert at writing compelling blog post introductions that hook readers and clearly introduce the topic.",
            "conclusion": "You are an expert at writing strong blog post conclusions that summarize key points and provide clear next steps for readers.",
            "section": "You are an expert at writing detailed, informative blog post sections that provide value to readers.",
            "title": "You are an expert at creating compelling, SEO-friendly blog post titles that attract clicks and accurately represent the content.",
            "meta_description": "You are an expert at writing concise, compelling meta descriptions that encourage clicks and accurately summarize the content.",
            "faq": "You are an expert at writing clear, helpful FAQ sections that address common questions and concerns.",
            "summary": "You are an expert at creating concise, accurate summaries that capture the key points of longer content."
        }
        
        system_prompt = base_prompts.get(request.content_type.value, base_prompts["blog_post"])
        
        # Add context if provided
        if request.context:
            if "tone" in request.context:
                system_prompt += f" Maintain a {request.context['tone']} tone throughout."
            if "audience" in request.context:
                system_prompt += f" Write for an audience of {request.context['audience']}."
            if "style" in request.context:
                system_prompt += f" Use a {request.context['style']} writing style."
        
        return system_prompt
