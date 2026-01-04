"""
Lightweight wrappers around DataForSEO Business Data, Content Analysis,
and Merchant endpoints used for category-based enrichment.

We reuse the existing DataForSEOClient._make_request for auth + transport.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from .dataforseo_integration import DataForSEOClient

logger = logging.getLogger(__name__)


class DataForSEOBusinessClient(DataForSEOClient):
    """Business Data + Content Analysis + Merchant helpers."""

    # ---------------------- Google Business Data ---------------------- #
    async def google_my_business_info(self, cid: str, tenant_id: str) -> Dict:
        payload = [{"cid": cid}]
        return await self._make_request("business_data/google/my_business_info/task_post", payload, tenant_id)

    async def google_my_business_updates(self, cid: str, tenant_id: str) -> Dict:
        payload = [{"cid": cid}]
        return await self._make_request("business_data/google/my_business_updates/task_post", payload, tenant_id)

    async def google_reviews(self, cid: str, tenant_id: str, page: int = 1) -> Dict:
        payload = [{"cid": cid, "page": page}]
        return await self._make_request("business_data/google/reviews/task_post", payload, tenant_id)

    async def google_hotel_info(self, hotel_identifier: str, tenant_id: str) -> Dict:
        payload = [{"hotel_identifier": hotel_identifier}]
        return await self._make_request("business_data/google/hotel_info/task_post", payload, tenant_id)

    async def google_hotel_searches(self, keyword: str, tenant_id: str) -> Dict:
        payload = [{"keyword": keyword}]
        return await self._make_request("business_data/google/hotel_searches/task_post", payload, tenant_id)

    # --------------------------- Tripadvisor -------------------------- #
    async def tripadvisor_search(self, keyword: str, location_name: Optional[str], tenant_id: str) -> Dict:
        task = {"keyword": keyword}
        if location_name:
            task["location_name"] = location_name
        payload = [task]
        return await self._make_request("business_data/tripadvisor/search/task_post", payload, tenant_id)

    async def tripadvisor_reviews(self, url_path: str, tenant_id: str) -> Dict:
        payload = [{"url_path": url_path}]
        return await self._make_request("business_data/tripadvisor/reviews/task_post", payload, tenant_id)

    # --------------------------- Trustpilot --------------------------- #
    async def trustpilot_search(self, keyword: str, tenant_id: str) -> Dict:
        payload = [{"keyword": keyword}]
        return await self._make_request("business_data/trustpilot/search/task_post", payload, tenant_id)

    async def trustpilot_reviews(self, domain: str, tenant_id: str) -> Dict:
        payload = [{"domain": domain}]
        return await self._make_request("business_data/trustpilot/reviews/task_post", payload, tenant_id)

    # ---------------------------- Social ------------------------------ #
    async def social_facebook(self, targets: List[str], tenant_id: str) -> Dict:
        payload = [{"targets": targets}]
        return await self._make_request("business_data/social_media/facebook/live", payload, tenant_id)

    async def social_pinterest(self, targets: List[str], tenant_id: str) -> Dict:
        payload = [{"targets": targets}]
        return await self._make_request("business_data/social_media/pinterest/live", payload, tenant_id)

    async def social_reddit(self, targets: List[str], tenant_id: str) -> Dict:
        payload = [{"targets": targets}]
        return await self._make_request("business_data/social_media/reddit/live", payload, tenant_id)

    # ----------------------- Content Analysis ------------------------- #
    async def sentiment_analysis(self, keyword: str, tenant_id: str) -> Dict:
        payload = [{"keyword": keyword}]
        return await self._make_request("content_analysis/sentiment_analysis/live", payload, tenant_id)

    async def summary(self, keyword: str, tenant_id: str) -> Dict:
        payload = [{"keyword": keyword}]
        return await self._make_request("content_analysis/summary/live", payload, tenant_id)

    # --------------------------- Merchant ----------------------------- #
    async def merchant_google_products(self, query: str, tenant_id: str) -> Dict:
        payload = [{"keyword": query}]
        return await self._make_request("merchant/google/products/task_post", payload, tenant_id)

    async def merchant_amazon_products(self, query: str, tenant_id: str) -> Dict:
        payload = [{"keyword": query}]
        return await self._make_request("merchant/amazon/products/task_post", payload, tenant_id)


def ensure_business_client(client: Optional[DataForSEOBusinessClient]) -> DataForSEOBusinessClient:
    """Factory with sensible defaults."""
    if client:
        return client
    return DataForSEOBusinessClient()

