"""
AI Provider Management API Endpoints

This module provides REST API endpoints for managing AI provider configurations,
including adding, updating, testing, and switching between different AI providers.
"""

import os
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from ..ai.base_provider import (
    AIProviderType, 
    AIProviderManager, 
    AIProviderConfig,
    AIRequest,
    ContentType,
    AIGenerationConfig
)
from ..ai.openai_provider import OpenAIProvider
from ..ai.anthropic_provider import AnthropicProvider
from ..ai.azure_openai_provider import AzureOpenAIProvider
from ..models.ai_provider_models import (
    AIProviderConfigRequest,
    AIProviderConfigResponse,
    AIProviderListResponse,
    AIProviderTestRequest,
    AIProviderTestResponse,
    AIProviderSwitchRequest,
    AIProviderSwitchResponse,
    AIProviderUsageStats,
    AIProviderHealthCheck,
    AIProviderBulkConfigRequest,
    AIProviderBulkConfigResponse,
    AIProviderModelInfo,
    AIProviderCapabilities,
    AIProviderStatus
)

logger = logging.getLogger(__name__)

# Create router for AI provider management endpoints
router = APIRouter(prefix="/api/v1/ai/providers", tags=["AI Provider Management"])

# Global AI provider manager instance
provider_manager = AIProviderManager()

# In-memory storage for provider configurations (in production, use a database)
provider_configs: Dict[str, AIProviderConfigResponse] = {}
usage_stats: Dict[str, AIProviderUsageStats] = {}
health_checks: Dict[str, AIProviderHealthCheck] = {}


def get_provider_class(provider_type: AIProviderType):
    """Get the provider class for a given provider type."""
    provider_classes = {
        AIProviderType.OPENAI: OpenAIProvider,
        AIProviderType.ANTHROPIC: AnthropicProvider,
        AIProviderType.AZURE_OPENAI: AzureOpenAIProvider,
    }
    
    if provider_type not in provider_classes:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported provider type: {provider_type}"
        )
    
    return provider_classes[provider_type]


async def validate_api_key(provider_type: AIProviderType, api_key: str) -> bool:
    """Validate an API key for a given provider."""
    try:
        provider_class = get_provider_class(provider_type)
        provider = provider_class(api_key=api_key)
        return await provider.validate_api_key()
    except Exception as e:
        logger.error(f"API key validation failed for {provider_type}: {e}")
        return False


async def test_provider_generation(provider_type: AIProviderType, api_key: str, test_prompt: str, model: Optional[str] = None) -> AIProviderTestResponse:
    """Test AI provider with a simple generation request."""
    start_time = time.time()
    
    try:
        provider_class = get_provider_class(provider_type)
        provider = provider_class(api_key=api_key)
        
        # Create test request
        test_request = AIRequest(
            prompt=test_prompt,
            content_type=ContentType.BLOG_POST,
            config=AIGenerationConfig(max_tokens=100, temperature=0.7)
        )
        
        # Generate content
        response = await provider.generate_content(test_request, model)
        
        response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        return AIProviderTestResponse(
            provider_type=provider_type,
            success=True,
            response_time_ms=response_time,
            tokens_used=response.tokens_used,
            cost_estimate=response.cost,
            generated_content=response.content,
            model_used=response.model,
            rate_limits=provider.get_rate_limits(),
            supported_models=provider.supported_models
        )
        
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        
        return AIProviderTestResponse(
            provider_type=provider_type,
            success=False,
            response_time_ms=response_time,
            error_message=str(e),
            error_code=type(e).__name__,
            supported_models=[]
        )


@router.post("/configure", response_model=AIProviderConfigResponse)
async def configure_provider(
    request: AIProviderConfigRequest,
    background_tasks: BackgroundTasks
):
    """
    Configure an AI provider with API key and settings.
    
    This endpoint allows the frontend to add or update AI provider configurations.
    The API key is validated before saving the configuration.
    """
    try:
        # Validate API key
        api_key_valid = await validate_api_key(request.provider_type, request.api_key.get_secret_value())
        
        if not api_key_valid:
            return AIProviderConfigResponse(
                provider_type=request.provider_type,
                status=AIProviderStatus.INVALID_KEY,
                priority=request.priority,
                enabled=False,
                api_key_valid=False,
                error_message="Invalid API key"
            )
        
        # Create provider instance
        provider_class = get_provider_class(request.provider_type)
        provider = provider_class(
            api_key=request.api_key.get_secret_value(),
            **(request.custom_config or {})
        )
        
        # Initialize provider
        await provider.initialize()
        
        # Create provider config
        provider_config = AIProviderConfig(
            provider_type=request.provider_type,
            api_key=request.api_key.get_secret_value(),
            default_model=request.default_model,
            priority=request.priority,
            enabled=request.enabled,
            custom_config=request.custom_config
        )
        
        # Add to manager
        provider_name = f"{request.provider_type.value}_{int(time.time())}"
        provider_manager.add_provider(provider_name, provider, provider_config)
        
        # Create response
        config_response = AIProviderConfigResponse(
            provider_type=request.provider_type,
            status=AIProviderStatus.CONFIGURED,
            priority=request.priority,
            enabled=request.enabled,
            api_key_valid=True,
            last_validated=datetime.utcnow(),
            supported_models=provider.supported_models,
            rate_limits=provider.get_rate_limits()
        )
        
        # Store configuration
        provider_configs[provider_name] = config_response
        
        # Initialize usage stats
        usage_stats[provider_name] = AIProviderUsageStats(provider_type=request.provider_type)
        
        # Schedule health check
        background_tasks.add_task(perform_health_check, provider_name, provider)
        
        logger.info(f"Successfully configured AI provider: {request.provider_type}")
        return config_response
        
    except Exception as e:
        logger.error(f"Failed to configure AI provider {request.provider_type}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to configure provider: {str(e)}"
        )


@router.get("/list", response_model=AIProviderListResponse)
async def list_providers():
    """
    List all configured AI providers with their status and capabilities.
    
    This endpoint provides the frontend with a complete overview of all
    configured AI providers, their status, and current configuration.
    """
    try:
        provider_list = list(provider_configs.values())
        active_provider = None
        fallback_order = provider_manager.fallback_order
        
        # Find active provider (first in fallback order)
        if fallback_order:
            active_provider = fallback_order[0]
        
        return AIProviderListResponse(
            providers=provider_list,
            active_provider=active_provider,
            fallback_order=fallback_order,
            total_providers=len(provider_list),
            configured_providers=len([p for p in provider_list if p.status == AIProviderStatus.CONFIGURED]),
            enabled_providers=len([p for p in provider_list if p.enabled])
        )
        
    except Exception as e:
        logger.error(f"Failed to list AI providers: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list providers: {str(e)}"
        )


@router.post("/test", response_model=AIProviderTestResponse)
async def test_provider(request: AIProviderTestRequest):
    """
    Test an AI provider configuration with a simple generation request.
    
    This endpoint allows the frontend to validate API keys and test
    provider functionality before saving the configuration.
    """
    try:
        result = await test_provider_generation(
            request.provider_type,
            request.api_key.get_secret_value(),
            request.test_prompt,
            request.model
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to test AI provider {request.provider_type}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to test provider: {str(e)}"
        )


@router.post("/switch", response_model=AIProviderSwitchResponse)
async def switch_provider(request: AIProviderSwitchRequest):
    """
    Switch the active AI provider for content generation.
    
    This endpoint allows the frontend to dynamically switch between
    configured AI providers without restarting the service.
    """
    try:
        # Find provider by type
        provider_name = None
        for name, config in provider_configs.items():
            if config.provider_type == request.provider_type and config.enabled:
                provider_name = name
                break
        
        if not provider_name:
            raise HTTPException(
                status_code=404,
                detail=f"Provider {request.provider_type} not found or not enabled"
            )
        
        # Get current active provider
        previous_provider = provider_manager.fallback_order[0] if provider_manager.fallback_order else None
        
        # Update provider priority to make it first
        if provider_name in provider_manager.provider_configs:
            provider_manager.provider_configs[provider_name].priority = 1
            provider_manager._update_fallback_order()
        
        current_provider = provider_manager.fallback_order[0] if provider_manager.fallback_order else None
        
        return AIProviderSwitchResponse(
            success=True,
            previous_provider=previous_provider,
            current_provider=current_provider or provider_name,
            message=f"Successfully switched to {request.provider_type}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to switch AI provider: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to switch provider: {str(e)}"
        )


@router.get("/health", response_model=Dict[str, AIProviderHealthCheck])
async def health_check_all():
    """
    Perform health checks on all configured AI providers.
    
    This endpoint provides real-time health status of all AI providers,
    including API key validity, rate limits, and error information.
    """
    try:
        health_results = {}
        
        for provider_name, provider in provider_manager.providers.items():
            try:
                health_result = await provider.health_check()
                
                health_check = AIProviderHealthCheck(
                    provider_type=provider.provider_type,
                    status=AIProviderStatus.CONFIGURED if health_result.get("status") == "healthy" else AIProviderStatus.ERROR,
                    api_key_valid=health_result.get("api_key_valid", False),
                    rate_limit_ok=health_result.get("rate_limits", {}).get("remaining", 0) > 0,
                    error_message=health_result.get("error")
                )
                
                health_results[provider_name] = health_check
                health_checks[provider_name] = health_check
                
            except Exception as e:
                health_check = AIProviderHealthCheck(
                    provider_type=provider.provider_type,
                    status=AIProviderStatus.ERROR,
                    error_message=str(e),
                    consecutive_failures=health_checks.get(provider_name, AIProviderHealthCheck(provider_type=provider.provider_type)).consecutive_failures + 1
                )
                health_results[provider_name] = health_check
                health_checks[provider_name] = health_check
        
        return health_results
        
    except Exception as e:
        logger.error(f"Failed to perform health checks: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to perform health checks: {str(e)}"
        )


@router.get("/stats", response_model=Dict[str, AIProviderUsageStats])
async def get_usage_stats():
    """
    Get usage statistics for all AI providers.
    
    This endpoint provides detailed usage statistics including request counts,
    success rates, costs, and performance metrics.
    """
    try:
        return usage_stats
        
    except Exception as e:
        logger.error(f"Failed to get usage stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get usage stats: {str(e)}"
        )


@router.get("/capabilities", response_model=Dict[str, AIProviderCapabilities])
async def get_provider_capabilities():
    """
    Get capabilities information for all supported AI providers.
    
    This endpoint provides information about what each AI provider supports,
    including available models, features, and limitations.
    """
    try:
        capabilities = {}
        
        for provider_type in AIProviderType:
            try:
                # Create a dummy provider to get capabilities
                provider_class = get_provider_class(provider_type)
                # Note: This would need to be implemented in each provider class
                # For now, we'll return basic information
                
                capabilities[provider_type.value] = AIProviderCapabilities(
                    provider_type=provider_type,
                    supported_models=[
                        AIProviderModelInfo(
                            model_id="default",
                            display_name=f"{provider_type.value.title()} Default Model",
                            description=f"Default model for {provider_type.value}"
                        )
                    ],
                    supports_streaming=True,
                    supports_function_calling=True,
                    pricing_model="per_token"
                )
                
            except Exception as e:
                logger.warning(f"Could not get capabilities for {provider_type}: {e}")
                continue
        
        return capabilities
        
    except Exception as e:
        logger.error(f"Failed to get provider capabilities: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get capabilities: {str(e)}"
        )


@router.delete("/{provider_name}")
async def remove_provider(provider_name: str):
    """
    Remove a configured AI provider.
    
    This endpoint allows the frontend to remove AI provider configurations
    that are no longer needed.
    """
    try:
        if provider_name not in provider_configs:
            raise HTTPException(
                status_code=404,
                detail=f"Provider {provider_name} not found"
            )
        
        # Remove from manager
        provider_manager.remove_provider(provider_name)
        
        # Remove from storage
        del provider_configs[provider_name]
        if provider_name in usage_stats:
            del usage_stats[provider_name]
        if provider_name in health_checks:
            del health_checks[provider_name]
        
        logger.info(f"Successfully removed AI provider: {provider_name}")
        return {"message": f"Provider {provider_name} removed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove AI provider {provider_name}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to remove provider: {str(e)}"
        )


@router.post("/bulk-configure", response_model=AIProviderBulkConfigResponse)
async def bulk_configure_providers(
    request: AIProviderBulkConfigRequest,
    background_tasks: BackgroundTasks
):
    """
    Configure multiple AI providers in a single request.
    
    This endpoint allows the frontend to configure multiple AI providers
    at once, useful for initial setup or bulk updates.
    """
    try:
        results = []
        errors = []
        successful_configs = 0
        
        for provider_request in request.providers:
            try:
                # Configure provider
                config_response = await configure_provider(provider_request, background_tasks)
                results.append(config_response)
                
                if config_response.status == AIProviderStatus.CONFIGURED:
                    successful_configs += 1
                else:
                    errors.append({
                        "provider": provider_request.provider_type.value,
                        "error": config_response.error_message or "Configuration failed"
                    })
                    
            except Exception as e:
                errors.append({
                    "provider": provider_request.provider_type.value,
                    "error": str(e)
                })
        
        return AIProviderBulkConfigResponse(
            total_providers=len(request.providers),
            successful_configs=successful_configs,
            failed_configs=len(errors),
            results=results,
            errors=errors
        )
        
    except Exception as e:
        logger.error(f"Failed to bulk configure providers: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to bulk configure providers: {str(e)}"
        )


async def perform_health_check(provider_name: str, provider):
    """Background task to perform health check on a provider."""
    try:
        health_result = await provider.health_check()
        
        health_check = AIProviderHealthCheck(
            provider_type=provider.provider_type,
            status=AIProviderStatus.CONFIGURED if health_result.get("status") == "healthy" else AIProviderStatus.ERROR,
            api_key_valid=health_result.get("api_key_valid", False),
            rate_limit_ok=health_result.get("rate_limits", {}).get("remaining", 0) > 0,
            error_message=health_result.get("error")
        )
        
        health_checks[provider_name] = health_check
        
    except Exception as e:
        logger.error(f"Health check failed for {provider_name}: {e}")
        health_check = AIProviderHealthCheck(
            provider_type=provider.provider_type,
            status=AIProviderStatus.ERROR,
            error_message=str(e)
        )
        health_checks[provider_name] = health_check


# Initialize with existing environment variables
async def initialize_from_env():
    """Initialize AI providers from environment variables."""
    try:
        # OpenAI
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            await configure_provider(
                AIProviderConfigRequest(
                    provider_type=AIProviderType.OPENAI,
                    api_key=openai_key,
                    default_model=os.getenv("OPENAI_DEFAULT_MODEL", "gpt-4o-mini"),
                    priority=1
                ),
                BackgroundTasks()
            )
        
        # Anthropic
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            await configure_provider(
                AIProviderConfigRequest(
                    provider_type=AIProviderType.ANTHROPIC,
                    api_key=anthropic_key,
                    default_model=os.getenv("ANTHROPIC_DEFAULT_MODEL", "claude-3-5-haiku-20241022"),
                    priority=2
                ),
                BackgroundTasks()
            )
        
        # Azure OpenAI
        azure_key = os.getenv("AZURE_OPENAI_API_KEY")
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        if azure_key and azure_endpoint:
            await configure_provider(
                AIProviderConfigRequest(
                    provider_type=AIProviderType.AZURE_OPENAI,
                    api_key=azure_key,
                    default_model=os.getenv("AZURE_OPENAI_DEFAULT_MODEL", "gpt-4o-mini"),
                    priority=3,
                    custom_config={
                        "azure_endpoint": azure_endpoint,
                        "api_version": os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
                    }
                ),
                BackgroundTasks()
            )
        
        logger.info("Initialized AI providers from environment variables")
        
    except Exception as e:
        logger.error(f"Failed to initialize AI providers from environment: {e}")


# Export the router and manager for use in main.py
__all__ = ["router", "provider_manager", "initialize_from_env"]
