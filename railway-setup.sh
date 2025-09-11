#!/bin/bash

# Railway Environment Variables Setup Script
# Configures all required environment variables for the Python Blog Writer SDK

set -e

echo "🚂 Setting up Railway Environment Variables for Python Blog Writer SDK"
echo "====================================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo -e "${RED}❌ Railway CLI not found. Please install it first:${NC}"
    echo "npm install -g @railway/cli"
    echo "or"
    echo "curl -fsSL https://railway.app/install.sh | sh"
    exit 1
fi

# Check if logged in to Railway
if ! railway whoami &> /dev/null; then
    echo -e "${YELLOW}⚠️  Not logged in to Railway. Please login first:${NC}"
    echo "railway login"
    exit 1
fi

echo -e "${GREEN}✅ Railway CLI is ready${NC}"
echo ""

# Function to set environment variable
set_env_var() {
    local key=$1
    local value=$2
    local description=$3
    
    if [ -n "$value" ] && [ "$value" != "your_value_here" ] && [ "$value" != "your-value-here" ]; then
        echo -e "${BLUE}Setting $key...${NC}"
        railway variables set "$key=$value"
        echo -e "${GREEN}✅ $key set${NC}"
    else
        echo -e "${YELLOW}⚠️  Skipping $key (no value provided)${NC}"
        echo "   Description: $description"
    fi
}

echo "🔧 Core Application Settings"
echo "============================"

# Core application settings
set_env_var "DEBUG" "false" "Enable debug mode"
set_env_var "HOST" "0.0.0.0" "Application host"
set_env_var "PORT" "8000" "Application port"
set_env_var "API_TITLE" "Blog Writer SDK API" "API title"
set_env_var "API_VERSION" "1.0.0" "API version"
set_env_var "API_DESCRIPTION" "A powerful REST API for AI-driven blog writing with advanced SEO optimization" "API description"

echo ""
echo "🔑 AI Provider Configuration"
echo "============================"

# Prompt for AI provider keys
echo -e "${BLUE}Please provide your AI provider API keys:${NC}"

read -p "OpenAI API Key (optional): " OPENAI_API_KEY
set_env_var "OPENAI_API_KEY" "$OPENAI_API_KEY" "OpenAI API key for GPT models"

read -p "OpenAI Organization ID (optional): " OPENAI_ORGANIZATION
set_env_var "OPENAI_ORGANIZATION" "$OPENAI_ORGANIZATION" "OpenAI organization ID"

set_env_var "OPENAI_DEFAULT_MODEL" "gpt-4o-mini" "Default OpenAI model"

read -p "Anthropic API Key (optional): " ANTHROPIC_API_KEY
set_env_var "ANTHROPIC_API_KEY" "$ANTHROPIC_API_KEY" "Anthropic API key for Claude models"

set_env_var "ANTHROPIC_DEFAULT_MODEL" "claude-3-5-haiku-20241022" "Default Anthropic model"

read -p "Azure OpenAI API Key (optional): " AZURE_OPENAI_API_KEY
set_env_var "AZURE_OPENAI_API_KEY" "$AZURE_OPENAI_API_KEY" "Azure OpenAI API key"

read -p "Azure OpenAI Endpoint (optional): " AZURE_OPENAI_ENDPOINT
set_env_var "AZURE_OPENAI_ENDPOINT" "$AZURE_OPENAI_ENDPOINT" "Azure OpenAI endpoint URL"

set_env_var "AZURE_OPENAI_API_VERSION" "2024-02-15-preview" "Azure OpenAI API version"
set_env_var "AZURE_OPENAI_DEFAULT_MODEL" "gpt-4o-mini" "Default Azure OpenAI model"

echo ""
echo "🗄️  Database Configuration (Supabase)"
echo "===================================="

read -p "Supabase URL: " SUPABASE_URL
set_env_var "SUPABASE_URL" "$SUPABASE_URL" "Supabase project URL"

read -p "Supabase Service Role Key: " SUPABASE_SERVICE_ROLE_KEY
set_env_var "SUPABASE_SERVICE_ROLE_KEY" "$SUPABASE_SERVICE_ROLE_KEY" "Supabase service role key (admin access)"

read -p "Supabase Anon Key: " SUPABASE_ANON_KEY
set_env_var "SUPABASE_ANON_KEY" "$SUPABASE_ANON_KEY" "Supabase anonymous key"

echo ""
echo "🔍 SEO & Analytics Configuration (Optional)"
echo "=========================================="

read -p "DataForSEO API Key (optional): " DATAFORSEO_API_KEY
set_env_var "DATAFORSEO_API_KEY" "$DATAFORSEO_API_KEY" "DataForSEO API key for SEO analysis"

read -p "DataForSEO API Secret (optional): " DATAFORSEO_API_SECRET
set_env_var "DATAFORSEO_API_SECRET" "$DATAFORSEO_API_SECRET" "DataForSEO API secret"

echo ""
echo "🌐 CORS & Security Configuration"
echo "==============================="

# Get the frontend URL from user
read -p "Frontend URL (e.g., https://your-app.vercel.app): " FRONTEND_URL
if [ -n "$FRONTEND_URL" ]; then
    ALLOWED_ORIGINS="http://localhost:3000,https://localhost:3000,$FRONTEND_URL"
else
    ALLOWED_ORIGINS="http://localhost:3000,https://localhost:3000"
fi

set_env_var "ALLOWED_ORIGINS" "$ALLOWED_ORIGINS" "Allowed CORS origins"

echo ""
echo "⚡ Performance & Rate Limiting"
echo "============================="

set_env_var "BATCH_MAX_CONCURRENT" "5" "Maximum concurrent batch operations"
set_env_var "BATCH_MAX_RETRIES" "2" "Maximum retry attempts for failed operations"
set_env_var "RATE_LIMIT_REQUESTS_PER_MINUTE" "60" "Rate limit: requests per minute"
set_env_var "RATE_LIMIT_REQUESTS_PER_HOUR" "1000" "Rate limit: requests per hour"
set_env_var "RATE_LIMIT_REQUESTS_PER_DAY" "10000" "Rate limit: requests per day"

echo ""
echo "📊 Content Generation Settings"
echo "============================="

set_env_var "DEFAULT_TONE" "professional" "Default content tone"
set_env_var "DEFAULT_LENGTH" "medium" "Default content length"
set_env_var "ENABLE_SEO_OPTIMIZATION" "true" "Enable SEO optimization features"
set_env_var "ENABLE_QUALITY_ANALYSIS" "true" "Enable content quality analysis"

echo ""
echo "📝 Logging & Monitoring"
echo "======================"

set_env_var "LOG_LEVEL" "info" "Logging level"
set_env_var "LOG_FORMAT" "json" "Log format"
set_env_var "METRICS_RETENTION_HOURS" "24" "Metrics retention period"

echo ""
echo -e "${GREEN}✅ Environment variables setup complete!${NC}"
echo ""
echo "🚀 Next steps:"
echo "1. Deploy your application: railway up"
echo "2. Check deployment status: railway status"
echo "3. Get your app URL: railway domain"
echo "4. View logs: railway logs"
echo ""
echo "📋 To view all environment variables:"
echo "railway variables"
echo ""
echo "🔧 To update a variable later:"
echo "railway variables set VARIABLE_NAME=new_value"
echo ""
echo -e "${BLUE}🎉 Your Python Blog Writer SDK is ready for Railway deployment!${NC}"
