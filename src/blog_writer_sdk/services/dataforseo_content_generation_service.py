"""
DataForSEO Content Generation Service

This service provides blog content generation using DataForSEO Content Generation API.
Supports multiple blog types: brands, top 10, product reviews, and custom content.
Enhanced with word count tolerance, SEO optimization, and backlink analysis.
"""

import logging
import re
from typing import Dict, List, Optional, Any
from enum import Enum
from ..integrations.dataforseo_integration import DataForSEOClient

logger = logging.getLogger(__name__)


class BlogType(str, Enum):
    """
    Supported blog types - Top 80% of popular content formats.
    
    Based on 2024 content marketing research, these types drive the most traffic:
    - How-to guides, tutorials, listicles (top 10), comparisons
    - Product reviews, case studies, news/articles
    - Brand content, guides, FAQs, interviews
    - Opinion pieces, thought leadership, checklists
    """
    # Core Types (Original)
    CUSTOM = "custom"
    BRAND = "brand"
    TOP_10 = "top_10"
    PRODUCT_REVIEW = "product_review"
    HOW_TO = "how_to"
    COMPARISON = "comparison"
    GUIDE = "guide"
    
    # Popular Content Types (Top 80%)
    TUTORIAL = "tutorial"  # Step-by-step learning content
    LISTICLE = "listicle"  # Numbered lists (Top 5, Top 20, etc.)
    CASE_STUDY = "case_study"  # Real-world examples and results
    NEWS = "news"  # Current events and updates
    OPINION = "opinion"  # Editorial and thought leadership
    INTERVIEW = "interview"  # Q&A with experts
    FAQ = "faq"  # Frequently asked questions
    CHECKLIST = "checklist"  # Actionable checklists
    TIPS = "tips"  # Tips and tricks
    DEFINITION = "definition"  # What is X? Explanatory content
    BENEFITS = "benefits"  # Benefits-focused content
    PROBLEM_SOLUTION = "problem_solution"  # Problem-solving content
    TREND_ANALYSIS = "trend_analysis"  # Industry trends
    STATISTICS = "statistics"  # Data-driven content
    RESOURCE_LIST = "resource_list"  # Curated resources
    TIMELINE = "timeline"  # Historical or process timelines
    MYTH_BUSTING = "myth_busting"  # Debunking myths
    BEST_PRACTICES = "best_practices"  # Industry best practices
    GETTING_STARTED = "getting_started"  # Beginner guides
    ADVANCED = "advanced"  # Advanced topics
    TROUBLESHOOTING = "troubleshooting"  # Problem-solving guides


class DataForSEOContentGenerationService:
    """
    Service for generating blog content using DataForSEO Content Generation API.
    
    This service handles:
    - Generating subtopics
    - Generating main content
    - Generating meta tags
    - Supporting different blog types (brands, top 10, product reviews, custom)
    - Word count tolerance (±25%)
    - SEO optimization and post-processing
    - Backlink analysis for premium content
    """
    
    # DataForSEO Content Generation API pricing
    PRICE_PER_TOKEN = 0.00005  # $0.00005 per new token
    PRICE_PER_SUBTOPIC_TASK = 0.0001  # $0.0001 per subtopic task
    PRICE_PER_META_TASK = 0.001  # $0.001 per meta tag task
    
    # Word count tolerance: ±25%
    WORD_COUNT_TOLERANCE = 0.25
    
    def __init__(self, dataforseo_client: Optional[DataForSEOClient] = None):
        """
        Initialize DataForSEO Content Generation Service.
        
        Args:
            dataforseo_client: Optional DataForSEO client instance
        """
        self.client = dataforseo_client
        self.is_configured = False
        
    async def initialize(self, tenant_id: str = "default"):
        """Initialize the DataForSEO client if not already initialized."""
        if not self.client:
            self.client = DataForSEOClient()
            await self.client.initialize_credentials(tenant_id)
        
        self.is_configured = self.client.is_configured
        
        if not self.is_configured:
            logger.warning("DataForSEO Content Generation Service not configured. Credentials missing.")
    
    def _calculate_word_count_range(self, target_word_count: int) -> tuple[int, int]:
        """
        Calculate acceptable word count range with ±25% tolerance.
        
        Args:
            target_word_count: Target word count
            
        Returns:
            Tuple of (min_words, max_words)
        """
        tolerance = int(target_word_count * self.WORD_COUNT_TOLERANCE)
        min_words = max(100, target_word_count - tolerance)  # Minimum 100 words
        max_words = target_word_count + tolerance
        return (min_words, max_words)
    
    def _post_process_content_for_seo(
        self,
        content: str,
        keywords: List[str],
        target_word_count: int
    ) -> Dict[str, Any]:
        """
        Post-process content for SEO and traffic optimization.
        
        Args:
            content: Generated content
            keywords: Target keywords
            target_word_count: Target word count
            
        Returns:
            Dictionary with optimized content and SEO metrics
        """
        word_count = len(content.split())
        min_words, max_words = self._calculate_word_count_range(target_word_count)
        
        # Check if content is within tolerance
        within_tolerance = min_words <= word_count <= max_words
        
        # Calculate keyword density
        content_lower = content.lower()
        keyword_density = {}
        for keyword in keywords:
            count = content_lower.count(keyword.lower())
            density = (count / max(word_count, 1)) * 100
            keyword_density[keyword] = {
                "count": count,
                "density": round(density, 2)
            }
        
        # Extract headings for structure analysis
        headings = re.findall(r'^#{1,6}\s+(.+)$', content, re.MULTILINE)
        
        # Calculate readability metrics (simple)
        sentences = len(re.findall(r'[.!?]+', content))
        avg_sentence_length = word_count / max(sentences, 1)
        
        # SEO score calculation
        seo_score = 0.0
        seo_factors = []
        
        # Keyword in title (if we can detect it)
        if headings:
            title_has_keyword = any(kw.lower() in headings[0].lower() for kw in keywords)
            if title_has_keyword:
                seo_score += 20
                seo_factors.append("Keyword in title")
        
        # Keyword density (optimal: 1-2%)
        avg_density = sum(kd["density"] for kd in keyword_density.values()) / max(len(keywords), 1)
        if 0.5 <= avg_density <= 2.5:
            seo_score += 20
            seo_factors.append("Optimal keyword density")
        elif avg_density > 0:
            seo_score += 10
            seo_factors.append("Keywords present")
        
        # Content length (within tolerance)
        if within_tolerance:
            seo_score += 20
            seo_factors.append("Optimal content length")
        elif word_count >= min_words:
            seo_score += 10
            seo_factors.append("Content length acceptable")
        
        # Heading structure
        if len(headings) >= 3:
            seo_score += 15
            seo_factors.append("Good heading structure")
        elif len(headings) >= 1:
            seo_score += 10
            seo_factors.append("Has headings")
        
        # Readability (optimal: 15-20 words per sentence)
        if 10 <= avg_sentence_length <= 25:
            seo_score += 15
            seo_factors.append("Good readability")
        elif avg_sentence_length <= 30:
            seo_score += 10
            seo_factors.append("Acceptable readability")
        
        # Content quality indicators
        if word_count >= target_word_count * 0.75:  # At least 75% of target
            seo_score += 10
            seo_factors.append("Sufficient content depth")
        
        # Truncate content if significantly over target (optional)
        optimized_content = content
        if word_count > max_words * 1.5:  # More than 50% over max
            # Try to truncate at a natural break point
            words = content.split()
            truncated_words = words[:max_words]
            # Find last sentence boundary
            truncated_text = " ".join(truncated_words)
            last_period = max(
                truncated_text.rfind("."),
                truncated_text.rfind("!"),
                truncated_text.rfind("?")
            )
            if last_period > len(truncated_text) * 0.8:  # If period is near end
                optimized_content = truncated_text[:last_period + 1]
                logger.info(f"Content truncated from {word_count} to {len(optimized_content.split())} words")
        
        return {
            "content": optimized_content,
            "word_count": len(optimized_content.split()),
            "original_word_count": word_count,
            "within_tolerance": within_tolerance,
            "min_words": min_words,
            "max_words": max_words,
            "keyword_density": keyword_density,
            "headings_count": len(headings),
            "avg_sentence_length": round(avg_sentence_length, 1),
            "seo_score": min(100, round(seo_score, 1)),
            "seo_factors": seo_factors,
            "readability_score": self._calculate_readability_score(optimized_content)
        }
    
    def _calculate_readability_score(self, content: str) -> float:
        """
        Calculate simple readability score (0-100).
        
        Args:
            content: Content to analyze
            
        Returns:
            Readability score (higher is better)
        """
        words = content.split()
        sentences = len(re.findall(r'[.!?]+', content))
        paragraphs = len(re.split(r'\n\s*\n', content))
        
        if not sentences or not paragraphs:
            return 50.0
        
        avg_sentence_length = len(words) / sentences
        avg_paragraph_length = len(words) / paragraphs
        
        # Optimal: 15-20 words per sentence, 100-200 words per paragraph
        sentence_score = 100 - abs(avg_sentence_length - 17.5) * 2
        paragraph_score = 100 - abs(avg_paragraph_length - 150) * 0.5
        
        # Combine scores
        readability = (sentence_score * 0.6 + paragraph_score * 0.4)
        return max(0, min(100, readability))
    
    async def analyze_backlinks_for_keywords(
        self,
        url: str,
        limit: int = 100,
        tenant_id: str = "default"
    ) -> Dict[str, Any]:
        """
        Analyze backlinks from a premium blog URL to extract high-performing keywords.
        
        Args:
            url: URL of the premium blog to analyze
            limit: Maximum number of backlinks to analyze
            tenant_id: Tenant ID
            
        Returns:
            Dictionary with:
            - extracted_keywords: List of keywords from backlink anchor text
            - top_keywords: Most common keywords
            - backlink_count: Total backlinks found
            - referring_domains: Number of referring domains
        """
        if not self.is_configured:
            await self.initialize(tenant_id)
        
        if not self.is_configured:
            raise ValueError("DataForSEO Content Generation Service not configured")
        
        try:
            # Use DataForSEO Backlinks API
            logger.info(f"Analyzing backlinks for URL: {url}")
            
            # Determine if URL or domain
            target_type = "url" if url.startswith("http") else "domain"
            
            # Get backlinks using DataForSEO API
            backlink_data = await self.client.get_backlinks(
                target=url,
                target_type=target_type,
                limit=limit,
                tenant_id=tenant_id
            )
            
            # Extract keywords from anchor texts
            anchor_texts = backlink_data.get("anchor_texts", [])
            extracted_keywords = backlink_data.get("extracted_keywords", [])
            
            # Count keyword frequency
            keyword_freq = {}
            for keyword in extracted_keywords:
                keyword_freq[keyword] = keyword_freq.get(keyword, 0) + 1
            
            # Get top keywords by frequency
            top_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)[:20]
            
            result = {
                "url": url,
                "backlink_count": backlink_data.get("total_count", 0),
                "referring_domains": backlink_data.get("referring_domains", 0),
                "extracted_keywords": extracted_keywords,
                "top_keywords": [kw[0] for kw in top_keywords],
                "anchor_texts": anchor_texts[:20],  # Top 20 anchor texts
                "backlinks": backlink_data.get("backlinks", [])[:10]  # Sample of backlinks
            }
            
            if "error" in backlink_data:
                result["error"] = backlink_data["error"]
                result["note"] = "Backlink analysis may require DataForSEO Backlinks API subscription"
            
            return result
            
        except Exception as e:
            logger.error(f"Backlink analysis failed: {e}")
            return {
                "url": url,
                "error": str(e),
                "extracted_keywords": [],
                "top_keywords": []
            }
    
    async def generate_subtopics(
        self,
        text: str,
        max_subtopics: int = 10,
        language: str = "en",
        tenant_id: str = "default"
    ) -> Dict[str, Any]:
        """
        Generate subtopics from text using DataForSEO API.
        
        Args:
            text: Input text to generate subtopics from
            max_subtopics: Maximum number of subtopics to generate
            language: Language code (default: "en")
            tenant_id: Tenant ID
            
        Returns:
            Dictionary with subtopics list and metadata
        """
        if not self.is_configured:
            logger.warning("DataForSEO Content Generation Service not configured, returning empty subtopics")
            return {"subtopics": [], "count": 0, "cost": 0.0, "metadata": {}}
        
        try:
            result = await self.client.generate_subtopics(
                text=text,
                max_subtopics=max_subtopics,
                language=language,
                tenant_id=tenant_id
            )
            
            return {
                "subtopics": result.get("subtopics", []),
                "count": result.get("count", 0),
                "cost": self.PRICE_PER_SUBTOPIC_TASK,
                "metadata": result.get("metadata", {})
            }
            
        except Exception as e:
            # Log error but don't raise - subtopics are optional
            logger.warning(f"DataForSEO subtopic generation failed (continuing without subtopics): {e}")
            return {"subtopics": [], "count": 0, "cost": 0.0, "metadata": {}}
    
    async def generate_text(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        creativity_index: Optional[float] = None,
        tone: Optional[str] = None,
        language: str = "en",
        tenant_id: str = "default"
    ) -> Dict[str, Any]:
        """
        Generate text content using DataForSEO API.
        
        Args:
            prompt: Text prompt for generation
            max_tokens: Maximum tokens to generate
            temperature: Creativity level (0.0-1.0)
            creativity_index: Alternative creativity parameter (0.0-1.0)
            tone: Writing tone (e.g., "professional", "casual")
            language: Language code (default: "en")
            tenant_id: Tenant ID
            
        Returns:
            Dictionary with generated text, tokens used, and cost
        """
        if not self.is_configured:
            raise ValueError("DataForSEO Content Generation Service not configured")
        
        try:
            # Use creativity_index if provided, otherwise use temperature
            creativity = creativity_index if creativity_index is not None else temperature
            
            result = await self.client.generate_text(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=creativity,
                tenant_id=tenant_id
            )
            
            tokens_used = result.get("tokens_used", 0)
            cost = tokens_used * self.PRICE_PER_TOKEN
            
            return {
                "text": result.get("text", ""),
                "tokens_used": tokens_used,
                "cost": cost,
                "metadata": result.get("metadata", {})
            }
            
        except Exception as e:
            logger.error(f"DataForSEO text generation failed: {e}")
            raise
    
    async def generate_meta_tags(
        self,
        title: str,
        content: str,
        language: str = "en",
        tenant_id: str = "default"
    ) -> Dict[str, Any]:
        """
        Generate meta tags using DataForSEO API.
        
        Args:
            title: Page title
            content: Page content
            language: Language code (default: "en")
            tenant_id: Tenant ID
            
        Returns:
            Dictionary with meta title, description, and keywords
        """
        if not self.is_configured:
            raise ValueError("DataForSEO Content Generation Service not configured")
        
        try:
            result = await self.client.generate_meta_tags(
                title=title,
                content=content,
                tenant_id=tenant_id
            )
            
            return {
                "meta_title": result.get("meta_title", title),
                "meta_description": result.get("meta_description", ""),
                "summary": result.get("summary", ""),
                "keywords": result.get("keywords", []),
                "cost": self.PRICE_PER_META_TASK,
                "metadata": result.get("metadata", {})
            }
            
        except Exception as e:
            logger.error(f"DataForSEO meta tag generation failed: {e}")
            raise
    
    def _build_prompt_for_blog_type(
        self,
        blog_type: BlogType,
        topic: str,
        keywords: List[str],
        **kwargs
    ) -> str:
        """
        Build prompt based on blog type with improved word count control.
        
        Args:
            blog_type: Type of blog to generate
            topic: Main topic
            keywords: List of keywords
            **kwargs: Additional parameters specific to blog type
            
        Returns:
            Formatted prompt string with explicit word count guidance
        """
        keywords_str = ", ".join(keywords[:10])  # Limit to 10 keywords
        word_count = kwargs.get('word_count', 1500)
        min_words, max_words = self._calculate_word_count_range(word_count)
        tone = kwargs.get('tone', 'professional')
        target_audience = kwargs.get('target_audience', 'general audience')
        
        # Enhanced word count instruction
        word_count_instruction = f"""IMPORTANT: Write approximately {word_count} words (acceptable range: {min_words}-{max_words} words). 
Quality and natural flow are more important than hitting the exact word count. 
Aim for comprehensive, valuable content that thoroughly covers the topic."""
        
        # SEO optimization instruction
        seo_instruction = f"""SEO Requirements:
- Naturally incorporate these keywords: {keywords_str}
- Use keywords in headings and throughout content (1-2% keyword density)
- Write for humans first, search engines second
- Create engaging, shareable content that drives traffic"""
        
        if blog_type == BlogType.BRAND:
            brand_name = kwargs.get("brand_name", topic)
            return f"""Write a comprehensive blog post about {brand_name}.

Topic: {topic}
Keywords: {keywords_str}
Target Audience: {target_audience}

Include:
- Brand history and background
- Key products or services
- Brand values and mission
- Market position and competitors
- Why choose this brand
- Customer testimonials or reviews (if available)

{word_count_instruction}

{seo_instruction}

Write in a {tone} tone."""

        elif blog_type == BlogType.TOP_10 or blog_type == BlogType.LISTICLE:
            category = kwargs.get("category", topic)
            number = kwargs.get("number", 10)
            return f"""Write a comprehensive "{number} {category}" listicle/blog post.

Topic: {topic}
Keywords: {keywords_str}
Target Audience: {target_audience}

Structure:
1. Introduction explaining why this list matters (10% of content)
2. Detailed entries for each item ({number} items, 70% of content), including:
   - Name/title
   - Key features or characteristics
   - Pros and cons
   - Why it made the list
   - Best use cases
3. Comparison table (if applicable, 10% of content)
4. Buying guide or recommendations (5% of content)
5. Conclusion with final recommendations (5% of content)

{word_count_instruction}

{seo_instruction}

Write in a {tone} tone."""

        elif blog_type == BlogType.PRODUCT_REVIEW:
            product_name = kwargs.get("product_name", topic)
            return f"""Write a comprehensive product review for {product_name}.

Topic: {topic}
Keywords: {keywords_str}
Target Audience: {target_audience}

Include:
1. Product Overview (15% of content)
   - Product name and manufacturer
   - Key specifications
   - Price range
2. Features and Benefits (25% of content)
   - Main features
   - Unique selling points
   - How it solves problems
3. Pros and Cons (20% of content)
   - Detailed advantages
   - Limitations or drawbacks
4. Performance and Quality (15% of content)
   - Build quality
   - Performance metrics
   - Durability
5. Comparison with Competitors (10% of content)
   - Similar products
   - Price comparison
   - Feature comparison
6. User Experience (10% of content)
   - Ease of use
   - Customer reviews summary
7. Verdict and Recommendations (5% of content)
   - Who should buy it
   - Who should avoid it
   - Final rating

{word_count_instruction}

{seo_instruction}

Write in a {tone} tone."""

        elif blog_type == BlogType.HOW_TO or blog_type == BlogType.TUTORIAL:
            return f"""Write a comprehensive "How to {topic}" guide/tutorial.

Topic: {topic}
Keywords: {keywords_str}
Target Audience: {target_audience}

Structure:
1. Introduction explaining what readers will learn (10% of content)
2. Prerequisites or requirements (10% of content)
3. Step-by-step instructions with clear headings (60% of content)
   - Number each step clearly
   - Include screenshots/examples where relevant
   - Explain why each step matters
4. Tips and best practices (10% of content)
5. Common mistakes to avoid (5% of content)
6. Troubleshooting section (5% of content)
7. Conclusion with next steps

{word_count_instruction}

{seo_instruction}

Write in a {tone} tone."""

        elif blog_type == BlogType.COMPARISON:
            items = kwargs.get("items", [topic])
            items_str = ", ".join(items[:5])  # Limit to 5 items
            return f"""Write a comprehensive comparison guide.

Topic: {topic}
Comparing: {items_str}
Keywords: {keywords_str}
Target Audience: {target_audience}

Structure:
1. Introduction to the comparison (10% of content)
2. Overview of each item being compared (20% of content)
3. Comparison table with key features (15% of content)
4. Detailed comparison by category (40% of content):
   - Features
   - Price
   - Performance
   - User experience
   - Pros and cons
5. Use case recommendations (10% of content)
6. Final verdict and recommendation (5% of content)

{word_count_instruction}

{seo_instruction}

Write in a {tone} tone."""

        elif blog_type == BlogType.GUIDE:
            return f"""Write a comprehensive guide about {topic}.

Topic: {topic}
Keywords: {keywords_str}
Target Audience: {target_audience}

Structure:
1. Introduction and overview (10% of content)
2. Key concepts and fundamentals (25% of content)
3. Detailed explanations with examples (40% of content)
4. Best practices (15% of content)
5. Common pitfalls to avoid (5% of content)
6. Advanced topics (if applicable, 5% of content)
7. Resources and further reading
8. Conclusion

{word_count_instruction}

{seo_instruction}

Write in a {tone} tone."""

        elif blog_type == BlogType.CASE_STUDY:
            return f"""Write a comprehensive case study about {topic}.

Topic: {topic}
Keywords: {keywords_str}
Target Audience: {target_audience}

Structure:
1. Executive Summary (10% of content)
2. Background and Context (15% of content)
3. Challenge/Problem Statement (15% of content)
4. Solution/Approach (30% of content)
5. Implementation Process (15% of content)
6. Results and Outcomes (10% of content)
7. Key Takeaways and Lessons Learned (5% of content)

{word_count_instruction}

{seo_instruction}

Write in a {tone} tone."""

        elif blog_type == BlogType.NEWS:
            return f"""Write a news article/blog post about {topic}.

Topic: {topic}
Keywords: {keywords_str}
Target Audience: {target_audience}

Structure:
1. Headline and lead paragraph (who, what, when, where, why)
2. Main story and details
3. Background context
4. Quotes or expert opinions (if applicable)
5. Implications
6. What's next or conclusion

{word_count_instruction}

{seo_instruction}

Write in a {tone} tone."""

        elif blog_type == BlogType.OPINION:
            return f"""Write an opinion piece/editorial about {topic}.

Topic: {topic}
Keywords: {keywords_str}
Target Audience: {target_audience}

Structure:
1. Hook and introduction
2. Your perspective/argument
3. Supporting evidence and examples
4. Counterarguments addressed
5. Conclusion and call to action

{word_count_instruction}

{seo_instruction}

Write in a {tone} tone."""

        elif blog_type == BlogType.INTERVIEW:
            return f"""Write an interview-style blog post about {topic}.

Topic: {topic}
Keywords: {keywords_str}
Target Audience: {target_audience}

Structure:
1. Introduction to the interviewee/topic
2. Q&A format with insightful questions
3. Key quotes highlighted
4. Analysis and commentary
5. Conclusion and takeaways

{word_count_instruction}

{seo_instruction}

Write in a {tone} tone."""

        elif blog_type == BlogType.FAQ:
            return f"""Write a comprehensive FAQ (Frequently Asked Questions) about {topic}.

Topic: {topic}
Keywords: {keywords_str}
Target Audience: {target_audience}

Structure:
1. Introduction explaining the topic
2. 10-15 common questions with detailed answers
3. Each answer should be comprehensive (50-150 words)
4. Conclusion with additional resources

{word_count_instruction}

{seo_instruction}

Write in a {tone} tone."""

        elif blog_type == BlogType.CHECKLIST:
            return f"""Write a comprehensive checklist about {topic}.

Topic: {topic}
Keywords: {keywords_str}
Target Audience: {target_audience}

Structure:
1. Introduction explaining the purpose
2. Prerequisites or preparation steps
3. Main checklist items (detailed, actionable)
4. Tips for each major item
5. Common mistakes to avoid
6. Conclusion

{word_count_instruction}

{seo_instruction}

Write in a {tone} tone."""

        elif blog_type == BlogType.TIPS:
            return f"""Write a tips and tricks blog post about {topic}.

Topic: {topic}
Keywords: {keywords_str}
Target Audience: {target_audience}

Structure:
1. Introduction
2. 10-20 practical tips (each with explanation)
3. Pro tips section
4. Common mistakes to avoid
5. Conclusion

{word_count_instruction}

{seo_instruction}

Write in a {tone} tone."""

        elif blog_type == BlogType.DEFINITION:
            return f"""Write a comprehensive definition/explanation of {topic}.

Topic: {topic}
Keywords: {keywords_str}
Target Audience: {target_audience}

Structure:
1. Clear definition
2. Key characteristics
3. How it works
4. Examples and use cases
5. Related concepts
6. Conclusion

{word_count_instruction}

{seo_instruction}

Write in a {tone} tone."""

        elif blog_type == BlogType.BENEFITS:
            return f"""Write a benefits-focused blog post about {topic}.

Topic: {topic}
Keywords: {keywords_str}
Target Audience: {target_audience}

Structure:
1. Introduction
2. Main benefits (detailed explanation of each)
3. How to achieve these benefits
4. Real-world examples
5. Conclusion

{word_count_instruction}

{seo_instruction}

Write in a {tone} tone."""

        elif blog_type == BlogType.PROBLEM_SOLUTION:
            return f"""Write a problem-solution blog post about {topic}.

Topic: {topic}
Keywords: {keywords_str}
Target Audience: {target_audience}

Structure:
1. Problem identification
2. Why this problem matters
3. Solution approach
4. Step-by-step solution
5. Alternative solutions
6. Prevention tips
7. Conclusion

{word_count_instruction}

{seo_instruction}

Write in a {tone} tone."""

        elif blog_type == BlogType.TREND_ANALYSIS:
            return f"""Write a trend analysis blog post about {topic}.

Topic: {topic}
Keywords: {keywords_str}
Target Audience: {target_audience}

Structure:
1. Current state overview
2. Emerging trends
3. Data and statistics
4. Implications
5. Future predictions
6. Actionable insights
7. Conclusion

{word_count_instruction}

{seo_instruction}

Write in a {tone} tone."""

        elif blog_type == BlogType.STATISTICS:
            return f"""Write a statistics/data-driven blog post about {topic}.

Topic: {topic}
Keywords: {keywords_str}
Target Audience: {target_audience}

Structure:
1. Introduction
2. Key statistics and data points
3. Analysis and interpretation
4. Visualizations (describe data)
5. Insights and takeaways
6. Conclusion

{word_count_instruction}

{seo_instruction}

Write in a {tone} tone."""

        elif blog_type == BlogType.RESOURCE_LIST:
            return f"""Write a curated resource list about {topic}.

Topic: {topic}
Keywords: {keywords_str}
Target Audience: {target_audience}

Structure:
1. Introduction
2. Categorized resources with descriptions
3. Why each resource is valuable
4. How to use these resources
5. Conclusion

{word_count_instruction}

{seo_instruction}

Write in a {tone} tone."""

        elif blog_type == BlogType.TIMELINE:
            return f"""Write a timeline blog post about {topic}.

Topic: {topic}
Keywords: {keywords_str}
Target Audience: {target_audience}

Structure:
1. Introduction
2. Chronological timeline with key events
3. Context for each major milestone
4. Analysis of progression
5. Current state
6. Conclusion

{word_count_instruction}

{seo_instruction}

Write in a {tone} tone."""

        elif blog_type == BlogType.MYTH_BUSTING:
            return f"""Write a myth-busting blog post about {topic}.

Topic: {topic}
Keywords: {keywords_str}
Target Audience: {target_audience}

Structure:
1. Introduction
2. Common myths listed
3. Debunking each myth with facts
4. Evidence and sources
5. Truth and best practices
6. Conclusion

{word_count_instruction}

{seo_instruction}

Write in a {tone} tone."""

        elif blog_type == BlogType.BEST_PRACTICES:
            return f"""Write a best practices blog post about {topic}.

Topic: {topic}
Keywords: {keywords_str}
Target Audience: {target_audience}

Structure:
1. Introduction
2. Industry best practices (detailed)
3. Why each practice matters
4. Implementation guide
5. Common mistakes to avoid
6. Conclusion

{word_count_instruction}

{seo_instruction}

Write in a {tone} tone."""

        elif blog_type == BlogType.GETTING_STARTED:
            return f"""Write a getting started guide about {topic}.

Topic: {topic}
Keywords: {keywords_str}
Target Audience: {target_audience}

Structure:
1. Introduction for beginners
2. Prerequisites
3. Step-by-step getting started guide
4. First steps
5. Common beginner mistakes
6. Next steps and resources
7. Conclusion

{word_count_instruction}

{seo_instruction}

Write in a {tone} tone."""

        elif blog_type == BlogType.ADVANCED:
            return f"""Write an advanced-level blog post about {topic}.

Topic: {topic}
Keywords: {keywords_str}
Target Audience: {target_audience}

Structure:
1. Introduction (assumes prior knowledge)
2. Advanced concepts
3. Deep dive into technical details
4. Advanced techniques
5. Expert tips
6. Conclusion

{word_count_instruction}

{seo_instruction}

Write in a {tone} tone."""

        elif blog_type == BlogType.TROUBLESHOOTING:
            return f"""Write a troubleshooting guide about {topic}.

Topic: {topic}
Keywords: {keywords_str}
Target Audience: {target_audience}

Structure:
1. Introduction
2. Common problems and symptoms
3. Diagnostic steps
4. Solutions for each problem
5. Prevention tips
6. When to seek help
7. Conclusion

{word_count_instruction}

{seo_instruction}

Write in a {tone} tone."""

        else:  # CUSTOM
            custom_instructions = kwargs.get("custom_instructions", "")
            return f"""Write a comprehensive blog post about {topic}.

Keywords: {keywords_str}
Target Audience: {target_audience}
{custom_instructions}

{word_count_instruction}

{seo_instruction}

Write in a {tone} tone."""
    
    async def generate_blog_content(
        self,
        topic: str,
        keywords: List[str],
        blog_type: BlogType = BlogType.CUSTOM,
        tone: str = "professional",
        word_count: int = 1500,
        target_audience: Optional[str] = None,
        language: str = "en",
        tenant_id: str = "default",
        optimize_for_traffic: bool = True,
        analyze_backlinks: bool = False,
        backlink_url: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate complete blog content using DataForSEO Content Generation API.
        
        This method:
        1. Generates subtopics from the topic
        2. Generates main content based on blog type
        3. Generates meta tags
        4. Post-processes for SEO and traffic optimization
        5. Optionally analyzes backlinks for keyword extraction
        
        Args:
            topic: Main topic for the blog
            keywords: List of keywords to optimize for
            blog_type: Type of blog (brand, top_10, product_review, custom, etc.)
            tone: Writing tone (professional, casual, friendly, etc.)
            word_count: Target word count (with ±25% tolerance)
            target_audience: Target audience description
            language: Language code (default: "en")
            tenant_id: Tenant ID
            optimize_for_traffic: Enable SEO post-processing (default: True)
            analyze_backlinks: Analyze backlinks for keyword extraction (default: False)
            backlink_url: URL to analyze for backlinks (required if analyze_backlinks=True)
            **kwargs: Additional parameters specific to blog type
        
        Returns:
            Dictionary with:
            - content: Generated blog content (post-processed)
            - title: Generated title
            - meta_title: SEO meta title
            - meta_description: SEO meta description
            - subtopics: List of subtopics
            - cost: Total API cost
            - tokens_used: Total tokens used
            - seo_metrics: SEO optimization metrics
            - backlink_keywords: Extracted keywords from backlinks (if analyzed)
        """
        if not self.is_configured:
            await self.initialize(tenant_id)
        
        if not self.is_configured:
            raise ValueError("DataForSEO Content Generation Service not configured. Please check credentials.")
        
        total_cost = 0.0
        total_tokens = 0
        backlink_keywords = []
        
        try:
            # Optional: Analyze backlinks for keyword extraction
            if analyze_backlinks and backlink_url:
                logger.info(f"Analyzing backlinks for keyword extraction: {backlink_url}")
                backlink_analysis = await self.analyze_backlinks_for_keywords(
                    url=backlink_url,
                    limit=100,
                    tenant_id=tenant_id
                )
                backlink_keywords = backlink_analysis.get("extracted_keywords", [])
                if backlink_keywords:
                    # Merge backlink keywords with provided keywords
                    keywords = list(set(keywords + backlink_keywords[:10]))  # Add top 10
                    logger.info(f"Added {len(backlink_keywords)} keywords from backlink analysis")
            
            # Step 1: Build prompt based on blog type
            prompt = self._build_prompt_for_blog_type(
                blog_type=blog_type,
                topic=topic,
                keywords=keywords,
                tone=tone,
                word_count=word_count,
                target_audience=target_audience or "general audience",
                **kwargs
            )
            
            # Step 2: Generate subtopics
            logger.info(f"Generating subtopics for blog type: {blog_type.value}")
            subtopics_result = await self.generate_subtopics(
                text=prompt,
                max_subtopics=10,
                language=language,
                tenant_id=tenant_id
            )
            subtopics = subtopics_result.get("subtopics", [])
            total_cost += subtopics_result.get("cost", 0.0)
            
            # Step 3: Generate main content
            # Estimate tokens needed (roughly 1 token = 0.75 words)
            # Account for ±25% tolerance
            min_words, max_words = self._calculate_word_count_range(word_count)
            estimated_tokens = int(max_words / 0.75)  # Use max for token estimation
            max_tokens = min(estimated_tokens + 500, 4000)  # Add buffer, cap at 4000
            
            logger.info(f"Generating main content ({max_tokens} tokens max, target: {word_count} words, range: {min_words}-{max_words})")
            content_result = await self.generate_text(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=0.7,
                tone=tone,
                language=language,
                tenant_id=tenant_id
            )
            generated_content = content_result.get("text", "")
            total_tokens += content_result.get("tokens_used", 0)
            total_cost += content_result.get("cost", 0.0)
            
            # Step 4: Post-process for SEO and traffic optimization
            if optimize_for_traffic:
                logger.info("Post-processing content for SEO and traffic optimization")
                seo_result = self._post_process_content_for_seo(
                    content=generated_content,
                    keywords=keywords,
                    target_word_count=word_count
                )
                generated_content = seo_result["content"]
                seo_metrics = {
                    "seo_score": seo_result["seo_score"],
                    "readability_score": seo_result["readability_score"],
                    "keyword_density": seo_result["keyword_density"],
                    "headings_count": seo_result["headings_count"],
                    "avg_sentence_length": seo_result["avg_sentence_length"],
                    "seo_factors": seo_result["seo_factors"],
                    "within_tolerance": seo_result["within_tolerance"],
                    "word_count_range": {
                        "min": seo_result["min_words"],
                        "max": seo_result["max_words"],
                        "actual": seo_result["word_count"]
                    }
                }
            else:
                seo_metrics = {}
            
            # Step 5: Generate title (use first part of content or topic)
            title = topic
            if generated_content:
                # Try to extract a title from the first line or use topic
                first_line = generated_content.split("\n")[0].strip()
                if len(first_line) < 100 and len(first_line) > 10:
                    title = first_line.replace("#", "").strip()
            
            # Step 6: Generate meta tags
            logger.info("Generating meta tags")
            meta_result = await self.generate_meta_tags(
                title=title,
                content=generated_content[:5000],  # Limit content for meta generation
                language=language,
                tenant_id=tenant_id
            )
            total_cost += meta_result.get("cost", 0.0)
            
            return {
                "content": generated_content,
                "title": title,
                "meta_title": meta_result.get("meta_title", title),
                "meta_description": meta_result.get("meta_description", ""),
                "subtopics": subtopics,
                "keywords": meta_result.get("keywords", keywords),
                "cost": total_cost,
                "tokens_used": total_tokens,
                "blog_type": blog_type.value,
                "seo_metrics": seo_metrics,
                "backlink_keywords": backlink_keywords if analyze_backlinks else [],
                "metadata": {
                    "subtopics_count": len(subtopics),
                    "word_count": len(generated_content.split()),
                    "generation_steps": 3 + (1 if optimize_for_traffic else 0) + (1 if analyze_backlinks else 0)
                }
            }
            
        except Exception as e:
            logger.error(f"Blog content generation failed: {e}", exc_info=True)
            raise
