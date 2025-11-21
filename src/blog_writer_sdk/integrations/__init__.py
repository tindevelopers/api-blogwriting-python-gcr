"""
Integration modules for the Blog Writer SDK.

This package contains integrations with external services
like databases, third-party APIs, and media storage providers.
"""

from .supabase_client import SupabaseClient
from .webflow_integration import WebflowClient, WebflowPublisher
from .shopify_integration import ShopifyClient, ShopifyPublisher
from .media_storage import (
    MediaStorageProvider,
    CloudinaryStorage,
    CloudflareR2Storage,
    MediaStorageManager,
    create_cloudinary_storage,
    create_cloudflare_r2_storage,
    create_media_storage_manager
)
from .yelp_integration import YelpClient
from .google_reviews_client import GoogleReviewsClient
from .review_aggregation import (
    ReviewAggregationService,
    Review,
    ReviewSource,
    BusinessReviewSummary,
)

__all__ = [
    "SupabaseClient",
    "WebflowClient",
    "WebflowPublisher",
    "ShopifyClient",
    "ShopifyPublisher",
    "MediaStorageProvider",
    "CloudinaryStorage",
    "CloudflareR2Storage",
    "MediaStorageManager",
    "create_cloudinary_storage",
    "create_cloudflare_r2_storage",
    "create_media_storage_manager",
    "YelpClient",
    "GoogleReviewsClient",
    "ReviewAggregationService",
    "Review",
    "ReviewSource",
    "BusinessReviewSummary",
]
