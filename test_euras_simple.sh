#!/bin/bash
# Simple test for Euras Technology - both modes with async jobs

set -e

API_URL="${API_URL:-https://blog-writer-api-dev-kq42l26tuq-od.a.run.app}"
ENDPOINT="${API_URL}/api/v1/blog/generate-enhanced"

TOPIC="Using Euras Technology to Fix Leaks in Critical Infrastructure, Basements and Garages"
KEYWORDS='["Euras Technology", "leak repair", "critical infrastructure", "basement leaks", "garage leaks", "waterproofing", "leak detection"]'
CUSTOM_INSTRUCTIONS="Focus on Euras Technology (www.eurastechnology.com) solutions for leak detection and repair in critical infrastructure, basements, and garages. Include specific benefits and applications. Target: 250 words."

echo "============================================================"
echo "Euras Technology Leak Fixing - Mode Comparison Test"
echo "Topic: ${TOPIC}"
echo "Target: 250 words"
echo "============================================================"
echo ""

# Test 1: Quick Generate Mode
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 1: Quick Generate Mode (DataForSEO)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

QUICK_PAYLOAD=$(cat <<EOF
{
  "topic": "${TOPIC}",
  "keywords": ${KEYWORDS},
  "tone": "professional",
  "length": "short",
  "mode": "quick_generate",
  "use_citations": false,
  "custom_instructions": "${CUSTOM_INSTRUCTIONS}"
}
EOF
)

echo "📡 Sending Quick Generate request..."
QUICK_RESPONSE=$(curl -s -X POST "${ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d "${QUICK_PAYLOAD}")

QUICK_JOB_ID=$(echo "$QUICK_RESPONSE" | jq -r '.job_id' 2>/dev/null)
echo "Job ID: ${QUICK_JOB_ID}"
echo "$QUICK_RESPONSE" | jq '.' > test_euras_quick_job.json

# Wait for Quick Generate (estimated 60 seconds)
echo "Waiting for Quick Generate to complete (estimated 60s)..."
for i in {1..20}; do
    sleep 3
    STATUS=$(curl -s "${API_URL}/api/v1/blog/jobs/${QUICK_JOB_ID}" | jq -r '.status' 2>/dev/null)
    echo "  Status: ${STATUS}"
    if [ "$STATUS" = "completed" ]; then
        echo "✓ Quick Generate completed!"
        curl -s "${API_URL}/api/v1/blog/jobs/${QUICK_JOB_ID}" | jq '.' > test_euras_quick_result.json
        break
    elif [ "$STATUS" = "failed" ]; then
        echo "✗ Quick Generate failed!"
        curl -s "${API_URL}/api/v1/blog/jobs/${QUICK_JOB_ID}" | jq '.' > test_euras_quick_result.json
        break
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 2: Multi-Phase Mode (Comprehensive Pipeline)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "⚠️  Note: Multi-Phase requires Google Custom Search for citations"
echo "   This test may fail if Google Custom Search is not configured"
echo ""

MULTI_PAYLOAD=$(cat <<EOF
{
  "topic": "${TOPIC}",
  "keywords": ${KEYWORDS},
  "tone": "professional",
  "length": "short",
  "mode": "multi_phase",
  "use_citations": true,
  "custom_instructions": "${CUSTOM_INSTRUCTIONS}"
}
EOF
)

echo "📡 Sending Multi-Phase request..."
MULTI_RESPONSE=$(curl -s -X POST "${ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d "${MULTI_PAYLOAD}")

MULTI_JOB_ID=$(echo "$MULTI_RESPONSE" | jq -r '.job_id' 2>/dev/null)
if [ "$MULTI_JOB_ID" != "null" ] && [ -n "$MULTI_JOB_ID" ]; then
    echo "Job ID: ${MULTI_JOB_ID}"
    echo "$MULTI_RESPONSE" | jq '.' > test_euras_multi_phase_job.json
    
    # Wait for Multi-Phase (estimated 240 seconds)
    echo "Waiting for Multi-Phase to complete (estimated 240s)..."
    for i in {1..50}; do
        sleep 5
        STATUS=$(curl -s "${API_URL}/api/v1/blog/jobs/${MULTI_JOB_ID}" | jq -r '.status' 2>/dev/null)
        echo "  Status: ${STATUS}"
        if [ "$STATUS" = "completed" ]; then
            echo "✓ Multi-Phase completed!"
            curl -s "${API_URL}/api/v1/blog/jobs/${MULTI_JOB_ID}" | jq '.' > test_euras_multi_phase_result.json
            break
        elif [ "$STATUS" = "failed" ]; then
            echo "✗ Multi-Phase failed!"
            curl -s "${API_URL}/api/v1/blog/jobs/${MULTI_JOB_ID}" | jq '.' > test_euras_multi_phase_result.json
            break
        fi
    done
else
    echo "✗ Multi-Phase request failed immediately"
    echo "$MULTI_RESPONSE" | jq '.' > test_euras_multi_phase_error.json
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "COMPARISON SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ -f "test_euras_quick_result.json" ]; then
    echo "Quick Generate Results:"
    QUICK_TITLE=$(cat test_euras_quick_result.json | jq -r '.title' 2>/dev/null)
    QUICK_WORDS=$(cat test_euras_quick_result.json | jq -r '.content' 2>/dev/null | wc -w | tr -d ' ')
    QUICK_STATUS=$(cat test_euras_quick_result.json | jq -r '.status' 2>/dev/null)
    echo "  Status: ${QUICK_STATUS}"
    echo "  Title: ${QUICK_TITLE}"
    echo "  Word Count: ${QUICK_WORDS}"
    echo "  File: test_euras_quick_result.json"
fi

echo ""

if [ -f "test_euras_multi_phase_result.json" ]; then
    echo "Multi-Phase Results:"
    MULTI_TITLE=$(cat test_euras_multi_phase_result.json | jq -r '.title' 2>/dev/null)
    MULTI_WORDS=$(cat test_euras_multi_phase_result.json | jq -r '.content' 2>/dev/null | wc -w | tr -d ' ')
    MULTI_STATUS=$(cat test_euras_multi_phase_result.json | jq -r '.status' 2>/dev/null)
    MULTI_CITATIONS=$(cat test_euras_multi_phase_result.json | jq -r '.citations | length' 2>/dev/null)
    MULTI_QUALITY=$(cat test_euras_multi_phase_result.json | jq -r '.quality_score' 2>/dev/null)
    echo "  Status: ${MULTI_STATUS}"
    echo "  Title: ${MULTI_TITLE}"
    echo "  Word Count: ${MULTI_WORDS}"
    echo "  Citations: ${MULTI_CITATIONS}"
    echo "  Quality Score: ${MULTI_QUALITY}"
    echo "  File: test_euras_multi_phase_result.json"
elif [ -f "test_euras_multi_phase_error.json" ]; then
    echo "Multi-Phase Error:"
    cat test_euras_multi_phase_error.json | jq -r '.message' 2>/dev/null
fi

