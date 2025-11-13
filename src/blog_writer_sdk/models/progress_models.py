"""
Progress tracking models for blog generation pipeline.
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class PipelineStage(str, Enum):
    """Pipeline stage identifiers."""
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


class ProgressUpdate(BaseModel):
    """Progress update for frontend."""
    stage: str = Field(..., description="Current pipeline stage")
    stage_number: int = Field(..., description="Stage number (1-based)")
    total_stages: int = Field(..., description="Total number of stages")
    progress_percentage: float = Field(..., ge=0, le=100, description="Overall progress percentage")
    status: str = Field(..., description="Current status message")
    details: Optional[str] = Field(None, description="Detailed status information")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    timestamp: float = Field(..., description="Timestamp of the update")


class ProgressCallback:
    """Callback interface for progress updates."""
    
    async def __call__(self, update: ProgressUpdate) -> None:
        """
        Called when a progress update is available.
        
        Args:
            update: Progress update information
        """
        pass

