#!/bin/bash
# Monitor Cloud Build trigger from GitHub push

echo "🔍 Monitoring Cloud Build for develop branch..."
echo ""

for i in {1..30}; do
  BUILD_ID=$(gcloud builds list --limit=1 --format="value(id)" --filter="source.repoSource.branchName=develop" --sort-by=~createTime 2>/dev/null)
  
  if [ -z "$BUILD_ID" ]; then
    echo "$(date '+%H:%M:%S') - Waiting for build to appear..."
    sleep 10
    continue
  fi
  
  STATUS=$(gcloud builds describe $BUILD_ID --format="value(status)" 2>/dev/null)
  CREATE_TIME=$(gcloud builds describe $BUILD_ID --format="value(createTime.time().seconds())" 2>/dev/null)
  CURRENT_TIME=$(date +%s)
  AGE=$((CURRENT_TIME - CREATE_TIME))
  
  # Only show builds from last 10 minutes
  if [ $AGE -gt 600 ]; then
    echo "$(date '+%H:%M:%S') - No recent build found. Waiting..."
    sleep 10
    continue
  fi
  
  echo "$(date '+%H:%M:%S') - Build $BUILD_ID: $STATUS (age: ${AGE}s)"
  
  if [ "$STATUS" = "SUCCESS" ]; then
    echo ""
    echo "✅ Build successful!"
    echo "Build ID: $BUILD_ID"
    echo ""
    echo "Testing deployed service..."
    break
  elif [ "$STATUS" = "FAILURE" ] || [ "$STATUS" = "CANCELLED" ] || [ "$STATUS" = "TIMEOUT" ]; then
    echo ""
    echo "❌ Build failed with status: $STATUS"
    echo "Build ID: $BUILD_ID"
    echo ""
    echo "Last 30 lines of build log:"
    gcloud builds log $BUILD_ID 2>&1 | tail -30
    break
  fi
  
  sleep 15
done

