"""
Usage Logger Service

Tracks AI API usage to database for cost monitoring and analytics.
Logs all AI operations including tokens, costs, latency, and cache hits.
"""

import os
import logging
from typing import Optional, Dict, Any, List, Union
from datetime import datetime, timedelta
from decimal import Decimal

logger = logging.getLogger(__name__)

from ..monitoring.request_context import get_usage_attribution, UNKNOWN_BUCKET

# Try to import Supabase
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    create_client = None
    Client = None


class UsageLogger:
    """
    Log AI usage to database for cost monitoring and analytics.
    
    Stores usage data in Supabase with support for:
    - Per-organization tracking
    - Per-user tracking
    - Operation type breakdown
    - Model usage statistics
    - Cost calculations
    - Cache hit tracking
    """
    
    def __init__(
        self,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None,
        environment: Optional[str] = None,
        enabled: bool = True
    ):
        """
        Initialize usage logger.
        
        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase service role key
            environment: Environment name (dev/staging/prod)
            enabled: Whether logging is enabled
        """
        self.enabled = enabled
        self.environment = environment or os.getenv("ENVIRONMENT", "dev")
        
        if not SUPABASE_AVAILABLE:
            logger.warning("Supabase not installed. Usage logging disabled.")
            self.client = None
            self.enabled = False
            return
        
        supabase_url = supabase_url or os.getenv("SUPABASE_URL")
        supabase_key = supabase_key or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not supabase_url or not supabase_key:
            logger.warning("Supabase credentials not configured. Usage logging disabled.")
            self.client = None
            self.enabled = False
            return
        
        try:
            self.client: Client = create_client(supabase_url, supabase_key)
            logger.info(f"UsageLogger initialized for environment: {self.environment}")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            self.client = None
            self.enabled = False
    
    def _get_table_name(self, base_name: str) -> str:
        """Get environment-specific table name."""
        return f"{base_name}_{self.environment}"
    
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
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Log AI usage to database.
        
        Args:
            org_id: Organization ID
            user_id: User ID
            operation: Operation type (generation, polishing, quality_check, meta_tags)
            model: Model name used
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            cost_usd: Cost in USD
            latency_ms: Latency in milliseconds
            cached: Whether response was from cache
            metadata: Additional metadata
        
        Returns:
            Created record or None if logging failed
        """
        if not self.enabled or not self.client:
            return None
        
        try:
            # Prefer explicit metadata values; fallback to current request context.
            meta = metadata or {}
            usage_source = (meta.get("usage_source") or meta.get("x-usage-source") or "").strip()
            usage_client = (meta.get("usage_client") or meta.get("x-usage-client") or "").strip()
            request_id = (meta.get("request_id") or meta.get("x-request-id") or "").strip()

            if not usage_source or not usage_client or not request_id:
                ctx_attr = get_usage_attribution()
                usage_source = usage_source or ctx_attr.get("usage_source", UNKNOWN_BUCKET)
                usage_client = usage_client or ctx_attr.get("usage_client", UNKNOWN_BUCKET)
                request_id = request_id or ctx_attr.get("request_id", UNKNOWN_BUCKET)

            record = {
                "org_id": org_id,
                "user_id": user_id,
                "operation": operation,
                "model": model,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
                "cost_usd": cost_usd,
                "latency_ms": latency_ms,
                "cached": cached,
                # Persist attribution as first-class columns (bucket missing as "unknown")
                "usage_source": usage_source or UNKNOWN_BUCKET,
                "usage_client": usage_client or UNKNOWN_BUCKET,
                "request_id": request_id or UNKNOWN_BUCKET,
                # Also keep in metadata for backwards compatibility / older tables.
                "metadata": {**(meta or {}), "usage_source": usage_source or UNKNOWN_BUCKET, "usage_client": usage_client or UNKNOWN_BUCKET, "request_id": request_id or UNKNOWN_BUCKET},
                "created_at": datetime.utcnow().isoformat()
            }
            
            table_name = self._get_table_name("ai_usage_logs")
            try:
                result = self.client.table(table_name).insert(record).execute()
            except Exception as e:
                # If the DB table hasn't been migrated yet, retry without the new columns.
                msg = str(e).lower()
                if "usage_source" in msg or "usage_client" in msg or "request_id" in msg:
                    fallback_record = dict(record)
                    fallback_record.pop("usage_source", None)
                    fallback_record.pop("usage_client", None)
                    fallback_record.pop("request_id", None)
                    result = self.client.table(table_name).insert(fallback_record).execute()
                else:
                    raise
            
            if result.data:
                logger.debug(f"Logged usage: {operation}, {model}, {cost_usd} USD")
                return result.data[0]
            return None
            
        except Exception as e:
            # Don't raise - logging failures shouldn't break generation
            logger.error(f"Failed to log usage: {e}")
            return None
    
    async def get_usage_stats(
        self,
        org_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        group_by: str = "day"
    ) -> Dict[str, Any]:
        """
        Get usage statistics for an organization.
        
        Args:
            org_id: Organization ID
            start_date: Start of date range (defaults to 30 days ago)
            end_date: End of date range (defaults to now)
            group_by: Grouping period (day, week, month)
        
        Returns:
            Usage statistics with totals and breakdowns
        """
        if not self.enabled or not self.client:
            return {"error": "Usage logging not enabled"}
        
        try:
            # Default date range
            end_date = end_date or datetime.utcnow()
            start_date = start_date or (end_date - timedelta(days=30))
            
            table_name = self._get_table_name("ai_usage_logs")
            
            # Get all records in date range
            result = self.client.table(table_name)\
                .select("*")\
                .eq("org_id", org_id)\
                .gte("created_at", start_date.isoformat())\
                .lte("created_at", end_date.isoformat())\
                .execute()
            
            records = result.data or []
            
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
                    "daily_breakdown": []
                }
            
            # Calculate totals
            total_requests = len(records)
            total_tokens = sum(r.get("total_tokens", 0) for r in records)
            total_cost = sum(float(r.get("cost_usd", 0)) for r in records)
            cached_requests = sum(1 for r in records if r.get("cached", False))
            avg_latency = sum(r.get("latency_ms", 0) for r in records) / total_requests
            
            # Group by operation
            by_operation = {}
            for r in records:
                op = r.get("operation", "unknown")
                if op not in by_operation:
                    by_operation[op] = {"count": 0, "tokens": 0, "cost": 0}
                by_operation[op]["count"] += 1
                by_operation[op]["tokens"] += r.get("total_tokens", 0)
                by_operation[op]["cost"] += float(r.get("cost_usd", 0))
            
            # Group by model
            by_model = {}
            for r in records:
                model = r.get("model", "unknown")
                if model not in by_model:
                    by_model[model] = {"count": 0, "tokens": 0, "cost": 0}
                by_model[model]["count"] += 1
                by_model[model]["tokens"] += r.get("total_tokens", 0)
                by_model[model]["cost"] += float(r.get("cost_usd", 0))
            
            # Daily breakdown
            daily = {}
            for r in records:
                date_str = r.get("created_at", "")[:10]  # YYYY-MM-DD
                if date_str not in daily:
                    daily[date_str] = {"requests": 0, "tokens": 0, "cost": 0}
                daily[date_str]["requests"] += 1
                daily[date_str]["tokens"] += r.get("total_tokens", 0)
                daily[date_str]["cost"] += float(r.get("cost_usd", 0))
            
            daily_breakdown = [
                {"date": date, **data}
                for date, data in sorted(daily.items())
            ]

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
                    entry = grouped.setdefault(
                        k,
                        {"requests": 0, "total_cost": 0.0, "tokens": 0, "_latency_sum": 0},
                    )
                    entry["requests"] += 1
                    entry["total_cost"] += float(r.get("cost_usd", 0) or 0)
                    entry["tokens"] += int(r.get("total_tokens", 0) or 0)
                    entry["_latency_sum"] += int(r.get("latency_ms", 0) or 0)

                # Finalize averages + rounding
                for _, entry in grouped.items():
                    reqs = entry["requests"] or 0
                    entry["total_cost"] = round(entry["total_cost"], 6)
                    entry["avg_latency_ms"] = round((entry["_latency_sum"] / reqs), 2) if reqs else 0
                    entry.pop("_latency_sum", None)
                return grouped
            
            return {
                "org_id": org_id,
                "period_start": start_date.isoformat(),
                "period_end": end_date.isoformat(),
                "total_requests": total_requests,
                "total_tokens": total_tokens,
                "total_cost_usd": round(total_cost, 4),
                "cached_requests": cached_requests,
                "cache_hit_rate": round(cached_requests / total_requests * 100, 2) if total_requests > 0 else 0,
                "average_latency_ms": round(avg_latency, 2),
                "by_operation": by_operation,
                "by_model": by_model,
                "usage_by_source": _aggregate_by("usage_source"),
                "usage_by_client": _aggregate_by("usage_client"),
                "daily_breakdown": daily_breakdown
            }
            
        except Exception as e:
            logger.error(f"Failed to get usage stats: {e}")
            return {"error": str(e)}
    
    async def get_cost_breakdown(
        self,
        org_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get cost breakdown for an organization.
        
        Args:
            org_id: Organization ID
            days: Number of days to look back
        
        Returns:
            Cost breakdown by model and operation
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        stats = await self.get_usage_stats(org_id, start_date, end_date)
        
        if "error" in stats:
            return stats

        # Dashboard-friendly shape (plus existing fields for backward compatibility)
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
            # New preferred keys
            "org_id": org_id,
            "days": days,
            "total_cost": stats["total_cost_usd"],
            "by_source": by_source,
            "by_client": by_client,

            # Backward-compatible keys
            "period_days": days,
            "total_cost_usd": stats["total_cost_usd"],
            "cost_by_model": {
                model: round(data["cost"], 4)
                for model, data in stats.get("by_model", {}).items()
            },
            "cost_by_operation": {
                op: round(data["cost"], 4)
                for op, data in stats.get("by_operation", {}).items()
            },
            "daily_costs": [
                {"date": d["date"], "cost": round(d["cost"], 4)}
                for d in stats.get("daily_breakdown", [])
            ],
            "average_daily_cost": round(stats["total_cost_usd"] / max(days, 1), 4),
            "projected_monthly_cost": round(stats["total_cost_usd"] / max(days, 1) * 30, 2),
        }
    
    async def get_cache_stats(
        self,
        org_id: str,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Get cache performance statistics.
        
        Args:
            org_id: Organization ID
            days: Number of days to look back
        
        Returns:
            Cache hit rate and savings
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        stats = await self.get_usage_stats(org_id, start_date, end_date)
        
        if "error" in stats:
            return stats
        
        # Estimate savings from cache hits
        # Assume cached requests would have cost the same as average request
        total_requests = stats.get("total_requests", 0)
        cached_requests = stats.get("cached_requests", 0)
        total_cost = stats.get("total_cost_usd", 0)
        
        if total_requests > cached_requests and total_requests > 0:
            avg_cost_per_request = total_cost / (total_requests - cached_requests)
            estimated_savings = cached_requests * avg_cost_per_request
        else:
            avg_cost_per_request = 0
            estimated_savings = 0
        
        return {
            "org_id": org_id,
            "period_days": days,
            "total_requests": total_requests,
            "cached_requests": cached_requests,
            "cache_hit_rate": stats.get("cache_hit_rate", 0),
            "estimated_savings_usd": round(estimated_savings, 4),
            "average_cost_per_request": round(avg_cost_per_request, 6)
        }
    
    async def get_user_usage(
        self,
        org_id: str,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get usage statistics for a specific user.
        
        Args:
            org_id: Organization ID
            user_id: User ID
            days: Number of days to look back
        
        Returns:
            User-specific usage statistics
        """
        if not self.enabled or not self.client:
            return {"error": "Usage logging not enabled"}
        
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            table_name = self._get_table_name("ai_usage_logs")
            
            result = self.client.table(table_name)\
                .select("*")\
                .eq("org_id", org_id)\
                .eq("user_id", user_id)\
                .gte("created_at", start_date.isoformat())\
                .execute()
            
            records = result.data or []
            
            if not records:
                return {
                    "org_id": org_id,
                    "user_id": user_id,
                    "period_days": days,
                    "total_requests": 0,
                    "total_cost_usd": 0
                }
            
            return {
                "org_id": org_id,
                "user_id": user_id,
                "period_days": days,
                "total_requests": len(records),
                "total_tokens": sum(r.get("total_tokens", 0) for r in records),
                "total_cost_usd": round(sum(float(r.get("cost_usd", 0)) for r in records), 4),
                "by_operation": self._group_by_field(records, "operation"),
                "average_latency_ms": round(
                    sum(r.get("latency_ms", 0) for r in records) / len(records), 2
                )
            }
            
        except Exception as e:
            logger.error(f"Failed to get user usage: {e}")
            return {"error": str(e)}
    
    def _group_by_field(self, records: List[Dict], field: str) -> Dict[str, int]:
        """Group records by a field and count."""
        result = {}
        for r in records:
            value = r.get(field, "unknown")
            result[value] = result.get(value, 0) + 1
        return result


try:
    from .firestore_usage_logger import FirestoreUsageLogger
except Exception:
    FirestoreUsageLogger = None  # type: ignore


def _env_truthy(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in ("1", "true", "yes", "y", "on")


def _should_use_firestore() -> bool:
    """
    Decide whether to use Firestore as the source-of-truth for AI usage logging.

    Preference:
    - Explicit opt-in via env var
    - Otherwise fallback to Firestore if Supabase creds are not set but Firebase is available
    """
    if _env_truthy("FIRESTORE_USAGE_LOGGING_ENABLED") or _env_truthy("USE_FIRESTORE_USAGE_LOGGING"):
        return True

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if supabase_url and supabase_key:
        return False

    firebase_project = os.getenv("FIREBASE_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")
    return bool(firebase_project) and FirestoreUsageLogger is not None


# Singleton instance (SupabaseUsageLogger or FirestoreUsageLogger)
_logger_instance: Optional[Union["UsageLogger", "FirestoreUsageLogger"]] = None


def get_usage_logger():
    """Get singleton usage logger instance (Firestore preferred if configured)."""
    global _logger_instance
    if _logger_instance is None:
        if _should_use_firestore():
            _logger_instance = FirestoreUsageLogger()  # type: ignore
        else:
            _logger_instance = UsageLogger()
    return _logger_instance


def initialize_usage_logger(
    supabase_url: Optional[str] = None,
    supabase_key: Optional[str] = None,
    environment: Optional[str] = None
) :
    """Initialize and return usage logger with custom configuration (Supabase)."""
    global _logger_instance
    _logger_instance = UsageLogger(
        supabase_url=supabase_url,
        supabase_key=supabase_key,
        environment=environment
    )
    return _logger_instance
