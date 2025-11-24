#!/bin/bash
# Non-interactive script to add DataForSEO secrets to staging and production
# Usage: 
#   DATAFORSEO_API_KEY="email" DATAFORSEO_API_SECRET="api-key" ./scripts/add-dataforseo-secrets-noninteractive.sh
#   ./scripts/add-dataforseo-secrets-noninteractive.sh "email" "api-key"

set -e

PROJECT_ID="api-ai-blog-writer"

echo "🔐 Adding DataForSEO secrets to STAGING and PRODUCTION (non-interactive)..."
echo "Project: $PROJECT_ID"
echo ""

# Function to add or update a secret value (handles both JSON and plain text formats)
add_secret_value() {
    local SECRET_NAME=$1
    local KEY=$2
    local VALUE=$3
    
    echo "📝 Adding $KEY to $SECRET_NAME..."
    
    # Check if secret exists
    if gcloud secrets describe "$SECRET_NAME" --project="$PROJECT_ID" &>/dev/null; then
        # Get current secret value
        CURRENT_CONTENT=$(gcloud secrets versions access latest --secret="$SECRET_NAME" --project="$PROJECT_ID")
        
        # Check if it's JSON format
        if echo "$CURRENT_CONTENT" | jq . >/dev/null 2>&1; then
            # JSON format - update JSON
            UPDATED_CONTENT=$(echo "$CURRENT_CONTENT" | jq --arg key "$KEY" --arg value "$VALUE" '. + {($key): $value}')
        else
            # Plain text format (env file) - append or update key-value pair
            # Remove existing line with this key if it exists
            UPDATED_CONTENT=$(echo "$CURRENT_CONTENT" | grep -v "^${KEY}=" || echo "$CURRENT_CONTENT")
            # Add new line
            UPDATED_CONTENT="${UPDATED_CONTENT}
${KEY}=${VALUE}"
        fi
        
        # Create new secret version
        echo "$UPDATED_CONTENT" | gcloud secrets versions add "$SECRET_NAME" \
            --data-file=- \
            --project="$PROJECT_ID" \
            --quiet
        
        echo "✅ Updated $KEY in $SECRET_NAME"
    else
        echo "❌ Secret $SECRET_NAME does not exist. Please create it first with:"
        echo "   echo '{}' | gcloud secrets create $SECRET_NAME --data-file=- --project=$PROJECT_ID"
        return 1
    fi
}

# Get DataForSEO credentials from command-line args or env vars
if [ $# -ge 2 ]; then
    # Provided as command-line arguments
    DATAFORSEO_API_KEY="$1"
    DATAFORSEO_API_SECRET="$2"
    echo "Using credentials from command-line arguments"
elif [ -n "$DATAFORSEO_API_KEY" ] && [ -n "$DATAFORSEO_API_SECRET" ]; then
    # Provided as environment variables
    echo "Using credentials from environment variables"
else
    echo "❌ Error: DataForSEO credentials are required"
    echo ""
    echo "Usage:"
    echo "  $0 [username-email] [api-key]"
    echo "   Or:"
    echo "  DATAFORSEO_API_KEY=\"email\" DATAFORSEO_API_SECRET=\"api-key\" $0"
    echo ""
    echo "Where:"
    echo "  username-email = Your DataForSEO account email/username"
    echo "  api-key = Your DataForSEO API key"
    exit 1
fi

# Validate credentials are provided
if [ -z "$DATAFORSEO_API_KEY" ] || [ -z "$DATAFORSEO_API_SECRET" ]; then
    echo "❌ Error: DataForSEO Username/Email and API Key are required"
    exit 1
fi

echo ""
echo "📋 Credential Mapping:"
echo "   Username/Email → DATAFORSEO_API_KEY"
echo "   API Key → DATAFORSEO_API_SECRET"
echo ""

# Add to staging environment
echo "=== STAGING Environment ==="
add_secret_value "blog-writer-env-staging" "DATAFORSEO_API_KEY" "$DATAFORSEO_API_KEY"
add_secret_value "blog-writer-env-staging" "DATAFORSEO_API_SECRET" "$DATAFORSEO_API_SECRET"
echo ""

# Add to production environment
echo "=== PRODUCTION Environment ==="
add_secret_value "blog-writer-env-prod" "DATAFORSEO_API_KEY" "$DATAFORSEO_API_KEY"
add_secret_value "blog-writer-env-prod" "DATAFORSEO_API_SECRET" "$DATAFORSEO_API_SECRET"
echo ""

echo "✅ DataForSEO secrets added successfully to STAGING and PRODUCTION!"
echo ""
echo "📋 Next steps:"
echo "1. Verify the secrets:"
echo "   ./scripts/verify-secrets-setup.sh staging"
echo "   ./scripts/verify-secrets-setup.sh prod"
echo ""
echo "2. Redeploy services:"
echo "   - Push to 'staging' branch for staging"
echo "   - Push to 'main' branch for production"

