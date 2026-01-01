#!/bin/bash

# Test API payload for creating topics and subtopics for 100 words
# Base URL from API documentation
BASE_URL="https://blog-writer-api-dev-kq42l26tuq-od.a.run.app"
ENDPOINT="${BASE_URL}/api/v1/blog/generate-enhanced"

echo "=========================================="
echo "Testing API: Generate Blog with 100 Words"
echo "=========================================="
echo ""
echo "Endpoint: ${ENDPOINT}"
echo ""

# Test payload with 100 word target
PAYLOAD=$(cat <<EOF
{
  "topic": "Introduction to Python Programming",
  "keywords": ["python", "programming", "coding"],
  "blog_type": "tutorial",
  "tone": "professional",
  "length": "short",
  "word_count_target": 100,
  "optimize_for_traffic": true,
  "use_dataforseo_content_generation": true
}
EOF
)

echo "Request Payload:"
echo "$PAYLOAD" | jq '.'
echo ""
echo "Sending request..."
echo ""

# Make the API call
RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST "${ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d "${PAYLOAD}")

# Extract HTTP status code
HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS/d')

echo "=========================================="
echo "Response Status: ${HTTP_STATUS}"
echo "=========================================="
echo ""

if [ "$HTTP_STATUS" -eq 200 ]; then
  echo "✅ SUCCESS - Response:"
  echo "$BODY" | jq '.'
  
  echo ""
  echo "=========================================="
  echo "Extracted Information:"
  echo "=========================================="
  
  # Extract key fields
  TITLE=$(echo "$BODY" | jq -r '.title // "N/A"')
  WORD_COUNT=$(echo "$BODY" | jq -r '.seo_metadata.word_count_range.actual // "N/A"')
  SUBTOPICS=$(echo "$BODY" | jq -r '.seo_metadata.subtopics // []')
  SUBTOPICS_COUNT=$(echo "$BODY" | jq -r '.seo_metadata.subtopics | length // 0')
  SEO_SCORE=$(echo "$BODY" | jq -r '.seo_score // "N/A"')
  COST=$(echo "$BODY" | jq -r '.total_cost // "N/A"')
  
  echo "Title: $TITLE"
  echo "Word Count: $WORD_COUNT"
  echo "Subtopics Count: $SUBTOPICS_COUNT"
  echo "SEO Score: $SEO_SCORE"
  echo "Total Cost: \$$COST"
  echo ""
  
  if [ "$SUBTOPICS_COUNT" -gt 0 ]; then
    echo "Subtopics:"
    echo "$SUBTOPICS" | jq -r '.[]' | nl
  else
    echo "⚠️  No subtopics generated"
  fi
  
else
  echo "❌ ERROR - Response:"
  echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY"
fi

echo ""
echo "=========================================="
echo "Test Complete"
echo "=========================================="










