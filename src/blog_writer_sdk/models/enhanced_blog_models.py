"""
Enhanced Blog Generation Models

Models for Phase 1 & 2 enhanced blog generation features.
"""

from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field
from .blog_models import ContentTone, ContentLength


class BlogContentType(str, Enum):
    """Blog content type enumeration."""
    CUSTOM = "custom"
    BRAND = "brand"
    TOP_10 = "top_10"
    PRODUCT_REVIEW = "product_review"
    HOW_TO = "how_to"
    COMPARISON = "comparison"
    GUIDE = "guide"


class EnhancedBlogGenerationRequest(BaseModel):
    """Request for enhanced multi-stage blog generation."""
    
    topic: str = Field(..., min_length=3, max_length=200, description="Main topic for the blog post")
    keywords: List[str] = Field(..., min_items=1, description="Target SEO keywords")
    tone: ContentTone = Field(default=ContentTone.PROFESSIONAL, description="Writing tone")
    length: ContentLength = Field(default=ContentLength.MEDIUM, description="Target content length")
    
    # Blog type for DataForSEO Content Generation
    blog_type: Optional[BlogContentType] = Field(
        default=BlogContentType.CUSTOM,
        description="Type of blog content (brand, top_10, product_review, how_to, comparison, guide, custom)"
    )
    
    # Blog type-specific fields
    brand_name: Optional[str] = Field(None, description="Brand name (for brand type)")
    category: Optional[str] = Field(None, description="Category for top 10 lists")
    product_name: Optional[str] = Field(None, description="Product name (for product review type)")
    comparison_items: Optional[List[str]] = Field(None, description="Items to compare (for comparison type)")
    
    # Use DataForSEO Content Generation (default: True)
    use_dataforseo_content_generation: bool = Field(
        default=True,
        description="Use DataForSEO Content Generation API for all blog generation"
    )
    
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
    custom_instructions: Optional[str] = Field(None, max_length=2000, description="Additional instructions for content generation")
    template_type: Optional[str] = Field(None, description="Prompt template type (expert_authority, how_to_guide, etc.)")
    word_count_target: Optional[int] = Field(None, ge=100, le=10000, description="Specific word count target")
    
    # Product research options (for product review/comparison content)
    include_product_research: bool = Field(default=False, description="Enable comprehensive product research (brands, models, prices, features)")
    include_brands: bool = Field(default=True, description="Include specific brand recommendations")
    include_models: bool = Field(default=True, description="Include specific product models")
    include_prices: bool = Field(default=False, description="Include current pricing information")
    include_features: bool = Field(default=True, description="Include product features and specifications")
    include_reviews: bool = Field(default=True, description="Include review summaries and ratings")
    include_pros_cons: bool = Field(default=True, description="Include pros and cons for each product")
    
    # Content structure options
    include_product_table: bool = Field(default=False, description="Include product comparison table")
    include_comparison_section: bool = Field(default=True, description="Include detailed comparison section")
    include_buying_guide: bool = Field(default=True, description="Include buying guide section")
    include_faq_section: bool = Field(default=True, description="Include FAQ section based on common questions")
    
    # Research depth
    research_depth: Optional[str] = Field(default="standard", description="Research depth: 'basic', 'standard', or 'comprehensive'")


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
    
    # Frontend stack support (unified + remark + rehype + schema-dts)
    content_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Structured content metadata for frontend processing (headings, images, links, code blocks, etc.)"
    )
    
    # Success indicators
    success: bool = Field(default=True, description="Whether generation was successful")
    warnings: List[str] = Field(default_factory=list, description="Warnings or issues encountered")
    
    # Progress tracking
    progress_updates: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Progress updates from pipeline stages (for frontend status display)"
    )

