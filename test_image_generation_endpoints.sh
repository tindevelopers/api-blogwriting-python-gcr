#!/bin/bash
# Test script for new image generation Cloud Tasks endpoints
# Tests async image generation, batch generation, and job status

set -e

API_URL="https://blog-writer-api-dev-kq42l26tuq-od.a.run.app"
TIMEOUT=180

echo "=========================================="
echo "Testing Image Generation Cloud Tasks Endpoints"
echo "=========================================="
echo ""
echo "Service URL: $API_URL"
echo "Timeout: ${TIMEOUT}s"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Function to test an endpoint
test_endpoint() {
    local name=$1
    local method=$2
    local endpoint=$3
    local data=$4
    local expected_status=${5:-200}
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Test: $name"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Method: $method"
    echo "Endpoint: $endpoint"
    
    START_TIME=$(date +%s)
    
    if [ -n "$data" ]; then
        HTTP_CODE=$(curl -s -w "%{http_code}" -X "$method" "$API_URL$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data" \
            -o /tmp/test_response.json \
            --max-time $TIMEOUT)
    else
        HTTP_CODE=$(curl -s -w "%{http_code}" -X "$method" "$API_URL$endpoint" \
            -o /tmp/test_response.json \
            --max-time $TIMEOUT)
    fi
    
    END_TIME=$(date +%s)
    ELAPSED=$((END_TIME - START_TIME))
    
    if [ "$HTTP_CODE" = "$expected_status" ]; then
        echo -e "${GREEN}✅ PASSED${NC} (HTTP $HTTP_CODE, ${ELAPSED}s)"
        if command -v jq &> /dev/null && [ -f /tmp/test_response.json ]; then
            echo "Response preview:"
            jq '.' /tmp/test_response.json 2>/dev/null | head -30 || cat /tmp/test_response.json | head -30
        fi
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}❌ FAILED${NC} (Expected HTTP $expected_status, got $HTTP_CODE, ${ELAPSED}s)"
        if [ -f /tmp/test_response.json ]; then
            echo "Response:"
            cat /tmp/test_response.json | head -50
        fi
        ((TESTS_FAILED++))
        return 1
    fi
    echo ""
}

# Test 1: Health Check
test_endpoint "Health Check" "GET" "/health" "" 200
echo ""

# Test 2: Image Providers Status
test_endpoint "Image Providers Status" "GET" "/api/v1/images/providers" "" 200
echo ""

# Test 3: Synchronous Image Generation (baseline)
echo -e "${YELLOW}Testing synchronous image generation (baseline)...${NC}"
test_endpoint "Synchronous Image Generation" "POST" "/api/v1/images/generate" \
    '{
        "prompt": "A beautiful sunset over mountains",
        "quality": "draft",
        "provider": "stability_ai",
        "aspect_ratio": "16:9"
    }' 200
echo ""

# Test 4: Async Image Generation (Draft)
echo -e "${YELLOW}Testing async image generation (draft quality)...${NC}"
DRAFT_JOB_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/images/generate-async" \
    -H "Content-Type: application/json" \
    -d '{
        "prompt": "A futuristic cityscape at sunset",
        "quality": "draft",
        "provider": "stability_ai",
        "aspect_ratio": "16:9"
    }' \
    --max-time $TIMEOUT)

if echo "$DRAFT_JOB_RESPONSE" | jq -e '.job_id' > /dev/null 2>&1; then
    DRAFT_JOB_ID=$(echo "$DRAFT_JOB_RESPONSE" | jq -r '.job_id')
    echo -e "${GREEN}✅ Async draft job created${NC}"
    echo "Job ID: $DRAFT_JOB_ID"
    echo "$DRAFT_JOB_RESPONSE" | jq '.'
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ Failed to create async draft job${NC}"
    echo "$DRAFT_JOB_RESPONSE"
    ((TESTS_FAILED++))
fi
echo ""

# Test 5: Async Image Generation (Standard Quality)
echo -e "${YELLOW}Testing async image generation (standard quality)...${NC}"
STANDARD_JOB_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/images/generate-async" \
    -H "Content-Type: application/json" \
    -d '{
        "prompt": "A professional business meeting",
        "quality": "standard",
        "provider": "stability_ai",
        "aspect_ratio": "1:1",
        "style": "photographic"
    }' \
    --max-time $TIMEOUT)

if echo "$STANDARD_JOB_RESPONSE" | jq -e '.job_id' > /dev/null 2>&1; then
    STANDARD_JOB_ID=$(echo "$STANDARD_JOB_RESPONSE" | jq -r '.job_id')
    echo -e "${GREEN}✅ Async standard job created${NC}"
    echo "Job ID: $STANDARD_JOB_ID"
    echo "$STANDARD_JOB_RESPONSE" | jq '.'
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ Failed to create async standard job${NC}"
    echo "$STANDARD_JOB_RESPONSE"
    ((TESTS_FAILED++))
fi
echo ""

# Test 6: Check Job Status (if we have a job ID)
if [ -n "$DRAFT_JOB_ID" ]; then
    echo -e "${YELLOW}Testing job status endpoint...${NC}"
    sleep 2  # Wait a bit for processing
    test_endpoint "Get Job Status" "GET" "/api/v1/images/jobs/$DRAFT_JOB_ID" "" 200
    echo ""
fi

# Test 7: Batch Image Generation
echo -e "${YELLOW}Testing batch image generation...${NC}"
BATCH_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/images/batch-generate" \
    -H "Content-Type: application/json" \
    -d '{
        "images": [
            {
                "prompt": "Hero image for blog post",
                "quality": "draft",
                "aspect_ratio": "16:9"
            },
            {
                "prompt": "Featured image",
                "quality": "draft",
                "aspect_ratio": "1:1"
            }
        ],
        "workflow": "draft_then_final"
    }' \
    --max-time $TIMEOUT)

if echo "$BATCH_RESPONSE" | jq -e '.batch_id' > /dev/null 2>&1; then
    BATCH_ID=$(echo "$BATCH_RESPONSE" | jq -r '.batch_id')
    echo -e "${GREEN}✅ Batch job created${NC}"
    echo "Batch ID: $BATCH_ID"
    echo "$BATCH_RESPONSE" | jq '.'
    ((TESTS_PASSED++))
    
    # Get first job ID from batch
    FIRST_JOB_ID=$(echo "$BATCH_RESPONSE" | jq -r '.job_ids[0]')
    if [ "$FIRST_JOB_ID" != "null" ] && [ -n "$FIRST_JOB_ID" ]; then
        echo ""
        echo -e "${YELLOW}Checking status of first batch job...${NC}"
        sleep 2
        test_endpoint "Get Batch Job Status" "GET" "/api/v1/images/jobs/$FIRST_JOB_ID" "" 200
    fi
else
    echo -e "${RED}❌ Failed to create batch job${NC}"
    echo "$BATCH_RESPONSE"
    ((TESTS_FAILED++))
fi
echo ""

# Test 8: List Image Jobs
test_endpoint "List Image Jobs" "GET" "/api/v1/images/jobs?limit=10" "" 200
echo ""

# Summary
echo ""
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo -e "${GREEN}Tests Passed: $TESTS_PASSED${NC}"
if [ $TESTS_FAILED -gt 0 ]; then
    echo -e "${RED}Tests Failed: $TESTS_FAILED${NC}"
else
    echo -e "${GREEN}Tests Failed: $TESTS_FAILED${NC}"
fi
echo ""
echo "Total Tests: $((TESTS_PASSED + TESTS_FAILED))"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed${NC}"
    exit 1
fi



