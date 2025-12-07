#!/bin/bash
# Test both Quick Generate and Multi-Phase modes
# Tests with smallest blog size that exercises all functionality

set -e

API_URL="https://blog-writer-api-dev-kq42l26tuq-od.a.run.app"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="test-results-${TIMESTAMP}"
mkdir -p "$OUTPUT_DIR"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Testing Both Generation Modes"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "API URL: $API_URL"
echo "Output Directory: $OUTPUT_DIR"
echo ""

# Test parameters
TOPIC="How to use tin.info for business analytics and data insights"
KEYWORDS=("tin.info" "business analytics" "data insights" "business intelligence")
WORD_COUNT=300  # Small size but enough to test functionality
GSC_SITE="https://tin.info"

echo "Test Parameters:"
echo "  Topic: $TOPIC"
echo "  Keywords: ${KEYWORDS[@]}"
echo "  Word Count: $WORD_COUNT"
echo "  GSC Site: $GSC_SITE"
echo ""

# Test 1: Quick Generate Mode
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 1: Quick Generate Mode (DataForSEO)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

QUICK_PAYLOAD=$(cat <<EOF
{
  "topic": "$TOPIC",
  "keywords": $(printf '%s\n' "${KEYWORDS[@]}" | jq -R . | jq -s .),
  "word_count": $WORD_COUNT,
  "mode": "quick_generate",
  "gsc_site_url": "$GSC_SITE",
  "use_citations": true,
  "use_google_search": true,
  "use_semantic_keywords": true,
  "use_quality_scoring": true,
  "custom_instructions": "Focus on practical business use cases and real-world examples. Include specific features and benefits of tin.info platform."
}
EOF
)

echo "Sending Quick Generate request (synchronous)..."
QUICK_RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST \
  "$API_URL/api/v1/blog/generate-enhanced?async_mode=false" \
  -H "Content-Type: application/json" \
  -d "$QUICK_PAYLOAD")

HTTP_STATUS=$(echo "$QUICK_RESPONSE" | grep "HTTP_STATUS:" | cut -d: -f2)
QUICK_BODY=$(echo "$QUICK_RESPONSE" | sed '/HTTP_STATUS:/d')

echo "HTTP Status: $HTTP_STATUS"
echo ""

if [ "$HTTP_STATUS" = "200" ]; then
    echo "$QUICK_BODY" | jq '.' > "$OUTPUT_DIR/quick-generate-response.json"
    echo "✅ Quick Generate successful!"
    echo "Response saved to: $OUTPUT_DIR/quick-generate-response.json"
    
    # Extract key metrics
    echo ""
    echo "Quick Generate Results:"
    echo "$QUICK_BODY" | jq -r '
      "  Word Count: " + (.word_count | tostring),
      "  Readability Score: " + (.readability_score | tostring),
      "  SEO Score: " + (.seo_score | tostring),
      "  Citations: " + (.citations | length | tostring),
      "  Warnings: " + (.warnings | length | tostring),
      if .warnings | length > 0 then "  Warning Messages: " + (.warnings | join(", ")) else empty end
    '
else
    echo "❌ Quick Generate failed!"
    echo "$QUICK_BODY" > "$OUTPUT_DIR/quick-generate-error.json"
    echo "Error saved to: $OUTPUT_DIR/quick-generate-error.json"
    echo "$QUICK_BODY" | jq '.' 2>/dev/null || echo "$QUICK_BODY"
fi

echo ""
echo "Waiting 5 seconds before next test..."
sleep 5

# Test 2: Multi-Phase Mode
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 2: Multi-Phase Mode (Comprehensive Pipeline)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

MULTI_PHASE_PAYLOAD=$(cat <<EOF
{
  "topic": "$TOPIC",
  "keywords": $(printf '%s\n' "${KEYWORDS[@]}" | jq -R . | jq -s .),
  "word_count": $WORD_COUNT,
  "mode": "multi_phase",
  "gsc_site_url": "$GSC_SITE",
  "use_citations": true,
  "use_google_search": true,
  "use_knowledge_graph": true,
  "use_semantic_keywords": true,
  "use_quality_scoring": true,
  "custom_instructions": "Focus on practical business use cases and real-world examples. Include specific features and benefits of tin.info platform. Ensure high readability and include first-hand experience indicators."
}
EOF
)

echo "Sending Multi-Phase request (synchronous)..."
MULTI_RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST \
  "$API_URL/api/v1/blog/generate-enhanced?async_mode=false" \
  -H "Content-Type: application/json" \
  -d "$MULTI_PHASE_PAYLOAD")

HTTP_STATUS=$(echo "$MULTI_RESPONSE" | grep "HTTP_STATUS:" | cut -d: -f2)
MULTI_BODY=$(echo "$MULTI_RESPONSE" | sed '/HTTP_STATUS:/d')

echo "HTTP Status: $HTTP_STATUS"
echo ""

if [ "$HTTP_STATUS" = "200" ]; then
    echo "$MULTI_BODY" | jq '.' > "$OUTPUT_DIR/multi-phase-response.json"
    echo "✅ Multi-Phase successful!"
    echo "Response saved to: $OUTPUT_DIR/multi-phase-response.json"
    
    # Extract key metrics
    echo ""
    echo "Multi-Phase Results:"
    echo "$MULTI_BODY" | jq -r '
      "  Word Count: " + (.word_count | tostring),
      "  Readability Score: " + (.readability_score | tostring),
      "  SEO Score: " + (.seo_score | tostring),
      "  Citations: " + (.citations | length | tostring),
      "  Warnings: " + (.warnings | length | tostring),
      if .warnings | length > 0 then "  Warning Messages: " + (.warnings | join(", ")) else empty end
    '
else
    echo "❌ Multi-Phase failed!"
    echo "$MULTI_BODY" > "$OUTPUT_DIR/multi-phase-error.json"
    echo "Error saved to: $OUTPUT_DIR/multi-phase-error.json"
    echo "$MULTI_BODY" | jq '.' 2>/dev/null || echo "$MULTI_BODY"
fi

# Comparison
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Comparison Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ -f "$OUTPUT_DIR/quick-generate-response.json" ] && [ -f "$OUTPUT_DIR/multi-phase-response.json" ]; then
    echo "Mode Comparison:"
    echo ""
    echo "Quick Generate:"
    cat "$OUTPUT_DIR/quick-generate-response.json" | jq -r '
      "  Word Count: " + (.word_count | tostring),
      "  Readability: " + (.readability_score | tostring),
      "  SEO Score: " + (.seo_score | tostring),
      "  Citations: " + (.citations | length | tostring),
      "  Generation Time: " + (.generation_time_ms | tostring) + "ms"
    '
    echo ""
    echo "Multi-Phase:"
    cat "$OUTPUT_DIR/multi-phase-response.json" | jq -r '
      "  Word Count: " + (.word_count | tostring),
      "  Readability: " + (.readability_score | tostring),
      "  SEO Score: " + (.seo_score | tostring),
      "  Citations: " + (.citations | length | tostring),
      "  Generation Time: " + (.generation_time_ms | tostring) + "ms"
    '
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Results saved to: $OUTPUT_DIR/"
echo ""

