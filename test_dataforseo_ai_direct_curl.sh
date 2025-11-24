#!/bin/bash
# Test DataForSEO AI Optimization API directly using curl

# Check if credentials are available
if [ -z "$DATAFORSEO_API_KEY" ] || [ -z "$DATAFORSEO_API_SECRET" ]; then
    echo "⚠️  DATAFORSEO_API_KEY and DATAFORSEO_API_SECRET must be set"
    echo "   Trying to get from Cloud Run service..."
    
    # Try to get from Cloud Run
    echo "   Checking Cloud Run environment variables..."
    exit 1
fi

BASE_URL="https://api.dataforseo.com/v3"
CREDENTIALS="${DATAFORSEO_API_KEY}:${DATAFORSEO_API_SECRET}"
ENCODED_CREDENTIALS=$(echo -n "$CREDENTIALS" | base64)

echo "=================================================================================="
echo "Testing DataForSEO AI Search Volume API"
echo "=================================================================================="
echo ""

# Test AI Search Volume endpoint
echo "📊 Testing: keywords_data/ai_optimization/search_volume/live"
echo ""

PAYLOAD='[{
  "keywords": ["chatgpt", "artificial intelligence", "machine learning"],
  "location_name": "United States",
  "language_code": "en"
}]'

RESPONSE=$(curl -s -X POST "${BASE_URL}/keywords_data/ai_optimization/search_volume/live" \
  -H "Authorization: Basic ${ENCODED_CREDENTIALS}" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD" \
  --max-time 30)

echo "Response Status:"
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null | head -50 || echo "$RESPONSE" | head -50

echo ""
echo "=================================================================================="
echo "Testing DataForSEO LLM Mentions API"
echo "=================================================================================="
echo ""

# Test LLM Mentions endpoint
echo "📊 Testing: ai_optimization/llm_mentions/search/live"
echo ""

PAYLOAD='[{
  "target": [{"keyword": "chatgpt"}],
  "location_name": "United States",
  "language_code": "en",
  "platform": "chat_gpt",
  "limit": 10
}]'

RESPONSE=$(curl -s -X POST "${BASE_URL}/ai_optimization/llm_mentions/search/live" \
  -H "Authorization: Basic ${ENCODED_CREDENTIALS}" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD" \
  --max-time 30)

echo "Response Status:"
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null | head -80 || echo "$RESPONSE" | head -80

echo ""
echo "=================================================================================="
echo "Summary"
echo "=================================================================================="
echo ""
echo "✅ API calls completed. Check output above for response structure."

