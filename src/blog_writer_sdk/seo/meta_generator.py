"""
Meta tag generation module for SEO optimization.

This module generates SEO-optimized meta tags including titles,
descriptions, and social media tags.
"""

import re
from typing import List, Optional
from urllib.parse import urljoin

from ..models.blog_models import MetaTags
from ..utils.text_utils import clean_text_for_excerpt, truncate_text


class MetaTagGenerator:
    """
    Generates SEO-optimized meta tags for blog content.
    
    This class creates meta tags following SEO best practices
    for search engines and social media platforms.
    """
    
    def __init__(self):
        """Initialize the meta tag generator."""
        self.title_max_length = 60
        self.description_max_length = 160
        self.og_title_max_length = 95
        self.og_description_max_length = 300
        self.twitter_title_max_length = 70
        self.twitter_description_max_length = 200
    
    async def generate_meta_tags(
        self,
        title: str,
        content: str,
        keywords: Optional[List[str]] = None,
        focus_keyword: Optional[str] = None,
        canonical_url: Optional[str] = None,
        image_url: Optional[str] = None,
        author: Optional[str] = None,
    ) -> MetaTags:
        """
        Generate comprehensive meta tags for a blog post.
        
        Args:
            title: Blog post title
            content: Blog post content
            keywords: Target keywords
            focus_keyword: Primary focus keyword
            canonical_url: Canonical URL for the post
            image_url: Featured image URL
            author: Author name
            
        Returns:
            MetaTags object with all generated tags
        """
        # Generate SEO title
        seo_title = self._generate_seo_title(title, focus_keyword)
        
        # Generate meta description
        meta_description = self._generate_meta_description(content, focus_keyword, keywords)
        
        # Generate Open Graph tags
        og_title = self._generate_og_title(title, focus_keyword)
        og_description = self._generate_og_description(content, focus_keyword)
        
        # Generate Twitter Card tags
        twitter_title = self._generate_twitter_title(title, focus_keyword)
        twitter_description = self._generate_twitter_description(content, focus_keyword)
        
        # Prepare keywords list
        meta_keywords = self._prepare_meta_keywords(keywords, focus_keyword)
        
        return MetaTags(
            title=seo_title,
            description=meta_description,
            keywords=meta_keywords,
            canonical_url=canonical_url,
            og_title=og_title,
            og_description=og_description,
            og_image=image_url,
            og_type="article",
            twitter_card="summary_large_image",
            twitter_title=twitter_title,
            twitter_description=twitter_description,
            twitter_image=image_url,
        )
    
    async def optimize_existing_meta_tags(
        self,
        existing_tags: MetaTags,
        content: str,
        focus_keyword: Optional[str] = None,
    ) -> MetaTags:
        """
        Optimize existing meta tags for better SEO.
        
        Args:
            existing_tags: Current meta tags
            content: Blog post content
            focus_keyword: Primary focus keyword
            
        Returns:
            Optimized MetaTags object
        """
        optimized_tags = existing_tags.copy()
        
        # Optimize title if needed
        if len(existing_tags.title) > self.title_max_length or len(existing_tags.title) < 30:
            optimized_tags.title = self._generate_seo_title(existing_tags.title, focus_keyword)
        
        # Optimize description if needed
        if (len(existing_tags.description) > self.description_max_length or 
            len(existing_tags.description) < 120):
            optimized_tags.description = self._generate_meta_description(
                content, focus_keyword
            )
        
        # Ensure Open Graph tags are present
        if not existing_tags.og_title:
            optimized_tags.og_title = self._generate_og_title(existing_tags.title, focus_keyword)
        
        if not existing_tags.og_description:
            optimized_tags.og_description = self._generate_og_description(content, focus_keyword)
        
        # Ensure Twitter Card tags are present
        if not existing_tags.twitter_title:
            optimized_tags.twitter_title = self._generate_twitter_title(
                existing_tags.title, focus_keyword
            )
        
        if not existing_tags.twitter_description:
            optimized_tags.twitter_description = self._generate_twitter_description(
                content, focus_keyword
            )
        
        return optimized_tags
    
    def _generate_seo_title(self, title: str, focus_keyword: Optional[str] = None) -> str:
        """Generate SEO-optimized title."""
        if not title:
            return "Untitled"
        
        # If focus keyword is provided and not in title, try to include it
        if focus_keyword and focus_keyword.lower() not in title.lower():
            # Try to naturally incorporate the focus keyword
            if len(title) + len(focus_keyword) + 3 <= self.title_max_length:  # +3 for " - "
                enhanced_title = f"{title} - {focus_keyword.title()}"
            else:
                # If too long, prioritize focus keyword
                max_title_length = self.title_max_length - len(focus_keyword) - 3
                if max_title_length > 20:  # Ensure reasonable title length
                    truncated_title = truncate_text(title, max_title_length, "")
                    enhanced_title = f"{focus_keyword.title()} - {truncated_title}"
                else:
                    enhanced_title = title
        else:
            enhanced_title = title
        
        # Ensure title is within optimal length
        if len(enhanced_title) > self.title_max_length:
            enhanced_title = truncate_text(enhanced_title, self.title_max_length, "")
        
        return enhanced_title
    
    def _generate_meta_description(
        self,
        content: str,
        focus_keyword: Optional[str] = None,
        keywords: Optional[List[str]] = None,
    ) -> str:
        """Generate SEO-optimized meta description."""
        # Clean content for excerpt
        clean_content = clean_text_for_excerpt(content)
        
        # Try to create description that includes focus keyword
        if focus_keyword:
            # Look for sentences containing the focus keyword
            sentences = clean_content.split('. ')
            keyword_sentences = [
                sentence for sentence in sentences 
                if focus_keyword.lower() in sentence.lower()
            ]
            
            if keyword_sentences:
                # Use the first sentence with the keyword as base
                base_description = keyword_sentences[0]
                
                # Extend with additional context if needed
                if len(base_description) < 100:
                    # Find the index of this sentence in original content
                    try:
                        sentence_index = sentences.index(keyword_sentences[0])
                        # Add next sentence if available and fits
                        if (sentence_index + 1 < len(sentences) and 
                            len(base_description) + len(sentences[sentence_index + 1]) < 140):
                            base_description += f". {sentences[sentence_index + 1]}"
                    except ValueError:
                        pass
                
                description = base_description
            else:
                # Focus keyword not found in sentences, create from excerpt
                excerpt = clean_content[:120]
                if focus_keyword:
                    description = f"Learn about {focus_keyword}. {excerpt}"
                else:
                    description = excerpt
        else:
            # No focus keyword, use content excerpt
            description = clean_content[:140]
        
        # Ensure description ends properly
        if not description.endswith('.'):
            # Find last complete sentence
            last_period = description.rfind('.')
            if last_period > len(description) * 0.7:  # At least 70% of description
                description = description[:last_period + 1]
            else:
                description = description.rstrip() + "."
        
        # Ensure optimal length
        if len(description) > self.description_max_length:
            description = truncate_text(description, self.description_max_length - 3, "...")
        elif len(description) < 120:
            # Try to expand if too short
            if len(clean_content) > len(description):
                additional_content = clean_content[len(description):].split('.')[0]
                if len(description) + len(additional_content) <= self.description_max_length:
                    description += additional_content + "."
        
        return description
    
    def _generate_og_title(self, title: str, focus_keyword: Optional[str] = None) -> str:
        """Generate Open Graph title."""
        # Open Graph titles can be slightly longer than SEO titles
        og_title = title
        
        if focus_keyword and focus_keyword.lower() not in title.lower():
            if len(title) + len(focus_keyword) + 3 <= self.og_title_max_length:
                og_title = f"{title} - {focus_keyword.title()}"
        
        if len(og_title) > self.og_title_max_length:
            og_title = truncate_text(og_title, self.og_title_max_length, "")
        
        return og_title
    
    def _generate_og_description(
        self, content: str, focus_keyword: Optional[str] = None
    ) -> str:
        """Generate Open Graph description."""
        # OG descriptions can be longer than meta descriptions
        clean_content = clean_text_for_excerpt(content)
        
        # Create engaging description for social sharing
        if focus_keyword:
            og_description = f"Discover everything you need to know about {focus_keyword}. "
            remaining_length = self.og_description_max_length - len(og_description)
            og_description += clean_content[:remaining_length]
        else:
            og_description = clean_content[:self.og_description_max_length]
        
        # Ensure proper ending
        if len(og_description) == self.og_description_max_length:
            og_description = truncate_text(og_description, self.og_description_max_length, "...")
        
        return og_description
    
    def _generate_twitter_title(self, title: str, focus_keyword: Optional[str] = None) -> str:
        """Generate Twitter Card title."""
        # Twitter titles should be shorter and more engaging
        twitter_title = title
        
        if len(twitter_title) > self.twitter_title_max_length:
            twitter_title = truncate_text(twitter_title, self.twitter_title_max_length, "")
        
        return twitter_title
    
    def _generate_twitter_description(
        self, content: str, focus_keyword: Optional[str] = None
    ) -> str:
        """Generate Twitter Card description."""
        clean_content = clean_text_for_excerpt(content)
        
        # Create concise, engaging description for Twitter
        twitter_description = clean_content[:self.twitter_description_max_length]
        
        if len(twitter_description) == self.twitter_description_max_length:
            twitter_description = truncate_text(
                twitter_description, self.twitter_description_max_length, "..."
            )
        
        return twitter_description
    
    def _prepare_meta_keywords(
        self, keywords: Optional[List[str]], focus_keyword: Optional[str]
    ) -> List[str]:
        """Prepare meta keywords list."""
        meta_keywords = []
        
        # Add focus keyword first
        if focus_keyword:
            meta_keywords.append(focus_keyword.lower())
        
        # Add other keywords
        if keywords:
            for keyword in keywords:
                keyword_lower = keyword.lower()
                if keyword_lower not in meta_keywords:
                    meta_keywords.append(keyword_lower)
        
        # Limit to reasonable number of keywords
        return meta_keywords[:10]
    
    def validate_meta_tags(self, meta_tags: MetaTags) -> List[str]:
        """
        Validate meta tags and return list of issues.
        
        Args:
            meta_tags: Meta tags to validate
            
        Returns:
            List of validation issues
        """
        issues = []
        
        # Title validation
        if not meta_tags.title:
            issues.append("Missing title tag")
        elif len(meta_tags.title) < 30:
            issues.append(f"Title too short ({len(meta_tags.title)} chars) - should be 30-60 characters")
        elif len(meta_tags.title) > 60:
            issues.append(f"Title too long ({len(meta_tags.title)} chars) - should be 30-60 characters")
        
        # Description validation
        if not meta_tags.description:
            issues.append("Missing meta description")
        elif len(meta_tags.description) < 120:
            issues.append(f"Meta description too short ({len(meta_tags.description)} chars) - should be 120-160 characters")
        elif len(meta_tags.description) > 160:
            issues.append(f"Meta description too long ({len(meta_tags.description)} chars) - should be 120-160 characters")
        
        # Open Graph validation
        if not meta_tags.og_title:
            issues.append("Missing Open Graph title")
        if not meta_tags.og_description:
            issues.append("Missing Open Graph description")
        
        # Twitter Card validation
        if not meta_tags.twitter_title:
            issues.append("Missing Twitter Card title")
        if not meta_tags.twitter_description:
            issues.append("Missing Twitter Card description")
        
        # Keywords validation
        if len(meta_tags.keywords) > 10:
            issues.append(f"Too many meta keywords ({len(meta_tags.keywords)}) - limit to 10")
        
        return issues
