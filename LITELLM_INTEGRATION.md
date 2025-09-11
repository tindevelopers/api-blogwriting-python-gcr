# 🚀 LiteLLM Integration Guide

This guide covers the integration of LiteLLM router for intelligent AI provider routing and cost optimization in the BlogWriter SDK.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Configuration](#configuration)
- [API Endpoints](#api-endpoints)
- [Usage Examples](#usage-examples)
- [Cost Optimization](#cost-optimization)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)

## 🎯 Overview

The BlogWriter SDK now includes **LiteLLM integration** for:

- **Intelligent AI Provider Routing**: Automatically select the best AI model for each task
- **Cost Optimization**: Route simple tasks to cheaper models, complex tasks to premium models
- **Automatic Failover**: Seamless fallback between providers when one fails
- **Multi-Modal Support**: Handle text, images, and other content types
- **Real-Time Cost Tracking**: Monitor and optimize AI spending

### Supported Providers

- ✅ **OpenAI**: GPT-4o, GPT-4-turbo, GPT-3.5-turbo
- ✅ **DeepSeek**: deepseek-chat, deepseek-coder
- ✅ **Anthropic**: Claude models (configurable)
- ✅ **Azure OpenAI**: All OpenAI models via Azure
- 🔄 **100+ more providers** supported by LiteLLM

## 🌟 Features

### 1. **Task-Based Routing**
```python
# Blog generation uses premium models
TaskType.BLOG_GENERATION → GPT-4o, GPT-4-turbo

# SEO analysis uses balanced models  
TaskType.SEO_ANALYSIS → GPT-3.5-turbo, DeepSeek

# Keyword extraction uses cost-optimized models
TaskType.KEYWORD_EXTRACTION → DeepSeek, GPT-3.5-turbo
```

### 2. **Complexity-Based Selection**
```python
# High complexity → Premium models
TaskComplexity.HIGH → GPT-4o, GPT-4-turbo

# Medium complexity → Balanced approach
TaskComplexity.MEDIUM → GPT-4o, DeepSeek

# Low complexity → Cost-optimized models
TaskComplexity.LOW → DeepSeek, GPT-3.5-turbo
```

### 3. **Automatic Failover**
```yaml
fallbacks:
  - ["gpt-4o", "gpt-4-turbo", "deepseek-chat"]
  - ["gpt-3.5-turbo", "deepseek-chat"]
  - ["deepseek-chat", "gpt-3.5-turbo"]
```

## ⚙️ Configuration

### 1. **Environment Variables**

Add to your `.env` file:

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# DeepSeek Configuration  
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_API_BASE=https://api.deepseek.com

# LiteLLM Configuration
LITELLM_MASTER_KEY=your_litellm_master_key_here
LITELLM_CONFIG_PATH=litellm_config.yaml

# Optional: Redis for caching
REDIS_HOST=localhost
REDIS_PORT=6379
```

### 2. **LiteLLM Configuration File**

The `litellm_config.yaml` file defines:

```yaml
model_list:
  # OpenAI Models
  - model_name: gpt-4o
    litellm_params:
      model: openai/gpt-4o
      api_key: os.environ/OPENAI_API_KEY
      rpm: 500
      tpm: 30000
      max_tokens: 4096
      temperature: 0.7
    model_info:
      mode: chat
      supports_vision: true
      supports_function_calling: true
      input_cost_per_token: 0.000005
      output_cost_per_token: 0.000015

  # DeepSeek Models
  - model_name: deepseek-chat
    litellm_params:
      model: deepseek/deepseek-chat
      api_key: os.environ/DEEPSEEK_API_KEY
      api_base: https://api.deepseek.com
      rpm: 1000
      tpm: 50000
      max_tokens: 4096
      temperature: 0.7
    model_info:
      mode: chat
      supports_function_calling: true
      input_cost_per_token: 0.00000014
      output_cost_per_token: 0.00000028

# Router Settings
router_settings:
  routing_strategy: "cost-based-routing"
  fallbacks:
    - ["gpt-4o", "gpt-4-turbo", "deepseek-chat"]
    - ["gpt-3.5-turbo", "deepseek-chat"]

# Task-based routing rules
task_routing:
  blog_generation:
    primary_models: ["gpt-4o", "gpt-4-turbo"]
    fallback_models: ["deepseek-chat"]
    max_cost: 0.10
    
  seo_analysis:
    primary_models: ["gpt-3.5-turbo", "deepseek-chat"]
    fallback_models: ["gpt-4o"]
    max_cost: 0.02
    
  keyword_extraction:
    primary_models: ["deepseek-chat", "gpt-3.5-turbo"]
    fallback_models: ["gpt-4o"]
    max_cost: 0.01
```

## 🔗 API Endpoints

### 1. **LiteLLM Health Check**
```http
GET /api/v1/litellm/health
```

**Response:**
```json
{
  "router_status": "healthy",
  "models": {
    "gpt-4o": {
      "status": "healthy",
      "response_time": "fast"
    },
    "deepseek-chat": {
      "status": "healthy",
      "response_time": "fast"
    }
  },
  "total_models": 2,
  "healthy_models": 2
}
```

### 2. **Available Models**
```http
GET /api/v1/litellm/models
```

**Response:**
```json
{
  "models": ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo", "deepseek-chat", "deepseek-coder"],
  "count": 5
}
```

### 3. **Cost Summary**
```http
GET /api/v1/litellm/costs
```

**Response:**
```json
{
  "total_cost": 0.45,
  "cost_by_task": {
    "blog_generation": 0.35,
    "seo_analysis": 0.08,
    "keyword_extraction": 0.02
  },
  "average_cost_per_task": 0.15
}
```

### 4. **Direct Content Generation**
```http
POST /api/v1/litellm/generate
```

**Request:**
```json
{
  "prompt": "Write a blog post about AI in healthcare",
  "task_type": "blog_generation",
  "complexity": "high",
  "max_tokens": 4096,
  "temperature": 0.7
}
```

**Response:**
```json
{
  "success": true,
  "content": "# AI in Healthcare: Transforming Patient Care...",
  "model_used": "gpt-4o",
  "usage": {
    "prompt_tokens": 15,
    "completion_tokens": 1250,
    "total_tokens": 1265
  },
  "metadata": {
    "task_type": "blog_generation",
    "complexity": "high",
    "cost": 0.025
  }
}
```

## 💡 Usage Examples

### 1. **Python SDK Integration**

```python
from src.blog_writer_sdk.ai.litellm_router import (
    LiteLLMRouterProvider, 
    TaskType, 
    TaskComplexity
)

# Initialize router
router = LiteLLMRouterProvider(
    config_path="litellm_config.yaml",
    enable_cost_tracking=True
)

# Generate blog content (uses premium models)
response = await router.generate_content(
    prompt="Write about sustainable technology",
    task_type=TaskType.BLOG_GENERATION,
    complexity=TaskComplexity.HIGH
)

# Extract keywords (uses cost-optimized models)
keywords_response = await router.generate_content(
    prompt="Extract keywords from: " + content,
    task_type=TaskType.KEYWORD_EXTRACTION,
    complexity=TaskComplexity.LOW
)

# Check costs
cost_summary = router.get_cost_summary()
print(f"Total cost: ${cost_summary['total_cost']:.4f}")
```

### 2. **Multi-Modal Content Analysis**

```python
# Analyze images with text
response = await router.generate_with_images(
    prompt="Describe this image and suggest blog topics",
    images=["https://example.com/image.jpg"],
    max_tokens=2048
)

print(f"Analysis: {response.content}")
print(f"Model used: {response.model}")
```

### 3. **Task-Specific Helper Functions**

```python
from src.blog_writer_sdk.ai.litellm_router import (
    generate_blog_content,
    analyze_seo_content,
    extract_keywords
)

# Generate blog content
blog_response = await generate_blog_content(
    router=router,
    prompt="Write about renewable energy trends",
    complexity=TaskComplexity.HIGH
)

# Analyze SEO
seo_response = await analyze_seo_content(
    router=router,
    content=blog_response.content
)

# Extract keywords
keywords_response = await extract_keywords(
    router=router,
    content=blog_response.content,
    max_keywords=20
)
```

### 4. **JavaScript/TypeScript Frontend**

```typescript
// Health check
const healthResponse = await fetch('/api/v1/litellm/health');
const health = await healthResponse.json();

// Generate content
const generateResponse = await fetch('/api/v1/litellm/generate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    prompt: 'Write a blog post about AI trends',
    task_type: 'blog_generation',
    complexity: 'high',
    max_tokens: 4096,
    temperature: 0.7
  })
});

const result = await generateResponse.json();
console.log(`Generated content: ${result.content}`);
console.log(`Cost: $${result.metadata.cost}`);
```

## 💰 Cost Optimization

### 1. **Automatic Cost Routing**

The router automatically selects models based on:

- **Task complexity**: Simple tasks → cheaper models
- **Content type**: Multi-modal → vision-capable models
- **Quality requirements**: High-quality → premium models
- **Budget constraints**: Configurable cost limits per task

### 2. **Cost Tracking**

```python
# Get detailed cost breakdown
cost_summary = router.get_cost_summary()

print(f"Total spent: ${cost_summary['total_cost']:.4f}")
print(f"Blog generation: ${cost_summary['cost_by_task']['blog_generation']:.4f}")
print(f"SEO analysis: ${cost_summary['cost_by_task']['seo_analysis']:.4f}")
print(f"Average per task: ${cost_summary['average_cost_per_task']:.4f}")
```

### 3. **Budget Controls**

Configure maximum costs per task type:

```yaml
task_routing:
  blog_generation:
    max_cost: 0.10  # Maximum $0.10 per blog post
  seo_analysis:
    max_cost: 0.02  # Maximum $0.02 per analysis
  keyword_extraction:
    max_cost: 0.01  # Maximum $0.01 per extraction
```

## 🚀 Deployment

### 1. **Standalone Proxy Server**

```bash
# Start LiteLLM proxy server
python litellm_proxy.py

# Server starts on http://localhost:8001
# Health check: http://localhost:8001/health
# OpenAI-compatible: http://localhost:8001/v1/chat/completions
```

### 2. **Docker Deployment**

```dockerfile
# Add to your Dockerfile
COPY litellm_config.yaml ./
COPY litellm_proxy.py ./

# Install LiteLLM
RUN pip install litellm

# Expose proxy port
EXPOSE 8001

# Start both services
CMD ["python", "litellm_proxy.py"]
```

### 3. **Railway Deployment**

The LiteLLM router is automatically included when you deploy the main BlogWriter API to Railway.

### 4. **Environment Configuration**

```bash
# Production environment variables
LITELLM_HOST=0.0.0.0
LITELLM_PORT=8001
LITELLM_CONFIG_PATH=litellm_config.yaml
LITELLM_MASTER_KEY=your_secure_master_key

# Enable caching for better performance
REDIS_HOST=your_redis_host
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password
```

## 🔧 Troubleshooting

### 1. **Common Issues**

**Router not initializing:**
```bash
# Check configuration file
cat litellm_config.yaml

# Verify API keys
echo $OPENAI_API_KEY
echo $DEEPSEEK_API_KEY
```

**Model not available:**
```python
# Check available models
models = router.get_available_models()
print(f"Available models: {models}")

# Check health status
health = await router.health_check()
print(f"Health status: {health}")
```

**High costs:**
```python
# Monitor costs in real-time
cost_summary = router.get_cost_summary()
print(f"Current costs: {cost_summary}")

# Adjust routing strategy
# Use more cost-optimized models for simple tasks
```

### 2. **Performance Optimization**

**Enable caching:**
```yaml
general_settings:
  cache:
    type: "redis"
    host: os.environ/REDIS_HOST
    port: 6379
    ttl: 3600  # Cache for 1 hour
```

**Adjust rate limits:**
```yaml
model_list:
  - model_name: gpt-4o
    litellm_params:
      rpm: 500    # Requests per minute
      tpm: 30000  # Tokens per minute
```

### 3. **Monitoring**

**Health checks:**
```bash
# Check router health
curl http://localhost:8000/api/v1/litellm/health

# Check individual models
curl http://localhost:8000/api/v1/litellm/models
```

**Cost monitoring:**
```bash
# Get cost summary
curl http://localhost:8000/api/v1/litellm/costs
```

## 📚 Additional Resources

- **LiteLLM Documentation**: [docs.litellm.ai](https://docs.litellm.ai)
- **Supported Providers**: [litellm.ai/providers](https://litellm.ai/providers)
- **Cost Optimization Guide**: See main README.md
- **API Reference**: Check `/docs` endpoint when server is running

## 🤝 Contributing

1. Fork the repository
2. Add new provider configurations
3. Implement custom routing strategies
4. Submit pull requests with improvements

## 📄 License

This integration maintains the same MIT license as the main BlogWriter SDK.
