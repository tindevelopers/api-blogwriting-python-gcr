"""
Models for category-based content analysis and source routing.

These enums and data classes define the taxonomy (format/category/entity)
and the source bundles to pull from DataForSEO (Business Data, Content
Analysis, Merchant, AI Optimization) while keeping enrichment separate
from content-quality scoring.
"""

from __future__ import annotations

import hashlib
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ContentFormatChoice(str, Enum):
    """User-facing content format choices (UI dropdown)."""

    BLOG = "blog"
    LISTICLE = "listicle"
    ARTICLE = "article"
    HOW_TO = "how_to"
    REVIEW = "review"
    RATING = "rating"
    TODO = "todo"


class ContentCategory(str, Enum):
    """High-level category that drives which sources are allowed."""

    ENTITY_REVIEW = "entity_review"
    SERVICE_REVIEW = "service_review"
    PRODUCT_COMPARISON = "product_comparison"


class EntityType(str, Enum):
    """Entity types for review-style content."""

    HOTEL = "hotel"
    RESTAURANT = "restaurant"
    ATTRACTION = "attraction"
    LOCAL_BUSINESS = "local_business"
    EVENT = "event"
    SERVICE = "service"
    PRODUCT = "product"


class SourceName(str, Enum):
    """Supported upstream sources."""

    GOOGLE = "google"
    TRIPADVISOR = "tripadvisor"
    TRUSTPILOT = "trustpilot"
    SOCIAL = "social"
    CONTENT_ANALYSIS = "content_analysis"
    MERCHANT = "merchant"
    AI_OPTIMIZATION = "ai_optimization"


class SourceEndpoint(BaseModel):
    """Endpoint descriptor for a given source."""

    source: SourceName
    endpoint: str
    identifier_keys: List[str] = Field(
        default_factory=list,
        description="Keys required to query the endpoint (e.g., cid, url_path, domain)",
    )
    live: bool = Field(
        default=False,
        description="Whether the endpoint uses the Live method (no POST/GET split).",
    )


class SourceBundle(BaseModel):
    """Bundle of endpoints to use for a category/entity combination."""

    name: str
    endpoints: List[SourceEndpoint]
    notes: Optional[str] = None


class ContentAnalysisRequest(BaseModel):
    """Request payload for content analysis routing."""

    content: str
    org_id: str
    user_id: str
    content_format: ContentFormatChoice
    content_category: ContentCategory
    entity_type: Optional[EntityType] = None
    entity_name: Optional[str] = None
    google_cid: Optional[str] = None
    google_hotel_identifier: Optional[str] = None
    tripadvisor_url_path: Optional[str] = None
    trustpilot_domain: Optional[str] = None
    canonical_url: Optional[str] = None

    def content_hash(self) -> str:
        """Stable hash of the content for cache reuse."""
        return hashlib.sha256(self.content.encode("utf-8")).hexdigest()


class EvidenceRecord(BaseModel):
    """Normalized evidence record persisted for reuse."""

    evidence_id: str
    analysis_id: str
    source: SourceName
    endpoint: str
    entity_ref: Optional[str] = None
    payload: Dict
    payload_hash: str
    fetched_at: str


class AnalysisRecord(BaseModel):
    """Stored analysis metadata and summary."""

    analysis_id: str
    content_id: str
    org_id: str
    content_hash: str
    content_category: ContentCategory
    entity_type: Optional[EntityType] = None
    summary: Dict
    created_at: str
    config_version: str = "1.0"


# ---------------------------------------------------------------------------
# Source bundles per category/entity

ENTITY_REVIEW_BUNDLE = SourceBundle(
    name="entity_review_bundle",
    endpoints=[
        SourceEndpoint(
            source=SourceName.GOOGLE,
            endpoint="business_data/google/my_business_info/task_post",
            identifier_keys=["google_cid"],
        ),
        SourceEndpoint(
            source=SourceName.GOOGLE,
            endpoint="business_data/google/my_business_updates/task_post",
            identifier_keys=["google_cid"],
        ),
        SourceEndpoint(
            source=SourceName.GOOGLE,
            endpoint="business_data/google/reviews/task_post",
            identifier_keys=["google_cid"],
        ),
        SourceEndpoint(
            source=SourceName.GOOGLE,
            endpoint="business_data/google/hotel_info/task_post",
            identifier_keys=["google_hotel_identifier"],
        ),
        SourceEndpoint(
            source=SourceName.GOOGLE,
            endpoint="business_data/google/hotel_searches/task_post",
            identifier_keys=["entity_name"],
        ),
        SourceEndpoint(
            source=SourceName.TRIPADVISOR,
            endpoint="business_data/tripadvisor/search/task_post",
            identifier_keys=["entity_name"],
        ),
        SourceEndpoint(
            source=SourceName.TRIPADVISOR,
            endpoint="business_data/tripadvisor/reviews/task_post",
            identifier_keys=["tripadvisor_url_path"],
        ),
        SourceEndpoint(
            source=SourceName.SOCIAL,
            endpoint="business_data/social_media/facebook/live",
            identifier_keys=["canonical_url"],
            live=True,
        ),
        SourceEndpoint(
            source=SourceName.SOCIAL,
            endpoint="business_data/social_media/pinterest/live",
            identifier_keys=["canonical_url"],
            live=True,
        ),
        SourceEndpoint(
            source=SourceName.SOCIAL,
            endpoint="business_data/social_media/reddit/live",
            identifier_keys=["canonical_url"],
            live=True,
        ),
        SourceEndpoint(
            source=SourceName.CONTENT_ANALYSIS,
            endpoint="content_analysis/sentiment_analysis/live",
            identifier_keys=["entity_name"],
            live=True,
        ),
        SourceEndpoint(
            source=SourceName.AI_OPTIMIZATION,
            endpoint="ai_optimization/perplexity/llm_responses/live",
            identifier_keys=["entity_name"],
            live=True,
        ),
    ],
    notes="Best for hotels/restaurants/attractions entity reviews.",
)

SERVICE_REVIEW_BUNDLE = SourceBundle(
    name="service_review_bundle",
    endpoints=[
        SourceEndpoint(
            source=SourceName.GOOGLE,
            endpoint="business_data/google/my_business_info/task_post",
            identifier_keys=["google_cid"],
        ),
        SourceEndpoint(
            source=SourceName.GOOGLE,
            endpoint="business_data/google/my_business_updates/task_post",
            identifier_keys=["google_cid"],
        ),
        SourceEndpoint(
            source=SourceName.GOOGLE,
            endpoint="business_data/google/reviews/task_post",
            identifier_keys=["google_cid"],
        ),
        SourceEndpoint(
            source=SourceName.TRUSTPILOT,
            endpoint="business_data/trustpilot/search/task_post",
            identifier_keys=["entity_name"],
        ),
        SourceEndpoint(
            source=SourceName.TRUSTPILOT,
            endpoint="business_data/trustpilot/reviews/task_post",
            identifier_keys=["trustpilot_domain"],
        ),
        SourceEndpoint(
            source=SourceName.SOCIAL,
            endpoint="business_data/social_media/facebook/live",
            identifier_keys=["canonical_url"],
            live=True,
        ),
        SourceEndpoint(
            source=SourceName.SOCIAL,
            endpoint="business_data/social_media/pinterest/live",
            identifier_keys=["canonical_url"],
            live=True,
        ),
        SourceEndpoint(
            source=SourceName.SOCIAL,
            endpoint="business_data/social_media/reddit/live",
            identifier_keys=["canonical_url"],
            live=True,
        ),
        SourceEndpoint(
            source=SourceName.CONTENT_ANALYSIS,
            endpoint="content_analysis/sentiment_analysis/live",
            identifier_keys=["entity_name"],
            live=True,
        ),
        SourceEndpoint(
            source=SourceName.AI_OPTIMIZATION,
            endpoint="ai_optimization/perplexity/llm_responses/live",
            identifier_keys=["entity_name"],
            live=True,
        ),
    ],
    notes="Local/service businesses with Trustpilot + Google reviews.",
)

PRODUCT_COMPARISON_BUNDLE = SourceBundle(
    name="product_comparison_bundle",
    endpoints=[
        SourceEndpoint(
            source=SourceName.MERCHANT,
            endpoint="merchant/google/products/task_post",
            identifier_keys=["entity_name"],
        ),
        SourceEndpoint(
            source=SourceName.MERCHANT,
            endpoint="merchant/amazon/products/task_post",
            identifier_keys=["entity_name"],
        ),
        SourceEndpoint(
            source=SourceName.TRUSTPILOT,
            endpoint="business_data/trustpilot/reviews/task_post",
            identifier_keys=["trustpilot_domain"],
        ),
        SourceEndpoint(
            source=SourceName.AI_OPTIMIZATION,
            endpoint="ai_optimization/llm_responses/live",
            identifier_keys=["entity_name"],
            live=True,
        ),
    ],
    notes="Product/SaaS comparisons; merchant data + Trustpilot + LLM responses.",
)


SOURCE_BUNDLE_MAP: Dict[ContentCategory, SourceBundle] = {
    ContentCategory.ENTITY_REVIEW: ENTITY_REVIEW_BUNDLE,
    ContentCategory.SERVICE_REVIEW: SERVICE_REVIEW_BUNDLE,
    ContentCategory.PRODUCT_COMPARISON: PRODUCT_COMPARISON_BUNDLE,
}


def resolve_bundle(category: ContentCategory) -> SourceBundle:
    """Return the bundle for a category."""
    return SOURCE_BUNDLE_MAP[category]

