"""API endpoint tests."""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_endpoint():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "version" in data


def test_config_endpoint():
    """Test the configuration endpoint."""
    response = client.get("/api/v1/config")
    assert response.status_code == 200
    
    data = response.json()
    assert "seo_optimization_enabled" in data
    assert "quality_analysis_enabled" in data
    assert "supported_tones" in data
    assert "supported_lengths" in data


def test_docs_endpoint():
    """Test that API documentation is accessible."""
    response = client.get("/docs")
    assert response.status_code == 200


def test_openapi_endpoint():
    """Test that OpenAPI schema is accessible."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    
    data = response.json()
    assert "openapi" in data
    assert "info" in data
    assert data["info"]["title"] == "Blog Writer SDK API"


def test_blog_generation_endpoint():
    """Test blog generation endpoint with valid data."""
    request_data = {
        "topic": "How to Build REST APIs with Python",
        "keywords": ["Python", "FastAPI", "REST", "API"],
        "tone": "professional",
        "length": "medium",
        "target_audience": "developers",
        "word_count_target": 1000
    }
    
    response = client.post("/api/v1/blog/generate", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "blog_post" in data
    assert "seo_analysis" in data
    assert "generation_metadata" in data


def test_blog_generation_invalid_data():
    """Test blog generation with invalid data."""
    # Test with missing required field
    request_data = {
        "keywords": ["Python", "API"],
        "tone": "professional"
        # Missing topic
    }
    
    response = client.post("/api/v1/blog/generate", json=request_data)
    assert response.status_code == 422  # Validation error


def test_keyword_analysis_endpoint():
    """Test keyword analysis endpoint."""
    request_data = {
        "keywords": ["Python", "FastAPI", "REST API"],
        "location": "United States",
        "language": "en"
    }
    
    response = client.post("/api/v1/keywords/analyze", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, dict)


def test_keyword_extraction_endpoint():
    """Test keyword extraction endpoint."""
    request_data = {
        "content": "This is a sample blog post about Python programming and web development. " * 10,
        "max_keywords": 10
    }
    
    response = client.post("/api/v1/keywords/extract", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "extracted_keywords" in data
    assert isinstance(data["extracted_keywords"], list)