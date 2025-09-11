"""
Tests for the SEO optimizer module.
"""

import pytest
from src.blog_writer_sdk.core.seo_optimizer import SEOOptimizer
from src.blog_writer_sdk.models.blog_models import MetaTags


class TestSEOOptimizer:
    """Test cases for SEOOptimizer class."""
    
    @pytest.fixture
    def seo_optimizer(self):
        """Create an SEOOptimizer instance for testing."""
        return SEOOptimizer()
    
    @pytest.fixture
    def sample_content(self):
        """Sample content for testing."""
        return """
        # AI Content Creation: The Future is Here
        
        Artificial intelligence is revolutionizing content creation.
        AI content tools are becoming more sophisticated every day.
        
        ## Benefits of AI Content
        
        AI content creation offers many advantages:
        - Speed and efficiency
        - Consistency in tone
        - SEO optimization
        
        ## Getting Started with AI Content
        
        To begin using AI content tools, consider your goals
        and choose the right platform for your needs.
        """
    
    @pytest.fixture
    def sample_meta_tags(self):
        """Sample meta tags for testing."""
        return MetaTags(
            title="AI Content Creation Guide",
            description="Learn how AI is transforming content creation",
            keywords=["AI content", "content creation", "automation"],
        )
    
    @pytest.mark.asyncio
    async def test_seo_analysis(self, seo_optimizer, sample_content, sample_meta_tags):
        """Test comprehensive SEO analysis."""
        result = await seo_optimizer.analyze_seo(
            content=sample_content,
            title="AI Content Creation Guide",
            meta_tags=sample_meta_tags,
            keywords=["AI content", "content creation"],
            focus_keyword="AI content",
        )
        
        assert result.word_count > 0
        assert result.overall_seo_score >= 0
        assert result.overall_seo_score <= 100
        assert result.title_seo_score >= 0
        assert result.meta_description_score >= 0
        assert result.heading_structure_score >= 0
        assert isinstance(result.recommendations, list)
        assert isinstance(result.warnings, list)
    
    @pytest.mark.asyncio
    async def test_keyword_optimization(self, seo_optimizer, sample_content):
        """Test keyword distribution optimization."""
        keywords = ["AI content", "content creation", "automation"]
        focus_keyword = "AI content"
        
        optimized_content = await seo_optimizer.optimize_keyword_distribution(
            content=sample_content,
            keywords=keywords,
            focus_keyword=focus_keyword,
        )
        
        assert isinstance(optimized_content, str)
        assert len(optimized_content) > 0
    
    @pytest.mark.asyncio
    async def test_heading_structure_optimization(self, seo_optimizer, sample_content):
        """Test heading structure optimization."""
        optimized_content = await seo_optimizer.optimize_heading_structure(
            sample_content
        )
        
        assert isinstance(optimized_content, str)
        assert "# AI Content Creation" in optimized_content
    
    @pytest.mark.asyncio
    async def test_internal_linking_suggestions(self, seo_optimizer, sample_content):
        """Test internal linking suggestions."""
        enhanced_content = await seo_optimizer.add_internal_linking_suggestions(
            sample_content
        )
        
        assert isinstance(enhanced_content, str)
        # Should contain the original content
        assert "AI Content Creation" in enhanced_content
    
    def test_title_analysis(self, seo_optimizer):
        """Test title SEO analysis."""
        # Good title
        good_title = "Complete Guide to AI Content Creation"
        good_score = seo_optimizer._analyze_title(good_title, "AI content")
        assert good_score > 50
        
        # Too short title
        short_title = "AI"
        short_score = seo_optimizer._analyze_title(short_title, "AI")
        assert short_score < good_score
        
        # Too long title
        long_title = "This is an extremely long title that exceeds the recommended character limit for SEO optimization"
        long_score = seo_optimizer._analyze_title(long_title, "AI")
        assert long_score < good_score
    
    def test_meta_description_analysis(self, seo_optimizer):
        """Test meta description analysis."""
        # Good description
        good_desc = "Learn how AI is revolutionizing content creation with practical tips and strategies for modern content creators."
        good_score = seo_optimizer._analyze_meta_description(good_desc, "AI content")
        assert good_score > 50
        
        # Too short description
        short_desc = "AI content guide"
        short_score = seo_optimizer._analyze_meta_description(short_desc, "AI content")
        assert short_score < good_score
    
    def test_keyword_density_calculation(self, seo_optimizer, sample_content):
        """Test keyword density calculation."""
        keywords = ["AI content", "content creation"]
        metrics = seo_optimizer._analyze_keywords(sample_content, keywords, "AI content")
        
        assert "density" in metrics
        assert "frequency" in metrics
        assert "focus_score" in metrics
        assert isinstance(metrics["density"], dict)
        assert isinstance(metrics["frequency"], dict)
