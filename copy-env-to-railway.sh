#!/bin/bash

# Copy Environment Variables from Vercel/Local to Railway
# This script helps transfer Supabase and other environment variables to Railway

set -e

echo "🔄 Copying Environment Variables to Railway"
echo "=========================================="

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
    exit 1
fi

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo -e "${YELLOW}⚠️  Vercel CLI not found. Will skip Vercel env extraction.${NC}"
    echo "Install with: npm install -g vercel"
    VERCEL_AVAILABLE=false
else
    VERCEL_AVAILABLE=true
fi

# Function to set Railway environment variable
set_railway_var() {
    local key=$1
    local value=$2
    
    if [ -n "$value" ] && [ "$value" != "undefined" ] && [ "$value" != "null" ]; then
        echo -e "${BLUE}Setting $key in Railway...${NC}"
        railway variables set "$key=$value"
        echo -e "${GREEN}✅ $key set successfully${NC}"
    else
        echo -e "${YELLOW}⚠️  Skipping $key (empty or undefined value)${NC}"
    fi
}

# Function to extract environment variable from local file
extract_local_env() {
    local env_file=$1
    local var_name=$2
    
    if [ -f "$env_file" ]; then
        grep "^$var_name=" "$env_file" 2>/dev/null | cut -d'=' -f2- | tr -d '"' | tr -d "'"
    fi
}

echo -e "${BLUE}🔍 Looking for environment variables...${NC}"

# Define the frontend path
FRONTEND_PATH="/Users/foo/Library/CloudStorage/Dropbox/~ Cursor Projects/AI BLOG WRITER SDK/AI BLOG WRITER CHAT LLM/tin-ai-agents"

# Check for local environment files
LOCAL_ENV_FILES=(
    "$FRONTEND_PATH/.env.local"
    "$FRONTEND_PATH/.env"
    "$FRONTEND_PATH/.env.production"
    ".env.local"
    ".env"
)

echo "Checking local environment files..."
for env_file in "${LOCAL_ENV_FILES[@]}"; do
    if [ -f "$env_file" ]; then
        echo -e "${GREEN}✅ Found: $env_file${NC}"
        
        # Extract Supabase variables
        SUPABASE_URL=$(extract_local_env "$env_file" "SUPABASE_URL")
        SUPABASE_ANON_KEY=$(extract_local_env "$env_file" "SUPABASE_ANON_KEY")
        SUPABASE_SERVICE_ROLE_KEY=$(extract_local_env "$env_file" "SUPABASE_SERVICE_ROLE_KEY")
        
        # Extract other common variables
        OPENAI_API_KEY=$(extract_local_env "$env_file" "OPENAI_API_KEY")
        ANTHROPIC_API_KEY=$(extract_local_env "$env_file" "ANTHROPIC_API_KEY")
        NEXTAUTH_SECRET=$(extract_local_env "$env_file" "NEXTAUTH_SECRET")
        NEXTAUTH_URL=$(extract_local_env "$env_file" "NEXTAUTH_URL")
        
        # Break after finding the first file with variables
        if [ -n "$SUPABASE_URL" ] || [ -n "$OPENAI_API_KEY" ]; then
            echo -e "${GREEN}✅ Found environment variables in $env_file${NC}"
            break
        fi
    fi
done

# Try to get variables from Vercel if available
if [ "$VERCEL_AVAILABLE" = true ]; then
    echo -e "${BLUE}🔍 Checking Vercel environment variables...${NC}"
    
    # Change to frontend directory for Vercel commands
    cd "$FRONTEND_PATH" 2>/dev/null || echo "Could not change to frontend directory"
    
    # Try to pull Vercel env vars (this requires the project to be linked)
    if vercel env ls > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Vercel project linked, extracting environment variables...${NC}"
        
        # Extract Vercel environment variables
        VERCEL_SUPABASE_URL=$(vercel env ls | grep "SUPABASE_URL" | awk '{print $3}' | head -1)
        VERCEL_SUPABASE_ANON_KEY=$(vercel env ls | grep "SUPABASE_ANON_KEY" | awk '{print $3}' | head -1)
        VERCEL_OPENAI_API_KEY=$(vercel env ls | grep "OPENAI_API_KEY" | awk '{print $3}' | head -1)
        
        # Use Vercel values if local ones are empty
        SUPABASE_URL=${SUPABASE_URL:-$VERCEL_SUPABASE_URL}
        SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY:-$VERCEL_SUPABASE_ANON_KEY}
        OPENAI_API_KEY=${OPENAI_API_KEY:-$VERCEL_OPENAI_API_KEY}
    else
        echo -e "${YELLOW}⚠️  Vercel project not linked or no access to env vars${NC}"
    fi
    
    # Return to original directory
    cd - > /dev/null
fi

echo ""
echo -e "${BLUE}🚂 Setting up Railway environment variables...${NC}"

# Set Supabase variables
if [ -n "$SUPABASE_URL" ]; then
    set_railway_var "SUPABASE_URL" "$SUPABASE_URL"
else
    echo -e "${RED}❌ SUPABASE_URL not found. Please set manually:${NC}"
    echo "railway variables set SUPABASE_URL=\"your-supabase-url\""
fi

if [ -n "$SUPABASE_ANON_KEY" ]; then
    set_railway_var "SUPABASE_ANON_KEY" "$SUPABASE_ANON_KEY"
else
    echo -e "${RED}❌ SUPABASE_ANON_KEY not found. Please set manually:${NC}"
    echo "railway variables set SUPABASE_ANON_KEY=\"your-supabase-anon-key\""
fi

if [ -n "$SUPABASE_SERVICE_ROLE_KEY" ]; then
    set_railway_var "SUPABASE_SERVICE_ROLE_KEY" "$SUPABASE_SERVICE_ROLE_KEY"
else
    echo -e "${YELLOW}⚠️  SUPABASE_SERVICE_ROLE_KEY not found locally.${NC}"
    echo "This is usually not stored in frontend env files for security."
    echo "Please get it from your Supabase dashboard and set manually:"
    echo "railway variables set SUPABASE_SERVICE_ROLE_KEY=\"your-service-role-key\""
fi

# Set AI provider keys
if [ -n "$OPENAI_API_KEY" ]; then
    set_railway_var "OPENAI_API_KEY" "$OPENAI_API_KEY"
else
    echo -e "${YELLOW}⚠️  OPENAI_API_KEY not found. Set manually if needed:${NC}"
    echo "railway variables set OPENAI_API_KEY=\"your-openai-key\""
fi

if [ -n "$ANTHROPIC_API_KEY" ]; then
    set_railway_var "ANTHROPIC_API_KEY" "$ANTHROPIC_API_KEY"
fi

# Set core application variables
echo -e "${BLUE}Setting core application variables...${NC}"
set_railway_var "DEBUG" "false"
set_railway_var "HOST" "0.0.0.0"
set_railway_var "PORT" "8000"
set_railway_var "API_TITLE" "Blog Writer SDK API"
set_railway_var "API_VERSION" "1.0.0"

# Set CORS origins (include the frontend URL)
if [ -n "$NEXTAUTH_URL" ]; then
    FRONTEND_URL="$NEXTAUTH_URL"
elif [ -n "$VERCEL_URL" ]; then
    FRONTEND_URL="https://$VERCEL_URL"
else
    # Try to detect from Vercel
    if [ "$VERCEL_AVAILABLE" = true ]; then
        cd "$FRONTEND_PATH" 2>/dev/null
        VERCEL_PROJECT_URL=$(vercel ls 2>/dev/null | grep "https://" | head -1 | awk '{print $2}')
        FRONTEND_URL="$VERCEL_PROJECT_URL"
        cd - > /dev/null
    fi
fi

if [ -n "$FRONTEND_URL" ]; then
    ALLOWED_ORIGINS="http://localhost:3000,https://localhost:3000,$FRONTEND_URL"
    set_railway_var "ALLOWED_ORIGINS" "$ALLOWED_ORIGINS"
    echo -e "${GREEN}✅ Set CORS origins including: $FRONTEND_URL${NC}"
else
    set_railway_var "ALLOWED_ORIGINS" "http://localhost:3000,https://localhost:3000"
    echo -e "${YELLOW}⚠️  Frontend URL not detected. Update ALLOWED_ORIGINS manually:${NC}"
    echo "railway variables set ALLOWED_ORIGINS=\"http://localhost:3000,https://your-frontend.vercel.app\""
fi

# Set default content generation settings
set_railway_var "DEFAULT_TONE" "professional"
set_railway_var "DEFAULT_LENGTH" "medium"
set_railway_var "ENABLE_SEO_OPTIMIZATION" "true"
set_railway_var "ENABLE_QUALITY_ANALYSIS" "true"

# Set performance settings
set_railway_var "BATCH_MAX_CONCURRENT" "5"
set_railway_var "RATE_LIMIT_REQUESTS_PER_MINUTE" "60"
set_railway_var "LOG_LEVEL" "info"

echo ""
echo -e "${GREEN}✅ Environment variable transfer complete!${NC}"
echo ""
echo "📋 To verify all variables were set:"
echo "railway variables"
echo ""
echo "🚀 To deploy your application:"
echo "railway up"
echo ""
echo "🔗 To get your app URL:"
echo "railway domain"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. Verify the variables: railway variables"
echo "2. Deploy the app: railway up"
echo "3. Test the health endpoint: curl https://your-app.railway.app/health"
echo "4. Update your frontend with the Railway URL"
