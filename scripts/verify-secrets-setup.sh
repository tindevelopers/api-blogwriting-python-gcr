#!/bin/bash
# Script to verify DataForSEO secrets are configured correctly in Google Secret Manager
# Usage: ./scripts/verify-secrets-setup.sh [env]
#   env: dev (default), staging, or prod

set -e

PROJECT_ID="api-ai-blog-writer"
ENV=${1:-dev}
SECRET_NAME="blog-writer-env-${ENV}"

echo "🔍 Verifying DataForSEO secrets setup..."
echo "Project: $PROJECT_ID"
echo "Environment: $ENV"
echo "Secret: $SECRET_NAME"
echo ""

# Check if secret exists
if ! gcloud secrets describe "$SECRET_NAME" --project="$PROJECT_ID" &>/dev/null; then
    echo "❌ Secret '$SECRET_NAME' does not exist!"
    echo ""
    echo "To create it, run:"
    echo "  echo '{}' | gcloud secrets create $SECRET_NAME --data-file=- --project=$PROJECT_ID"
    exit 1
fi

echo "✅ Secret '$SECRET_NAME' exists"
echo ""

# Get secret content
SECRET_CONTENT=$(gcloud secrets versions access latest --secret="$SECRET_NAME" --project="$PROJECT_ID")

# Check if it's JSON format
if echo "$SECRET_CONTENT" | jq . >/dev/null 2>&1; then
    echo "✅ Secret is in JSON format"
    
    # Check for DataForSEO credentials
    API_KEY=$(echo "$SECRET_CONTENT" | jq -r '.DATAFORSEO_API_KEY // empty')
    API_SECRET=$(echo "$SECRET_CONTENT" | jq -r '.DATAFORSEO_API_SECRET // empty')
    
    if [ -z "$API_KEY" ] || [ "$API_KEY" == "null" ] || [ "$API_KEY" == "" ]; then
        echo "❌ DATAFORSEO_API_KEY is missing or empty"
        MISSING=true
    else
        echo "✅ DATAFORSEO_API_KEY is set (length: ${#API_KEY} chars)"
    fi
    
    if [ -z "$API_SECRET" ] || [ "$API_SECRET" == "null" ] || [ "$API_SECRET" == "" ]; then
        echo "❌ DATAFORSEO_API_SECRET is missing or empty"
        MISSING=true
    else
        echo "✅ DATAFORSEO_API_SECRET is set (length: ${#API_SECRET} chars)"
    fi
    
    # Check for AI provider credentials (optional but recommended)
    OPENAI_KEY=$(echo "$SECRET_CONTENT" | jq -r '.OPENAI_API_KEY // empty')
    ANTHROPIC_KEY=$(echo "$SECRET_CONTENT" | jq -r '.ANTHROPIC_API_KEY // empty')
    
    if [ -z "$OPENAI_KEY" ] || [ "$OPENAI_KEY" == "null" ] || [ "$OPENAI_KEY" == "" ]; then
        echo "⚠️  OPENAI_API_KEY is not set (optional, for pipeline fallback)"
    else
        echo "✅ OPENAI_API_KEY is set"
    fi
    
    if [ -z "$ANTHROPIC_KEY" ] || [ "$ANTHROPIC_KEY" == "null" ] || [ "$ANTHROPIC_KEY" == "" ]; then
        echo "⚠️  ANTHROPIC_API_KEY is not set (optional, for pipeline fallback)"
    else
        echo "✅ ANTHROPIC_API_KEY is set"
    fi
    
else
    echo "⚠️  Secret is not in JSON format (plain text format)"
    echo "Checking for DataForSEO credentials..."
    
    if echo "$SECRET_CONTENT" | grep -q "DATAFORSEO_API_KEY"; then
        echo "✅ DATAFORSEO_API_KEY found in secret"
    else
        echo "❌ DATAFORSEO_API_KEY not found in secret"
        MISSING=true
    fi
    
    if echo "$SECRET_CONTENT" | grep -q "DATAFORSEO_API_SECRET"; then
        echo "✅ DATAFORSEO_API_SECRET found in secret"
    else
        echo "❌ DATAFORSEO_API_SECRET not found in secret"
        MISSING=true
    fi
fi

echo ""

# Check service account permissions
echo "🔐 Checking service account permissions..."
SERVICE_ACCOUNT="blog-writer-service-account@${PROJECT_ID}.iam.gserviceaccount.com"

# Try to get IAM policy
IAM_POLICY=$(gcloud secrets get-iam-policy "$SECRET_NAME" --project="$PROJECT_ID" 2>/dev/null || echo "")

if echo "$IAM_POLICY" | grep -q "$SERVICE_ACCOUNT"; then
    echo "✅ Service account '$SERVICE_ACCOUNT' has access to secret"
else
    echo "⚠️  Service account '$SERVICE_ACCOUNT' may not have access"
    echo "   Grant access with:"
    echo "   gcloud secrets add-iam-policy-binding $SECRET_NAME \\"
    echo "     --member=\"serviceAccount:$SERVICE_ACCOUNT\" \\"
    echo "     --role=\"roles/secretmanager.secretAccessor\" \\"
    echo "     --project=$PROJECT_ID"
fi

echo ""

# Summary
if [ "$MISSING" = true ]; then
    echo "❌ Setup incomplete: Missing required DataForSEO credentials"
    echo ""
    echo "To add credentials, run:"
    echo "  ./scripts/add-dataforseo-secrets.sh"
    echo ""
    echo "Or manually:"
    echo "  See GOOGLE_SECRETS_SETUP_V1.3.6.md for instructions"
    exit 1
else
    echo "✅ Setup complete: All required secrets are configured"
    echo ""
    echo "Next steps:"
    echo "1. Redeploy the service (push to 'develop' branch for dev)"
    echo "2. Check Cloud Run logs for: '✅ Environment variables loaded from secrets'"
    echo "3. Test the endpoint:"
    echo "   curl -X POST https://blog-writer-api-dev-kq42l26tuq-od.a.run.app/api/v1/blog/generate-enhanced \\"
    echo "     -H 'Content-Type: application/json' \\"
    echo "     -d '{\"topic\":\"Test\",\"keywords\":[\"test\"],\"blog_type\":\"tutorial\",\"length\":\"short\"}'"
    exit 0
fi

