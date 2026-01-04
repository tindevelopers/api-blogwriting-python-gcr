"""
Evidence store for DataForSEO-derived enrichment.

Persists Analyses and Evidence in Supabase when available, with a Redis/memory
cache to avoid re-fetching unchanged inputs. Falls back to in-memory storage if
Supabase is not configured.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from uuid import uuid4

from ..cache.redis_cache import CacheManager
from ..integrations.supabase_client import SupabaseClient
from ..models.content_routing_models import AnalysisRecord, EvidenceRecord

logger = logging.getLogger(__name__)


def _hash_payload(payload: Dict) -> str:
    """Stable hash for payload deduplication."""
    return hashlib.sha256(str(payload).encode("utf-8")).hexdigest()


class EvidenceStore:
    """
    Persistence layer for analyses and evidence with caching.
    """

    def __init__(
        self,
        supabase: Optional[SupabaseClient] = None,
        cache: Optional[CacheManager] = None,
        environment: str = "dev",
    ):
        self.supabase = supabase
        self.cache = cache or CacheManager(default_ttl=3600)
        self.environment = environment
        self._mem_analyses: Dict[str, Dict] = {}
        self._mem_evidence: Dict[str, Dict] = {}

    # ------------------------------------------------------------------ #
    # Analysis helpers
    # ------------------------------------------------------------------ #

    async def save_analysis(
        self,
        content_id: str,
        org_id: str,
        content_hash: str,
        content_category: str,
        entity_type: Optional[str],
        summary: Dict,
        config_version: str = "1.0",
        analysis_id: Optional[str] = None,
    ) -> AnalysisRecord:
        """Persist an analysis and cache it."""
        analysis_id = analysis_id or str(uuid4())
        record = AnalysisRecord(
            analysis_id=analysis_id,
            content_id=content_id,
            org_id=org_id,
            content_hash=content_hash,
            content_category=content_category,
            entity_type=entity_type,
            summary=summary,
            created_at=datetime.utcnow().isoformat(),
            config_version=config_version,
        )

        # Cache
        await self.cache.set(
            key=self._cache_key("analysis", analysis_id),
            value=record.model_dump(),
            cache_type="dataforseo_result",
        )

        # Supabase (best-effort)
        if self.supabase:
            try:
                table = self.supabase._get_table_name("content_analyses")  # type: ignore
                self.supabase.client.table(table).insert(record.model_dump()).execute()
            except Exception as e:
                logger.warning(f"Supabase save_analysis failed: {e}")
        else:
            self._mem_analyses[analysis_id] = record.model_dump()

        return record

    async def get_analysis(self, analysis_id: str) -> Optional[Dict]:
        """Fetch analysis by id (cache → Supabase → memory)."""
        cached = await self.cache.get(self._cache_key("analysis", analysis_id))
        if cached:
            return cached

        if self.supabase:
            try:
                table = self.supabase._get_table_name("content_analyses")  # type: ignore
                result = (
                    self.supabase.client.table(table)
                    .select("*")
                    .eq("analysis_id", analysis_id)
                    .limit(1)
                    .execute()
                )
                if result.data:
                    record = result.data[0]
                    await self.cache.set(
                        self._cache_key("analysis", analysis_id),
                        record,
                        cache_type="dataforseo_result",
                    )
                    return record
            except Exception as e:
                logger.warning(f"Supabase get_analysis failed: {e}")

        return self._mem_analyses.get(analysis_id)

    async def list_analyses(self, limit: int = 100) -> List[Dict]:
        """List stored analyses for monitoring."""
        if self.supabase:
            try:
                table = self.supabase._get_table_name("content_analyses")  # type: ignore
                result = (
                    self.supabase.client.table(table)
                    .select("*")
                    .order("created_at", desc=True)
                    .limit(limit)
                    .execute()
                )
                return result.data or []
            except Exception as e:
                logger.warning(f"Supabase list_analyses failed: {e}")

        # memory fallback (unsorted)
        return list(self._mem_analyses.values())[:limit]

    # ------------------------------------------------------------------ #
    # Evidence helpers
    # ------------------------------------------------------------------ #

    async def save_evidence_batch(
        self,
        analysis_id: str,
        items: List[Tuple[str, str, Optional[str], Dict]],
    ) -> List[EvidenceRecord]:
        """
        Save a batch of evidence.

        items: list of (source, endpoint, entity_ref, payload)
        """
        results: List[EvidenceRecord] = []
        if not items:
            return results

        rows = []
        for source, endpoint, entity_ref, payload in items:
            evidence_id = str(uuid4())
            payload_hash = _hash_payload(payload)
            row = EvidenceRecord(
                evidence_id=evidence_id,
                analysis_id=analysis_id,
                source=source,
                endpoint=endpoint,
                entity_ref=entity_ref,
                payload=payload,
                payload_hash=payload_hash,
                fetched_at=datetime.utcnow().isoformat(),
            )
            rows.append(row)
            results.append(row)

        # Cache hashes to avoid duplicates
        for row in rows:
            cache_key = self._cache_key("evidence", f"{row.source}:{row.payload_hash}")
            await self.cache.set(cache_key, row.model_dump(), cache_type="dataforseo_result")

        # Supabase best-effort
        if self.supabase:
            try:
                table = self.supabase._get_table_name("content_evidence")  # type: ignore
                payload = [r.model_dump() for r in rows]
                self.supabase.client.table(table).insert(payload).execute()
            except Exception as e:
                logger.warning(f"Supabase save_evidence_batch failed: {e}")
        else:
            for row in rows:
                self._mem_evidence[row.evidence_id] = row.model_dump()

        return results

    async def list_evidence(self, analysis_id: str) -> List[Dict]:
        """Return evidence for an analysis."""
        # No cache to keep it simple; Supabase first
        if self.supabase:
            try:
                table = self.supabase._get_table_name("content_evidence")  # type: ignore
                result = (
                    self.supabase.client.table(table)
                    .select("*")
                    .eq("analysis_id", analysis_id)
                    .execute()
                )
                if result.data:
                    return result.data
            except Exception as e:
                logger.warning(f"Supabase list_evidence failed: {e}")

        return [v for v in self._mem_evidence.values() if v["analysis_id"] == analysis_id]

    async def is_payload_seen(self, source: str, payload: Dict) -> bool:
        """Check if payload hash already cached to avoid re-fetch."""
        payload_hash = _hash_payload(payload)
        cache_key = self._cache_key("evidence", f"{source}:{payload_hash}")
        cached = await self.cache.get(cache_key)
        return cached is not None

    # ------------------------------------------------------------------ #
    # Utilities
    # ------------------------------------------------------------------ #

    def _cache_key(self, prefix: str, key: str) -> str:
        return f"content:{prefix}:{key}"


async def run_in_thread(fn, *args, **kwargs):
    """Utility to offload blocking DB calls."""
    return await asyncio.to_thread(fn, *args, **kwargs)

