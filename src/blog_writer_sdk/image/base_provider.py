"""
Base Image Provider Interface

This module defines the abstract base classes for image generation providers,
enabling easy switching between different image generation services.
"""

import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from pydantic import BaseModel, Field
from dataclasses import dataclass

from ..models.image_models import (
    ImageProviderType,
    ImageStyle,
    ImageAspectRatio,
    ImageQuality,
    ImageGenerationRequest,
    ImageGenerationResponse,
    GeneratedImage,
    ImageProviderConfig,
    ImageVariationRequest,
    ImageUpscaleRequest,
    ImageEditRequest
)

logger = logging.getLogger(__name__)


class ImageProviderError(Exception):
    """Base exception for image provider errors."""
    def __init__(self, message: str, provider: str, error_code: Optional[str] = None):
        self.message = message
        self.provider = provider
        self.error_code = error_code
        super().__init__(f"[{provider}] {message}")


class ImageProviderRateLimitError(ImageProviderError):
    """Exception raised when rate limits are exceeded."""
    pass


class ImageProviderAuthenticationError(ImageProviderError):
    """Exception raised when authentication fails."""
    pass


class ImageProviderQuotaExceededError(ImageProviderError):
    """Exception raised when quota is exceeded."""
    pass


class ImageProviderContentPolicyError(ImageProviderError):
    """Exception raised when content violates provider policies."""
    pass


class BaseImageProvider(ABC):
    """
    Abstract base class for image generation providers.
    
    This class defines the interface that all image providers must implement,
    enabling easy switching between different image generation services.
    """
    
    def __init__(self, api_key: str, **kwargs):
        """
        Initialize the image provider.
        
        Args:
            api_key: API key for the provider
            **kwargs: Additional provider-specific configuration
        """
        self.api_key = api_key
        self.config = kwargs
        self._client = None
    
    @property
    @abstractmethod
    def provider_type(self) -> ImageProviderType:
        """Return the provider type."""
        pass
    
    @property
    @abstractmethod
    def supported_styles(self) -> List[ImageStyle]:
        """Return list of supported image styles."""
        pass
    
    @property
    @abstractmethod
    def supported_aspect_ratios(self) -> List[ImageAspectRatio]:
        """Return list of supported aspect ratios."""
        pass
    
    @property
    @abstractmethod
    def max_resolution(self) -> str:
        """Return maximum supported resolution."""
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
    async def generate_image(
        self, 
        request: ImageGenerationRequest
    ) -> ImageGenerationResponse:
        """
        Generate an image using the provider.
        
        Args:
            request: Image generation request
            
        Returns:
            Image generation response with generated images
        """
        pass
    
    @abstractmethod
    async def generate_variations(
        self, 
        request: ImageVariationRequest
    ) -> ImageGenerationResponse:
        """
        Generate variations of an existing image.
        
        Args:
            request: Image variation request
            
        Returns:
            Image generation response with variations
        """
        pass
    
    @abstractmethod
    async def upscale_image(
        self, 
        request: ImageUpscaleRequest
    ) -> ImageGenerationResponse:
        """
        Upscale an existing image.
        
        Args:
            request: Image upscale request
            
        Returns:
            Image generation response with upscaled image
        """
        pass
    
    @abstractmethod
    async def edit_image(
        self, 
        request: ImageEditRequest
    ) -> ImageGenerationResponse:
        """
        Edit an existing image (inpainting/outpainting).
        
        Args:
            request: Image edit request
            
        Returns:
            Image generation response with edited image
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
    def estimate_cost(self, request: ImageGenerationRequest) -> float:
        """
        Estimate the cost for image generation.
        
        Args:
            request: Image generation request
            
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
                "rate_limits": self.get_rate_limits(),
                "supported_styles": [style.value for style in self.supported_styles],
                "supported_aspect_ratios": [ratio.value for ratio in self.supported_aspect_ratios],
                "max_resolution": self.max_resolution
            }
        except Exception as e:
            return {
                "provider": self.provider_type.value,
                "status": "error",
                "error": str(e)
            }
    
    def _calculate_dimensions(self, aspect_ratio: ImageAspectRatio, width: Optional[int] = None, height: Optional[int] = None) -> tuple[int, int]:
        """
        Calculate image dimensions based on aspect ratio and optional custom dimensions.
        
        Args:
            aspect_ratio: Desired aspect ratio
            width: Optional custom width
            height: Optional custom height
            
        Returns:
            Tuple of (width, height)
        """
        if aspect_ratio == ImageAspectRatio.CUSTOM and width and height:
            return width, height
        
        # Default dimensions for each aspect ratio
        aspect_ratios = {
            ImageAspectRatio.SQUARE: (1024, 1024),
            ImageAspectRatio.PORTRAIT: (768, 1024),
            ImageAspectRatio.LANDSCAPE: (1024, 768),
            ImageAspectRatio.WIDE: (1024, 576),
            ImageAspectRatio.ULTRA_WIDE: (1024, 432),
            ImageAspectRatio.TALL: (768, 1152),
        }
        
        return aspect_ratios.get(aspect_ratio, (1024, 1024))
    
    def _validate_request(self, request: ImageGenerationRequest) -> None:
        """
        Validate the image generation request.
        
        Args:
            request: Image generation request
            
        Raises:
            ImageProviderError: If request is invalid
        """
        if not request.prompt.strip():
            raise ImageProviderError("Prompt cannot be empty", self.provider_type.value)
        
        if request.style and request.style not in self.supported_styles:
            raise ImageProviderError(
                f"Style '{request.style}' not supported by {self.provider_type.value}",
                self.provider_type.value
            )
        
        if request.aspect_ratio not in self.supported_aspect_ratios:
            raise ImageProviderError(
                f"Aspect ratio '{request.aspect_ratio}' not supported by {self.provider_type.value}",
                self.provider_type.value
            )
    
    def _create_generated_image(
        self,
        image_data: bytes,
        image_url: Optional[str] = None,
        width: int = 1024,
        height: int = 1024,
        format: str = "png",
        seed: Optional[int] = None,
        steps: Optional[int] = None,
        guidance_scale: Optional[float] = None,
        model: Optional[str] = None
    ) -> GeneratedImage:
        """
        Create a GeneratedImage object from image data.
        
        Args:
            image_data: Raw image data
            image_url: Optional URL to the image
            width: Image width
            height: Image height
            format: Image format
            seed: Generation seed
            steps: Generation steps
            guidance_scale: Guidance scale used
            model: Model used
            
        Returns:
            GeneratedImage object
        """
        import uuid
        import base64
        
        image_id = str(uuid.uuid4())
        image_data_b64 = base64.b64encode(image_data).decode('utf-8')
        
        return GeneratedImage(
            image_id=image_id,
            image_url=image_url,
            image_data=image_data_b64,
            width=width,
            height=height,
            format=format,
            size_bytes=len(image_data),
            seed=seed,
            steps=steps,
            guidance_scale=guidance_scale,
            provider=self.provider_type,
            model=model
        )


class ImageProviderManager:
    """
    Manager class for handling multiple image providers with fallback support.
    """
    
    def __init__(self):
        self.providers: Dict[str, BaseImageProvider] = {}
        self.provider_configs: Dict[str, ImageProviderConfig] = {}
        self.fallback_order: List[str] = []
    
    def add_provider(self, name: str, provider: BaseImageProvider, config: ImageProviderConfig):
        """Add an image provider to the manager."""
        self.providers[name] = provider
        self.provider_configs[name] = config
        self._update_fallback_order()
    
    def remove_provider(self, name: str):
        """Remove an image provider from the manager."""
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
    
    async def generate_image(
        self, 
        request: ImageGenerationRequest, 
        preferred_provider: Optional[str] = None
    ) -> ImageGenerationResponse:
        """
        Generate an image using the specified provider or fallback chain.
        
        Args:
            request: Image generation request
            preferred_provider: Preferred provider name
            
        Returns:
            Image generation response
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
            raise ImageProviderError("No enabled image providers available", "manager")
        
        last_error = None
        
        for provider_name in providers_to_try:
            try:
                provider = self.providers[provider_name]
                response = await provider.generate_image(request)
                return response
            
            except ImageProviderRateLimitError as e:
                last_error = e
                continue  # Try next provider
            
            except ImageProviderQuotaExceededError as e:
                last_error = e
                continue  # Try next provider
            
            except Exception as e:
                last_error = e
                continue  # Try next provider
        
        # If we get here, all providers failed
        raise ImageProviderError(
            f"All image providers failed. Last error: {str(last_error)}", 
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
                "available": provider is not None,
                "supported_styles": [style.value for style in provider.supported_styles] if provider else [],
                "supported_aspect_ratios": [ratio.value for ratio in provider.supported_aspect_ratios] if provider else [],
                "max_resolution": provider.max_resolution if provider else None
            }
        return status

