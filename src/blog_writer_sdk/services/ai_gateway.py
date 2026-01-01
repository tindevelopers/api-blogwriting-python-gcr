"""
AI Gateway Service

Centralized AI gateway for all LLM operations.
Routes all requests through LiteLLM proxy for caching, rate limiting, and cost tracking.

This service consolidates AI operations that were previously split between frontend and backend:
- Content generation (was backend)
- Content polishing (was frontend post-processor)
- Quality checks (was frontend quality-checker)
- Meta tag generation (was frontend post-processor)
"""

import os
import re
import json
import time
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

try:
    from litellm import acompletion
    LITELLM_AVAILABLE = True
except ImportError:
    LITELLM_AVAILABLE = False
    acompletion = None

logger = logging.getLogger(__name__)


# Model pricing (USD per 1K tokens) - Updated Dec 2024
MODEL_PRICING = {
    "gpt-4o": {"input": 0.0025, "output": 0.01},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "claude-3-5-sonnet": {"input": 0.003, "output": 0.015},
    "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
    "default": {"input": 0.002, "output": 0.008},
}


def calculate_cost(model: str, usage: Any) -> float:
    """Calculate cost based on model and token usage."""
    pricing = MODEL_PRICING.get(model, MODEL_PRICING["default"])
    prompt_cost = (usage.prompt_tokens / 1000) * pricing["input"]
    completion_cost = (usage.completion_tokens / 1000) * pricing["output"]
    return round(prompt_cost + completion_cost, 6)


class AIGateway:
    """
    Centralized AI gateway for all LLM operations.
    Routes all requests through LiteLLM proxy for caching, rate limiting, and cost tracking.
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        default_model: str = "gpt-4o",
        enable_caching: bool = True,
        cache_ttl: int = 3600,
    ):
        """
        Initialize AI Gateway.
        
        Args:
            base_url: LiteLLM proxy URL (defaults to LITELLM_PROXY_URL env var)
            api_key: LiteLLM API key (defaults to LITELLM_API_KEY env var)
            default_model: Default model to use for generation
            enable_caching: Whether to enable response caching
            cache_ttl: Cache time-to-live in seconds
        """
        self.base_url = base_url or os.getenv("LITELLM_PROXY_URL", "http://localhost:4000")
        self.api_key = api_key or os.getenv("LITELLM_API_KEY", "")
        self.default_model = default_model
        self.enable_caching = enable_caching
        self.cache_ttl = cache_ttl
        
        # Usage logger will be set after initialization to avoid circular imports
        self._usage_logger = None
        
        if not LITELLM_AVAILABLE:
            logger.warning("LiteLLM not installed. AI Gateway will use fallback mode.")
        
        if not self.base_url or self.base_url == "http://localhost:4000":
            logger.warning("LITELLM_PROXY_URL not set, using localhost. Configure for production use.")
        
        logger.info(f"AIGateway initialized with base_url: {self.base_url}, default_model: {self.default_model}")
    
    def set_usage_logger(self, logger_instance):
        """Set the usage logger instance."""
        self._usage_logger = logger_instance
    
    async def _log_usage(
        self,
        org_id: str,
        user_id: str,
        operation: str,
        model: str,
        response: Any,
        latency_ms: int,
        cached: bool = False
    ):
        """Log usage to database if logger is available."""
        if self._usage_logger and hasattr(response, 'usage'):
            try:
                await self._usage_logger.log_usage(
                    org_id=org_id,
                    user_id=user_id,
                    operation=operation,
                    model=model,
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens,
                    cost_usd=calculate_cost(model, response.usage),
                    latency_ms=latency_ms,
                    cached=cached
                )
            except Exception as e:
                logger.error(f"Failed to log usage: {e}")
    
    async def generate_content(
        self, 
        messages: List[Dict[str, str]], 
        org_id: str, 
        user_id: str, 
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate content with full metadata tracking.
        
        Args:
            messages: List of chat messages
            org_id: Organization ID for tracking
            user_id: User ID for tracking
            model: Model to use (defaults to default_model)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            metadata: Additional metadata for tracking
        
        Returns:
            Generated content as string
        """
        model = model or self.default_model
        start_time = time.time()
        
        try:
            if not LITELLM_AVAILABLE:
                # Fallback: Use direct OpenAI/Anthropic API
                return await self._fallback_generate(messages, model, temperature, max_tokens)
            
            # Build request kwargs
            kwargs = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "api_base": self.base_url,
                "api_key": self.api_key,
                "metadata": {
                    "org_id": org_id,
                    "user_id": user_id,
                    "operation": "content_generation",
                    "tags": ["blog", "generation"],
                    "timestamp": datetime.utcnow().isoformat(),
                    **(metadata or {})
                }
            }
            
            # Add caching if enabled
            if self.enable_caching:
                kwargs["cache"] = {
                    "enabled": True,
                    "ttl": self.cache_ttl
                }
            
            response = await acompletion(**kwargs)
            
            latency_ms = int((time.time() - start_time) * 1000)
            content = response.choices[0].message.content
            cached = getattr(response, '_hidden_params', {}).get('cache_hit', False)
            
            # Log usage
            await self._log_usage(org_id, user_id, "content_generation", model, response, latency_ms, cached)
            
            logger.info(f"Generated content: {len(content)} chars, model: {model}, org: {org_id}, latency: {latency_ms}ms")
            
            return content
            
        except Exception as e:
            logger.error(f"Content generation failed: {e}", exc_info=True)
            raise
    
    async def _fallback_generate(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: int
    ) -> str:
        """Fallback generation using direct API calls when LiteLLM is not available."""
        import httpx
        
        # Determine which API to use based on model name
        if "claude" in model.lower():
            # Use Anthropic API
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not set for Claude model")
            
            # Convert messages to Anthropic format
            system_message = ""
            anthropic_messages = []
            for msg in messages:
                if msg["role"] == "system":
                    system_message = msg["content"]
                else:
                    anthropic_messages.append(msg)
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json"
                    },
                    json={
                        "model": "claude-3-5-sonnet-20241022" if "sonnet" in model.lower() else "claude-3-haiku-20240307",
                        "max_tokens": max_tokens,
                        "system": system_message,
                        "messages": anthropic_messages
                    },
                    timeout=120.0
                )
                response.raise_for_status()
                data = response.json()
                return data["content"][0]["text"]
        else:
            # Use OpenAI API
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not set for OpenAI model")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model.replace("openai/", ""),
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens
                    },
                    timeout=120.0
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
    
    async def polish_content(
        self, 
        content: str, 
        instructions: str,
        org_id: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Polish and clean content.
        
        This was previously done in TypeScript frontend (post-processor.ts).
        Now consolidated in Python backend.
        
        Args:
            content: Raw content to polish
            instructions: Polishing instructions
            org_id: Organization ID
            user_id: Optional user ID
        
        Returns:
            Dict with polished_content, sanitization_applied, artifacts_removed, and metadata
        """
        start_time = time.time()
        
        # First, strip artifacts using comprehensive sanitizer (fast, no AI needed)
        cleaned_content, artifacts_list = self._strip_artifacts_with_report(content)
        artifacts_removed_count = len(content) - len(cleaned_content)
        sanitization_applied = len(artifacts_list) > 0
        
        # If minimal changes needed, skip AI polishing
        if artifacts_removed_count < 50 and len(cleaned_content) > 500:
            # Quick structural checks only
            return {
                "polished_content": cleaned_content,
                "original_length": len(content),
                "polished_length": len(cleaned_content),
                "artifacts_removed": artifacts_list,
                "artifacts_removed_count": artifacts_removed_count,
                "sanitization_applied": sanitization_applied,
                "ai_polished": False
            }
        
        # Use AI for intelligent polishing
        polish_prompt = f"""You are an expert content editor. Polish this blog content by:
1. Removing any remaining AI artifacts or thinking tags
2. Improving flow and readability
3. Fixing grammar and punctuation
4. Ensuring consistent tone
5. Keeping the original meaning intact

Additional instructions: {instructions}

Content to polish:
{cleaned_content}

Return ONLY the polished content, no explanations or meta-commentary."""

        messages = [
            {"role": "system", "content": "You are an expert content editor. Return only the polished content."},
            {"role": "user", "content": polish_prompt}
        ]
        
        try:
            polished = await self.generate_content(
                messages=messages,
                org_id=org_id,
                user_id=user_id or "system",
                model="gpt-4o-mini",  # Cheaper model for polishing
                temperature=0.3,  # Lower temp for consistency
                max_tokens=len(cleaned_content) + 500,
                metadata={"operation": "content_polishing"}
            )
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Apply sanitization to AI-polished content as well (in case AI added artifacts)
            final_content, final_artifacts = self._strip_artifacts_with_report(polished)
            all_artifacts = artifacts_list + final_artifacts
            
            return {
                "polished_content": final_content,
                "original_length": len(content),
                "polished_length": len(final_content),
                "artifacts_removed": all_artifacts,
                "artifacts_removed_count": len(content) - len(final_content),
                "sanitization_applied": True,
                "ai_polished": True,
                "latency_ms": latency_ms
            }
            
        except Exception as e:
            logger.error(f"Content polishing failed: {e}", exc_info=True)
            # Fallback to cleaned content without AI polishing
            return {
                "polished_content": cleaned_content,
                "original_length": len(content),
                "polished_length": len(cleaned_content),
                "artifacts_removed": artifacts_list,
                "artifacts_removed_count": artifacts_removed_count,
                "sanitization_applied": sanitization_applied,
                "ai_polished": False,
                "error": str(e)
            }
    
    def _strip_artifacts(self, content: str) -> str:
        """
        Strip AI artifacts from content.
        
        Uses the comprehensive content_sanitizer module for thorough artifact removal.
        
        Args:
            content: Raw content with potential artifacts
            
        Returns:
            Cleaned content
        """
        if not content:
            return content
        
        # Use comprehensive sanitizer
        from ..utils.content_sanitizer import sanitize_llm_output
        cleaned, _ = sanitize_llm_output(content)
        return cleaned
    
    def _strip_artifacts_with_report(self, content: str) -> tuple:
        """
        Strip AI artifacts from content and return a report of what was removed.
        
        Args:
            content: Raw content with potential artifacts
            
        Returns:
            Tuple of (cleaned_content, artifacts_removed_list)
        """
        if not content:
            return content, []
        
        from ..utils.content_sanitizer import sanitize_llm_output
        return sanitize_llm_output(content)
    
    async def generate_excerpt(
        self,
        content: str,
        org_id: str,
        primary_keyword: Optional[str] = None,
        user_id: Optional[str] = None,
        max_length: int = 160
    ) -> Dict[str, Any]:
        """
        Generate a high-quality excerpt/meta description using a dedicated LLM call.
        
        This creates a compelling meta description that:
        - Is exactly 150-160 characters
        - Includes the primary keyword naturally
        - Has a call-to-action or engaging hook
        - Ends with proper punctuation (not cut off mid-sentence)
        
        Args:
            content: Full blog content to summarize
            org_id: Organization ID
            primary_keyword: Primary keyword to include
            user_id: Optional user ID
            max_length: Maximum character length (default 160)
            
        Returns:
            Dict with excerpt, character_count, and metadata
        """
        # Extract first 1500 chars for context (introduction + first section)
        content_preview = content[:1500] if len(content) > 1500 else content
        
        keyword_instruction = f"- Include the keyword '{primary_keyword}' naturally" if primary_keyword else ""
        
        excerpt_prompt = f"""Create a compelling meta description for this blog post.

REQUIREMENTS:
- EXACTLY 150-160 characters (this is critical for SEO)
- Write a complete, engaging sentence
- Include a hook or value proposition
- End with proper punctuation (period, exclamation, or question mark)
- DO NOT end mid-sentence or use ellipsis
{keyword_instruction}

CONTENT:
{content_preview}

OUTPUT ONLY the meta description text, nothing else. No quotes, no explanation, just the text."""

        messages = [
            {
                "role": "system", 
                "content": "You are an SEO specialist. Output only the meta description text, exactly 150-160 characters."
            },
            {"role": "user", "content": excerpt_prompt}
        ]
        
        try:
            excerpt = await self.generate_content(
                messages=messages,
                org_id=org_id,
                user_id=user_id or "system",
                model="gpt-4o-mini",  # Fast and efficient for short outputs
                temperature=0.5,
                max_tokens=100,
                metadata={"operation": "excerpt_generation"}
            )
            
            # Clean and sanitize the excerpt
            from ..utils.content_sanitizer import sanitize_excerpt
            cleaned_excerpt = sanitize_excerpt(excerpt.strip(), primary_keyword)
            
            # Ensure proper length
            if len(cleaned_excerpt) > max_length:
                # Find last complete sentence within limit
                for end_char in ['. ', '! ', '? ']:
                    last_pos = cleaned_excerpt[:max_length-3].rfind(end_char)
                    if last_pos > 100:
                        cleaned_excerpt = cleaned_excerpt[:last_pos + 1]
                        break
                else:
                    # No sentence end found, truncate at word boundary
                    cleaned_excerpt = cleaned_excerpt[:max_length-3].rsplit(' ', 1)[0] + '...'
            
            return {
                "excerpt": cleaned_excerpt,
                "character_count": len(cleaned_excerpt),
                "within_limit": len(cleaned_excerpt) <= max_length,
                "contains_keyword": primary_keyword.lower() in cleaned_excerpt.lower() if primary_keyword else None
            }
            
        except Exception as e:
            logger.error(f"Excerpt generation failed: {e}", exc_info=True)
            
            # Fallback: Extract first sentence from content
            from ..utils.content_sanitizer import sanitize_excerpt
            
            # Find first paragraph (skip title)
            lines = content.split('\n')
            first_para = ""
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#') and len(line) > 50:
                    first_para = line
                    break
            
            fallback = sanitize_excerpt(first_para[:200], primary_keyword)
            
            return {
                "excerpt": fallback,
                "character_count": len(fallback),
                "within_limit": len(fallback) <= max_length,
                "contains_keyword": primary_keyword.lower() in fallback.lower() if primary_keyword else None,
                "is_fallback": True,
                "error": str(e)
            }
    
    async def check_quality(self, content: str) -> Dict[str, Any]:
        """
        Check content quality.
        
        Python port of quality-checker.ts from frontend.
        
        Args:
            content: Content to check
        
        Returns:
            Dict with quality_score, issues, and cleaned_content
        """
        issues = []
        
        # Check for remaining artifacts
        artifact_patterns = [
            (r'<thinking>|<thought>|<reasoning>', "AI thinking artifacts found"),
            (r'\[THINKING\]|\[THOUGHT\]', "AI thinking brackets found"),
            (r'<internal>|<reflection>', "Internal reflection tags found"),
        ]
        
        for pattern, message in artifact_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                issues.append({
                    "type": "artifacts",
                    "severity": "high",
                    "message": message
                })
        
        # Check content length
        word_count = len(content.split())
        if word_count < 300:
            issues.append({
                "type": "length",
                "severity": "medium",
                "message": f"Content is short ({word_count} words, recommended: 300+)"
            })
        elif word_count < 100:
            issues.append({
                "type": "length",
                "severity": "high",
                "message": f"Content is very short ({word_count} words)"
            })
        
        # Check for placeholder text
        placeholders = ['[INSERT', '[TODO', '[TK]', 'Lorem ipsum', '[PLACEHOLDER', '[ADD']
        for placeholder in placeholders:
            if placeholder.lower() in content.lower():
                issues.append({
                    "type": "placeholder",
                    "severity": "high",
                    "message": f"Placeholder text found: {placeholder}"
                })
        
        # Check heading structure
        h2_count = len(re.findall(r'^##\s+', content, re.MULTILINE))
        h1_count = len(re.findall(r'^#\s+[^#]', content, re.MULTILINE))
        
        if h2_count < 2:
            issues.append({
                "type": "structure",
                "severity": "low",
                "message": f"Only {h2_count} H2 headings (recommended: 2+)"
            })
        
        if h1_count > 1:
            issues.append({
                "type": "structure",
                "severity": "medium",
                "message": f"Multiple H1 headings found ({h1_count}), should have only 1"
            })
        
        # Check for proper intro/conclusion
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip() and not p.strip().startswith('#')]
        if len(paragraphs) < 3:
            issues.append({
                "type": "structure",
                "severity": "medium",
                "message": "Content lacks proper structure (intro, body, conclusion)"
            })
        
        # Calculate quality score (0-100)
        score = 100
        for issue in issues:
            if issue["severity"] == "high":
                score -= 20
            elif issue["severity"] == "medium":
                score -= 10
            else:
                score -= 5
        
        score = max(0, min(100, score))
        
        # Determine quality grade
        if score >= 90:
            grade = "excellent"
        elif score >= 75:
            grade = "good"
        elif score >= 60:
            grade = "fair"
        elif score >= 40:
            grade = "poor"
        else:
            grade = "needs_improvement"
        
        return {
            "quality_score": score,
            "quality_grade": grade,
            "issues": issues,
            "word_count": word_count,
            "h2_count": h2_count,
            "paragraph_count": len(paragraphs),
            "cleaned_content": self._strip_artifacts(content)
        }
    
    async def generate_meta_tags(
        self, 
        content: str, 
        title: str, 
        keywords: List[str],
        org_id: str,
        user_id: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Generate SEO-optimized meta tags.
        
        Python port of meta tag generation from frontend post-processor.ts.
        
        Args:
            content: Full content
            title: Original title
            keywords: Target keywords
            org_id: Organization ID
            user_id: Optional user ID
        
        Returns:
            Dict with title, description, og_title, og_description
        """
        prompt = f"""Generate SEO-optimized meta tags for this blog post.

Title: {title}
Keywords: {', '.join(keywords[:5])}
Content Preview: {content[:1500]}

Return a JSON object with exactly these fields:
- title: SEO title (50-60 characters, include primary keyword near the beginning)
- description: Meta description (150-160 characters, compelling, includes keywords naturally)
- og_title: Open Graph title (can be slightly longer, more engaging)
- og_description: Open Graph description (can be more descriptive, up to 200 chars)

Return ONLY valid JSON, no markdown code blocks, no explanations."""

        try:
            response = await self.generate_content(
                messages=[
                    {"role": "system", "content": "You are an SEO expert. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                org_id=org_id,
                user_id=user_id or "system",
                model="gpt-4o-mini",
                temperature=0.3,
                max_tokens=500,
                metadata={"operation": "meta_tag_generation"}
            )
            
            # Parse JSON response
            # Clean up response in case it has markdown code blocks
            clean_response = response.strip()
            if clean_response.startswith("```"):
                clean_response = re.sub(r'^```\w*\n?', '', clean_response)
                clean_response = re.sub(r'\n?```$', '', clean_response)
            
            result = json.loads(clean_response)
            
            # Validate and return
            return {
                "title": result.get("title", title[:60]),
                "description": result.get("description", self._extract_excerpt(content, 160)),
                "og_title": result.get("og_title", title),
                "og_description": result.get("og_description", self._extract_excerpt(content, 200))
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse meta tags JSON: {e}")
            # Fallback to basic extraction
            return self._generate_fallback_meta_tags(title, content, keywords)
        except Exception as e:
            logger.error(f"Meta tag generation failed: {e}", exc_info=True)
            return self._generate_fallback_meta_tags(title, content, keywords)
    
    def _generate_fallback_meta_tags(self, title: str, content: str, keywords: List[str]) -> Dict[str, str]:
        """Generate basic meta tags without AI."""
        description = self._extract_excerpt(content, 160)
        
        # Try to include primary keyword in title if not already present
        seo_title = title
        if keywords and keywords[0].lower() not in title.lower():
            if len(title) + len(keywords[0]) + 3 <= 60:
                seo_title = f"{title} - {keywords[0].title()}"
        
        if len(seo_title) > 60:
            seo_title = seo_title[:57] + "..."
        
        return {
            "title": seo_title,
            "description": description,
            "og_title": title,
            "og_description": self._extract_excerpt(content, 200)
        }
    
    def _extract_excerpt(self, content: str, max_length: int) -> str:
        """Extract an excerpt from content."""
        # Remove markdown/HTML formatting
        plain = re.sub(r'[#*`<>\[\]]', '', content)
        plain = re.sub(r'\!?\[([^\]]*)\]\([^\)]*\)', r'\1', plain)  # Remove links/images
        plain = re.sub(r'\s+', ' ', plain).strip()
        
        if len(plain) <= max_length:
            return plain
        
        # Cut at word boundary
        truncated = plain[:max_length]
        last_space = truncated.rfind(' ')
        
        if last_space > max_length * 0.7:  # Only cut at space if reasonably close to end
            truncated = truncated[:last_space]
        
        return truncated.rstrip('.,;:') + '...'
    
    async def generate_complete_blog(
        self,
        topic: str,
        keywords: List[str],
        org_id: str,
        user_id: str,
        word_count: int = 1500,
        tone: str = "professional",
        custom_instructions: str = "",
        include_polishing: bool = True,
        include_quality_check: bool = True,
        include_meta_tags: bool = True
    ) -> Dict[str, Any]:
        """
        Complete blog generation with polishing, quality checks, and meta tags.
        
        This method handles the full pipeline that was previously split between backend and frontend.
        
        Args:
            topic: Blog topic
            keywords: Target keywords
            org_id: Organization ID
            user_id: User ID
            word_count: Target word count
            tone: Content tone
            custom_instructions: Additional instructions
            include_polishing: Whether to polish content
            include_quality_check: Whether to run quality checks
            include_meta_tags: Whether to generate meta tags
        
        Returns:
            Complete blog with content, quality score, meta tags
        """
        start_time = time.time()
        
        try:
            # Step 1: Generate raw content
            logger.info(f"Generating content for topic: {topic}")
            
            messages = self._build_generation_prompt(
                topic=topic,
                keywords=keywords,
                word_count=word_count,
                tone=tone,
                custom_instructions=custom_instructions
            )
            
            raw_content = await self.generate_content(
                messages=messages,
                org_id=org_id,
                user_id=user_id,
                model=self.default_model
            )
            
            result = {
                "content": raw_content,
                "title": topic,
                "raw_content": raw_content,
                "model_used": self.default_model,
                "generated_at": datetime.utcnow().isoformat()
            }
            
            # Step 2: Polish content (optional)
            if include_polishing:
                logger.info("Polishing content")
                polish_result = await self.polish_content(
                    content=raw_content,
                    instructions=f"Ensure {tone} tone, remove artifacts",
                    org_id=org_id,
                    user_id=user_id
                )
                result["content"] = polish_result["polished_content"]
                result["artifacts_removed"] = polish_result.get("artifacts_removed", 0)
                result["ai_polished"] = polish_result.get("ai_polished", False)
            
            # Step 3: Quality check (optional)
            if include_quality_check:
                logger.info("Checking quality")
                quality_result = await self.check_quality(result["content"])
                result["quality_score"] = quality_result["quality_score"]
                result["quality_grade"] = quality_result["quality_grade"]
                result["quality_issues"] = quality_result["issues"]
                result["word_count"] = quality_result["word_count"]
            else:
                result["word_count"] = len(result["content"].split())
            
            # Step 4: Generate meta tags (optional)
            if include_meta_tags:
                logger.info("Generating meta tags")
                meta_tags = await self.generate_meta_tags(
                    content=result["content"],
                    title=topic,
                    keywords=keywords,
                    org_id=org_id,
                    user_id=user_id
                )
                result["meta_tags"] = meta_tags
            
            # Calculate total processing time
            result["processing_time"] = round(time.time() - start_time, 2)
            
            logger.info(
                f"Blog generation complete: {result.get('word_count', 'N/A')} words, "
                f"quality: {result.get('quality_grade', 'N/A')}, "
                f"time: {result['processing_time']}s"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Blog generation failed: {e}", exc_info=True)
            raise
    
    def _build_generation_prompt(
        self,
        topic: str,
        keywords: List[str],
        word_count: int,
        tone: str,
        custom_instructions: str
    ) -> List[Dict[str, str]]:
        """Build the generation prompt messages."""
        
        keywords_str = ', '.join(keywords[:5]) if keywords else 'none specified'
        
        system_prompt = f"""You are an expert blog writer creating high-quality, SEO-optimized content that sounds natural and human-written.

Write a comprehensive, {tone} blog post about: {topic}

Requirements:
- Target length: approximately {word_count} words
- Include these keywords naturally throughout the content: {keywords_str}
- Use proper markdown formatting:
  - One H1 heading (the title)
  - Multiple H2 headings for main sections
  - H3 headings for subsections where appropriate
- Structure:
  - Engaging introduction that hooks the reader
  - Well-organized body with clear sections
  - Strong conclusion with key takeaways or call to action
- Write in a {tone} tone
- Make it engaging, informative, and valuable to readers
- Include specific examples, data, or actionable advice where relevant

NATURAL WRITING STYLE (CRITICAL):
- Write conversationally, like explaining to a friend
- Use contractions naturally (it's, don't, we'll, can't)
- Vary sentence length - mix short punchy sentences with longer ones
- AVOID obvious AI transition words: "Moreover", "Furthermore", "Additionally", "In conclusion", "In summary"
- Instead use natural transitions: "Here's the thing", "So", "Now", "The bottom line", or continue naturally
- Start conclusions naturally, NOT with "In conclusion" or "To sum up"

{f"Additional instructions: {custom_instructions}" if custom_instructions else ""}

CRITICAL: Return ONLY the blog content in markdown format. 
- Do NOT include thinking tags, meta-commentary, or explanations.
- Do NOT wrap the content in code blocks.
- Start directly with the title heading."""

        user_prompt = f"""Write a {word_count}-word blog post about: {topic}

Primary keywords to incorporate: {keywords_str}

Begin with an H1 title and structure the content with H2 sections."""

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]


# Singleton instance
_gateway_instance: Optional[AIGateway] = None


def get_ai_gateway() -> AIGateway:
    """Get singleton AI gateway instance."""
    global _gateway_instance
    if _gateway_instance is None:
        _gateway_instance = AIGateway()
    return _gateway_instance


def initialize_ai_gateway(
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    default_model: str = "gpt-4o"
) -> AIGateway:
    """Initialize and return AI gateway with custom configuration."""
    global _gateway_instance
    _gateway_instance = AIGateway(
        base_url=base_url,
        api_key=api_key,
        default_model=default_model
    )
    return _gateway_instance
