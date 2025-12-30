#!/bin/bash

# Test Both Modes Using Async Mode (Recommended)
# Uses async job creation and polling for better reliability

set -e

BASE_URL="https://blog-writer-api-dev-kq42l26tuq-od.a.run.app"
ENDPOINT="${BASE_URL}/api/v1/blog/generate-enhanced"
JOBS_ENDPOINT="${BASE_URL}/api/v1/blog/jobs"

TOPIC="Benefits of Python Programming"
KEYWORDS='["python", "programming", "coding", "development"]'
WORD_COUNT=500

echo "============================================================"
echo "Testing Both Modes (Async Mode)"
echo "============================================================"
echo ""

# Function to poll job status
poll_job() {
    local JOB_ID=$1
    local MAX_WAIT=${2:-600}  # Default 10 minutes
    local INTERVAL=5
    local ELAPSED=0
    
    echo "Polling job: ${JOB_ID}"
    echo "Max wait time: ${MAX_WAIT}s"
    echo ""
    
    while [ $ELAPSED -lt $MAX_WAIT ]; do
        STATUS_RESPONSE=$(curl -s "${JOBS_ENDPOINT}/${JOB_ID}")
        STATUS=$(echo "$STATUS_RESPONSE" | jq -r '.status // "unknown"')
        PROGRESS=$(echo "$STATUS_RESPONSE" | jq -r '.progress_percentage // 0')
        
        echo "  [${ELAPSED}s] Status: ${STATUS} (${PROGRESS}%)"
        
        if [ "$STATUS" = "completed" ]; then
            echo "$STATUS_RESPONSE" | jq '.'
            return 0
        elif [ "$STATUS" = "failed" ]; then
            echo "❌ Job failed!"
            echo "$STATUS_RESPONSE" | jq '.'
            return 1
        fi
        
        sleep $INTERVAL
        ELAPSED=$((ELAPSED + INTERVAL))
    done
    
    echo "⏱️  Timeout waiting for job completion"
    return 1
}

# ============================================================================
# TEST 1: Quick Generate Mode
# ============================================================================
echo "============================================================"
echo "TEST 1: Quick Generate Mode (Async)"
echo "============================================================"
echo ""

QUICK_PAYLOAD=$(cat <<EOF
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
  "async_mode": true
}
EOF
)

echo "📡 Creating Quick Generate job..."
QUICK_RESPONSE=$(curl -s -X POST "${ENDPOINT}?async_mode=true" \
  -H "Content-Type: application/json" \
  -d "${QUICK_PAYLOAD}")

QUICK_JOB_ID=$(echo "$QUICK_RESPONSE" | jq -r '.job_id // empty')

if [ -z "$QUICK_JOB_ID" ] || [ "$QUICK_JOB_ID" = "null" ]; then
    echo "❌ Failed to create Quick Generate job"
    echo "$QUICK_RESPONSE" | jq '.' 2>/dev/null || echo "$QUICK_RESPONSE"
    QUICK_JOB_ID=""
else
    echo "✅ Job created: ${QUICK_JOB_ID}"
    echo ""
    poll_job "$QUICK_JOB_ID" 180  # 3 minutes max
    QUICK_RESULT=$?
    
    if [ $QUICK_RESULT -eq 0 ]; then
        echo ""
        echo "✅ Quick Generate completed!"
        QUICK_STATUS=$(curl -s "${JOBS_ENDPOINT}/${QUICK_JOB_ID}")
        echo "$QUICK_STATUS" | jq '{title, word_count, quality_score, seo_score, readability_score, total_cost, citations: (.citations | length), engagement: .quality_dimensions.engagement.score, accessibility: .quality_dimensions.accessibility.score, eeat: .quality_dimensions.eeat.score}' > /tmp/quick_async_result.json
        echo "$QUICK_STATUS" | jq '{title, word_count, quality_score, seo_score, readability_score, total_cost, citations: (.citations | length), engagement: .quality_dimensions.engagement.score, accessibility: .quality_dimensions.accessibility.score, eeat: .quality_dimensions.eeat.score}'
    fi
fi

echo ""
echo "Waiting 10 seconds before next test..."
sleep 10

# ============================================================================
# TEST 2: Multi-Phase Mode
# ============================================================================
echo ""
echo "============================================================"
echo "TEST 2: Multi-Phase Mode (Async)"
echo "============================================================"
echo ""

MULTI_PAYLOAD=$(cat <<EOF
{
  "topic": "${TOPIC}",
  "keywords": ${KEYWORDS},
  "blog_type": "tutorial",
  "tone": "professional",
  "length": "medium",
  "word_count_target": ${WORD_COUNT},
  "mode": "multi_phase",
  "optimize_for_traffic": true,
  "use_dataforseo_content_generation": false,
  "use_google_search": true,
  "use_fact_checking": true,
  "use_citations": true,
  "use_serp_optimization": true,
  "use_consensus_generation": true,
  "use_knowledge_graph": true,
  "use_semantic_keywords": true,
  "use_quality_scoring": true,
  "async_mode": true
}
EOF
)

echo "📡 Creating Multi-Phase job..."
MULTI_RESPONSE=$(curl -s -X POST "${ENDPOINT}?async_mode=true" \
  -H "Content-Type: application/json" \
  -d "${MULTI_PAYLOAD}")

MULTI_JOB_ID=$(echo "$MULTI_RESPONSE" | jq -r '.job_id // empty')

if [ -z "$MULTI_JOB_ID" ] || [ "$MULTI_JOB_ID" = "null" ]; then
    echo "❌ Failed to create Multi-Phase job"
    echo "$MULTI_RESPONSE" | jq '.' 2>/dev/null || echo "$MULTI_RESPONSE"
    MULTI_JOB_ID=""
else
    echo "✅ Job created: ${MULTI_JOB_ID}"
    echo ""
    poll_job "$MULTI_JOB_ID" 600  # 10 minutes max
    MULTI_RESULT=$?
    
    if [ $MULTI_RESULT -eq 0 ]; then
        echo ""
        echo "✅ Multi-Phase completed!"
        MULTI_STATUS=$(curl -s "${JOBS_ENDPOINT}/${MULTI_JOB_ID}")
        echo "$MULTI_STATUS" | jq '{title, word_count, quality_score, seo_score, readability_score, total_cost, citations: (.citations | length), engagement: .quality_dimensions.engagement.score, accessibility: .quality_dimensions.accessibility.score, eeat: .quality_dimensions.eeat.score}' > /tmp/multi_async_result.json
        echo "$MULTI_STATUS" | jq '{title, word_count, quality_score, seo_score, readability_score, total_cost, citations: (.citations | length), engagement: .quality_dimensions.engagement.score, accessibility: .quality_dimensions.accessibility.score, eeat: .quality_dimensions.eeat.score}'
    fi
fi

echo ""
echo "============================================================"
echo "Test Complete"
echo "============================================================"







