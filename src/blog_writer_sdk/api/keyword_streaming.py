"""
Streaming support for keyword search endpoints.

Provides Server-Sent Events (SSE) streaming for keyword analysis
to show real-time progress of search stages.
"""

import json
import time
from typing import Dict, Any, Optional, Callable, AsyncGenerator
from enum import Enum

class KeywordSearchStage(str, Enum):
    """Stages of keyword search process."""
    INITIALIZING = "initializing"
    DETECTING_LOCATION = "detecting_location"
    ANALYZING_KEYWORDS = "analyzing_keywords"
    GETTING_SUGGESTIONS = "getting_suggestions"
    ANALYZING_SUGGESTIONS = "analyzing_suggestions"
    CLUSTERING_KEYWORDS = "clustering_keywords"
    GETTING_AI_DATA = "getting_ai_data"
    GETTING_AI_SEARCH_VOLUME = "getting_ai_search_volume"
    GETTING_LLM_MENTIONS = "getting_llm_mentions"
    GETTING_SEARCH_VOLUME = "getting_search_volume"
    GETTING_DIFFICULTY = "getting_difficulty"
    GETTING_KEYWORD_OVERVIEW = "getting_keyword_overview"
    GETTING_RELATED_KEYWORDS = "getting_related_keywords"
    GETTING_KEYWORD_IDEAS = "getting_keyword_ideas"
    ANALYZING_SERP = "analyzing_serp"
    ANALYZING_CONTENT = "analyzing_content"
    ANALYZING_INTENT = "analyzing_intent"
    BUILDING_DISCOVERY = "building_discovery"
    GENERATING_RECOMMENDATIONS = "generating_recommendations"
    COMPLETED = "completed"
    ERROR = "error"

def create_stage_update(stage: KeywordSearchStage, progress: float, data: Optional[Dict[str, Any]] = None, message: Optional[str] = None) -> Dict[str, Any]:
    """
    Create a standardized stage update message.
    
    Args:
        stage: Current stage of the search
        progress: Progress percentage (0-100)
        data: Optional data for this stage
        message: Optional human-readable message
        
    Returns:
        Dictionary with stage update information
    """
    update = {
        "stage": stage.value,
        "progress": progress,
        "timestamp": time.time()
    }
    
    if message:
        update["message"] = message
    
    if data:
        update["data"] = data
    
    return update

async def stream_stage_update(stage: KeywordSearchStage, progress: float, data: Optional[Dict[str, Any]] = None, message: Optional[str] = None) -> str:
    """
    Format a stage update as SSE data line.
    
    Args:
        stage: Current stage
        progress: Progress percentage
        data: Optional stage data
        message: Optional message
        
    Returns:
        SSE-formatted string
    """
    update = create_stage_update(stage, progress, data, message)
    return f"data: {json.dumps(update)}\n\n"

async def stream_keyword_search_stages(
    search_func: Callable,
    *args,
    **kwargs
) -> AsyncGenerator[str, None]:
    """
    Stream keyword search stages as SSE events.
    
    This generator yields SSE-formatted updates as each stage completes.
    
    Args:
        search_func: The search function to execute
        *args: Arguments to pass to search_func
        **kwargs: Keyword arguments to pass to search_func
        
    Yields:
        SSE-formatted strings with stage updates
    """
    try:
        # Stage 1: Initializing
        yield await stream_stage_update(
            KeywordSearchStage.INITIALIZING,
            5.0,
            message="Initializing keyword search..."
        )
        
        # Stage 2: Detecting location (if applicable)
        yield await stream_stage_update(
            KeywordSearchStage.DETECTING_LOCATION,
            10.0,
            message="Detecting location..."
        )
        
        # Execute search function with progress callbacks
        # The search function should accept a progress_callback parameter
        result = await search_func(*args, **kwargs)
        
        # Stage 3: Analyzing keywords
        yield await stream_stage_update(
            KeywordSearchStage.ANALYZING_KEYWORDS,
            30.0,
            data={"keywords_analyzed": len(kwargs.get("keywords", []))},
            message="Analyzing keywords..."
        )
        
        # Stage 4: Getting suggestions
        yield await stream_stage_update(
            KeywordSearchStage.GETTING_SUGGESTIONS,
            50.0,
            message="Getting keyword suggestions..."
        )
        
        # Stage 5: Analyzing suggestions
        yield await stream_stage_update(
            KeywordSearchStage.ANALYZING_SUGGESTIONS,
            60.0,
            message="Analyzing suggested keywords..."
        )
        
        # Stage 6: Clustering
        yield await stream_stage_update(
            KeywordSearchStage.CLUSTERING_KEYWORDS,
            70.0,
            message="Clustering keywords by topic..."
        )
        
        # Stage 7: Getting AI data
        yield await stream_stage_update(
            KeywordSearchStage.GETTING_AI_DATA,
            80.0,
            message="Getting AI optimization data..."
        )
        
        # Stage 8: Getting related keywords
        yield await stream_stage_update(
            KeywordSearchStage.GETTING_RELATED_KEYWORDS,
            85.0,
            message="Finding related keywords..."
        )
        
        # Stage 9: Getting keyword ideas
        yield await stream_stage_update(
            KeywordSearchStage.GETTING_KEYWORD_IDEAS,
            90.0,
            message="Getting keyword ideas..."
        )
        
        # Stage 10: Analyzing SERP (if requested)
        if kwargs.get("include_serp", False):
            yield await stream_stage_update(
                KeywordSearchStage.ANALYZING_SERP,
                95.0,
                message="Analyzing SERP features..."
            )
        
        # Stage 11: Building discovery
        yield await stream_stage_update(
            KeywordSearchStage.BUILDING_DISCOVERY,
            98.0,
            message="Building discovery data..."
        )
        
        # Stage 12: Completed
        yield await stream_stage_update(
            KeywordSearchStage.COMPLETED,
            100.0,
            data={"result": result},
            message="Search completed successfully"
        )
        
    except Exception as e:
        # Error stage
        yield await stream_stage_update(
            KeywordSearchStage.ERROR,
            0.0,
            data={"error": str(e)},
            message=f"Search failed: {str(e)}"
        )
        raise

