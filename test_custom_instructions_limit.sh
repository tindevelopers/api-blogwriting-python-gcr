#!/bin/bash

# Test script for custom_instructions limit increase to 5000 characters

BASE_URL="${BASE_URL:-http://localhost:8000}"
ENDPOINT="${BASE_URL}/api/v1/blog/generate-enhanced"

echo "🧪 Testing Custom Instructions Limit Increase"
echo "Endpoint: ${ENDPOINT}"
echo "Expected limit: 5000 characters"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results array
declare -a TEST_RESULTS

test_length() {
    local length=$1
    local description=$2
    local should_pass=$3
    
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}Test: ${description}${NC}"
    echo -e "${BLUE}Length: ${length} characters${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    # Generate custom_instructions of specified length
    if [ $length -eq 0 ]; then
        CUSTOM_INSTRUCTIONS=""
        PAYLOAD=$(cat <<EOF
{
  "topic": "Test Blog Post",
  "keywords": ["test", "blogging"],
  "tone": "professional",
  "length": "short"
}
EOF
)
    else
        # Create instruction text of exact length
        BASE_TEXT="MANDATORY STRUCTURE: Use H1 for title, H2 for sections, include internal links, add images with alt text. "
        REPEAT_TEXT="Repeat this instruction. "
        REMAINING=$((length - ${#BASE_TEXT}))
        REPEAT_COUNT=$((REMAINING / ${#REPEAT_TEXT}))
        CUSTOM_INSTRUCTIONS="${BASE_TEXT}$(printf "${REPEAT_TEXT}%.0s" $(seq 1 $REPEAT_COUNT))"
        CUSTOM_INSTRUCTIONS="${CUSTOM_INSTRUCTIONS:0:$length}"
        
        # Escape JSON
        CUSTOM_INSTRUCTIONS_ESCAPED=$(echo "$CUSTOM_INSTRUCTIONS" | sed 's/"/\\"/g')
        
        PAYLOAD=$(cat <<EOF
{
  "topic": "Test Blog Post",
  "keywords": ["test", "blogging"],
  "tone": "professional",
  "length": "short",
  "custom_instructions": "${CUSTOM_INSTRUCTIONS_ESCAPED}"
}
EOF
)
    fi
    
    ACTUAL_LENGTH=${#CUSTOM_INSTRUCTIONS}
    echo "Actual length: ${ACTUAL_LENGTH} characters"
    
    # Make request
    START_TIME=$(date +%s.%N)
    RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST "${ENDPOINT}" \
        -H "Content-Type: application/json" \
        -d "${PAYLOAD}" \
        --max-time 60)
    END_TIME=$(date +%s.%N)
    
    ELAPSED=$(echo "$END_TIME - $START_TIME" | bc)
    HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
    BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS/d')
    
    # Check result
    if [ "$HTTP_STATUS" = "200" ]; then
        echo -e "${GREEN}✅ SUCCESS${NC} - Status: ${HTTP_STATUS}"
        echo "   Response time: ${ELAPSED}s"
        TEST_RESULTS+=("✅ PASS - ${description} (${ACTUAL_LENGTH} chars) - Status: ${HTTP_STATUS}")
    elif [ "$HTTP_STATUS" = "422" ] || [ "$HTTP_STATUS" = "400" ]; then
        ERROR_MSG=$(echo "$BODY" | grep -o '"detail":"[^"]*"' | head -1 | cut -d'"' -f4)
        if [ -z "$ERROR_MSG" ]; then
            ERROR_MSG=$(echo "$BODY" | head -3)
        fi
        echo -e "${RED}❌ VALIDATION ERROR${NC} - Status: ${HTTP_STATUS}"
        echo "   Error: ${ERROR_MSG}"
        if [ "$should_pass" = "true" ]; then
            TEST_RESULTS+=("❌ FAIL - ${description} (${ACTUAL_LENGTH} chars) - Unexpected validation error")
        else
            TEST_RESULTS+=("✅ PASS - ${description} (${ACTUAL_LENGTH} chars) - Correctly rejected")
        fi
    else
        ERROR_MSG=$(echo "$BODY" | head -3)
        echo -e "${RED}❌ FAILED${NC} - Status: ${HTTP_STATUS}"
        echo "   Error: ${ERROR_MSG}"
        TEST_RESULTS+=("❌ FAIL - ${description} (${ACTUAL_LENGTH} chars) - Status: ${HTTP_STATUS}")
    fi
    
    echo ""
}

# Check if server is running
echo "Checking if server is running..."
if ! curl -s "${BASE_URL}/health" > /dev/null 2>&1; then
    echo -e "${RED}❌ Server is not running at ${BASE_URL}${NC}"
    echo "Please start the server first:"
    echo "  uvicorn main:app --reload"
    exit 1
fi

echo -e "${GREEN}✅ Server is running${NC}"
echo ""

# Run tests
test_length 0 "No custom_instructions" true
test_length 500 "Small instruction (500 chars)" true
test_length 1500 "Medium instruction (1500 chars)" true
test_length 2000 "At old enhanced limit (2000 chars)" true
test_length 3500 "Between old and new limit (3500 chars)" true
test_length 5000 "At new limit (5000 chars)" true
test_length 5001 "Over new limit (5001 chars - should fail)" false
test_length 10000 "Way over limit (10000 chars - should fail)" false

# Summary
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}TEST SUMMARY${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

for result in "${TEST_RESULTS[@]}"; do
    echo "$result"
done

echo ""
PASSED=$(echo "${TEST_RESULTS[@]}" | grep -o "✅ PASS" | wc -l | tr -d ' ')
FAILED=$(echo "${TEST_RESULTS[@]}" | grep -o "❌ FAIL" | wc -l | tr -d ' ')
echo "Total tests: ${#TEST_RESULTS[@]}"
echo -e "${GREEN}✅ Passed: ${PASSED}${NC}"
echo -e "${RED}❌ Failed: ${FAILED}${NC}"

