#!/bin/bash
# Setup Cloud Tasks queue for blog generation

set -e

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-${GCP_PROJECT_ID}}"
LOCATION="${GCP_LOCATION:-europe-west1}"
QUEUE_NAME="${CLOUD_TASKS_QUEUE_NAME:-blog-generation-queue}"

if [ -z "$PROJECT_ID" ]; then
    echo "❌ Error: GOOGLE_CLOUD_PROJECT or GCP_PROJECT_ID must be set"
    exit 1
fi

echo "🚀 Setting up Cloud Tasks queue for blog generation"
echo "   Project: $PROJECT_ID"
echo "   Location: $LOCATION"
echo "   Queue: $QUEUE_NAME"

# Create Cloud Tasks queue
gcloud tasks queues create "$QUEUE_NAME" \
  --location="$LOCATION" \
  --max-dispatches-per-second=100 \
  --max-concurrent-dispatches=500 \
  --max-retry-duration=3600s \
  --project="$PROJECT_ID" \
  2>&1 | grep -v "already exists" || echo "✅ Queue already exists"

echo "✅ Cloud Tasks queue setup complete!"
echo ""
echo "Queue configuration:"
echo "  - Max dispatches per second: 100"
echo "  - Max concurrent dispatches: 500"
echo "  - Max retry duration: 1 hour"
echo ""
echo "Next steps:"
echo "  1. Update your API to use Cloud Tasks service"
echo "  2. Deploy worker service to handle tasks"
echo "  3. Monitor queue depth in Cloud Console"

