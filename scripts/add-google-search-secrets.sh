#!/bin/bash
# Script to add Google Search API credentials to Google Secret Manager
# Usage: ./scripts/add-google-search-secrets.sh

set -e

PROJECT_ID="api-ai-blog-writer"
SECRET_NAME="blog-writer-env-dev"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "🔍 Google Search API Credentials Setup"
echo "======================================"
echo ""

# Check if gcloud is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &>/dev/null; then
    echo -e "${RED}❌ Not authenticated to Google Cloud. Please run: gcloud auth login${NC}"
    exit 1
fi

# Check if secret exists
if ! gcloud secrets describe "$SECRET_NAME" --project="$PROJECT_ID" &>/dev/null; then
    echo -e "${RED}❌ Secret $SECRET_NAME does not exist.${NC}"
    echo "Please create it first or check the secret name."
    exit 1
fi

echo -e "${GREEN}✅ Secret $SECRET_NAME found${NC}"
echo ""

# Function to add or update a secret value
add_secret_value() {
    local KEY=$1
    local VALUE=$2
    local DESCRIPTION=$3
    
    echo "📝 Adding $KEY..."
    
    CURRENT_CONTENT=$(gcloud secrets versions access latest --secret="$SECRET_NAME" --project="$PROJECT_ID" 2>/dev/null)
    
    if echo "$CURRENT_CONTENT" | jq . >/dev/null 2>&1; then
        # JSON format
        UPDATED_CONTENT=$(echo "$CURRENT_CONTENT" | jq --arg key "$KEY" --arg value "$VALUE" '. + {($key): $value}')
        echo "$UPDATED_CONTENT" | gcloud secrets versions add "$SECRET_NAME" \
            --data-file=- \
            --project="$PROJECT_ID" \
            --quiet
        echo -e "${GREEN}✅ Updated $KEY in $SECRET_NAME (JSON format)${NC}"
    else
        # Plain text format (env file)
        # Remove existing line if present
        UPDATED_CONTENT=$(echo "$CURRENT_CONTENT" | grep -v "^${KEY}=" || echo "$CURRENT_CONTENT")
        # Add new line
        UPDATED_CONTENT="${UPDATED_CONTENT}
${KEY}=${VALUE}"
        echo "$UPDATED_CONTENT" | gcloud secrets versions add "$SECRET_NAME" \
            --data-file=- \
            --project="$PROJECT_ID" \
            --quiet
        echo -e "${GREEN}✅ Updated $KEY in $SECRET_NAME (plain text format)${NC}"
    fi
}

# Get Google Custom Search API Key
echo "=== Google Custom Search API ==="
echo "Get your API key from: https://console.cloud.google.com/apis/credentials"
echo "Enable 'Custom Search API' in: https://console.cloud.google.com/apis/library/customsearch.googleapis.com"
echo ""
read -p "Enter GOOGLE_CUSTOM_SEARCH_API_KEY (or press Enter to skip): " CUSTOM_SEARCH_KEY

if [ ! -z "$CUSTOM_SEARCH_KEY" ]; then
    add_secret_value "GOOGLE_CUSTOM_SEARCH_API_KEY" "$CUSTOM_SEARCH_KEY" "Google Custom Search API Key"
fi

# Get Google Custom Search Engine ID
echo ""
echo "Create a Custom Search Engine at: https://programmablesearchengine.google.com/"
echo "After creating, copy the 'Search engine ID' (CX)"
echo ""
read -p "Enter GOOGLE_CUSTOM_SEARCH_ENGINE_ID (or press Enter to skip): " CUSTOM_SEARCH_ENGINE_ID

if [ ! -z "$CUSTOM_SEARCH_ENGINE_ID" ]; then
    add_secret_value "GOOGLE_CUSTOM_SEARCH_ENGINE_ID" "$CUSTOM_SEARCH_ENGINE_ID" "Google Custom Search Engine ID"
fi

# Get Google Knowledge Graph API Key
echo ""
echo "=== Google Knowledge Graph API ==="
echo "Get your API key from: https://console.cloud.google.com/apis/credentials"
echo "Enable 'Knowledge Graph Search API' in: https://console.cloud.google.com/apis/library/kgsearch.googleapis.com"
echo ""
read -p "Enter GOOGLE_KNOWLEDGE_GRAPH_API_KEY (or press Enter to skip): " KNOWLEDGE_GRAPH_KEY

if [ ! -z "$KNOWLEDGE_GRAPH_KEY" ]; then
    add_secret_value "GOOGLE_KNOWLEDGE_GRAPH_API_KEY" "$KNOWLEDGE_GRAPH_KEY" "Google Knowledge Graph API Key"
fi

# Summary
echo ""
echo "======================================"
echo -e "${GREEN}✅ Credentials added successfully!${NC}"
echo ""
echo "Next steps:"
echo "1. Redeploy Cloud Run service to load new credentials:"
echo "   git push origin develop"
echo ""
echo "2. Check startup logs to verify initialization:"
echo "   gcloud logging read \"resource.type=cloud_run_revision AND resource.labels.service_name=blog-writer-api-dev AND textPayload=~'Google'\" --limit=10 --project=$PROJECT_ID"
echo ""
echo "3. Test the API endpoint with use_google_search=true"

