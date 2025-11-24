#!/bin/bash
# Script to add DataForSEO secrets to Google Secret Manager for all environments
# Usage: 
#   ./scripts/add-dataforseo-secrets.sh
#   DATAFORSEO_API_KEY=xxx DATAFORSEO_API_SECRET=yyy ./scripts/add-dataforseo-secrets.sh
#   ./scripts/add-dataforseo-secrets.sh <api-key> <api-secret>

set -e

PROJECT_ID="api-ai-blog-writer"

echo "🔐 Adding DataForSEO secrets to Google Secret Manager..."
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
        echo "   echo '' | gcloud secrets create $SECRET_NAME --data-file=- --project=$PROJECT_ID"
        return 1
    fi
}

# Get DataForSEO credentials from command-line args, env vars, or prompt
if [ $# -ge 2 ]; then
    # Provided as command-line arguments
    DATAFORSEO_API_KEY="$1"
    DATAFORSEO_API_SECRET="$2"
    echo "Using credentials from command-line arguments"
elif [ -n "$DATAFORSEO_API_KEY" ] && [ -n "$DATAFORSEO_API_SECRET" ]; then
    # Provided as environment variables
    echo "Using credentials from environment variables"
else
    # Prompt interactively
    echo "Please enter your DataForSEO credentials:"
    echo ""
    echo "DataForSEO uses Basic Authentication:"
    echo "  - Username/Email address (used as API Key)"
    echo "  - API Key (used as API Secret)"
    echo ""
    read -p "DataForSEO Username/Email: " DATAFORSEO_API_KEY
    read -sp "DataForSEO API Key: " DATAFORSEO_API_SECRET
    echo ""
fi

# Validate credentials are provided
if [ -z "$DATAFORSEO_API_KEY" ] || [ -z "$DATAFORSEO_API_SECRET" ]; then
    echo "❌ Error: DataForSEO Username/Email and API Key are required"
    echo ""
    echo "Usage: $0 [username-email] [api-key]"
    echo "   Or: DATAFORSEO_API_KEY=xxx DATAFORSEO_API_SECRET=yyy $0"
    echo ""
    echo "Where:"
    echo "  username-email = Your DataForSEO account email/username"
    echo "  api-key = Your DataForSEO API key"
    exit 1
fi

echo ""

# Add to dev environment
echo "=== DEV Environment ==="
echo "Adding Username/Email as DATAFORSEO_API_KEY..."
add_secret_value "blog-writer-env-dev" "DATAFORSEO_API_KEY" "$DATAFORSEO_API_KEY"
echo "Adding API Key as DATAFORSEO_API_SECRET..."
add_secret_value "blog-writer-env-dev" "DATAFORSEO_API_SECRET" "$DATAFORSEO_API_SECRET"
echo ""

# Add to staging environment
echo "=== STAGING Environment ==="
echo "Adding Username/Email as DATAFORSEO_API_KEY..."
add_secret_value "blog-writer-env-staging" "DATAFORSEO_API_KEY" "$DATAFORSEO_API_KEY"
echo "Adding API Key as DATAFORSEO_API_SECRET..."
add_secret_value "blog-writer-env-staging" "DATAFORSEO_API_SECRET" "$DATAFORSEO_API_SECRET"
echo ""

# Add to production environment
echo "=== PRODUCTION Environment ==="
if [ -z "$SKIP_PROD" ]; then
    read -p "Add to production? (y/N): " CONFIRM_PROD
    if [[ "$CONFIRM_PROD" =~ ^[Yy]$ ]]; then
        echo "Adding Username/Email as DATAFORSEO_API_KEY..."
        add_secret_value "blog-writer-env-prod" "DATAFORSEO_API_KEY" "$DATAFORSEO_API_KEY"
        echo "Adding API Key as DATAFORSEO_API_SECRET..."
        add_secret_value "blog-writer-env-prod" "DATAFORSEO_API_SECRET" "$DATAFORSEO_API_SECRET"
    else
        echo "⏭️  Skipping production"
    fi
else
    echo "⏭️  Skipping production (SKIP_PROD set)"
fi

echo ""
echo "✅ DataForSEO secrets added successfully!"
echo ""
echo "📋 Credential Mapping:"
echo "   Username/Email → DATAFORSEO_API_KEY"
echo "   API Key → DATAFORSEO_API_SECRET"
echo ""
echo "📋 Next steps:"
echo "1. Redeploy each environment to pick up the new secrets:"
echo "   - Push to 'develop' branch for dev"
echo "   - Push to 'staging' branch for staging"
echo "   - Push to 'main' branch for production"
echo ""
echo "2. Verify the secrets are accessible:"
echo "   gcloud secrets versions access latest --secret=blog-writer-env-dev --project=$PROJECT_ID | jq '.DATAFORSEO_API_KEY'"
echo ""
echo "3. Test the endpoint after deployment:"
echo "   curl -X POST https://blog-writer-api-dev-kq42l26tuq-od.a.run.app/api/v1/blog/generate-enhanced \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"topic\":\"Test\",\"keywords\":[\"test\"],\"blog_type\":\"tutorial\",\"length\":\"short\"}'"

