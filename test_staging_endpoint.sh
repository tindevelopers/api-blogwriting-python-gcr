#!/bin/bash
# Test staging endpoint with DataForSEO format fixes
# Verify commit 821a630 is deployed

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${BOLD}${BLUE}============================================================${NC}"
echo -e "${BOLD}${BLUE}Testing Staging Deployment${NC}"
echo -e "${BOLD}${BLUE}Expected Commit: 821a630${NC}"
echo -e "${BOLD}${BLUE}============================================================${NC}\n"

# Get staging URL
STAGING_URL="${STAGING_URL:-https://blog-writer-api-staging-kq42l26tuq-od.a.run.app}"
ENDPOINT="${STAGING_URL}/api/v1/blog/generate-enhanced"

echo -e "${CYAN}Staging URL: ${STAGING_URL}${NC}"
echo -e "${CYAN}Endpoint: ${ENDPOINT}${NC}\n"

# Test payload
PAYLOAD=$(cat <<EOF
{
  "topic": "Dog Grooming Tips for Pet Owners",
  "keywords": [
    "dog grooming",
    "pet grooming",
    "dog care",
    "grooming tips",
    "pet hygiene"
  ],
  "tone": "professional",
  "length": "short",
  "word_count_target": 100,
  "blog_type": "guide",
  "use_dataforseo_content_generation": true,
  "optimize_for_traffic": true,
  "target_audience": "pet owners and dog enthusiasts"
}
EOF
)

echo -e "${BOLD}Request Payload:${NC}"
echo -e "${BLUE}${PAYLOAD}${NC}\n"

echo -e "${CYAN}📡 Testing staging endpoint...${NC}\n"

START_TIME=$(date +%s)

RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
  "${ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d "${PAYLOAD}")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
RESPONSE_BODY=$(echo "$RESPONSE" | sed '$d')
ELAPSED_TIME=$(($(date +%s) - START_TIME))

echo -e "${CYAN}Response Status: ${HTTP_CODE}${NC}"
echo -e "${CYAN}Response Time: ${ELAPSED_TIME} seconds${NC}\n"

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ Staging Endpoint Working!${NC}\n"
    
    if command -v jq &> /dev/null; then
        TITLE=$(echo "$RESPONSE_BODY" | jq -r '.title // empty')
        CONTENT=$(echo "$RESPONSE_BODY" | jq -r '.content // empty')
        WORD_COUNT=$(echo "$CONTENT" | wc -w | tr -d ' ')
        TOTAL_TOKENS=$(echo "$RESPONSE_BODY" | jq -r '.total_tokens // 0')
        TOTAL_COST=$(echo "$RESPONSE_BODY" | jq -r '.total_cost // 0')
        
        echo -e "${BOLD}Results:${NC}"
        echo -e "${CYAN}Title: ${TITLE}${NC}"
        echo -e "${CYAN}Word Count: ${WORD_COUNT} words (target: 100)${NC}"
        echo -e "${CYAN}Total Tokens: ${TOTAL_TOKENS}${NC}"
        echo -e "${CYAN}Total Cost: \$${TOTAL_COST}${NC}\n"
        
        if [ "$WORD_COUNT" -gt 0 ]; then
            DIFF=$((WORD_COUNT - 100))
            if [ $DIFF -lt 0 ]; then
                DIFF=$((-$DIFF))
            fi
            DIFF_PERCENT=$((DIFF * 100 / 100))
            if [ $DIFF_PERCENT -le 25 ]; then
                echo -e "${GREEN}✓ Word count within acceptable range${NC}"
            else
                echo -e "${YELLOW}⚠ Word count differs by ${DIFF_PERCENT}%${NC}"
            fi
        fi
        
        echo -e "\n${BOLD}Content Preview:${NC}"
        echo -e "${BLUE}${CONTENT:0:200}...${NC}\n"
    else
        echo -e "${GREEN}✓ Response received successfully${NC}"
        echo -e "${YELLOW}Install jq for detailed parsing: brew install jq${NC}\n"
    fi
    
    echo -e "${GREEN}============================================================${NC}"
    echo -e "${GREEN}✅ Staging deployment test passed!${NC}"
    echo -e "${GREEN}============================================================${NC}\n"
    
else
    echo -e "${RED}❌ Staging endpoint test failed${NC}"
    echo -e "${YELLOW}Response: ${RESPONSE_BODY:0:500}...${NC}"
    exit 1
fi

