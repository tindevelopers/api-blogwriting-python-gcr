# AI Provider Management API Guide

## Overview

The Blog Writer SDK API includes a comprehensive AI Provider Management system that allows frontend applications to dynamically configure, test, and switch between different AI providers without requiring service restarts. This system provides secure API key management, real-time health monitoring, and usage statistics.

## Supported AI Providers

### 1. OpenAI
- **Provider Type**: `openai`
- **Models**: GPT-4o, GPT-4o-mini, GPT-4-turbo, GPT-4, GPT-3.5-turbo
- **Features**: Text generation, function calling, streaming
- **Pricing**: Per-token pricing model

### 2. Anthropic
- **Provider Type**: `anthropic`
- **Models**: Claude-3.5-Haiku, Claude-3.5-Sonnet, Claude-3-Opus
- **Features**: Text generation, long context windows
- **Pricing**: Per-token pricing model

### 3. Azure OpenAI
- **Provider Type**: `azure_openai`
- **Models**: Same as OpenAI (hosted on Azure)
- **Features**: Enterprise-grade security, compliance
- **Pricing**: Azure-specific pricing

## API Endpoints

### Base URL
All AI provider management endpoints are prefixed with `/api/v1/ai/providers`

### 1. Configure AI Provider
**POST** `/api/v1/ai/providers/configure`

Configure a new AI provider with API key and settings.

**Request Body:**
```json
{
  "provider_type": "openai",
  "api_key": "sk-...",
  "default_model": "gpt-4o-mini",
  "priority": 1,
  "enabled": true,
  "custom_config": {
    "organization": "org-...",
    "timeout": 30
  }
}
```

**Response:**
```json
{
  "provider_type": "openai",
  "status": "configured",
  "configured_at": "2024-01-15T10:30:00Z",
  "default_model": "gpt-4o-mini",
  "priority": 1,
  "enabled": true,
  "api_key_valid": true,
  "last_validated": "2024-01-15T10:30:00Z",
  "supported_models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
  "rate_limits": {
    "requests_per_minute": 60,
    "tokens_per_minute": 150000
  },
  "total_requests": 0,
  "successful_requests": 0,
  "failed_requests": 0
}
```

### 2. List All Providers
**GET** `/api/v1/ai/providers/list`

Get a complete overview of all configured AI providers.

**Response:**
```json
{
  "providers": [
    {
      "provider_type": "openai",
      "status": "configured",
      "enabled": true,
      "priority": 1,
      "api_key_valid": true
    }
  ],
  "active_provider": "openai_1642248600",
  "fallback_order": ["openai_1642248600", "anthropic_1642248700"],
  "total_providers": 2,
  "configured_providers": 2,
  "enabled_providers": 2
}
```

### 3. Test Provider Configuration
**POST** `/api/v1/ai/providers/test`

Test an AI provider configuration with a simple generation request.

**Request Body:**
```json
{
  "provider_type": "openai",
  "api_key": "sk-...",
  "test_prompt": "Hello, this is a test prompt.",
  "model": "gpt-4o-mini"
}
```

**Response:**
```json
{
  "provider_type": "openai",
  "success": true,
  "response_time_ms": 1250.5,
  "tokens_used": 25,
  "cost_estimate": 0.0001,
  "generated_content": "Hello! This is a test response from the AI provider.",
  "model_used": "gpt-4o-mini",
  "rate_limits": {
    "requests_per_minute": 60,
    "tokens_per_minute": 150000
  },
  "supported_models": ["gpt-4o", "gpt-4o-mini"]
}
```

### 4. Switch Active Provider
**POST** `/api/v1/ai/providers/switch`

Dynamically switch the active AI provider for content generation.

**Request Body:**
```json
{
  "provider_type": "anthropic",
  "reason": "OpenAI rate limit exceeded"
}
```

**Response:**
```json
{
  "success": true,
  "previous_provider": "openai_1642248600",
  "current_provider": "anthropic_1642248700",
  "switched_at": "2024-01-15T10:35:00Z",
  "message": "Successfully switched to anthropic"
}
```

### 5. Health Check All Providers
**GET** `/api/v1/ai/providers/health`

Perform real-time health checks on all configured AI providers.

**Response:**
```json
{
  "openai_1642248600": {
    "provider_type": "openai",
    "status": "configured",
    "last_check": "2024-01-15T10:40:00Z",
    "response_time_ms": 150.2,
    "api_key_valid": true,
    "rate_limit_ok": true,
    "quota_available": true,
    "consecutive_failures": 0,
    "recommendations": []
  }
}
```

### 6. Get Usage Statistics
**GET** `/api/v1/ai/providers/stats`

Get detailed usage statistics for all AI providers.

**Response:**
```json
{
  "openai_1642248600": {
    "provider_type": "openai",
    "total_requests": 150,
    "successful_requests": 145,
    "failed_requests": 5,
    "total_tokens": 45000,
    "total_cost": 0.675,
    "avg_response_time_ms": 1200.5,
    "requests_today": 25,
    "requests_this_week": 150,
    "requests_this_month": 600,
    "rate_limit_errors": 2,
    "quota_exceeded_errors": 0,
    "authentication_errors": 1,
    "other_errors": 2
  }
}
```

### 7. Get Provider Capabilities
**GET** `/api/v1/ai/providers/capabilities`

Get information about what each AI provider supports.

**Response:**
```json
{
  "openai": {
    "provider_type": "openai",
    "supported_models": [
      {
        "model_id": "gpt-4o",
        "display_name": "GPT-4o",
        "description": "Most advanced GPT-4 model",
        "max_tokens": 128000,
        "cost_per_1k_tokens": 0.005,
        "context_window": 128000,
        "capabilities": ["text", "function_calling", "vision"],
        "recommended_for": ["complex_tasks", "reasoning", "analysis"]
      }
    ],
    "max_concurrent_requests": 10,
    "rate_limit_per_minute": 60,
    "supports_streaming": true,
    "supports_function_calling": true,
    "supports_vision": true,
    "pricing_model": "per_token"
  }
}
```

### 8. Remove Provider
**DELETE** `/api/v1/ai/providers/{provider_name}`

Remove a configured AI provider.

**Response:**
```json
{
  "message": "Provider openai_1642248600 removed successfully"
}
```

### 9. Bulk Configure Providers
**POST** `/api/v1/ai/providers/bulk-configure`

Configure multiple AI providers in a single request.

**Request Body:**
```json
{
  "providers": [
    {
      "provider_type": "openai",
      "api_key": "sk-...",
      "default_model": "gpt-4o-mini",
      "priority": 1
    },
    {
      "provider_type": "anthropic",
      "api_key": "sk-ant-...",
      "default_model": "claude-3-5-haiku-20241022",
      "priority": 2
    }
  ],
  "validate_keys": true,
  "enable_after_config": true
}
```

## Frontend Integration Examples

### React/Next.js Example

```typescript
// AI Provider Management Hook
import { useState, useEffect } from 'react';

interface AIProvider {
  provider_type: string;
  status: string;
  enabled: boolean;
  api_key_valid: boolean;
}

export const useAIProviders = () => {
  const [providers, setProviders] = useState<AIProvider[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchProviders = async () => {
    try {
      const response = await fetch('/api/v1/ai/providers/list');
      const data = await response.json();
      setProviders(data.providers);
    } catch (error) {
      console.error('Failed to fetch providers:', error);
    } finally {
      setLoading(false);
    }
  };

  const configureProvider = async (config: any) => {
    try {
      const response = await fetch('/api/v1/ai/providers/configure', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });
      const result = await response.json();
      await fetchProviders(); // Refresh list
      return result;
    } catch (error) {
      console.error('Failed to configure provider:', error);
      throw error;
    }
  };

  const testProvider = async (config: any) => {
    try {
      const response = await fetch('/api/v1/ai/providers/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });
      return await response.json();
    } catch (error) {
      console.error('Failed to test provider:', error);
      throw error;
    }
  };

  const switchProvider = async (providerType: string) => {
    try {
      const response = await fetch('/api/v1/ai/providers/switch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider_type: providerType })
      });
      return await response.json();
    } catch (error) {
      console.error('Failed to switch provider:', error);
      throw error;
    }
  };

  useEffect(() => {
    fetchProviders();
  }, []);

  return {
    providers,
    loading,
    configureProvider,
    testProvider,
    switchProvider,
    refreshProviders: fetchProviders
  };
};
```

### Vue.js Example

```vue
<template>
  <div class="ai-provider-management">
    <h2>AI Provider Management</h2>
    
    <!-- Provider List -->
    <div class="providers-list">
      <div 
        v-for="provider in providers" 
        :key="provider.provider_type"
        class="provider-card"
        :class="{ active: provider.provider_type === activeProvider }"
      >
        <h3>{{ provider.provider_type }}</h3>
        <p>Status: {{ provider.status }}</p>
        <p>API Key Valid: {{ provider.api_key_valid ? 'Yes' : 'No' }}</p>
        <button 
          @click="switchToProvider(provider.provider_type)"
          :disabled="!provider.enabled"
        >
          Switch to {{ provider.provider_type }}
        </button>
      </div>
    </div>

    <!-- Add New Provider -->
    <div class="add-provider">
      <h3>Add New Provider</h3>
      <form @submit.prevent="addProvider">
        <select v-model="newProvider.provider_type">
          <option value="openai">OpenAI</option>
          <option value="anthropic">Anthropic</option>
          <option value="azure_openai">Azure OpenAI</option>
        </select>
        <input 
          v-model="newProvider.api_key" 
          type="password" 
          placeholder="API Key"
          required
        />
        <input 
          v-model="newProvider.default_model" 
          placeholder="Default Model (optional)"
        />
        <button type="submit">Add Provider</button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';

const providers = ref([]);
const activeProvider = ref('');
const newProvider = ref({
  provider_type: 'openai',
  api_key: '',
  default_model: ''
});

const fetchProviders = async () => {
  try {
    const response = await fetch('/api/v1/ai/providers/list');
    const data = await response.json();
    providers.value = data.providers;
    activeProvider.value = data.active_provider;
  } catch (error) {
    console.error('Failed to fetch providers:', error);
  }
};

const addProvider = async () => {
  try {
    const response = await fetch('/api/v1/ai/providers/configure', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newProvider.value)
    });
    
    if (response.ok) {
      await fetchProviders();
      newProvider.value = { provider_type: 'openai', api_key: '', default_model: '' };
    }
  } catch (error) {
    console.error('Failed to add provider:', error);
  }
};

const switchToProvider = async (providerType) => {
  try {
    const response = await fetch('/api/v1/ai/providers/switch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ provider_type: providerType })
    });
    
    if (response.ok) {
      await fetchProviders();
    }
  } catch (error) {
    console.error('Failed to switch provider:', error);
  }
};

onMounted(() => {
  fetchProviders();
});
</script>
```

## Best Practices

### 1. Security
- **Never store API keys in frontend code**
- Use environment variables or secure key management
- Implement proper authentication for provider management endpoints
- Rotate API keys regularly

### 2. Error Handling
- Always handle API key validation failures gracefully
- Implement retry logic for rate limit errors
- Provide clear error messages to users
- Log errors for debugging

### 3. Performance
- Cache provider capabilities and health status
- Implement connection pooling for high-traffic applications
- Monitor usage statistics to optimize costs
- Use appropriate timeouts for API calls

### 4. User Experience
- Show real-time provider status
- Provide clear feedback during configuration
- Allow easy switching between providers
- Display usage statistics and costs

### 5. Monitoring
- Set up alerts for provider failures
- Monitor rate limits and quotas
- Track costs and usage patterns
- Implement health checks

## Environment Variables

The system automatically initializes providers from environment variables:

```bash
# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_DEFAULT_MODEL=gpt-4o-mini
OPENAI_ORGANIZATION=org-...

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_DEFAULT_MODEL=claude-3-5-haiku-20241022

# Azure OpenAI
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEFAULT_MODEL=gpt-4o-mini
```

## Troubleshooting

### Common Issues

1. **API Key Invalid**
   - Verify the API key is correct
   - Check if the key has proper permissions
   - Ensure the key is not expired

2. **Rate Limit Exceeded**
   - Implement exponential backoff
   - Switch to a different provider
   - Monitor usage patterns

3. **Provider Not Responding**
   - Check network connectivity
   - Verify provider status
   - Check service health endpoints

4. **Configuration Errors**
   - Validate request format
   - Check required fields
   - Verify provider-specific settings

### Debug Endpoints

- **Health Check**: `GET /api/v1/ai/providers/health`
- **Usage Stats**: `GET /api/v1/ai/providers/stats`
- **Provider List**: `GET /api/v1/ai/providers/list`

## Support

For additional support or questions about the AI Provider Management system:

1. Check the API documentation at `/docs`
2. Review the OpenAPI specification at `/openapi.json`
3. Monitor the health endpoints for real-time status
4. Check logs for detailed error information
