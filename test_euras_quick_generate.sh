#!/bin/bash

# Test Quick Generate Mode for Euras Technology Leak Fixing
# Target: 250 words

ENDPOINT="${CLOUD_RUN_URL:-https://api-blogwriting-python-gcr-xxxxx.run.app}/api/v1/blog/generate-enhanced"

echo "Testing Quick Generate Mode (DataForSEO)"
echo "Topic: Using Euras Technology to fix leaks in critical infrastructure, basements and garages"
echo "Target: 250 words"
echo "---"

curl -X POST "$ENDPOINT" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${API_KEY:-your-api-key}" \
  -d '{
    "topic": "Using Euras Technology to Fix Leaks in Critical Infrastructure, Basements and Garages",
    "keywords": ["Euras Technology", "leak repair", "critical infrastructure", "basement leaks", "garage leaks", "waterproofing", "leak detection"],
    "tone": "professional",
    "length": "short",
    "mode": "quick_generate",
    "use_citations": false,
    "use_dataforseo_content_generation": true,
    "custom_instructions": "Focus on Euras Technology (www.eurastechnology.com) solutions for leak detection and repair in critical infrastructure, basements, and garages. Include specific benefits and applications.",
    "async_mode": false
  }' \
  -w "\n\nHTTP Status: %{http_code}\n" \
  -o test_euras_quick_result.json

echo ""
echo "Response saved to: test_euras_quick_result.json"
echo "---"

