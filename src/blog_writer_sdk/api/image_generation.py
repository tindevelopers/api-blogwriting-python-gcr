"""
Image Generation API Endpoints

This module provides REST API endpoints for image generation,
including text-to-image, image variations, upscaling, and editing.
"""

import os
import time
import logging
import asyncio
import uuid
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
from .image_streaming import (
    ImageGenerationStage,
    create_image_stage_update,
    stream_image_stage_update
)
from .image_prompt_generator import (
    ImagePromptGenerator,
    ImageType,
    ImageStyle,
    ImagePrompt,
    ImagePlacementSuggestion
)

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


@router.post("/generate", response_model=CreateImageJobResponse)
async def generate_image(
    request: ImageGenerationRequest,
    blog_id: Optional[str] = None,
    blog_job_id: Optional[str] = None
):
    """
    Generate an image from a text prompt (async via Cloud Tasks queue).
    
    This endpoint creates an async job via Cloud Tasks and returns immediately with job_id.
    Use GET /api/v1/images/jobs/{job_id} to check status and retrieve results.
    
    This endpoint always uses async mode (queue) for better scalability.
    """
    # Delegate to async endpoint
    return await generate_image_async(request, blog_id, blog_job_id)


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
    
    Note: /generate endpoint now uses this same async logic by default.
    Use this endpoint for backward compatibility or explicit async behavior.
    """
    
    try:
        from ..monitoring.request_context import get_usage_attribution
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
                "request": request.dict(),
                "usage": get_usage_attribution(),
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


@router.post("/generate/stream")
async def generate_image_stream(
    request: ImageGenerationRequest,
    blog_id: Optional[str] = None,
    blog_job_id: Optional[str] = None
):
    """
    Streaming version of image generation.
    
    Returns Server-Sent Events (SSE) stream showing progress through each stage:
    - queued: Job created and queued
    - processing: Starting generation
    - generating: AI generating image
    - uploading: Uploading to storage
    - completed: Image ready
    
    This endpoint always uses async mode (queue) and streams stage updates.
    Frontend can listen to these events to show real-time progress.
    
    Example:
    ```typescript
    const response = await fetch('/api/v1/images/generate/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt: 'A sunset', quality: 'draft' })
    });
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      const chunk = decoder.decode(value);
      const lines = chunk.split('\\n');
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const update = JSON.parse(line.slice(6));
          console.log(`Stage: ${update.stage}, Progress: ${update.progress}%`);
        }
      }
    }
    ```
    """
    async def generate_stream():
        try:
            global image_generation_jobs
            from ..monitoring.request_context import get_usage_attribution
            
            # Create async job
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
            
            # Yield initial queued status
            yield await stream_image_stage_update(
                ImageGenerationStage.QUEUED,
                0.0,
                message="Image generation job created",
                job_id=job_id,
                status="queued"
            )
            
            try:
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
                        "request": request.dict(),
                        "usage": get_usage_attribution(),
                    },
                    worker_url=worker_url,
                    queue_name=os.getenv("CLOUD_TASKS_IMAGE_QUEUE_NAME", "image-generation-queue")
                )
                
                # Update job
                job.task_name = task_name
                job.status = ImageJobStatus.QUEUED
                job.queued_at = datetime.utcnow()
                
                # Yield queued status
                yield await stream_image_stage_update(
                    ImageGenerationStage.QUEUED,
                    10.0,
                    message="Job queued successfully",
                    job_id=job_id,
                    status="queued"
                )
                
                # Poll job status and stream updates
                last_stage = None
                last_progress = 0.0
                max_wait_time = 300  # 5 minutes max
                start_time = time.time()
                
                while True:
                    # Check timeout
                    if time.time() - start_time > max_wait_time:
                        yield await stream_image_stage_update(
                            ImageGenerationStage.ERROR,
                            0.0,
                            data={"error": "Timeout waiting for job completion"},
                            message="Job timeout - took too long",
                            job_id=job_id,
                            status="failed"
                        )
                        break
                    
                    # Get current job status
                    if job_id not in image_generation_jobs:
                        yield await stream_image_stage_update(
                            ImageGenerationStage.ERROR,
                            0.0,
                            data={"error": "Job not found"},
                            message="Job not found",
                            job_id=job_id,
                            status="failed"
                        )
                        break
                    
                    job = image_generation_jobs[job_id]
                    
                    # Map job status to stage
                    if job.status == ImageJobStatus.QUEUED:
                        current_stage = ImageGenerationStage.QUEUED
                        progress = 10.0
                    elif job.status == ImageJobStatus.PROCESSING:
                        current_stage = ImageGenerationStage.GENERATING
                        progress = 30.0 + (job.progress_percentage * 0.5)  # 30-80% during generation
                    elif job.status == ImageJobStatus.COMPLETED:
                        current_stage = ImageGenerationStage.COMPLETED
                        progress = 100.0
                    elif job.status == ImageJobStatus.FAILED:
                        current_stage = ImageGenerationStage.ERROR
                        progress = job.progress_percentage
                    else:
                        current_stage = ImageGenerationStage.PROCESSING
                        progress = 20.0
                    
                    # Yield update if stage or progress changed
                    if current_stage != last_stage or progress != last_progress:
                        yield await stream_image_stage_update(
                            current_stage,
                            progress,
                            data={
                                "is_draft": job.is_draft,
                                "blog_id": job.blog_id,
                                "blog_job_id": job.blog_job_id
                            },
                            message=f"Image generation: {current_stage.value}",
                            job_id=job_id,
                            status=job.status.value
                        )
                        
                        last_stage = current_stage
                        last_progress = progress
                    
                    # Check if completed
                    if job.status == ImageJobStatus.COMPLETED:
                        yield await stream_image_stage_update(
                            ImageGenerationStage.COMPLETED,
                            100.0,
                            data={"result": job.result},
                            message="Image generation completed successfully",
                            job_id=job_id,
                            status="completed"
                        )
                        break
                    
                    # Check if failed
                    if job.status == ImageJobStatus.FAILED:
                        yield await stream_image_stage_update(
                            ImageGenerationStage.ERROR,
                            progress,
                            data={"error": job.error_message, "error_details": job.error_details},
                            message=f"Image generation failed: {job.error_message}",
                            job_id=job_id,
                            status="failed"
                        )
                        break
                    
                    # Wait before next poll
                    await asyncio.sleep(0.3)
                    
            except Exception as e:
                logger.error(f"Failed to create or monitor image generation job: {e}", exc_info=True)
                yield await stream_image_stage_update(
                    ImageGenerationStage.ERROR,
                    0.0,
                    data={"error": str(e)},
                    message=f"Failed to create job: {str(e)}",
                    job_id=job_id,
                    status="failed"
                )
                
        except Exception as e:
            logger.error(f"Image generation stream error: {e}", exc_info=True)
            yield await stream_image_stage_update(
                ImageGenerationStage.ERROR,
                0.0,
                data={"error": str(e)},
                message=f"Stream error: {str(e)}",
                status="failed"
            )
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
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
        from ..monitoring.request_context import set_usage_attribution
        global image_generation_jobs

        usage = request.get("usage") if isinstance(request, dict) else None
        if isinstance(usage, dict):
            set_usage_attribution(
                usage_source=usage.get("usage_source"),
                usage_client=usage.get("usage_client"),
                request_id=usage.get("request_id"),
            )
        
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
        from ..monitoring.request_context import get_usage_attribution
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
                    "request": image_request.dict(),
                    "usage": get_usage_attribution(),
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


@router.post("/suggestions", response_model=Dict[str, Any])
async def get_image_suggestions(
    content: str,
    topic: str,
    keywords: List[str],
    tone: str = "professional"
):
    """
    Analyze blog content and suggest image placements with prompts.
    
    This endpoint analyzes blog content and returns:
    - Image placement suggestions
    - Generated prompts for each image
    - Style recommendations
    - Alt text suggestions
    
    Use this before generating images to get smart suggestions.
    """
    try:
        prompt_generator = ImagePromptGenerator()
        
        suggestions = prompt_generator.analyze_content_for_images(
            content=content,
            topic=topic,
            keywords=keywords,
            tone=tone
        )
        
        # Convert to response format
        response_suggestions = []
        for suggestion in suggestions:
            # Generate full prompt details
            if suggestion.image_type == ImageType.FEATURED:
                prompt_details = prompt_generator.generate_featured_image_prompt(
                    topic, keywords, tone
                )
            else:
                # Extract section content for section images
                sections = prompt_generator._extract_sections(content)
                section = sections[suggestion.position // 1000] if sections else None
                if section:
                    prompt_details = prompt_generator.generate_prompt_from_section(
                        section["content"],
                        section["title"],
                        topic,
                        keywords,
                        suggestion.image_type,
                        tone
                    )
                else:
                    continue
            
            response_suggestions.append({
                "image_type": suggestion.image_type.value,
                "style": suggestion.style.value,
                "aspect_ratio": suggestion.aspect_ratio,
                "prompt": prompt_details.prompt,
                "prompt_variations": prompt_details.variations,
                "alt_text": prompt_details.alt_text_suggestion,
                "placement": {
                    "position": suggestion.position,
                    "section": suggestion.section_title,
                    "priority": suggestion.priority
                }
            })
        
        return {
            "suggestions": response_suggestions,
            "total_suggestions": len(response_suggestions),
            "recommended_count": len([s for s in response_suggestions if s["placement"]["priority"] >= 4])
        }
        
    except Exception as e:
        logger.error(f"Failed to generate image suggestions: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate image suggestions: {str(e)}"
        )


@router.post("/generate-from-content", response_model=CreateImageJobResponse)
async def generate_image_from_content(
    content: str,
    topic: str,
    keywords: List[str],
    image_type: str = "featured",
    tone: str = "professional",
    section_title: Optional[str] = None
):
    """
    Generate image prompt from blog content and create generation job.
    
    This endpoint:
    1. Analyzes blog content
    2. Generates content-aware prompt
    3. Creates image generation job
    
    Use this for automatic prompt generation from content.
    """
    try:
        prompt_generator = ImagePromptGenerator()
        
        # Generate prompt based on image type
        image_type_enum = ImageType(image_type)
        
        if image_type_enum == ImageType.FEATURED:
            prompt_details = prompt_generator.generate_featured_image_prompt(
                topic, keywords, tone
            )
        else:
            # Extract section for section images
            sections = prompt_generator._extract_sections(content)
            section = None
            if section_title:
                section = next((s for s in sections if s["title"] == section_title), None)
            elif sections:
                section = sections[0]
            
            if not section:
                raise HTTPException(
                    status_code=400,
                    detail=f"Section '{section_title}' not found in content"
                )
            
            prompt_details = prompt_generator.generate_prompt_from_section(
                section["content"],
                section["title"],
                topic,
                keywords,
                image_type_enum,
                tone
            )
        
        # Create image generation request
        from ..models.image_models import ImageGenerationRequest, ImageQuality
        
        image_request = ImageGenerationRequest(
            prompt=prompt_details.prompt,
            provider=ImageProviderType.STABILITY_AI,
            style=prompt_details.style.value,
            aspect_ratio=prompt_details.aspect_ratio,
            quality=ImageQuality.HIGH,
            width=1920 if prompt_details.aspect_ratio == "16:9" else 1200,
            height=1080 if prompt_details.aspect_ratio == "16:9" else 900
        )
        
        # Create async job
        return await generate_image_async(image_request)
        
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid image type: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Failed to generate image from content: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate image from content: {str(e)}"
        )


# Export the router and manager for use in main.py
__all__ = ["router", "image_provider_manager", "initialize_image_providers_from_env"]

