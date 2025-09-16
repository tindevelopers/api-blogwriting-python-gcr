# 🌐 Frontend Integration Guide

## Creating a Frontend for Your BlogWriter SDK

### Option 1: Next.js Frontend (Recommended)

#### 1. Create New Next.js Project
```bash
npx create-next-app@latest blog-writer-frontend
cd blog-writer-frontend
npm install axios
```

#### 2. Environment Configuration
Create `.env.local`:
```bash
NEXT_PUBLIC_BLOGWRITER_API_URL=https://blog-writer-sdk-kq42l26tuq-uc.a.run.app
```

#### 3. API Client Setup
Create `lib/blogwriter-api.js`:
```javascript
import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_BLOGWRITER_API_URL;

const blogWriterAPI = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const generateBlogPost = async (blogRequest) => {
  try {
    const response = await blogWriterAPI.post('/api/v1/blog/generate', blogRequest);
    return response.data;
  } catch (error) {
    throw new Error(`Blog generation failed: ${error.response?.data?.message || error.message}`);
  }
};

export const getAPIConfig = async () => {
  try {
    const response = await blogWriterAPI.get('/api/v1/config');
    return response.data;
  } catch (error) {
    throw new Error(`Failed to fetch API config: ${error.message}`);
  }
};

export const checkAIHealth = async () => {
  try {
    const response = await blogWriterAPI.get('/api/v1/ai/health');
    return response.data;
  } catch (error) {
    throw new Error(`AI health check failed: ${error.message}`);
  }
};
```

#### 4. Blog Generator Component
Create `components/BlogGenerator.jsx`:
```jsx
import { useState } from 'react';
import { generateBlogPost } from '../lib/blogwriter-api';

export default function BlogGenerator() {
  const [formData, setFormData] = useState({
    topic: '',
    keywords: '',
    tone: 'professional',
    length: 'medium',
    target_audience: '',
    custom_instructions: ''
  });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const blogRequest = {
        ...formData,
        keywords: formData.keywords.split(',').map(k => k.trim()).filter(k => k)
      };
      
      const response = await generateBlogPost(blogRequest);
      setResult(response);
    } catch (error) {
      console.error('Error generating blog:', error);
      alert('Failed to generate blog post: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-8">AI Blog Writer</h1>
      
      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label className="block text-sm font-medium mb-2">Topic</label>
          <input
            type="text"
            value={formData.topic}
            onChange={(e) => setFormData({...formData, topic: e.target.value})}
            className="w-full p-3 border rounded-lg"
            placeholder="Enter your blog topic..."
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Keywords (comma-separated)</label>
          <input
            type="text"
            value={formData.keywords}
            onChange={(e) => setFormData({...formData, keywords: e.target.value})}
            className="w-full p-3 border rounded-lg"
            placeholder="Python, FastAPI, REST API"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2">Tone</label>
            <select
              value={formData.tone}
              onChange={(e) => setFormData({...formData, tone: e.target.value})}
              className="w-full p-3 border rounded-lg"
            >
              <option value="professional">Professional</option>
              <option value="casual">Casual</option>
              <option value="instructional">Instructional</option>
              <option value="persuasive">Persuasive</option>
              <option value="entertaining">Entertaining</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Length</label>
            <select
              value={formData.length}
              onChange={(e) => setFormData({...formData, length: e.target.value})}
              className="w-full p-3 border rounded-lg"
            >
              <option value="short">Short (300-500 words)</option>
              <option value="medium">Medium (500-1000 words)</option>
              <option value="long">Long (1000-2000 words)</option>
              <option value="very_long">Very Long (2000+ words)</option>
            </select>
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? 'Generating...' : 'Generate Blog Post'}
        </button>
      </form>

      {result && (
        <div className="mt-8 p-6 bg-gray-50 rounded-lg">
          <h2 className="text-2xl font-bold mb-4">{result.blog_post.title}</h2>
          <div className="prose max-w-none">
            <div dangerouslySetInnerHTML={{ __html: result.blog_post.content }} />
          </div>
          
          <div className="mt-6 p-4 bg-white rounded border">
            <h3 className="font-semibold mb-2">SEO Meta Tags</h3>
            <p><strong>Description:</strong> {result.blog_post.meta_description}</p>
            <p><strong>Keywords:</strong> {result.blog_post.meta_keywords?.join(', ')}</p>
          </div>
        </div>
      )}
    </div>
  );
}
```

#### 5. Deploy Frontend to Vercel
```bash
# In your frontend project
npm run build
npx vercel --prod
```

### Option 2: Python Client Library

#### Create a Python Client
```python
import requests
from typing import Dict, List, Optional

class BlogWriterClient:
    def __init__(self, api_url: str):
        self.api_url = api_url.rstrip('/')
        
    def generate_blog(
        self,
        topic: str,
        keywords: Optional[List[str]] = None,
        tone: str = "professional",
        length: str = "medium",
        target_audience: Optional[str] = None,
        custom_instructions: Optional[str] = None
    ) -> Dict:
        """Generate a blog post using the BlogWriter API."""
        
        payload = {
            "topic": topic,
            "tone": tone,
            "length": length
        }
        
        if keywords:
            payload["keywords"] = keywords
        if target_audience:
            payload["target_audience"] = target_audience
        if custom_instructions:
            payload["custom_instructions"] = custom_instructions
            
        response = requests.post(
            f"{self.api_url}/api/v1/blog/generate",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        response.raise_for_status()
        return response.json()
    
    def get_config(self) -> Dict:
        """Get API configuration."""
        response = requests.get(f"{self.api_url}/api/v1/config")
        response.raise_for_status()
        return response.json()

# Usage example
client = BlogWriterClient("https://blog-writer-sdk-kq42l26tuq-uc.a.run.app")

result = client.generate_blog(
    topic="How to Build a Python REST API",
    keywords=["Python", "FastAPI", "REST API"],
    tone="instructional",
    length="medium"
)

print(f"Generated: {result['blog_post']['title']}")
```

### Option 3: Direct Integration in Existing Projects

You can integrate the BlogWriter API directly into existing applications:

#### JavaScript/Node.js
```javascript
const axios = require('axios');

const blogWriterAPI = axios.create({
  baseURL: 'https://blog-writer-sdk-kq42l26tuq-uc.a.run.app'
});

async function generateBlog(topic, keywords = []) {
  try {
    const response = await blogWriterAPI.post('/api/v1/blog/generate', {
      topic,
      keywords,
      tone: 'professional',
      length: 'medium'
    });
    
    return response.data;
  } catch (error) {
    console.error('Blog generation failed:', error.response?.data || error.message);
    throw error;
  }
}
```

#### PHP
```php
<?php
function generateBlog($topic, $keywords = []) {
    $url = 'https://blog-writer-sdk-kq42l26tuq-uc.a.run.app/api/v1/blog/generate';
    
    $data = [
        'topic' => $topic,
        'keywords' => $keywords,
        'tone' => 'professional',
        'length' => 'medium'
    ];
    
    $options = [
        'http' => [
            'header' => "Content-type: application/json\r\n",
            'method' => 'POST',
            'content' => json_encode($data)
        ]
    ];
    
    $context = stream_context_create($options);
    $result = file_get_contents($url, false, $context);
    
    return json_decode($result, true);
}
?>
```

## 🔧 **CORS Configuration**

Make sure your Google Cloud Run deployment has the correct CORS settings. Update the `ALLOWED_ORIGINS` environment variable to include your frontend domain:

```bash
ALLOWED_ORIGINS=http://localhost:3000,https://your-frontend.vercel.app,https://yourdomain.com
```

## 📚 **API Documentation**

Once deployed, you can access interactive API documentation at:
```
https://blog-writer-sdk-kq42l26tuq-uc.a.run.app/docs
```

This provides a complete interface to test all endpoints and see request/response schemas.

## 🎯 **Recommended Approach**

1. **Start with Direct API Testing** using curl or Postman
2. **Build a Simple Frontend** (Next.js recommended)
3. **Deploy Frontend to Vercel** for a complete solution
4. **Integrate into Existing Projects** as needed

Would you like me to help you set up any of these integration options?
