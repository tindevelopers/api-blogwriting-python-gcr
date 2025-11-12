#!/bin/bash
# Quick setup script for Google Search credentials
# Opens web console links and guides through setup

set -e

PROJECT_ID="api-ai-blog-writer"

echo "🚀 Google Search API Quick Setup"
echo "================================"
echo ""
echo "This script will help you get Google Search credentials."
echo ""

# Check if we're on macOS (can open URLs)
if [[ "$OSTYPE" == "darwin"* ]]; then
    OPEN_CMD="open"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OPEN_CMD="xdg-open"
else
    OPEN_CMD="echo"
fi

echo "Step 1: Create Google Custom Search API Key"
echo "-------------------------------------------"
echo "Opening Google Cloud Console..."
$OPEN_CMD "https://console.cloud.google.com/apis/credentials?project=$PROJECT_ID" 2>/dev/null || true
echo ""
echo "In the console:"
echo "  1. Click 'Create Credentials' → 'API Key'"
echo "  2. Copy the API key"
echo "  3. (Optional) Click 'Restrict Key' → Restrict to 'Custom Search API'"
echo ""
read -p "Paste your GOOGLE_CUSTOM_SEARCH_API_KEY here: " CUSTOM_SEARCH_KEY

echo ""
echo "Step 2: Create Custom Search Engine (CX)"
echo "-----------------------------------------"
echo "Opening Custom Search Engine page..."
$OPEN_CMD "https://programmablesearchengine.google.com/" 2>/dev/null || true
echo ""
echo "In the console:"
echo "  1. Click 'Add' to create a new search engine"
echo "  2. Enter a name (e.g., 'Blog Writer Search')"
echo "  3. Choose 'Search the entire web'"
echo "  4. Click 'Create'"
echo "  5. Copy the 'Search engine ID' (CX) from Overview page"
echo ""
read -p "Paste your GOOGLE_CUSTOM_SEARCH_ENGINE_ID here: " CUSTOM_SEARCH_ENGINE_ID

echo ""
echo "Step 3: Create Google Knowledge Graph API Key (Optional)"
echo "--------------------------------------------------------"
echo "Opening Google Cloud Console..."
$OPEN_CMD "https://console.cloud.google.com/apis/credentials?project=$PROJECT_ID" 2>/dev/null || true
echo ""
echo "In the console:"
echo "  1. Click 'Create Credentials' → 'API Key'"
echo "  2. Copy the API key"
echo "  3. (Optional) Click 'Restrict Key' → Restrict to 'Knowledge Graph Search API'"
echo ""
read -p "Paste your GOOGLE_KNOWLEDGE_GRAPH_API_KEY here (or press Enter to skip): " KG_KEY

echo ""
echo "Step 4: Adding to Secret Manager"
echo "---------------------------------"
echo ""

if [ -z "$CUSTOM_SEARCH_KEY" ] || [ -z "$CUSTOM_SEARCH_ENGINE_ID" ]; then
    echo "❌ Error: Custom Search API Key and Engine ID are required"
    exit 1
fi

# Add to Secret Manager using the add script
export GOOGLE_CUSTOM_SEARCH_API_KEY="$CUSTOM_SEARCH_KEY"
export GOOGLE_CUSTOM_SEARCH_ENGINE_ID="$CUSTOM_SEARCH_ENGINE_ID"
[ ! -z "$KG_KEY" ] && export GOOGLE_KNOWLEDGE_GRAPH_API_KEY="$KG_KEY"

echo "Adding credentials to Secret Manager..."
./scripts/add-google-search-secrets.sh << EOF
$CUSTOM_SEARCH_KEY
$CUSTOM_SEARCH_ENGINE_ID
${KG_KEY:-}
EOF

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Redeploy Cloud Run: git push origin develop"
echo "2. Check logs: gcloud logging read \"resource.type=cloud_run_revision AND resource.labels.service_name=blog-writer-api-dev AND textPayload=~'Google'\" --limit=10 --project=$PROJECT_ID"

