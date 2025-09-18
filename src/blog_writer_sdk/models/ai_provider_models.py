"""
AI Provider Management Models

This module contains Pydantic models for managing AI provider configurations,
API keys, and provider selection through the frontend interface.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, field_validator, SecretStr
from src.blog_writer_sdk.ai.base_provider import AIProviderType


class AIProviderStatus(str, Enum):
    """Status of AI provider configuration."""
    CONFIGURED = "configured"
    NOT_CONFIGURED = "not_configured"
    INVALID_KEY = "invalid_key"
    RATE_LIMITED = "rate_limited"
    QUOTA_EXCEEDED = "quota_exceeded"
    ERROR = "error"


class AIProviderConfigRequest(BaseModel):
    """Request model for configuring an AI provider."""
    
    provider_type: AIProviderType = Field(..., description="Type of AI provider")
    api_key: SecretStr = Field(..., description="API key for the provider")
    default_model: Optional[str] = Field(None, description="Default model to use")
    priority: int = Field(default=1, ge=1, le=10, description="Priority (1=highest, 10=lowest)")
    enabled: bool = Field(default=True, description="Whether provider is enabled")
    
    # Provider-specific configuration
    custom_config: Optional[Dict[str, Any]] = Field(None, description="Provider-specific settings")
    
    @field_validator('default_model')
    @classmethod
    def validate_default_model(cls, v, info):
        """Validate default model based on provider type."""
        if v and 'provider_type' in info.data:
            provider_type = info.data['provider_type']
            # Add model validation logic here if needed
            return v
        return v


class AIProviderConfigResponse(BaseModel):
    """Response model for AI provider configuration."""
    
    provider_type: AIProviderType = Field(..., description="Type of AI provider")
    status: AIProviderStatus = Field(..., description="Current status of the provider")
    configured_at: datetime = Field(default_factory=datetime.utcnow, description="When provider was configured")
    default_model: Optional[str] = Field(None, description="Default model configured")
    priority: int = Field(..., description="Provider priority")
    enabled: bool = Field(..., description="Whether provider is enabled")
    
    # Status information
    api_key_valid: bool = Field(default=False, description="Whether API key is valid")
    last_validated: Optional[datetime] = Field(None, description="Last validation timestamp")
    error_message: Optional[str] = Field(None, description="Error message if any")
    
    # Provider capabilities
    supported_models: List[str] = Field(default_factory=list, description="Supported models")
    rate_limits: Optional[Dict[str, Any]] = Field(None, description="Rate limit information")
    
    # Usage statistics
    total_requests: int = Field(default=0, description="Total requests made")
    successful_requests: int = Field(default=0, description="Successful requests")
    failed_requests: int = Field(default=0, description="Failed requests")
    last_used: Optional[datetime] = Field(None, description="Last usage timestamp")


class AIProviderListResponse(BaseModel):
    """Response model for listing all AI providers."""
    
    providers: List[AIProviderConfigResponse] = Field(..., description="List of configured providers")
    active_provider: Optional[str] = Field(None, description="Currently active provider")
    fallback_order: List[str] = Field(default_factory=list, description="Fallback provider order")
    total_providers: int = Field(..., description="Total number of providers")
    configured_providers: int = Field(..., description="Number of configured providers")
    enabled_providers: int = Field(..., description="Number of enabled providers")


class AIProviderTestRequest(BaseModel):
    """Request model for testing AI provider configuration."""
    
    provider_type: AIProviderType = Field(..., description="Type of AI provider to test")
    api_key: SecretStr = Field(..., description="API key to test")
    test_prompt: str = Field(default="Hello, this is a test prompt.", description="Test prompt to send")
    model: Optional[str] = Field(None, description="Specific model to test")


class AIProviderTestResponse(BaseModel):
    """Response model for AI provider test results."""
    
    provider_type: AIProviderType = Field(..., description="Type of AI provider tested")
    success: bool = Field(..., description="Whether test was successful")
    response_time_ms: float = Field(..., description="Response time in milliseconds")
    tokens_used: Optional[int] = Field(None, description="Tokens used in test")
    cost_estimate: Optional[float] = Field(None, description="Estimated cost of test")
    
    # Test results
    generated_content: Optional[str] = Field(None, description="Generated test content")
    model_used: Optional[str] = Field(None, description="Model that was used")
    
    # Error information
    error_message: Optional[str] = Field(None, description="Error message if test failed")
    error_code: Optional[str] = Field(None, description="Error code if test failed")
    
    # Provider information
    rate_limits: Optional[Dict[str, Any]] = Field(None, description="Rate limit information")
    supported_models: List[str] = Field(default_factory=list, description="Supported models")


class AIProviderSwitchRequest(BaseModel):
    """Request model for switching active AI provider."""
    
    provider_type: AIProviderType = Field(..., description="Provider to switch to")
    reason: Optional[str] = Field(None, description="Reason for switching")


class AIProviderSwitchResponse(BaseModel):
    """Response model for AI provider switching."""
    
    success: bool = Field(..., description="Whether switch was successful")
    previous_provider: Optional[str] = Field(None, description="Previous active provider")
    current_provider: str = Field(..., description="Current active provider")
    switched_at: datetime = Field(default_factory=datetime.utcnow, description="When switch occurred")
    message: str = Field(..., description="Status message")


class AIProviderUsageStats(BaseModel):
    """Usage statistics for AI providers."""
    
    provider_type: AIProviderType = Field(..., description="Provider type")
    total_requests: int = Field(default=0, description="Total requests")
    successful_requests: int = Field(default=0, description="Successful requests")
    failed_requests: int = Field(default=0, description="Failed requests")
    total_tokens: int = Field(default=0, description="Total tokens used")
    total_cost: float = Field(default=0.0, description="Total cost")
    avg_response_time_ms: float = Field(default=0.0, description="Average response time")
    
    # Time-based statistics
    requests_today: int = Field(default=0, description="Requests today")
    requests_this_week: int = Field(default=0, description="Requests this week")
    requests_this_month: int = Field(default=0, description="Requests this month")
    
    # Error breakdown
    rate_limit_errors: int = Field(default=0, description="Rate limit errors")
    quota_exceeded_errors: int = Field(default=0, description="Quota exceeded errors")
    authentication_errors: int = Field(default=0, description="Authentication errors")
    other_errors: int = Field(default=0, description="Other errors")


class AIProviderHealthCheck(BaseModel):
    """Health check information for AI providers."""
    
    provider_type: AIProviderType = Field(..., description="Provider type")
    status: AIProviderStatus = Field(..., description="Current status")
    last_check: datetime = Field(default_factory=datetime.utcnow, description="Last health check")
    response_time_ms: Optional[float] = Field(None, description="Health check response time")
    
    # Health indicators
    api_key_valid: bool = Field(default=False, description="API key validity")
    rate_limit_ok: bool = Field(default=True, description="Rate limit status")
    quota_available: bool = Field(default=True, description="Quota availability")
    
    # Error information
    error_message: Optional[str] = Field(None, description="Error message if unhealthy")
    consecutive_failures: int = Field(default=0, description="Consecutive failure count")
    
    # Recommendations
    recommendations: List[str] = Field(default_factory=list, description="Health recommendations")


class AIProviderBulkConfigRequest(BaseModel):
    """Request model for bulk AI provider configuration."""
    
    providers: List[AIProviderConfigRequest] = Field(..., description="List of providers to configure")
    validate_keys: bool = Field(default=True, description="Whether to validate API keys")
    enable_after_config: bool = Field(default=True, description="Whether to enable providers after configuration")


class AIProviderBulkConfigResponse(BaseModel):
    """Response model for bulk AI provider configuration."""
    
    total_providers: int = Field(..., description="Total providers processed")
    successful_configs: int = Field(..., description="Successfully configured providers")
    failed_configs: int = Field(..., description="Failed configurations")
    results: List[AIProviderConfigResponse] = Field(..., description="Individual results")
    errors: List[Dict[str, str]] = Field(default_factory=list, description="Configuration errors")


class AIProviderModelInfo(BaseModel):
    """Information about AI models available from a provider."""
    
    model_id: str = Field(..., description="Model identifier")
    display_name: str = Field(..., description="Human-readable model name")
    description: Optional[str] = Field(None, description="Model description")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens supported")
    cost_per_1k_tokens: Optional[float] = Field(None, description="Cost per 1k tokens")
    context_window: Optional[int] = Field(None, description="Context window size")
    capabilities: List[str] = Field(default_factory=list, description="Model capabilities")
    recommended_for: List[str] = Field(default_factory=list, description="Recommended use cases")


class AIProviderCapabilities(BaseModel):
    """Capabilities information for an AI provider."""
    
    provider_type: AIProviderType = Field(..., description="Provider type")
    supported_models: List[AIProviderModelInfo] = Field(..., description="Available models")
    max_concurrent_requests: Optional[int] = Field(None, description="Max concurrent requests")
    rate_limit_per_minute: Optional[int] = Field(None, description="Rate limit per minute")
    rate_limit_per_day: Optional[int] = Field(None, description="Rate limit per day")
    supports_streaming: bool = Field(default=False, description="Supports streaming responses")
    supports_function_calling: bool = Field(default=False, description="Supports function calling")
    supports_vision: bool = Field(default=False, description="Supports vision/image analysis")
    supports_audio: bool = Field(default=False, description="Supports audio processing")
    pricing_model: str = Field(default="per_token", description="Pricing model")
    data_retention_policy: Optional[str] = Field(None, description="Data retention policy")
