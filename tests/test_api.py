"""
Tests for the FastAPI application.
"""

import pytest
from fastapi.testclient import TestClient
from main import app


class TestAPI:
    """Test cases for the FastAPI application."""
    
    @pytest.fixture
    def client(self):
        """Create a test client for the FastAPI app."""
        return TestClient(app)
    
    def test_health_check(self, client):
        """Test the health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
    
    def test_root_endpoint(self, client):
        """Test the root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "endpoints" in data
    
    def test_config_endpoint(self, client):
        """Test the configuration endpoint."""
        response = client.get("/api/v1/config")
        assert response.status_code == 200
        
        data = response.json()
        assert "seo_optimization_enabled" in data
        assert "quality_analysis_enabled" in data
        assert "supported_tones" in data
        assert "supported_lengths" in data
    
    def test_blog_generation_endpoint(self, client):
        """Test the blog generation endpoint."""
        request_data = {
            "topic": "Test Blog Topic",
            "keywords": ["test", "blog", "content"],
            "tone": "professional",
            "length": "medium",
            "focus_keyword": "test blog"
        }
        
        response = client.post("/api/v1/generate", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "success" in data
        assert "blog_post" in data or "error_message" in data
    
    def test_content_analysis_endpoint(self, client):
        """Test the content analysis endpoint."""
        request_data = {
            "content": "This is a test article with some content to analyze. It should provide good metrics.",
            "title": "Test Article",
            "keywords": ["test", "article"]
        }
        
        response = client.post("/api/v1/analyze", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "success" in data
    
    def test_keyword_analysis_endpoint(self, client):
        """Test the keyword analysis endpoint."""
        request_data = ["test keyword", "content creation", "SEO optimization"]
        
        response = client.post("/api/v1/keywords/analyze", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "keyword_analysis" in data
    
    def test_keyword_extraction_endpoint(self, client):
        """Test the keyword extraction endpoint."""
        request_data = {
            "content": "This is a comprehensive article about artificial intelligence and machine learning. AI technology is revolutionizing many industries.",
            "max_keywords": 10
        }
        
        response = client.post("/api/v1/keywords/extract", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "extracted_keywords" in data
        assert isinstance(data["extracted_keywords"], list)
    
    def test_keyword_suggestions_endpoint(self, client):
        """Test the keyword suggestions endpoint."""
        request_data = {
            "keyword": "content marketing"
        }
        
        response = client.post("/api/v1/keywords/suggest", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "keyword_suggestions" in data
        assert isinstance(data["keyword_suggestions"], list)
    
    def test_content_optimization_endpoint(self, client):
        """Test the content optimization endpoint."""
        request_data = {
            "content": "This is a test article about content marketing. Content marketing is important for businesses.",
            "keywords": ["content marketing", "business"],
            "focus_keyword": "content marketing"
        }
        
        response = client.post("/api/v1/optimize", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "optimized_content" in data
        assert "original_length" in data
        assert "optimized_length" in data
    
    def test_invalid_blog_generation_request(self, client):
        """Test blog generation with invalid request data."""
        request_data = {
            "topic": "",  # Empty topic should fail validation
            "keywords": [],
        }
        
        response = client.post("/api/v1/generate", json=request_data)
        assert response.status_code == 422  # Validation error
    
    def test_invalid_content_analysis_request(self, client):
        """Test content analysis with invalid request data."""
        request_data = {
            "content": "Short",  # Too short content
        }
        
        response = client.post("/api/v1/analyze", json=request_data)
        assert response.status_code == 422  # Validation error
