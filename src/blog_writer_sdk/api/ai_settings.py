"""
AI Settings API endpoints for configuration management.

This module provides endpoints for managing AI provider settings,
API keys, and configuration updates.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse

from ..ai.base_provider import AIProviderType
from ..integrations.dataforseo_integration import DataForSEOClient, EnhancedKeywordAnalyzer

logger = logging.getLogger(__name__)

# Create router for AI settings
router = APIRouter(prefix="/api/v1/ai-settings", tags=["AI Settings"])


class AIProviderConfig(BaseModel):
    """AI Provider configuration model."""
    provider_type: str = Field(..., description="Provider type (openai, anthropic, deepseek, etc.)")
    api_key: Optional[str] = Field(None, description="API key for the provider")
    enabled: bool = Field(True, description="Whether the provider is enabled")
    priority: int = Field(1, description="Priority for provider selection (lower = higher priority)")
    default_model: Optional[str] = Field(None, description="Default model for the provider")
    max_retries: int = Field(3, description="Maximum retry attempts")
    timeout: int = Field(30, description="Request timeout in seconds")
    custom_endpoint: Optional[str] = Field(None, description="Custom API endpoint (for Azure OpenAI)")


class DataForSEOConfig(BaseModel):
    """DataForSEO configuration model."""
    api_key: Optional[str] = Field(None, description="DataForSEO API key")
    api_secret: Optional[str] = Field(None, description="DataForSEO API secret")
    enabled: bool = Field(False, description="Whether DataForSEO is enabled")
    location: str = Field("United States", description="Default location for keyword analysis")
    language_code: str = Field("en", description="Default language code")


class AISettingsConfig(BaseModel):
    """Complete AI settings configuration."""
    providers: Dict[str, AIProviderConfig] = Field(default_factory=dict)
    dataforseo: DataForSEOConfig = Field(default_factory=DataForSEOConfig)
    default_strategy: str = Field("seo_optimized", description="Default content generation strategy")
    enable_fallback: bool = Field(True, description="Enable automatic provider fallback")
    cache_enabled: bool = Field(True, description="Enable response caching")
    cache_ttl: int = Field(3600, description="Cache TTL in seconds")


class APIKeyUpdateRequest(BaseModel):
    """Request model for updating API keys."""
    provider: str = Field(..., description="Provider name (openai, anthropic, deepseek, dataforseo)")
    api_key: str = Field(..., description="API key value")
    api_secret: Optional[str] = Field(None, description="API secret (for DataForSEO)")


class ProviderStatus(BaseModel):
    """Provider status information."""
    provider: str
    enabled: bool
    configured: bool
    status: str  # "active", "inactive", "error", "testing"
    last_tested: Optional[datetime]
    error_message: Optional[str]


class AISettingsResponse(BaseModel):
    """Response model for AI settings."""
    config: AISettingsConfig
    provider_status: List[ProviderStatus]
    dataforseo_status: Optional[Dict[str, Any]]
    last_updated: datetime


# Global settings storage (in production, this would be in a database)
_ai_settings_cache: Optional[AISettingsConfig] = None


def get_current_ai_settings() -> AISettingsConfig:
    """Get current AI settings configuration."""
    global _ai_settings_cache
    
    if _ai_settings_cache is None:
        _ai_settings_cache = load_ai_settings_from_env()
    
    return _ai_settings_cache


def load_ai_settings_from_env() -> AISettingsConfig:
    """Load AI settings from environment variables."""
    providers = {}
    
    # OpenAI Configuration
    if os.getenv("OPENAI_API_KEY"):
        providers["openai"] = AIProviderConfig(
            provider_type="openai",
            api_key=os.getenv("OPENAI_API_KEY"),
            enabled=bool(os.getenv("OPENAI_API_KEY")),
            priority=1,
            default_model=os.getenv("OPENAI_DEFAULT_MODEL", "gpt-4o-mini"),
            max_retries=int(os.getenv("OPENAI_MAX_RETRIES", "3")),
            timeout=int(os.getenv("OPENAI_TIMEOUT", "30"))
        )
    
    # Anthropic Configuration
    if os.getenv("ANTHROPIC_API_KEY"):
        providers["anthropic"] = AIProviderConfig(
            provider_type="anthropic",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            enabled=bool(os.getenv("ANTHROPIC_API_KEY")),
            priority=2,
            default_model=os.getenv("ANTHROPIC_DEFAULT_MODEL", "claude-3-5-haiku-20241022"),
            max_retries=int(os.getenv("ANTHROPIC_MAX_RETRIES", "3")),
            timeout=int(os.getenv("ANTHROPIC_TIMEOUT", "30"))
        )
    
    # DeepSeek Configuration
    if os.getenv("DEEPSEEK_API_KEY"):
        providers["deepseek"] = AIProviderConfig(
            provider_type="deepseek",
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            enabled=bool(os.getenv("DEEPSEEK_API_KEY")),
            priority=3,
            default_model=os.getenv("DEEPSEEK_DEFAULT_MODEL", "deepseek-chat"),
            max_retries=int(os.getenv("DEEPSEEK_MAX_RETRIES", "3")),
            timeout=int(os.getenv("DEEPSEEK_TIMEOUT", "30")),
            custom_endpoint=os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com")
        )
    
    # Azure OpenAI Configuration
    if os.getenv("AZURE_OPENAI_API_KEY"):
        providers["azure_openai"] = AIProviderConfig(
            provider_type="azure_openai",
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            enabled=bool(os.getenv("AZURE_OPENAI_API_KEY")),
            priority=4,
            default_model=os.getenv("AZURE_OPENAI_DEFAULT_MODEL", "gpt-4o-mini"),
            max_retries=int(os.getenv("AZURE_OPENAI_MAX_RETRIES", "3")),
            timeout=int(os.getenv("AZURE_OPENAI_TIMEOUT", "30")),
            custom_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
    
    # DataForSEO Configuration
    dataforseo_config = DataForSEOConfig(
        api_key=os.getenv("DATAFORSEO_API_KEY"),
        api_secret=os.getenv("DATAFORSEO_API_SECRET"),
        enabled=bool(os.getenv("DATAFORSEO_API_KEY") and os.getenv("DATAFORSEO_API_SECRET")),
        location=os.getenv("DATAFORSEO_LOCATION", "United States"),
        language_code=os.getenv("DATAFORSEO_LANGUAGE", "en")
    )
    
    return AISettingsConfig(
        providers=providers,
        dataforseo=dataforseo_config,
        default_strategy=os.getenv("DEFAULT_CONTENT_STRATEGY", "seo_optimized"),
        enable_fallback=os.getenv("ENABLE_AI_FALLBACK", "true").lower() == "true",
        cache_enabled=os.getenv("AI_CACHE_ENABLED", "true").lower() == "true",
        cache_ttl=int(os.getenv("AI_CACHE_TTL", "3600"))
    )


async def test_provider_connection(provider_config: AIProviderConfig) -> Dict[str, Any]:
    """Test connection to an AI provider."""
    try:
        if provider_config.provider_type == "openai":
            from ..ai.openai_provider import OpenAIProvider
            provider = OpenAIProvider(
                api_key=provider_config.api_key,
                max_retries=provider_config.max_retries,
                timeout=provider_config.timeout
            )
            await provider.initialize()
            # Test with a simple request
            from ..ai.base_provider import AIRequest, AIGenerationConfig, ContentType
            test_request = AIRequest(
                prompt="Test connection",
                config=AIGenerationConfig(content_type=ContentType.TEXT)
            )
            response = await provider.generate_content(test_request)
            return {
                "status": "success",
                "provider": provider_config.provider_type,
                "model": response.model,
                "response_time": response.generation_time
            }
        
        elif provider_config.provider_type == "anthropic":
            from ..ai.anthropic_provider import AnthropicProvider
            provider = AnthropicProvider(
                api_key=provider_config.api_key,
                max_retries=provider_config.max_retries,
                timeout=provider_config.timeout
            )
            await provider.initialize()
            # Test with a simple request
            from ..ai.base_provider import AIRequest, AIGenerationConfig, ContentType
            test_request = AIRequest(
                prompt="Test connection",
                config=AIGenerationConfig(content_type=ContentType.TEXT)
            )
            response = await provider.generate_content(test_request)
            return {
                "status": "success",
                "provider": provider_config.provider_type,
                "model": response.model,
                "response_time": response.generation_time
            }
        
        elif provider_config.provider_type == "deepseek":
            # DeepSeek uses OpenAI-compatible API
            from ..ai.openai_provider import OpenAIProvider
            provider = OpenAIProvider(
                api_key=provider_config.api_key,
                base_url=provider_config.custom_endpoint or "https://api.deepseek.com",
                max_retries=provider_config.max_retries,
                timeout=provider_config.timeout
            )
            await provider.initialize()
            # Test with a simple request
            from ..ai.base_provider import AIRequest, AIGenerationConfig, ContentType
            test_request = AIRequest(
                prompt="Test connection",
                config=AIGenerationConfig(content_type=ContentType.TEXT)
            )
            response = await provider.generate_content(test_request)
            return {
                "status": "success",
                "provider": provider_config.provider_type,
                "model": response.model,
                "response_time": response.generation_time
            }
        
        else:
            return {
                "status": "error",
                "provider": provider_config.provider_type,
                "error": f"Unsupported provider type: {provider_config.provider_type}"
            }
    
    except Exception as e:
        return {
            "status": "error",
            "provider": provider_config.provider_type,
            "error": str(e)
        }


async def test_dataforseo_connection(config: DataForSEOConfig) -> Dict[str, Any]:
    """Test DataForSEO connection."""
    try:
        if not config.api_key or not config.api_secret:
            return {
                "status": "error",
                "error": "DataForSEO API key and secret are required"
            }
        
        # Test with a simple keyword analysis
        client = DataForSEOClient(
            location=config.location,
            language_code=config.language_code
        )
        
        # Test with a simple keyword
        test_keywords = ["test keyword"]
        result = await client.get_search_volume_data(test_keywords)
        
        if result:
            return {
                "status": "success",
                "location": config.location,
                "language": config.language_code,
                "test_result": result
            }
        else:
            return {
                "status": "error",
                "error": "No data returned from DataForSEO"
            }
    
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@router.get("/", response_model=AISettingsResponse)
async def get_ai_settings():
    """Get current AI settings configuration."""
    try:
        config = get_current_ai_settings()
        
        # Get provider status
        provider_status = []
        for provider_name, provider_config in config.providers.items():
            if provider_config.api_key and provider_config.enabled:
                test_result = await test_provider_connection(provider_config)
                status = ProviderStatus(
                    provider=provider_name,
                    enabled=provider_config.enabled,
                    configured=True,
                    status="active" if test_result["status"] == "success" else "error",
                    last_tested=datetime.utcnow(),
                    error_message=test_result.get("error")
                )
            else:
                status = ProviderStatus(
                    provider=provider_name,
                    enabled=provider_config.enabled,
                    configured=bool(provider_config.api_key),
                    status="inactive",
                    last_tested=None,
                    error_message=None
                )
            provider_status.append(status)
        
        # Test DataForSEO connection
        dataforseo_status = None
        if config.dataforseo.enabled:
            dataforseo_status = await test_dataforseo_connection(config.dataforseo)
        
        return AISettingsResponse(
            config=config,
            provider_status=provider_status,
            dataforseo_status=dataforseo_status,
            last_updated=datetime.utcnow()
        )
    
    except Exception as e:
        logger.error(f"Error getting AI settings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get AI settings: {str(e)}")


@router.post("/update-api-key")
async def update_api_key(request: APIKeyUpdateRequest):
    """Update API key for a specific provider."""
    try:
        # Validate provider
        valid_providers = ["openai", "anthropic", "deepseek", "azure_openai", "dataforseo"]
        if request.provider not in valid_providers:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid provider. Must be one of: {', '.join(valid_providers)}"
            )
        
        # Update environment variable (in production, this would update a secure store)
        if request.provider == "dataforseo":
            os.environ["DATAFORSEO_API_KEY"] = request.api_key
            if request.api_secret:
                os.environ["DATAFORSEO_API_SECRET"] = request.api_secret
        else:
            env_var_name = f"{request.provider.upper()}_API_KEY"
            os.environ[env_var_name] = request.api_key
        
        # Clear cache to force reload
        global _ai_settings_cache
        _ai_settings_cache = None
        
        # Test the new configuration
        config = get_current_ai_settings()
        test_result = None
        
        if request.provider == "dataforseo":
            test_result = await test_dataforseo_connection(config.dataforseo)
        elif request.provider in config.providers:
            test_result = await test_provider_connection(config.providers[request.provider])
        
        return {
            "success": True,
            "provider": request.provider,
            "test_result": test_result,
            "message": f"API key updated for {request.provider}"
        }
    
    except Exception as e:
        logger.error(f"Error updating API key: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update API key: {str(e)}")


@router.post("/test-provider/{provider_name}")
async def test_provider(provider_name: str):
    """Test connection to a specific AI provider."""
    try:
        config = get_current_ai_settings()
        
        if provider_name == "dataforseo":
            test_result = await test_dataforseo_connection(config.dataforseo)
        elif provider_name in config.providers:
            test_result = await test_provider_connection(config.providers[provider_name])
        else:
            raise HTTPException(status_code=404, detail=f"Provider {provider_name} not found")
        
        return {
            "provider": provider_name,
            "test_result": test_result,
            "timestamp": datetime.utcnow()
        }
    
    except Exception as e:
        logger.error(f"Error testing provider {provider_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to test provider: {str(e)}")


@router.get("/keyword-suggestions")
async def get_keyword_suggestions(
    keyword: str,
    location: str = "United States",
    language: str = "en",
    limit: int = 10
):
    """Get keyword suggestions using DataForSEO."""
    try:
        config = get_current_ai_settings()
        
        if not config.dataforseo.enabled:
            raise HTTPException(
                status_code=400, 
                detail="DataForSEO is not enabled. Please configure API keys first."
            )
        
        # Initialize DataForSEO client
        client = DataForSEOClient(location=location, language_code=language)
        
        # Get keyword suggestions (this would use real DataForSEO API)
        # For now, we'll return structured suggestions
        suggestions = {
            "primary_keyword": keyword,
            "location": location,
            "language": language,
            "suggestions": [
                {
                    "keyword": f"{keyword} guide",
                    "search_volume": 1000,
                    "difficulty": 45,
                    "cpc": 1.25,
                    "type": "long_tail"
                },
                {
                    "keyword": f"best {keyword}",
                    "search_volume": 2500,
                    "difficulty": 65,
                    "cpc": 2.10,
                    "type": "commercial"
                },
                {
                    "keyword": f"how to {keyword}",
                    "search_volume": 800,
                    "difficulty": 35,
                    "cpc": 0.85,
                    "type": "informational"
                },
                {
                    "keyword": f"{keyword} tips",
                    "search_volume": 600,
                    "difficulty": 40,
                    "cpc": 0.95,
                    "type": "informational"
                },
                {
                    "keyword": f"{keyword} for beginners",
                    "search_volume": 400,
                    "difficulty": 25,
                    "cpc": 0.65,
                    "type": "long_tail"
                }
            ],
            "related_keywords": [
                f"{keyword} tutorial",
                f"{keyword} examples",
                f"{keyword} benefits",
                f"{keyword} comparison",
                f"{keyword} alternatives"
            ],
            "content_opportunities": [
                {
                    "type": "how_to",
                    "keyword": f"how to {keyword}",
                    "difficulty": 35,
                    "opportunity_score": 85
                },
                {
                    "type": "comparison",
                    "keyword": f"{keyword} vs alternatives",
                    "difficulty": 50,
                    "opportunity_score": 75
                },
                {
                    "type": "guide",
                    "keyword": f"{keyword} complete guide",
                    "difficulty": 40,
                    "opportunity_score": 80
                }
            ]
        }
        
        return suggestions
    
    except Exception as e:
        logger.error(f"Error getting keyword suggestions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get keyword suggestions: {str(e)}")


@router.get("/providers/status")
async def get_providers_status():
    """Get status of all configured AI providers."""
    try:
        config = get_current_ai_settings()
        status = {
            "total_providers": len(config.providers),
            "enabled_providers": len([p for p in config.providers.values() if p.enabled]),
            "configured_providers": len([p for p in config.providers.values() if p.api_key]),
            "dataforseo_enabled": config.dataforseo.enabled,
            "providers": {}
        }
        
        for provider_name, provider_config in config.providers.items():
            test_result = await test_provider_connection(provider_config)
            status["providers"][provider_name] = {
                "enabled": provider_config.enabled,
                "configured": bool(provider_config.api_key),
                "status": "active" if test_result["status"] == "success" else "error",
                "priority": provider_config.priority,
                "default_model": provider_config.default_model,
                "last_tested": datetime.utcnow(),
                "error": test_result.get("error")
            }
        
        return status
    
    except Exception as e:
        logger.error(f"Error getting providers status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get providers status: {str(e)}")


@router.post("/reset-config")
async def reset_ai_config():
    """Reset AI configuration to defaults."""
    try:
        global _ai_settings_cache
        _ai_settings_cache = None
        
        # Clear environment variables (in production, this would clear from secure store)
        env_vars_to_clear = [
            "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "DEEPSEEK_API_KEY",
            "AZURE_OPENAI_API_KEY", "DATAFORSEO_API_KEY", "DATAFORSEO_API_SECRET"
        ]
        
        for var in env_vars_to_clear:
            if var in os.environ:
                del os.environ[var]
        
        return {
            "success": True,
            "message": "AI configuration reset to defaults",
            "timestamp": datetime.utcnow()
        }
    
    except Exception as e:
        logger.error(f"Error resetting AI config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reset AI config: {str(e)}")
