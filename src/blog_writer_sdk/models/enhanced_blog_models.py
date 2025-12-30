"""
Enhanced Blog Generation Models

Models for Phase 1 & 2 enhanced blog generation features.
Updated December 2025 with multi-site support and enhanced internal linking.
"""

from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field
from .blog_models import ContentTone, ContentLength


# ============================================================================
# Internal Link Models (Multi-Site Support)
# ============================================================================

class InternalLinkTarget(BaseModel):
    """
    Internal link target from frontend or database.
    
    Supports both simple format (backwards compatible) and enhanced format.
    """
    title: str = Field(..., description="Page title")
    url: str = Field(..., description="Full URL or relative path to the page")
    slug: Optional[str] = Field(None, description="URL slug (optional)")
    keywords: List[str] = Field(default_factory=list, description="Keywords associated with this page")
    type: Optional[str] = Field(None, description="Content type: 'cms', 'static', 'blog', etc.")
    published_at: Optional[str] = Field(None, description="ISO 8601 publication date")


class InsertedInternalLink(BaseModel):
    """Details of an internal link that was inserted into content."""
    anchor_text: str = Field(..., description="Text used for the link")
    url: str = Field(..., description="URL the link points to")
    target_title: Optional[str] = Field(None, description="Title of the target page")
    position: str = Field(default="body", description="Where in content: 'introduction', 'body', 'conclusion'")
    relevance_score: float = Field(default=0.0, ge=0, le=1, description="Relevance score 0-1")


class InternalLinksMetadata(BaseModel):
    """Metadata about internal links in the generated content."""
    inserted: List[InsertedInternalLink] = Field(default_factory=list, description="Links that were inserted")
    available_count: int = Field(default=0, description="Total available link targets")
    inserted_count: int = Field(default=0, description="Number of links actually inserted")
    max_allowed: int = Field(default=5, description="Maximum links allowed")


class SiteContext(BaseModel):
    """Context about the site for internal linking."""
    site_id: Optional[str] = Field(None, description="Site identifier")
    site_domain: Optional[str] = Field(None, description="Site domain URL")
    scan_date: Optional[str] = Field(None, description="When site content was last scanned")
    total_pages: int = Field(default=0, description="Total pages available for linking")


class ImagePosition(BaseModel):
    """Suggested image position in content."""
    position: str = Field(..., description="Where to place: 'after_h1', 'before_section_2', etc.")
    suggested_alt: str = Field(..., description="Suggested alt text for the image")
    context: str = Field(default="", description="Context about why an image fits here")


class GenerationMode(str, Enum):
    """Blog generation mode."""
    QUICK_GENERATE = "quick_generate"  # Fast, DataForSEO only
    MULTI_PHASE = "multi_phase"        # Comprehensive, Pipeline with enhancements


class BlogContentType(str, Enum):
    """
    Blog content type enumeration - Top 80% of popular content formats.
    
    Supports all major blog types that drive traffic and engagement.
    """
    # Core Types
    CUSTOM = "custom"
    BRAND = "brand"
    TOP_10 = "top_10"
    PRODUCT_REVIEW = "product_review"
    HOW_TO = "how_to"
    COMPARISON = "comparison"
    GUIDE = "guide"
    
    # Popular Content Types (Top 80%)
    TUTORIAL = "tutorial"
    LISTICLE = "listicle"
    CASE_STUDY = "case_study"
    NEWS = "news"
    OPINION = "opinion"
    INTERVIEW = "interview"
    FAQ = "faq"
    CHECKLIST = "checklist"
    TIPS = "tips"
    DEFINITION = "definition"
    BENEFITS = "benefits"
    PROBLEM_SOLUTION = "problem_solution"
    TREND_ANALYSIS = "trend_analysis"
    STATISTICS = "statistics"
    RESOURCE_LIST = "resource_list"
    TIMELINE = "timeline"
    MYTH_BUSTING = "myth_busting"
    BEST_PRACTICES = "best_practices"
    GETTING_STARTED = "getting_started"
    ADVANCED = "advanced"
    TROUBLESHOOTING = "troubleshooting"


class EnhancedBlogGenerationRequest(BaseModel):
    """Request for enhanced multi-stage blog generation."""
    
    topic: str = Field(..., min_length=3, max_length=200, description="Main topic for the blog post")
    keywords: List[str] = Field(..., min_items=1, description="Target SEO keywords")
    tone: ContentTone = Field(default=ContentTone.PROFESSIONAL, description="Writing tone")
    length: ContentLength = Field(default=ContentLength.MEDIUM, description="Target content length")
    
    # Generation mode: determines which workflow to use
    mode: GenerationMode = Field(
        default=GenerationMode.QUICK_GENERATE,
        description="Generation mode: 'quick_generate' uses DataForSEO (fast, cost-effective), 'multi_phase' uses comprehensive pipeline (premium quality)"
    )
    
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
    
    # SEO and Traffic Optimization
    optimize_for_traffic: bool = Field(
        default=True,
        description="Enable SEO post-processing and traffic optimization"
    )
    
    # Backlink Analysis (Premium Feature)
    analyze_backlinks: bool = Field(
        default=False,
        description="Analyze backlinks from a premium blog URL to extract high-performing keywords"
    )
    backlink_url: Optional[str] = Field(
        None,
        description="URL of premium blog to analyze for keyword extraction (required if analyze_backlinks=True)"
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
    custom_instructions: Optional[str] = Field(None, max_length=5000, description="Additional instructions for content generation")
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
    
    # Google Search Console site URL (optional, for multi-site support)
    gsc_site_url: Optional[str] = Field(
        None,
        description="Google Search Console site URL (optional). If not provided, uses default GSC_SITE_URL from environment. Format: 'https://example.com' or 'sc-domain:example.com'"
    )
    
    # Multi-site support (December 2025)
    org_id: Optional[str] = Field(
        None,
        description="Organization ID for multi-tenant support"
    )
    site_id: Optional[str] = Field(
        None,
        description="Specific site ID for organizations with multiple sites. Used to filter internal link targets."
    )
    site_domain: Optional[str] = Field(
        None,
        description="Site domain URL (e.g., 'https://example.com'). Used for internal link URL generation."
    )
    
    # Internal linking options
    internal_link_targets: Optional[List[InternalLinkTarget]] = Field(
        None,
        description="List of available internal link targets from the site. If not provided, backend will generate placeholder links."
    )
    max_internal_links: int = Field(
        default=5,
        ge=0,
        le=10,
        description="Maximum number of internal links to insert (0-10)"
    )


class EnhancedBlogGenerationResponse(BaseModel):
    """Response from enhanced blog generation."""
    
    # Content
    title: str = Field(..., description="Blog post title")
    content: str = Field(..., description="Blog post content")
    excerpt: Optional[str] = Field(
        None,
        max_length=300,
        description="Short excerpt/summary for previews"
    )
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
    internal_links: List[Dict[str, str]] = Field(default_factory=list, description="Internal linking suggestions (legacy format)")
    
    # Enhanced internal links (December 2025)
    internal_links_metadata: Optional[InternalLinksMetadata] = Field(
        None,
        description="Detailed metadata about inserted internal links"
    )
    site_context: Optional[SiteContext] = Field(
        None,
        description="Context about the site used for internal linking"
    )
    
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
    
    # Sanitization info (December 2025)
    sanitization_applied: bool = Field(
        default=False,
        description="Whether content sanitization was applied to remove LLM artifacts"
    )
    artifacts_removed: List[str] = Field(
        default_factory=list,
        description="List of artifact types that were removed (e.g., 'preamble: 1 instance(s)')"
    )
    
    # Image positions (December 2025)
    image_positions: List[ImagePosition] = Field(
        default_factory=list,
        description="Suggested image positions in content (instead of embedding placeholder images)"
    )
    
    # Progress tracking
    progress_updates: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Progress updates from pipeline stages (for frontend status display)"
    )

