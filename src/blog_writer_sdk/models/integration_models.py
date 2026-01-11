"""
Models for integration and interlinking functionality.
"""
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, validator


class ContentSystemProvider(str, Enum):
    """Content system provider types."""
    webflow = "webflow"
    wordpress = "wordpress"
    shopify = "shopify"
    medium = "medium"
    custom = "custom"


# Legacy models for backward compatibility
class KeywordRecommendation(BaseModel):
    """Legacy model for keyword recommendation (backward compatibility)."""
    keyword: str
    difficulty: Optional[float] = None
    suggested_backlinks: int = 0
    suggested_interlinks: int = 0


class IntegrationConnectAndRecommendRequest(BaseModel):
    """Legacy request model (backward compatibility)."""
    tenant_id: Optional[str] = None
    provider: ContentSystemProvider
    connection: Dict[str, Any]
    keywords: List[str]
    interlinking_settings: Optional[InterlinkingSettings] = Field(
        default=None,
        description="Optional settings to control interlinking analysis (relevance threshold, authority weight, allow low-value links)"
    )


class IntegrationRecommendationResponse(BaseModel):
    """Legacy response model (backward compatibility)."""
    provider: str
    tenant_id: Optional[str] = None
    saved_integration: bool = False
    recommended_backlinks: int = 0
    recommended_interlinks: int = 0
    per_keyword: List[KeywordRecommendation]
    notes: Optional[str] = None


class InterlinkingSettings(BaseModel):
    """Settings for controlling interlinking analysis."""
    relevance_threshold: float = Field(
        default=0.4,
        ge=0.0,
        le=1.0,
        description="Minimum relevance score threshold (0.0 to 1.0). Links below this score will be filtered out unless allow_low_value_links is true."
    )
    authority_weight: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Weight for authority score in relevance calculation (0.0 to 1.0). Higher values prioritize authoritative content."
    )
    allow_low_value_links: bool = Field(
        default=False,
        description="If true, include links even if they fall below the relevance threshold. Useful for strategic linking despite lower relevance."
    )


class InterlinkOpportunity(BaseModel):
    """Model for a single interlink opportunity."""
    target_url: str = Field(..., description="URL of the target content")
    target_title: str = Field(..., description="Title of the target content")
    anchor_text: str = Field(..., description="Suggested anchor text for the link")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance score (0.0 to 1.0)")


class KeywordInterlinkAnalysis(BaseModel):
    """Model for interlink analysis per keyword."""
    keyword: str = Field(..., description="The keyword being analyzed")
    difficulty: Optional[float] = Field(None, description="Keyword difficulty score (if available)")
    suggested_interlinks: int = Field(..., ge=0, description="Number of suggested interlinks for this keyword")
    suggested_backlinks: int = Field(default=0, ge=0, description="Number of suggested backlinks (for future use)")
    interlink_opportunities: List[InterlinkOpportunity] = Field(
        default_factory=list,
        description="List of interlink opportunities for this keyword"
    )


class ConnectAndRecommendRequest(BaseModel):
    """Request model for connect and recommend endpoint."""
    tenant_id: Optional[str] = Field(None, description="Organization/tenant ID")
    provider: Literal['webflow', 'wordpress', 'shopify', 'medium'] = Field(
        ...,
        description="Content provider type"
    )
    connection: Dict[str, Any] = Field(
        ...,
        description="Connection object with provider credentials and structure"
    )
    keywords: List[str] = Field(
        ...,
        min_items=1,
        max_items=50,
        description="Keywords for interlinking analysis (1-50 keywords)"
    )
    interlinking_settings: Optional[InterlinkingSettings] = Field(
        default=None,
        description="Optional settings to control interlinking analysis (relevance threshold, authority weight, allow low-value links)"
    )

    @validator('keywords')
    def validate_keywords(cls, v):
        """Validate keywords array."""
        if not v or len(v) == 0:
            raise ValueError('Keywords array must contain at least 1 keyword')
        if len(v) > 50:
            raise ValueError('Keywords array must contain at most 50 keywords')
        return v


class ConnectAndRecommendResponse(BaseModel):
    """Response model for connect and recommend endpoint."""
    provider: str = Field(..., description="Content provider type")
    tenant_id: Optional[str] = Field(None, description="Organization/tenant ID")
    saved_integration: bool = Field(
        default=False,
        description="Whether integration was saved to database"
    )
    recommended_interlinks: int = Field(
        ...,
        ge=0,
        description="Total number of recommended interlinks"
    )
    recommended_backlinks: int = Field(
        default=0,
        ge=0,
        description="Total number of recommended backlinks (for future use)"
    )
    per_keyword: List[KeywordInterlinkAnalysis] = Field(
        ...,
        description="Interlink analysis results per keyword"
    )
    notes: Optional[str] = Field(None, description="Additional notes or information")


class ExistingContentItem(BaseModel):
    """Model for existing content item from provider."""
    id: str = Field(..., description="Unique identifier for the content")
    title: str = Field(..., description="Title of the content")
    url: str = Field(..., description="URL of the content")
    slug: str = Field(..., description="URL slug of the content")
    keywords: List[str] = Field(default_factory=list, description="Keywords associated with the content")
    categories: Optional[List[str]] = Field(None, description="Categories for the content")
    published_at: Optional[str] = Field(None, description="Publication date (ISO format)")
    excerpt: Optional[str] = Field(None, description="Content excerpt or summary")
    # SEO metadata (used for richer matching)
    meta_description: Optional[str] = Field(None, description="SEO meta description for the page")
    title_tag: Optional[str] = Field(None, description="SEO title tag if different from display title")
    short_description: Optional[str] = Field(None, description="Short description/summary from CMS")
    # Collection and page type awareness
    collection_slug: Optional[str] = Field(None, description="Collection slug (e.g., solutions, blog-posts, projects)")
    collection_name: Optional[str] = Field(None, description="Collection name (e.g., Solutions, Blog Posts, Projects)")
    page_type: Optional[str] = Field(
        None,
        description="Normalized page type (solution, blog, case-study, static, project, etc.)"
    )
    # Strategic priority score supplied by provider or mapping (0.0-2.0, higher = more important)
    strategic_priority: Optional[float] = Field(
        None,
        ge=0.0,
        le=2.0,
        description="Strategic importance weight (0.0-2.0). Higher values prioritized for interlinking."
    )
