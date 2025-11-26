#!/bin/bash
# Script to recreate Cloud Tasks queue after cooldown period
# Google Cloud has a ~10-15 minute cooldown after queue deletion

set -e

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-${GCP_PROJECT_ID}}"
QUEUE_NAME="${CLOUD_TASKS_QUEUE_NAME:-blog-generation-queue}"
LOCATION="${CLOUD_TASKS_QUEUE_LOCATION:-europe-west1}"

if [ -z "$PROJECT_ID" ]; then
    echo "❌ Error: GOOGLE_CLOUD_PROJECT or GCP_PROJECT_ID must be set"
    exit 1
fi

echo "🔄 Recreating Cloud Tasks Queue"
echo "   Project: $PROJECT_ID"
echo "   Location: $LOCATION"
echo "   Queue: $QUEUE_NAME"
echo ""

# Try to create the queue
echo "Attempting to create queue..."
if gcloud tasks queues create "$QUEUE_NAME" \
  --location="$LOCATION" \
  --max-dispatches-per-second=100 \
  --max-concurrent-dispatches=500 \
  --max-retry-duration=3600s \
  --project="$PROJECT_ID" 2>&1; then
    echo "✅ Queue created successfully!"
    echo ""
    echo "Waiting 30 seconds for queue to initialize..."
    sleep 30
    
    echo "Verifying queue..."
    gcloud tasks queues describe "$QUEUE_NAME" \
      --location="$LOCATION" \
      --format="table(name,state,rateLimits.maxDispatchesPerSecond)"
    
    echo ""
    echo "✅ Queue is ready!"
    echo ""
    echo "You can now test async blog generation:"
    echo "  curl -X POST 'https://blog-writer-api-dev-kq42l26tuq-od.a.run.app/api/v1/blog/generate-enhanced?async_mode=true' \\"
    echo "    -H 'Content-Type: application/json' \\"
    echo "    -d '{\"topic\":\"Test\",\"keywords\":[\"test\"],\"use_google_search\":false}'"
else
    echo ""
    echo "⚠️  Queue creation failed - likely still in cooldown period"
    echo ""
    echo "Google Cloud has a cooldown period (~10-15 minutes) after queue deletion."
    echo "Please wait and try again, or check the error message above."
    echo ""
    echo "To check when you can recreate:"
    echo "  gcloud tasks queues list --location=$LOCATION"
    echo ""
    echo "You can also check Cloud Console:"
    echo "  https://console.cloud.google.com/cloudtasks/queue/list?project=$PROJECT_ID"
fi


