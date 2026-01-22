"""
Cluster Content Generation Module

Generates content recommendations (titles, descriptions, URLs) for keyword clusters
using AI to create pillar and sub-page structures.
"""

import re
import logging
from typing import Dict, List, Optional, Any
from urllib.parse import quote
from ..seo.keyword_categorizer import KeywordCategory, ClusterContentRecommendation
from ..ai.base_provider import AIRequest, AIGenerationConfig, ContentType
from ..ai.ai_content_generator import AIContentGenerator

logger = logging.getLogger(__name__)


class ClusterContentGenerator:
    """
    Generates content recommendations for keyword clusters.
    
    Uses AI to create:
    - Pillar article titles and descriptions
    - Sub-page article titles and descriptions
    - URL slugs
    - Content hierarchy (pillar vs sub-page)
    """
    
    def __init__(self, ai_generator: Optional[AIContentGenerator] = None):
        """
        Initialize cluster content generator.
        
        Args:
            ai_generator: Optional AI content generator for title/description generation
        """
        self.ai_generator = ai_generator
    
    async def generate_cluster_content_recommendations(
        self,
        cluster: Dict[str, Any],
        category: KeywordCategory,
        keywords_data: Dict[str, Dict[str, Any]],
        priority: int = 3
    ) -> ClusterContentRecommendation:
        """
        Generate content recommendations for a keyword cluster.
        
        Args:
            cluster: Cluster object with parent_topic and keywords
            category: Strategic category for the cluster
            keywords_data: Full keyword analysis data for cluster keywords
            priority: Priority score (1-5)
            
        Returns:
            ClusterContentRecommendation with titles, descriptions, URLs
        """
        cluster_name = cluster.get('parent_topic', 'Unknown Topic')
        cluster_keywords = cluster.get('keywords', [])
        
        if not cluster_keywords:
            return ClusterContentRecommendation(
                cluster_name=cluster_name,
                category=category,
                priority=priority
            )
        
        # Get top keywords from cluster (by search volume or priority)
        top_keywords = self._get_top_keywords(cluster_keywords, keywords_data, limit=5)
        
        # Generate pillar article
        pillar = await self._generate_pillar_article(
            cluster_name=cluster_name,
            top_keywords=top_keywords,
            category=category,
            keywords_data=keywords_data
        )
        
        # Generate sub-page articles
        sub_pages = await self._generate_sub_pages(
            cluster_name=cluster_name,
            cluster_keywords=cluster_keywords,
            top_keywords=top_keywords,
            keywords_data=keywords_data,
            category=category
        )
        
        # Estimate word count based on category and keyword count
        estimated_word_count = self._estimate_word_count(category, len(cluster_keywords))
        
        return ClusterContentRecommendation(
            cluster_name=cluster_name,
            category=category,
            pillar_title=pillar.get('title'),
            pillar_description=pillar.get('description'),
            pillar_url=pillar.get('url'),
            sub_pages=sub_pages,
            priority=priority,
            estimated_word_count=estimated_word_count
        )
    
    def _get_top_keywords(
        self,
        keywords: List[str],
        keywords_data: Dict[str, Dict[str, Any]],
        limit: int = 5
    ) -> List[str]:
        """Get top keywords by search volume and priority."""
        keyword_scores = []
        
        for kw in keywords:
            kw_data = keywords_data.get(kw, {})
            search_volume = kw_data.get('search_volume', 0)
            difficulty = kw_data.get('difficulty_score', 50.0)
            priority_score = kw_data.get('priority_score', 0.5)
            
            # Score = volume * (1 - difficulty/100) * priority
            score = search_volume * (1 - difficulty/100) * (priority_score or 0.5)
            keyword_scores.append((kw, score))
        
        # Sort by score descending
        keyword_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Return top keywords
        return [kw for kw, _ in keyword_scores[:limit]]
    
    async def _generate_pillar_article(
        self,
        cluster_name: str,
        top_keywords: List[str],
        category: KeywordCategory,
        keywords_data: Dict[str, Dict[str, Any]]
    ) -> Dict[str, str]:
        """
        Generate pillar article title, description, and URL.
        
        Pillar articles are comprehensive guides that cover the main topic.
        """
        # Build context from top keywords
        keyword_context = []
        for kw in top_keywords[:3]:
            kw_data = keywords_data.get(kw, {})
            volume = kw_data.get('search_volume', 0)
            difficulty = kw_data.get('difficulty_score', 50.0)
            keyword_context.append(f"{kw} (volume: {volume}, difficulty: {difficulty:.0f})")
        
        # Generate title using AI if available, otherwise use template
        if self.ai_generator and len(top_keywords) > 0:
            try:
                title = await self._generate_title_with_ai(
                    cluster_name=cluster_name,
                    keywords=top_keywords,
                    article_type="pillar",
                    category=category
                )
            except Exception as e:
                logger.warning(f"AI title generation failed: {e}, using template")
                title = self._generate_title_template(cluster_name, top_keywords[0], "pillar")
        else:
            title = self._generate_title_template(cluster_name, top_keywords[0] if top_keywords else cluster_name, "pillar")
        
        # Generate description
        description = self._generate_description(cluster_name, top_keywords, category, "pillar")
        
        # Generate URL slug
        url = self._generate_url_slug(title)
        
        return {
            "title": title,
            "description": description,
            "url": url
        }
    
    async def _generate_sub_pages(
        self,
        cluster_name: str,
        cluster_keywords: List[str],
        top_keywords: List[str],
        keywords_data: Dict[str, Dict[str, Any]],
        category: KeywordCategory
    ) -> List[Dict[str, str]]:
        """
        Generate sub-page article recommendations.
        
        Sub-pages are more specific articles that support the pillar.
        """
        sub_pages = []
        
        # Use keywords that aren't in top keywords for sub-pages
        sub_keywords = [kw for kw in cluster_keywords if kw not in top_keywords[:3]]
        
        # Limit to 7 sub-pages max
        for kw in sub_keywords[:7]:
            kw_data = keywords_data.get(kw, {})
            
            # Generate title
            if self.ai_generator:
                try:
                    title = await self._generate_title_with_ai(
                        cluster_name=cluster_name,
                        keywords=[kw],
                        article_type="sub-page",
                        category=category
                    )
                except Exception as e:
                    logger.warning(f"AI title generation failed for {kw}: {e}, using template")
                    title = self._generate_title_template(cluster_name, kw, "sub-page")
            else:
                title = self._generate_title_template(cluster_name, kw, "sub-page")
            
            # Generate description
            description = self._generate_description(cluster_name, [kw], category, "sub-page")
            
            # Generate URL slug
            url = self._generate_url_slug(title)
            
            sub_pages.append({
                "title": title,
                "description": description,
                "url": url,
                "keyword": kw
            })
        
        return sub_pages
    
    async def _generate_title_with_ai(
        self,
        cluster_name: str,
        keywords: List[str],
        article_type: str,
        category: KeywordCategory
    ) -> str:
        """Generate article title using AI."""
        if not self.ai_generator:
            raise ValueError("AI generator not available")
        
        article_type_desc = "comprehensive guide" if article_type == "pillar" else "focused article"
        
        prompt = f"""Generate a compelling, SEO-optimized blog article title for the following topic cluster.

CLUSTER TOPIC: {cluster_name}
PRIMARY KEYWORDS: {', '.join(keywords[:3])}
ARTICLE TYPE: {article_type_desc}
CATEGORY: {category.value}

REQUIREMENTS:
1. Title should be 50-70 characters
2. Include the primary keyword naturally
3. Make it compelling and click-worthy
4. For pillar articles: Use words like "Complete Guide", "Ultimate Guide", "Comprehensive"
5. For sub-pages: Be more specific and focused
6. Avoid generic words like "Everything You Need to Know" unless appropriate

Return ONLY the title, no quotes, no markdown, no explanation."""

        try:
            from ..ai.base_provider import AIRequest, AIGenerationConfig, ContentType
            
            request = AIRequest(
                prompt=prompt,
                content_type=ContentType.TITLE,
                config=AIGenerationConfig(
                    max_tokens=100,
                    temperature=0.7,
                    top_p=0.9
                )
            )
            
            response = await self.ai_generator.provider_manager.generate_content(
                request=request,
                preferred_provider=None  # Use default
            )
            
            title = response.content.strip()
            # Remove quotes if present
            title = title.strip('"\'')
            
            # Limit to 70 characters
            if len(title) > 70:
                title = title[:67] + "..."
            
            return title
            
        except Exception as e:
            logger.error(f"AI title generation failed: {e}")
            raise
    
    def _generate_title_template(
        self,
        cluster_name: str,
        primary_keyword: str,
        article_type: str
    ) -> str:
        """Generate title using template (fallback)."""
        if article_type == "pillar":
            # Pillar article templates
            templates = [
                f"Complete Guide to {cluster_name}",
                f"Ultimate {cluster_name} Guide: Everything You Need to Know",
                f"Comprehensive Guide to {cluster_name}",
                f"{cluster_name}: The Complete Resource"
            ]
        else:
            # Sub-page templates
            templates = [
                f"{primary_keyword.title()}: Expert Tips and Best Practices",
                f"How to {primary_keyword.title()}: A Practical Guide",
                f"{primary_keyword.title()}: What You Need to Know",
                f"Understanding {primary_keyword.title()}"
            ]
        
        # Use first template that fits
        for template in templates:
            if len(template) <= 70:
                return template
        
        # Fallback
        return f"{cluster_name}: {primary_keyword.title()}"
    
    def _generate_description(
        self,
        cluster_name: str,
        keywords: List[str],
        category: KeywordCategory,
        article_type: str
    ) -> str:
        """Generate article description."""
        primary_keyword = keywords[0] if keywords else cluster_name
        
        if article_type == "pillar":
            description = f"Comprehensive guide to {cluster_name.lower()}. Learn everything about {primary_keyword.lower()} including best practices, expert tips, and actionable strategies."
        else:
            description = f"Expert insights on {primary_keyword.lower()}. Discover practical tips, best practices, and actionable advice for {cluster_name.lower()}."
        
        # Limit to 160 characters (meta description length)
        if len(description) > 160:
            description = description[:157] + "..."
        
        return description
    
    def _generate_url_slug(self, title: str) -> str:
        """Generate URL slug from title."""
        # Convert to lowercase
        slug = title.lower()
        
        # Remove special characters, keep alphanumeric, spaces, and hyphens
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        
        # Replace multiple spaces with single hyphen
        slug = re.sub(r'\s+', '-', slug)
        
        # Remove leading/trailing hyphens
        slug = slug.strip('-')
        
        # Limit length
        if len(slug) > 60:
            slug = slug[:60].rstrip('-')
        
        return f"/{slug}"
    
    def _estimate_word_count(
        self,
        category: KeywordCategory,
        keyword_count: int
    ) -> int:
        """Estimate word count based on category and keyword count."""
        base_counts = {
            KeywordCategory.QUICK_WINS: 1200,
            KeywordCategory.AUTHORITY_BUILDERS: 3000,
            KeywordCategory.EMERGING_TOPICS: 2000,
            KeywordCategory.INTENT_SIGNALS: 1500,
            KeywordCategory.SEMANTIC_TOPICS: 1800
        }
        
        base = base_counts.get(category, 1500)
        
        # Adjust based on keyword count (more keywords = more content)
        multiplier = 1 + (keyword_count * 0.1)
        
        return int(base * multiplier)
