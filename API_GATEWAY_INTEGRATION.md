# 🚀 API Gateway Integration Guide

## Overview
Your **API AI Blog Writer** is perfect for integration into an API gateway/control panel! Here's how to add it to your existing system.

## 🔗 API Endpoints Summary

### **Core Blog Generation**
- `POST /api/v1/generate` - Generate blog posts
- `POST /api/v1/blog/generate` - Alternative endpoint
- `POST /api/v1/abstraction/blog/generate` - Advanced generation

### **Content Analysis**
- `POST /api/v1/analyze` - Analyze existing content
- `POST /api/v1/optimize` - Optimize content for SEO

### **Keyword Tools**
- `POST /api/v1/keywords/analyze` - Analyze keywords
- `POST /api/v1/keywords/extract` - Extract keywords from content
- `POST /api/v1/keywords/suggest` - Get keyword suggestions

### **Batch Processing**
- `POST /api/v1/batch/generate` - Create batch jobs
- `GET /api/v1/batch/{job_id}/status` - Check job status
- `GET /api/v1/batch/{job_id}/stream` - Stream results

### **Monitoring**
- `GET /health` - Health check
- `GET /api/v1/metrics` - System metrics
- `GET /api/v1/config` - API configuration

## 🎯 Integration Examples

### 1. **Simple Blog Generation**
```javascript
// Add to your API gateway
const blogWriterAPI = {
  name: "Blog Writer AI",
  baseUrl: "https://api-ai-blog-writer-kq42l26tuq-ue.a.run.app",
  endpoints: {
    generate: "/api/v1/generate",
    analyze: "/api/v1/analyze",
    keywords: "/api/v1/keywords/analyze"
  }
};

// Example request
const generateBlog = async (topic, keywords = []) => {
  const response = await fetch(`${blogWriterAPI.baseUrl}${blogWriterAPI.endpoints.generate}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': 'YOUR_API_KEY' // If you implement auth
    },
    body: JSON.stringify({
      topic: topic,
      keywords: keywords,
      tone: "professional",
      length: "medium",
      format: "html"
    })
  });
  return response.json();
};
```

### 2. **API Gateway Configuration**
```yaml
# Add to your gateway config
services:
  blog-writer:
    name: "Blog Writer AI"
    url: "https://api-ai-blog-writer-kq42l26tuq-ue.a.run.app"
    endpoints:
      - path: "/api/v1/generate"
        method: "POST"
        description: "Generate blog posts"
      - path: "/api/v1/analyze"
        method: "POST"
        description: "Analyze content"
      - path: "/api/v1/keywords/*"
        method: "POST"
        description: "Keyword analysis tools"
    rate_limit: "100/hour"
    auth: "api_key"
```

### 3. **Frontend Integration**
```jsx
// React component for your control panel
import React, { useState } from 'react';

const BlogWriterPanel = () => {
  const [topic, setTopic] = useState('');
  const [keywords, setKeywords] = useState('');
  const [result, setResult] = useState(null);

  const generateBlog = async () => {
    const response = await fetch('/api/gateway/blog-writer/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        topic,
        keywords: keywords.split(',').map(k => k.trim())
      })
    });
    setResult(await response.json());
  };

  return (
    <div className="blog-writer-panel">
      <h3>Blog Writer AI</h3>
      <input 
        placeholder="Blog topic"
        value={topic}
        onChange={(e) => setTopic(e.target.value)}
      />
      <input 
        placeholder="Keywords (comma-separated)"
        value={keywords}
        onChange={(e) => setKeywords(e.target.value)}
      />
      <button onClick={generateBlog}>Generate Blog</button>
      {result && (
        <div className="result">
          <h4>{result.title}</h4>
          <div dangerouslySetInnerHTML={{ __html: result.content }} />
        </div>
      )}
    </div>
  );
};
```

## 🔐 Authentication Options

### Option 1: API Key (Recommended)
```bash
# Generate API key
API_KEY=$(openssl rand -hex 32)

# Store in your gateway's secret management
echo "$API_KEY" | gcloud secrets versions add blog-writer-api-key --data-file=-
```

### Option 2: IAM Authentication
```bash
# Grant access to your gateway service account
gcloud run services add-iam-policy-binding api-ai-blog-writer \
  --region=us-east1 \
  --member="serviceAccount:your-gateway@project.iam.gserviceaccount.com" \
  --role="roles/run.invoker" \
  --project=api-ai-blog-writer
```

## 📊 Monitoring Integration

### Add to your monitoring dashboard:
```javascript
const blogWriterMetrics = {
  health: "https://api-ai-blog-writer-kq42l26tuq-ue.a.run.app/health",
  metrics: "https://api-ai-blog-writer-kq42l26tuq-ue.a.run.app/api/v1/metrics",
  status: "https://api-ai-blog-writer-kq42l26tuq-ue.a.run.app/api/v1/cloudrun/status"
};
```

## 🚀 Quick Setup

1. **Add to your gateway config**
2. **Set up authentication**
3. **Configure rate limiting**
4. **Add monitoring**
5. **Test integration**

Your Blog Writer API is now ready for your API gateway! 🎉

