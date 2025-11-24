#!/bin/bash
# Test script to verify access to all environment secrets
# This tests read access without modifying secrets

set -e

PROJECT_ID="api-ai-blog-writer"

echo "🔍 Testing Google Secret Manager Access"
echo "Project: $PROJECT_ID"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test function
test_secret() {
    local SECRET_NAME=$1
    local ENV_NAME=$2
    
    echo "Testing $ENV_NAME environment..."
    echo "Secret: $SECRET_NAME"
    
    # Check if secret exists
    if gcloud secrets describe "$SECRET_NAME" --project="$PROJECT_ID" &>/dev/null; then
        echo -e "${GREEN}✅ Secret exists${NC}"
        
        # Try to access latest version
        if gcloud secrets versions access latest --secret="$SECRET_NAME" --project="$PROJECT_ID" &>/dev/null; then
            echo -e "${GREEN}✅ Can read secret content${NC}"
            
            # Check if it's JSON format
            SECRET_CONTENT=$(gcloud secrets versions access latest --secret="$SECRET_NAME" --project="$PROJECT_ID" 2>/dev/null)
            if echo "$SECRET_CONTENT" | jq . >/dev/null 2>&1; then
                echo -e "${GREEN}✅ Secret is in JSON format${NC}"
                
                # Check for DataForSEO credentials
                API_KEY=$(echo "$SECRET_CONTENT" | jq -r '.DATAFORSEO_API_KEY // empty')
                API_SECRET=$(echo "$SECRET_CONTENT" | jq -r '.DATAFORSEO_API_SECRET // empty')
                
                if [ -n "$API_KEY" ] && [ "$API_KEY" != "null" ] && [ "$API_KEY" != "" ]; then
                    echo -e "${GREEN}✅ DATAFORSEO_API_KEY is set (${#API_KEY} chars)${NC}"
                else
                    echo -e "${YELLOW}⚠️  DATAFORSEO_API_KEY is not set${NC}"
                fi
                
                if [ -n "$API_SECRET" ] && [ "$API_SECRET" != "null" ] && [ "$API_SECRET" != "" ]; then
                    echo -e "${GREEN}✅ DATAFORSEO_API_SECRET is set (${#API_SECRET} chars)${NC}"
                else
                    echo -e "${YELLOW}⚠️  DATAFORSEO_API_SECRET is not set${NC}"
                fi
            else
                echo -e "${YELLOW}⚠️  Secret is not in JSON format (plain text)${NC}"
            fi
        else
            echo -e "${RED}❌ Cannot read secret content (permission denied)${NC}"
        fi
    else
        echo -e "${RED}❌ Secret does not exist${NC}"
    fi
    
    echo ""
}

# Test all environments
test_secret "blog-writer-env-dev" "DEV"
test_secret "blog-writer-env-staging" "STAGING"
test_secret "blog-writer-env-prod" "PRODUCTION"

echo "✅ Access test complete"
echo ""
echo "Next steps:"
echo "1. If secrets don't exist, create them first"
echo "2. If credentials are missing, run: ./scripts/add-dataforseo-secrets.sh"
echo "3. If permission denied, grant access to service account"

