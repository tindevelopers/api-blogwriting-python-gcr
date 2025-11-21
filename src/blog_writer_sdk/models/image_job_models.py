"""
Image job models for Cloud Tasks async processing.

These models track the status and results of asynchronous image generation jobs
processed via Cloud Tasks.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel, Field

from .image_models import ImageGenerationRequest, ImageGenerationResponse


class ImageJobStatus(str, Enum):
    """Image job status enumeration."""
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ImageGenerationJobStatus(BaseModel):
    """Model for tracking async image generation jobs with Cloud Tasks."""
    
    job_id: str = Field(..., description="Unique job identifier")
    status: ImageJobStatus = Field(default=ImageJobStatus.PENDING, description="Current job status")
    
    # Request data
    request: Dict[str, Any] = Field(..., description="Original image generation request")
    
    # Progress tracking
    progress_percentage: float = Field(default=0.0, ge=0, le=100, description="Generation progress")
    current_stage: Optional[str] = Field(None, description="Current generation stage")
    
    # Results
    result: Optional[Dict[str, Any]] = Field(None, description="Image generation result (when completed)")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Job creation time")
    queued_at: Optional[datetime] = Field(None, description="When job was queued")
    started_at: Optional[datetime] = Field(None, description="When generation started")
    completed_at: Optional[datetime] = Field(None, description="When generation completed")
    
    # Error handling
    error_message: Optional[str] = Field(None, description="Error message if failed")
    error_details: Optional[Dict[str, Any]] = Field(None, description="Detailed error information")
    retry_count: int = Field(default=0, ge=0, description="Number of retry attempts")
    
    # Cloud Tasks metadata
    task_name: Optional[str] = Field(None, description="Cloud Tasks task name")
    
    # Blog linking (for tracking which blog these images belong to)
    blog_id: Optional[str] = Field(None, description="Associated blog ID if generated for a blog")
    blog_job_id: Optional[str] = Field(None, description="Associated blog generation job ID")
    
    # Quality workflow tracking
    is_draft: bool = Field(default=False, description="Whether this is a draft image")
    final_job_id: Optional[str] = Field(None, description="Job ID for final version if this is a draft")
    draft_job_id: Optional[str] = Field(None, description="Draft job ID if this is a final version")


class ImageJobStatusResponse(BaseModel):
    """Response model for image job status queries."""
    
    job_id: str = Field(..., description="Job identifier")
    status: ImageJobStatus = Field(..., description="Current status")
    progress_percentage: float = Field(..., ge=0, le=100, description="Progress percentage")
    current_stage: Optional[str] = Field(None, description="Current stage")
    
    # Timestamps
    created_at: datetime = Field(..., description="Creation time")
    started_at: Optional[datetime] = Field(None, description="Start time")
    completed_at: Optional[datetime] = Field(None, description="Completion time")
    
    # Results (only if completed)
    result: Optional[Dict[str, Any]] = Field(None, description="Result if completed")
    
    # Error (only if failed)
    error_message: Optional[str] = Field(None, description="Error if failed")
    
    # Estimated time
    estimated_time_remaining: Optional[int] = Field(None, description="Estimated seconds remaining")
    
    # Quality workflow
    is_draft: bool = Field(default=False, description="Whether this is a draft")
    final_job_id: Optional[str] = Field(None, description="Final version job ID if draft")


class CreateImageJobResponse(BaseModel):
    """Response when creating an async image job."""
    
    job_id: str = Field(..., description="Job identifier")
    status: ImageJobStatus = Field(..., description="Initial status")
    message: str = Field(..., description="Status message")
    estimated_completion_time: Optional[int] = Field(None, description="Estimated seconds until completion")
    is_draft: bool = Field(default=False, description="Whether this is a draft image")


class BatchImageGenerationRequest(BaseModel):
    """Request model for batch image generation."""
    
    images: List[ImageGenerationRequest] = Field(..., min_items=1, max_items=20, description="List of image generation requests")
    blog_id: Optional[str] = Field(None, description="Associated blog ID")
    blog_job_id: Optional[str] = Field(None, description="Associated blog generation job ID")
    workflow: Optional[str] = Field("draft_then_final", description="Workflow: 'draft_then_final' or 'final_only'")


class BatchImageGenerationResponse(BaseModel):
    """Response model for batch image generation."""
    
    batch_id: str = Field(..., description="Batch job identifier")
    job_ids: List[str] = Field(..., description="Individual job IDs")
    status: ImageJobStatus = Field(..., description="Batch status")
    total_images: int = Field(..., description="Total number of images")
    estimated_completion_time: Optional[int] = Field(None, description="Estimated seconds until completion")

