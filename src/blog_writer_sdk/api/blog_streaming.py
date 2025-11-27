"""
Streaming support for blog generation endpoints.

Provides Server-Sent Events (SSE) streaming for blog generation
to show real-time progress of generation stages.
"""

import json
import time
from typing import Dict, Any, Optional
from enum import Enum


class BlogGenerationStage(str, Enum):
    """Stages of blog generation process."""
    INITIALIZATION = "initialization"
    KEYWORD_ANALYSIS = "keyword_analysis"
    COMPETITOR_ANALYSIS = "competitor_analysis"
    INTENT_ANALYSIS = "intent_analysis"
    LENGTH_OPTIMIZATION = "length_optimization"
    RESEARCH_OUTLINE = "research_outline"
    DRAFT_GENERATION = "draft_generation"
    ENHANCEMENT = "enhancement"
    SEO_POLISH = "seo_polish"
    SEMANTIC_INTEGRATION = "semantic_integration"
    QUALITY_SCORING = "quality_scoring"
    CITATION_GENERATION = "citation_generation"
    FINALIZATION = "finalization"
    COMPLETED = "completed"
    ERROR = "error"
    QUEUED = "queued"
    PROCESSING = "processing"


def create_blog_stage_update(
    stage: BlogGenerationStage,
    progress: float,
    data: Optional[Dict[str, Any]] = None,
    message: Optional[str] = None,
    job_id: Optional[str] = None,
    status: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a standardized blog generation stage update message.
    
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


async def stream_blog_stage_update(
    stage: BlogGenerationStage,
    progress: float,
    data: Optional[Dict[str, Any]] = None,
    message: Optional[str] = None,
    job_id: Optional[str] = None,
    status: Optional[str] = None
) -> str:
    """
    Format a blog generation stage update as SSE data line.
    
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
    update = create_blog_stage_update(stage, progress, data, message, job_id, status)
    return f"data: {json.dumps(update)}\n\n"

