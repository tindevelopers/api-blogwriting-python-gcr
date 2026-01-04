"""
Bi-weekly monitoring helper that refreshes content analyses and captures deltas.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from .content_analysis_service import ContentAnalysisService

logger = logging.getLogger(__name__)


async def run_biweekly_monitoring(
    service: ContentAnalysisService,
    limit: int = 100,
) -> Dict[str, int]:
    """
    Refresh recent analyses to pick up new reviews/social/sentiment.

    Returns a summary with counts of attempted/updated.
    """
    analyses = await service.evidence_store.list_analyses(limit=limit)
    attempted = 0
    updated = 0

    for record in analyses:
        analysis_id = record.get("analysis_id")
        if not analysis_id:
            continue
        attempted += 1
        try:
            refresh_result = await service.refresh_from_saved(analysis_id)
            updated += int(refresh_result.get("new_evidence", 0) > 0)
        except Exception as e:
            logger.warning(f"Bi-weekly refresh failed for {analysis_id}: {e}")

    return {"attempted": attempted, "updated": updated}

