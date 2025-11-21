"""
Keyword Difficulty Refinement

Provides multi-factor difficulty analysis with time-to-rank estimates.
"""

import logging
from typing import Dict, Optional, List, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class CompetitionLevel(str, Enum):
    """Competition level."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class BacklinkRequirement(str, Enum):
    """Backlink requirements."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class DifficultyFactors:
    """Multi-factor difficulty analysis."""
    domain_authority_required: float  # 0-100
    backlink_requirements: BacklinkRequirement
    content_length_needed: int  # Word count
    competition_level: CompetitionLevel
    time_to_rank: str  # e.g., "1-3 months"
    ranking_probability: Dict[str, float]  # {"1_month": 0.2, "3_months": 0.5, "6_months": 0.8}


@dataclass
class DifficultyAnalysis:
    """Complete difficulty analysis."""
    overall_difficulty: float  # 0-100
    factors: DifficultyFactors
    recommendations: List[str]
    metadata: Dict[str, Any]


class KeywordDifficultyAnalyzer:
    """
    Analyzes keyword difficulty with multi-factor analysis.
    
    Provides:
    - Domain authority requirements
    - Backlink requirements
    - Content length needs
    - Competition level
    - Time-to-rank estimates
    - Ranking probability over time
    """
    
    def __init__(self, dataforseo_client=None):
        """
        Initialize difficulty analyzer.
        
        Args:
            dataforseo_client: DataForSEO client for real data (optional)
        """
        self.df_client = dataforseo_client
    
    async def analyze_difficulty(
        self,
        keyword: str,
        search_volume: int = 0,
        difficulty: float = 50.0,
        competition: float = 0.5,
        location: str = "United States",
        language: str = "en"
    ) -> DifficultyAnalysis:
        """
        Analyze keyword difficulty with multi-factor analysis.
        
        Args:
            keyword: Target keyword
            search_volume: Monthly search volume
            difficulty: Basic difficulty score (0-100)
            competition: Competition index (0-1)
            location: Location for analysis
            language: Language code
            
        Returns:
            DifficultyAnalysis with comprehensive factors
        """
        # Determine domain authority required
        domain_authority_required = self._calculate_domain_authority_required(
            difficulty, competition, search_volume
        )
        
        # Determine backlink requirements
        backlink_requirements = self._calculate_backlink_requirements(
            difficulty, competition, search_volume
        )
        
        # Determine content length needed
        content_length_needed = self._calculate_content_length_needed(
            difficulty, competition, search_volume
        )
        
        # Determine competition level
        competition_level = self._determine_competition_level(competition, difficulty)
        
        # Estimate time to rank
        time_to_rank = self._estimate_time_to_rank(
            difficulty, competition, domain_authority_required
        )
        
        # Calculate ranking probability
        ranking_probability = self._calculate_ranking_probability(
            difficulty, competition, domain_authority_required
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            domain_authority_required,
            backlink_requirements,
            content_length_needed,
            competition_level,
            time_to_rank
        )
        
        factors = DifficultyFactors(
            domain_authority_required=domain_authority_required,
            backlink_requirements=backlink_requirements,
            content_length_needed=content_length_needed,
            competition_level=competition_level,
            time_to_rank=time_to_rank,
            ranking_probability=ranking_probability
        )
        
        return DifficultyAnalysis(
            overall_difficulty=difficulty,
            factors=factors,
            recommendations=recommendations,
            metadata={
                "keyword": keyword,
                "search_volume": search_volume,
                "competition_index": competition
            }
        )
    
    def _calculate_domain_authority_required(
        self,
        difficulty: float,
        competition: float,
        search_volume: int
    ) -> float:
        """Calculate required domain authority (0-100)."""
        # Base requirement from difficulty
        base_da = difficulty * 0.8
        
        # Adjust for competition
        competition_adjustment = competition * 20
        
        # Adjust for search volume (higher volume = more authority needed)
        volume_adjustment = min(20, search_volume / 1000)
        
        required_da = base_da + competition_adjustment + volume_adjustment
        
        return min(100.0, max(10.0, required_da))
    
    def _calculate_backlink_requirements(
        self,
        difficulty: float,
        competition: float,
        search_volume: int
    ) -> BacklinkRequirement:
        """Determine backlink requirements."""
        score = difficulty + (competition * 50) + min(20, search_volume / 500)
        
        if score >= 70:
            return BacklinkRequirement.HIGH
        elif score >= 40:
            return BacklinkRequirement.MEDIUM
        else:
            return BacklinkRequirement.LOW
    
    def _calculate_content_length_needed(
        self,
        difficulty: float,
        competition: float,
        search_volume: int
    ) -> int:
        """Calculate optimal content length in words."""
        # Base length
        base_length = 1500
        
        # Adjust for difficulty
        difficulty_adjustment = difficulty * 10
        
        # Adjust for competition
        competition_adjustment = competition * 500
        
        # Adjust for search volume
        volume_adjustment = min(500, search_volume / 10)
        
        total_length = base_length + difficulty_adjustment + competition_adjustment + volume_adjustment
        
        # Round to nearest 100
        return int(round(total_length / 100) * 100)
    
    def _determine_competition_level(
        self,
        competition: float,
        difficulty: float
    ) -> CompetitionLevel:
        """Determine overall competition level."""
        combined_score = (competition * 50) + (difficulty * 0.5)
        
        if combined_score >= 60:
            return CompetitionLevel.HIGH
        elif combined_score >= 30:
            return CompetitionLevel.MEDIUM
        else:
            return CompetitionLevel.LOW
    
    def _estimate_time_to_rank(
        self,
        difficulty: float,
        competition: float,
        domain_authority_required: float
    ) -> str:
        """Estimate time to rank."""
        # Calculate ranking time score
        time_score = difficulty + (competition * 50) + (domain_authority_required * 0.3)
        
        if time_score >= 80:
            return "6-12 months"
        elif time_score >= 60:
            return "3-6 months"
        elif time_score >= 40:
            return "1-3 months"
        else:
            return "2-4 weeks"
    
    def _calculate_ranking_probability(
        self,
        difficulty: float,
        competition: float,
        domain_authority_required: float
    ) -> Dict[str, float]:
        """Calculate ranking probability over time."""
        # Base probability decreases with difficulty
        base_prob_1m = max(0.0, 1.0 - (difficulty / 100))
        base_prob_3m = max(0.0, 1.0 - (difficulty / 150))
        base_prob_6m = max(0.0, 1.0 - (difficulty / 200))
        
        # Adjust for competition
        competition_penalty = competition * 0.3
        
        # Adjust for domain authority gap (simplified - would compare actual DA)
        da_gap_penalty = max(0.0, (domain_authority_required - 50) / 100) * 0.2
        
        prob_1m = max(0.0, min(1.0, base_prob_1m - competition_penalty - da_gap_penalty))
        prob_3m = max(0.0, min(1.0, base_prob_3m - competition_penalty * 0.7 - da_gap_penalty * 0.7))
        prob_6m = max(0.0, min(1.0, base_prob_6m - competition_penalty * 0.5 - da_gap_penalty * 0.5))
        
        return {
            "1_month": round(prob_1m, 2),
            "3_months": round(prob_3m, 2),
            "6_months": round(prob_6m, 2)
        }
    
    def _generate_recommendations(
        self,
        domain_authority_required: float,
        backlink_requirements: BacklinkRequirement,
        content_length_needed: int,
        competition_level: CompetitionLevel,
        time_to_rank: str
    ) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        # Domain authority recommendations
        if domain_authority_required > 60:
            recommendations.append(
                f"Focus on building domain authority (target: {domain_authority_required:.0f}/100)"
            )
        elif domain_authority_required > 40:
            recommendations.append("Continue building domain authority through quality content")
        
        # Backlink recommendations
        if backlink_requirements == BacklinkRequirement.HIGH:
            recommendations.append("Build 30-50 quality backlinks from authoritative sites")
        elif backlink_requirements == BacklinkRequirement.MEDIUM:
            recommendations.append("Build 15-30 quality backlinks from relevant sites")
        else:
            recommendations.append("Focus on 5-15 quality backlinks for faster ranking")
        
        # Content length recommendations
        recommendations.append(
            f"Create comprehensive content of at least {content_length_needed} words"
        )
        
        # Competition recommendations
        if competition_level == CompetitionLevel.HIGH:
            recommendations.append("Target long-tail variations for faster ranking")
            recommendations.append("Focus on niche-specific content to stand out")
        elif competition_level == CompetitionLevel.MEDIUM:
            recommendations.append("Optimize for related keywords to capture more traffic")
        
        # Time-to-rank recommendations
        recommendations.append(f"Expected ranking time: {time_to_rank}")
        
        return recommendations

