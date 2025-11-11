from typing import Any, Dict, List, Optional
import os
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from ..models.integration_models import (
    IntegrationConnectAndRecommendRequest,
    IntegrationRecommendationResponse,
    KeywordRecommendation,
    ContentSystemProvider,
)
from ..integrations.supabase_client import SupabaseClient
from .. import BlogWriter


router = APIRouter(prefix="/api/v1/integrations", tags=["Integrations"])


def get_supabase_safe() -> Optional[SupabaseClient]:
    try:
        return SupabaseClient()
    except Exception:
        return None


def get_writer_dependency() -> BlogWriter:
    from ...blog_writer_sdk import BlogWriter as _BW
    # Import from main singleton if available; fallback to a minimal instance if not
    try:
        from main import get_blog_writer  # type: ignore
        return get_blog_writer()
    except Exception:
        return _BW(enable_seo_optimization=True, enable_quality_analysis=True)


@router.post("/connect-and-recommend", response_model=IntegrationRecommendationResponse)
async def connect_and_recommend(
    request: IntegrationConnectAndRecommendRequest,
    writer: BlogWriter = Depends(get_writer_dependency),
):
    if not request.keywords:
        raise HTTPException(status_code=400, detail="At least one keyword is required")

    # Persist (best-effort) integration metadata in Supabase
    saved = False
    sb = get_supabase_safe()
    if sb:
        try:
            env = os.getenv("ENVIRONMENT", "dev")
            table = f"integrations_{env}"
            record: Dict[str, Any] = {
                "tenant_id": request.tenant_id,
                "provider": request.provider.value,
                "connection": request.connection,
            }
            # best-effort insert; ignore missing table errors
            sb.client.table(table).insert(record).execute()
            saved = True
        except Exception:
            saved = False

    # Compute recommendations using enhanced analyzer if available, else heuristics
    per_keyword: List[KeywordRecommendation] = []

    def heuristic(keyword: str) -> KeywordRecommendation:
        base = max(1, min(10, len(keyword.split())))
        # simple scaling
        backlinks = max(1, int(base * 2))
        interlinks = max(1, int(base * 3))
        return KeywordRecommendation(
            keyword=keyword,
            difficulty=None,
            suggested_backlinks=backlinks,
            suggested_interlinks=interlinks,
        )

    analyzer = getattr(writer, "keyword_analyzer", None)
    use_enhanced = hasattr(analyzer, "analyze_keyword")

    for kw in request.keywords:
        kw_norm = kw.strip()
        if not kw_norm:
            continue
        try:
            if use_enhanced:
                analysis = await analyzer.analyze_keyword(kw_norm)  # type: ignore
                difficulty = float(analysis.get("difficulty", 0.5)) if isinstance(analysis, dict) else None
                # scale recommendations: more difficult => more backlinks/interlinks
                factor = 1.0 + (difficulty if difficulty is not None else 0.5)
                backlinks = max(1, int(3 * factor))
                interlinks = max(1, int(5 * factor))
                per_keyword.append(
                    KeywordRecommendation(
                        keyword=kw_norm,
                        difficulty=difficulty,
                        suggested_backlinks=backlinks,
                        suggested_interlinks=interlinks,
                    )
                )
            else:
                per_keyword.append(heuristic(kw_norm))
        except Exception:
            per_keyword.append(heuristic(kw_norm))

    # Aggregate totals (mean rounded up)
    total_backlinks = sum(k.suggested_backlinks for k in per_keyword)
    total_interlinks = sum(k.suggested_interlinks for k in per_keyword)
    n = max(1, len(per_keyword))
    recommended_backlinks = max(1, int(round(total_backlinks / n)))
    recommended_interlinks = max(1, int(round(total_interlinks / n)))

    notes = None
    if request.provider == ContentSystemProvider.wordpress:
        notes = "WordPress integration not currently installed on the backend; recommendations still computed."

    # Persist recommendations (best-effort) into recommendations_{env}
    if sb:
        try:
            env = os.getenv("ENVIRONMENT", "dev")
            rec_table = f"recommendations_{env}"
            rec_record = {
                "tenant_id": request.tenant_id,
                "provider": request.provider.value,
                "keywords": request.keywords,
                "recommended_backlinks": recommended_backlinks,
                "recommended_interlinks": recommended_interlinks,
                "per_keyword": [k.model_dump() for k in per_keyword],
                "notes": notes,
            }
            sb.client.table(rec_table).insert(rec_record).execute()
        except Exception:
            # Ignore persistence failures; endpoint remains target-agnostic
            pass

    return IntegrationRecommendationResponse(
        provider=request.provider,
        tenant_id=request.tenant_id,
        saved_integration=saved,
        recommended_backlinks=recommended_backlinks,
        recommended_interlinks=recommended_interlinks,
        per_keyword=per_keyword,
        notes=notes,
    )


