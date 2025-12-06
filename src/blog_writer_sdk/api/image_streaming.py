"""
Streaming support for image generation endpoints.

Provides Server-Sent Events (SSE) streaming for image generation
to show real-time progress of generation stages.
"""

import json
import time
from typing import Dict, Any, Optional
from enum import Enum


class ImageGenerationStage(str, Enum):
    """Stages of image generation process."""
    QUEUED = "queued"
    PROCESSING = "processing"
    GENERATING = "generating"
    UPLOADING = "uploading"
    COMPLETED = "completed"
    ERROR = "error"


def create_image_stage_update(
    stage: ImageGenerationStage,
    progress: float,
    data: Optional[Dict[str, Any]] = None,
    message: Optional[str] = None,
    job_id: Optional[str] = None,
    status: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a standardized image generation stage update message.
    
    Args:
        stage: Current stage of the generation
        progress: Progress percentage (0-100)
        data: Optional data for this stage
        message: Optional human-readable message
        job_id: Optional job ID for tracking
        status: Optional status (queued, processing, completed, failed)
        
    Returns:
        Dictionary with stage update information
    """
    update = {
        "stage": stage.value,
        "progress": progress,
        "timestamp": time.time()
    }
    
    if message:
        update["message"] = message
    
    if data:
        update["data"] = data
    
    if job_id:
        update["job_id"] = job_id
    
    if status:
        update["status"] = status
    
    return update


async def stream_image_stage_update(
    stage: ImageGenerationStage,
    progress: float,
    data: Optional[Dict[str, Any]] = None,
    message: Optional[str] = None,
    job_id: Optional[str] = None,
    status: Optional[str] = None
) -> str:
    """
    Format an image generation stage update as SSE data line.
    
    Args:
        stage: Current stage
        progress: Progress percentage
        data: Optional stage data
        message: Optional message
        job_id: Optional job ID
        status: Optional status
        
    Returns:
        SSE-formatted string
    """
    update = create_image_stage_update(stage, progress, data, message, job_id, status)
    return f"data: {json.dumps(update)}\n\n"

