#!/bin/bash
# Check latest Cloud Run logs for Google Custom Search status

PROJECT_ID="api-ai-blog-writer"
SERVICE_NAME="blog-writer-api-dev"
LATEST_REVISION=$(gcloud run revisions list --service="${SERVICE_NAME}" --region=europe-west9 --project="${PROJECT_ID}" --limit=1 --format="value(name)" 2>/dev/null)

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Cloud Run Logs - Google Custom Search Status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Service: ${SERVICE_NAME}"
echo "Latest Revision: ${LATEST_REVISION}"
echo ""

echo "=== Initialization Logs ==="
gcloud logging read \
    "resource.type=cloud_run_revision AND resource.labels.service_name=${SERVICE_NAME} AND resource.labels.revision_name=${LATEST_REVISION}" \
    --limit=100 \
    --format="value(timestamp,textPayload)" \
    --project="${PROJECT_ID}" \
    --freshness=1h 2>/dev/null | grep -E "Google Custom Search|initialized|✅|⚠️|DataForSEO|Anthropic|OpenAI" | head -20

echo ""
echo "=== Recent Activity ==="
gcloud logging read \
    "resource.type=cloud_run_revision AND resource.labels.service_name=${SERVICE_NAME}" \
    --limit=10 \
    --format="table(timestamp,textPayload)" \
    --project="${PROJECT_ID}" \
    --freshness=30m 2>/dev/null | head -15

echo ""
echo "View full logs: https://cloudlogging.app.goo.gl/9P4nXoqzg9ysBfu76"

