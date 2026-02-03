"""
Keyword Quality Scorer Module

Calculates quality scores for keywords based on multiple metrics to enable
Ahrefs-like ranking and prioritization.
"""

from typing import Dict, Any, Optional


def calculate_keyword_quality_score(
    search_volume: int = 0,
    difficulty: float = 50.0,
    cpc: float = 0.0,
    competition: float = 0.5,
    relevance: float = 1.0,
    keyword_type: Optional[str] = None
) -> float:
    """
    Calculate quality score (0-100) for keyword ranking.
    
    Higher score = better keyword (more valuable, easier to rank, higher commercial value).
    
    Scoring breakdown:
    - Volume component: 0-40 points (higher volume = higher score)
    - Difficulty component: 0-30 points (lower difficulty = higher score)
    - CPC component: 0-15 points (higher CPC = more commercial value)
    - Competition component: 0-10 points (lower competition = higher score)
    - Relevance component: 0-5 points (semantic relevance to seed keyword)
    
    Args:
        search_volume: Monthly search volume
        difficulty: Keyword difficulty score (0-100)
        cpc: Cost per click ($)
        competition: Competition level (0.0-1.0)
        relevance: Semantic relevance score (0.0-1.0)
        keyword_type: Type of keyword (e.g., "Related Keyword", "Keyword Suggestion", "KW Idea")
        
    Returns:
        Quality score (0.0-100.0)
    """
    # Type conversion to ensure numeric types (handle string values from API)
    try:
        search_volume = int(search_volume) if search_volume else 0
    except (ValueError, TypeError):
        search_volume = 0
    
    try:
        difficulty = float(difficulty) if difficulty else 50.0
    except (ValueError, TypeError):
        difficulty = 50.0
    
    try:
        cpc = float(cpc) if cpc else 0.0
    except (ValueError, TypeError):
        cpc = 0.0
    
    try:
        competition = float(competition) if competition else 0.5
    except (ValueError, TypeError):
        competition = 0.5
    
    try:
        relevance = float(relevance) if relevance else 1.0
    except (ValueError, TypeError):
        relevance = 1.0
    # Volume component (0-40 points)
    if search_volume >= 10000:
        volume_score = 40
    elif search_volume >= 5000:
        volume_score = 35
    elif search_volume >= 1000:
        volume_score = 30
    elif search_volume >= 500:
        volume_score = 25
    elif search_volume >= 100:
        volume_score = 20
    elif search_volume >= 50:
        volume_score = 15
    elif search_volume >= 10:
        volume_score = 10
    elif search_volume >= 1:
        volume_score = 5
    else:
        volume_score = 0
    
    # Difficulty component (0-30 points) - lower difficulty = higher score
    if difficulty <= 20:
        difficulty_score = 30
    elif difficulty <= 30:
        difficulty_score = 27
    elif difficulty <= 40:
        difficulty_score = 24
    elif difficulty <= 50:
        difficulty_score = 20
    elif difficulty <= 60:
        difficulty_score = 15
    elif difficulty <= 70:
        difficulty_score = 10
    elif difficulty <= 80:
        difficulty_score = 5
    else:
        difficulty_score = 0
    
    # CPC component (0-15 points) - higher CPC = more commercial value
    if cpc >= 5.0:
        cpc_score = 15
    elif cpc >= 3.0:
        cpc_score = 12
    elif cpc >= 2.0:
        cpc_score = 10
    elif cpc >= 1.0:
        cpc_score = 8
    elif cpc >= 0.5:
        cpc_score = 5
    elif cpc >= 0.1:
        cpc_score = 2
    else:
        cpc_score = 0
    
    # Competition component (0-10 points) - lower competition = higher score
    # Competition is typically 0.0-1.0, where 1.0 = highest competition
    if competition <= 0.2:
        competition_score = 10
    elif competition <= 0.4:
        competition_score = 8
    elif competition <= 0.6:
        competition_score = 6
    elif competition <= 0.8:
        competition_score = 4
    else:
        competition_score = 2
    
    # Relevance component (0-5 points)
    relevance_score = relevance * 5
    
    # Calculate total score
    total_score = volume_score + difficulty_score + cpc_score + competition_score + relevance_score
    
    # Type-based bonus (small boost for certain types)
    type_bonus = 0
    if keyword_type == "Related Keyword":
        type_bonus = 1  # Related keywords are often high quality
    elif keyword_type == "KW Idea":
        type_bonus = 0.5  # Ideas can be valuable
    
    total_score += type_bonus
    
    # Normalize to 0-100 range
    return min(100.0, max(0.0, total_score))


def sort_keywords_by_quality(
    keywords: list[Dict[str, Any]],
    reverse: bool = True
) -> list[Dict[str, Any]]:
    """
    Sort keywords by quality score (highest first by default).
    
    Args:
        keywords: List of keyword dicts with metrics
        reverse: If True, sort descending (highest quality first)
        
    Returns:
        Sorted list of keywords
    """
    def get_quality_score(kw: Dict[str, Any]) -> float:
        """Extract or calculate quality score for a keyword."""
        # If quality_score already exists, use it (ensure it's numeric)
        if "quality_score" in kw:
            try:
                return float(kw["quality_score"])
            except (ValueError, TypeError):
                pass  # Fall through to calculation
        
        # Otherwise calculate it (with type conversion)
        return calculate_keyword_quality_score(
            search_volume=kw.get("search_volume", 0),
            difficulty=kw.get("keyword_difficulty", kw.get("difficulty_score", 50.0)),
            cpc=kw.get("cpc", 0.0),
            competition=kw.get("competition", 0.5),
            relevance=kw.get("relevance", kw.get("confidence", 1.0)),
            keyword_type=kw.get("type")
        )
    
    return sorted(keywords, key=get_quality_score, reverse=reverse)
