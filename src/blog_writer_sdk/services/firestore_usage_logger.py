"""
Firestore-backed AI Usage Logger.

This is used when Supabase is not configured/available and Firebase Admin SDK
credentials are present (e.g., Cloud Run service account).
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..monitoring.request_context import UNKNOWN_BUCKET, get_usage_attribution

try:
    # Reuse existing Firebase initialization patterns in the codebase
    from ..integrations.firebase_config_client import get_firebase_config_client, FIREBASE_AVAILABLE
    from firebase_admin import firestore  # type: ignore
    from google.cloud.firestore_v1.base_query import FieldFilter  # type: ignore
except Exception:
    FIREBASE_AVAILABLE = False
    firestore = None  # type: ignore
    FieldFilter = None  # type: ignore
    get_firebase_config_client = None  # type: ignore

logger = logging.getLogger(__name__)


class FirestoreUsageLogger:
    """
    Log AI usage to Firestore for cost monitoring and analytics.
    """

    def __init__(
        self,
        project_id: Optional[str] = None,
        environment: Optional[str] = None,
        enabled: bool = True,
        collection_base: str = "ai_usage_logs",
    ):
        self.environment = environment or os.getenv("ENVIRONMENT", "dev")
        self.project_id = project_id or os.getenv("FIREBASE_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")
        self.collection_base = collection_base
        self.enabled = enabled and bool(self.project_id) and bool(FIREBASE_AVAILABLE)

        self.db = None
        if self.enabled:
            try:
                self.db = get_firebase_config_client().db  # initializes firebase_admin if needed
                logger.info(
                    f"FirestoreUsageLogger initialized (project={self.project_id}, env={self.environment}, collection={self.collection_name})"
                )
            except Exception as e:
                logger.warning(f"Failed to initialize Firestore client: {e}")
                self.enabled = False
                self.db = None

    @property
    def collection_name(self) -> str:
        return f"{self.collection_base}_{self.environment}"

    def _attr_from_meta_or_ctx(self, metadata: Optional[Dict[str, Any]]) -> Dict[str, str]:
        meta = metadata or {}
        usage_source = (meta.get("usage_source") or meta.get("x-usage-source") or "").strip()
        usage_client = (meta.get("usage_client") or meta.get("x-usage-client") or "").strip()
        request_id = (meta.get("request_id") or meta.get("x-request-id") or "").strip()

        if not usage_source or not usage_client or not request_id:
            ctx = get_usage_attribution()
            usage_source = usage_source or ctx.get("usage_source", UNKNOWN_BUCKET)
            usage_client = usage_client or ctx.get("usage_client", UNKNOWN_BUCKET)
            request_id = request_id or ctx.get("request_id", UNKNOWN_BUCKET)

        return {
            "usage_source": usage_source or UNKNOWN_BUCKET,
            "usage_client": usage_client or UNKNOWN_BUCKET,
            "request_id": request_id or UNKNOWN_BUCKET,
        }

    async def log_usage(
        self,
        org_id: str,
        user_id: str,
        operation: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        cost_usd: float,
        latency_ms: int,
        cached: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        if not self.enabled or not self.db:
            return None

        try:
            attr = self._attr_from_meta_or_ctx(metadata)
            created_at = datetime.utcnow()
            total_tokens = int(prompt_tokens or 0) + int(completion_tokens or 0)

            doc = {
                "org_id": org_id,
                "user_id": user_id,
                "operation": operation,
                "model": model,
                "prompt_tokens": int(prompt_tokens or 0),
                "completion_tokens": int(completion_tokens or 0),
                "total_tokens": total_tokens,
                "cost_usd": float(cost_usd or 0.0),
                "latency_ms": int(latency_ms or 0),
                "cached": bool(cached),
                **attr,
                "metadata": {**(metadata or {}), **attr},
                "created_at": created_at,
                # also store server timestamp for consistency across writers
                "created_at_server": firestore.SERVER_TIMESTAMP if firestore else None,
            }

            doc_ref = self.db.collection(self.collection_name).document()
            doc_ref.set(doc)
            return {"id": doc_ref.id, **doc}
        except Exception as e:
            logger.error(f"Failed to log usage to Firestore: {e}")
            return None

    async def _fetch_records(
        self,
        org_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> List[Dict[str, Any]]:
        if not self.enabled or not self.db:
            return []

        try:
            col = self.db.collection(self.collection_name)
            # Prefer created_at (client timestamp) for range queries.
            q = (
                col.where(filter=FieldFilter("org_id", "==", org_id))
                .where(filter=FieldFilter("created_at", ">=", start_date))
                .where(filter=FieldFilter("created_at", "<=", end_date))
            )
            return [doc.to_dict() for doc in q.stream()]
        except Exception as e:
            logger.error(f"Failed to fetch Firestore usage records: {e}")
            return []

    async def get_usage_stats(
        self,
        org_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        group_by: str = "day",
    ) -> Dict[str, Any]:
        if not self.enabled or not self.db:
            return {"error": "Usage logging not enabled"}

        end_date = end_date or datetime.utcnow()
        start_date = start_date or (end_date - timedelta(days=30))

        records = await self._fetch_records(org_id=org_id, start_date=start_date, end_date=end_date)

        if not records:
            return {
                "org_id": org_id,
                "period_start": start_date.isoformat(),
                "period_end": end_date.isoformat(),
                "total_requests": 0,
                "total_tokens": 0,
                "total_cost_usd": 0,
                "cached_requests": 0,
                "cache_hit_rate": 0,
                "by_operation": {},
                "by_model": {},
                "usage_by_source": {},
                "usage_by_client": {},
                "daily_breakdown": [],
            }

        total_requests = len(records)
        total_tokens = sum(int(r.get("total_tokens", 0) or 0) for r in records)
        total_cost = sum(float(r.get("cost_usd", 0) or 0) for r in records)
        cached_requests = sum(1 for r in records if r.get("cached", False))
        avg_latency = sum(int(r.get("latency_ms", 0) or 0) for r in records) / max(total_requests, 1)

        by_operation: Dict[str, Dict[str, Any]] = {}
        for r in records:
            op = (r.get("operation") or "unknown").strip() if isinstance(r.get("operation"), str) else (r.get("operation") or "unknown")
            by_operation.setdefault(op, {"count": 0, "tokens": 0, "cost": 0.0})
            by_operation[op]["count"] += 1
            by_operation[op]["tokens"] += int(r.get("total_tokens", 0) or 0)
            by_operation[op]["cost"] += float(r.get("cost_usd", 0) or 0)

        by_model: Dict[str, Dict[str, Any]] = {}
        for r in records:
            model = (r.get("model") or "unknown").strip() if isinstance(r.get("model"), str) else (r.get("model") or "unknown")
            by_model.setdefault(model, {"count": 0, "tokens": 0, "cost": 0.0})
            by_model[model]["count"] += 1
            by_model[model]["tokens"] += int(r.get("total_tokens", 0) or 0)
            by_model[model]["cost"] += float(r.get("cost_usd", 0) or 0)

        daily: Dict[str, Dict[str, Any]] = {}
        for r in records:
            created_at = r.get("created_at")
            if isinstance(created_at, datetime):
                date_str = created_at.date().isoformat()
            else:
                # fallback: try iso string
                date_str = str(created_at)[:10] if created_at else "unknown"
            daily.setdefault(date_str, {"requests": 0, "tokens": 0, "cost": 0.0})
            daily[date_str]["requests"] += 1
            daily[date_str]["tokens"] += int(r.get("total_tokens", 0) or 0)
            daily[date_str]["cost"] += float(r.get("cost_usd", 0) or 0)

        daily_breakdown = [{"date": d, **data} for d, data in sorted(daily.items())]

        def _attr_value(r: Dict[str, Any], key: str) -> str:
            value = r.get(key)
            if not value and isinstance(r.get("metadata"), dict):
                value = r["metadata"].get(key)
            if value is None:
                return UNKNOWN_BUCKET
            if not isinstance(value, str):
                value = str(value)
            value = value.strip()
            return value or UNKNOWN_BUCKET

        def _aggregate_by(key: str) -> Dict[str, Any]:
            grouped: Dict[str, Dict[str, Any]] = {}
            for r in records:
                k = _attr_value(r, key)
                entry = grouped.setdefault(k, {"requests": 0, "total_cost": 0.0, "tokens": 0, "_lat_sum": 0})
                entry["requests"] += 1
                entry["total_cost"] += float(r.get("cost_usd", 0) or 0)
                entry["tokens"] += int(r.get("total_tokens", 0) or 0)
                entry["_lat_sum"] += int(r.get("latency_ms", 0) or 0)
            for _, entry in grouped.items():
                reqs = entry["requests"] or 0
                entry["total_cost"] = round(entry["total_cost"], 6)
                entry["avg_latency_ms"] = round(entry["_lat_sum"] / reqs, 2) if reqs else 0
                entry.pop("_lat_sum", None)
            return grouped

        return {
            "org_id": org_id,
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "total_requests": total_requests,
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost, 4),
            "cached_requests": cached_requests,
            "cache_hit_rate": round(cached_requests / total_requests * 100, 2) if total_requests else 0,
            "average_latency_ms": round(avg_latency, 2),
            "by_operation": by_operation,
            "by_model": by_model,
            "usage_by_source": _aggregate_by("usage_source"),
            "usage_by_client": _aggregate_by("usage_client"),
            "daily_breakdown": daily_breakdown,
        }

    async def get_cost_breakdown(self, org_id: str, days: int = 30) -> Dict[str, Any]:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        stats = await self.get_usage_stats(org_id=org_id, start_date=start_date, end_date=end_date)
        if "error" in stats:
            return stats

        by_source = {
            source: {
                "total_cost": round(data.get("total_cost", 0.0), 6),
                "requests": int(data.get("requests", 0)),
                "tokens": int(data.get("tokens", 0)),
            }
            for source, data in (stats.get("usage_by_source", {}) or {}).items()
        }
        by_client = {
            client: {
                "total_cost": round(data.get("total_cost", 0.0), 6),
                "requests": int(data.get("requests", 0)),
                "tokens": int(data.get("tokens", 0)),
            }
            for client, data in (stats.get("usage_by_client", {}) or {}).items()
        }

        return {
            "org_id": org_id,
            "days": days,
            "total_cost": stats.get("total_cost_usd", 0),
            "by_source": by_source,
            "by_client": by_client,
        }

    async def get_cache_stats(self, org_id: str, days: int = 7) -> Dict[str, Any]:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        stats = await self.get_usage_stats(org_id=org_id, start_date=start_date, end_date=end_date)
        if "error" in stats:
            return stats

        total_requests = int(stats.get("total_requests", 0) or 0)
        cached_requests = int(stats.get("cached_requests", 0) or 0)
        total_cost = float(stats.get("total_cost_usd", 0) or 0)

        if total_requests > cached_requests and total_requests > 0:
            avg_cost_per_request = total_cost / (total_requests - cached_requests)
            estimated_savings = cached_requests * avg_cost_per_request
        else:
            avg_cost_per_request = 0.0
            estimated_savings = 0.0

        return {
            "org_id": org_id,
            "period_days": days,
            "total_requests": total_requests,
            "cached_requests": cached_requests,
            "cache_hit_rate": stats.get("cache_hit_rate", 0),
            "estimated_savings_usd": round(estimated_savings, 4),
            "average_cost_per_request": round(avg_cost_per_request, 6),
        }


