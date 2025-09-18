"""
Image Generation Models

This module contains Pydantic models for image generation requests,
responses, and provider configurations.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, field_validator, HttpUrl
import base64


class ImageProviderType(str, Enum):
    """Supported image generation provider types."""
    STABILITY_AI = "stability_ai"
    OPENAI_DALL_E = "openai_dall_e"
    MIDJOURNEY = "midjourney"
    REPLICATE = "replicate"
    HUGGINGFACE = "huggingface"


class ImageStyle(str, Enum):
    """Available image styles for generation."""
    PHOTOGRAPHIC = "photographic"
    DIGITAL_ART = "digital_art"
    PAINTING = "painting"
    SKETCH = "sketch"
    CARTOON = "cartoon"
    ANIME = "anime"
    REALISTIC = "realistic"
    ABSTRACT = "abstract"
    MINIMALIST = "minimalist"
    VINTAGE = "vintage"
    CYBERPUNK = "cyberpunk"
    FANTASY = "fantasy"
    SCI_FI = "sci_fi"
    WATERCOLOR = "watercolor"
    OIL_PAINTING = "oil_painting"


class ImageAspectRatio(str, Enum):
    """Available aspect ratios for image generation."""
    SQUARE = "1:1"
    PORTRAIT = "3:4"
    LANDSCAPE = "4:3"
    WIDE = "16:9"
    ULTRA_WIDE = "21:9"
    TALL = "2:3"
    CUSTOM = "custom"


class ImageQuality(str, Enum):
    """Image quality levels."""
    DRAFT = "draft"
    STANDARD = "standard"
    HIGH = "high"
    ULTRA = "ultra"


class ImageGenerationRequest(BaseModel):
    """Request model for image generation."""
    
    prompt: str = Field(..., min_length=3, max_length=1000, description="Text prompt for image generation")
    provider: ImageProviderType = Field(default=ImageProviderType.STABILITY_AI, description="Image generation provider")
    style: Optional[ImageStyle] = Field(None, description="Image style preference")
    aspect_ratio: ImageAspectRatio = Field(default=ImageAspectRatio.SQUARE, description="Desired aspect ratio")
    quality: ImageQuality = Field(default=ImageQuality.STANDARD, description="Image quality level")
    
    # Advanced options
    negative_prompt: Optional[str] = Field(None, max_length=500, description="What to avoid in the image")
    seed: Optional[int] = Field(None, ge=0, le=4294967295, description="Random seed for reproducible results")
    steps: Optional[int] = Field(None, ge=10, le=150, description="Number of generation steps")
    guidance_scale: Optional[float] = Field(None, ge=1.0, le=20.0, description="How closely to follow the prompt")
    
    # Image dimensions (for custom aspect ratio)
    width: Optional[int] = Field(None, ge=64, le=2048, description="Image width in pixels")
    height: Optional[int] = Field(None, ge=64, le=2048, description="Image height in pixels")
    
    # Reference images
    reference_image_url: Optional[HttpUrl] = Field(None, description="Reference image URL for style transfer")
    mask_image_url: Optional[HttpUrl] = Field(None, description="Mask image URL for inpainting")
    
    # Metadata
    tags: List[str] = Field(default_factory=list, max_length=10, description="Tags for categorization")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    
    @field_validator('prompt')
    @classmethod
    def validate_prompt(cls, v):
        """Validate and clean the prompt."""
        return v.strip()
    
    @field_validator('negative_prompt')
    @classmethod
    def validate_negative_prompt(cls, v):
        """Validate negative prompt."""
        if v:
            return v.strip()
        return v
    
    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v):
        """Validate and clean tags."""
        return [tag.strip().lower() for tag in v if tag.strip()]


class ImageGenerationResponse(BaseModel):
    """Response model for image generation."""
    
    success: bool = Field(..., description="Whether generation was successful")
    images: List['GeneratedImage'] = Field(default_factory=list, description="Generated images")
    
    # Generation metadata
    generation_time_seconds: float = Field(default=0.0, ge=0, description="Time taken to generate")
    provider: ImageProviderType = Field(..., description="Provider used for generation")
    model: Optional[str] = Field(None, description="Model used for generation")
    
    # Cost and usage
    cost: Optional[float] = Field(None, ge=0, description="Cost of generation in USD")
    credits_used: Optional[int] = Field(None, ge=0, description="Credits consumed")
    
    # Request information
    request_id: Optional[str] = Field(None, description="Unique request identifier")
    prompt_used: str = Field(..., description="Actual prompt used for generation")
    
    # Error handling
    error_message: Optional[str] = Field(None, description="Error message if generation failed")
    error_code: Optional[str] = Field(None, description="Error code for debugging")
    
    # Provider-specific data
    provider_metadata: Optional[Dict[str, Any]] = Field(None, description="Provider-specific information")


class GeneratedImage(BaseModel):
    """Model for a generated image."""
    
    image_id: str = Field(..., description="Unique identifier for the image")
    image_url: Optional[HttpUrl] = Field(None, description="URL to access the generated image")
    image_data: Optional[str] = Field(None, description="Base64 encoded image data")
    
    # Image properties
    width: int = Field(..., ge=1, description="Image width in pixels")
    height: int = Field(..., ge=1, description="Image height in pixels")
    format: str = Field(default="png", description="Image format")
    size_bytes: Optional[int] = Field(None, ge=0, description="Image file size in bytes")
    
    # Generation details
    seed: Optional[int] = Field(None, description="Seed used for generation")
    steps: Optional[int] = Field(None, description="Steps used for generation")
    guidance_scale: Optional[float] = Field(None, description="Guidance scale used")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Generation timestamp")
    expires_at: Optional[datetime] = Field(None, description="When the image URL expires")
    
    # Quality metrics
    quality_score: Optional[float] = Field(None, ge=0, le=1, description="AI-assessed quality score")
    safety_score: Optional[float] = Field(None, ge=0, le=1, description="Content safety score")
    
    # Provider information
    provider: ImageProviderType = Field(..., description="Provider that generated the image")
    model: Optional[str] = Field(None, description="Model used for generation")
    
    # Additional data
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional image metadata")


class ImageProviderConfig(BaseModel):
    """Configuration for image generation providers."""
    
    provider_type: ImageProviderType = Field(..., description="Type of image provider")
    api_key: str = Field(..., description="API key for the provider")
    enabled: bool = Field(default=True, description="Whether provider is enabled")
    priority: int = Field(default=1, ge=1, le=10, description="Priority (1=highest, 10=lowest)")
    
    # Provider-specific settings
    default_model: Optional[str] = Field(None, description="Default model to use")
    max_concurrent_requests: int = Field(default=5, ge=1, le=50, description="Max concurrent requests")
    timeout_seconds: int = Field(default=120, ge=30, le=600, description="Request timeout")
    
    # Rate limiting
    requests_per_minute: Optional[int] = Field(None, ge=1, description="Rate limit per minute")
    requests_per_day: Optional[int] = Field(None, ge=1, description="Rate limit per day")
    
    # Cost settings
    cost_per_image: Optional[float] = Field(None, ge=0, description="Cost per image in USD")
    credits_per_image: Optional[int] = Field(None, ge=0, description="Credits per image")
    
    # Custom configuration
    custom_config: Optional[Dict[str, Any]] = Field(None, description="Provider-specific settings")


class ImageProviderStatus(BaseModel):
    """Status information for an image provider."""
    
    provider_type: ImageProviderType = Field(..., description="Provider type")
    status: str = Field(..., description="Current status")
    enabled: bool = Field(..., description="Whether provider is enabled")
    priority: int = Field(..., description="Provider priority")
    
    # Health information
    last_health_check: Optional[datetime] = Field(None, description="Last health check time")
    api_key_valid: bool = Field(default=False, description="Whether API key is valid")
    rate_limit_ok: bool = Field(default=True, description="Rate limit status")
    quota_available: bool = Field(default=True, description="Quota availability")
    
    # Usage statistics
    total_requests: int = Field(default=0, description="Total requests made")
    successful_requests: int = Field(default=0, description="Successful requests")
    failed_requests: int = Field(default=0, description="Failed requests")
    total_cost: float = Field(default=0.0, description="Total cost incurred")
    
    # Error information
    last_error: Optional[str] = Field(None, description="Last error message")
    consecutive_failures: int = Field(default=0, description="Consecutive failure count")
    
    # Capabilities
    supported_styles: List[ImageStyle] = Field(default_factory=list, description="Supported styles")
    supported_aspect_ratios: List[ImageAspectRatio] = Field(default_factory=list, description="Supported aspect ratios")
    max_resolution: Optional[str] = Field(None, description="Maximum supported resolution")


class ImageGenerationJob(BaseModel):
    """Model for asynchronous image generation jobs."""
    
    job_id: str = Field(..., description="Unique job identifier")
    status: str = Field(..., description="Job status")
    request: ImageGenerationRequest = Field(..., description="Original generation request")
    
    # Progress tracking
    progress_percentage: float = Field(default=0.0, ge=0, le=100, description="Generation progress")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")
    
    # Results
    result: Optional[ImageGenerationResponse] = Field(None, description="Generation result")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Job creation time")
    started_at: Optional[datetime] = Field(None, description="When generation started")
    completed_at: Optional[datetime] = Field(None, description="When generation completed")
    
    # Error handling
    error_message: Optional[str] = Field(None, description="Error message if failed")
    retry_count: int = Field(default=0, ge=0, description="Number of retry attempts")


class ImageVariationRequest(BaseModel):
    """Request model for generating image variations."""
    
    source_image_url: HttpUrl = Field(..., description="URL of the source image")
    provider: ImageProviderType = Field(default=ImageProviderType.STABILITY_AI, description="Provider to use")
    variation_strength: float = Field(default=0.5, ge=0.0, le=1.0, description="How much to vary the image")
    num_variations: int = Field(default=4, ge=1, le=10, description="Number of variations to generate")
    
    # Additional options
    style: Optional[ImageStyle] = Field(None, description="Style to apply to variations")
    seed: Optional[int] = Field(None, description="Random seed for reproducible results")
    
    # Metadata
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")


class ImageUpscaleRequest(BaseModel):
    """Request model for image upscaling."""
    
    source_image_url: HttpUrl = Field(..., description="URL of the image to upscale")
    provider: ImageProviderType = Field(default=ImageProviderType.STABILITY_AI, description="Provider to use")
    scale_factor: float = Field(default=2.0, ge=1.0, le=4.0, description="Upscaling factor")
    quality: ImageQuality = Field(default=ImageQuality.HIGH, description="Upscaling quality")
    
    # Additional options
    preserve_details: bool = Field(default=True, description="Whether to preserve fine details")
    enhance_colors: bool = Field(default=False, description="Whether to enhance colors")
    
    # Metadata
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")


class ImageEditRequest(BaseModel):
    """Request model for image editing (inpainting/outpainting)."""
    
    source_image_url: HttpUrl = Field(..., description="URL of the source image")
    mask_image_url: Optional[HttpUrl] = Field(None, description="URL of the mask image")
    prompt: str = Field(..., description="Edit instruction prompt")
    provider: ImageProviderType = Field(default=ImageProviderType.STABILITY_AI, description="Provider to use")
    
    # Edit options
    edit_type: str = Field(default="inpaint", description="Type of edit (inpaint, outpaint, etc.)")
    strength: float = Field(default=0.8, ge=0.0, le=1.0, description="Edit strength")
    
    # Additional options
    seed: Optional[int] = Field(None, description="Random seed for reproducible results")
    guidance_scale: Optional[float] = Field(None, ge=1.0, le=20.0, description="Guidance scale")
    
    # Metadata
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")


# Update forward references
ImageGenerationResponse.model_rebuild()

