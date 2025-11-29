"""
Field Enhancement API Endpoint

This module provides a lightweight endpoint for enhancing mandatory CMS fields
(SEO title, meta description, slug, featured image alt text) using OpenAI.
"""

import os
import logging
import re
from typing import Dict, List, Optional, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..ai.openai_provider import OpenAIProvider
from ..ai.base_provider import AIRequest, ContentType, AIGenerationConfig

logger = logging.getLogger(__name__)

# Create router for field enhancement endpoints
router = APIRouter(prefix="/api/v1/content", tags=["Field Enhancement"])

# Global OpenAI provider instance (initialized on first use)
_openai_provider: Optional[OpenAIProvider] = None


def get_openai_provider() -> Optional[OpenAIProvider]:
    """Get or initialize OpenAI provider."""
    global _openai_provider
    
    if _openai_provider is None:
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            return None
        
        try:
            _openai_provider = OpenAIProvider(
                api_key=openai_api_key,
                organization=os.getenv("OPENAI_ORGANIZATION"),
                max_retries=3,
                timeout=30
            )
            logger.info("OpenAI provider initialized for field enhancement")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI provider: {e}")
            return None
    
    return _openai_provider


class FieldEnhancementRequest(BaseModel):
    """Request model for field enhancement."""
    
    # Required - existing content to enhance
    title: str = Field(..., min_length=1, max_length=200, description="Current title")
    content: Optional[str] = Field(None, max_length=5000, description="Optional: content excerpt for context")
    featured_image_url: Optional[str] = Field(None, description="Optional: URL of featured image")
    
    # Optional - fields to enhance
    enhance_seo_title: bool = Field(default=True, description="Enhance SEO title")
    enhance_meta_description: bool = Field(default=True, description="Enhance meta description")
    enhance_slug: bool = Field(default=True, description="Enhance slug")
    enhance_image_alt: bool = Field(default=True, description="Enhance featured image alt text")
    
    # Optional - context
    keywords: Optional[List[str]] = Field(default_factory=list, max_length=10, description="SEO keywords for optimization")
    target_audience: Optional[str] = Field(None, max_length=200, description="Target audience context")


class EnhancedFields(BaseModel):
    """Enhanced field values."""
    seo_title: Optional[str] = Field(None, description="SEO-optimized title (50-60 chars)")
    meta_description: Optional[str] = Field(None, description="Meta description (150-160 chars)")
    slug: Optional[str] = Field(None, description="SEO-friendly slug")
    featured_image_alt: Optional[str] = Field(None, description="Alt text for featured image")


class FieldEnhancementResponse(BaseModel):
    """Response model for field enhancement."""
    enhanced_fields: EnhancedFields = Field(..., description="Enhanced field values")
    original_fields: Dict[str, Any] = Field(..., description="Original field values")
    enhanced_at: str = Field(..., description="ISO timestamp of enhancement")
    provider: str = Field(default="openai", description="AI provider used")
    model: Optional[str] = Field(None, description="Model used for generation")


def _build_enhancement_prompt(
    title: str,
    content: Optional[str],
    keywords: List[str],
    target_audience: Optional[str],
    enhance_seo_title: bool,
    enhance_meta_description: bool,
    enhance_slug: bool,
    enhance_image_alt: bool,
    featured_image_url: Optional[str]
) -> str:
    """Build prompt for field enhancement."""
    
    prompt_parts = [
        "You are an SEO specialist optimizing CMS field values for maximum search engine visibility.",
        "",
        f"CURRENT TITLE: {title}",
    ]
    
    if content:
        content_preview = content[:1000] + "..." if len(content) > 1000 else content
        prompt_parts.append(f"CONTENT EXCERPT: {content_preview}")
    
    if keywords:
        prompt_parts.append(f"TARGET KEYWORDS: {', '.join(keywords)}")
    
    if target_audience:
        prompt_parts.append(f"TARGET AUDIENCE: {target_audience}")
    
    if featured_image_url:
        prompt_parts.append(f"FEATURED IMAGE URL: {featured_image_url}")
    
    prompt_parts.append("")
    prompt_parts.append("ENHANCEMENT TASKS:")
    
    if enhance_seo_title:
        prompt_parts.append("1. SEO Title - Create an SEO-optimized title (50-60 characters) that includes primary keywords")
    
    if enhance_meta_description:
        prompt_parts.append("2. Meta Description - Write a compelling meta description (150-160 characters) with primary keyword and call-to-action")
    
    if enhance_slug:
        prompt_parts.append("3. Slug - Create an SEO-friendly URL slug (lowercase, hyphens, no special characters)")
    
    if enhance_image_alt and featured_image_url:
        prompt_parts.append("4. Featured Image Alt Text - Write descriptive, keyword-rich alt text for the featured image")
    
    prompt_parts.append("")
    prompt_parts.append("OUTPUT FORMAT:")
    prompt_parts.append("Provide your response in the following exact format:")
    prompt_parts.append("")
    
    if enhance_seo_title:
        prompt_parts.append("SEO Title: [Your SEO-optimized title here - 50-60 characters]")
    
    if enhance_meta_description:
        prompt_parts.append("Meta Description: [Your compelling meta description here - 150-160 characters]")
    
    if enhance_slug:
        prompt_parts.append("Slug: [seo-friendly-url-slug]")
    
    if enhance_image_alt and featured_image_url:
        prompt_parts.append("Featured Image Alt Text: [Descriptive alt text for the featured image]")
    
    prompt_parts.append("")
    prompt_parts.append("IMPORTANT:")
    prompt_parts.append("- SEO Title MUST be 50-60 characters and include primary keywords")
    prompt_parts.append("- Meta Description MUST be 150-160 characters with a call-to-action")
    prompt_parts.append("- Slug MUST be lowercase, use hyphens, and be URL-friendly")
    prompt_parts.append("- All values should be optimized for search engines while remaining human-readable")
    
    return "\n".join(prompt_parts)


def _parse_enhanced_fields(
    ai_response: str,
    enhance_seo_title: bool,
    enhance_meta_description: bool,
    enhance_slug: bool,
    enhance_image_alt: bool
) -> Dict[str, Optional[str]]:
    """Parse enhanced fields from AI response."""
    
    enhanced = {
        "seo_title": None,
        "meta_description": None,
        "slug": None,
        "featured_image_alt": None
    }
    
    # Parse SEO Title
    if enhance_seo_title:
        seo_title_match = re.search(r'SEO Title:\s*(.+?)(?:\n|$)', ai_response, re.IGNORECASE)
        if seo_title_match:
            enhanced["seo_title"] = seo_title_match.group(1).strip()
    
    # Parse Meta Description
    if enhance_meta_description:
        meta_desc_match = re.search(r'Meta Description:\s*(.+?)(?:\n|$)', ai_response, re.IGNORECASE)
        if meta_desc_match:
            enhanced["meta_description"] = meta_desc_match.group(1).strip()
    
    # Parse Slug
    if enhance_slug:
        slug_match = re.search(r'Slug:\s*(.+?)(?:\n|$)', ai_response, re.IGNORECASE)
        if slug_match:
            enhanced["slug"] = slug_match.group(1).strip()
    
    # Parse Featured Image Alt Text
    if enhance_image_alt:
        alt_match = re.search(r'Featured Image Alt Text:\s*(.+?)(?:\n|$)', ai_response, re.IGNORECASE)
        if alt_match:
            enhanced["featured_image_alt"] = alt_match.group(1).strip()
    
    return enhanced


def _generate_slug_fallback(title: str) -> str:
    """Generate a slug from title as fallback."""
    slug = title.lower()
    slug = re.sub(r'[^\w\s-]', '', slug)  # Remove special characters
    slug = re.sub(r'[-\s]+', '-', slug)   # Replace spaces with hyphens
    slug = slug.strip('-')                # Remove leading/trailing hyphens
    return slug


@router.post("/enhance-fields", response_model=FieldEnhancementResponse)
async def enhance_fields(request: FieldEnhancementRequest):
    """
    Enhance mandatory CMS fields using OpenAI.
    
    This endpoint enhances SEO title, meta description, slug, and featured image alt text
    for Webflow CMS items after image generation. It uses OpenAI directly for fast,
    focused field enhancement.
    
    **Use Case:** After generating images for a blog post, enhance the mandatory
    fields (SEO title, meta description, slug, featured image alt text) to optimize
    for search engines.
    
    **Requirements:** OpenAI API key must be configured in Google Cloud Run secrets.
    """
    
    # Check if OpenAI is available
    openai_provider = get_openai_provider()
    if not openai_provider:
        raise HTTPException(
            status_code=503,
            detail="OpenAI API key is not configured. Please configure OPENAI_API_KEY in Google Cloud Run secrets."
        )
    
    # Validate that at least one field is requested for enhancement
    if not any([
        request.enhance_seo_title,
        request.enhance_meta_description,
        request.enhance_slug,
        request.enhance_image_alt
    ]):
        raise HTTPException(
            status_code=400,
            detail="At least one field must be requested for enhancement"
        )
    
    # Validate image alt enhancement requires featured image URL
    if request.enhance_image_alt and not request.featured_image_url:
        raise HTTPException(
            status_code=400,
            detail="Featured image URL is required when enhancing image alt text"
        )
    
    try:
        # Build enhancement prompt
        prompt = _build_enhancement_prompt(
            title=request.title,
            content=request.content,
            keywords=request.keywords or [],
            target_audience=request.target_audience,
            enhance_seo_title=request.enhance_seo_title,
            enhance_meta_description=request.enhance_meta_description,
            enhance_slug=request.enhance_slug,
            enhance_image_alt=request.enhance_image_alt,
            featured_image_url=request.featured_image_url
        )
        
        # Initialize provider if needed
        if not openai_provider._client:
            await openai_provider.initialize()
        
        # Generate enhanced fields using OpenAI
        ai_request = AIRequest(
            prompt=prompt,
            content_type=ContentType.META_DESCRIPTION,
            config=AIGenerationConfig(
                max_tokens=500,
                temperature=0.7,
                top_p=0.9
            )
        )
        
        ai_response = await openai_provider.generate_content(
            ai_request,
            model=os.getenv("OPENAI_DEFAULT_MODEL", "gpt-4o-mini")
        )
        
        # Parse enhanced fields from response
        enhanced_dict = _parse_enhanced_fields(
            ai_response.content,
            request.enhance_seo_title,
            request.enhance_meta_description,
            request.enhance_slug,
            request.enhance_image_alt
        )
        
        # Fallback for slug if not generated
        if request.enhance_slug and not enhanced_dict["slug"]:
            enhanced_dict["slug"] = _generate_slug_fallback(request.title)
        
        # Build response
        enhanced_fields = EnhancedFields(**enhanced_dict)
        
        original_fields = {
            "title": request.title,
            "content": request.content[:200] + "..." if request.content and len(request.content) > 200 else request.content,
            "featured_image_url": request.featured_image_url
        }
        
        return FieldEnhancementResponse(
            enhanced_fields=enhanced_fields,
            original_fields=original_fields,
            enhanced_at=datetime.now().isoformat(),
            provider="openai",
            model=ai_response.model
        )
        
    except Exception as e:
        logger.error(f"Field enhancement failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to enhance fields: {str(e)}"
        )

