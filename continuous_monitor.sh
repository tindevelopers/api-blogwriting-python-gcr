#!/bin/bash
# Continuously monitor for new builds and track deployment

PROJECT_ID="api-ai-blog-writer"
BRANCH="develop"
COMMIT_SHA=$(git rev-parse HEAD)
LAST_BUILD_ID=""

echo "🔍 Continuous Monitoring Mode"
echo "   Commit: $COMMIT_SHA"
echo "   Branch: $BRANCH"
echo "   Monitoring for new builds..."
echo ""

while true; do
  # Check for new builds
  CURRENT_BUILD=$(gcloud builds list \
    --project=$PROJECT_ID \
    --filter="source.repoSource.commitSha=$COMMIT_SHA" \
    --limit=1 \
    --format="value(id)" \
    2>/dev/null)
  
  if [ -n "$CURRENT_BUILD" ] && [ "$CURRENT_BUILD" != "$LAST_BUILD_ID" ]; then
    echo "[$(date +%H:%M:%S)] ✅ New build detected: $CURRENT_BUILD"
    LAST_BUILD_ID=$CURRENT_BUILD
    
    # Get build info
    BUILD_INFO=$(gcloud builds describe $CURRENT_BUILD --project=$PROJECT_ID --format="json" 2>/dev/null)
    BUILD_STATUS=$(echo "$BUILD_INFO" | jq -r '.status // "UNKNOWN"')
    BUILD_TRIGGER_ID=$(echo "$BUILD_INFO" | jq -r '.buildTriggerId // "none"')
    
    echo "   Status: $BUILD_STATUS"
    echo "   Trigger ID: $BUILD_TRIGGER_ID"
    
    if [ "$BUILD_TRIGGER_ID" != "none" ] && [ -n "$BUILD_TRIGGER_ID" ]; then
      echo "   ✅ Verified trigger-based build"
    fi
    
    # Monitor this build
    echo ""
    echo "📊 Monitoring build: $CURRENT_BUILD"
    
    while [ "$BUILD_STATUS" != "SUCCESS" ] && [ "$BUILD_STATUS" != "FAILURE" ] && [ "$BUILD_STATUS" != "CANCELLED" ]; do
      sleep 15
      BUILD_INFO=$(gcloud builds describe $CURRENT_BUILD --project=$PROJECT_ID --format="json" 2>/dev/null)
      NEW_STATUS=$(echo "$BUILD_INFO" | jq -r '.status // "UNKNOWN"')
      
      if [ "$NEW_STATUS" != "$BUILD_STATUS" ]; then
        BUILD_STATUS=$NEW_STATUS
        echo "[$(date +%H:%M:%S)] Status: $BUILD_STATUS"
      fi
    done
    
    if [ "$BUILD_STATUS" = "SUCCESS" ]; then
      echo ""
      echo "✅✅✅ BUILD SUCCESSFUL! ✅✅✅"
      
      SERVICE_URL=$(gcloud run services describe blog-writer-api-dev \
        --region=europe-west9 \
        --project=$PROJECT_ID \
        --format="value(status.url)" \
        2>/dev/null || echo "unknown")
      
      cat > deployment_status.json << EOF_STATUS
{
  "status": "success",
  "build_id": "$CURRENT_BUILD",
  "trigger_id": "$BUILD_TRIGGER_ID",
  "commit_sha": "$COMMIT_SHA",
  "service_url": "$SERVICE_URL",
  "deployed_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
}
EOF_STATUS
      
      git add deployment_status.json
      git commit -m "chore: Deployment successful - $CURRENT_BUILD" && git push origin develop || echo "Status update skipped"
      
      echo "   Service URL: $SERVICE_URL"
      echo "   Status saved to deployment_status.json"
      exit 0
    else
      echo ""
      echo "❌ Build failed: $BUILD_STATUS"
      echo "📋 Logs:"
      gcloud builds log $CURRENT_BUILD --project=$PROJECT_ID 2>/dev/null | tail -30
      exit 1
    fi
  fi
  
  # Also check for any recent builds on develop branch
  RECENT_BUILD=$(gcloud builds list \
    --project=$PROJECT_ID \
    --filter="source.repoSource.branchName=$BRANCH" \
    --limit=1 \
    --format="value(id)" \
    2>/dev/null)
  
  if [ -n "$RECENT_BUILD" ] && [ "$RECENT_BUILD" != "$LAST_BUILD_ID" ]; then
    BUILD_TIME=$(gcloud builds describe $RECENT_BUILD --project=$PROJECT_ID --format="value(createTime)" 2>/dev/null)
    BUILD_TIME_EPOCH=$(date -d "$BUILD_TIME" +%s 2>/dev/null || date -j -f "%Y-%m-%dT%H:%M:%S" "${BUILD_TIME%Z}" +%s 2>/dev/null || echo "0")
    CURRENT_TIME=$(date +%s)
    TIME_DIFF=$((CURRENT_TIME - BUILD_TIME_EPOCH))
    
    # If build is less than 5 minutes old, it might be our build
    if [ $TIME_DIFF -lt 300 ]; then
      echo "[$(date +%H:%M:%S)] ⚠️  Recent build found: $RECENT_BUILD (${TIME_DIFF}s ago)"
      echo "   Checking if it matches our commit..."
      
      BUILD_COMMIT=$(gcloud builds describe $RECENT_BUILD --project=$PROJECT_ID --format="value(source.repoSource.commitSha)" 2>/dev/null)
      if [ "$BUILD_COMMIT" = "$COMMIT_SHA" ]; then
        echo "   ✅ Matches our commit! Monitoring..."
        LAST_BUILD_ID=$RECENT_BUILD
        continue
      fi
    fi
  fi
  
  echo -n "."
  sleep 10
done
