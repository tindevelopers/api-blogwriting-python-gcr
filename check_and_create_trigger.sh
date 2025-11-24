#!/bin/bash
set -e

PROJECT_ID="api-ai-blog-writer"
TRIGGER_NAME="deploy-dev-on-develop"
REPO_OWNER="tindevelopers"
REPO_NAME="api-blogwriting-python-gcr"
BRANCH_PATTERN="^develop$"

echo "🔍 Checking for existing trigger: $TRIGGER_NAME"
EXISTING_TRIGGER=$(gcloud builds triggers list --project=$PROJECT_ID --format="value(name)" 2>&1 | grep -i "$TRIGGER_NAME" || echo "")

if [ -n "$EXISTING_TRIGGER" ]; then
    echo "✅ Trigger '$TRIGGER_NAME' exists"
    echo ""
    echo "📋 Trigger details:"
    gcloud builds triggers describe "$TRIGGER_NAME" --project=$PROJECT_ID --format="yaml" 2>&1 | head -30
    echo ""
    echo "🔍 Checking if trigger is enabled..."
    DISABLED=$(gcloud builds triggers describe "$TRIGGER_NAME" --project=$PROJECT_ID --format="value(disabled)" 2>&1)
    if [ "$DISABLED" = "True" ]; then
        echo "⚠️  Trigger is DISABLED - enabling it..."
        gcloud builds triggers update "$TRIGGER_NAME" --enable --project=$PROJECT_ID 2>&1
        echo "✅ Trigger enabled"
    else
        echo "✅ Trigger is enabled"
    fi
else
    echo "❌ Trigger '$TRIGGER_NAME' not found"
    echo ""
    echo "💡 To create trigger, you can use Cloud Console:"
    echo "   https://console.cloud.google.com/cloud-build/triggers/add?project=$PROJECT_ID"
    echo ""
    echo "   Or use gcloud CLI (may require GitHub connection setup):"
    echo "   gcloud builds triggers create github \\"
    echo "     --name=$TRIGGER_NAME \\"
    echo "     --repo-name=$REPO_NAME \\"
    echo "     --repo-owner=$REPO_OWNER \\"
    echo "     --branch-pattern='$BRANCH_PATTERN' \\"
    echo "     --build-config=cloudbuild.yaml \\"
    echo "     --substitutions=_REGION=europe-west9,_ENV=dev,_SERVICE_NAME=blog-writer-api-dev \\"
    echo "     --project=$PROJECT_ID"
fi
