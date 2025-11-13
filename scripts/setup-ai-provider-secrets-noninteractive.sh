#!/bin/bash

# Non-interactive version - uses environment variables
# Usage: OPENAI_API_KEY=xxx ANTHROPIC_API_KEY=yyy ./scripts/setup-ai-provider-secrets-noninteractive.sh

set -e

PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-"api-ai-blog-writer"}
REGION=${REGION:-"europe-west1"}
SERVICE_NAME=${SERVICE_NAME:-"blog-writer-api-dev"}

echo "🤖 Setting up AI Provider Secrets (Non-Interactive)"
echo "=================================================="
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Service: $SERVICE_NAME"
echo ""

# Check if API keys are provided
if [ -z "$OPENAI_API_KEY" ] && [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "❌ Error: At least one API key must be provided"
    echo "Usage: OPENAI_API_KEY=xxx ANTHROPIC_API_KEY=yyy $0"
    exit 1
fi

# Enable Secret Manager API
echo "🔧 Enabling Secret Manager API..."
gcloud services enable secretmanager.googleapis.com --project=$PROJECT_ID 2>/dev/null || true

# Function to create or update secret
create_or_update_secret() {
    local SECRET_NAME=$1
    local SECRET_VALUE=$2
    
    if gcloud secrets describe $SECRET_NAME --project=$PROJECT_ID &>/dev/null; then
        echo "   Updating existing secret: $SECRET_NAME"
        echo -n "$SECRET_VALUE" | gcloud secrets versions add $SECRET_NAME \
            --data-file=- \
            --project=$PROJECT_ID >/dev/null
    else
        echo "   Creating new secret: $SECRET_NAME"
        echo -n "$SECRET_VALUE" | gcloud secrets create $SECRET_NAME \
            --data-file=- \
            --replication-policy="automatic" \
            --project=$PROJECT_ID >/dev/null
    fi
    echo "   ✅ Secret '$SECRET_NAME' ready"
}

# Create secrets
if [ ! -z "$OPENAI_API_KEY" ]; then
    echo "🔒 Creating/updating OPENAI_API_KEY..."
    create_or_update_secret "OPENAI_API_KEY" "$OPENAI_API_KEY"
fi

if [ ! -z "$ANTHROPIC_API_KEY" ]; then
    echo "🔒 Creating/updating ANTHROPIC_API_KEY..."
    create_or_update_secret "ANTHROPIC_API_KEY" "$ANTHROPIC_API_KEY"
fi

# Get service account
echo ""
echo "🔐 Granting Cloud Run service account access..."
SERVICE_ACCOUNT=$(gcloud run services describe $SERVICE_NAME \
    --region=$REGION \
    --project=$PROJECT_ID \
    --format="value(spec.template.spec.serviceAccountName)" 2>/dev/null || echo "613248238610-compute@developer.gserviceaccount.com")

echo "   Using service account: $SERVICE_ACCOUNT"

# Grant access
if [ ! -z "$OPENAI_API_KEY" ]; then
    echo "   Granting access to OPENAI_API_KEY..."
    gcloud secrets add-iam-policy-binding OPENAI_API_KEY \
        --member="serviceAccount:$SERVICE_ACCOUNT" \
        --role="roles/secretmanager.secretAccessor" \
        --project=$PROJECT_ID >/dev/null 2>&1 || echo "   ⚠️  Access may already be granted"
fi

if [ ! -z "$ANTHROPIC_API_KEY" ]; then
    echo "   Granting access to ANTHROPIC_API_KEY..."
    gcloud secrets add-iam-policy-binding ANTHROPIC_API_KEY \
        --member="serviceAccount:$SERVICE_ACCOUNT" \
        --role="roles/secretmanager.secretAccessor" \
        --project=$PROJECT_ID >/dev/null 2>&1 || echo "   ⚠️  Access may already be granted"
fi

# Update Cloud Run service
echo ""
echo "🚀 Updating Cloud Run service..."
UPDATE_ARGS=""

if [ ! -z "$OPENAI_API_KEY" ]; then
    UPDATE_ARGS="$UPDATE_ARGS --update-secrets=OPENAI_API_KEY=OPENAI_API_KEY:latest"
fi

if [ ! -z "$ANTHROPIC_API_KEY" ]; then
    UPDATE_ARGS="$UPDATE_ARGS --update-secrets=ANTHROPIC_API_KEY=ANTHROPIC_API_KEY:latest"
fi

if [ ! -z "$UPDATE_ARGS" ]; then
    gcloud run services update $SERVICE_NAME \
        --region=$REGION \
        --project=$PROJECT_ID \
        $UPDATE_ARGS
    
    echo "✅ Service updated successfully!"
else
    echo "⚠️  No secrets to update"
fi

echo ""
echo "🎉 Setup Complete!"
echo ""
echo "📋 Summary:"
[ ! -z "$OPENAI_API_KEY" ] && echo "✅ OPENAI_API_KEY: Configured" || echo "⚠️  OPENAI_API_KEY: Not configured"
[ ! -z "$ANTHROPIC_API_KEY" ] && echo "✅ ANTHROPIC_API_KEY: Configured" || echo "⚠️  ANTHROPIC_API_KEY: Not configured"
