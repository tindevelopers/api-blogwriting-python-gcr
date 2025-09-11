#!/bin/bash

# Quick Vercel to Railway Environment Variable Transfer
# Specifically for Supabase and AI provider keys

# set -e  # Commented out to continue even if some variables fail

echo "🔄 Transferring Vercel Environment Variables to Railway"
echo "====================================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Check CLI tools
if ! command -v railway &> /dev/null; then
    echo -e "${RED}❌ Railway CLI not found. Install with: npm install -g @railway/cli${NC}"
    exit 1
fi

if ! command -v vercel &> /dev/null; then
    echo -e "${RED}❌ Vercel CLI not found. Install with: npm install -g vercel${NC}"
    exit 1
fi

# Navigate to frontend directory
FRONTEND_DIR="/Users/foo/Library/CloudStorage/Dropbox/~ Cursor Projects/AI BLOG WRITER SDK/AI BLOG WRITER CHAT LLM/tin-ai-agents"

if [ -d "$FRONTEND_DIR" ]; then
    cd "$FRONTEND_DIR"
    echo -e "${GREEN}✅ Changed to frontend directory${NC}"
else
    echo -e "${RED}❌ Frontend directory not found: $FRONTEND_DIR${NC}"
    exit 1
fi

# Function to get Vercel environment variable
get_vercel_env() {
    local var_name=$1
    local env_type=${2:-"production"}  # production, preview, or development
    
    # Try to get the variable value from Vercel
    vercel env pull .env.vercel 2>/dev/null || true
    
    if [ -f ".env.vercel" ]; then
        grep "^$var_name=" .env.vercel 2>/dev/null | cut -d'=' -f2- | tr -d '"' | tr -d "'"
    fi
}

# Function to set Railway variable
set_railway_env() {
    local key=$1
    local value=$2
    
    if [ -n "$value" ] && [ "$value" != "undefined" ]; then
        echo -e "${BLUE}Setting $key in Railway...${NC}"
        # Change back to Python SDK directory to maintain Railway link
        cd "/Users/foo/Library/CloudStorage/Dropbox/~ Cursor Projects/AI BLOG WRITER SDK/sdk-ai-blog-writer-python"
        railway variables --set "$key=$value"
        # Return to frontend directory
        cd "$FRONTEND_DIR"
        echo -e "${GREEN}✅ $key set${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️  $key not found or empty${NC}"
        return 1
    fi
}

echo -e "${BLUE}📥 Pulling environment variables from Vercel...${NC}"

# Pull environment variables from Vercel
vercel env pull .env.vercel

if [ ! -f ".env.vercel" ]; then
    echo -e "${RED}❌ Could not pull environment variables from Vercel${NC}"
    echo "Make sure you're logged in: vercel login"
    echo "And linked to the project: vercel link"
    exit 1
fi

echo -e "${GREEN}✅ Environment variables pulled from Vercel${NC}"

# Extract key variables
SUPABASE_URL=$(get_vercel_env "SUPABASE_URL")
SUPABASE_ANON_KEY=$(get_vercel_env "SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY=$(get_vercel_env "SUPABASE_SERVICE_ROLE_KEY")

# AI Provider Keys
OPENAI_API_KEY=$(get_vercel_env "OPENAI_API_KEY")
OPENAI_ORGANIZATION=$(get_vercel_env "OPENAI_ORGANIZATION")
ANTHROPIC_API_KEY=$(get_vercel_env "ANTHROPIC_API_KEY")

# DataForSEO Keys
DATAFORSEO_API_KEY=$(get_vercel_env "DATAFORSEO_API_KEY")
DATAFORSEO_API_SECRET=$(get_vercel_env "DATAFORSEO_API_SECRET")

# Azure OpenAI (if used)
AZURE_OPENAI_API_KEY=$(get_vercel_env "AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT=$(get_vercel_env "AZURE_OPENAI_ENDPOINT")

# Other keys
NEXTAUTH_SECRET=$(get_vercel_env "NEXTAUTH_SECRET")
NEXTAUTH_URL=$(get_vercel_env "NEXTAUTH_URL")
STABILITY_API_KEY=$(get_vercel_env "STABILITY_API_KEY")
CLOUDINARY_CLOUD_NAME=$(get_vercel_env "CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY=$(get_vercel_env "CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET=$(get_vercel_env "CLOUDINARY_API_SECRET")

echo ""
echo -e "${BLUE}🚂 Setting variables in Railway...${NC}"

# Set Supabase variables (required)
set_railway_env "SUPABASE_URL" "$SUPABASE_URL"
set_railway_env "SUPABASE_ANON_KEY" "$SUPABASE_ANON_KEY"
set_railway_env "SUPABASE_SERVICE_ROLE_KEY" "$SUPABASE_SERVICE_ROLE_KEY"

# Set OpenAI keys
set_railway_env "OPENAI_API_KEY" "$OPENAI_API_KEY"
set_railway_env "OPENAI_ORGANIZATION" "$OPENAI_ORGANIZATION"

# Set Anthropic keys
set_railway_env "ANTHROPIC_API_KEY" "$ANTHROPIC_API_KEY"

# Set DataForSEO keys
set_railway_env "DATAFORSEO_API_KEY" "$DATAFORSEO_API_KEY"
set_railway_env "DATAFORSEO_API_SECRET" "$DATAFORSEO_API_SECRET"

# Set Azure OpenAI keys (if available)
set_railway_env "AZURE_OPENAI_API_KEY" "$AZURE_OPENAI_API_KEY"
set_railway_env "AZURE_OPENAI_ENDPOINT" "$AZURE_OPENAI_ENDPOINT"

# Set other service keys
set_railway_env "STABILITY_API_KEY" "$STABILITY_API_KEY"
set_railway_env "CLOUDINARY_CLOUD_NAME" "$CLOUDINARY_CLOUD_NAME"
set_railway_env "CLOUDINARY_API_KEY" "$CLOUDINARY_API_KEY"
set_railway_env "CLOUDINARY_API_SECRET" "$CLOUDINARY_API_SECRET"

# Set CORS origins based on NEXTAUTH_URL
if [ -n "$NEXTAUTH_URL" ]; then
    ALLOWED_ORIGINS="http://localhost:3000,https://localhost:3000,$NEXTAUTH_URL"
    set_railway_env "ALLOWED_ORIGINS" "$ALLOWED_ORIGINS"
    echo -e "${GREEN}✅ CORS configured for: $NEXTAUTH_URL${NC}"
fi

# Set core application variables
echo -e "${BLUE}Setting core application variables...${NC}"
cd "/Users/foo/Library/CloudStorage/Dropbox/~ Cursor Projects/AI BLOG WRITER SDK/sdk-ai-blog-writer-python"
railway variables --set DEBUG=false
railway variables --set HOST=0.0.0.0
railway variables --set PORT=8000
railway variables --set API_TITLE="Blog Writer SDK API"
railway variables --set API_VERSION="1.0.0"
railway variables --set API_DESCRIPTION="A powerful REST API for AI-driven blog writing with advanced SEO optimization"

# Set AI model defaults
railway variables --set OPENAI_DEFAULT_MODEL="gpt-4o-mini"
railway variables --set ANTHROPIC_DEFAULT_MODEL="claude-3-5-haiku-20241022"
railway variables --set AZURE_OPENAI_API_VERSION="2024-02-15-preview"
railway variables --set AZURE_OPENAI_DEFAULT_MODEL="gpt-4o-mini"

# Set content generation settings
railway variables --set DEFAULT_TONE="professional"
railway variables --set DEFAULT_LENGTH="medium"
railway variables --set ENABLE_SEO_OPTIMIZATION="true"
railway variables --set ENABLE_QUALITY_ANALYSIS="true"

# Set performance and rate limiting
railway variables --set BATCH_MAX_CONCURRENT="5"
railway variables --set BATCH_MAX_RETRIES="2"
railway variables --set RATE_LIMIT_REQUESTS_PER_MINUTE="60"
railway variables --set RATE_LIMIT_REQUESTS_PER_HOUR="1000"
railway variables --set RATE_LIMIT_REQUESTS_PER_DAY="10000"

# Set logging and monitoring
railway variables --set LOG_LEVEL="info"
railway variables --set LOG_FORMAT="json"
railway variables --set METRICS_RETENTION_HOURS="24"
cd "$FRONTEND_DIR"

# Clean up
rm -f .env.vercel

echo ""
echo -e "${GREEN}🎉 Environment variable transfer complete!${NC}"
echo ""
echo -e "${BLUE}📋 Variables transferred from Vercel to Railway:${NC}"
echo "✅ Supabase: URL, Anon Key, Service Role Key (if available)"
echo "✅ OpenAI: API Key, Organization ID, Default Model"
echo "✅ Anthropic: API Key, Default Model"
echo "✅ DataForSEO: API Key, API Secret"
echo "✅ Azure OpenAI: API Key, Endpoint (if available)"
echo "✅ Stability AI: API Key (if available)"
echo "✅ Cloudinary: Cloud Name, API Key, API Secret (if available)"
echo "✅ CORS: Configured with your frontend URL"
echo "✅ Performance: Rate limiting and batch processing settings"
echo ""
echo "📋 Verify all variables were set:"
echo "railway variables"
echo ""
echo "🚀 Deploy your application:"
echo "railway up"
echo ""
echo "🔗 Get your Railway app URL:"
echo "railway domain"
echo ""
echo "🧪 Test your deployment:"
echo "curl https://your-app.railway.app/health"
echo "curl https://your-app.railway.app/api/v1/config"
echo ""
echo -e "${YELLOW}💡 Pro tip:${NC} If any key wasn't found in Vercel, you can set it manually:"
echo "railway variables --set KEY_NAME=\"your-key-value\""
