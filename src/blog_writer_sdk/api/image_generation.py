"""
Image Generation API Endpoints

This module provides REST API endpoints for image generation,
including text-to-image, image variations, upscaling, and editing.
"""

import os
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import ValidationError

from ..image.base_provider import ImageProviderManager
from ..image.stability_ai_provider import StabilityAIProvider
from ..models.image_models import (
    ImageProviderType,
    ImageGenerationRequest,
    ImageGenerationResponse,
    ImageVariationRequest,
    ImageUpscaleRequest,
    ImageEditRequest,
    ImageProviderConfig,
    ImageProviderStatus,
    ImageGenerationJob
)

logger = logging.getLogger(__name__)

# Create router for image generation endpoints
router = APIRouter(prefix="/api/v1/images", tags=["Image Generation"])

# Global image provider manager instance
image_provider_manager = ImageProviderManager()

# In-memory storage for image generation jobs (in production, use a database)
image_jobs: Dict[str, ImageGenerationJob] = {}


def get_provider_class(provider_type: ImageProviderType):
    """Get the provider class for a given provider type."""
    provider_classes = {
        ImageProviderType.STABILITY_AI: StabilityAIProvider,
        # Add more providers here as they are implemented
    }
    
    if provider_type not in provider_classes:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported image provider type: {provider_type}"
        )
    
    return provider_classes[provider_type]


@router.post("/generate", response_model=ImageGenerationResponse)
async def generate_image(
    request: ImageGenerationRequest,
    background_tasks: BackgroundTasks
):
    """
    Generate an image from a text prompt.
    
    This endpoint allows users to generate images using various AI providers
    with customizable styles, aspect ratios, and quality settings.
    """
    try:
        # Check if provider is available
        if not image_provider_manager.providers:
            raise HTTPException(
                status_code=503,
                detail="No image providers configured. Please configure at least one provider."
            )
        
        # Generate image using the provider manager
        response = await image_provider_manager.generate_image(request)
        
        # Log generation for monitoring
        logger.info(f"Image generated successfully using {response.provider}: {len(response.images)} images")
        
        return response
        
    except Exception as e:
        logger.error(f"Image generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Image generation failed: {str(e)}"
        )


@router.post("/variations", response_model=ImageGenerationResponse)
async def generate_image_variations(
    request: ImageVariationRequest,
    background_tasks: BackgroundTasks
):
    """
    Generate variations of an existing image.
    
    This endpoint creates multiple variations of a source image with
    customizable variation strength and style preferences.
    """
    try:
        # Find the appropriate provider
        provider_name = None
        for name, provider in image_provider_manager.providers.items():
            if provider.provider_type == request.provider:
                provider_name = name
                break
        
        if not provider_name:
            raise HTTPException(
                status_code=404,
                detail=f"Provider {request.provider} not found or not configured"
            )
        
        provider = image_provider_manager.providers[provider_name]
        response = await provider.generate_variations(request)
        
        logger.info(f"Image variations generated successfully: {len(response.images)} variations")
        
        return response
        
    except Exception as e:
        logger.error(f"Image variation generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Image variation generation failed: {str(e)}"
        )


@router.post("/upscale", response_model=ImageGenerationResponse)
async def upscale_image(
    request: ImageUpscaleRequest,
    background_tasks: BackgroundTasks
):
    """
    Upscale an existing image to higher resolution.
    
    This endpoint enhances the resolution of an image while preserving
    quality and details.
    """
    try:
        # Find the appropriate provider
        provider_name = None
        for name, provider in image_provider_manager.providers.items():
            if provider.provider_type == request.provider:
                provider_name = name
                break
        
        if not provider_name:
            raise HTTPException(
                status_code=404,
                detail=f"Provider {request.provider} not found or not configured"
            )
        
        provider = image_provider_manager.providers[provider_name]
        response = await provider.upscale_image(request)
        
        logger.info(f"Image upscaled successfully: {len(response.images)} images")
        
        return response
        
    except Exception as e:
        logger.error(f"Image upscaling failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Image upscaling failed: {str(e)}"
        )


@router.post("/edit", response_model=ImageGenerationResponse)
async def edit_image(
    request: ImageEditRequest,
    background_tasks: BackgroundTasks
):
    """
    Edit an existing image using inpainting or outpainting.
    
    This endpoint allows users to modify specific parts of an image
    or extend the image beyond its original boundaries.
    """
    try:
        # Find the appropriate provider
        provider_name = None
        for name, provider in image_provider_manager.providers.items():
            if provider.provider_type == request.provider:
                provider_name = name
                break
        
        if not provider_name:
            raise HTTPException(
                status_code=404,
                detail=f"Provider {request.provider} not found or not configured"
            )
        
        provider = image_provider_manager.providers[provider_name]
        response = await provider.edit_image(request)
        
        logger.info(f"Image edited successfully: {len(response.images)} images")
        
        return response
        
    except Exception as e:
        logger.error(f"Image editing failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Image editing failed: {str(e)}"
        )


@router.post("/jobs", response_model=Dict[str, str])
async def create_image_generation_job(
    request: ImageGenerationRequest,
    background_tasks: BackgroundTasks
):
    """
    Create an asynchronous image generation job.
    
    This endpoint creates a background job for image generation,
    useful for long-running or batch operations.
    """
    try:
        import uuid
        job_id = str(uuid.uuid4())
        
        # Create job
        job = ImageGenerationJob(
            job_id=job_id,
            status="queued",
            request=request
        )
        
        image_jobs[job_id] = job
        
        # Start background task
        background_tasks.add_task(process_image_generation_job, job_id)
        
        logger.info(f"Image generation job created: {job_id}")
        
        return {"job_id": job_id, "status": "queued"}
        
    except Exception as e:
        logger.error(f"Failed to create image generation job: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create job: {str(e)}"
        )


@router.get("/jobs/{job_id}", response_model=ImageGenerationJob)
async def get_image_generation_job(job_id: str):
    """
    Get the status and result of an image generation job.
    
    This endpoint allows users to check the progress and retrieve
    results of asynchronous image generation jobs.
    """
    try:
        if job_id not in image_jobs:
            raise HTTPException(
                status_code=404,
                detail=f"Job {job_id} not found"
            )
        
        return image_jobs[job_id]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get image generation job {job_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get job: {str(e)}"
        )


@router.get("/jobs", response_model=List[ImageGenerationJob])
async def list_image_generation_jobs(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """
    List image generation jobs with optional filtering.
    
    This endpoint provides a list of image generation jobs with
    optional filtering by status and pagination support.
    """
    try:
        jobs = list(image_jobs.values())
        
        # Filter by status if provided
        if status:
            jobs = [job for job in jobs if job.status == status]
        
        # Apply pagination
        jobs = jobs[offset:offset + limit]
        
        return jobs
        
    except Exception as e:
        logger.error(f"Failed to list image generation jobs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list jobs: {str(e)}"
        )


@router.delete("/jobs/{job_id}")
async def cancel_image_generation_job(job_id: str):
    """
    Cancel an image generation job.
    
    This endpoint allows users to cancel pending or running
    image generation jobs.
    """
    try:
        if job_id not in image_jobs:
            raise HTTPException(
                status_code=404,
                detail=f"Job {job_id} not found"
            )
        
        job = image_jobs[job_id]
        if job.status in ["completed", "failed", "cancelled"]:
            raise HTTPException(
                status_code=400,
                detail=f"Job {job_id} cannot be cancelled (status: {job.status})"
            )
        
        job.status = "cancelled"
        job.completed_at = datetime.utcnow()
        
        logger.info(f"Image generation job cancelled: {job_id}")
        
        return {"message": f"Job {job_id} cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel image generation job {job_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel job: {str(e)}"
        )


@router.get("/providers", response_model=Dict[str, ImageProviderStatus])
async def list_image_providers():
    """
    List all configured image generation providers.
    
    This endpoint provides information about all configured
    image generation providers and their current status.
    """
    try:
        status_info = image_provider_manager.get_provider_status()
        
        # Convert to ImageProviderStatus objects
        providers = {}
        for name, info in status_info.items():
            providers[name] = ImageProviderStatus(
                provider_type=info["provider_type"],
                status="configured" if info["available"] else "not_configured",
                enabled=info["enabled"],
                priority=info["priority"],
                supported_styles=info.get("supported_styles", []),
                supported_aspect_ratios=info.get("supported_aspect_ratios", []),
                max_resolution=info.get("max_resolution")
            )
        
        return providers
        
    except Exception as e:
        logger.error(f"Failed to list image providers: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list providers: {str(e)}"
        )


@router.get("/providers/health", response_model=Dict[str, Dict[str, Any]])
async def health_check_image_providers():
    """
    Perform health checks on all image generation providers.
    
    This endpoint provides real-time health status of all
    image generation providers.
    """
    try:
        health_results = await image_provider_manager.health_check_all()
        return health_results
        
    except Exception as e:
        logger.error(f"Failed to perform health checks: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to perform health checks: {str(e)}"
        )


@router.post("/providers/configure")
async def configure_image_provider(
    provider_type: ImageProviderType,
    api_key: str,
    enabled: bool = True,
    priority: int = 1,
    default_model: Optional[str] = None,
    background_tasks: BackgroundTasks = None
):
    """
    Configure an image generation provider.
    
    This endpoint allows users to add or update image generation
    provider configurations with API keys and settings.
    """
    try:
        # Create provider instance
        provider_class = get_provider_class(provider_type)
        provider = provider_class(api_key=api_key)
        
        # Initialize provider
        await provider.initialize()
        
        # Validate API key
        is_valid = await provider.validate_api_key()
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail="Invalid API key for the specified provider"
            )
        
        # Create provider config
        provider_config = ImageProviderConfig(
            provider_type=provider_type,
            api_key=api_key,
            enabled=enabled,
            priority=priority,
            default_model=default_model
        )
        
        # Add to manager
        provider_name = f"{provider_type.value}_{int(time.time())}"
        image_provider_manager.add_provider(provider_name, provider, provider_config)
        
        logger.info(f"Image provider configured successfully: {provider_type}")
        
        return {
            "message": f"Provider {provider_type} configured successfully",
            "provider_name": provider_name,
            "status": "configured"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to configure image provider {provider_type}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to configure provider: {str(e)}"
        )


@router.delete("/providers/{provider_name}")
async def remove_image_provider(provider_name: str):
    """
    Remove a configured image generation provider.
    
    This endpoint allows users to remove image generation
    provider configurations that are no longer needed.
    """
    try:
        if provider_name not in image_provider_manager.providers:
            raise HTTPException(
                status_code=404,
                detail=f"Provider {provider_name} not found"
            )
        
        # Remove from manager
        image_provider_manager.remove_provider(provider_name)
        
        logger.info(f"Image provider removed successfully: {provider_name}")
        
        return {"message": f"Provider {provider_name} removed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove image provider {provider_name}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to remove provider: {str(e)}"
        )


async def process_image_generation_job(job_id: str):
    """Background task to process image generation jobs."""
    try:
        if job_id not in image_jobs:
            return
        
        job = image_jobs[job_id]
        job.status = "processing"
        job.started_at = datetime.utcnow()
        
        # Generate image
        response = await image_provider_manager.generate_image(job.request)
        
        # Update job with result
        job.status = "completed"
        job.completed_at = datetime.utcnow()
        job.result = response
        job.progress_percentage = 100.0
        
        logger.info(f"Image generation job completed: {job_id}")
        
    except Exception as e:
        if job_id in image_jobs:
            job = image_jobs[job_id]
            job.status = "failed"
            job.completed_at = datetime.utcnow()
            job.error_message = str(e)
        
        logger.error(f"Image generation job failed {job_id}: {e}")


# Initialize with existing environment variables
async def initialize_image_providers_from_env():
    """Initialize image providers from environment variables."""
    try:
        # Stability AI
        stability_key = os.getenv("STABILITY_AI_API_KEY")
        if stability_key:
            await configure_image_provider(
                provider_type=ImageProviderType.STABILITY_AI,
                api_key=stability_key,
                enabled=True,
                priority=1,
                default_model=os.getenv("STABILITY_AI_DEFAULT_MODEL", "stable-diffusion-xl-1024-v1-0")
            )
        
        logger.info("Image providers initialized from environment variables")
        
    except Exception as e:
        logger.error(f"Failed to initialize image providers from environment: {e}")


# Export the router and manager for use in main.py
__all__ = ["router", "image_provider_manager", "initialize_image_providers_from_env"]

