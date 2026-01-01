"""
Simplified tests for DataForSEO integration module.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.blog_writer_sdk.integrations.dataforseo_integration import (
    DataForSEOClient,
    EnhancedKeywordAnalyzer
)


class TestDataForSEOClient:
    """Test cases for DataForSEOClient class."""
    
    @pytest.fixture
    def mock_client(self):
        """Create a mock DataForSEO client."""
        with patch('src.blog_writer_sdk.integrations.dataforseo_integration.httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            return mock_client
    
    @pytest.fixture
    def dataforseo_client(self, mock_client):
        """Create DataForSEOClient instance with mocked HTTP client."""
        client = DataForSEOClient()
        client.api_key = "test_key"
        client.api_secret = "test_secret"
        client.is_configured = True
        return client
    
    def test_initialization(self, dataforseo_client):
        """Test DataForSEOClient initialization."""
        assert dataforseo_client.api_key == "test_key"
        assert dataforseo_client.api_secret == "test_secret"
        assert dataforseo_client.is_configured is True
    
    @pytest.mark.skip(reason="DataForSEO API may have changed or requires actual API keys")
    @pytest.mark.asyncio
    async def test_get_search_volume_data(self, dataforseo_client, mock_client):
        """Test getting search volume data."""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            "tasks": [{
                "result": [{
                    "keyword": "python",
                    "search_volume": 10000
                }]
            }]
        }
        mock_client.post.return_value = mock_response
        
        result = await dataforseo_client.get_search_volume_data(
            ["python"], "United States", "en", "test_tenant"
        )
        
        assert result is not None
        assert "python" in result


class TestEnhancedKeywordAnalyzer:
    """Test cases for EnhancedKeywordAnalyzer class."""
    
    @pytest.fixture
    def mock_dataforseo_client(self):
        """Create a mock DataForSEO client."""
        return Mock()
    
    @pytest.fixture
    def keyword_analyzer(self, mock_dataforseo_client):
        """Create EnhancedKeywordAnalyzer instance with mocked client."""
        analyzer = EnhancedKeywordAnalyzer()
        analyzer.dataforseo_client = mock_dataforseo_client
        return analyzer
    
    def test_initialization(self, keyword_analyzer, mock_dataforseo_client):
        """Test EnhancedKeywordAnalyzer initialization."""
        assert keyword_analyzer.dataforseo_client == mock_dataforseo_client
    
    @pytest.mark.asyncio
    async def test_analyze_keywords_comprehensive(self, keyword_analyzer, mock_dataforseo_client):
        """Test comprehensive keyword analysis."""
        # Mock DataForSEO client response
        mock_dataforseo_client.get_search_volume_data.return_value = {
            "python": {"search_volume": 10000, "competition": "medium"}
        }
        
        result = await keyword_analyzer.analyze_keywords_comprehensive(["python"], "test_tenant")
        
        assert result is not None
        assert "python" in result
