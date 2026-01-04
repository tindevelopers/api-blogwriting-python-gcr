"""
Request context utilities (usage attribution).

Captures and stores per-request attribution fields so downstream services
can log usage with correct source/client/request_id without threading params.
"""

from __future__ import annotations

from contextvars import ContextVar
from typing import Any, Dict, Mapping, Optional

UNKNOWN_BUCKET = "unknown"

_request_ctx: ContextVar[Dict[str, Any]] = ContextVar("blogwriter_request_ctx", default={})


def _norm(value: Optional[str]) -> str:
    if value is None:
        return UNKNOWN_BUCKET
    if not isinstance(value, str):
        value = str(value)
    value = value.strip()
    return value or UNKNOWN_BUCKET


def set_usage_attribution(
    *,
    usage_source: Optional[str] = None,
    usage_client: Optional[str] = None,
    request_id: Optional[str] = None,
) -> None:
    """
    Set (or overwrite) attribution values in the current request context.
    """
    ctx = dict(_request_ctx.get() or {})
    ctx["usage_source"] = _norm(usage_source)
    ctx["usage_client"] = _norm(usage_client)
    ctx["request_id"] = _norm(request_id)
    _request_ctx.set(ctx)


def set_usage_attribution_from_headers(headers: Mapping[str, str]) -> None:
    """
    Extract attribution headers and store them in the request context.
    """
    # Header keys are case-insensitive, but FastAPI's headers mapping normalizes them.
    usage_source = headers.get("x-usage-source")
    usage_client = headers.get("x-usage-client")
    request_id = headers.get("x-request-id")
    set_usage_attribution(
        usage_source=usage_source,
        usage_client=usage_client,
        request_id=request_id,
    )


def get_usage_attribution() -> Dict[str, str]:
    """
    Get attribution values for the current request context (with 'unknown' defaults).
    """
    ctx = _request_ctx.get() or {}
    return {
        "usage_source": _norm(ctx.get("usage_source")),
        "usage_client": _norm(ctx.get("usage_client")),
        "request_id": _norm(ctx.get("request_id")),
    }


