#!/bin/bash

# Test AI Gateway Connection
# Tests if AI requests are reaching through the backend AI Gateway

BASE_URL="${API_URL:-https://blog-writer-api-dev-613248238610.europe-west9.run.app}"
TEST_ORG_ID="test-org-123"
TEST_USER_ID="test-user-456"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "\n${BLUE}======================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}======================================================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Test 1: Health Check
test_health_check() {
    print_header "Test 1: Health Check"
    
    RESPONSE=$(curl -s -w "\n%{http_code}" "$BASE_URL/health" 2>&1)
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')
    
    if [ "$HTTP_CODE" = "200" ]; then
        print_success "Backend is healthy"
        echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
        
        # Check if AI Gateway is mentioned
        if echo "$BODY" | grep -q "ai_gateway"; then
            print_info "AI Gateway configuration detected"
        fi
        
        return 0
    else
        print_error "Health check failed: HTTP $HTTP_CODE"
        echo "$BODY"
        return 1
    fi
}

# Test 2: AI Gateway Content Generation
test_ai_gateway_generate() {
    print_header "Test 2: AI Gateway Content Generation"
    
    print_info "Sending request to $BASE_URL/api/v1/blog/generate-gateway"
    print_info "Topic: Benefits of Python Programming"
    print_info "Model: gpt-4o-mini"
    
    REQUEST_JSON=$(cat <<EOF
{
  "topic": "Benefits of Python Programming",
  "keywords": ["python", "programming", "benefits"],
  "org_id": "$TEST_ORG_ID",
  "user_id": "$TEST_USER_ID",
  "word_count": 500,
  "tone": "professional",
  "model": "gpt-4o-mini"
}
EOF
)
    
    START_TIME=$(date +%s)
    
    RESPONSE=$(curl -s -w "\n%{http_code}" \
        -X POST "$BASE_URL/api/v1/blog/generate-gateway" \
        -H "Content-Type: application/json" \
        -d "$REQUEST_JSON" \
        --max-time 120 \
        2>&1)
    
    END_TIME=$(date +%s)
    ELAPSED=$((END_TIME - START_TIME))
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')
    
    if [ "$HTTP_CODE" = "200" ]; then
        print_success "Content generated successfully in ${ELAPSED}s"
        
        # Extract key information
        CONTENT_LENGTH=$(echo "$BODY" | python3 -c "import sys, json; print(len(json.load(sys.stdin).get('content', '')))" 2>/dev/null || echo "N/A")
        WORD_COUNT=$(echo "$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin).get('word_count', 'N/A'))" 2>/dev/null || echo "N/A")
        QUALITY_SCORE=$(echo "$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin).get('quality_score', 'N/A'))" 2>/dev/null || echo "N/A")
        MODEL_USED=$(echo "$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin).get('model_used', 'N/A'))" 2>/dev/null || echo "N/A")
        
        print_info "Content length: $CONTENT_LENGTH characters"
        print_info "Word count: $WORD_COUNT"
        print_info "Quality score: $QUALITY_SCORE/100"
        print_info "Model used: $MODEL_USED"
        
        # Show content preview
        CONTENT_PREVIEW=$(echo "$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin).get('content', '')[:200])" 2>/dev/null)
        if [ -n "$CONTENT_PREVIEW" ]; then
            echo -e "\n${YELLOW}Content preview:${NC}"
            echo "$CONTENT_PREVIEW..."
        fi
        
        return 0
    else
        print_error "Generation failed: HTTP $HTTP_CODE"
        echo "$BODY"
        return 1
    fi
}

# Test 3: AI Gateway Content Polishing
test_ai_gateway_polish() {
    print_header "Test 3: AI Gateway Content Polishing"
    
    REQUEST_JSON=$(cat <<EOF
{
  "content": "<thinking>This is a test artifact</thinking>\n# Test Post\n\nContent here.",
  "instructions": "Remove artifacts and improve readability",
  "org_id": "$TEST_ORG_ID",
  "user_id": "$TEST_USER_ID"
}
EOF
)
    
    print_info "Sending polish request"
    
    RESPONSE=$(curl -s -w "\n%{http_code}" \
        -X POST "$BASE_URL/api/v1/blog/polish" \
        -H "Content-Type: application/json" \
        -d "$REQUEST_JSON" \
        --max-time 60 \
        2>&1)
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')
    
    if [ "$HTTP_CODE" = "200" ]; then
        print_success "Content polished successfully"
        
        ORIGINAL_LENGTH=$(echo "$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin).get('original_length', 0))" 2>/dev/null || echo "0")
        POLISHED_LENGTH=$(echo "$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin).get('polished_length', 0))" 2>/dev/null || echo "0")
        ARTIFACTS_REMOVED=$(echo "$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin).get('artifacts_removed', 0))" 2>/dev/null || echo "0")
        
        print_info "Original length: $ORIGINAL_LENGTH"
        print_info "Polished length: $POLISHED_LENGTH"
        print_info "Artifacts removed: $ARTIFACTS_REMOVED chars"
        
        return 0
    else
        print_error "Polishing failed: HTTP $HTTP_CODE"
        echo "$BODY"
        return 1
    fi
}

# Test 4: AI Gateway Quality Check
test_ai_gateway_quality() {
    print_header "Test 4: AI Gateway Quality Check"
    
    REQUEST_JSON=$(cat <<EOF
{
  "content": "# Sample Post\n\nIntro paragraph.\n\n## Section 1\n\nContent.\n\n## Section 2\n\nMore content."
}
EOF
)
    
    print_info "Checking content quality"
    
    RESPONSE=$(curl -s -w "\n%{http_code}" \
        -X POST "$BASE_URL/api/v1/blog/quality-check" \
        -H "Content-Type: application/json" \
        -d "$REQUEST_JSON" \
        --max-time 30 \
        2>&1)
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')
    
    if [ "$HTTP_CODE" = "200" ]; then
        print_success "Quality check completed"
        
        QUALITY_SCORE=$(echo "$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin).get('quality_score', 'N/A'))" 2>/dev/null || echo "N/A")
        QUALITY_GRADE=$(echo "$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin).get('quality_grade', 'N/A'))" 2>/dev/null || echo "N/A")
        WORD_COUNT=$(echo "$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin).get('word_count', 'N/A'))" 2>/dev/null || echo "N/A")
        
        print_info "Quality score: $QUALITY_SCORE/100"
        print_info "Quality grade: $QUALITY_GRADE"
        print_info "Word count: $WORD_COUNT"
        
        return 0
    else
        print_error "Quality check failed: HTTP $HTTP_CODE"
        echo "$BODY"
        return 1
    fi
}

# Test 5: Check Backend Logs (if accessible)
check_backend_logs() {
    print_header "Test 5: Backend Configuration Info"
    
    print_info "Checking environment variables..."
    
    if [ -n "$LITELLM_PROXY_URL" ]; then
        print_success "LITELLM_PROXY_URL is set: $LITELLM_PROXY_URL"
    else
        print_error "LITELLM_PROXY_URL is not set in environment"
    fi
    
    if [ -n "$LITELLM_API_KEY" ]; then
        print_success "LITELLM_API_KEY is set"
    else
        print_error "LITELLM_API_KEY is not set in environment"
    fi
    
    # Check if we can access Cloud Run logs
    print_info "To check backend logs, run:"
    echo "  gcloud logs read --project=api-ai-blog-writer --service=blog-writer-api-dev --limit=50"
}

# Main execution
main() {
    echo -e "${GREEN}======================================================================${NC}"
    echo -e "${GREEN}AI Gateway Connection Test Suite${NC}"
    echo -e "${GREEN}======================================================================${NC}"
    echo -e "${YELLOW}Testing backend: $BASE_URL${NC}"
    echo -e "${YELLOW}Time: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
    
    PASSED=0
    TOTAL=0
    
    # Run tests
    test_health_check && ((PASSED++))
    ((TOTAL++))
    sleep 1
    
    test_ai_gateway_generate && ((PASSED++))
    ((TOTAL++))
    sleep 2
    
    test_ai_gateway_polish && ((PASSED++))
    ((TOTAL++))
    sleep 1
    
    test_ai_gateway_quality && ((PASSED++))
    ((TOTAL++))
    sleep 1
    
    check_backend_logs
    
    # Print summary
    print_header "Test Summary"
    
    if [ $PASSED -eq $TOTAL ]; then
        print_success "All tests passed! ($PASSED/$TOTAL)"
        echo -e "\n${GREEN}✓ AI requests are successfully reaching your backend.${NC}"
        echo -e "${GREEN}✓ The AI Gateway is functioning correctly.${NC}"
        
        if [ -n "$LITELLM_PROXY_URL" ]; then
            echo -e "\n${YELLOW}Note: Requests are being routed through LiteLLM proxy at:${NC}"
            echo -e "${YELLOW}  $LITELLM_PROXY_URL${NC}"
        else
            echo -e "\n${YELLOW}Note: Requests are using direct AI provider integrations${NC}"
            echo -e "${YELLOW}  (LiteLLM proxy is not configured)${NC}"
        fi
        
        return 0
    else
        print_error "Some tests failed ($PASSED/$TOTAL passed)"
        echo -e "\n${RED}✗ Check the errors above for details.${NC}"
        
        echo -e "\n${YELLOW}Troubleshooting tips:${NC}"
        echo "1. Verify the backend is deployed and running"
        echo "2. Check API keys are configured (OPENAI_API_KEY, ANTHROPIC_API_KEY)"
        echo "3. Review backend logs with:"
        echo "   gcloud logs read --project=api-ai-blog-writer --service=blog-writer-api-dev --limit=50"
        echo "4. Ensure CORS is configured for your frontend domain"
        
        return 1
    fi
}

# Run main function
main
exit $?

