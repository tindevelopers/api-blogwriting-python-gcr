#!/bin/bash
# Script to add Stability.ai API Key to Google Secret Manager
# Usage: ./scripts/add-stability-ai-secrets.sh

set -e

PROJECT_ID="api-ai-blog-writer"

# Function to add or update a secret value (handles both JSON and plain text formats)
add_secret_value() {
    local SECRET_NAME=$1
    local KEY=$2
    local VALUE=$3
    
    echo "📝 Adding $KEY to $SECRET_NAME..."
    
    if gcloud secrets describe "$SECRET_NAME" --project="$PROJECT_ID" &>/dev/null; then
        CURRENT_CONTENT=$(gcloud secrets versions access latest --secret="$SECRET_NAME" --project="$PROJECT_ID")
        
        if echo "$CURRENT_CONTENT" | jq . >/dev/null 2>&1; then
            # JSON format
            UPDATED_CONTENT=$(echo "$CURRENT_CONTENT" | jq --arg key "$KEY" --arg value "$VALUE" '. + {($key): $value}')
        else
            # Plain text format (env file)
            if echo "$CURRENT_CONTENT" | grep -q "^${KEY}="; then
                # Update existing key
                UPDATED_CONTENT=$(echo "$CURRENT_CONTENT" | sed "s|^${KEY}=.*|${KEY}=${VALUE}|")
            else
                # Add new key
                UPDATED_CONTENT="${CURRENT_CONTENT}
${KEY}=${VALUE}"
            fi
        fi
        
        echo "$UPDATED_CONTENT" | gcloud secrets versions add "$SECRET_NAME" \
            --data-file=- \
            --project="$PROJECT_ID" \
            --quiet
        
        echo "✅ Updated $KEY in $SECRET_NAME"
    else
        echo "❌ Secret $SECRET_NAME does not exist. Please create it first with:"
        echo "   echo '' | gcloud secrets create $SECRET_NAME --data-file=- --project=$PROJECT_ID"
        return 1
    fi
}

# Get Stability.ai API Key
echo "🔑 Stability.ai API Key Setup"
echo "================================"
echo ""
echo "You can get your Stability.ai API key from:"
echo "https://platform.stability.ai/account/keys"
echo ""

if [ -n "$STABILITY_AI_API_KEY" ]; then
    API_KEY="$STABILITY_AI_API_KEY"
    echo "✅ Using API key from environment variable"
elif [ -n "$1" ]; then
    API_KEY="$1"
    echo "✅ Using API key from command line argument"
else
    read -p "Enter your Stability.ai API Key: " API_KEY
fi

if [ -z "$API_KEY" ]; then
    echo "❌ API key is required"
    exit 1
fi

# Optional: Get default model
DEFAULT_MODEL="${STABILITY_AI_DEFAULT_MODEL:-stable-diffusion-xl-1024-v1-0}"
if [ -n "$2" ]; then
    DEFAULT_MODEL="$2"
fi

echo ""
echo "📋 Configuration:"
echo "   API Key: ${API_KEY:0:10}...${API_KEY: -4}"
echo "   Default Model: $DEFAULT_MODEL"
echo ""

# Add to dev environment
echo "🔧 Adding to dev environment..."
add_secret_value "blog-writer-env-dev" "STABILITY_AI_API_KEY" "$API_KEY"
add_secret_value "blog-writer-env-dev" "STABILITY_AI_DEFAULT_MODEL" "$DEFAULT_MODEL"

# Ask about staging
read -p "Add to staging environment? (y/n): " ADD_STAGING
if [[ "$ADD_STAGING" =~ ^[Yy]$ ]]; then
    echo "🔧 Adding to staging environment..."
    add_secret_value "blog-writer-env-staging" "STABILITY_AI_API_KEY" "$API_KEY"
    add_secret_value "blog-writer-env-staging" "STABILITY_AI_DEFAULT_MODEL" "$DEFAULT_MODEL"
fi

# Ask about production
read -p "Add to production environment? (y/n): " ADD_PROD
if [[ "$ADD_PROD" =~ ^[Yy]$ ]]; then
    echo "🔧 Adding to production environment..."
    add_secret_value "blog-writer-env-prod" "STABILITY_AI_API_KEY" "$API_KEY"
    add_secret_value "blog-writer-env-prod" "STABILITY_AI_DEFAULT_MODEL" "$DEFAULT_MODEL"
fi

echo ""
echo "✅ Stability.ai API key added successfully!"
echo ""
echo "📝 Next steps:"
echo "   1. Restart Cloud Run service or wait for next deployment"
echo "   2. Verify: curl https://blog-writer-api-dev-613248238610.europe-west1.run.app/api/v1/images/providers"
echo "   3. Test: POST /api/v1/images/generate"
echo ""

