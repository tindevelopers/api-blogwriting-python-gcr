# Frontend Testing Guide - Backend API Endpoints

## 🔐 Authentication

All user management endpoints require JWT authentication using Supabase Auth tokens.

### Getting a JWT Token

1. **Sign in with Supabase Auth** (frontend):
```javascript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY)

// Sign in
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'password123'
})

// Get the access token
const token = data.session.access_token
```

2. **Use token in API requests**:
```javascript
const response = await fetch('https://blog-writer-api-dev-613248238610.europe-west9.run.app/api/v1/users', {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
})
```

### Authentication Flow

1. User signs in via Supabase Auth (frontend)
2. Frontend receives JWT token from Supabase
3. Frontend includes token in `Authorization: Bearer <token>` header
4. Backend verifies token with Supabase Auth
5. Backend retrieves user profile from Supabase database
6. Backend checks user role and permissions
7. Request is authorized or rejected based on role

### Required Environment Variables

For the backend to work with Supabase:
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_ANON_KEY` - Supabase anon key (for token verification)
- `SUPABASE_SERVICE_ROLE_KEY` - Supabase service role key (for database operations)

---

# Frontend Testing Guide - Backend API Endpoints

## Base URL

**Development Environment:**
```
https://blog-writer-api-dev-613248238610.europe-west9.run.app
```

**Staging Environment:**
```
https://blog-writer-api-staging-613248238610.europe-west9.run.app
```

**Production Environment:**
```
https://blog-writer-api-prod-613248238610.us-east1.run.app
```

---

## 1. Health Check Endpoints

### GET `/health`
Check if the API is running.

**Request:**
```bash
curl https://blog-writer-api-dev-613248238610.europe-west9.run.app/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-16T18:55:10.197256"
}
```

### GET `/`
Get API information and status.

**Request:**
```bash
curl https://blog-writer-api-dev-613248238610.europe-west9.run.app/
```

**Response:**
```json
{
  "message": "Blog Writer SDK API",
  "version": "1.0.0",
  "environment": "cloud-run",
  "testing_mode": true,
  "docs": "/docs",
  "health": "/health",
  "endpoints": {
    "generate": "/api/v1/blog/generate",
    "analyze": "/api/v1/analyze",
    "keywords": "/api/v1/keywords"
  }
}
```

---

## 2. Enhanced Blog Generation Endpoint

### POST `/api/v1/blog/generate-enhanced`

**Main endpoint for blog generation** - Supports both synchronous and async modes.

#### Synchronous Mode (Default)

**Request:**
```bash
curl -X POST https://blog-writer-api-dev-613248238610.europe-west9.run.app/api/v1/blog/generate-enhanced \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Dog grooming tips for beginners",
    "keywords": ["dog grooming", "pet care"],
    "tone": "professional",
    "length": "short",
    "include_images": false
  }'
```

**JavaScript/Fetch Example:**
```javascript
const response = await fetch('https://blog-writer-api-dev-613248238610.europe-west9.run.app/api/v1/blog/generate-enhanced', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    topic: "Dog grooming tips for beginners",
    keywords: ["dog grooming", "pet care"],
    tone: "professional",
    length: "short",
    include_images: false
  })
});

const blogPost = await response.json();
console.log(blogPost);
```

**Response Structure:**
```json
{
  "title": "Dog Grooming Tips for Beginners",
  "content": "# Dog Grooming Tips for Beginners\n\n...",
  "meta_title": "Dog Grooming Tips for Beginners: Complete Guide",
  "meta_description": "Learn essential dog grooming tips...",
  "readability_score": 75.5,
  "seo_score": 85.0,
  "stage_results": [...],
  "citations": [
    {
      "text": "...",
      "url": "https://...",
      "title": "Source Title"
    }
  ],
  "total_tokens": 2500,
  "total_cost": 0.05,
  "generation_time": 45.2,
  "seo_metadata": {...},
  "internal_links": [
    {
      "text": "dog grooming",
      "url": "/dog-grooming"
    }
  ],
  "quality_score": 88.5,
  "quality_dimensions": {...},
  "structured_data": {...},
  "semantic_keywords": ["pet care", "dog hygiene"],
  "content_metadata": {...},
  "success": true,
  "warnings": []
}
```

**Request Parameters:**
- `topic` (string, required): Blog topic
- `keywords` (array, required): List of keywords
- `tone` (string, optional): "professional", "casual", "friendly", "technical" (default: "professional")
- `length` (string, optional): "short", "medium", "long" (default: "medium")
- `include_images` (boolean, optional): Whether to generate images (default: false)
- `use_google_search` (boolean, optional): Enable Google Search research (default: true)
- `use_serp_optimization` (boolean, optional): Enable SERP optimization (default: true)
- `use_consensus_generation` (boolean, optional): Use multi-model consensus (default: false)
- `use_semantic_keywords` (boolean, optional): Enable semantic keyword integration (default: true)
- `use_quality_scoring` (boolean, optional): Enable quality scoring (default: true)
- `use_knowledge_graph` (boolean, optional): Enable Google Knowledge Graph (default: false)

#### Async Mode

**Request:**
```bash
curl -X POST "https://blog-writer-api-dev-613248238610.europe-west9.run.app/api/v1/blog/generate-enhanced?async_mode=true" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Advanced Python programming techniques",
    "keywords": ["python", "programming"],
    "tone": "professional",
    "length": "medium",
    "include_images": false
  }'
```

**JavaScript/Fetch Example:**
```javascript
const response = await fetch('https://blog-writer-api-dev-613248238610.europe-west9.run.app/api/v1/blog/generate-enhanced?async_mode=true', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    topic: "Advanced Python programming techniques",
    keywords: ["python", "programming"],
    tone: "professional",
    length: "medium",
    include_images: false
  })
});

const jobResponse = await response.json();
console.log('Job ID:', jobResponse.job_id);
```

**Response (Async Mode):**
```json
{
  "job_id": "c35fb264-5451-4a3b-80c6-c27fd9c34cb3",
  "status": "queued",
  "message": "Blog generation job queued successfully",
  "estimated_completion_time": 240
}
```

**Check Job Status:**
```bash
curl https://blog-writer-api-dev-613248238610.europe-west9.run.app/api/v1/blog/jobs/{job_id}
```

**JavaScript Example:**
```javascript
async function checkJobStatus(jobId) {
  const response = await fetch(`https://blog-writer-api-dev-613248238610.europe-west9.run.app/api/v1/blog/jobs/${jobId}`);
  const status = await response.json();
  
  console.log('Status:', status.status);
  console.log('Progress:', status.progress_percentage + '%');
  console.log('Current Stage:', status.current_stage);
  
  if (status.status === 'completed') {
    console.log('Blog:', status.result);
  }
  
  return status;
}

// Poll every 5 seconds
const jobId = 'c35fb264-5451-4a3b-80c6-c27fd9c34cb3';
const interval = setInterval(async () => {
  const status = await checkJobStatus(jobId);
  if (status.status === 'completed' || status.status === 'failed') {
    clearInterval(interval);
  }
}, 5000);
```

**Job Status Response:**
```json
{
  "job_id": "c35fb264-5451-4a3b-80c6-c27fd9c34cb3",
  "status": "completed",
  "progress_percentage": 100.0,
  "current_stage": "completed",
  "queued_at": "2025-11-16T18:55:10.197256",
  "started_at": "2025-11-16T18:55:15.123456",
  "completed_at": "2025-11-16T18:59:30.789012",
  "result": {
    "title": "...",
    "content": "...",
    "internal_links": [...],
    ...
  },
  "error_message": null
}
```

**Job Status Values:**
- `pending`: Job created but not yet queued
- `queued`: Job queued in Cloud Tasks
- `processing`: Job is being processed
- `completed`: Job completed successfully
- `failed`: Job failed with error

---

## 3. Keyword Analysis Endpoints

### POST `/api/v1/keywords/analyze`

Analyze keywords and get search volume, CPC, and related keywords.

**Request:**
```bash
curl -X POST https://blog-writer-api-dev-613248238610.europe-west9.run.app/api/v1/keywords/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": ["dog grooming", "pet care"],
    "search_type": "web",
    "language": "en",
    "location": "United States"
  }'
```

**JavaScript/Fetch Example:**
```javascript
const response = await fetch('https://blog-writer-api-dev-613248238610.europe-west9.run.app/api/v1/keywords/analyze', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    keywords: ["dog grooming", "pet care"],
    search_type: "web",
    language: "en",
    location: "United States"
  })
});

const analysis = await response.json();
console.log(analysis);
```

**Response:**
```json
{
  "keywords": [
    {
      "keyword": "dog grooming",
      "search_volume": 1300,
      "cpc": 3.81,
      "competition": 0.65,
      "trend_score": 0.75,
      "difficulty_score": 45.0,
      "recommended": true,
      "reason": "Good search volume with moderate competition"
    }
  ],
  "related_keywords": [...],
  "long_tail_keywords": [...],
  "total_keywords": 25
}
```

**Request Parameters:**
- `keywords` (array, required): List of keywords to analyze
- `search_type` (string, optional): "web", "news", "ecommerce" (default: "web")
- `language` (string, optional): Language code (default: "en")
- `location` (string, optional): Location name (default: "United States")

### POST `/api/v1/keywords/enhanced`

Enhanced keyword analysis with clustering and SERP data.

**Request:**
```bash
curl -X POST https://blog-writer-api-dev-613248238610.europe-west9.run.app/api/v1/keywords/enhanced \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": ["dog grooming", "pet care"],
    "include_clustering": true,
    "include_serp": true,
    "include_backlinks": false
  }'
```

**Response:**
```json
{
  "keywords": [...],
  "clusters": [
    {
      "cluster_id": 1,
      "theme": "Dog Grooming Services",
      "keywords": ["dog grooming", "pet grooming"],
      "avg_volume": 1200,
      "avg_cpc": 3.50
    }
  ],
  "serp_analysis": {...},
  "backlinks_analysis": {...},
  "trend_data": {...}
}
```

---

## 4. Standard Blog Generation Endpoint

### POST `/api/v1/blog/generate`

Simpler blog generation endpoint (without enhanced features).

**Request:**
```bash
curl -X POST https://blog-writer-api-dev-613248238610.europe-west9.run.app/api/v1/blog/generate \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Python programming tips",
    "keywords": ["python"],
    "tone": "professional",
    "length": "medium"
  }'
```

---

## 5. Error Handling

### Error Response Format

```json
{
  "error": "HTTP 500",
  "message": "Enhanced blog generation failed: ...",
  "timestamp": "2025-11-16T18:55:10.197256"
}
```

### Common Error Codes

- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Missing or invalid credentials
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Endpoint not found
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Service temporarily unavailable

### JavaScript Error Handling Example

```javascript
async function generateBlog(requestData) {
  try {
    const response = await fetch('https://blog-writer-api-dev-613248238610.europe-west9.run.app/api/v1/blog/generate-enhanced', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestData)
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || `HTTP ${response.status}`);
    }

    const blogPost = await response.json();
    return blogPost;
  } catch (error) {
    console.error('Blog generation failed:', error);
    throw error;
  }
}
```

---

## 6. Testing Scenarios

### Scenario 1: Quick Blog Generation (Synchronous)

```javascript
const quickBlog = await generateBlog({
  topic: "Quick test blog",
  keywords: ["test"],
  tone: "professional",
  length: "short",
  include_images: false
});
```

### Scenario 2: Long Blog with Async Mode

```javascript
// Start async job
const jobResponse = await fetch('https://blog-writer-api-dev-613248238610.europe-west9.run.app/api/v1/blog/generate-enhanced?async_mode=true', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    topic: "Comprehensive guide to Python programming",
    keywords: ["python", "programming", "tutorial"],
    tone: "professional",
    length: "long",
    include_images: false
  })
});

const { job_id } = await jobResponse.json();

// Poll for completion
const checkStatus = async () => {
  const status = await fetch(`https://blog-writer-api-dev-613248238610.europe-west9.run.app/api/v1/blog/jobs/${job_id}`);
  return await status.json();
};

// Poll every 5 seconds
const pollInterval = setInterval(async () => {
  const status = await checkStatus();
  if (status.status === 'completed') {
    clearInterval(pollInterval);
    console.log('Blog ready:', status.result);
  } else if (status.status === 'failed') {
    clearInterval(pollInterval);
    console.error('Blog generation failed:', status.error_message);
  }
}, 5000);
```

### Scenario 3: Keyword Research Before Blog Generation

```javascript
// First, analyze keywords
const keywordAnalysis = await fetch('https://blog-writer-api-dev-613248238610.europe-west9.run.app/api/v1/keywords/analyze', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    keywords: ["dog grooming", "pet care"],
    search_type: "web",
    language: "en",
    location: "United States"
  })
});

const analysis = await keywordAnalysis.json();

// Use top keywords for blog generation
const topKeywords = analysis.keywords
  .filter(k => k.recommended)
  .map(k => k.keyword)
  .slice(0, 5);

const blog = await generateBlog({
  topic: "Dog grooming guide",
  keywords: topKeywords,
  tone: "professional",
  length: "medium"
});
```

---

## 7. Internal Links Format

**Important:** Internal links are returned as `Dict[str, str]` with `text` and `url` keys.

```javascript
const blogPost = await generateBlog({...});

// Access internal links
blogPost.internal_links.forEach(link => {
  console.log(`Link: ${link.text} -> ${link.url}`);
  // Example: Link: dog grooming -> /dog-grooming
});
```

**Format:**
```json
{
  "internal_links": [
    {
      "text": "dog grooming",
      "url": "/dog-grooming"
    },
    {
      "text": "pet care",
      "url": "/pet-care"
    }
  ]
}
```

---

## 8. Testing Mode

When `TESTING_MODE=true` is enabled, the API applies data limits:

- **Max Keywords**: 5 primary keywords
- **Max Suggestions**: 5 per keyword
- **Max Long-tail**: 5 per keyword
- **Max Total Keywords**: 25

Check testing mode status:
```bash
curl https://blog-writer-api-dev-613248238610.europe-west9.run.app/
```

Response includes `"testing_mode": true/false`.

---

## 9. Complete Frontend Example

```javascript
class BlogWriterAPI {
  constructor(baseUrl) {
    this.baseUrl = baseUrl;
  }

  async generateBlog(requestData, asyncMode = false) {
    const url = `${this.baseUrl}/api/v1/blog/generate-enhanced${asyncMode ? '?async_mode=true' : ''}`;
    
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestData)
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || `HTTP ${response.status}`);
    }

    return await response.json();
  }

  async checkJobStatus(jobId) {
    const response = await fetch(`${this.baseUrl}/api/v1/blog/jobs/${jobId}`);
    if (!response.ok) {
      throw new Error(`Failed to check job status: ${response.status}`);
    }
    return await response.json();
  }

  async analyzeKeywords(keywords, options = {}) {
    const response = await fetch(`${this.baseUrl}/api/v1/keywords/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        keywords,
        search_type: options.search_type || 'web',
        language: options.language || 'en',
        location: options.location || 'United States'
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || `HTTP ${response.status}`);
    }

    return await response.json();
  }

  async healthCheck() {
    const response = await fetch(`${this.baseUrl}/health`);
    return await response.json();
  }
}

// Usage
const api = new BlogWriterAPI('https://blog-writer-api-dev-613248238610.europe-west9.run.app');

// Generate blog synchronously
const blog = await api.generateBlog({
  topic: "Dog grooming tips",
  keywords: ["dog grooming"],
  tone: "professional",
  length: "short"
});

// Generate blog asynchronously
const job = await api.generateBlog({
  topic: "Advanced Python guide",
  keywords: ["python"],
  tone: "professional",
  length: "long"
}, true);

// Check job status
const status = await api.checkJobStatus(job.job_id);
```

---

## 10. Quick Test Checklist

- [ ] Health check endpoint returns `{"status": "healthy"}`
- [ ] Root endpoint returns API information
- [ ] Synchronous blog generation works
- [ ] Async blog generation creates job
- [ ] Job status endpoint returns job information
- [ ] Keyword analysis returns search volume and CPC
- [ ] Internal links are properly formatted (Dict[str, str])
- [ ] Error handling works correctly
- [ ] Testing mode limits are applied when enabled

---

## Support

For issues or questions:
- Check API documentation: `https://blog-writer-api-dev-613248238610.europe-west9.run.app/docs`
- Review error messages in response
- Check Cloud Run logs for detailed error information

