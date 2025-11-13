#!/bin/bash

# Update Cloud Run service to use Secret Manager secrets for AI providers
# This script updates the Cloud Run service configuration to reference secrets

set -e

PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-"api-ai-blog-writer"}
REGION=${REGION:-"europe-west1"}
SERVICE_NAME=${SERVICE_NAME:-"blog-writer-api-dev"}

echo "🚀 Updating Cloud Run service to use AI provider secrets..."
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Service: $SERVICE_NAME"
echo ""

# Check if secrets exist
echo "Checking secrets..."
gcloud secrets describe OPENAI_API_KEY --project=$PROJECT_ID &>/dev/null && echo "✅ OPENAI_API_KEY exists" || echo "⚠️  OPENAI_API_KEY not found"
gcloud secrets describe ANTHROPIC_API_KEY --project=$PROJECT_ID &>/dev/null && echo "✅ ANTHROPIC_API_KEY exists" || echo "⚠️  ANTHROPIC_API_KEY not found"

echo ""
echo "Updating Cloud Run service..."

# Build update command with available secrets
UPDATE_CMD="gcloud run services update $SERVICE_NAME --region=$REGION --project=$PROJECT_ID"

# Add secrets if they exist
if gcloud secrets describe OPENAI_API_KEY --project=$PROJECT_ID &>/dev/null; then
    UPDATE_CMD="$UPDATE_CMD --update-secrets=OPENAI_API_KEY=OPENAI_API_KEY:latest"
fi

if gcloud secrets describe ANTHROPIC_API_KEY --project=$PROJECT_ID &>/dev/null; then
    UPDATE_CMD="$UPDATE_CMD --update-secrets=ANTHROPIC_API_KEY=ANTHROPIC_API_KEY:latest"
fi

# Execute update
eval $UPDATE_CMD

echo ""
echo "✅ Service updated successfully!"
echo ""
echo "Verifying configuration..."
gcloud run services describe $SERVICE_NAME \
  --region=$REGION \
  --project=$PROJECT_ID \
  --format="value(spec.template.spec.containers[0].env)" | grep -i "openai\|anthropic" || echo "⚠️  Secrets may not be visible in this format"

echo ""
echo "🎉 Done! The service will restart with new secrets."
