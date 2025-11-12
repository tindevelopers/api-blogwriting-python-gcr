#!/bin/bash
# Quick script to add Google Search credentials immediately
# Usage: Provide credentials when prompted

set -e

PROJECT_ID="api-ai-blog-writer"
SECRET_NAME="blog-writer-env-dev"

echo "🔐 Adding Google Search Credentials to Secret Manager"
echo "====================================================="
echo ""

# Function to add secret value
add_secret_value() {
    local KEY=$1
    local VALUE=$2
    
    CURRENT_CONTENT=$(gcloud secrets versions access latest --secret="$SECRET_NAME" --project="$PROJECT_ID" 2>/dev/null)
    
    if echo "$CURRENT_CONTENT" | jq . >/dev/null 2>&1; then
        UPDATED_CONTENT=$(echo "$CURRENT_CONTENT" | jq --arg key "$KEY" --arg value "$VALUE" '. + {($key): $value}')
        echo "$UPDATED_CONTENT" | gcloud secrets versions add "$SECRET_NAME" \
            --data-file=- \
            --project="$PROJECT_ID" \
            --quiet
    else
        UPDATED_CONTENT=$(echo "$CURRENT_CONTENT" | grep -v "^${KEY}=" || echo "$CURRENT_CONTENT")
        UPDATED_CONTENT="${UPDATED_CONTENT}
${KEY}=${VALUE}"
        echo "$UPDATED_CONTENT" | gcloud secrets versions add "$SECRET_NAME" \
            --data-file=- \
            --project="$PROJECT_ID" \
            --quiet
    fi
    echo "✅ Added $KEY"
}

# Get credentials
read -p "Enter GOOGLE_CUSTOM_SEARCH_API_KEY: " CUSTOM_SEARCH_KEY
read -p "Enter GOOGLE_CUSTOM_SEARCH_ENGINE_ID (CX): " CUSTOM_SEARCH_ENGINE_ID
read -p "Enter GOOGLE_KNOWLEDGE_GRAPH_API_KEY (or press Enter to skip): " KG_KEY

echo ""
echo "Adding to Secret Manager..."

add_secret_value "GOOGLE_CUSTOM_SEARCH_API_KEY" "$CUSTOM_SEARCH_KEY"
add_secret_value "GOOGLE_CUSTOM_SEARCH_ENGINE_ID" "$CUSTOM_SEARCH_ENGINE_ID"

if [ ! -z "$KG_KEY" ]; then
    add_secret_value "GOOGLE_KNOWLEDGE_GRAPH_API_KEY" "$KG_KEY"
fi

echo ""
echo "✅ Credentials added successfully!"
echo ""
echo "Next: Redeploy Cloud Run to load credentials:"
echo "  git push origin develop"

