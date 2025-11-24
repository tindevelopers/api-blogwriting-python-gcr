#!/bin/bash
# Check for new builds and monitor deployment

PROJECT_ID="api-ai-blog-writer"
BRANCH="develop"
COMMIT_SHA=$(git rev-parse HEAD)

echo "🔍 Checking for builds triggered by latest commit..."
echo "   Commit: $COMMIT_SHA"
echo "   Branch: $BRANCH"
echo ""

# Check if there's a build for this commit
BUILD_ID=$(gcloud builds list \
  --project=$PROJECT_ID \
  --filter="source.repoSource.commitSha=$COMMIT_SHA" \
  --limit=1 \
  --format="value(id)" \
  2>/dev/null)

if [ -z "$BUILD_ID" ]; then
  echo "⏳ No build found for commit $COMMIT_SHA"
  echo "   This might mean:"
  echo "   1. The trigger hasn't fired yet (can take 1-2 minutes)"
  echo "   2. The trigger is disabled"
  echo "   3. The trigger configuration needs to be checked"
  echo ""
  echo "📋 Checking trigger status..."
  
  TRIGGER_STATUS=$(gcloud builds triggers list \
    --project=$PROJECT_ID \
    --filter="name:deploy-dev-on-develop" \
    --format="value(disabled)" \
    2>/dev/null)
  
  if [ "$TRIGGER_STATUS" = "True" ]; then
    echo "❌ Trigger 'deploy-dev-on-develop' is DISABLED"
    echo "   Please enable it in Cloud Console or via CLI"
  else
    echo "✅ Trigger appears to be enabled"
    echo "   Waiting for trigger to fire..."
    
    # Wait up to 2 minutes for trigger to fire
    for i in {1..24}; do
      sleep 5
      BUILD_ID=$(gcloud builds list \
        --project=$PROJECT_ID \
        --filter="source.repoSource.commitSha=$COMMIT_SHA" \
        --limit=1 \
        --format="value(id)" \
        2>/dev/null)
      
      if [ -n "$BUILD_ID" ]; then
        echo "✅ Build started: $BUILD_ID"
        break
      fi
      
      if [ $i -eq 24 ]; then
        echo "❌ No build started after 2 minutes"
        echo "   Please check trigger configuration manually"
        exit 1
      fi
    done
  fi
else
  echo "✅ Found build: $BUILD_ID"
fi

# Now monitor the build
if [ -n "$BUILD_ID" ]; then
  echo ""
  echo "📊 Monitoring build: $BUILD_ID"
  echo ""
  
  # Get build details
  BUILD_INFO=$(gcloud builds describe $BUILD_ID --project=$PROJECT_ID --format="json" 2>/dev/null)
  BUILD_STATUS=$(echo "$BUILD_INFO" | jq -r '.status // "UNKNOWN"')
  BUILD_TRIGGER_ID=$(echo "$BUILD_INFO" | jq -r '.buildTriggerId // "none"')
  
  echo "   Status: $BUILD_STATUS"
  echo "   Trigger ID: $BUILD_TRIGGER_ID"
  
  if [ "$BUILD_TRIGGER_ID" = "none" ] || [ -z "$BUILD_TRIGGER_ID" ]; then
    echo "   ⚠️  WARNING: This build does not appear to be trigger-based!"
  else
    echo "   ✅ Verified: Build is trigger-based"
  fi
  
  # Monitor until completion
  while [ "$BUILD_STATUS" != "SUCCESS" ] && [ "$BUILD_STATUS" != "FAILURE" ] && [ "$BUILD_STATUS" != "CANCELLED" ] && [ "$BUILD_STATUS" != "TIMEOUT" ]; do
    sleep 10
    BUILD_INFO=$(gcloud builds describe $BUILD_ID --project=$PROJECT_ID --format="json" 2>/dev/null)
    NEW_STATUS=$(echo "$BUILD_INFO" | jq -r '.status // "UNKNOWN"')
    
    if [ "$NEW_STATUS" != "$BUILD_STATUS" ]; then
      BUILD_STATUS=$NEW_STATUS
      echo "[$(date +%H:%M:%S)] Status changed to: $BUILD_STATUS"
    fi
  done
  
  echo ""
  if [ "$BUILD_STATUS" = "SUCCESS" ]; then
    echo "✅ Build SUCCESSFUL!"
    
    # Get service URL
    SERVICE_URL=$(gcloud run services describe blog-writer-api-dev \
      --region=europe-west9 \
      --project=$PROJECT_ID \
      --format="value(status.url)" \
      2>/dev/null || echo "unknown")
    
    echo "   Service URL: $SERVICE_URL"
    
    # Create status file
    cat > deployment_status.json << EOF_STATUS
{
  "status": "success",
  "build_id": "$BUILD_ID",
  "trigger_id": "$BUILD_TRIGGER_ID",
  "commit_sha": "$COMMIT_SHA",
  "branch": "$BRANCH",
  "service_url": "$SERVICE_URL",
  "verified_trigger_based": true
}
EOF_STATUS
    
    exit 0
  else
    echo "❌ Build FAILED with status: $BUILD_STATUS"
    
    # Get error details
    echo ""
    echo "📋 Error details:"
    gcloud builds log $BUILD_ID --project=$PROJECT_ID 2>/dev/null | tail -30
    
    exit 1
  fi
fi
