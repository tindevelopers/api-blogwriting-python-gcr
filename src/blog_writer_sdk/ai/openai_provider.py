"""
OpenAI provider implementation for the AI abstraction layer.
"""

import time
from typing import Dict, List, Optional, Any
import asyncio
from openai import AsyncOpenAI
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


class OpenAIProvider(BaseAIProvider):
    """OpenAI provider implementation."""
    
    # Model pricing per 1K tokens (input, output)
    MODEL_PRICING = {
        "gpt-4o": (0.0025, 0.01),
        "gpt-4o-mini": (0.00015, 0.0006),
        "gpt-4-turbo": (0.01, 0.03),
        "gpt-4": (0.03, 0.06),
        "gpt-3.5-turbo": (0.0005, 0.0015),
        "gpt-3.5-turbo-16k": (0.003, 0.004),
    }
    
    def __init__(self, api_key: str, **kwargs):
        """Initialize OpenAI provider."""
        super().__init__(api_key, **kwargs)
        self.organization = kwargs.get('organization')
        self.base_url = kwargs.get('base_url')
        self.max_retries = kwargs.get('max_retries', 3)
        self.timeout = kwargs.get('timeout', 30)
    
    @property
    def provider_type(self) -> AIProviderType:
        """Return the provider type."""
        return AIProviderType.OPENAI
    
    @property
    def supported_models(self) -> List[str]:
        """Return list of supported models."""
        return list(self.MODEL_PRICING.keys())
    
    @property
    def default_model(self) -> str:
        """Return the default model."""
        return "gpt-4o-mini"
    
    async def initialize(self) -> None:
        """Initialize the OpenAI client."""
        self._client = AsyncOpenAI(
            api_key=self.api_key,
            organization=self.organization,
            base_url=self.base_url,
            max_retries=self.max_retries,
            timeout=self.timeout
        )
    
    async def generate_content(
        self, 
        request: AIRequest, 
        model: Optional[str] = None
    ) -> AIResponse:
        """Generate content using OpenAI."""
        if not self._client:
            await self.initialize()
        
        model_to_use = model or self.default_model
        start_time = time.time()
        
        try:
            # Prepare messages
            messages = [
                {"role": "system", "content": self._get_system_prompt(request.content_type)},
                {"role": "user", "content": request.prompt}
            ]
            
            # Add context if provided
            if request.context:
                context_message = self._format_context(request.context)
                messages.insert(1, {"role": "system", "content": context_message})
            
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
            
            # Make the API call
            response: ChatCompletion = await self._client.chat.completions.create(**params)
            
            generation_time = time.time() - start_time
            
            # Extract content
            content = response.choices[0].message.content or ""
            
            # Calculate cost
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
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                }
            )
            
        except Exception as e:
            error_message = str(e)
            
            # Handle specific OpenAI errors
            if "rate_limit_exceeded" in error_message.lower():
                raise AIProviderRateLimitError(error_message, self.provider_type.value)
            elif "insufficient_quota" in error_message.lower():
                raise AIProviderQuotaExceededError(error_message, self.provider_type.value)
            elif "invalid_api_key" in error_message.lower():
                raise AIProviderAuthenticationError(error_message, self.provider_type.value)
            else:
                raise AIProviderError(error_message, self.provider_type.value)
    
    async def validate_api_key(self) -> bool:
        """Validate the OpenAI API key."""
        if not self._client:
            await self.initialize()
        
        try:
            # Make a minimal API call to test the key
            await self._client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
            )
            return True
        except Exception:
            return False
    
    def estimate_cost(self, tokens: int, model: Optional[str] = None) -> float:
        """Estimate cost for given tokens."""
        model_to_use = model or self.default_model
        
        if model_to_use not in self.MODEL_PRICING:
            # Use default pricing if model not found
            input_price, output_price = self.MODEL_PRICING[self.default_model]
        else:
            input_price, output_price = self.MODEL_PRICING[model_to_use]
        
        # Assume 70% input, 30% output tokens (rough estimate)
        input_tokens = int(tokens * 0.7)
        output_tokens = int(tokens * 0.3)
        
        cost = (input_tokens / 1000 * input_price) + (output_tokens / 1000 * output_price)
        return round(cost, 6)
    
    def get_rate_limits(self) -> Dict[str, Any]:
        """Get OpenAI rate limits."""
        return {
            "requests_per_minute": 3500,  # Varies by model and tier
            "tokens_per_minute": 90000,   # Varies by model and tier
            "requests_per_day": 10000,    # Varies by tier
        }
    
    def _get_system_prompt(self, content_type) -> str:
        """Get system prompt based on content type."""
        prompts = {
            "blog_post": (
                "You are an expert blog writer specializing in SEO-optimized, "
                "engaging content. Create well-structured, informative blog posts "
                "that provide value to readers while being optimized for search engines."
            ),
            "introduction": (
                "You are an expert at writing compelling blog post introductions. "
                "Create engaging openings that hook readers and clearly introduce "
                "the topic while incorporating relevant keywords naturally."
            ),
            "conclusion": (
                "You are an expert at writing effective blog post conclusions. "
                "Create summaries that reinforce key points, provide actionable "
                "takeaways, and encourage reader engagement."
            ),
            "section": (
                "You are an expert at writing detailed blog post sections. "
                "Create informative, well-structured content that thoroughly "
                "covers the topic while maintaining reader engagement."
            ),
            "title": (
                "You are an expert at writing compelling, SEO-optimized blog titles. "
                "Create titles that are attention-grabbing, keyword-rich, and "
                "accurately represent the content."
            ),
            "meta_description": (
                "You are an expert at writing SEO meta descriptions. Create "
                "compelling descriptions under 160 characters that accurately "
                "summarize the content and encourage clicks."
            ),
            "faq": (
                "You are an expert at creating FAQ sections for blog posts. "
                "Generate relevant questions and comprehensive answers that "
                "address common reader concerns and improve SEO."
            ),
            "summary": (
                "You are an expert at creating concise, informative summaries. "
                "Extract and present the key points in a clear, digestible format."
            )
        }
        
        return prompts.get(content_type.value, prompts["blog_post"])
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context information for the prompt."""
        context_parts = []
        
        if "keywords" in context:
            keywords = ", ".join(context["keywords"])
            context_parts.append(f"Target keywords: {keywords}")
        
        if "tone" in context:
            context_parts.append(f"Writing tone: {context['tone']}")
        
        if "audience" in context:
            context_parts.append(f"Target audience: {context['audience']}")
        
        if "word_count" in context:
            context_parts.append(f"Target word count: {context['word_count']}")
        
        if "brand_voice" in context:
            context_parts.append(f"Brand voice: {context['brand_voice']}")
        
        if "additional_instructions" in context:
            context_parts.append(f"Additional instructions: {context['additional_instructions']}")
        
        return "Context: " + " | ".join(context_parts) if context_parts else ""


class AzureOpenAIProvider(OpenAIProvider):
    """Azure OpenAI provider implementation."""
    
    def __init__(self, api_key: str, azure_endpoint: str, api_version: str = "2024-02-15-preview", **kwargs):
        """Initialize Azure OpenAI provider."""
        super().__init__(api_key, **kwargs)
        self.azure_endpoint = azure_endpoint
        self.api_version = api_version
    
    @property
    def provider_type(self) -> AIProviderType:
        """Return the provider type."""
        return AIProviderType.AZURE_OPENAI
    
    async def initialize(self) -> None:
        """Initialize the Azure OpenAI client."""
        self._client = AsyncOpenAI(
            api_key=self.api_key,
            azure_endpoint=self.azure_endpoint,
            api_version=self.api_version,
            max_retries=self.max_retries,
            timeout=self.timeout
        )
    
    def get_rate_limits(self) -> Dict[str, Any]:
        """Get Azure OpenAI rate limits."""
        return {
            "requests_per_minute": 240,   # Default for standard deployment
            "tokens_per_minute": 40000,   # Default for standard deployment
            "requests_per_day": None,     # No daily limit by default
        }
