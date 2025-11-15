#!/bin/bash
# Test script for deployed enhanced endpoint

SERVICE_URL="https://blog-writer-api-dev-613248238610.europe-west1.run.app"
ENDPOINT="/api/v1/blog/generate-enhanced"
TEST_FILE="test_notary_california.json"
OUTPUT_FILE="test_deployed_response.json"

echo "=========================================="
echo "Testing Enhanced Blog Generation Endpoint"
echo "=========================================="
echo ""
echo "Service: $SERVICE_URL"
echo "Endpoint: $ENDPOINT"
echo "Test File: $TEST_FILE"
echo ""
echo "Sending request (this may take 60-120 seconds)..."
echo ""

# Make the request and save to file
START_TIME=$(date +%s)
HTTP_CODE=$(curl -X POST "$SERVICE_URL$ENDPOINT" \
  -H 'Content-Type: application/json' \
  -d @"$TEST_FILE" \
  -w "%{http_code}" \
  -o "$OUTPUT_FILE" \
  -s \
  --max-time 180)

END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))

echo ""
echo "=========================================="
echo "Response Summary"
echo "=========================================="
echo "HTTP Status: $HTTP_CODE"
echo "Time Elapsed: ${ELAPSED}s"
echo ""

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ SUCCESS!"
    echo ""
    echo "Response Preview:"
    if command -v jq &> /dev/null; then
        jq -r '.title, .seo_score, .readability_score, .quality_score, .total_tokens, .total_cost, .generation_time' "$OUTPUT_FILE" 2>/dev/null | head -10
    else
        head -50 "$OUTPUT_FILE"
    fi
    echo ""
    echo "Full response saved to: $OUTPUT_FILE"
elif [ "$HTTP_CODE" = "500" ]; then
    echo "❌ SERVER ERROR"
    echo ""
    echo "Error Details:"
    if command -v jq &> /dev/null; then
        jq '.' "$OUTPUT_FILE" 2>/dev/null
    else
        cat "$OUTPUT_FILE"
    fi
else
    echo "⚠️  Unexpected Status: $HTTP_CODE"
    echo ""
    echo "Response:"
    cat "$OUTPUT_FILE"
fi

echo ""
echo "=========================================="

