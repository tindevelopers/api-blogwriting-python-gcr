#!/bin/bash
echo "=========================================="
echo "Complete Blog Generation Verification Test"
echo "=========================================="
echo ""

API_URL="https://blog-writer-api-dev-kq42l26tuq-od.a.run.app"

echo "1. Testing Health Endpoint..."
curl -s "$API_URL/health" | jq '.' && echo "✅ Health check passed" || echo "❌ Health check failed"
echo ""

echo "2. Testing Async Job Creation..."
JOB_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/blog/generate-enhanced?async_mode=true" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Best Coffee Makers 2025",
    "keywords": ["best coffee makers", "coffee machines"],
    "tone": "professional",
    "length": "short",
    "use_google_search": true,
    "use_fact_checking": false,
    "use_citations": false,
    "use_serp_optimization": false,
    "use_knowledge_graph": false,
    "use_semantic_keywords": false,
    "use_quality_scoring": false
  }')

JOB_ID=$(echo "$JOB_RESPONSE" | jq -r '.job_id')
echo "Job Created: $JOB_ID"
echo "$JOB_RESPONSE" | jq '.'
echo ""

echo "3. Waiting 10 seconds, then checking job status..."
sleep 10
STATUS_RESPONSE=$(curl -s "$API_URL/api/v1/blog/jobs/$JOB_ID")
echo "$STATUS_RESPONSE" | jq '.'
echo ""

echo "4. Checking for progress_updates in response..."
PROGRESS_COUNT=$(echo "$STATUS_RESPONSE" | jq '.progress_updates | length' 2>/dev/null || echo "0")
echo "Progress updates found: $PROGRESS_COUNT"
echo ""

echo "5. Checking for generated_images in result..."
if echo "$STATUS_RESPONSE" | jq -e '.result.generated_images' > /dev/null 2>&1; then
    IMAGE_COUNT=$(echo "$STATUS_RESPONSE" | jq '.result.generated_images | length')
    echo "✅ Generated images found: $IMAGE_COUNT"
    echo "$STATUS_RESPONSE" | jq '.result.generated_images' | head -20
else
    echo "⚠️  No generated_images in result yet (may still be processing)"
fi
echo ""

echo "=========================================="
echo "Test Complete"
echo "=========================================="
