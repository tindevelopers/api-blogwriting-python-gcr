#!/bin/bash
# Simple test script for DataForSEO API endpoints

BASE64_AUTH="ZGV2ZWxvcGVyQHRpbi5pbmZvOjcyNWVjODhlMGFmMGM5MDU="
BASE_URL="https://api.dataforseo.com/v3"

echo "=========================================="
echo "Testing LLM Mentions Endpoint"
echo "=========================================="
curl -s -X POST "${BASE_URL}/ai_optimization/llm_mentions/search/live" \
  -H "Authorization: Basic ${BASE64_AUTH}" \
  -H "Content-Type: application/json" \
  -d '[{
    "target": [{"keyword": "chatgpt"}],
    "location_name": "United States",
    "language_code": "en",
    "platform": "chat_gpt",
    "limit": 10
  }]' | python3 -m json.tool | head -50

echo ""
echo "=========================================="
echo "Testing AI Search Volume - Path 1"
echo "=========================================="
curl -s -X POST "${BASE_URL}/ai_optimization/keyword_data/live" \
  -H "Authorization: Basic ${BASE64_AUTH}" \
  -H "Content-Type: application/json" \
  -d '[{
    "keywords": ["chatgpt"],
    "location_name": "United States",
    "language_code": "en"
  }]' | python3 -m json.tool | head -50

echo ""
echo "=========================================="
echo "Testing AI Search Volume - Path 2"
echo "=========================================="
curl -s -X POST "${BASE_URL}/ai_optimization/ai_keyword_data/live" \
  -H "Authorization: Basic ${BASE64_AUTH}" \
  -H "Content-Type: application/json" \
  -d '[{
    "keywords": ["chatgpt"],
    "location_name": "United States",
    "language_code": "en"
  }]' | python3 -m json.tool | head -50

