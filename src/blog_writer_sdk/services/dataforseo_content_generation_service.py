"""
DataForSEO Content Generation Service

This service provides blog content generation using DataForSEO Content Generation API.
Supports multiple blog types: brands, top 10, product reviews, and custom content.
"""

import logging
from typing import Dict, List, Optional, Any
from enum import Enum
from ..integrations.dataforseo_integration import DataForSEOClient

logger = logging.getLogger(__name__)


class BlogType(str, Enum):
    """Supported blog types."""
    CUSTOM = "custom"
    BRAND = "brand"
    TOP_10 = "top_10"
    PRODUCT_REVIEW = "product_review"
    HOW_TO = "how_to"
    COMPARISON = "comparison"
    GUIDE = "guide"


class DataForSEOContentGenerationService:
    """
    Service for generating blog content using DataForSEO Content Generation API.
    
    This service handles:
    - Generating subtopics
    - Generating main content
    - Generating meta tags
    - Supporting different blog types (brands, top 10, product reviews, custom)
    """
    
    # DataForSEO Content Generation API pricing
    PRICE_PER_TOKEN = 0.00005  # $0.00005 per new token
    PRICE_PER_SUBTOPIC_TASK = 0.0001  # $0.0001 per subtopic task
    PRICE_PER_META_TASK = 0.001  # $0.001 per meta tag task
    
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
            raise ValueError("DataForSEO Content Generation Service not configured")
        
        try:
            # DataForSEO API endpoint for subtopics
            payload = [{
                "text": text,
                "max_subtopics": max_subtopics,
                "language": language
            }]
            
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
            logger.error(f"DataForSEO subtopic generation failed: {e}")
            raise
    
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
            
            payload = [{
                "text": prompt,
                "max_tokens": max_tokens,
                "temperature": creativity,
                "language": language
            }]
            
            # Add tone if provided
            if tone:
                payload[0]["tone"] = tone
            
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
        Build prompt based on blog type.
        
        Args:
            blog_type: Type of blog to generate
            topic: Main topic
            keywords: List of keywords
            **kwargs: Additional parameters specific to blog type
            
        Returns:
            Formatted prompt string
        """
        keywords_str = ", ".join(keywords[:10])  # Limit to 10 keywords
        
        if blog_type == BlogType.BRAND:
            brand_name = kwargs.get("brand_name", topic)
            return f"""Write a comprehensive blog post about {brand_name}.

Topic: {topic}
Keywords: {keywords_str}
Target Audience: {kwargs.get('target_audience', 'general audience')}

Include:
- Brand history and background
- Key products or services
- Brand values and mission
- Market position and competitors
- Why choose this brand
- Customer testimonials or reviews (if available)

Write in a {kwargs.get('tone', 'professional')} tone. Target length: {kwargs.get('word_count', 1500)} words."""

        elif blog_type == BlogType.TOP_10:
            category = kwargs.get("category", topic)
            return f"""Write a comprehensive "Top 10 {category}" blog post.

Topic: {topic}
Keywords: {keywords_str}
Target Audience: {kwargs.get('target_audience', 'general audience')}

Structure:
1. Introduction explaining why this top 10 list matters
2. Detailed entries for each of the top 10 items, including:
   - Name/title
   - Key features or characteristics
   - Pros and cons
   - Why it made the list
   - Best use cases
3. Comparison table (if applicable)
4. Buying guide or recommendations
5. Conclusion with final recommendations

Write in a {kwargs.get('tone', 'professional')} tone. Target length: {kwargs.get('word_count', 2000)} words."""

        elif blog_type == BlogType.PRODUCT_REVIEW:
            product_name = kwargs.get("product_name", topic)
            return f"""Write a comprehensive product review for {product_name}.

Topic: {topic}
Keywords: {keywords_str}
Target Audience: {kwargs.get('target_audience', 'potential buyers')}

Include:
1. Product Overview
   - Product name and manufacturer
   - Key specifications
   - Price range
2. Features and Benefits
   - Main features
   - Unique selling points
   - How it solves problems
3. Pros and Cons
   - Detailed advantages
   - Limitations or drawbacks
4. Performance and Quality
   - Build quality
   - Performance metrics
   - Durability
5. Comparison with Competitors
   - Similar products
   - Price comparison
   - Feature comparison
6. User Experience
   - Ease of use
   - Customer reviews summary
7. Verdict and Recommendations
   - Who should buy it
   - Who should avoid it
   - Final rating

Write in a {kwargs.get('tone', 'professional')} tone. Target length: {kwargs.get('word_count', 2000)} words."""

        elif blog_type == BlogType.HOW_TO:
            return f"""Write a comprehensive "How to {topic}" guide.

Topic: {topic}
Keywords: {keywords_str}
Target Audience: {kwargs.get('target_audience', 'beginners')}

Structure:
1. Introduction explaining what readers will learn
2. Prerequisites or requirements
3. Step-by-step instructions with clear headings
4. Tips and best practices
5. Common mistakes to avoid
6. Troubleshooting section
7. Conclusion with next steps

Write in a {kwargs.get('tone', 'instructional')} tone. Target length: {kwargs.get('word_count', 1500)} words."""

        elif blog_type == BlogType.COMPARISON:
            items = kwargs.get("items", [topic])
            items_str = ", ".join(items[:5])  # Limit to 5 items
            return f"""Write a comprehensive comparison guide.

Topic: {topic}
Comparing: {items_str}
Keywords: {keywords_str}
Target Audience: {kwargs.get('target_audience', 'decision makers')}

Structure:
1. Introduction to the comparison
2. Overview of each item being compared
3. Comparison table with key features
4. Detailed comparison by category:
   - Features
   - Price
   - Performance
   - User experience
   - Pros and cons
5. Use case recommendations
6. Final verdict and recommendation

Write in a {kwargs.get('tone', 'professional')} tone. Target length: {kwargs.get('word_count', 2000)} words."""

        elif blog_type == BlogType.GUIDE:
            return f"""Write a comprehensive guide about {topic}.

Topic: {topic}
Keywords: {keywords_str}
Target Audience: {kwargs.get('target_audience', 'general audience')}

Structure:
1. Introduction and overview
2. Key concepts and fundamentals
3. Detailed explanations with examples
4. Best practices
5. Common pitfalls to avoid
6. Advanced topics (if applicable)
7. Resources and further reading
8. Conclusion

Write in a {kwargs.get('tone', 'professional')} tone. Target length: {kwargs.get('word_count', 2000)} words."""

        else:  # CUSTOM
            custom_instructions = kwargs.get("custom_instructions", "")
            return f"""Write a comprehensive blog post about {topic}.

Keywords: {keywords_str}
Target Audience: {kwargs.get('target_audience', 'general audience')}
{custom_instructions}

Write in a {kwargs.get('tone', 'professional')} tone. Target length: {kwargs.get('word_count', 1500)} words."""
    
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
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate complete blog content using DataForSEO Content Generation API.
        
        This method:
        1. Generates subtopics from the topic
        2. Generates main content based on blog type
        3. Generates meta tags
        
        Args:
            topic: Main topic for the blog
            keywords: List of keywords to optimize for
            blog_type: Type of blog (brand, top_10, product_review, custom, etc.)
            tone: Writing tone (professional, casual, friendly, etc.)
            word_count: Target word count
            target_audience: Target audience description
            language: Language code (default: "en")
            tenant_id: Tenant ID
            **kwargs: Additional parameters specific to blog type:
                - brand_name: For BRAND type
                - category: For TOP_10 type
                - product_name: For PRODUCT_REVIEW type
                - items: List of items for COMPARISON type
                - custom_instructions: For CUSTOM type
        
        Returns:
            Dictionary with:
            - content: Generated blog content
            - title: Generated title
            - meta_title: SEO meta title
            - meta_description: SEO meta description
            - subtopics: List of subtopics
            - cost: Total API cost
            - tokens_used: Total tokens used
        """
        if not self.is_configured:
            await self.initialize(tenant_id)
        
        if not self.is_configured:
            raise ValueError("DataForSEO Content Generation Service not configured. Please check credentials.")
        
        total_cost = 0.0
        total_tokens = 0
        
        try:
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
            estimated_tokens = int(word_count / 0.75)
            max_tokens = min(estimated_tokens + 500, 4000)  # Add buffer, cap at 4000
            
            logger.info(f"Generating main content ({max_tokens} tokens max)")
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
            
            # Step 4: Generate title (use first part of content or topic)
            title = topic
            if generated_content:
                # Try to extract a title from the first line or use topic
                first_line = generated_content.split("\n")[0].strip()
                if len(first_line) < 100 and len(first_line) > 10:
                    title = first_line.replace("#", "").strip()
            
            # Step 5: Generate meta tags
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
                "metadata": {
                    "subtopics_count": len(subtopics),
                    "word_count": len(generated_content.split()),
                    "generation_steps": 3
                }
            }
            
        except Exception as e:
            logger.error(f"Blog content generation failed: {e}", exc_info=True)
            raise

