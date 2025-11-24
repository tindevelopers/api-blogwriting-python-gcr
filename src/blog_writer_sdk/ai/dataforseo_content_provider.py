"""
DataForSEO Content Generation API provider implementation.

This provider integrates with DataForSEO's Content Generation API for
cost-effective blog and content generation.
"""

import time
import logging
from typing import Dict, List, Optional, Any
from ..integrations.dataforseo_integration import DataForSEOClient
from .base_provider import (
    BaseAIProvider,
    AIProviderType,
    AIRequest,
    AIResponse,
    AIProviderError,
    AIProviderRateLimitError,
    AIProviderAuthenticationError,
    AIProviderQuotaExceededError,
    AIGenerationConfig
)

logger = logging.getLogger(__name__)


class DataForSEOContentProvider(BaseAIProvider):
    """DataForSEO Content Generation API provider implementation."""
    
    # DataForSEO Content Generation API pricing
    # $0.00005 per new token ($50 for 1M tokens)
    PRICE_PER_TOKEN = 0.00005
    
    def __init__(self, api_key: str, api_secret: str, **kwargs):
        """
        Initialize DataForSEO Content Generation provider.
        
        Args:
            api_key: DataForSEO API key
            api_secret: DataForSEO API secret
            **kwargs: Additional configuration
        """
        super().__init__(api_key, **kwargs)
        self.api_secret = api_secret
        self._client: Optional[DataForSEOClient] = None
        self.base_url = kwargs.get('base_url', 'https://api.dataforseo.com/v3')
        self.timeout = kwargs.get('timeout', 60)  # Content generation can take longer
    
    @property
    def provider_type(self) -> AIProviderType:
        """Return the provider type."""
        # Add DATAFORSEO to enum if not present, or use existing
        try:
            return AIProviderType.DATAFORSEO
        except AttributeError:
            # Fallback if enum doesn't have DATAFORSEO yet
            return AIProviderType.OPENAI  # Temporary fallback
    
    @property
    def supported_models(self) -> List[str]:
        """Return list of supported models."""
        # DataForSEO uses a single model for content generation
        return ["dataforseo-content-generator"]
    
    @property
    def default_model(self) -> str:
        """Return the default model."""
        return "dataforseo-content-generator"
    
    async def initialize(self) -> None:
        """Initialize the DataForSEO client."""
        if not self._client:
            self._client = DataForSEOClient(
                api_key=self.api_key,
                api_secret=self.api_secret,
                location="United States",
                language_code="en"
            )
            await self._client.initialize_credentials("default")
    
    async def generate_content(
        self,
        request: AIRequest,
        model: Optional[str] = None
    ) -> AIResponse:
        """
        Generate content using DataForSEO Content Generation API.
        
        Args:
            request: AI generation request
            model: Optional model override (ignored, DataForSEO uses single model)
            
        Returns:
            AI response with generated content
        """
        if not self._client:
            await self.initialize()
        
        if not self._client.is_configured:
            raise AIProviderAuthenticationError(
                "DataForSEO API not configured",
                "dataforseo"
            )
        
        start_time = time.time()
        
        try:
            # Prepare prompt based on content type and context
            prompt = self._build_prompt(request)
            
            # Call DataForSEO Content Generation API
            result = await self._client.generate_text(
                prompt=prompt,
                max_tokens=request.config.max_tokens,
                temperature=request.config.temperature,
                tenant_id="default"
            )
            
            generation_time = time.time() - start_time
            
            # Extract generated content
            content = result.get("text", "")
            tokens_used = result.get("tokens_used", 0)
            cost = self.estimate_cost(tokens_used)
            
            return AIResponse(
                content=content,
                provider="dataforseo",
                model=self.default_model,
                tokens_used=tokens_used,
                cost=cost,
                generation_time=generation_time,
                metadata={
                    "api_endpoint": "content_generation/generate_text/live",
                    "prompt_length": len(prompt),
                    "result_length": len(content)
                }
            )
            
        except Exception as e:
            logger.error(f"DataForSEO content generation failed: {e}")
            if "401" in str(e) or "unauthorized" in str(e).lower():
                raise AIProviderAuthenticationError(
                    f"DataForSEO authentication failed: {e}",
                    "dataforseo"
                )
            elif "429" in str(e) or "rate limit" in str(e).lower():
                raise AIProviderRateLimitError(
                    f"DataForSEO rate limit exceeded: {e}",
                    "dataforseo"
                )
            else:
                raise AIProviderError(
                    f"DataForSEO content generation failed: {e}",
                    "dataforseo"
                )
    
    def _build_prompt(self, request: AIRequest) -> str:
        """
        Build prompt for DataForSEO Content Generation API.
        
        Args:
            request: AI generation request
            
        Returns:
            Formatted prompt string
        """
        base_prompt = request.prompt
        
        # Add context if available
        if request.context:
            context_parts = []
            if "keywords" in request.context:
                keywords = request.context["keywords"]
                if keywords:
                    context_parts.append(f"Keywords: {', '.join(keywords)}")
            
            if "tone" in request.context:
                context_parts.append(f"Tone: {request.context['tone']}")
            
            if "target_length" in request.context:
                context_parts.append(f"Target length: {request.context['target_length']} words")
            
            if context_parts:
                context_str = "\n".join(context_parts)
                base_prompt = f"{context_str}\n\n{base_prompt}"
        
        return base_prompt
    
    async def validate_api_key(self) -> bool:
        """Validate the DataForSEO API credentials."""
        try:
            if not self._client:
                await self.initialize()
            return self._client.is_configured
        except Exception as e:
            logger.error(f"DataForSEO API key validation failed: {e}")
            return False
    
    def estimate_cost(self, tokens: int, model: Optional[str] = None) -> float:
        """
        Estimate cost for token usage.
        
        Args:
            tokens: Number of tokens
            model: Optional model override (ignored)
            
        Returns:
            Estimated cost in USD
        """
        return tokens * self.PRICE_PER_TOKEN
    
    async def paraphrase_content(
        self,
        text: str,
        tenant_id: str = "default"
    ) -> Dict[str, Any]:
        """
        Paraphrase content using DataForSEO API.
        
        Args:
            text: Text to paraphrase
            tenant_id: Tenant ID
            
        Returns:
            Paraphrased content result
        """
        if not self._client:
            await self.initialize()
        
        return await self._client.paraphrase_text(
            text=text,
            tenant_id=tenant_id
        )
    
    async def check_grammar(
        self,
        text: str,
        tenant_id: str = "default"
    ) -> Dict[str, Any]:
        """
        Check grammar using DataForSEO API.
        
        Args:
            text: Text to check
            tenant_id: Tenant ID
            
        Returns:
            Grammar check result
        """
        if not self._client:
            await self.initialize()
        
        return await self._client.check_grammar(
            text=text,
            tenant_id=tenant_id
        )
    
    async def generate_meta_tags(
        self,
        title: str,
        content: str,
        tenant_id: str = "default"
    ) -> Dict[str, Any]:
        """
        Generate meta tags using DataForSEO API.
        
        Args:
            title: Page title
            content: Page content
            tenant_id: Tenant ID
            
        Returns:
            Meta tags result
        """
        if not self._client:
            await self.initialize()
        
        return await self._client.generate_meta_tags(
            title=title,
            content=content,
            tenant_id=tenant_id
        )

