#!/bin/bash

# Test Quick Generate Mode Only
# With extended timeout for testing

set -e

BASE_URL="https://blog-writer-api-dev-kq42l26tuq-od.a.run.app"
ENDPOINT="${BASE_URL}/api/v1/blog/generate-enhanced"

TOPIC="Benefits of Python Programming"
KEYWORDS='["python", "programming", "coding", "development"]'
WORD_COUNT=500

echo "============================================================"
echo "TEST: Quick Generate Mode"
echo "============================================================"
echo ""
echo "Topic: ${TOPIC}"
echo "Word Count: ${WORD_COUNT}"
echo ""

PAYLOAD=$(cat <<EOF
{
  "topic": "${TOPIC}",
  "keywords": ${KEYWORDS},
  "blog_type": "tutorial",
  "tone": "professional",
  "length": "medium",
  "word_count_target": ${WORD_COUNT},
  "mode": "quick_generate",
  "optimize_for_traffic": true,
  "use_dataforseo_content_generation": true,
  "async_mode": false
}
EOF
)

echo "📡 Sending request..."
START=$(date +%s)

RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST "${ENDPOINT}?async_mode=false" \
  -H "Content-Type: application/json" \
  -d "${PAYLOAD}" \
  --max-time 180)

END=$(date +%s)
DURATION=$((END - START))

HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS/d')

echo "Response Time: ${DURATION}s"
echo "HTTP Status: ${HTTP_STATUS}"
echo ""

if [ "$HTTP_STATUS" -eq 200 ]; then
    echo "✅ SUCCESS"
    echo "$BODY" | jq '{title, word_count, quality_score, seo_score, readability_score, total_cost, citations: (.citations | length), engagement: .quality_dimensions.engagement.score, accessibility: .quality_dimensions.accessibility.score, eeat: .quality_dimensions.eeat.score}' > /tmp/quick_test_result.json
    echo "$BODY" | jq '{title, word_count, quality_score, seo_score, readability_score, total_cost, citations: (.citations | length), engagement: .quality_dimensions.engagement.score, accessibility: .quality_dimensions.accessibility.score, eeat: .quality_dimensions.eeat.score}'
else
    echo "❌ FAILED"
    echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY"
fi







