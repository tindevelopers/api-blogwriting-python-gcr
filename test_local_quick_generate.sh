#!/bin/bash

# Test Quick Generate mode locally with the status code fix
# Make sure the local server is running: python main.py

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

LOCAL_URL="http://localhost:8000"
ENDPOINT="${LOCAL_URL}/api/v1/blog/generate-enhanced"

echo -e "${BOLD}${BLUE}============================================================${NC}"
echo -e "${BOLD}${BLUE}Local Test: Quick Generate Mode (Status Code Fix)${NC}"
echo -e "${BOLD}${BLUE}============================================================${NC}\n"

# Check if local server is running
echo -e "${CYAN}Checking if local server is running...${NC}"
if ! curl -s "${LOCAL_URL}/" > /dev/null 2>&1; then
    echo -e "${RED}❌ Local server is not running!${NC}"
    echo -e "${YELLOW}Please start the server first:${NC}"
    echo -e "${CYAN}  python main.py${NC}"
    echo -e "${CYAN}  or${NC}"
    echo -e "${CYAN}  uvicorn main:app --host 0.0.0.0 --port 8000${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Local server is running${NC}\n"

# Test payload with 100 word target
PAYLOAD=$(cat <<EOF
{
  "topic": "Benefits of Python Programming",
  "keywords": ["python", "programming", "coding", "development"],
  "blog_type": "tutorial",
  "tone": "professional",
  "length": "short",
  "word_count_target": 100,
  "mode": "quick_generate",
  "optimize_for_traffic": true,
  "use_dataforseo_content_generation": true,
  "async_mode": false
}
EOF
)

echo -e "${BOLD}Test Parameters:${NC}"
echo -e "${CYAN}Topic: Benefits of Python Programming${NC}"
echo -e "${CYAN}Keywords: python, programming, coding, development${NC}"
echo -e "${CYAN}Target Word Count: 100 words${NC}"
echo -e "${CYAN}Mode: quick_generate${NC}\n"

echo -e "${CYAN}Request Payload:${NC}"
echo "$PAYLOAD" | jq '.'
echo ""
echo -e "${CYAN}📡 Sending request to local server...${NC}\n"

START=$(date +%s)
RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST "${ENDPOINT}?async_mode=false" \
  -H "Content-Type: application/json" \
  -d "${PAYLOAD}" \
  --max-time 120)

END=$(date +%s)
DURATION=$((END - START))

HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS/d')

echo -e "${BOLD}Response Status: ${HTTP_STATUS}${NC}"
echo -e "${CYAN}Duration: ${DURATION} seconds${NC}\n"

if [ "$HTTP_STATUS" -eq 200 ]; then
    echo -e "${GREEN}✅ SUCCESS${NC}\n"
    
    # Extract key information
    TITLE=$(echo "$BODY" | jq -r '.title // "N/A"')
    CONTENT=$(echo "$BODY" | jq -r '.content // ""')
    WORD_COUNT=$(echo "$CONTENT" | wc -w | xargs)
    SUBTOPICS=$(echo "$BODY" | jq -r '.seo_metadata.subtopics // []')
    SUBTOPICS_COUNT=$(echo "$BODY" | jq -r '.seo_metadata.subtopics | length // 0')
    SEO_SCORE=$(echo "$BODY" | jq -r '.seo_score // "N/A"')
    COST=$(echo "$BODY" | jq -r '.total_cost // "N/A"')
    
    echo -e "${BOLD}Results:${NC}"
    echo -e "${CYAN}Title: ${TITLE}${NC}"
    echo -e "${CYAN}Word Count: ${WORD_COUNT} words${NC}"
    echo -e "${CYAN}Subtopics Count: ${SUBTOPICS_COUNT}${NC}"
    echo -e "${CYAN}SEO Score: ${SEO_SCORE}${NC}"
    echo -e "${CYAN}Total Cost: \$${COST}${NC}"
    echo ""
    
    if [ "$SUBTOPICS_COUNT" -gt 0 ]; then
        echo -e "${GREEN}✓ Subtopics Generated:${NC}"
        echo "$SUBTOPICS" | jq -r '.[]' | nl -w2 -s'. '
    else
        echo -e "${YELLOW}⚠ No subtopics generated${NC}"
    fi
    
    echo ""
    echo -e "${CYAN}Content Preview (first 300 chars):${NC}"
    echo "$CONTENT" | head -c 300
    echo "..."
    
    # Save response
    echo "$BODY" | jq '.' > /tmp/local_quick_generate_response.json
    echo -e "\n${CYAN}Full response saved to: /tmp/local_quick_generate_response.json${NC}"
    
elif [ "$HTTP_STATUS" -eq 500 ]; then
    echo -e "${RED}❌ ERROR - Server Error${NC}"
    echo -e "${YELLOW}This should now show the actual DataForSEO API error (status code fix working)${NC}\n"
    
    ERROR_MSG=$(echo "$BODY" | jq -r '.message // .detail // .error // "Unknown error"' 2>/dev/null || echo "$BODY")
    echo -e "${BOLD}Error Message:${NC}"
    echo -e "${RED}${ERROR_MSG}${NC}\n"
    
    # Check if error mentions status code (fix is working)
    if echo "$ERROR_MSG" | grep -q "status_code"; then
        echo -e "${GREEN}✅ Status code fix is working!${NC}"
        echo -e "${CYAN}The error now shows the actual DataForSEO API status code instead of 'empty content'${NC}"
    else
        echo -e "${YELLOW}⚠ Error message doesn't mention status_code - check logs for details${NC}"
    fi
    
    echo ""
    echo -e "${CYAN}Full Error Response:${NC}"
    echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY"
    
else
    echo -e "${RED}❌ ERROR - HTTP ${HTTP_STATUS}${NC}"
    echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY"
fi

echo ""
echo -e "${BOLD}${BLUE}============================================================${NC}"
echo -e "${BOLD}${BLUE}Test Complete${NC}"
echo -e "${BOLD}${BLUE}============================================================${NC}\n"

echo -e "${CYAN}To check server logs, look at the terminal where you ran 'python main.py'${NC}"
echo -e "${CYAN}The logs should show:${NC}"
echo -e "${CYAN}  - DataForSEO API status code${NC}"
echo -e "${CYAN}  - Error message if status != 20000${NC}"
echo -e "${CYAN}  - Clear indication of what went wrong${NC}"

