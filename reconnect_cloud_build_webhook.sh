#!/bin/bash
set -e

PROJECT_ID="api-ai-blog-writer"
REGION="europe-west9"
TRIGGER_ID="5cabcb18-791d-4082-8871-d7b2c027be27"
CONNECTION_NAME="europe-west9-paris"
REPO_OWNER="tindevelopers"
REPO_NAME="api-blogwriting-python-gcr"

echo "🔧 Cloud Build Webhook Reconnection Script"
echo "=========================================="
echo ""
echo "⚠️  IMPORTANT: Cloud Build uses GitHub App webhooks, not manual webhooks."
echo "   Webhooks are created automatically when repository is connected."
echo ""
echo "📋 Current Status:"
echo "   Project: $PROJECT_ID"
echo "   Region: $REGION"
echo "   Trigger ID: $TRIGGER_ID"
echo "   Connection: $CONNECTION_NAME"
echo ""

# Check connection status
echo "🔍 Checking GitHub connection status..."
CONNECTION_STATUS=$(gcloud builds connections describe "$CONNECTION_NAME" \
  --project="$PROJECT_ID" \
  --region="$REGION" \
  --format="value(installationState.stage)" 2>&1)

echo "   Connection status: $CONNECTION_STATUS"

if [ "$CONNECTION_STATUS" != "COMPLETE" ]; then
    echo "   ⚠️  Connection is not complete. Reconnecting..."
    echo ""
    echo "   To reconnect:"
    echo "   1. Go to Cloud Console:"
    echo "      https://console.cloud.google.com/cloud-build/triggers?project=$PROJECT_ID"
    echo "   2. Select region: $REGION"
    echo "   3. Click on trigger 'develop'"
    echo "   4. Click 'Edit'"
    echo "   5. Under 'Source', click 'Reconnect'"
    echo "   6. Save trigger"
else
    echo "   ✅ Connection is complete"
fi

echo ""
echo "🔍 Checking trigger configuration..."
TRIGGER_CONFIG=$(gcloud builds triggers describe "$TRIGGER_ID" \
  --project="$PROJECT_ID" \
  --region="$REGION" \
  --format="yaml" 2>&1)

echo "   Trigger name: $(echo "$TRIGGER_CONFIG" | grep '^name:' | awk '{print $2}')"
echo "   Branch pattern: $(echo "$TRIGGER_CONFIG" | grep 'branch:' | awk '{print $2}')"
echo "   Repository: $(echo "$TRIGGER_CONFIG" | grep 'repository:' | awk '{print $2}' | cut -d'/' -f6-)"

echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Verify GitHub App Installation:"
echo "   https://github.com/settings/installations"
echo "   Look for 'Google Cloud Build' app"
echo "   Verify it has access to: $REPO_OWNER/$REPO_NAME"
echo ""
echo "2. Reconnect Repository (if webhook missing):"
echo "   https://console.cloud.google.com/cloud-build/triggers?project=$PROJECT_ID"
echo "   - Select region: $REGION"
echo "   - Edit trigger 'develop'"
echo "   - Reconnect repository"
echo ""
echo "3. Test Manual Trigger:"
echo "   gcloud builds triggers run $TRIGGER_ID \\"
echo "     --project=$PROJECT_ID \\"
echo "     --region=$REGION \\"
echo "     --branch=develop"
echo ""
echo "4. Test Automatic Trigger:"
echo "   git commit --allow-empty -m 'test: Verify webhook'"
echo "   git push origin develop"
echo "   # Monitor: gcloud builds list --project=$PROJECT_ID --ongoing"

