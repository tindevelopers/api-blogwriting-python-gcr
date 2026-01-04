"""
API router for category-based content analysis/enrichment.
"""

from __future__ import annotations

import logging
import os
from fastapi import APIRouter, Depends, HTTPException

from ..integrations.supabase_client import SupabaseClient
from ..services.content_analysis_service import ContentAnalysisService
from ..services.evidence_store import EvidenceStore
from ..models.content_routing_models import ContentAnalysisRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/content", tags=["Content Analysis"])


def get_supabase_optional() -> SupabaseClient | None:
    try:
        return SupabaseClient()
    except Exception as e:
        logger.debug(f"Supabase not configured: {e}")
        return None


def get_content_analysis_service() -> ContentAnalysisService:
    supabase = get_supabase_optional()
    evidence_store = EvidenceStore(supabase=supabase)
    return ContentAnalysisService(evidence_store=evidence_store)


@router.post("/analyze")
async def analyze_content(
    request: ContentAnalysisRequest,
    service: ContentAnalysisService = Depends(get_content_analysis_service),
):
    """
    Run category-based enrichment and persist evidence for reuse.
    """
    try:
        result = await service.analyze(request)
        return result
    except Exception as e:
        logger.error(f"Analyze failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh")
async def refresh_sources(
    analysis_id: str,
    request: ContentAnalysisRequest,
    service: ContentAnalysisService = Depends(get_content_analysis_service),
):
    """
    Refresh evidence for an existing analysis (bi-weekly monitoring hook).
    """
    try:
        result = await service.refresh(analysis_id, request)
        return result
    except Exception as e:
        logger.error(f"Refresh failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/{analysis_id}")
async def get_analysis(
    analysis_id: str,
    service: ContentAnalysisService = Depends(get_content_analysis_service),
):
    """Retrieve stored analysis + evidence list."""
    record = await service.evidence_store.get_analysis(analysis_id)
    if not record:
        raise HTTPException(status_code=404, detail="Analysis not found")
    evidence = await service.evidence_store.list_evidence(analysis_id)
    return {"analysis": record, "evidence": evidence}

