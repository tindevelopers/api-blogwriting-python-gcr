"""Basic tests for the BlogWriter SDK."""

import pytest
from src.blog_writer_sdk.models.blog_models import BlogRequest, ContentTone, ContentLength


def test_blog_request_creation():
    """Test that BlogRequest can be created with valid data."""
    request = BlogRequest(
        topic="How to Build APIs",
        keywords=["Python", "FastAPI", "REST"],
        tone=ContentTone.PROFESSIONAL,
        length=ContentLength.MEDIUM
    )
    
    assert request.topic == "How to Build APIs"
    assert request.keywords == ["Python", "FastAPI", "REST"]
    assert request.tone == ContentTone.PROFESSIONAL
    assert request.length == ContentLength.MEDIUM


def test_content_tone_enum():
    """Test ContentTone enum values."""
    assert ContentTone.PROFESSIONAL.value == "professional"
    assert ContentTone.CASUAL.value == "casual"
    assert ContentTone.TECHNICAL.value == "technical"


def test_content_length_enum():
    """Test ContentLength enum values."""
    assert ContentLength.SHORT.value == "short"
    assert ContentLength.MEDIUM.value == "medium"
    assert ContentLength.LONG.value == "long"


def test_blog_request_validation():
    """Test BlogRequest validation."""
    # Test minimum topic length
    with pytest.raises(ValueError):
        BlogRequest(topic="Hi")  # Too short
    
    # Test maximum keywords
    with pytest.raises(ValueError):
        BlogRequest(
            topic="Valid topic that is long enough",
            keywords=["keyword"] * 21  # Too many keywords (max 20)
        )


def test_imports():
    """Test that main modules can be imported without errors."""
    from src.blog_writer_sdk import BlogWriter
    from src.blog_writer_sdk.core.content_generator import ContentGenerator
    from src.blog_writer_sdk.seo.keyword_analyzer import KeywordAnalyzer
    
    # Test that classes can be instantiated
    writer = BlogWriter()
    generator = ContentGenerator()
    analyzer = KeywordAnalyzer()
    
    assert writer is not None
    assert generator is not None
    assert analyzer is not None
