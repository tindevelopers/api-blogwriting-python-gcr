#!/bin/bash
# Add Cloud Tasks environment variables for image generation to Google Secret Manager
# Follows the same pattern as blog generation Cloud Tasks setup

set -e

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-${GCP_PROJECT_ID}}"
ENV="${1:-dev}"  # dev, staging, or prod

if [ -z "$PROJECT_ID" ]; then
    echo "❌ Error: GOOGLE_CLOUD_PROJECT or GCP_PROJECT_ID must be set"
    exit 1
fi

echo "🔐 Adding Cloud Tasks environment variables for image generation"
echo "   Project: $PROJECT_ID"
echo "   Environment: $ENV"
echo ""

SECRET_NAME="blog-writer-env-${ENV}"

# Cloud Tasks configuration for image generation
CLOUD_TASKS_IMAGE_QUEUE_NAME="${CLOUD_TASKS_IMAGE_QUEUE_NAME:-image-generation-queue}"
CLOUD_TASKS_QUEUE_LOCATION="${CLOUD_TASKS_QUEUE_LOCATION:-europe-west1}"

# Check if secret exists
if ! gcloud secrets describe "$SECRET_NAME" --project="$PROJECT_ID" &>/dev/null; then
    echo "❌ Secret $SECRET_NAME does not exist. Please create it first."
    echo "   Run: gcloud secrets create $SECRET_NAME --project=$PROJECT_ID"
    exit 1
fi

echo "📝 Reading current secret value..."
CURRENT_CONTENT=$(gcloud secrets versions access latest --secret="$SECRET_NAME" --project="$PROJECT_ID" 2>/dev/null || echo "")

# If secret is empty or doesn't exist, start with empty JSON
if [ -z "$CURRENT_CONTENT" ]; then
    CURRENT_CONTENT="{}"
fi

# Add or update Cloud Tasks environment variables
echo "🔧 Updating secret with Cloud Tasks configuration..."

# Use jq to update the JSON, or create new JSON if jq is not available
if command -v jq &> /dev/null; then
    UPDATED_CONTENT=$(echo "$CURRENT_CONTENT" | jq --arg queue_name "$CLOUD_TASKS_IMAGE_QUEUE_NAME" \
        --arg location "$CLOUD_TASKS_QUEUE_LOCATION" \
        --arg project_id "$PROJECT_ID" \
        '. + {
            CLOUD_TASKS_IMAGE_QUEUE_NAME: $queue_name,
            CLOUD_TASKS_QUEUE_LOCATION: $location,
            GOOGLE_CLOUD_PROJECT: $project_id
        }')
else
    echo "⚠️  jq not found. Please manually add these to $SECRET_NAME:"
    echo "   CLOUD_TASKS_IMAGE_QUEUE_NAME=$CLOUD_TASKS_IMAGE_QUEUE_NAME"
    echo "   CLOUD_TASKS_QUEUE_LOCATION=$CLOUD_TASKS_QUEUE_LOCATION"
    echo "   GOOGLE_CLOUD_PROJECT=$PROJECT_ID"
    exit 1
fi

# Create new secret version
echo "$UPDATED_CONTENT" | gcloud secrets versions add "$SECRET_NAME" \
    --data-file=- \
    --project="$PROJECT_ID"

echo ""
echo "✅ Cloud Tasks environment variables added to secret: $SECRET_NAME"
echo ""
echo "Added variables:"
echo "  - CLOUD_TASKS_IMAGE_QUEUE_NAME=$CLOUD_TASKS_IMAGE_QUEUE_NAME"
echo "  - CLOUD_TASKS_QUEUE_LOCATION=$CLOUD_TASKS_QUEUE_LOCATION"
echo "  - GOOGLE_CLOUD_PROJECT=$PROJECT_ID"
echo ""
echo "Note: These variables are already set for blog generation."
echo "      Image generation will use the same GOOGLE_CLOUD_PROJECT and CLOUD_TASKS_QUEUE_LOCATION."
echo "      Only CLOUD_TASKS_IMAGE_QUEUE_NAME is new."
echo ""
echo "Next steps:"
echo "  1. Redeploy Cloud Run service to pick up new secret version"
echo "  2. Test async image generation endpoints"
echo "  3. Monitor Cloud Tasks queue in Cloud Console"



