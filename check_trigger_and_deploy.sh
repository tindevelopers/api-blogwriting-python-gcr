#!/bin/bash
# Check trigger status and create a deployment update

PROJECT_ID="api-ai-blog-writer"
COMMIT_SHA=$(git rev-parse HEAD)

echo "🔍 Checking Cloud Build Trigger Status"
echo ""

# List all triggers
echo "📋 Available triggers:"
gcloud builds triggers list --project=$PROJECT_ID --format="table(name,github.push.branch,filename,disabled)" 2>&1 | head -10

echo ""
echo "📊 Recent builds:"
gcloud builds list --project=$PROJECT_ID --limit=3 --format="table(id,status,createTime,source.repoSource.branchName)" 2>&1 | head -5

echo ""
echo "🔍 Checking for build with commit: ${COMMIT_SHA:0:7}..."
BUILD_FOUND=$(gcloud builds list \
  --project=$PROJECT_ID \
  --filter="source.repoSource.commitSha=$COMMIT_SHA" \
  --limit=1 \
  --format="value(id)" \
  2>/dev/null)

if [ -n "$BUILD_FOUND" ]; then
  echo "✅ Build found: $BUILD_FOUND"
  
  BUILD_INFO=$(gcloud builds describe $BUILD_FOUND --project=$PROJECT_ID --format="json" 2>/dev/null)
  STATUS=$(echo "$BUILD_INFO" | jq -r '.status')
  TRIGGER_ID=$(echo "$BUILD_INFO" | jq -r '.buildTriggerId // "none"')
  
  echo "   Status: $STATUS"
  echo "   Trigger ID: $TRIGGER_ID"
  
  if [ "$STATUS" = "SUCCESS" ]; then
    echo ""
    echo "✅✅✅ Deployment Successful! ✅✅✅"
    
    SERVICE_URL=$(gcloud run services describe blog-writer-api-dev \
      --region=europe-west9 \
      --project=$PROJECT_ID \
      --format="value(status.url)" \
      2>/dev/null || echo "unknown")
    
    cat > deployment_status.json << EOF_STATUS
{
  "status": "success",
  "build_id": "$BUILD_FOUND",
  "trigger_id": "$TRIGGER_ID",
  "commit_sha": "$COMMIT_SHA",
  "service_url": "$SERVICE_URL",
  "deployed_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
}
EOF_STATUS
    
    git add deployment_status.json
    git commit -m "chore: Deployment successful - Build $BUILD_FOUND" && git push origin develop
    
    echo "   Service URL: $SERVICE_URL"
    exit 0
  elif [ "$STATUS" = "FAILURE" ] || [ "$STATUS" = "CANCELLED" ]; then
    echo ""
    echo "❌ Build failed: $STATUS"
    echo "📋 Last 20 lines of logs:"
    gcloud builds log $BUILD_FOUND --project=$PROJECT_ID 2>/dev/null | tail -20
    exit 1
  else
    echo ""
    echo "⏳ Build in progress: $STATUS"
    echo "   Monitor with: gcloud builds log $BUILD_FOUND --project=$PROJECT_ID --stream"
    exit 2
  fi
else
  echo "⏳ No build found yet for this commit"
  echo ""
  echo "💡 If trigger is configured, it should fire within 1-2 minutes"
  echo "   Monitor with: gcloud builds list --project=$PROJECT_ID --ongoing"
  exit 2
fi
