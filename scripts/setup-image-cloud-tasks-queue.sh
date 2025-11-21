#!/bin/bash
# Setup Cloud Tasks queue for image generation
# Follows the same pattern as blog generation queue setup

set -e

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-${GCP_PROJECT_ID}}"
# Cloud Tasks queue location (must be a valid Cloud Tasks region)
# Note: Queue can be in different region than Cloud Run service
# Using europe-west1 as it's closest to europe-west9 and is a valid Cloud Tasks location
LOCATION="${CLOUD_TASKS_QUEUE_LOCATION:-europe-west1}"
QUEUE_NAME="${CLOUD_TASKS_IMAGE_QUEUE_NAME:-image-generation-queue}"

if [ -z "$PROJECT_ID" ]; then
    echo "❌ Error: GOOGLE_CLOUD_PROJECT or GCP_PROJECT_ID must be set"
    exit 1
fi

echo "🚀 Setting up Cloud Tasks queue for image generation"
echo "   Project: $PROJECT_ID"
echo "   Location: $LOCATION"
echo "   Queue: $QUEUE_NAME"
echo ""

# Create Cloud Tasks queue
echo "Creating Cloud Tasks queue..."
gcloud tasks queues create "$QUEUE_NAME" \
  --location="$LOCATION" \
  --max-dispatches-per-second=200 \
  --max-concurrent-dispatches=1000 \
  --max-retry-duration=1800s \
  --project="$PROJECT_ID" \
  2>&1 | grep -v "already exists" || echo "✅ Queue already exists"

echo ""
echo "✅ Cloud Tasks queue setup complete!"
echo ""
echo "Queue configuration:"
echo "  - Max dispatches per second: 200 (higher than blog queue for faster image processing)"
echo "  - Max concurrent dispatches: 1000 (higher than blog queue for batch operations)"
echo "  - Max retry duration: 30 minutes (shorter than blog queue, images are faster)"
echo ""
echo "Environment variables to set:"
echo "  - CLOUD_TASKS_IMAGE_QUEUE_NAME=$QUEUE_NAME"
echo "  - CLOUD_TASKS_QUEUE_LOCATION=$LOCATION"
echo "  - GOOGLE_CLOUD_PROJECT=$PROJECT_ID"
echo ""
echo "Next steps:"
echo "  1. Set environment variables in Cloud Run secrets"
echo "  2. Deploy updated service"
echo "  3. Test async image generation endpoints"
echo "  4. Monitor queue depth in Cloud Console"



