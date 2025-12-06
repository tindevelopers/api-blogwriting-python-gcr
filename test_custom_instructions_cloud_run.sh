#!/bin/bash

# Test custom_instructions limit on Google Cloud Run deployment
BASE_URL="https://blog-writer-api-dev-kq42l26tuq-od.a.run.app"
ENDPOINT="${BASE_URL}/api/v1/blog/generate-enhanced"

echo "🧪 Testing Custom Instructions Limit on Google Cloud Run"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Endpoint: ${ENDPOINT}"
echo "Expected limit: 5000 characters"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Results array
declare -a TEST_RESULTS
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

# Function to generate text of exact length
generate_text() {
    local length=$1
    base="MANDATORY STRUCTURE: Use H1 for title, H2 for sections, include internal links, add images with alt text. "
    repeat="Repeat this instruction. "
    
    if [ $length -le ${#base} ]; then
        echo "${base:0:$length}"
        return
    fi
    
    remaining=$((length - ${#base}))
    repeat_count=$((remaining / ${#repeat}))
    text="${base}$(printf "${repeat}%.0s" $(seq 1 $repeat_count))"
    echo "${text:0:$length}"
}

# Function to test a specific length
test_length() {
    local length=$1
    local description=$2
    local should_pass=$3
    
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}Test: ${description}${NC}"
    echo -e "${BLUE}Length: ${length} characters${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    # Generate custom_instructions
    if [ $length -eq 0 ]; then
        CUSTOM_INSTRUCTIONS=""
        PAYLOAD=$(cat <<EOF
{
  "topic": "Test Blog Post - Custom Instructions Limit",
  "keywords": ["test", "blogging", "validation"],
  "tone": "professional",
  "length": "short",
  "blog_type": "guide"
}
EOF
)
    else
        CUSTOM_INSTRUCTIONS=$(generate_text $length)
        # Escape JSON properly
        CUSTOM_INSTRUCTIONS_ESCAPED=$(echo "$CUSTOM_INSTRUCTIONS" | sed 's/\\/\\\\/g' | sed 's/"/\\"/g' | sed ':a;N;$!ba;s/\n/\\n/g')
        
        PAYLOAD=$(cat <<EOF
{
  "topic": "Test Blog Post - Custom Instructions Limit",
  "keywords": ["test", "blogging", "validation"],
  "tone": "professional",
  "length": "short",
  "blog_type": "guide",
  "custom_instructions": "${CUSTOM_INSTRUCTIONS_ESCAPED}"
}
EOF
)
    fi
    
    ACTUAL_LENGTH=${#CUSTOM_INSTRUCTIONS}
    echo "Actual custom_instructions length: ${ACTUAL_LENGTH} characters"
    
    # Make request
    START_TIME=$(date +%s.%N)
    RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}\nTIME_TOTAL:%{time_total}" \
        -X POST "${ENDPOINT}" \
        -H "Content-Type: application/json" \
        -d "${PAYLOAD}" \
        --max-time 120)
    END_TIME=$(date +%s.%N)
    
    HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
    TIME_TOTAL=$(echo "$RESPONSE" | grep "TIME_TOTAL" | cut -d: -f2)
    BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS/d' | sed '/TIME_TOTAL/d')
    
    # Parse response
    if [ "$HTTP_STATUS" = "200" ]; then
        echo -e "${GREEN}✅ SUCCESS${NC} - Status: ${HTTP_STATUS}"
        echo "   Response time: ${TIME_TOTAL}s"
        
        # Check if response has content
        if echo "$BODY" | grep -q '"content"\|"title"\|"blog_content"'; then
            echo "   Response contains blog content"
            TEST_RESULTS+=("✅ PASS - ${description} (${ACTUAL_LENGTH} chars) - Status: ${HTTP_STATUS} - Response received")
        else
            echo "   ⚠️  Response structure unexpected"
            TEST_RESULTS+=("⚠️  WARN - ${description} (${ACTUAL_LENGTH} chars) - Status: ${HTTP_STATUS} - Unexpected response")
        fi
    elif [ "$HTTP_STATUS" = "422" ] || [ "$HTTP_STATUS" = "400" ]; then
        ERROR_MSG=$(echo "$BODY" | grep -o '"detail"[^}]*' | head -1 | sed 's/"detail"://' | sed 's/"//g' | cut -d',' -f1)
        if [ -z "$ERROR_MSG" ]; then
            ERROR_MSG=$(echo "$BODY" | head -5 | grep -o '"msg":"[^"]*"' | head -1 | cut -d'"' -f4)
        fi
        if [ -z "$ERROR_MSG" ]; then
            ERROR_MSG="Validation error (check response body)"
        fi
        
        echo -e "${RED}❌ VALIDATION ERROR${NC} - Status: ${HTTP_STATUS}"
        echo "   Error: ${ERROR_MSG}"
        
        if [ "$should_pass" = "true" ]; then
            TEST_RESULTS+=("❌ FAIL - ${description} (${ACTUAL_LENGTH} chars) - Unexpected validation error: ${ERROR_MSG}")
        else
            TEST_RESULTS+=("✅ PASS - ${description} (${ACTUAL_LENGTH} chars) - Correctly rejected: ${ERROR_MSG}")
        fi
    else
        ERROR_MSG=$(echo "$BODY" | head -3)
        echo -e "${RED}❌ FAILED${NC} - Status: ${HTTP_STATUS}"
        echo "   Error: ${ERROR_MSG}"
        TEST_RESULTS+=("❌ FAIL - ${description} (${ACTUAL_LENGTH} chars) - Status: ${HTTP_STATUS}")
    fi
    
    echo ""
    
    # Save detailed response for analysis
    echo "=== Response Details ===" >> test_responses.log
    echo "Test: ${description}" >> test_responses.log
    echo "Length: ${ACTUAL_LENGTH} chars" >> test_responses.log
    echo "Status: ${HTTP_STATUS}" >> test_responses.log
    echo "Response: ${BODY:0:500}" >> test_responses.log
    echo "" >> test_responses.log
}

# Clear previous log
> test_responses.log

echo "Starting tests at ${TIMESTAMP}"
echo ""

# Run test cases
test_length 0 "No custom_instructions" true
test_length 500 "Small instruction (500 chars)" true
test_length 2000 "At old enhanced limit (2000 chars)" true
test_length 3500 "Between old and new limit (3500 chars)" true
test_length 5000 "At new limit (5000 chars)" true
test_length 5001 "Over new limit (5001 chars - should fail)" false
test_length 6000 "Way over limit (6000 chars - should fail)" false

# Summary
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}TEST SUMMARY${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

for result in "${TEST_RESULTS[@]}"; do
    if [[ $result == *"✅ PASS"* ]]; then
        echo -e "${GREEN}${result}${NC}"
    elif [[ $result == *"❌ FAIL"* ]]; then
        echo -e "${RED}${result}${NC}"
    else
        echo -e "${YELLOW}${result}${NC}"
    fi
done

echo ""
PASSED=$(echo "${TEST_RESULTS[@]}" | grep -o "✅ PASS" | wc -l | tr -d ' ')
FAILED=$(echo "${TEST_RESULTS[@]}" | grep -o "❌ FAIL" | wc -l | tr -d ' ')
WARNED=$(echo "${TEST_RESULTS[@]}" | grep -o "⚠️  WARN" | wc -l | tr -d ' ')

echo "Total tests: ${#TEST_RESULTS[@]}"
echo -e "${GREEN}✅ Passed: ${PASSED}${NC}"
echo -e "${RED}❌ Failed: ${FAILED}${NC}"
if [ "$WARNED" -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Warnings: ${WARNED}${NC}"
fi

echo ""
echo "Detailed responses saved to: test_responses.log"

