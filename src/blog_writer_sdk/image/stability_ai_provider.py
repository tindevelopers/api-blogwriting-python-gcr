"""
Stability AI Provider Implementation

This module provides an implementation of the BaseImageProvider interface
for Stability AI services, enabling integration with Stable Diffusion models.
"""

import os
import time
import logging
import asyncio
import aiohttp
import base64
from typing import Dict, List, Optional, Any
from io import BytesIO

from .base_provider import (
    BaseImageProvider,
    ImageProviderType,
    ImageProviderError,
    ImageProviderRateLimitError,
    ImageProviderAuthenticationError,
    ImageProviderQuotaExceededError,
    ImageProviderContentPolicyError
)
from ..models.image_models import (
    ImageGenerationRequest,
    ImageGenerationResponse,
    GeneratedImage,
    ImageVariationRequest,
    ImageUpscaleRequest,
    ImageEditRequest,
    ImageStyle,
    ImageAspectRatio,
    ImageQuality
)

logger = logging.getLogger(__name__)


class StabilityAIProvider(BaseImageProvider):
    """
    Stability AI provider implementation.
    
    This provider integrates with Stability AI's API, providing access
    to Stable Diffusion models for image generation.
    """
    
    def __init__(self, api_key: str, **kwargs):
        """
        Initialize Stability AI provider.
        
        Args:
            api_key: Stability AI API key
            **kwargs: Additional configuration including:
                - base_url: API base URL (default: https://api.stability.ai)
                - default_model: Default model to use
                - timeout: Request timeout in seconds
        """
        super().__init__(api_key, **kwargs)
        
        self.base_url = kwargs.get("base_url", "https://api.stability.ai")
        self.default_model = kwargs.get("default_model", "stable-diffusion-xl-1024-v1-0")
        self.timeout = kwargs.get("timeout", 120)
        self._session = None
    
    @property
    def provider_type(self) -> ImageProviderType:
        """Return the provider type."""
        return ImageProviderType.STABILITY_AI
    
    @property
    def supported_styles(self) -> List[ImageStyle]:
        """Return list of supported image styles."""
        return [
            ImageStyle.PHOTOGRAPHIC,
            ImageStyle.DIGITAL_ART,
            ImageStyle.PAINTING,
            ImageStyle.SKETCH,
            ImageStyle.CARTOON,
            ImageStyle.ANIME,
            ImageStyle.REALISTIC,
            ImageStyle.ABSTRACT,
            ImageStyle.MINIMALIST,
            ImageStyle.VINTAGE,
            ImageStyle.CYBERPUNK,
            ImageStyle.FANTASY,
            ImageStyle.SCI_FI,
            ImageStyle.WATERCOLOR,
            ImageStyle.OIL_PAINTING
        ]
    
    @property
    def supported_aspect_ratios(self) -> List[ImageAspectRatio]:
        """Return list of supported aspect ratios."""
        return [
            ImageAspectRatio.SQUARE,
            ImageAspectRatio.PORTRAIT,
            ImageAspectRatio.LANDSCAPE,
            ImageAspectRatio.WIDE,
            ImageAspectRatio.ULTRA_WIDE,
            ImageAspectRatio.TALL,
            ImageAspectRatio.CUSTOM
        ]
    
    @property
    def max_resolution(self) -> str:
        """Return maximum supported resolution."""
        return "2048x2048"
    
    @property
    def default_model(self) -> str:
        """Return the default model for this provider."""
        return self.default_model
    
    async def initialize(self) -> None:
        """Initialize the Stability AI client."""
        try:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout),
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Accept": "application/json",
                    "User-Agent": "BlogWriterSDK/1.0.0"
                }
            )
            logger.info(f"Stability AI client initialized with base URL: {self.base_url}")
        except Exception as e:
            logger.error(f"Failed to initialize Stability AI client: {e}")
            raise ImageProviderError(f"Failed to initialize client: {e}", self.provider_type.value)
    
    async def generate_image(
        self, 
        request: ImageGenerationRequest
    ) -> ImageGenerationResponse:
        """
        Generate an image using Stability AI.
        
        Args:
            request: Image generation request
            
        Returns:
            Image generation response with generated images
        """
        if not self._session:
            await self.initialize()
        
        start_time = time.time()
        
        try:
            # Validate request
            self._validate_request(request)
            
            # Calculate dimensions
            width, height = self._calculate_dimensions(
                request.aspect_ratio, 
                request.width, 
                request.height
            )
            
            # Prepare request payload
            payload = self._prepare_generation_payload(request, width, height)
            
            # Make API call
            async with self._session.post(
                f"{self.base_url}/v1/generation/{self.default_model}/text-to-image",
                json=payload
            ) as response:
                if response.status == 401:
                    raise ImageProviderAuthenticationError(
                        "Invalid API key", 
                        self.provider_type.value
                    )
                elif response.status == 429:
                    raise ImageProviderRateLimitError(
                        "Rate limit exceeded", 
                        self.provider_type.value
                    )
                elif response.status == 402:
                    raise ImageProviderQuotaExceededError(
                        "Insufficient credits", 
                        self.provider_type.value
                    )
                elif response.status == 400:
                    error_data = await response.json()
                    if "content_policy" in str(error_data).lower():
                        raise ImageProviderContentPolicyError(
                            "Content violates policy", 
                            self.provider_type.value
                        )
                    else:
                        raise ImageProviderError(
                            f"Bad request: {error_data}", 
                            self.provider_type.value
                        )
                elif response.status != 200:
                    error_data = await response.text()
                    raise ImageProviderError(
                        f"API error {response.status}: {error_data}", 
                        self.provider_type.value
                    )
                
                result = await response.json()
            
            generation_time = time.time() - start_time
            
            # Process results
            images = []
            for artifact in result.get("artifacts", []):
                if artifact.get("finishReason") == "SUCCESS":
                    image_data = base64.b64decode(artifact["base64"])
                    generated_image = self._create_generated_image(
                        image_data=image_data,
                        width=width,
                        height=height,
                        seed=artifact.get("seed"),
                        steps=payload.get("steps"),
                        guidance_scale=payload.get("cfg_scale"),
                        model=self.default_model
                    )
                    images.append(generated_image)
            
            if not images:
                raise ImageProviderError(
                    "No images generated successfully", 
                    self.provider_type.value
                )
            
            # Calculate cost
            cost = self.estimate_cost(request)
            
            return ImageGenerationResponse(
                success=True,
                images=images,
                generation_time_seconds=generation_time,
                provider=self.provider_type,
                model=self.default_model,
                cost=cost,
                request_id=result.get("id"),
                prompt_used=request.prompt
            )
            
        except (ImageProviderError, ImageProviderRateLimitError, 
                ImageProviderAuthenticationError, ImageProviderQuotaExceededError,
                ImageProviderContentPolicyError):
            raise
        except Exception as e:
            generation_time = time.time() - start_time
            raise ImageProviderError(
                f"Unexpected error: {str(e)}", 
                self.provider_type.value
            )
    
    async def generate_variations(
        self, 
        request: ImageVariationRequest
    ) -> ImageGenerationResponse:
        """
        Generate variations of an existing image using Stability AI.
        
        Args:
            request: Image variation request
            
        Returns:
            Image generation response with variations
        """
        if not self._session:
            await self.initialize()
        
        start_time = time.time()
        
        try:
            # Download source image
            async with self._session.get(str(request.source_image_url)) as response:
                if response.status != 200:
                    raise ImageProviderError(
                        f"Failed to download source image: {response.status}", 
                        self.provider_type.value
                    )
                source_image_data = await response.read()
            
            # Prepare request payload
            payload = {
                "init_image": base64.b64encode(source_image_data).decode('utf-8'),
                "init_image_mode": "IMAGE_STRENGTH",
                "image_strength": request.variation_strength,
                "text_prompts": [
                    {
                        "text": f"variation of the image, {request.style.value if request.style else ''}",
                        "weight": 1.0
                    }
                ],
                "cfg_scale": 7.0,
                "steps": 30,
                "samples": request.num_variations,
                "seed": request.seed or 0
            }
            
            # Make API call
            async with self._session.post(
                f"{self.base_url}/v1/generation/{self.default_model}/image-to-image",
                json=payload
            ) as response:
                if response.status != 200:
                    error_data = await response.text()
                    raise ImageProviderError(
                        f"API error {response.status}: {error_data}", 
                        self.provider_type.value
                    )
                
                result = await response.json()
            
            generation_time = time.time() - start_time
            
            # Process results
            images = []
            for artifact in result.get("artifacts", []):
                if artifact.get("finishReason") == "SUCCESS":
                    image_data = base64.b64decode(artifact["base64"])
                    generated_image = self._create_generated_image(
                        image_data=image_data,
                        width=1024,  # Default size for variations
                        height=1024,
                        seed=artifact.get("seed"),
                        steps=payload.get("steps"),
                        guidance_scale=payload.get("cfg_scale"),
                        model=self.default_model
                    )
                    images.append(generated_image)
            
            return ImageGenerationResponse(
                success=True,
                images=images,
                generation_time_seconds=generation_time,
                provider=self.provider_type,
                model=self.default_model,
                request_id=result.get("id"),
                prompt_used=f"variation of image with {request.variation_strength} strength"
            )
            
        except Exception as e:
            generation_time = time.time() - start_time
            raise ImageProviderError(
                f"Failed to generate variations: {str(e)}", 
                self.provider_type.value
            )
    
    async def upscale_image(
        self, 
        request: ImageUpscaleRequest
    ) -> ImageGenerationResponse:
        """
        Upscale an existing image using Stability AI.
        
        Args:
            request: Image upscale request
            
        Returns:
            Image generation response with upscaled image
        """
        if not self._session:
            await self.initialize()
        
        start_time = time.time()
        
        try:
            # Download source image
            async with self._session.get(str(request.source_image_url)) as response:
                if response.status != 200:
                    raise ImageProviderError(
                        f"Failed to download source image: {response.status}", 
                        self.provider_type.value
                    )
                source_image_data = await response.read()
            
            # Prepare request payload
            payload = {
                "image": base64.b64encode(source_image_data).decode('utf-8'),
                "width": int(1024 * request.scale_factor),  # Assuming base size of 1024
                "height": int(1024 * request.scale_factor)
            }
            
            # Make API call
            async with self._session.post(
                f"{self.base_url}/v1/image-to-image/upscale",
                json=payload
            ) as response:
                if response.status != 200:
                    error_data = await response.text()
                    raise ImageProviderError(
                        f"API error {response.status}: {error_data}", 
                        self.provider_type.value
                    )
                
                result = await response.json()
            
            generation_time = time.time() - start_time
            
            # Process results
            images = []
            for artifact in result.get("artifacts", []):
                if artifact.get("finishReason") == "SUCCESS":
                    image_data = base64.b64decode(artifact["base64"])
                    generated_image = self._create_generated_image(
                        image_data=image_data,
                        width=int(1024 * request.scale_factor),
                        height=int(1024 * request.scale_factor),
                        model="upscaler"
                    )
                    images.append(generated_image)
            
            return ImageGenerationResponse(
                success=True,
                images=images,
                generation_time_seconds=generation_time,
                provider=self.provider_type,
                model="upscaler",
                request_id=result.get("id"),
                prompt_used=f"upscale by {request.scale_factor}x"
            )
            
        except Exception as e:
            generation_time = time.time() - start_time
            raise ImageProviderError(
                f"Failed to upscale image: {str(e)}", 
                self.provider_type.value
            )
    
    async def edit_image(
        self, 
        request: ImageEditRequest
    ) -> ImageGenerationResponse:
        """
        Edit an existing image using Stability AI.
        
        Args:
            request: Image edit request
            
        Returns:
            Image generation response with edited image
        """
        if not self._session:
            await self.initialize()
        
        start_time = time.time()
        
        try:
            # Download source image
            async with self._session.get(str(request.source_image_url)) as response:
                if response.status != 200:
                    raise ImageProviderError(
                        f"Failed to download source image: {response.status}", 
                        self.provider_type.value
                    )
                source_image_data = await response.read()
            
            # Download mask image if provided
            mask_image_data = None
            if request.mask_image_url:
                async with self._session.get(str(request.mask_image_url)) as response:
                    if response.status != 200:
                        raise ImageProviderError(
                            f"Failed to download mask image: {response.status}", 
                            self.provider_type.value
                        )
                    mask_image_data = await response.read()
            
            # Prepare request payload
            payload = {
                "init_image": base64.b64encode(source_image_data).decode('utf-8'),
                "text_prompts": [
                    {
                        "text": request.prompt,
                        "weight": 1.0
                    }
                ],
                "cfg_scale": request.guidance_scale or 7.0,
                "steps": 30,
                "image_strength": request.strength
            }
            
            if mask_image_data:
                payload["mask_image"] = base64.b64encode(mask_image_data).decode('utf-8')
                payload["mask_source"] = "MASK_IMAGE_WHITE"
            
            # Make API call
            async with self._session.post(
                f"{self.base_url}/v1/generation/{self.default_model}/image-to-image",
                json=payload
            ) as response:
                if response.status != 200:
                    error_data = await response.text()
                    raise ImageProviderError(
                        f"API error {response.status}: {error_data}", 
                        self.provider_type.value
                    )
                
                result = await response.json()
            
            generation_time = time.time() - start_time
            
            # Process results
            images = []
            for artifact in result.get("artifacts", []):
                if artifact.get("finishReason") == "SUCCESS":
                    image_data = base64.b64decode(artifact["base64"])
                    generated_image = self._create_generated_image(
                        image_data=image_data,
                        width=1024,  # Default size
                        height=1024,
                        seed=artifact.get("seed"),
                        steps=payload.get("steps"),
                        guidance_scale=payload.get("cfg_scale"),
                        model=self.default_model
                    )
                    images.append(generated_image)
            
            return ImageGenerationResponse(
                success=True,
                images=images,
                generation_time_seconds=generation_time,
                provider=self.provider_type,
                model=self.default_model,
                request_id=result.get("id"),
                prompt_used=request.prompt
            )
            
        except Exception as e:
            generation_time = time.time() - start_time
            raise ImageProviderError(
                f"Failed to edit image: {str(e)}", 
                self.provider_type.value
            )
    
    async def validate_api_key(self) -> bool:
        """
        Validate the Stability AI API key.
        
        Returns:
            True if API key is valid, False otherwise
        """
        try:
            if not self._session:
                await self.initialize()
            
            # Make a simple API call to validate the key
            async with self._session.get(f"{self.base_url}/v1/user/account") as response:
                return response.status == 200
                
        except Exception as e:
            logger.error(f"API key validation failed for Stability AI: {e}")
            return False
    
    def estimate_cost(self, request: ImageGenerationRequest) -> float:
        """
        Estimate the cost for image generation.
        
        Args:
            request: Image generation request
            
        Returns:
            Estimated cost in USD
        """
        # Stability AI pricing (as of 2024, may need updates)
        # These are approximate costs per image
        base_cost = 0.004  # Base cost per image
        
        # Adjust cost based on quality and size
        quality_multiplier = {
            ImageQuality.DRAFT: 0.5,
            ImageQuality.STANDARD: 1.0,
            ImageQuality.HIGH: 1.5,
            ImageQuality.ULTRA: 2.0
        }
        
        multiplier = quality_multiplier.get(request.quality, 1.0)
        
        # Adjust for image size (larger images cost more)
        width, height = self._calculate_dimensions(request.aspect_ratio, request.width, request.height)
        size_factor = (width * height) / (1024 * 1024)  # Normalize to 1024x1024
        
        return base_cost * multiplier * size_factor
    
    def get_rate_limits(self) -> Dict[str, Any]:
        """
        Get rate limit information for the provider.
        
        Returns:
            Dictionary with rate limit information
        """
        return {
            "requests_per_minute": 10,
            "requests_per_hour": 100,
            "requests_per_day": 1000,
            "concurrent_requests": 3,
            "max_image_size": "2048x2048"
        }
    
    def _prepare_generation_payload(
        self, 
        request: ImageGenerationRequest, 
        width: int, 
        height: int
    ) -> Dict[str, Any]:
        """Prepare the API payload for image generation."""
        # Build prompt with style
        prompt = request.prompt
        if request.style:
            prompt = f"{prompt}, {request.style.value} style"
        
        # Add negative prompt
        negative_prompt = request.negative_prompt or ""
        
        payload = {
            "text_prompts": [
                {
                    "text": prompt,
                    "weight": 1.0
                }
            ],
            "cfg_scale": request.guidance_scale or 7.0,
            "steps": request.steps or 30,
            "samples": 1,
            "width": width,
            "height": height,
            "seed": request.seed or 0
        }
        
        if negative_prompt:
            payload["text_prompts"].append({
                "text": negative_prompt,
                "weight": -1.0
            })
        
        # Add style preset if available
        if request.style:
            style_presets = {
                ImageStyle.PHOTOGRAPHIC: "photographic",
                ImageStyle.DIGITAL_ART: "digital-art",
                ImageStyle.PAINTING: "enhance",
                ImageStyle.ANIME: "anime",
                ImageStyle.CARTOON: "comic-book",
                ImageStyle.FANTASY: "fantasy-art",
                ImageStyle.SCI_FI: "neon-punk"
            }
            
            if request.style in style_presets:
                payload["style_preset"] = style_presets[request.style]
        
        return payload
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._session:
            await self._session.close()

