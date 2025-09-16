# Deployment Guide 🚀

This guide covers deploying the Blog Writer SDK to various platforms, with a focus on the recommended **Vercel + Google Cloud Run + Supabase** architecture.

## 🏗️ Architecture Overview

```
┌─────────────────┐    HTTPS API     ┌─────────────────┐    PostgreSQL    ┌─────────────────┐
│   Next.js App   │ ◄──────────────► │  Python API     │ ◄──────────────► │   Supabase DB   │
│   (Vercel)      │                  │ (Google Cloud)  │                  │   + Auth + APIs │
│   Auto SSL ✅   │                  │   Auto SSL ✅   │                  │   Auto SSL ✅   │
└─────────────────┘                  └─────────────────┘                  └─────────────────┘
```

## 📋 Prerequisites

- GitHub account
- Supabase account
- Railway account
- Vercel account (for frontend)

## 🗄️ Step 1: Set Up Supabase Database

### 1.1 Create Supabase Project

1. Go to [supabase.com](https://supabase.com)
2. Click "Start your project"
3. Create a new organization/project
4. Choose a region close to your users

### 1.2 Set Up Database Schema

1. Go to the SQL Editor in your Supabase dashboard
2. Copy the schema from `src/blog_writer_sdk/integrations/supabase_client.py`
3. Run the `create_database_schema()` SQL in the editor

```sql
-- The complete schema is available in the SupabaseClient class
-- This creates tables for blog_posts and generation_analytics
-- Plus indexes and Row Level Security policies
```

### 1.3 Get Supabase Credentials

1. Go to Settings → API
2. Copy your:
   - Project URL
   - `anon` public key
   - `service_role` secret key (for server-side operations)

## ☁️ Step 2: Deploy to Google Cloud Run

### 2.1 Setup Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing one
3. Enable Cloud Run API
4. Enable Cloud Build API

### 2.2 Configure Environment Variables

Set up environment variables in Google Cloud:

```bash
# Required
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Optional
DEBUG=false
PORT=8000
ALLOWED_ORIGINS=https://your-app.vercel.app,http://localhost:3000
```

### 2.3 Deploy

1. Use the included `cloudbuild.yaml` for automated deployment
2. Push to main branch triggers automatic deployment via GitHub Actions
3. You'll get a URL like `https://your-service-name-xxxxx-uc.a.run.app`

### 2.4 Custom Domain (Optional)

1. Go to Settings → Domains
2. Add your custom domain
3. Configure DNS as instructed
4. SSL is automatically provisioned

## 🌐 Step 3: Frontend Integration (Next.js + Vercel)

### 3.1 Create Next.js Client

```typescript
// lib/blogWriter.ts
export class BlogWriterClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  async generateBlog(params: BlogGenerationParams) {
    const response = await fetch(`${this.baseUrl}/api/v1/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params)
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return response.json();
  }

  async analyzeBlog(content: string, title?: string) {
    const response = await fetch(`${this.baseUrl}/api/v1/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content, title })
    });
    
    return response.json();
  }
}
```

### 3.2 Environment Variables for Next.js

```bash
# .env.local
NEXT_PUBLIC_SUPABASE_URL=https://your-project-id.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
PYTHON_API_URL=https://your-service-name-xxxxx-uc.a.run.app
```

### 3.3 API Route Example

```typescript
// pages/api/blog/generate.ts
import { BlogWriterClient } from '../../../lib/blogWriter';

const blogWriter = new BlogWriterClient(process.env.PYTHON_API_URL!);

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const result = await blogWriter.generateBlog(req.body);
    res.status(200).json(result);
  } catch (error) {
    console.error('Blog generation error:', error);
    res.status(500).json({ error: 'Failed to generate blog' });
  }
}
```

### 3.4 Deploy to Vercel

1. Connect your Next.js repository to Vercel
2. Add environment variables in Vercel dashboard
3. Deploy automatically on git push

## 🔧 Step 4: Configuration & Testing

### 4.1 Test the API

```bash
# Health check
curl https://your-service-name-xxxxx-uc.a.run.app/health

# Generate blog
curl -X POST https://your-service-name-xxxxx-uc.a.run.app/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Test Blog Post",
    "keywords": ["test", "blog"],
    "tone": "professional",
    "length": "medium"
  }'
```

### 4.2 Test Frontend Integration

```javascript
// Test in browser console
const response = await fetch('/api/blog/generate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    topic: 'Test Blog Post',
    keywords: ['test', 'blog'],
    tone: 'professional',
    length: 'medium'
  })
});

const result = await response.json();
console.log(result);
```

## 📊 Step 5: Monitoring & Analytics

### 5.1 Google Cloud Run Monitoring

- View logs in Google Cloud Console
- Monitor resource usage
- Set up alerts for errors

### 5.2 Supabase Analytics

- Monitor database performance
- Track API usage
- Review query performance

### 5.3 Custom Analytics

```python
# Add to your API endpoints
await supabase_client.log_generation(
    topic=request.topic,
    success=result.success,
    word_count=result.word_count,
    generation_time=result.generation_time_seconds,
    user_id=user_id,  # if you have user authentication
)
```

## 🔒 Step 6: Security & Performance

### 6.1 Environment Security

- Never commit `.env` files
- Use Google Cloud's environment variables
- Rotate API keys regularly

### 6.2 CORS Configuration

```python
# In main.py, update CORS origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-app.vercel.app",
        "https://your-custom-domain.com",
        "http://localhost:3000",  # Development only
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

### 6.3 Rate Limiting (Optional)

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/api/v1/generate")
@limiter.limit("10/minute")
async def generate_blog(request: Request, ...):
    # Your endpoint logic
```

## 🚀 Alternative Deployment Options

### Docker Compose (Local Development)

```yaml
# docker-compose.yml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_SERVICE_ROLE_KEY}
    depends_on:
      - db
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=blogwriter
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    ports:
      - "5432:5432"
```

### AWS Deployment

```bash
# Using AWS App Runner
aws apprunner create-service \
  --service-name blog-writer-sdk \
  --source-configuration '{
    "ImageRepository": {
      "ImageIdentifier": "your-ecr-repo/blog-writer-sdk:latest",
      "ImageConfiguration": {
        "Port": "8000"
      }
    }
  }'
```

### Google Cloud Run

```bash
# Build and deploy
gcloud builds submit --tag gcr.io/PROJECT-ID/blog-writer-sdk
gcloud run deploy --image gcr.io/PROJECT-ID/blog-writer-sdk --platform managed
```

## 🔍 Troubleshooting

### Common Issues

1. **CORS Errors**
   - Check `ALLOWED_ORIGINS` environment variable
   - Ensure frontend URL is included

2. **Database Connection Issues**
   - Verify Supabase credentials
   - Check network connectivity
   - Review Supabase logs

3. **Build Failures**
   - Check Dockerfile syntax
   - Verify all dependencies in `pyproject.toml`
   - Review Google Cloud build logs

4. **Performance Issues**
   - Monitor Google Cloud resource usage
   - Consider upgrading Google Cloud plan
   - Implement caching for repeated requests

### Getting Help

- Check Google Cloud logs: `gcloud logs read`
- Review Supabase logs in dashboard
- Test API endpoints with curl
- Use Google Cloud support if needed

## 📈 Scaling Considerations

### Horizontal Scaling

- Google Cloud Run automatically handles load balancing
- Consider multiple Google Cloud Run services for different regions
- Use Supabase read replicas for database scaling

### Performance Optimization

- Implement Redis caching for keyword analysis
- Use CDN for static assets
- Optimize database queries
- Consider async processing for long-running tasks

---

**🎉 Congratulations!** Your Blog Writer SDK is now deployed and ready for production use. The architecture provides excellent scalability, security, and developer experience.
