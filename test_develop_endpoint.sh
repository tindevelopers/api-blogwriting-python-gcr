#!/bin/bash
# Comprehensive test script for develop endpoint
# Tests all major endpoints on the develop environment

set -e

API_URL="https://blog-writer-api-dev-kq42l26tuq-od.a.run.app"
TIMEOUT=180

echo "=========================================="
echo "Testing Develop Endpoint"
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
            jq '.' /tmp/test_response.json 2>/dev/null | head -20 || cat /tmp/test_response.json | head -20
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

# Test 2: Root Endpoint
test_endpoint "Root Endpoint" "GET" "/" "" 200
echo ""

# Test 3: Ready Check
test_endpoint "Ready Check" "GET" "/ready" "" 200
echo ""

# Test 4: Live Check
test_endpoint "Live Check" "GET" "/live" "" 200
echo ""

# Test 5: API Documentation
test_endpoint "API Documentation" "GET" "/docs" "" 200
echo ""

# Test 6: Standard Keyword Analysis
test_endpoint "Standard Keyword Analysis" "POST" "/api/v1/keywords/analyze" \
    '{
        "keywords": ["dog grooming"],
        "location": "United States",
        "language": "en"
    }' 200
echo ""

# Test 7: Enhanced Keyword Analysis (quick test)
test_endpoint "Enhanced Keyword Analysis" "POST" "/api/v1/keywords/enhanced" \
    '{
        "keywords": ["dog grooming"],
        "location": "United States",
        "language": "en",
        "max_suggestions_per_keyword": 5
    }' 200
echo ""

# Test 8: Standard Blog Generation (short)
test_endpoint "Standard Blog Generation" "POST" "/api/v1/blog/generate" \
    '{
        "topic": "dog grooming tips",
        "keywords": ["dog grooming"],
        "tone": "professional",
        "length": "short"
    }' 200
echo ""

# Test 9: AI Providers List
test_endpoint "AI Providers List" "GET" "/api/v1/ai/providers/list" "" 200
echo ""

# Test 10: Image Providers Status
test_endpoint "Image Providers Status" "GET" "/api/v1/images/providers" "" 200
echo ""

# Test 11: AI Health Check
test_endpoint "AI Health Check" "GET" "/api/v1/ai/health" "" 200
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

