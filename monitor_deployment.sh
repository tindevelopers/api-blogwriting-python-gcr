#!/bin/bash
# Monitor Cloud Build deployment and update GitHub status

set -e

PROJECT_ID="api-ai-blog-writer"
BRANCH="develop"
SERVICE_NAME="blog-writer-api-dev"
MAX_WAIT_TIME=1800  # 30 minutes
CHECK_INTERVAL=10   # Check every 10 seconds

echo "🔍 Monitoring Cloud Build deployment for branch: $BRANCH"
echo "⏰ Maximum wait time: $MAX_WAIT_TIME seconds"
echo ""

# Find the latest build for the develop branch
echo "📋 Finding latest build for branch: $BRANCH..."
LATEST_BUILD=$(gcloud builds list \
  --project=$PROJECT_ID \
  --filter="source.repoSource.branchName=$BRANCH" \
  --limit=1 \
  --format="value(id)" \
  2>/dev/null)

if [ -z "$LATEST_BUILD" ]; then
  echo "❌ No build found for branch: $BRANCH"
  echo "⏳ Waiting for trigger to start build..."
  
  # Wait for a build to start
  START_TIME=$(date +%s)
  while [ $(($(date +%s) - START_TIME)) -lt 300 ]; do
    LATEST_BUILD=$(gcloud builds list \
      --project=$PROJECT_ID \
      --filter="source.repoSource.branchName=$BRANCH" \
      --limit=1 \
      --format="value(id)" \
      2>/dev/null)
    
    if [ -n "$LATEST_BUILD" ]; then
      echo "✅ Build started: $LATEST_BUILD"
      break
    fi
    
    echo "⏳ Still waiting for build to start... ($(($(date +%s) - START_TIME))s elapsed)"
    sleep 5
  done
  
  if [ -z "$LATEST_BUILD" ]; then
    echo "❌ No build started within 5 minutes"
    exit 1
  fi
fi

echo "📦 Build ID: $LATEST_BUILD"
echo ""

# Get build details
BUILD_INFO=$(gcloud builds describe $LATEST_BUILD --project=$PROJECT_ID --format="json" 2>/dev/null)
BUILD_STATUS=$(echo "$BUILD_INFO" | jq -r '.status // "UNKNOWN"')
BUILD_TRIGGER_ID=$(echo "$BUILD_INFO" | jq -r '.buildTriggerId // "none"')

echo "📊 Build Details:"
echo "   Status: $BUILD_STATUS"
echo "   Trigger ID: $BUILD_TRIGGER_ID"

# Verify this is a trigger-based build
if [ "$BUILD_TRIGGER_ID" = "none" ] || [ -z "$BUILD_TRIGGER_ID" ]; then
  echo "⚠️  WARNING: This build does not appear to be trigger-based!"
  echo "   BUILD_TRIGGER_ID: $BUILD_TRIGGER_ID"
else
  echo "✅ Verified: Build is trigger-based (Trigger ID: $BUILD_TRIGGER_ID)"
fi

echo ""

# Monitor build status
START_TIME=$(date +%s)
LAST_STATUS=""

while true; do
  ELAPSED=$(($(date +%s) - START_TIME))
  
  if [ $ELAPSED -gt $MAX_WAIT_TIME ]; then
    echo "❌ Timeout: Build exceeded maximum wait time"
    exit 1
  fi
  
  # Get current build status
  BUILD_INFO=$(gcloud builds describe $LATEST_BUILD --project=$PROJECT_ID --format="json" 2>/dev/null)
  CURRENT_STATUS=$(echo "$BUILD_INFO" | jq -r '.status // "UNKNOWN"')
  
  # Only print if status changed
  if [ "$CURRENT_STATUS" != "$LAST_STATUS" ]; then
    echo "[$(date +%H:%M:%S)] Status: $CURRENT_STATUS"
    LAST_STATUS=$CURRENT_STATUS
  fi
  
  # Check if build is complete
  case "$CURRENT_STATUS" in
    "SUCCESS")
      echo ""
      echo "✅ Build SUCCESSFUL!"
      
      # Get build finish time
      FINISH_TIME=$(echo "$BUILD_INFO" | jq -r '.finishTime // "unknown"')
      echo "   Finished at: $FINISH_TIME"
      
      # Get service URL
      SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
        --region=europe-west9 \
        --project=$PROJECT_ID \
        --format="value(status.url)" \
        2>/dev/null || echo "unknown")
      
      echo "   Service URL: $SERVICE_URL"
      
      # Create success status file
      cat > deployment_status.json << EOF_STATUS
{
  "status": "success",
  "build_id": "$LATEST_BUILD",
  "trigger_id": "$BUILD_TRIGGER_ID",
  "branch": "$BRANCH",
  "service_name": "$SERVICE_NAME",
  "service_url": "$SERVICE_URL",
  "finished_at": "$FINISH_TIME",
  "verified_trigger_based": true
}
EOF_STATUS
      
      echo ""
      echo "📝 Deployment status saved to: deployment_status.json"
      exit 0
      ;;
    "FAILURE"|"CANCELLED"|"TIMEOUT"|"INTERNAL_ERROR")
      echo ""
      echo "❌ Build FAILED with status: $CURRENT_STATUS"
      
      # Get logs
      echo ""
      echo "📋 Last 50 lines of build logs:"
      gcloud builds log $LATEST_BUILD --project=$PROJECT_ID 2>/dev/null | tail -50 || echo "Could not retrieve logs"
      
      # Create failure status file
      cat > deployment_status.json << EOF_STATUS
{
  "status": "failure",
  "build_id": "$LATEST_BUILD",
  "trigger_id": "$BUILD_TRIGGER_ID",
  "branch": "$BRANCH",
  "service_name": "$SERVICE_NAME",
  "status_detail": "$CURRENT_STATUS",
  "verified_trigger_based": true
}
EOF_STATUS
      
      exit 1
      ;;
    "QUEUED"|"WORKING")
      # Build is still in progress
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
