"""
Job status models for async blog generation.

These models track the status and results of asynchronous blog generation jobs
processed via Cloud Tasks.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """Job status enumeration."""
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BlogGenerationJob(BaseModel):
    """Model for tracking async blog generation jobs."""
    
    job_id: str = Field(..., description="Unique job identifier")
    status: JobStatus = Field(default=JobStatus.PENDING, description="Current job status")
    
    # Request data
    request: Dict[str, Any] = Field(..., description="Original blog generation request")
    
    # Progress tracking
    progress_percentage: float = Field(default=0.0, ge=0, le=100, description="Generation progress")
    current_stage: Optional[str] = Field(None, description="Current pipeline stage")
    
    # Results
    result: Optional[Dict[str, Any]] = Field(None, description="Blog generation result (when completed)")
    
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
    
    # Progress updates from pipeline
    progress_updates: list[Dict[str, Any]] = Field(
        default_factory=list,
        description="Progress updates from pipeline stages"
    )


class JobStatusResponse(BaseModel):
    """Response model for job status queries."""
    
    job_id: str = Field(..., description="Job identifier")
    status: JobStatus = Field(..., description="Current status")
    progress_percentage: float = Field(..., ge=0, le=100, description="Progress percentage")
    current_stage: Optional[str] = Field(None, description="Current stage")
    
    # Progress updates for stage tracking
    progress_updates: list[Dict[str, Any]] = Field(
        default_factory=list,
        description="All progress updates from pipeline stages. Use this to track stage completion."
    )
    
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


class CreateJobResponse(BaseModel):
    """Response when creating an async job."""
    
    job_id: str = Field(..., description="Job identifier")
    status: JobStatus = Field(..., description="Initial status")
    message: str = Field(..., description="Status message")
    estimated_completion_time: Optional[int] = Field(None, description="Estimated seconds until completion")

