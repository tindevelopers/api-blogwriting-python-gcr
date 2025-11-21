# Rate Limiting Setup for Production

## Current Status: ⚠️ Rate Limiting Disabled

Your API has rate limiting middleware available but it's **currently disabled**:
```python
# Add rate limiting middleware (disabled for development)
# app.middleware("http")(rate_limit_middleware)
```

## Enable Rate Limiting

### 1. Enable the Middleware
```python
# In main.py, uncomment this line:
app.middleware("http")(rate_limit_middleware)
```

### 2. Configure Rate Limits
Add to your environment variables:
```bash
# Rate limiting configuration
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_REQUESTS_PER_HOUR=1000
RATE_LIMIT_BURST_SIZE=10
```

### 3. Custom Rate Limits per Endpoint
```python
# Add to main.py
from fastapi import Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Apply to specific endpoints
@app.post("/api/v1/blog/generate")
@limiter.limit("5/minute")  # 5 blog generations per minute
async def generate_blog(request: Request, ...):
    # ... endpoint logic

@app.post("/api/v1/keywords/analyze")
@limiter.limit("30/minute")  # 30 keyword analyses per minute
async def analyze_keywords(request: Request, ...):
    # ... endpoint logic
```

## Recommended Rate Limits for Next.js Frontend

| Endpoint | Rate Limit | Reason |
|----------|------------|--------|
| `/api/v1/blog/generate` | 5/minute | Expensive AI operations |
| `/api/v1/keywords/analyze` | 30/minute | Moderate cost |
| `/api/v1/images/generate` | 3/minute | Very expensive operations |
| `/health`, `/metrics` | 120/minute | Lightweight checks |

## Frontend Handling
```javascript
// Handle rate limit errors in Next.js
const handleApiCall = async (data) => {
  try {
    const response = await fetch('/api/blog/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    
    if (response.status === 429) {
      // Rate limit exceeded
      const retryAfter = response.headers.get('Retry-After');
      throw new Error(`Rate limit exceeded. Try again in ${retryAfter} seconds.`);
    }
    
    return await response.json();
  } catch (error) {
    // Handle rate limit errors gracefully
    console.error('API Error:', error.message);
  }
};
```

