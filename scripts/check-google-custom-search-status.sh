#!/bin/bash
# Check Google Custom Search API status in Cloud Run logs

PROJECT_ID="api-ai-blog-writer"
SERVICE_NAME="blog-writer-api-dev"
REGION="europe-west9"

echo "Checking Google Custom Search API status..."
echo ""

# Check recent logs for Google Custom Search initialization
echo "=== Recent Logs ==="
gcloud logging read \
    "resource.type=cloud_run_revision AND resource.labels.service_name=${SERVICE_NAME}" \
    --limit=50 \
    --format="value(timestamp,textPayload)" \
    --project="${PROJECT_ID}" \
    --freshness=1h 2>/dev/null | grep -i "google\|custom\|search\|initialized" | head -10

echo ""
echo "=== Service Status ==="
gcloud run services describe "${SERVICE_NAME}" \
    --region="${REGION}" \
    --project="${PROJECT_ID}" \
    --format="value(status.latestReadyRevisionName,status.url)" 2>/dev/null

echo ""
echo "=== Latest Builds ==="
gcloud builds list \
    --project="${PROJECT_ID}" \
    --limit=3 \
    --format="table(id,status,createTime,source.repoSource.branchName)" 2>/dev/null

echo ""
echo "=== Test API Endpoint ==="
echo "Testing health endpoint..."
curl -s "https://blog-writer-api-dev-kq42l26tuq-od.a.run.app/health" | jq '.' 2>/dev/null || echo "Health check failed"

