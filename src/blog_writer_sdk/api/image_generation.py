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
from ..models.image_job_models import (
    ImageJobStatus,
    ImageGenerationJobStatus,
    ImageJobStatusResponse,
    CreateImageJobResponse,
    BatchImageGenerationRequest,
    BatchImageGenerationResponse
)
from ..services.cloud_tasks_service import get_cloud_tasks_service

logger = logging.getLogger(__name__)

# Create router for image generation endpoints
router = APIRouter(prefix="/api/v1/images", tags=["Image Generation"])

# Global image provider manager instance
image_provider_manager = ImageProviderManager()

# In-memory storage for image generation jobs (in production, use a database)
image_jobs: Dict[str, ImageGenerationJob] = {}

# Cloud Tasks job storage (for async processing)
image_generation_jobs: Dict[str, ImageGenerationJobStatus] = {}


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


@router.get("/jobs/{job_id}", response_model=ImageJobStatusResponse)
async def get_image_generation_job(job_id: str):
    """
    Get the status and result of an image generation job.
    
    This endpoint allows users to check the progress and retrieve
    results of asynchronous image generation jobs (Cloud Tasks or BackgroundTasks).
    
    Checks both Cloud Tasks jobs and legacy BackgroundTasks jobs.
    """
    try:
        global image_generation_jobs, image_jobs
        
        # Check Cloud Tasks jobs first
        if job_id in image_generation_jobs:
            job = image_generation_jobs[job_id]
            
            # Calculate estimated time remaining
            estimated_remaining = None
            if job.status == ImageJobStatus.PROCESSING and job.started_at:
                elapsed = (datetime.utcnow() - job.started_at).total_seconds()
                total_estimate = 5 if job.is_draft else 15
                estimated_remaining = max(0, int(total_estimate - elapsed))
            
            return ImageJobStatusResponse(
                job_id=job.job_id,
                status=job.status,
                progress_percentage=job.progress_percentage,
                current_stage=job.current_stage,
                created_at=job.created_at,
                started_at=job.started_at,
                completed_at=job.completed_at,
                result=job.result,
                error_message=job.error_message,
                estimated_time_remaining=estimated_remaining,
                is_draft=job.is_draft,
                final_job_id=job.final_job_id
            )
        
        # Check legacy BackgroundTasks jobs
        if job_id in image_jobs:
            legacy_job = image_jobs[job_id]
            # Convert legacy job to new format
            status = ImageJobStatus.PROCESSING if legacy_job.status == "processing" else \
                     ImageJobStatus.COMPLETED if legacy_job.status == "completed" else \
                     ImageJobStatus.FAILED if legacy_job.status == "failed" else \
                     ImageJobStatus.QUEUED if legacy_job.status == "queued" else \
                     ImageJobStatus.PENDING
            
            return ImageJobStatusResponse(
                job_id=legacy_job.job_id,
                status=status,
                progress_percentage=legacy_job.progress_percentage,
                current_stage=None,
                created_at=legacy_job.created_at,
                started_at=legacy_job.started_at,
                completed_at=legacy_job.completed_at,
                result=legacy_job.result.dict() if legacy_job.result else None,
                error_message=None,
                estimated_time_remaining=None,
                is_draft=False,
                final_job_id=None
            )
        
        raise HTTPException(
            status_code=404,
            detail=f"Job {job_id} not found"
        )
        
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


@router.post("/generate-async", response_model=CreateImageJobResponse)
async def generate_image_async(
    request: ImageGenerationRequest,
    blog_id: Optional[str] = None,
    blog_job_id: Optional[str] = None
):
    """
    Create an asynchronous image generation job via Cloud Tasks.
    
    This endpoint creates a Cloud Task for image generation, enabling:
    - Non-blocking image generation
    - Better scalability for multiple images
    - Automatic retries on failure
    - Progress tracking via job status endpoint
    
    Use this for generating multiple images for blogs or batch operations.
    """
    import uuid
    
    try:
        # Create job
        job_id = str(uuid.uuid4())
        is_draft = request.quality.value == "draft"
        
        job = ImageGenerationJobStatus(
            job_id=job_id,
            status=ImageJobStatus.PENDING,
            request=request.dict(),
            blog_id=blog_id,
            blog_job_id=blog_job_id,
            is_draft=is_draft
        )
        
        image_generation_jobs[job_id] = job
        
        # Get Cloud Tasks service
        cloud_tasks_service = get_cloud_tasks_service()
        
        # Get worker URL
        worker_url = os.getenv("CLOUD_RUN_WORKER_URL")
        if not worker_url:
            service_base_url = os.getenv("CLOUD_RUN_SERVICE_URL", "https://blog-writer-api-dev-kq42l26tuq-od.a.run.app")
            worker_url = f"{service_base_url}/api/v1/images/worker"
        
        # Create Cloud Task
        task_name = cloud_tasks_service.create_image_generation_task(
            request_data={
                "job_id": job_id,
                "request": request.dict()
            },
            worker_url=worker_url,
            queue_name=os.getenv("CLOUD_TASKS_IMAGE_QUEUE_NAME", "image-generation-queue")
        )
        
        # Update job
        job.task_name = task_name
        job.status = ImageJobStatus.QUEUED
        job.queued_at = datetime.utcnow()
        
        logger.info(f"Created async image generation job: {job_id}, task: {task_name}")
        
        # Estimate completion time based on quality
        estimated_time = 5 if is_draft else 15  # Draft: 5s, Final: 15s
        
        return CreateImageJobResponse(
            job_id=job_id,
            status=ImageJobStatus.QUEUED,
            message="Image generation job queued successfully",
            estimated_completion_time=estimated_time,
            is_draft=is_draft
        )
        
    except Exception as e:
        logger.error(f"Failed to create async image job: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create image generation job: {str(e)}"
        )


@router.post("/worker")
async def image_generation_worker(request: Dict[str, Any]):
    """
    Internal worker endpoint called by Cloud Tasks to process image generation jobs.
    
    This endpoint:
    1. Receives job_id and request data from Cloud Tasks
    2. Updates job status to PROCESSING
    3. Generates the image
    4. Updates job with result or error
    5. Marks job as COMPLETED or FAILED
    
    This endpoint should not be called directly by clients.
    """
    try:
        global image_generation_jobs
        
        # Extract job_id and request data
        job_id = request.get("job_id")
        if not job_id:
            logger.error("Worker called without job_id")
            return JSONResponse(
                status_code=400,
                content={"error": "job_id is required"}
            )
        
        # Get job from storage
        if job_id not in image_generation_jobs:
            logger.error(f"Image job {job_id} not found")
            return JSONResponse(
                status_code=404,
                content={"error": f"Job {job_id} not found"}
            )
        
        job = image_generation_jobs[job_id]
        
        # Update job status
        job.status = ImageJobStatus.PROCESSING
        job.started_at = datetime.utcnow()
        job.current_stage = "generating"
        job.progress_percentage = 10.0
        
        # Parse request
        request_data = request.get("request", {})
        image_request = ImageGenerationRequest(**request_data)
        
        try:
            # Generate image
            job.progress_percentage = 30.0
            job.current_stage = "calling_provider"
            
            response = await image_provider_manager.generate_image(image_request)
            
            job.progress_percentage = 90.0
            job.current_stage = "processing_result"
            
            # Update job with result
            job.status = ImageJobStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            job.result = response.dict()
            job.progress_percentage = 100.0
            
            logger.info(f"Image generation job completed: {job_id}")
            
            return JSONResponse(
                status_code=200,
                content={"status": "completed", "job_id": job_id}
            )
            
        except Exception as e:
            job.status = ImageJobStatus.FAILED
            job.completed_at = datetime.utcnow()
            job.error_message = str(e)
            job.error_details = {"exception_type": type(e).__name__}
            
            logger.error(f"Image generation job failed {job_id}: {e}")
            
            return JSONResponse(
                status_code=500,
                content={"status": "failed", "job_id": job_id, "error": str(e)}
            )
            
    except Exception as e:
        logger.error(f"Worker error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )




@router.post("/batch-generate", response_model=BatchImageGenerationResponse)
async def batch_generate_images(request: BatchImageGenerationRequest):
    """
    Generate multiple images asynchronously via Cloud Tasks.
    
    This endpoint creates multiple Cloud Tasks for batch image generation,
    useful for generating all images needed for a blog post.
    
    Supports draft_then_final workflow:
    - First generates draft images (fast)
    - Then generates final images (high quality) after approval
    """
    import uuid
    
    try:
        batch_id = str(uuid.uuid4())
        job_ids = []
        
        # Create jobs for each image
        for image_request in request.images:
            is_draft = request.workflow == "draft_then_final" and image_request.quality.value == "draft"
            
            job_id = str(uuid.uuid4())
            job = ImageGenerationJobStatus(
                job_id=job_id,
                status=ImageJobStatus.PENDING,
                request=image_request.dict(),
                blog_id=request.blog_id,
                blog_job_id=request.blog_job_id,
                is_draft=is_draft
            )
            
            image_generation_jobs[job_id] = job
            job_ids.append(job_id)
            
            # Get Cloud Tasks service
            cloud_tasks_service = get_cloud_tasks_service()
            
            # Get worker URL
            worker_url = os.getenv("CLOUD_RUN_WORKER_URL")
            if not worker_url:
                service_base_url = os.getenv("CLOUD_RUN_SERVICE_URL", "https://blog-writer-api-dev-kq42l26tuq-od.a.run.app")
                worker_url = f"{service_base_url}/api/v1/images/worker"
            
            # Create Cloud Task
            task_name = cloud_tasks_service.create_image_generation_task(
                request_data={
                    "job_id": job_id,
                    "request": image_request.dict()
                },
                worker_url=worker_url,
                queue_name=os.getenv("CLOUD_TASKS_IMAGE_QUEUE_NAME", "image-generation-queue")
            )
            
            # Update job
            job.task_name = task_name
            job.status = ImageJobStatus.QUEUED
            job.queued_at = datetime.utcnow()
        
        logger.info(f"Created batch image generation: {batch_id} with {len(job_ids)} jobs")
        
        # Estimate completion time
        draft_count = sum(1 for img in request.images if img.quality.value == "draft")
        final_count = len(request.images) - draft_count
        estimated_time = (draft_count * 5) + (final_count * 15)
        
        return BatchImageGenerationResponse(
            batch_id=batch_id,
            job_ids=job_ids,
            status=ImageJobStatus.QUEUED,
            total_images=len(request.images),
            estimated_completion_time=estimated_time
        )
        
    except Exception as e:
        logger.error(f"Failed to create batch image generation: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create batch image generation: {str(e)}"
        )


# Initialize with existing environment variables
async def initialize_image_providers_from_env():
    """Initialize image providers from environment variables."""
    try:
        # Stability AI
        stability_key = os.getenv("STABILITY_AI_API_KEY")
        if stability_key and stability_key.strip() and stability_key != "placeholder-key":
            await configure_image_provider(
                provider_type=ImageProviderType.STABILITY_AI,
                api_key=stability_key,
                enabled=True,
                priority=1,
                default_model=os.getenv("STABILITY_AI_DEFAULT_MODEL", "stable-diffusion-xl-1024-v1-0")
            )
            logger.info("✅ Stability AI image provider initialized successfully")
        else:
            logger.warning("⚠️ STABILITY_AI_API_KEY not found or invalid. Image generation will be disabled.")
            logger.warning("   To enable image generation, set STABILITY_AI_API_KEY in Cloud Run secrets.")
        
        # Log provider status
        if image_provider_manager and image_provider_manager.providers:
            logger.info(f"✅ {len(image_provider_manager.providers)} image provider(s) available")
        else:
            logger.warning("⚠️ No image providers available. Image generation will be disabled.")
        
    except Exception as e:
        logger.error(f"Failed to initialize image providers from environment: {e}", exc_info=True)


# Export the router and manager for use in main.py
__all__ = ["router", "image_provider_manager", "initialize_image_providers_from_env"]

