#!/bin/bash
# Script to help get Google Search API credentials using gcloud CLI
# Usage: ./scripts/get-google-search-credentials.sh

set -e

PROJECT_ID="api-ai-blog-writer"

echo "🔍 Google Search API Credentials Helper"
echo "======================================"
echo ""

# Check authentication
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &>/dev/null; then
    echo "❌ Not authenticated. Please run: gcloud auth login"
    exit 1
fi

echo "✅ Authenticated as: $(gcloud auth list --filter=status:ACTIVE --format='value(account)')"
echo ""

# Enable required APIs
echo "=== Step 1: Enabling Required APIs ==="
echo "Enabling Custom Search API..."
gcloud services enable customsearch.googleapis.com --project="$PROJECT_ID" 2>&1 | grep -v "already enabled" || true

echo "Enabling Knowledge Graph API..."
gcloud services enable kgsearch.googleapis.com --project="$PROJECT_ID" 2>&1 | grep -v "already enabled" || true

echo "Enabling API Keys API..."
gcloud services enable apikeys.googleapis.com --project="$PROJECT_ID" 2>&1 | grep -v "already enabled" || true

echo "✅ APIs enabled"
echo ""

# Check for existing API keys
echo "=== Step 2: Checking Existing API Keys ==="
EXISTING_KEYS=$(gcloud services api-keys list --project="$PROJECT_ID" 2>/dev/null | grep -v "DISPLAY_NAME" | wc -l | tr -d ' ')
if [ "$EXISTING_KEYS" -gt 0 ]; then
    echo "Found $EXISTING_KEYS existing API key(s):"
    gcloud services api-keys list --project="$PROJECT_ID" 2>/dev/null | head -5
    echo ""
    read -p "Use existing key? (y/N): " USE_EXISTING
    if [[ "$USE_EXISTING" =~ ^[Yy]$ ]]; then
        echo "Select an API key to use:"
        gcloud services api-keys list --project="$PROJECT_ID" --format="table(name,displayName)" 2>/dev/null
        read -p "Enter API key name (or press Enter to create new): " KEY_NAME
    fi
else
    echo "No existing API keys found"
fi

echo ""

# Create API keys
echo "=== Step 3: Creating API Keys ==="
echo ""
echo "⚠️  Note: API key creation via CLI may require additional permissions."
echo "   If this fails, create keys via: https://console.cloud.google.com/apis/credentials"
echo ""

# Try to create Custom Search API key
echo "Creating Custom Search API key..."
CUSTOM_SEARCH_KEY=$(gcloud alpha services api-keys create \
    --display-name="Blog Writer Custom Search API Key" \
    --api-target=service=customsearch.googleapis.com \
    --project="$PROJECT_ID" \
    --format="value(name)" 2>&1) || CUSTOM_SEARCH_KEY=""

if [ ! -z "$CUSTOM_SEARCH_KEY" ] && [ ! "$CUSTOM_SEARCH_KEY" = *"error"* ]; then
    echo "✅ Custom Search API key created: $CUSTOM_SEARCH_KEY"
    # Get the actual key value
    CUSTOM_SEARCH_KEY_VALUE=$(gcloud alpha services api-keys get-key-string "$CUSTOM_SEARCH_KEY" --project="$PROJECT_ID" --format="value(keyString)" 2>&1)
    echo "   Key value: ${CUSTOM_SEARCH_KEY_VALUE:0:20}..."
else
    echo "⚠️  Could not create via CLI. Please create manually:"
    echo "   https://console.cloud.google.com/apis/credentials"
    echo "   Then run: ./scripts/add-google-search-secrets.sh"
    CUSTOM_SEARCH_KEY_VALUE=""
fi

echo ""

# Try to create Knowledge Graph API key
echo "Creating Knowledge Graph API key..."
KG_KEY=$(gcloud alpha services api-keys create \
    --display-name="Blog Writer Knowledge Graph API Key" \
    --api-target=service=kgsearch.googleapis.com \
    --project="$PROJECT_ID" \
    --format="value(name)" 2>&1) || KG_KEY=""

if [ ! -z "$KG_KEY" ] && [ ! "$KG_KEY" = *"error"* ]; then
    echo "✅ Knowledge Graph API key created: $KG_KEY"
    KG_KEY_VALUE=$(gcloud alpha services api-keys get-key-string "$KG_KEY" --project="$PROJECT_ID" --format="value(keyString)" 2>&1)
    echo "   Key value: ${KG_KEY_VALUE:0:20}..."
else
    echo "⚠️  Could not create via CLI. Please create manually:"
    echo "   https://console.cloud.google.com/apis/credentials"
    KG_KEY_VALUE=""
fi

echo ""

# Custom Search Engine ID
echo "=== Step 4: Custom Search Engine ID (CX) ==="
echo ""
echo "❌ Custom Search Engine ID cannot be created via CLI."
echo "   You must create it manually:"
echo ""
echo "   1. Go to: https://programmablesearchengine.google.com/"
echo "   2. Click 'Add' to create a new search engine"
echo "   3. Enter a name and description"
echo "   4. Choose 'Search the entire web'"
echo "   5. Click 'Create'"
echo "   6. Copy the 'Search engine ID' (CX) from the Overview page"
echo ""
read -p "Enter your Custom Search Engine ID (CX) or press Enter to skip: " CUSTOM_SEARCH_ENGINE_ID

echo ""

# Summary
echo "======================================"
echo "Summary"
echo "======================================"
echo ""

if [ ! -z "$CUSTOM_SEARCH_KEY_VALUE" ]; then
    echo "✅ Custom Search API Key: ${CUSTOM_SEARCH_KEY_VALUE:0:20}..."
else
    echo "⚠️  Custom Search API Key: Not created (create manually)"
fi

if [ ! -z "$KG_KEY_VALUE" ]; then
    echo "✅ Knowledge Graph API Key: ${KG_KEY_VALUE:0:20}..."
else
    echo "⚠️  Knowledge Graph API Key: Not created (create manually)"
fi

if [ ! -z "$CUSTOM_SEARCH_ENGINE_ID" ]; then
    echo "✅ Custom Search Engine ID: $CUSTOM_SEARCH_ENGINE_ID"
else
    echo "⚠️  Custom Search Engine ID: Not provided"
fi

echo ""

# Offer to add to Secret Manager
if [ ! -z "$CUSTOM_SEARCH_KEY_VALUE" ] && [ ! -z "$CUSTOM_SEARCH_ENGINE_ID" ]; then
    read -p "Add these credentials to Secret Manager now? (y/N): " ADD_TO_SECRETS
    if [[ "$ADD_TO_SECRETS" =~ ^[Yy]$ ]]; then
        echo ""
        echo "Adding to Secret Manager..."
        
        # Use the add script
        export GOOGLE_CUSTOM_SEARCH_API_KEY="$CUSTOM_SEARCH_KEY_VALUE"
        export GOOGLE_CUSTOM_SEARCH_ENGINE_ID="$CUSTOM_SEARCH_ENGINE_ID"
        [ ! -z "$KG_KEY_VALUE" ] && export GOOGLE_KNOWLEDGE_GRAPH_API_KEY="$KG_KEY_VALUE"
        
        ./scripts/add-google-search-secrets.sh << EOF
$CUSTOM_SEARCH_KEY_VALUE
$CUSTOM_SEARCH_ENGINE_ID
${KG_KEY_VALUE:-}
EOF
    fi
else
    echo ""
    echo "⚠️  Cannot add to Secret Manager - missing required credentials"
    echo "   Run ./scripts/add-google-search-secrets.sh after getting credentials"
fi

echo ""
echo "✅ Done!"

