# 🚂 Railway Deployment Guide for Python Blog Writer SDK

This guide will help you deploy the Python Blog Writer SDK to Railway with proper environment variable configuration.

## 📋 Prerequisites

1. **Railway CLI installed**:
   ```bash
   npm install -g @railway/cli
   # or
   curl -fsSL https://railway.app/install.sh | sh
   ```

2. **Railway account**: Sign up at [railway.app](https://railway.app)

3. **GitHub repository**: Code should be pushed to GitHub first

## 🚀 Deployment Steps

### Step 1: Login to Railway

```bash
railway login
```

### Step 2: Create or Link Project

**Option A: Create new project**
```bash
railway init
```

**Option B: Link existing project**
```bash
railway link
```

### Step 3: Connect to GitHub Repository

1. Go to Railway dashboard
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose `tindevelopers/sdk-ai-blog-writer-python`
5. Select `main` branch

### Step 4: Configure Environment Variables

**Option A: Use the interactive setup script**
```bash
chmod +x railway-setup.sh
./railway-setup.sh
```

**Option B: Use the template commands**
```bash
# Copy commands from railway-env-template.txt and run them
# Make sure to replace placeholder values with your actual credentials
```

**Option C: Manual setup via Railway CLI**
```bash
# Required variables
railway variables set SUPABASE_URL="your-supabase-url"
railway variables set SUPABASE_SERVICE_ROLE_KEY="your-service-key"
railway variables set SUPABASE_ANON_KEY="your-anon-key"
railway variables set OPENAI_API_KEY="your-openai-key"
railway variables set ALLOWED_ORIGINS="https://your-frontend.vercel.app"

# See railway-env-template.txt for complete list
```

### Step 5: Deploy

**If using GitHub integration:**
- Railway will automatically deploy when you push to main branch

**If using CLI:**
```bash
railway up
```

### Step 6: Verify Deployment

```bash
# Check deployment status
railway status

# Get your app URL
railway domain

# View logs
railway logs

# Test the health endpoint
curl https://your-app.railway.app/health
```

## 🔧 Environment Variables Reference

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SUPABASE_URL` | Supabase project URL | `https://abc123.supabase.co` |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key | `eyJ...` |
| `SUPABASE_ANON_KEY` | Supabase anonymous key | `eyJ...` |
| `OPENAI_API_KEY` | OpenAI API key | `sk-...` |
| `ALLOWED_ORIGINS` | CORS allowed origins | `https://app.vercel.app` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Anthropic API key | - |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI key | - |
| `DATAFORSEO_API_KEY` | DataForSEO API key | - |
| `DEBUG` | Debug mode | `false` |
| `LOG_LEVEL` | Logging level | `info` |

## 🔍 Troubleshooting

### Common Issues

1. **Build fails**: Check that all required dependencies are in `pyproject.toml`
2. **App crashes**: Check logs with `railway logs`
3. **CORS errors**: Verify `ALLOWED_ORIGINS` includes your frontend URL
4. **Database errors**: Verify Supabase credentials and database schema

### Useful Commands

```bash
# View all environment variables
railway variables

# Update a variable
railway variables set VARIABLE_NAME=new_value

# Delete a variable
railway variables delete VARIABLE_NAME

# View service logs
railway logs --follow

# Connect to service shell
railway shell

# View service metrics
railway status
```

## 🔗 Integration with Frontend

Once deployed, update your frontend environment variables:

```bash
# In your Next.js project
echo 'NEXT_PUBLIC_PYTHON_SDK_URL="https://your-app.railway.app"' >> .env.local
```

## 📊 Monitoring

Railway provides built-in monitoring:

1. **Metrics**: CPU, Memory, Network usage
2. **Logs**: Application and system logs
3. **Deployments**: Deployment history and rollbacks
4. **Domains**: Custom domain configuration

## 🔄 Continuous Deployment

Railway automatically deploys when you push to the connected branch:

1. Push code to GitHub
2. Railway detects changes
3. Builds and deploys automatically
4. Health checks verify deployment

## 🎉 Success!

Your Python Blog Writer SDK should now be running on Railway! 

Test the deployment:
```bash
curl https://your-app.railway.app/health
curl https://your-app.railway.app/api/v1/config
```

Next steps:
1. Update your frontend to use the Railway URL
2. Test the integration end-to-end
3. Set up monitoring and alerts
4. Configure custom domain (optional)
