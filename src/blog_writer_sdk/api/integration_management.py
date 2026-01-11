from typing import Any, Dict, List, Optional, Tuple
import os
import logging
from fastapi import APIRouter, HTTPException, Depends

from ..models.integration_models import (
    IntegrationConnectAndRecommendRequest,
    IntegrationRecommendationResponse,
    KeywordRecommendation,
    ContentSystemProvider,
    ConnectAndRecommendRequest,
    ConnectAndRecommendResponse,
    KeywordInterlinkAnalysis,
    InterlinkOpportunity,
)
from ..seo.interlinking_analyzer import InterlinkingAnalyzer
from ..integrations.supabase_client import SupabaseClient
from .. import BlogWriter

logger = logging.getLogger(__name__)


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


def validate_structure(structure: Optional[Dict[str, Any]]) -> Tuple[bool, str]:
    """Validate structure and return (is_valid, error_message)."""
    if not structure:
        return False, "Structure is required"
    
    if 'existing_content' not in structure:
        return False, "Structure must contain existing_content"
    
    if not isinstance(structure['existing_content'], list):
        return False, "existing_content must be an array"
    
    if len(structure['existing_content']) == 0:
        return False, "existing_content cannot be empty"
    
    # Validate each content item
    required_fields = ['id', 'title', 'url', 'keywords']
    for i, item in enumerate(structure['existing_content']):
        for field in required_fields:
            if field not in item:
                return False, f"Content item {i} missing required field: {field}"
    
    return True, ""


@router.post("/connect-and-recommend", response_model=IntegrationRecommendationResponse)
async def connect_and_recommend(
    request: IntegrationConnectAndRecommendRequest,
    writer: BlogWriter = Depends(get_writer_dependency),
):
    """
    Connect to a content provider and recommend interlinking opportunities.
    
    This endpoint supports both legacy format (without structure) and new format (with structure).
    When structure is provided, it uses the interlinking analyzer to find actual opportunities.
    """
    if not request.keywords:
        raise HTTPException(status_code=400, detail="At least one keyword is required")
    
    if len(request.keywords) < 1 or len(request.keywords) > 50:
        raise HTTPException(
            status_code=400,
            detail="Keywords array must contain 1-50 keywords"
        )

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
        except Exception as e:
            logger.debug(f"Failed to save integration to Supabase: {e}")
            saved = False

    # Check if structure is provided in connection
    structure = request.connection.get('structure')
    existing_content = None
    
    if structure:
        # Validate structure
        is_valid, error_message = validate_structure(structure)
        if not is_valid:
            logger.warning(f"Invalid structure provided: {error_message}")
            # Fall back to heuristic method
            structure = None
        else:
            existing_content = structure.get('existing_content', [])
    
    # Use interlinking analyzer if structure is provided
    if existing_content and len(existing_content) > 0:
        try:
            logger.info(f"Using interlinking analyzer with {len(existing_content)} existing content items")
            interlinking_analyzer = InterlinkingAnalyzer()
            
            # Get interlinking settings from request (if provided)
            interlinking_settings = request.interlinking_settings
            
            # Analyze interlinking opportunities
            analysis_result = interlinking_analyzer.analyze_interlinking_opportunities(
                keywords=request.keywords,
                existing_content=existing_content,
                settings=interlinking_settings
            )
            
            # Convert to response format
            per_keyword: List[KeywordRecommendation] = []
            
            # Get keyword difficulty if available
            analyzer = getattr(writer, "keyword_analyzer", None)
            use_enhanced = hasattr(analyzer, "analyze_keyword")
            
            for kw_result in analysis_result['per_keyword']:
                keyword = kw_result['keyword']
                difficulty = None
                
                # Try to get difficulty from enhanced analyzer
                if use_enhanced:
                    try:
                        analysis = await analyzer.analyze_keyword(keyword)  # type: ignore
                        difficulty = float(analysis.get("difficulty", 0.5)) if isinstance(analysis, dict) else None
                    except Exception:
                        pass
                
                # Convert interlink opportunities to legacy format
                # Note: We're keeping the legacy response format but could enhance it later
                per_keyword.append(
                    KeywordRecommendation(
                        keyword=keyword,
                        difficulty=difficulty,
                        suggested_backlinks=0,  # Backlinks not implemented yet
                        suggested_interlinks=kw_result['suggested_interlinks'],
                    )
                )
            
            recommended_interlinks = analysis_result['recommended_interlinks']
            recommended_backlinks = 0
            
            notes = f"Found {recommended_interlinks} interlinking opportunities from {len(existing_content)} existing content items"
            if request.provider == ContentSystemProvider.wordpress:
                notes += ". WordPress integration not currently installed on the backend; recommendations still computed."
            
        except Exception as e:
            logger.error(f"Interlinking analysis failed: {e}", exc_info=True)
            # Fall back to heuristic method
            structure = None
    
    # Fallback to heuristic method if no structure or analysis failed
    if not existing_content or len(existing_content) == 0:
        logger.info("Using heuristic method for recommendations (no structure provided)")
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
        provider=request.provider.value if isinstance(request.provider, ContentSystemProvider) else request.provider,
        tenant_id=request.tenant_id,
        saved_integration=saved,
        recommended_backlinks=recommended_backlinks,
        recommended_interlinks=recommended_interlinks,
        per_keyword=per_keyword,
        notes=notes,
    )


@router.post("/connect-and-recommend-v2", response_model=ConnectAndRecommendResponse)
async def connect_and_recommend_v2(
    request: ConnectAndRecommendRequest,
):
    """
    Enhanced connect and recommend endpoint with full interlinking analysis.
    
    This endpoint uses the interlinking analyzer to find actual opportunities
    from existing content structure.
    """
    # Validate keywords
    if not request.keywords or len(request.keywords) == 0:
        raise HTTPException(status_code=400, detail="At least one keyword is required")
    
    if len(request.keywords) > 50:
        raise HTTPException(status_code=400, detail="Keywords array must contain at most 50 keywords")
    
    # Extract structure from connection
    structure = request.connection.get('structure')
    
    if not structure:
        raise HTTPException(
            status_code=400,
            detail="Structure with existing_content is required for interlinking analysis"
        )
    
    # Validate structure
    is_valid, error_message = validate_structure(structure)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_message)
    
    existing_content = structure.get('existing_content', [])
    
    if len(existing_content) == 0:
        raise HTTPException(
            status_code=400,
            detail="existing_content array cannot be empty"
        )
    
    # Persist (best-effort) integration metadata in Supabase
    saved = False
    sb = get_supabase_safe()
    if sb:
        try:
            env = os.getenv("ENVIRONMENT", "dev")
            table = f"integrations_{env}"
            record: Dict[str, Any] = {
                "tenant_id": request.tenant_id,
                "provider": request.provider,
                "connection": request.connection,
            }
            sb.client.table(table).insert(record).execute()
            saved = True
        except Exception as e:
            logger.debug(f"Failed to save integration to Supabase: {e}")
            saved = False
    
    # Use interlinking analyzer
    try:
        logger.info(f"Analyzing interlinking opportunities for {len(request.keywords)} keywords against {len(existing_content)} content items")
        interlinking_analyzer = InterlinkingAnalyzer()
        
        # Get interlinking settings from request (if provided)
        interlinking_settings = request.interlinking_settings
        
        # Analyze interlinking opportunities
        analysis_result = interlinking_analyzer.analyze_interlinking_opportunities(
            keywords=request.keywords,
            existing_content=existing_content,
            settings=interlinking_settings
        )
        
        # Convert to response format with full interlink opportunities
        per_keyword: List[KeywordInterlinkAnalysis] = []
        
        for kw_result in analysis_result['per_keyword']:
            keyword = kw_result['keyword']
            
            # Convert opportunities
            opportunities = [
                InterlinkOpportunity(
                    target_url=opp['target_url'],
                    target_title=opp['target_title'],
                    anchor_text=opp['anchor_text'],
                    relevance_score=opp['relevance_score']
                )
                for opp in kw_result['interlink_opportunities']
            ]
            
            per_keyword.append(
                KeywordInterlinkAnalysis(
                    keyword=keyword,
                    difficulty=None,  # Could be enhanced with keyword difficulty analysis
                    suggested_interlinks=kw_result['suggested_interlinks'],
                    suggested_backlinks=0,  # Backlinks not implemented yet
                    interlink_opportunities=opportunities
                )
            )
        
        recommended_interlinks = analysis_result['recommended_interlinks']
        
        notes = f"Found {recommended_interlinks} interlinking opportunities from {len(existing_content)} existing content items"
        
        return ConnectAndRecommendResponse(
            provider=request.provider,
            tenant_id=request.tenant_id,
            saved_integration=saved,
            recommended_interlinks=recommended_interlinks,
            recommended_backlinks=0,
            per_keyword=per_keyword,
            notes=notes
        )
        
    except Exception as e:
        logger.error(f"Interlinking analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Interlinking analysis failed: {str(e)}")


