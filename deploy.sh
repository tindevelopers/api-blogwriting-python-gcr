#!/bin/bash

# Railway Deployment Script for BlogWriter SDK
echo "🚂 Deploying BlogWriter SDK to Railway..."

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Please install it first."
    exit 1
fi

# Check if logged in
if ! railway whoami &> /dev/null; then
    echo "❌ Not logged in to Railway. Please run 'railway login' first."
    exit 1
fi

echo "✅ Railway CLI ready"

# Set essential environment variables
echo "🔧 Setting environment variables..."

# Basic configuration
railway variables --set "PORT=8000" --set "HOST=0.0.0.0" --set "DEBUG=false"

# API configuration
railway variables --set "API_TITLE=Blog Writer SDK API" --set "API_VERSION=0.1.0"

# Content settings
railway variables --set "DEFAULT_TONE=professional" --set "DEFAULT_LENGTH=medium"
railway variables --set "ENABLE_SEO_OPTIMIZATION=true" --set "ENABLE_QUALITY_ANALYSIS=true"

# CORS settings (update with your frontend domain)
railway variables --set "ALLOWED_ORIGINS=http://localhost:3000,https://your-app.vercel.app"

echo "✅ Environment variables set"

# Deploy the application
echo "🚀 Deploying application..."
railway up --detach

echo "✅ Deployment initiated!"
echo "📊 Check deployment status: railway logs"
echo "🌐 Open dashboard: railway open"
echo "🔗 Your project: https://railway.com/project/9f57aa33-7859-4f0d-9c9a-d3118c3b0f0b"

echo ""
echo "🎉 Deployment Complete!"
echo ""
echo "Next steps:"
echo "1. Add AI provider API keys in Railway dashboard (Variables tab)"
echo "2. Add Supabase credentials if needed"
echo "3. Update ALLOWED_ORIGINS with your frontend domain"
echo "4. Test your API endpoints"
echo ""
echo "API Endpoints available:"
echo "- GET  /health - Health check"
echo "- GET  /api/v1/config - Configuration status"
echo "- GET  /api/v1/ai/health - AI providers health"
echo "- POST /api/v1/blog/generate - Generate blog content"
echo "- GET  /docs - API documentation"
