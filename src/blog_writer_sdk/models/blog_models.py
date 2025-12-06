"""
Data models for the Blog Writer SDK.

This module contains all the Pydantic models used throughout the SDK for
type safety, validation, and serialization.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field, HttpUrl, field_validator


class ContentTone(str, Enum):
    """Available content tones for blog generation."""
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    FRIENDLY = "friendly"
    AUTHORITATIVE = "authoritative"
    CONVERSATIONAL = "conversational"
    TECHNICAL = "technical"
    CREATIVE = "creative"


class ContentLength(str, Enum):
    """Available content lengths for blog generation."""
    SHORT = "short"      # 300-600 words
    MEDIUM = "medium"    # 600-1200 words
    LONG = "long"        # 1200-2500 words
    EXTENDED = "extended"  # 2500+ words


class ContentFormat(str, Enum):
    """Available output formats."""
    MARKDOWN = "markdown"
    HTML = "html"
    PLAIN_TEXT = "plain_text"
    JSON = "json"


class SEODifficulty(str, Enum):
    """SEO keyword difficulty levels."""
    VERY_EASY = "very_easy"    # 0-20
    EASY = "easy"              # 21-40
    MEDIUM = "medium"          # 41-60
    HARD = "hard"              # 61-80
    VERY_HARD = "very_hard"    # 81-100


class BlogRequest(BaseModel):
    """Request model for blog generation."""
    
    topic: str = Field(..., min_length=3, max_length=200, description="Main topic for the blog post")
    keywords: List[str] = Field(default_factory=list, description="Target SEO keywords")
    tone: ContentTone = Field(default=ContentTone.PROFESSIONAL, description="Writing tone")
    length: ContentLength = Field(default=ContentLength.MEDIUM, description="Target content length")
    format: ContentFormat = Field(default=ContentFormat.MARKDOWN, description="Output format")
    
    # SEO Configuration
    target_audience: Optional[str] = Field(None, description="Target audience description")
    competitor_urls: List[HttpUrl] = Field(default_factory=list, description="Competitor URLs for analysis")
    focus_keyword: Optional[str] = Field(None, description="Primary focus keyword")
    
    # Content Structure
    include_introduction: bool = Field(default=True, description="Include introduction section")
    include_conclusion: bool = Field(default=True, description="Include conclusion section")
    include_faq: bool = Field(default=False, description="Include FAQ section")
    include_toc: bool = Field(default=True, description="Include table of contents")
    
    # Advanced Options
    readability_target: Optional[str] = Field(default="general", description="Target readability level")
    word_count_target: Optional[int] = Field(None, ge=100, le=10000, description="Specific word count target")
    custom_instructions: Optional[str] = Field(None, max_length=5000, description="Additional instructions")

    @field_validator('keywords')
    @classmethod
    def validate_keywords(cls, v):
        """Validate keywords list."""
        if len(v) > 20:
            raise ValueError("Maximum 20 keywords allowed")
        return [keyword.strip().lower() for keyword in v if keyword.strip()]

    @field_validator('focus_keyword')
    @classmethod
    def validate_focus_keyword(cls, v):
        """Validate focus keyword."""
        if v:
            return v.strip().lower()
        return v


class SEOMetrics(BaseModel):
    """SEO analysis metrics for content."""
    
    # Keyword Metrics
    keyword_density: Dict[str, float] = Field(default_factory=dict, description="Keyword density percentages")
    keyword_frequency: Dict[str, int] = Field(default_factory=dict, description="Keyword frequency counts")
    focus_keyword_score: float = Field(default=0.0, ge=0, le=100, description="Focus keyword optimization score")
    
    # Content Structure
    title_seo_score: float = Field(default=0.0, ge=0, le=100, description="Title SEO optimization score")
    meta_description_score: float = Field(default=0.0, ge=0, le=100, description="Meta description score")
    heading_structure_score: float = Field(default=0.0, ge=0, le=100, description="Heading structure score")
    
    # Technical SEO
    word_count: int = Field(default=0, ge=0, description="Total word count")
    reading_time_minutes: float = Field(default=0.0, ge=0, description="Estimated reading time")
    internal_links_count: int = Field(default=0, ge=0, description="Number of internal links")
    external_links_count: int = Field(default=0, ge=0, description="Number of external links")
    
    # Overall Scores
    overall_seo_score: float = Field(default=0.0, ge=0, le=100, description="Overall SEO score")
    content_quality_score: float = Field(default=0.0, ge=0, le=100, description="Content quality score")
    
    # Recommendations
    recommendations: List[str] = Field(default_factory=list, description="SEO improvement recommendations")
    warnings: List[str] = Field(default_factory=list, description="SEO warnings")


class ContentQuality(BaseModel):
    """Content quality analysis metrics."""
    
    # Readability Metrics
    flesch_kincaid_grade: float = Field(default=0.0, description="Flesch-Kincaid grade level")
    flesch_reading_ease: float = Field(default=0.0, description="Flesch reading ease score")
    gunning_fog_index: float = Field(default=0.0, description="Gunning Fog readability index")
    
    # Content Structure
    sentence_count: int = Field(default=0, ge=0, description="Total sentence count")
    paragraph_count: int = Field(default=0, ge=0, description="Total paragraph count")
    avg_sentence_length: float = Field(default=0.0, ge=0, description="Average sentence length")
    avg_paragraph_length: float = Field(default=0.0, ge=0, description="Average paragraph length")
    
    # Vocabulary Analysis
    unique_words: int = Field(default=0, ge=0, description="Number of unique words")
    vocabulary_diversity: float = Field(default=0.0, ge=0, le=1, description="Vocabulary diversity ratio")
    complex_words_ratio: float = Field(default=0.0, ge=0, le=1, description="Ratio of complex words")
    
    # Content Scoring
    readability_score: float = Field(default=0.0, ge=0, le=100, description="Overall readability score")
    engagement_score: float = Field(default=0.0, ge=0, le=100, description="Content engagement score")
    
    # Suggestions
    readability_suggestions: List[str] = Field(default_factory=list, description="Readability improvements")
    structure_suggestions: List[str] = Field(default_factory=list, description="Structure improvements")


class MetaTags(BaseModel):
    """Meta tags for SEO optimization."""
    
    title: str = Field(..., min_length=10, max_length=60, description="SEO title tag")
    description: str = Field(..., min_length=50, max_length=160, description="Meta description")
    keywords: List[str] = Field(default_factory=list, description="Meta keywords")
    canonical_url: Optional[HttpUrl] = Field(None, description="Canonical URL")
    
    # Open Graph
    og_title: Optional[str] = Field(None, description="Open Graph title")
    og_description: Optional[str] = Field(None, description="Open Graph description")
    og_image: Optional[HttpUrl] = Field(None, description="Open Graph image URL")
    og_type: str = Field(default="article", description="Open Graph type")
    
    # Twitter Card
    twitter_card: str = Field(default="summary_large_image", description="Twitter card type")
    twitter_title: Optional[str] = Field(None, description="Twitter title")
    twitter_description: Optional[str] = Field(None, description="Twitter description")
    twitter_image: Optional[HttpUrl] = Field(None, description="Twitter image URL")


class BlogPost(BaseModel):
    """Complete blog post model."""
    
    # Content
    title: str = Field(..., min_length=10, max_length=100, description="Blog post title")
    content: str = Field(..., min_length=100, description="Main blog content")
    excerpt: Optional[str] = Field(None, max_length=300, description="Blog post excerpt")
    
    # Metadata
    meta_tags: MetaTags = Field(..., description="SEO meta tags")
    slug: str = Field(..., description="URL slug")
    author: Optional[str] = Field(None, description="Author name")
    
    # Categories and Tags
    categories: List[str] = Field(default_factory=list, description="Content categories")
    tags: List[str] = Field(default_factory=list, description="Content tags")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    published_at: Optional[datetime] = Field(None, description="Publication timestamp")
    
    # SEO and Quality
    seo_metrics: Optional[SEOMetrics] = Field(None, description="SEO analysis results")
    content_quality: Optional[ContentQuality] = Field(None, description="Content quality analysis")
    
    # Status
    status: str = Field(default="draft", description="Publication status")
    featured_image: Optional[HttpUrl] = Field(None, description="Featured image URL")


class BlogGenerationResult(BaseModel):
    """Result of blog generation process."""
    
    success: bool = Field(..., description="Whether generation was successful")
    blog_post: Optional[BlogPost] = Field(None, description="Generated blog post")
    
    # Generation Metadata
    generation_time_seconds: float = Field(default=0.0, ge=0, description="Time taken to generate")
    word_count: int = Field(default=0, ge=0, description="Generated content word count")
    
    # Quality Metrics
    seo_score: float = Field(default=0.0, ge=0, le=100, description="Overall SEO score")
    readability_score: float = Field(default=0.0, ge=0, le=100, description="Readability score")
    
    # Feedback
    warnings: List[str] = Field(default_factory=list, description="Generation warnings")
    suggestions: List[str] = Field(default_factory=list, description="Improvement suggestions")
    
    # Error Handling
    error_message: Optional[str] = Field(None, description="Error message if generation failed")
    error_code: Optional[str] = Field(None, description="Error code for debugging")

    @field_validator('blog_post')
    @classmethod
    def validate_blog_post_with_success(cls, v, info):
        """Ensure blog_post is present when success is True."""
        if info.data.get('success') and not v:
            raise ValueError("blog_post is required when success is True")
        return v


class KeywordAnalysis(BaseModel):
    """Keyword analysis result."""
    
    keyword: str = Field(..., description="Analyzed keyword")
    search_volume: Optional[int] = Field(None, ge=0, description="Monthly search volume")
    global_search_volume: Optional[int] = Field(
        None, ge=0, description="Global monthly search volume"
    )
    search_volume_by_country: Dict[str, int] = Field(
        default_factory=dict,
        description="Search volume split by country code",
    )
    monthly_searches: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Historical monthly search volume breakdown",
    )
    difficulty: SEODifficulty = Field(..., description="SEO difficulty level")
    competition: float = Field(default=0.0, ge=0, le=1, description="Competition score")
    
    # Related Keywords
    related_keywords: List[str] = Field(default_factory=list, description="Related keywords")
    long_tail_keywords: List[str] = Field(default_factory=list, description="Long-tail variations")
    
    # Metrics
    cpc: Optional[float] = Field(None, ge=0, description="Cost per click")
    cpc_currency: Optional[str] = Field(None, description="Currency for CPC values")
    cps: Optional[float] = Field(None, ge=0, description="Cost per sale / CPS metric")
    clicks: Optional[float] = Field(None, ge=0, description="Estimated clicks per month")
    trend_score: float = Field(default=0.0, ge=-1, le=1, description="Trend score (-1 to 1)")
    traffic_potential: Optional[int] = Field(
        None, ge=0, description="Estimated traffic potential if ranking in top positions"
    )
    parent_topic: Optional[str] = Field(
        None, description="Parent topic cluster for this keyword"
    )
    serp_features: List[str] = Field(
        default_factory=list, description="SERP features observed for this keyword"
    )
    serp_feature_counts: Dict[str, Any] = Field(
        default_factory=dict, description="SERP feature counts/summary data"
    )
    primary_intent: Optional[str] = Field(
        None, description="Primary search intent inferred from SERP"
    )
    intent_probabilities: Dict[str, float] = Field(
        default_factory=dict, description="Intent probability distribution"
    )
    also_rank_for: List[str] = Field(
        default_factory=list,
        description="Other keywords domains ranking for this keyword also rank for",
    )
    also_talk_about: List[str] = Field(
        default_factory=list,
        description="Semantically related entities/topics mentioned on SERP",
    )
    top_competitors: List[str] = Field(
        default_factory=list, description="Top competitor domains on the SERP"
    )
    first_seen: Optional[str] = Field(
        None, description="Date the keyword was first observed by DataForSEO"
    )
    last_updated: Optional[str] = Field(
        None, description="Date the keyword metrics were last updated"
    )
    
    # Recommendations
    recommended: bool = Field(default=True, description="Whether keyword is recommended")
    reason: Optional[str] = Field(None, description="Recommendation reason")


class CompetitorAnalysis(BaseModel):
    """Competitor content analysis."""
    
    url: HttpUrl = Field(..., description="Competitor URL")
    title: str = Field(..., description="Competitor page title")
    word_count: int = Field(default=0, ge=0, description="Content word count")
    
    # SEO Metrics
    title_length: int = Field(default=0, ge=0, description="Title length")
    meta_description_length: int = Field(default=0, ge=0, description="Meta description length")
    heading_count: Dict[str, int] = Field(default_factory=dict, description="Heading tag counts")
    
    # Content Analysis
    keywords_found: List[str] = Field(default_factory=list, description="Keywords found in content")
    readability_score: float = Field(default=0.0, ge=0, le=100, description="Content readability")
    
    # Strengths and Weaknesses
    strengths: List[str] = Field(default_factory=list, description="Content strengths")
    weaknesses: List[str] = Field(default_factory=list, description="Content weaknesses")
    opportunities: List[str] = Field(default_factory=list, description="Content opportunities")
