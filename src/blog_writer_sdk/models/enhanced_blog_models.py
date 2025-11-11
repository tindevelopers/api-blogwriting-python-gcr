"""
Enhanced Blog Generation Models

Models for Phase 1 & 2 enhanced blog generation features.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from .blog_models import ContentTone, ContentLength


class EnhancedBlogGenerationRequest(BaseModel):
    """Request for enhanced multi-stage blog generation."""
    
    topic: str = Field(..., min_length=3, max_length=200, description="Main topic for the blog post")
    keywords: List[str] = Field(..., min_items=1, description="Target SEO keywords")
    tone: ContentTone = Field(default=ContentTone.PROFESSIONAL, description="Writing tone")
    length: ContentLength = Field(default=ContentLength.MEDIUM, description="Target content length")
    
    # Enhanced options
    use_google_search: bool = Field(default=True, description="Use Google Custom Search for research")
    use_fact_checking: bool = Field(default=True, description="Enable fact-checking")
    use_citations: bool = Field(default=True, description="Include citations and sources")
    use_serp_optimization: bool = Field(default=True, description="Optimize for SERP features")
    
    # Phase 3 options
    use_consensus_generation: bool = Field(default=False, description="Use multi-model consensus generation (Phase 3)")
    use_knowledge_graph: bool = Field(default=True, description="Use Google Knowledge Graph for entities (Phase 3)")
    use_semantic_keywords: bool = Field(default=True, description="Use advanced semantic keyword integration (Phase 3)")
    use_quality_scoring: bool = Field(default=True, description="Enable comprehensive quality scoring (Phase 3)")
    
    # Additional context
    target_audience: Optional[str] = Field(None, description="Target audience")
    custom_instructions: Optional[str] = Field(None, max_length=1000, description="Additional instructions")
    template_type: Optional[str] = Field(None, description="Prompt template type (expert_authority, how_to_guide, etc.)")


class EnhancedBlogGenerationResponse(BaseModel):
    """Response from enhanced blog generation."""
    
    # Content
    title: str = Field(..., description="Blog post title")
    content: str = Field(..., description="Blog post content")
    meta_title: str = Field(..., description="SEO-optimized meta title")
    meta_description: str = Field(..., description="SEO-optimized meta description")
    
    # Quality metrics
    readability_score: float = Field(..., ge=0, le=100, description="Flesch Reading Ease score")
    seo_score: float = Field(..., ge=0, le=100, description="Overall SEO score")
    
    # Pipeline information
    stage_results: List[Dict[str, Any]] = Field(default_factory=list, description="Results from each pipeline stage")
    citations: List[Dict[str, str]] = Field(default_factory=list, description="Citations and sources")
    
    # Performance metrics
    total_tokens: int = Field(..., ge=0, description="Total tokens used")
    total_cost: float = Field(..., ge=0, description="Total cost in USD")
    generation_time: float = Field(..., ge=0, description="Generation time in seconds")
    
    # SEO metadata
    seo_metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional SEO metadata")
    internal_links: List[Dict[str, str]] = Field(default_factory=list, description="Internal linking suggestions")
    
    # Phase 3 features
    quality_score: Optional[float] = Field(None, ge=0, le=100, description="Overall content quality score (Phase 3)")
    quality_dimensions: Dict[str, float] = Field(default_factory=dict, description="Quality scores by dimension (Phase 3)")
    structured_data: Optional[Dict[str, Any]] = Field(None, description="Schema.org structured data (Phase 3)")
    semantic_keywords: List[str] = Field(default_factory=list, description="Semantically integrated keywords (Phase 3)")
    
    # Success indicators
    success: bool = Field(default=True, description="Whether generation was successful")
    warnings: List[str] = Field(default_factory=list, description="Warnings or issues encountered")

