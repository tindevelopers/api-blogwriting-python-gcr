"""
Anthropic Claude provider implementation for the AI abstraction layer.
"""

import time
from typing import Dict, List, Optional, Any
from anthropic import AsyncAnthropic
from anthropic.types import Message

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


class AnthropicProvider(BaseAIProvider):
    """Anthropic Claude provider implementation."""
    
    # Model pricing per 1M tokens (input, output)
    MODEL_PRICING = {
        "claude-3-5-sonnet-20241022": (3.00, 15.00),
        "claude-3-5-haiku-20241022": (0.25, 1.25),
        "claude-3-opus-20240229": (15.00, 75.00),
        "claude-3-sonnet-20240229": (3.00, 15.00),
        "claude-3-haiku-20240307": (0.25, 1.25),
    }
    
    def __init__(self, api_key: str, **kwargs):
        """Initialize Anthropic provider."""
        super().__init__(api_key, **kwargs)
        self.max_retries = kwargs.get('max_retries', 3)
        self.timeout = kwargs.get('timeout', 30)
    
    @property
    def provider_type(self) -> AIProviderType:
        """Return the provider type."""
        return AIProviderType.ANTHROPIC
    
    @property
    def supported_models(self) -> List[str]:
        """Return list of supported models."""
        return list(self.MODEL_PRICING.keys())
    
    @property
    def default_model(self) -> str:
        """Return the default model."""
        return "claude-3-5-haiku-20241022"
    
    async def initialize(self) -> None:
        """Initialize the Anthropic client."""
        self._client = AsyncAnthropic(
            api_key=self.api_key,
            max_retries=self.max_retries,
            timeout=self.timeout
        )
    
    async def generate_content(
        self, 
        request: AIRequest, 
        model: Optional[str] = None
    ) -> AIResponse:
        """Generate content using Anthropic Claude."""
        if not self._client:
            await self.initialize()
        
        model_to_use = model or self.default_model
        start_time = time.time()
        
        try:
            # Prepare system prompt
            system_prompt = self._get_system_prompt(request.content_type)
            
            # Add context to system prompt if provided
            if request.context:
                context_message = self._format_context(request.context)
                system_prompt += f"\n\n{context_message}"
            
            # Prepare parameters
            params = {
                "model": model_to_use,
                "max_tokens": request.config.max_tokens,
                "temperature": request.config.temperature,
                "top_p": request.config.top_p,
                "system": system_prompt,
                "messages": [
                    {"role": "user", "content": request.prompt}
                ]
            }
            
            # Add stop sequences if provided
            if request.config.stop_sequences:
                params["stop_sequences"] = request.config.stop_sequences
            
            # Add model-specific parameters
            if request.config.model_specific_params:
                # Filter out parameters that Claude doesn't support
                claude_params = {
                    k: v for k, v in request.config.model_specific_params.items()
                    if k in ["top_k", "metadata"]
                }
                params.update(claude_params)
            
            # Make the API call
            response: Message = await self._client.messages.create(**params)
            
            generation_time = time.time() - start_time
            
            # Extract content
            content = ""
            if response.content:
                for block in response.content:
                    if hasattr(block, 'text'):
                        content += block.text
            
            # Calculate cost
            input_tokens = response.usage.input_tokens if response.usage else 0
            output_tokens = response.usage.output_tokens if response.usage else 0
            total_tokens = input_tokens + output_tokens
            cost = self._calculate_cost(input_tokens, output_tokens, model_to_use)
            
            return AIResponse(
                content=content,
                provider=self.provider_type.value,
                model=model_to_use,
                tokens_used=total_tokens,
                cost=cost,
                generation_time=generation_time,
                metadata={
                    "stop_reason": response.stop_reason,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "stop_sequence": response.stop_sequence,
                }
            )
            
        except Exception as e:
            error_message = str(e)
            
            # Handle specific Anthropic errors
            if "rate_limit" in error_message.lower():
                raise AIProviderRateLimitError(error_message, self.provider_type.value)
            elif "insufficient_quota" in error_message.lower() or "quota" in error_message.lower():
                raise AIProviderQuotaExceededError(error_message, self.provider_type.value)
            elif "authentication" in error_message.lower() or "api_key" in error_message.lower():
                raise AIProviderAuthenticationError(error_message, self.provider_type.value)
            else:
                raise AIProviderError(error_message, self.provider_type.value)
    
    async def validate_api_key(self) -> bool:
        """Validate the Anthropic API key."""
        if not self._client:
            await self.initialize()
        
        try:
            # Make a minimal API call to test the key
            await self._client.messages.create(
                model=self.default_model,
                max_tokens=1,
                messages=[{"role": "user", "content": "test"}]
            )
            return True
        except Exception:
            return False
    
    def estimate_cost(self, tokens: int, model: Optional[str] = None) -> float:
        """Estimate cost for given tokens."""
        model_to_use = model or self.default_model
        
        # Assume 70% input, 30% output tokens (rough estimate)
        input_tokens = int(tokens * 0.7)
        output_tokens = int(tokens * 0.3)
        
        return self._calculate_cost(input_tokens, output_tokens, model_to_use)
    
    def _calculate_cost(self, input_tokens: int, output_tokens: int, model: str) -> float:
        """Calculate exact cost based on input and output tokens."""
        if model not in self.MODEL_PRICING:
            # Use default pricing if model not found
            input_price, output_price = self.MODEL_PRICING[self.default_model]
        else:
            input_price, output_price = self.MODEL_PRICING[model]
        
        # Pricing is per 1M tokens
        cost = (input_tokens / 1_000_000 * input_price) + (output_tokens / 1_000_000 * output_price)
        return round(cost, 6)
    
    def get_rate_limits(self) -> Dict[str, Any]:
        """Get Anthropic rate limits."""
        return {
            "requests_per_minute": 1000,  # Varies by model and tier
            "tokens_per_minute": 100000,  # Varies by model and tier
            "requests_per_day": 10000,    # Varies by tier
        }
    
    def _get_system_prompt(self, content_type) -> str:
        """Get system prompt based on content type."""
        prompts = {
            "blog_post": (
                "You are Claude, an expert blog writer with deep expertise in SEO optimization "
                "and engaging content creation. Your writing is clear, informative, and valuable "
                "to readers. You structure content logically with proper headings, incorporate "
                "keywords naturally, and maintain a consistent tone throughout. You always "
                "provide accurate, well-researched information and cite sources when appropriate."
            ),
            "introduction": (
                "You are Claude, an expert at crafting compelling blog post introductions. "
                "You excel at creating openings that immediately capture reader attention, "
                "clearly establish the value proposition, and smoothly transition into the "
                "main content. Your introductions are concise yet comprehensive, setting "
                "proper expectations for what readers will learn."
            ),
            "conclusion": (
                "You are Claude, an expert at writing impactful blog post conclusions. "
                "You excel at summarizing key insights, reinforcing the main message, "
                "and providing clear, actionable next steps. Your conclusions leave "
                "readers feeling satisfied and motivated to take action or learn more."
            ),
            "section": (
                "You are Claude, an expert at developing detailed, informative blog post sections. "
                "You break down complex topics into digestible parts, use examples and analogies "
                "to clarify concepts, and maintain logical flow between ideas. Your content is "
                "thorough yet accessible, providing real value to readers."
            ),
            "title": (
                "You are Claude, an expert at creating compelling, SEO-optimized blog titles. "
                "You craft titles that are both search-engine friendly and irresistibly "
                "clickable. Your titles accurately represent the content while incorporating "
                "power words and emotional triggers that drive engagement."
            ),
            "meta_description": (
                "You are Claude, an expert at writing persuasive SEO meta descriptions. "
                "You create descriptions that accurately summarize content in under 160 "
                "characters while compelling users to click. Your descriptions include "
                "relevant keywords and clear value propositions."
            ),
            "faq": (
                "You are Claude, an expert at creating comprehensive FAQ sections. "
                "You anticipate common reader questions and provide thorough, helpful "
                "answers. Your FAQs address both basic and advanced concerns, improving "
                "user experience and SEO performance through structured data opportunities."
            ),
            "summary": (
                "You are Claude, an expert at distilling complex information into clear, "
                "concise summaries. You identify and present the most important points "
                "while maintaining the essence and nuance of the original content. "
                "Your summaries are both comprehensive and accessible."
            )
        }
        
        return prompts.get(content_type.value, prompts["blog_post"])
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context information for the prompt."""
        context_parts = []
        
        if "keywords" in context:
            keywords = ", ".join(context["keywords"])
            context_parts.append(f"Target keywords to incorporate naturally: {keywords}")
        
        if "tone" in context:
            context_parts.append(f"Writing tone and style: {context['tone']}")
        
        if "audience" in context:
            context_parts.append(f"Target audience: {context['audience']}")
        
        if "word_count" in context:
            context_parts.append(f"Target word count: approximately {context['word_count']} words")
        
        if "brand_voice" in context:
            context_parts.append(f"Brand voice and personality: {context['brand_voice']}")
        
        if "additional_instructions" in context:
            context_parts.append(f"Special instructions: {context['additional_instructions']}")
        
        if "industry" in context:
            context_parts.append(f"Industry context: {context['industry']}")
        
        if "competitor_analysis" in context:
            context_parts.append(f"Competitive landscape: {context['competitor_analysis']}")
        
        return "CONTEXT AND REQUIREMENTS:\n" + "\n".join(f"• {part}" for part in context_parts) if context_parts else ""
