"""
Tests for AI Content Generator module.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.blog_writer_sdk.ai.ai_content_generator import (
    AIContentGenerator,
    ContentTemplate
)
from src.blog_writer_sdk.ai.base_provider import AIRequest, AIResponse, ContentType
from src.blog_writer_sdk.models.blog_models import ContentTone, ContentLength


class TestAIContentGenerator:
    """Test cases for AIContentGenerator class."""
    
    @pytest.fixture
    def mock_provider_manager(self):
        """Create a mock provider manager."""
        manager = Mock()
        manager.get_available_providers.return_value = ["openai", "anthropic"]
        manager.get_provider.return_value = Mock()
        return manager
    
    @pytest.fixture
    def content_generator(self, mock_provider_manager):
        """Create AIContentGenerator instance with mocked dependencies."""
        with patch('src.blog_writer_sdk.ai.ai_content_generator.AIProviderManager') as mock_manager_class:
            mock_manager_class.return_value = mock_provider_manager
            return AIContentGenerator()
    
    def test_initialization(self, content_generator):
        """Test AIContentGenerator initialization."""
        assert content_generator is not None
        assert hasattr(content_generator, 'provider_manager')
    
    def test_content_template_enum(self):
        """Test ContentTemplate enum values."""
        assert ContentTemplate.HOW_TO_GUIDE == "how_to_guide"
        assert ContentTemplate.LISTICLE == "listicle"
        assert ContentTemplate.REVIEW == "review"
        assert ContentTemplate.COMPARISON == "comparison"
        assert ContentTemplate.NEWS_ARTICLE == "news_article"
        assert ContentTemplate.TUTORIAL == "tutorial"
        assert ContentTemplate.CASE_STUDY == "case_study"
        assert ContentTemplate.OPINION_PIECE == "opinion_piece"
        assert ContentTemplate.INTERVIEW == "interview"
        assert ContentTemplate.ROUNDUP == "roundup"
    
    @pytest.mark.asyncio
    async def test_generate_content_success(self, content_generator):
        """Test successful content generation."""
        # Mock the provider manager and its methods
        mock_provider = AsyncMock()
        mock_response = AIResponse(
            content="Generated blog content",
            metadata={"provider": "openai", "tokens_used": 150},
            success=True
        )
        mock_provider.generate_content.return_value = mock_response
        content_generator.provider_manager.get_provider.return_value = mock_provider
        
        # Test content generation
        request = AIRequest(
            prompt="Write a blog about Python",
            content_type=ContentType.BLOG_POST,
            max_tokens=500
        )
        
        result = await content_generator.generate_content(request)
        
        assert result is not None
        assert result.success is True
        assert "Generated blog content" in result.content
    
    @pytest.mark.asyncio
    async def test_generate_content_with_fallback(self, content_generator):
        """Test content generation with provider fallback."""
        # Mock first provider to fail
        mock_provider1 = AsyncMock()
        mock_provider1.generate_content.side_effect = Exception("Provider 1 failed")
        
        # Mock second provider to succeed
        mock_provider2 = AsyncMock()
        mock_response = AIResponse(
            content="Generated content from fallback provider",
            metadata={"provider": "anthropic", "tokens_used": 200},
            success=True
        )
        mock_provider2.generate_content.return_value = mock_response
        
        # Configure provider manager to return different providers
        content_generator.provider_manager.get_provider.side_effect = [
            mock_provider1, mock_provider2
        ]
        
        request = AIRequest(
            prompt="Write a blog about AI",
            content_type=ContentType.BLOG_POST,
            max_tokens=500
        )
        
        result = await content_generator.generate_content(request)
        
        assert result is not None
        assert result.success is True
        assert "Generated content from fallback provider" in result.content
    
    @pytest.mark.asyncio
    async def test_generate_content_all_providers_fail(self, content_generator):
        """Test content generation when all providers fail."""
        # Mock all providers to fail
        mock_provider = AsyncMock()
        mock_provider.generate_content.side_effect = Exception("All providers failed")
        content_generator.provider_manager.get_provider.return_value = mock_provider
        
        request = AIRequest(
            prompt="Write a blog about testing",
            content_type=ContentType.BLOG_POST,
            max_tokens=500
        )
        
        result = await content_generator.generate_content(request)
        
        assert result is not None
        assert result.success is False
        assert "error" in result.content.lower() or "failed" in result.content.lower()
    
    def test_get_available_templates(self, content_generator):
        """Test getting available content templates."""
        templates = content_generator.get_available_templates()
        
        assert isinstance(templates, list)
        assert len(templates) > 0
        assert "how_to_guide" in templates
        assert "listicle" in templates
    
    def test_get_provider_status(self, content_generator):
        """Test getting provider status."""
        # Mock provider manager status
        content_generator.provider_manager.get_provider_status.return_value = {
            "openai": {"status": "active", "cost": 0.02},
            "anthropic": {"status": "active", "cost": 0.03}
        }
        
        status = content_generator.get_provider_status()
        
        assert isinstance(status, dict)
        assert "openai" in status
        assert "anthropic" in status
        assert status["openai"]["status"] == "active"
    
    @pytest.mark.asyncio
    async def test_optimize_content(self, content_generator):
        """Test content optimization."""
        # Mock optimization process
        mock_provider = AsyncMock()
        mock_response = AIResponse(
            content="Optimized content with better SEO and readability",
            metadata={"optimization_score": 0.95},
            success=True
        )
        mock_provider.optimize_content.return_value = mock_response
        content_generator.provider_manager.get_provider.return_value = mock_provider
        
        original_content = "Original blog content that needs optimization"
        result = await content_generator.optimize_content(original_content)
        
        assert result is not None
        assert result.success is True
        assert "Optimized content" in result.content
    
    def test_validate_content_quality(self, content_generator):
        """Test content quality validation."""
        # Test high-quality content
        good_content = "This is a well-written blog post with proper structure, clear headings, and engaging content that provides value to readers."
        quality_score = content_generator.validate_content_quality(good_content)
        
        assert isinstance(quality_score, float)
        assert 0.0 <= quality_score <= 1.0
        assert quality_score > 0.5  # Should be considered good quality
        
        # Test low-quality content
        poor_content = "bad content"
        poor_quality_score = content_generator.validate_content_quality(poor_content)
        
        assert poor_quality_score < quality_score
    
    def test_get_generation_stats(self, content_generator):
        """Test getting generation statistics."""
        # Mock some generation history
        content_generator._generation_history = [
            {"provider": "openai", "tokens": 150, "success": True},
            {"provider": "anthropic", "tokens": 200, "success": True},
            {"provider": "openai", "tokens": 100, "success": False}
        ]
        
        stats = content_generator.get_generation_stats()
        
        assert isinstance(stats, dict)
        assert "total_generations" in stats
        assert "success_rate" in stats
        assert "total_tokens" in stats
        assert stats["total_generations"] == 3
        assert stats["success_rate"] == 2/3
        assert stats["total_tokens"] == 450
