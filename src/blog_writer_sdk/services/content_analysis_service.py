"""
Service to orchestrate category-based analysis using DataForSEO sources.
"""

from __future__ import annotations

import asyncio
import logging
import os
import uuid
from typing import Dict, List, Optional

from ..integrations.dataforseo_business import DataForSEOBusinessClient, ensure_business_client
from ..models.content_routing_models import (
    ContentAnalysisRequest,
    ContentCategory,
    EvidenceRecord,
    resolve_bundle,
    SourceEndpoint,
    SourceName,
)
from .evidence_store import EvidenceStore

logger = logging.getLogger(__name__)


class ContentAnalysisService:
    """High-level coordinator for content analysis/enrichment."""

    def __init__(
        self,
        dataforseo_client: Optional[DataForSEOBusinessClient] = None,
        evidence_store: Optional[EvidenceStore] = None,
    ):
        self.client = ensure_business_client(dataforseo_client)
        self.evidence_store = evidence_store or EvidenceStore()
        self.environment = os.getenv("ENVIRONMENT", "dev")

    async def analyze(self, request: ContentAnalysisRequest) -> Dict:
        """Perform analysis and persist evidence."""
        bundle = resolve_bundle(request.content_category)
        content_id = str(uuid.uuid4())
        analysis_id = str(uuid.uuid4())
        content_hash = request.content_hash()

        # Fetch endpoints in parallel where possible
        tasks = []
        task_endpoints: List[SourceEndpoint] = []
        for ep in bundle.endpoints:
            # Skip endpoints lacking identifiers
            if not self._has_identifiers(request, ep):
                continue
            tasks.append(self._fetch_endpoint(ep, request))
            task_endpoints.append(ep)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Rebuild evidence_items deterministically
        evidence_items = []
        for idx, res in enumerate(results):
            ep = task_endpoints[idx]
            if isinstance(res, Exception):
                logger.warning(f"{ep.endpoint} failed: {res}")
                continue
            evidence_items.append(
                (
                    ep.source.value,
                    ep.endpoint,
                    self._entity_ref(request, ep),
                    res or {},
                )
            )

        evidence_records: List[EvidenceRecord] = await self.evidence_store.save_evidence_batch(
            analysis_id=analysis_id, items=evidence_items
        )

        request_snapshot = request.model_dump(exclude={"content"})

        summary = {
            "bundle": bundle.name,
            "content_category": request.content_category.value,
            "entity_type": request.entity_type.value if request.entity_type else None,
            "evidence_count": len(evidence_records),
            "request": request_snapshot,
        }

        analysis_record = await self.evidence_store.save_analysis(
            content_id=content_id,
            org_id=request.org_id,
            content_hash=content_hash,
            content_category=request.content_category.value,
            entity_type=request.entity_type.value if request.entity_type else None,
            summary=summary,
            analysis_id=analysis_id,
        )

        return {
            "analysis_id": analysis_record.analysis_id,
            "content_id": content_id,
            "evidence_count": len(evidence_records),
            "bundle": bundle.name,
        }

    async def refresh(self, analysis_id: str, request: ContentAnalysisRequest) -> Dict:
        """Refresh sources for an existing analysis (fetch deltas)."""
        bundle = resolve_bundle(request.content_category)
        tasks = []
        task_endpoints: List[SourceEndpoint] = []
        for ep in bundle.endpoints:
            if not self._has_identifiers(request, ep):
                continue
            tasks.append(self._fetch_endpoint(ep, request))
            task_endpoints.append(ep)
        results = await asyncio.gather(*tasks, return_exceptions=True)

        evidence_items = []
        for idx, res in enumerate(results):
            ep = task_endpoints[idx]
            if isinstance(res, Exception):
                logger.warning(f"{ep.endpoint} refresh failed: {res}")
                continue
            evidence_items.append(
                (
                    ep.source.value,
                    ep.endpoint,
                    self._entity_ref(request, ep),
                    res or {},
                )
            )

        new_records = await self.evidence_store.save_evidence_batch(
            analysis_id=analysis_id, items=evidence_items
        )

        return {"analysis_id": analysis_id, "new_evidence": len(new_records)}

    async def refresh_from_saved(self, analysis_id: str) -> Dict:
        """Refresh using stored request snapshot (for scheduled jobs)."""
        record = await self.evidence_store.get_analysis(analysis_id)
        if not record:
            raise ValueError("Analysis not found")
        summary = record.get("summary", {})
        snapshot = summary.get("request")
        if not snapshot:
            raise ValueError("Request snapshot missing; cannot refresh")

        # Rehydrate request with minimal required fields; content is not needed for refresh
        snapshot.setdefault("content", "")
        req = ContentAnalysisRequest(**snapshot)
        return await self.refresh(analysis_id=analysis_id, request=req)

    async def _fetch_endpoint(self, endpoint: SourceEndpoint, request: ContentAnalysisRequest) -> Dict:
        """Dispatch to the right client call based on endpoint id."""
        try:
            if endpoint.source == SourceName.GOOGLE:
                if "my_business_info" in endpoint.endpoint:
                    return await self.client.google_my_business_info(request.google_cid, request.org_id)  # type: ignore
                if "my_business_updates" in endpoint.endpoint:
                    return await self.client.google_my_business_updates(request.google_cid, request.org_id)  # type: ignore
                if "reviews" in endpoint.endpoint and "hotel" not in endpoint.endpoint:
                    return await self.client.google_reviews(request.google_cid, request.org_id)  # type: ignore
                if "hotel_info" in endpoint.endpoint:
                    return await self.client.google_hotel_info(request.google_hotel_identifier, request.org_id)  # type: ignore
                if "hotel_searches" in endpoint.endpoint:
                    return await self.client.google_hotel_searches(request.entity_name or "", request.org_id)

            if endpoint.source == SourceName.TRIPADVISOR:
                if "search" in endpoint.endpoint:
                    return await self.client.tripadvisor_search(request.entity_name or "", None, request.org_id)
                if "reviews" in endpoint.endpoint:
                    return await self.client.tripadvisor_reviews(request.tripadvisor_url_path, request.org_id)  # type: ignore

            if endpoint.source == SourceName.TRUSTPILOT:
                if "search" in endpoint.endpoint:
                    return await self.client.trustpilot_search(request.entity_name or "", request.org_id)
                if "reviews" in endpoint.endpoint:
                    return await self.client.trustpilot_reviews(request.trustpilot_domain, request.org_id)  # type: ignore

            if endpoint.source == SourceName.SOCIAL:
                targets = [request.canonical_url] if request.canonical_url else []
                if not targets:
                    return {}
                if "facebook" in endpoint.endpoint:
                    return await self.client.social_facebook(targets, request.org_id)
                if "pinterest" in endpoint.endpoint:
                    return await self.client.social_pinterest(targets, request.org_id)
                if "reddit" in endpoint.endpoint:
                    return await self.client.social_reddit(targets, request.org_id)

            if endpoint.source == SourceName.CONTENT_ANALYSIS:
                keyword = request.entity_name or request.canonical_url or ""
                if not keyword:
                    return {}
                if "sentiment_analysis" in endpoint.endpoint:
                    return await self.client.sentiment_analysis(keyword, request.org_id)
                if "summary" in endpoint.endpoint:
                    return await self.client.summary(keyword, request.org_id)

            if endpoint.source == SourceName.MERCHANT:
                query = request.entity_name or ""
                if not query:
                    return {}
                if "merchant/google" in endpoint.endpoint:
                    return await self.client.merchant_google_products(query, request.org_id)
                if "merchant/amazon" in endpoint.endpoint:
                    return await self.client.merchant_amazon_products(query, request.org_id)

            if endpoint.source == SourceName.AI_OPTIMIZATION:
                # Placeholder: calling LLM Responses would require prompts; skip here
                return {}

            return {}
        except Exception as e:
            logger.error(f"Endpoint fetch failed for {endpoint.endpoint}: {e}")
            return {}

    def _has_identifiers(self, request: ContentAnalysisRequest, endpoint: SourceEndpoint) -> bool:
        """Ensure required identifier keys are present."""
        for key in endpoint.identifier_keys:
            if not getattr(request, key, None):
                return False
        return True

    def _entity_ref(self, request: ContentAnalysisRequest, endpoint: SourceEndpoint) -> Optional[str]:
        """Return a stable entity reference for evidence."""
        for key in endpoint.identifier_keys:
            val = getattr(request, key, None)
            if val:
                return str(val)
        return request.entity_name or None

