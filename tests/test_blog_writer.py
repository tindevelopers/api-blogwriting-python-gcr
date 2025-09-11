"""
Tests for the main BlogWriter class.
"""

import pytest
from src.blog_writer_sdk import BlogWriter
from src.blog_writer_sdk.models.blog_models import (
    BlogRequest,
    ContentTone,
    ContentLength,
    ContentFormat,
)


class TestBlogWriter:
    """Test cases for BlogWriter class."""
    
    @pytest.fixture
    def blog_writer(self):
        """Create a BlogWriter instance for testing."""
        return BlogWriter(
            enable_seo_optimization=True,
            enable_quality_analysis=True,
        )
    
    @pytest.fixture
    def sample_request(self):
        """Create a sample blog request for testing."""
        return BlogRequest(
            topic="The Future of AI in Content Creation",
            keywords=["AI content", "automation", "writing tools"],
            tone=ContentTone.PROFESSIONAL,
            length=ContentLength.MEDIUM,
            focus_keyword="AI content creation",
        )
    
    @pytest.mark.asyncio
    async def test_blog_generation_success(self, blog_writer, sample_request):
        """Test successful blog generation."""
        result = await blog_writer.generate(sample_request)
        
        assert result.success is True
        assert result.blog_post is not None
        assert result.blog_post.title
        assert result.blog_post.content
        assert result.word_count > 0
        assert result.generation_time_seconds > 0
    
    @pytest.mark.asyncio
    async def test_blog_generation_with_different_tones(self, blog_writer):
        """Test blog generation with different tones."""
        tones = [ContentTone.PROFESSIONAL, ContentTone.CASUAL, ContentTone.FRIENDLY]
        
        for tone in tones:
            request = BlogRequest(
                topic="Test Topic",
                tone=tone,
                length=ContentLength.SHORT,
            )
            
            result = await blog_writer.generate(request)
            assert result.success is True
            assert result.blog_post is not None
    
    @pytest.mark.asyncio
    async def test_blog_generation_with_different_lengths(self, blog_writer):
        """Test blog generation with different content lengths."""
        lengths = [ContentLength.SHORT, ContentLength.MEDIUM, ContentLength.LONG]
        
        for length in lengths:
            request = BlogRequest(
                topic="Test Topic",
                length=length,
            )
            
            result = await blog_writer.generate(request)
            assert result.success is True
            assert result.blog_post is not None
    
    @pytest.mark.asyncio
    async def test_content_analysis(self, blog_writer):
        """Test content analysis functionality."""
        sample_content = """
        # Test Article
        
        This is a test article with some content to analyze.
        It has multiple paragraphs and should provide good
        metrics for analysis.
        
        ## Section 1
        
        This section contains more detailed information about
        the topic we're discussing.
        """
        
        result = await blog_writer.analyze_existing_content(
            content=sample_content,
            title="Test Article"
        )
        
        assert result.success is True
        assert result.blog_post is not None
        assert result.seo_score >= 0
        assert result.readability_score >= 0
    
    def test_blog_writer_initialization(self):
        """Test BlogWriter initialization with different parameters."""
        writer = BlogWriter(
            default_tone=ContentTone.CASUAL,
            default_length=ContentLength.LONG,
            enable_seo_optimization=False,
            enable_quality_analysis=False,
        )
        
        assert writer.default_tone == ContentTone.CASUAL
        assert writer.default_length == ContentLength.LONG
        assert writer.enable_seo_optimization is False
        assert writer.enable_quality_analysis is False
    
    def test_set_defaults(self, blog_writer):
        """Test setting default values."""
        blog_writer.set_defaults(
            tone=ContentTone.FRIENDLY,
            length=ContentLength.EXTENDED,
        )
        
        assert blog_writer.default_tone == ContentTone.FRIENDLY
        assert blog_writer.default_length == ContentLength.EXTENDED
