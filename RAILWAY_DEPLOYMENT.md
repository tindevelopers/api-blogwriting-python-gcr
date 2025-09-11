# 🚂 Railway Deployment Guide

## BlogWriter SDK - AI-Enhanced Blog Generation API

### 🎯 Deployment Status

✅ **Railway CLI**: Installed and authenticated  
✅ **Project Created**: "sdk Blog Writer V.1.0"  
✅ **Project URL**: https://railway.com/project/9f57aa33-7859-4f0d-9c9a-d3118c3b0f0b  
✅ **Docker Configuration**: Ready with Dockerfile and railway.json  
✅ **AI Integration**: Multi-provider support (OpenAI, Anthropic, Azure OpenAI)  

---

## 🚀 Deployment Methods

### Method 1: Railway Dashboard (Recommended)

1. **Open Railway Dashboard**
   ```bash
   railway open
   ```
   Or visit: https://railway.com/project/9f57aa33-7859-4f0d-9c9a-d3118c3b0f0b

2. **Add Service**
   - Click "New Service"
   - Choose "GitHub Repo" (recommended) or "Empty Service"
   - If GitHub: Connect repository and auto-deploy
   - If Empty: Deploy via CLI using `railway up`

3. **Configure Environment Variables**
   - Go to Service → Variables tab
   - Add variables from the list below

### Method 2: Automated Script

```bash
./deploy.sh
```

### Method 3: Manual CLI

```bash
# Set environment variables
railway variables --set "PORT=8000" --set "HOST=0.0.0.0"

# Deploy
railway up
```

---

## ⚙️ Environment Variables

### 🔧 Essential Variables (Required)

```bash
# Application
PORT=8000
HOST=0.0.0.0
DEBUG=false

# API Configuration
API_TITLE=Blog Writer SDK API
API_VERSION=0.1.0
ALLOWED_ORIGINS=https://your-frontend.vercel.app

# Content Generation
DEFAULT_TONE=professional
DEFAULT_LENGTH=medium
ENABLE_SEO_OPTIMIZATION=true
ENABLE_QUALITY_ANALYSIS=true
```

### 🤖 AI Provider Variables (Optional but Recommended)

#### OpenAI (Cost-effective, recommended)
```bash
OPENAI_API_KEY=sk-your-openai-key
OPENAI_DEFAULT_MODEL=gpt-4o-mini
OPENAI_ORGANIZATION=org-your-org-id  # Optional
```

#### Anthropic (High-quality alternative)
```bash
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
ANTHROPIC_DEFAULT_MODEL=claude-3-5-haiku-20241022
```

#### Azure OpenAI (Enterprise option)
```bash
AZURE_OPENAI_API_KEY=your-azure-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEFAULT_MODEL=gpt-4o-mini
```

### 🗄️ Database Variables (Optional)

#### Supabase
```bash
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_ANON_KEY=your-anon-key
```

### 🔍 SEO Enhancement Variables (Optional)

#### DataForSEO Integration
```bash
DATAFORSEO_API_KEY=your-dataforseo-key
DATAFORSEO_API_SECRET=your-dataforseo-secret
```

---

## 🔗 API Endpoints

Once deployed, your API will be available at: `https://your-service.railway.app`

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/docs` | Interactive API documentation |
| `GET` | `/api/v1/config` | Configuration and feature status |
| `GET` | `/api/v1/ai/health` | AI providers health check |
| `POST` | `/api/v1/blog/generate` | Generate blog content |

### Example API Usage

```bash
# Health check
curl https://your-service.railway.app/health

# Generate blog post
curl -X POST https://your-service.railway.app/api/v1/blog/generate \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "How to Build a Python REST API",
    "keywords": ["Python API", "FastAPI", "REST"],
    "tone": "instructional",
    "length": "medium",
    "enable_ai_enhancement": true
  }'
```

---

## 🎛️ Configuration Features

### AI Enhancement Levels

1. **No AI**: Traditional template-based generation
2. **AI Fallback**: AI-enhanced with traditional fallback
3. **AI Primary**: AI-first with intelligent provider switching

### Content Templates Available

- How-to Guide
- Listicle  
- Review
- Comparison
- Tutorial
- Case Study
- News Article
- Opinion Piece

### SEO Features

- Keyword analysis and optimization
- Meta tag generation
- Content structure optimization
- Readability scoring
- DataForSEO integration (optional)

---

## 🔧 Post-Deployment Setup

### 1. Verify Deployment
```bash
# Check deployment status
railway logs

# Test health endpoint
curl https://your-service.railway.app/health
```

### 2. Configure AI Providers
- Add at least one AI provider API key
- Test AI functionality via `/api/v1/ai/health`

### 3. Update CORS Settings
- Replace `your-frontend.vercel.app` with your actual frontend domain
- Add multiple domains separated by commas

### 4. Test API Endpoints
- Visit `/docs` for interactive API documentation
- Test blog generation with sample requests

---

## 🚨 Troubleshooting

### Common Issues

1. **Build Failures**
   - Check Railway build logs
   - Verify Dockerfile syntax
   - Ensure all dependencies in pyproject.toml

2. **Environment Variable Issues**
   - Verify variables are set in Railway dashboard
   - Check variable names match exactly
   - Restart service after adding variables

3. **AI Provider Errors**
   - Verify API keys are valid
   - Check provider health via `/api/v1/ai/health`
   - Review provider rate limits

4. **CORS Errors**
   - Update `ALLOWED_ORIGINS` with your frontend domain
   - Include both HTTP and HTTPS versions if needed

### Debug Commands

```bash
# View logs
railway logs

# Check service status
railway status

# Open dashboard
railway open

# Check environment variables
railway variables
```

---

## 📊 Monitoring & Analytics

### Built-in Monitoring

- Health checks at `/health`
- AI provider status at `/api/v1/ai/health`
- Configuration status at `/api/v1/config`

### Railway Monitoring

- CPU and memory usage in Railway dashboard
- Request logs and error tracking
- Deployment history and rollback options

---

## 🔄 Updates & Maintenance

### Updating the Application

1. **Via GitHub** (if connected):
   - Push changes to your repository
   - Railway auto-deploys

2. **Via CLI**:
   ```bash
   railway up
   ```

### Environment Variable Updates

```bash
# Update variables
railway variables --set "NEW_VAR=value"

# View current variables
railway variables
```

---

## 🎉 Success Checklist

- [ ] Railway project created and deployed
- [ ] Environment variables configured
- [ ] AI provider API keys added
- [ ] Health endpoints responding
- [ ] API documentation accessible at `/docs`
- [ ] CORS configured for your frontend
- [ ] Test blog generation working
- [ ] Monitoring and logs accessible

---

## 🆘 Support

- **Railway Documentation**: https://docs.railway.app/
- **API Documentation**: `https://your-service.railway.app/docs`
- **Project Dashboard**: https://railway.com/project/9f57aa33-7859-4f0d-9c9a-d3118c3b0f0b

Your AI-enhanced BlogWriter SDK is now ready to serve hundreds of clients with robust, scalable blog generation capabilities! 🚀
