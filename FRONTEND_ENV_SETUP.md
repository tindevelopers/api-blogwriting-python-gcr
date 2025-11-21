# Environment Configuration for Next.js Frontend

## Required Environment Variables

### 1. API Configuration
```bash
# .env.local (Next.js frontend)
NEXT_PUBLIC_API_URL=http://localhost:8000  # Development
# NEXT_PUBLIC_API_URL=https://your-api-domain.com  # Production

NEXT_PUBLIC_API_KEY=your-frontend-api-key
NEXT_PUBLIC_SUPABASE_URL=your-supabase-url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key
```

### 2. Feature Flags
```bash
# Feature toggles for frontend
NEXT_PUBLIC_ENABLE_IMAGE_GENERATION=true
NEXT_PUBLIC_ENABLE_BATCH_PROCESSING=true
NEXT_PUBLIC_ENABLE_ANALYTICS=true
NEXT_PUBLIC_MAX_BLOG_LENGTH=2000
```

### 3. Rate Limiting Configuration
```bash
# Frontend rate limiting awareness
NEXT_PUBLIC_RATE_LIMIT_BLOG_GENERATION=5
NEXT_PUBLIC_RATE_LIMIT_KEYWORD_ANALYSIS=30
NEXT_PUBLIC_RATE_LIMIT_IMAGE_GENERATION=3
```

## Next.js Configuration

### 1. API Route Configuration
```javascript
// next.config.js
/** @type {import('next').NextConfig} */
const nextConfig = {
  env: {
    CUSTOM_KEY: process.env.CUSTOM_KEY,
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_URL}/api/:path*`,
      },
    ];
  },
  async headers() {
    return [
      {
        source: '/api/:path*',
        headers: [
          {
            key: 'Access-Control-Allow-Origin',
            value: '*',
          },
          {
            key: 'Access-Control-Allow-Methods',
            value: 'GET, POST, PUT, DELETE, OPTIONS',
          },
          {
            key: 'Access-Control-Allow-Headers',
            value: 'Content-Type, Authorization',
          },
        ],
      },
    ];
  },
};

module.exports = nextConfig;
```

### 2. Environment Validation
```javascript
// lib/env.js
export const env = {
  API_URL: process.env.NEXT_PUBLIC_API_URL,
  API_KEY: process.env.NEXT_PUBLIC_API_KEY,
  SUPABASE_URL: process.env.NEXT_PUBLIC_SUPABASE_URL,
  SUPABASE_ANON_KEY: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
  
  // Feature flags
  ENABLE_IMAGE_GENERATION: process.env.NEXT_PUBLIC_ENABLE_IMAGE_GENERATION === 'true',
  ENABLE_BATCH_PROCESSING: process.env.NEXT_PUBLIC_ENABLE_BATCH_PROCESSING === 'true',
  
  // Rate limits
  RATE_LIMIT_BLOG: parseInt(process.env.NEXT_PUBLIC_RATE_LIMIT_BLOG_GENERATION || '5'),
  RATE_LIMIT_KEYWORDS: parseInt(process.env.NEXT_PUBLIC_RATE_LIMIT_KEYWORD_ANALYSIS || '30'),
  
  // Validation
  validate() {
    const required = ['API_URL', 'API_KEY'];
    const missing = required.filter(key => !this[key]);
    
    if (missing.length > 0) {
      throw new Error(`Missing required environment variables: ${missing.join(', ')}`);
    }
  }
};

// Call validation on import
env.validate();
```

### 3. API Client Configuration
```javascript
// lib/api-client.js
import { env } from './env';

class ApiClient {
  constructor() {
    this.baseURL = env.API_URL;
    this.apiKey = env.API_KEY;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    
    const config = {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.apiKey}`,
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({ 
          message: 'Network error' 
        }));
        throw new Error(error.message || `HTTP ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('API Request failed:', error);
      throw error;
    }
  }

  // Blog generation
  async generateBlog(data) {
    return this.request('/api/v1/blog/generate', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Keyword analysis
  async analyzeKeywords(data) {
    return this.request('/api/v1/keywords/analyze', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Health check
  async healthCheck() {
    return this.request('/health');
  }
}

export const apiClient = new ApiClient();
```

## Production Deployment Considerations

### 1. API Domain Configuration
```bash
# Production environment variables
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_WS_URL=wss://api.yourdomain.com  # For WebSocket connections
```

### 2. CORS Configuration Update
Update your FastAPI CORS settings for production:
```python
# In main.py, update CORS origins for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Development
        "https://yourdomain.com",  # Production
        "https://www.yourdomain.com",  # Production with www
        "https://*.vercel.app",   # Vercel deployments
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
```

### 3. SSL/HTTPS Configuration
Ensure your API is served over HTTPS in production:
```python
# For production deployment
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        ssl_keyfile="path/to/keyfile",
        ssl_certfile="path/to/certfile",
    )
```

