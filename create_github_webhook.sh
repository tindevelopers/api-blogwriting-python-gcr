#!/bin/bash
set -e

REPO_OWNER="tindevelopers"
REPO_NAME="api-blogwriting-python-gcr"
PROJECT_ID="api-ai-blog-writer"
REGION="europe-west9"
TRIGGER_ID="5cabcb18-791d-4082-8871-d7b2c027be27"

echo "🔍 Checking existing webhooks for Cloud Build..."

# List all webhooks
WEBHOOKS=$(gh api repos/${REPO_OWNER}/${REPO_NAME}/hooks --jq '.[] | {id: .id, url: .config.url, active: .active}' 2>&1)

if echo "$WEBHOOKS" | grep -q "cloudbuild\|googleapis\|gcp"; then
    echo "✅ Found Cloud Build webhook(s):"
    echo "$WEBHOOKS" | grep -A 2 -B 2 "cloudbuild\|googleapis\|gcp"
else
    echo "❌ No Cloud Build webhook found"
    echo ""
    echo "⚠️  IMPORTANT: Cloud Build GitHub App webhooks are managed automatically."
    echo "   Manual webhook creation is NOT recommended for Cloud Build triggers."
    echo ""
    echo "🔧 To fix webhook issues:"
    echo "   1. Go to Cloud Console:"
    echo "      https://console.cloud.google.com/cloud-build/triggers?project=${PROJECT_ID}"
    echo "   2. Select region: ${REGION} (top right)"
    echo "   3. Click on trigger 'develop'"
    echo "   4. Click 'Edit'"
    echo "   5. Under 'Source', verify repository connection"
    echo "   6. If connection shows error, click 'Reconnect'"
    echo "   7. Save trigger"
    echo ""
    echo "   This will automatically recreate the webhook."
fi

echo ""
echo "📋 All webhooks:"
gh api repos/${REPO_OWNER}/${REPO_NAME}/hooks --jq '.[] | "  - ID: \(.id) | URL: \(.config.url) | Active: \(.active)"' 2>&1

