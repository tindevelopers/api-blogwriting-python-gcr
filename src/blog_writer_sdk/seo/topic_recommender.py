"""
Topic Recommendation Engine

Recommends high-ranking blog topics based on:
- DataForSEO keyword analysis (search volume, difficulty, competition)
- Google Custom Search (content gaps, competitor analysis)
- Keyword clustering (topic opportunities)
- AI-powered topic generation (Claude)
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class RecommendedTopic:
    """Represents a recommended blog topic."""
    topic: str
    primary_keyword: str
    search_volume: int
    difficulty: float  # 0-100
    competition: float  # 0-1
    cpc: float
    ranking_score: float  # 0-100, calculated score
    opportunity_score: float  # 0-100, content gap opportunity
    related_keywords: List[str]
    content_gaps: List[str]  # Missing content opportunities
    estimated_traffic: int  # Estimated monthly traffic potential
    reason: str  # Why this topic is recommended


@dataclass
class TopicRecommendationResult:
    """Result of topic recommendation analysis."""
    recommended_topics: List[RecommendedTopic]
    total_opportunities: int
    high_priority_topics: List[RecommendedTopic]  # Top 5 by ranking_score
    trending_topics: List[RecommendedTopic]  # Topics with rising trends
    low_competition_topics: List[RecommendedTopic]  # Easy wins
    analysis_date: str


class TopicRecommendationEngine:
    """
    Recommends high-ranking blog topics using multiple data sources.
    
    Uses:
    1. DataForSEO for keyword metrics (volume, difficulty, competition)
    2. Google Custom Search for content gap analysis
    3. Keyword clustering for topic opportunities
    4. Claude AI for intelligent topic generation
    """
    
    def __init__(
        self,
        dataforseo_client=None,
        google_search_client=None,
        ai_generator=None,
        keyword_clustering=None
    ):
        """
        Initialize topic recommendation engine.
        
        Args:
            dataforseo_client: DataForSEO client for keyword analysis
            google_search_client: Google Custom Search client for content gaps
            ai_generator: AI generator (for Claude-powered topic suggestions)
            keyword_clustering: Keyword clustering instance
        """
        self.df_client = dataforseo_client
        self.google_search = google_search_client
        self.ai_generator = ai_generator
        self.keyword_clustering = keyword_clustering
    
    async def recommend_topics(
        self,
        seed_keywords: List[str],
        location: str = "United States",
        language: str = "en",
        max_topics: int = 20,
        min_search_volume: int = 100,
        max_difficulty: float = 70.0,
        include_ai_suggestions: bool = True
    ) -> TopicRecommendationResult:
        """
        Recommend high-ranking blog topics based on seed keywords.
        
        Args:
            seed_keywords: Initial keywords to base recommendations on
            location: Location for search volume analysis
            language: Language code
            max_topics: Maximum number of topics to return
            min_search_volume: Minimum monthly search volume
            max_difficulty: Maximum keyword difficulty (0-100)
            include_ai_suggestions: Whether to use Claude for topic generation
        
        Returns:
            TopicRecommendationResult with recommended topics
        """
        logger.info(f"Recommending topics for {len(seed_keywords)} seed keywords")
        
        all_topics: List[RecommendedTopic] = []
        
        # Step 1: Get keyword suggestions from DataForSEO
        if self.df_client:
            try:
                # Get related keywords and suggestions
                for seed in seed_keywords[:5]:  # Limit to avoid too many API calls
                    try:
                        # Get keyword suggestions
                        suggestions = await self.df_client.get_keyword_suggestions(
                            seed_keyword=seed,
                            location_name=location,
                            language_code=language,
                            tenant_id="default",
                            limit=50
                        )
                        
                        # Get related keywords
                        related = await self.df_client.get_related_keywords(
                            keyword=seed,
                            location_name=location,
                            language_code=language,
                            tenant_id="default",
                            depth=1,
                            limit=30
                        )
                        
                        # Parse related keywords response
                        related_keywords_list = []
                        if isinstance(related, dict) and "items" in related:
                            related_keywords_list = [r.get("keyword", "") for r in related.get("items", [])[:20] if r.get("keyword")]
                        elif isinstance(related, list):
                            related_keywords_list = [r.get("keyword", "") for r in related[:20] if isinstance(r, dict) and r.get("keyword")]
                        
                        # Parse suggestions response
                        suggestions_list = []
                        if isinstance(suggestions, list):
                            suggestions_list = [s.get("keyword", "") for s in suggestions[:30] if isinstance(s, dict) and s.get("keyword")]
                        elif isinstance(suggestions, dict) and "items" in suggestions:
                            suggestions_list = [s.get("keyword", "") for s in suggestions.get("items", [])[:30] if s.get("keyword")]
                        
                        # Combine and analyze
                        candidate_keywords = (suggestions_list or []) + (related_keywords_list or [])
                        
                        # Analyze each candidate
                        if candidate_keywords:
                            for keyword in set(candidate_keywords):
                                if not keyword or len(keyword) < 3:
                                    continue
                                
                                topic = await self._analyze_topic_potential(
                                    keyword, location, language
                                )
                                
                                if topic and self._meets_criteria(topic, min_search_volume, max_difficulty):
                                    all_topics.append(topic)
                                
                    except Exception as e:
                        logger.warning(f"Failed to get suggestions for {seed}: {e}")
                        continue
                        
            except Exception as e:
                logger.warning(f"DataForSEO topic analysis failed: {e}")
        
        # Step 2: Use Google Search to find content gaps
        if self.google_search:
            try:
                gap_topics = await self._find_content_gaps(seed_keywords)
                if gap_topics:
                    all_topics.extend(gap_topics)
            except Exception as e:
                logger.warning(f"Content gap analysis failed: {e}")
        
        # Step 3: Use AI (Claude) to generate topic suggestions
        if include_ai_suggestions and self.ai_generator:
            try:
                ai_topics = await self._generate_ai_topics(
                    seed_keywords, location, language
                )
                if ai_topics:
                    all_topics.extend(ai_topics)
            except Exception as e:
                logger.warning(f"AI topic generation failed: {e}")
        
        # Step 4: Deduplicate and score topics
        unique_topics = self._deduplicate_topics(all_topics)
        scored_topics = sorted(
            unique_topics,
            key=lambda t: t.ranking_score,
            reverse=True
        )[:max_topics]
        
        # Step 5: Categorize topics
        high_priority = [t for t in scored_topics if t.ranking_score >= 70][:5]
        trending = [t for t in scored_topics if t.search_volume > 1000 and t.difficulty < 50][:5]
        low_competition = [t for t in scored_topics if t.difficulty < 40][:5]
        
        return TopicRecommendationResult(
            recommended_topics=scored_topics,
            total_opportunities=len(scored_topics),
            high_priority_topics=high_priority,
            trending_topics=trending,
            low_competition_topics=low_competition,
            analysis_date=datetime.now().isoformat()
        )
    
    async def _analyze_topic_potential(
        self,
        keyword: str,
        location: str,
        language: str
    ) -> Optional[RecommendedTopic]:
        """Analyze a keyword's potential as a blog topic."""
        try:
            if not self.df_client:
                return None
            
            # Get keyword overview
            overview = await self.df_client.get_keyword_overview(
                keywords=[keyword],
                location_name=location,
                language_code=language,
                tenant_id="default"
            )
            
            if not overview:
                return None
            
            # Handle different response formats
            if isinstance(overview, dict):
                if keyword in overview:
                    data = overview[keyword]
                elif "items" in overview:
                    items = overview.get("items", [])
                    if items and len(items) > 0:
                        data = items[0]
                    else:
                        return None
                else:
                    return None
            else:
                return None
            
            search_volume = data.get("search_volume", 0) or data.get("monthly_searches", 0)
            difficulty = data.get("keyword_difficulty", 50.0) or data.get("difficulty", 50.0)
            competition = data.get("competition", 0.5) or data.get("competition_index", 0.5)
            cpc = data.get("cpc", 0.0) or data.get("cost_per_click", 0.0)
            
            # Get related keywords
            related = await self.df_client.get_related_keywords(
                keyword=keyword,
                location_name=location,
                language_code=language,
                tenant_id="default",
                depth=1,
                limit=10
            )
            # Handle different response formats
            related_keywords = []
            if isinstance(related, dict):
                if "items" in related:
                    related_keywords = [r.get("keyword", "") for r in related.get("items", [])[:10] if r.get("keyword")]
                elif isinstance(related, list):
                    related_keywords = [r.get("keyword", "") for r in related[:10] if isinstance(r, dict) and r.get("keyword")]
            elif isinstance(related, list):
                related_keywords = [r.get("keyword", "") for r in related[:10] if isinstance(r, dict) and r.get("keyword")]
            
            # Calculate ranking score
            ranking_score = self._calculate_ranking_score(
                search_volume, difficulty, competition, cpc
            )
            
            # Calculate opportunity score (content gap potential)
            opportunity_score = self._calculate_opportunity_score(
                search_volume, difficulty, competition
            )
            
            # Estimate traffic potential
            estimated_traffic = int(search_volume * 0.1)  # Conservative estimate: 10% CTR
            
            # Generate reason
            reason = self._generate_recommendation_reason(
                search_volume, difficulty, competition, cpc
            )
            
            # Find content gaps
            content_gaps = await self._identify_content_gaps(keyword)
            
            return RecommendedTopic(
                topic=keyword.title(),
                primary_keyword=keyword,
                search_volume=search_volume,
                difficulty=difficulty,
                competition=competition,
                cpc=cpc,
                ranking_score=ranking_score,
                opportunity_score=opportunity_score,
                related_keywords=related_keywords,
                content_gaps=content_gaps,
                estimated_traffic=estimated_traffic,
                reason=reason
            )
            
        except Exception as e:
            logger.warning(f"Failed to analyze topic potential for {keyword}: {e}")
            return None
    
    def _calculate_ranking_score(
        self,
        search_volume: int,
        difficulty: float,
        competition: float,
        cpc: float
    ) -> float:
        """
        Calculate ranking score (0-100) for a topic.
        
        Higher score = better ranking opportunity.
        """
        # Volume score (0-40 points)
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
        else:
            volume_score = 10
        
        # Difficulty score (0-30 points) - lower difficulty = higher score
        if difficulty <= 30:
            difficulty_score = 30
        elif difficulty <= 50:
            difficulty_score = 25
        elif difficulty <= 70:
            difficulty_score = 20
        else:
            difficulty_score = 10
        
        # Competition score (0-20 points) - lower competition = higher score
        if competition <= 0.3:
            competition_score = 20
        elif competition <= 0.5:
            competition_score = 15
        elif competition <= 0.7:
            competition_score = 10
        else:
            competition_score = 5
        
        # CPC score (0-10 points) - higher CPC = more commercial value
        if cpc >= 5.0:
            cpc_score = 10
        elif cpc >= 2.0:
            cpc_score = 8
        elif cpc >= 1.0:
            cpc_score = 6
        elif cpc >= 0.5:
            cpc_score = 4
        else:
            cpc_score = 2
        
        return volume_score + difficulty_score + competition_score + cpc_score
    
    def _calculate_opportunity_score(
        self,
        search_volume: int,
        difficulty: float,
        competition: float
    ) -> float:
        """
        Calculate opportunity score (0-100) for content gaps.
        
        Higher score = better content gap opportunity.
        """
        # High volume + low difficulty + low competition = high opportunity
        opportunity = 0.0
        
        # Volume component (40%)
        if search_volume >= 1000:
            opportunity += 40
        elif search_volume >= 500:
            opportunity += 30
        elif search_volume >= 100:
            opportunity += 20
        else:
            opportunity += 10
        
        # Low difficulty component (35%)
        if difficulty <= 40:
            opportunity += 35
        elif difficulty <= 60:
            opportunity += 25
        else:
            opportunity += 15
        
        # Low competition component (25%)
        if competition <= 0.4:
            opportunity += 25
        elif competition <= 0.6:
            opportunity += 15
        else:
            opportunity += 5
        
        return min(100.0, opportunity)
    
    def _generate_recommendation_reason(
        self,
        search_volume: int,
        difficulty: float,
        competition: float,
        cpc: float
    ) -> str:
        """Generate human-readable reason for recommendation."""
        reasons = []
        
        if search_volume >= 1000:
            reasons.append(f"High search volume ({search_volume:,}/month)")
        elif search_volume >= 500:
            reasons.append(f"Moderate search volume ({search_volume:,}/month)")
        
        if difficulty <= 40:
            reasons.append("Low competition difficulty")
        elif difficulty <= 60:
            reasons.append("Moderate competition difficulty")
        
        if competition <= 0.4:
            reasons.append("Low competition")
        elif competition <= 0.6:
            reasons.append("Moderate competition")
        
        if cpc >= 2.0:
            reasons.append(f"High commercial value (CPC: ${cpc:.2f})")
        
        if not reasons:
            reasons.append("Good keyword opportunity")
        
        return "; ".join(reasons)
    
    async def _find_content_gaps(
        self,
        seed_keywords: List[str],
        competitor_domains: List[str] = None
    ) -> List[RecommendedTopic]:
        """
        Find content gaps using Google Search with competitor analysis.
        
        Enhanced to include:
        - Competitor coverage analysis
        - Your coverage vs competitor coverage
        - Opportunity scoring based on gaps
        """
        gap_topics = []
        
        if not self.google_search:
            return gap_topics
        
        competitor_domains = competitor_domains or []
        
        try:
            for keyword in seed_keywords[:3]:  # Limit to avoid rate limits
                # Search for top-ranking content
                results = await self.google_search.search(
                    query=keyword,
                    num_results=10
                )
                
                # Analyze competitor coverage
                competitor_coverage = {}
                your_coverage = 0
                
                for result in results:
                    domain = result.get("display_link", "").replace("www.", "")
                    if domain:
                        # Check if it's a competitor
                        is_competitor = any(
                            comp_domain.replace("www.", "") in domain 
                            for comp_domain in competitor_domains
                        )
                        
                        if is_competitor:
                            competitor_coverage[domain] = competitor_coverage.get(domain, 0) + 1
                        # In production, would check if domain is yours
                        # your_coverage += 1 if domain == your_domain else 0
                
                # Calculate coverage percentages
                total_results = len(results)
                competitor_count = sum(competitor_coverage.values())
                competitor_coverage_pct = (competitor_count / total_results * 100) if total_results > 0 else 0
                your_coverage_pct = (your_coverage / total_results * 100) if total_results > 0 else 0
                
                # Calculate opportunity score
                opportunity_score = self._calculate_gap_opportunity_score(
                    competitor_coverage_pct,
                    your_coverage_pct,
                    total_results
                )
                
                # Identify specific gaps
                content_gaps = await self._identify_content_gaps(keyword, results, competitor_domains)
                
                # Only recommend if there's a significant gap
                if opportunity_score >= 60 or len(content_gaps) > 0:
                    # Get keyword metrics if available
                    search_volume = 500  # Default estimate
                    difficulty = 50.0
                    competition = competitor_coverage_pct / 100.0
                    
                    if self.df_client:
                        try:
                            overview = await self.df_client.get_keyword_overview(
                                keywords=[keyword],
                                location_name="United States",
                                language_code="en",
                                tenant_id="default"
                            )
                            if overview:
                                # Parse overview data
                                if isinstance(overview, dict):
                                    data = overview.get(keyword) or (overview.get("items", [{}])[0] if overview.get("items") else {})
                                    search_volume = data.get("search_volume", 500) or data.get("monthly_searches", 500)
                                    difficulty = data.get("keyword_difficulty", 50.0) or data.get("difficulty", 50.0)
                        except Exception:
                            pass
                    
                    topic = RecommendedTopic(
                        topic=keyword.title(),
                        primary_keyword=keyword,
                        search_volume=search_volume,
                        difficulty=difficulty,
                        competition=competition,
                        cpc=1.0,
                        ranking_score=self._calculate_ranking_score(search_volume, difficulty, competition, 1.0),
                        opportunity_score=opportunity_score,
                        related_keywords=[],
                        content_gaps=content_gaps,
                        estimated_traffic=int(search_volume * 0.1),
                        reason=f"Content gap: {competitor_coverage_pct:.0f}% competitor coverage, {your_coverage_pct:.0f}% your coverage"
                    )
                    gap_topics.append(topic)
                    
        except Exception as e:
            logger.warning(f"Content gap analysis failed: {e}")
        
        return gap_topics
    
    def _calculate_gap_opportunity_score(
        self,
        competitor_coverage_pct: float,
        your_coverage_pct: float,
        total_results: int
    ) -> float:
        """
        Calculate opportunity score based on content gaps.
        
        Higher score = better opportunity (competitors rank but you don't).
        """
        score = 0.0
        
        # Gap size component (40 points)
        gap_size = competitor_coverage_pct - your_coverage_pct
        if gap_size >= 50:
            score += 40
        elif gap_size >= 30:
            score += 30
        elif gap_size >= 10:
            score += 20
        else:
            score += 10
        
        # Competition level component (30 points)
        # Lower competition = higher opportunity
        if competitor_coverage_pct <= 30:
            score += 30
        elif competitor_coverage_pct <= 50:
            score += 20
        elif competitor_coverage_pct <= 70:
            score += 10
        
        # SERP saturation component (30 points)
        # Fewer results = less saturated = better opportunity
        if total_results < 5:
            score += 30
        elif total_results < 8:
            score += 20
        else:
            score += 10
        
        return min(100.0, score)
    
    async def _identify_content_gaps(
        self,
        keyword: str,
        search_results: List[Dict[str, Any]] = None,
        competitor_domains: List[str] = None
    ) -> List[str]:
        """
        Identify specific content gaps for a keyword.
        
        Enhanced to include:
        - Competitor content analysis
        - Content freshness gaps
        - Content depth gaps
        - SERP feature opportunities
        """
        gaps = []
        
        if not self.google_search and not search_results:
            return gaps
        
        competitor_domains = competitor_domains or []
        
        try:
            if not search_results:
                search_results = await self.google_search.search(
                    query=keyword,
                    num_results=10
                )
            
            # Check for common gaps
            if len(search_results) < 3:
                gaps.append("Limited content available - low competition")
            
            # Analyze competitor content depth
            competitor_results = [
                r for r in search_results
                if any(comp_domain.replace("www.", "") in r.get("display_link", "").replace("www.", "") 
                      for comp_domain in competitor_domains)
            ]
            
            if len(competitor_results) > len(search_results) * 0.5:
                gaps.append(f"Competitors dominate SERP ({len(competitor_results)}/{len(search_results)} results)")
            
            # Check content freshness (simplified - would parse dates in production)
            # Look for "recent" indicators in snippets
            recent_indicators = ["2024", "2025", "recent", "new", "updated", "latest"]
            recent_count = sum(
                1 for result in search_results
                if any(indicator in result.get("snippet", "").lower() for indicator in recent_indicators)
            )
            
            if recent_count < len(search_results) * 0.3:
                gaps.append("Content freshness gap - most results are older")
            
            # Check for SERP feature opportunities
            # Look for question-based queries
            if any(q_word in keyword.lower() for q_word in ["how", "what", "why", "when", "where"]):
                gaps.append("Featured snippet opportunity - question-based query")
            
            # Check content type gaps
            content_types = {
                "video": sum(1 for r in search_results if "youtube.com" in r.get("display_link", "")),
                "image": sum(1 for r in search_results if any(ext in r.get("link", "") for ext in [".jpg", ".png", ".gif"])),
                "guide": sum(1 for r in search_results if any(word in r.get("snippet", "").lower() for word in ["guide", "tutorial", "how to"]))
            }
            
            if content_types["guide"] < 3:
                gaps.append("Comprehensive guide opportunity - few detailed guides")
            
            if content_types["video"] == 0:
                gaps.append("Video content gap - no video results")
            
        except Exception as e:
            logger.warning(f"Failed to identify content gaps for {keyword}: {e}")
        
        return gaps
    
    async def _generate_ai_topics(
        self,
        seed_keywords: List[str],
        location: str,
        language: str
    ) -> List[RecommendedTopic]:
        """Use Claude AI to generate intelligent topic suggestions."""
        ai_topics = []
        
        if not self.ai_generator:
            return ai_topics
        
        try:
            # Get keyword data for context
            keyword_context = []
            if self.df_client:
                for kw in seed_keywords[:3]:
                    try:
                        overview = await self.df_client.get_keyword_overview(
                            keywords=[kw],
                            location_name=location,
                            language_code=language,
                            tenant_id="default"
                        )
                        if overview:
                            # Handle different response formats
                            data = None
                            if isinstance(overview, dict):
                                if kw in overview:
                                    data = overview[kw]
                                elif "items" in overview:
                                    items = overview.get("items", [])
                                    if items:
                                        data = items[0]
                            
                            if data:
                                keyword_context.append({
                                    "keyword": kw,
                                    "volume": data.get("search_volume", 0) or data.get("monthly_searches", 0),
                                    "difficulty": data.get("keyword_difficulty", 50.0) or data.get("difficulty", 50.0)
                                })
                    except:
                        continue
            
            # Build prompt for Claude
            prompt = f"""You are an expert SEO content strategist. Based on these seed keywords and their metrics, suggest 10 high-value blog topics that would rank well.

SEED KEYWORDS & METRICS:
{chr(10).join([f"- {ctx['keyword']}: {ctx['volume']:,} searches/month, difficulty {ctx['difficulty']:.0f}/100" for ctx in keyword_context])}

REQUIREMENTS:
1. Topics should be related to the seed keywords
2. Focus on topics with good search volume potential (500+ searches/month)
3. Prioritize topics with low-medium competition (difficulty < 60)
4. Include a mix of informational, how-to, and comparison topics
5. Each topic should be a complete blog post idea (not just a keyword)

OUTPUT FORMAT:
Return a JSON array of topic objects, each with:
- "topic": Full blog topic title
- "primary_keyword": Main keyword for the topic
- "reason": Why this topic would rank well

Example:
[
  {{
    "topic": "Complete Guide to Pet Grooming at Home",
    "primary_keyword": "pet grooming guide",
    "reason": "High search volume, low competition, comprehensive content opportunity"
  }}
]

Return only valid JSON, no markdown formatting."""
            
            # Generate with Claude
            from ..ai.base_provider import AIRequest, ContentType
            
            request = AIRequest(
                prompt=prompt,
                content_type=ContentType.BLOG_POST,
                max_tokens=2000,
                temperature=0.7,
                preferred_provider="anthropic"
            )
            
            response = await self.ai_generator.generate_content(request, model="claude-3-5-sonnet-20241022")
            
            # Parse response
            import json
            import re
            
            content = response.content.strip()
            # Extract JSON from response
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                topics_data = json.loads(json_match.group())
                
                # Convert to RecommendedTopic objects
                for topic_data in topics_data[:10]:
                    keyword = topic_data.get("primary_keyword", topic_data.get("topic", "").lower())
                    
                    # Analyze the suggested keyword
                    topic = await self._analyze_topic_potential(keyword, location, language)
                    if topic:
                        # Update with AI-generated topic title
                        topic.topic = topic_data.get("topic", keyword.title())
                        topic.reason = topic_data.get("reason", topic.reason)
                        ai_topics.append(topic)
            
        except Exception as e:
            logger.warning(f"AI topic generation failed: {e}")
        
        return ai_topics
    
    def _meets_criteria(
        self,
        topic: RecommendedTopic,
        min_search_volume: int,
        max_difficulty: float
    ) -> bool:
        """Check if topic meets minimum criteria."""
        return (
            topic.search_volume >= min_search_volume and
            topic.difficulty <= max_difficulty
        )
    
    def _deduplicate_topics(
        self,
        topics: List[RecommendedTopic]
    ) -> List[RecommendedTopic]:
        """Remove duplicate topics based on primary keyword."""
        seen = set()
        unique = []
        
        for topic in topics:
            key = topic.primary_keyword.lower().strip()
            if key not in seen:
                seen.add(key)
                unique.append(topic)
        
        return unique

