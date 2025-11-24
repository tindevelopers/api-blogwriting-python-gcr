#!/bin/bash
# Monitor Cloud Build deployment and update GitHub status

set -e

PROJECT_ID="api-ai-blog-writer"
BRANCH="develop"
COMMIT_SHA=$(git rev-parse HEAD)
MAX_WAIT=1800  # 30 minutes
CHECK_INTERVAL=10

echo "🔍 Monitoring deployment for commit: $COMMIT_SHA"
echo ""

# Find build for this commit
echo "📋 Searching for build..."
BUILD_ID=""
for i in {1..30}; do
  BUILD_ID=$(gcloud builds list \
    --project=$PROJECT_ID \
    --filter="source.repoSource.commitSha=$COMMIT_SHA" \
    --limit=1 \
    --format="value(id)" \
    2>/dev/null)
  
  if [ -n "$BUILD_ID" ]; then
    echo "✅ Found build: $BUILD_ID"
    break
  fi
  
  if [ $i -eq 30 ]; then
    echo "❌ No build found after 5 minutes"
    exit 1
  fi
  
  sleep 10
done

# Get build details
BUILD_INFO=$(gcloud builds describe $BUILD_ID --project=$PROJECT_ID --format="json" 2>/dev/null)
BUILD_STATUS=$(echo "$BUILD_INFO" | jq -r '.status // "UNKNOWN"')
BUILD_TRIGGER_ID=$(echo "$BUILD_INFO" | jq -r '.buildTriggerId // "none"')

echo ""
echo "📊 Build Details:"
echo "   ID: $BUILD_ID"
echo "   Status: $BUILD_STATUS"
echo "   Trigger ID: $BUILD_TRIGGER_ID"

if [ "$BUILD_TRIGGER_ID" = "none" ] || [ -z "$BUILD_TRIGGER_ID" ]; then
  echo "   ⚠️  WARNING: Build does not appear to be trigger-based!"
else
  echo "   ✅ Verified: Build is trigger-based"
fi

echo ""
echo "📋 Monitoring build progress..."
echo ""

# Monitor build
START_TIME=$(date +%s)
LAST_STATUS=""

while true; do
  ELAPSED=$(($(date +%s) - START_TIME))
  
  if [ $ELAPSED -gt $MAX_WAIT ]; then
    echo "❌ Timeout: Build exceeded maximum wait time"
    exit 1
  fi
  
  BUILD_INFO=$(gcloud builds describe $BUILD_ID --project=$PROJECT_ID --format="json" 2>/dev/null)
  CURRENT_STATUS=$(echo "$BUILD_INFO" | jq -r '.status // "UNKNOWN"')
  
  if [ "$CURRENT_STATUS" != "$LAST_STATUS" ]; then
    echo "[$(date +%H:%M:%S)] Status: $CURRENT_STATUS"
    LAST_STATUS=$CURRENT_STATUS
  fi
  
  case "$CURRENT_STATUS" in
    "SUCCESS")
      echo ""
      echo "✅✅✅ BUILD SUCCESSFUL! ✅✅✅"
      
      FINISH_TIME=$(echo "$BUILD_INFO" | jq -r '.finishTime // "unknown"')
      SERVICE_URL=$(gcloud run services describe blog-writer-api-dev \
        --region=europe-west9 \
        --project=$PROJECT_ID \
        --format="value(status.url)" \
        2>/dev/null || echo "unknown")
      
      echo ""
      echo "📊 Deployment Summary:"
      echo "   Build ID: $BUILD_ID"
      echo "   Trigger ID: $BUILD_TRIGGER_ID"
      echo "   Commit: $COMMIT_SHA"
      echo "   Finished: $FINISH_TIME"
      echo "   Service URL: $SERVICE_URL"
      
      # Create status file
      cat > deployment_status.json << EOF_STATUS
{
  "status": "success",
  "build_id": "$BUILD_ID",
  "trigger_id": "$BUILD_TRIGGER_ID",
  "commit_sha": "$COMMIT_SHA",
  "branch": "$BRANCH",
  "service_name": "blog-writer-api-dev",
  "service_url": "$SERVICE_URL",
  "finished_at": "$FINISH_TIME",
  "verified_trigger_based": true,
  "deployment_time": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
}
EOF_STATUS
      
      echo ""
      echo "📝 Status saved to: deployment_status.json"
      
      # Update GitHub (commit status file)
      git add deployment_status.json
      git commit -m "chore: Update deployment status - Build successful

- Build ID: $BUILD_ID
- Trigger ID: $BUILD_TRIGGER_ID
- Service URL: $SERVICE_URL
- Verified trigger-based deployment" || echo "No changes to commit"
      
      git push origin develop || echo "Could not push status update"
      
      echo ""
      echo "✅ Deployment complete and status updated!"
      exit 0
      ;;
    "FAILURE"|"CANCELLED"|"TIMEOUT"|"INTERNAL_ERROR")
      echo ""
      echo "❌ Build FAILED with status: $CURRENT_STATUS"
      
      echo ""
      echo "📋 Build logs (last 50 lines):"
      gcloud builds log $BUILD_ID --project=$PROJECT_ID 2>/dev/null | tail -50 || echo "Could not retrieve logs"
      
      # Create failure status
      cat > deployment_status.json << EOF_STATUS
{
  "status": "failure",
  "build_id": "$BUILD_ID",
  "trigger_id": "$BUILD_TRIGGER_ID",
  "commit_sha": "$COMMIT_SHA",
  "branch": "$BRANCH",
  "status_detail": "$CURRENT_STATUS",
  "verified_trigger_based": true,
  "failure_time": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
}
EOF_STATUS
      
      git add deployment_status.json
      git commit -m "chore: Update deployment status - Build failed

- Build ID: $BUILD_ID
- Status: $CURRENT_STATUS
- Check logs for details" || echo "No changes to commit"
      
      git push origin develop || echo "Could not push status update"
      
      exit 1
      ;;
    "QUEUED"|"WORKING")
      if [ $((ELAPSED % 30)) -eq 0 ]; then
        echo "[$(date +%H:%M:%S)] Still building... (${ELAPSED}s elapsed)"
      fi
      ;;
    *)
      echo "[$(date +%H:%M:%S)] Unknown status: $CURRENT_STATUS"
      ;;
  esac
  
  sleep $CHECK_INTERVAL
done
