#!/bin/bash
# Test /api/v1/blog/generate-enhanced endpoint with new DataForSEO format
# Tests a 100-word blog about dog grooming

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${BOLD}${BLUE}============================================================${NC}"
echo -e "${BOLD}${BLUE}Testing /api/v1/blog/generate-enhanced${NC}"
echo -e "${BOLD}${BLUE}Topic: Dog Grooming Tips for Pet Owners${NC}"
echo -e "${BOLD}${BLUE}Target: 100 words${NC}"
echo -e "${BOLD}${BLUE}============================================================${NC}\n"

# Determine API URL (use Cloud Run dev URL if not specified)
API_URL="${API_URL:-https://blog-writer-api-dev-kq42l26tuq-od.a.run.app}"
ENDPOINT="${API_URL}/api/v1/blog/generate-enhanced"

echo -e "${CYAN}API Endpoint: ${ENDPOINT}${NC}\n"

# Create JSON payload
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

echo -e "${CYAN}📡 Sending request...${NC}\n"

START_TIME=$(date +%s)

# Make the request
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
  "${ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d "${PAYLOAD}")

# Extract HTTP status code (last line)
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
# Extract response body (all but last line)
RESPONSE_BODY=$(echo "$RESPONSE" | sed '$d')

ELAPSED_TIME=$(($(date +%s) - START_TIME))

echo -e "${CYAN}Response Status: ${HTTP_CODE}${NC}"
echo -e "${CYAN}Response Time: ${ELAPSED_TIME} seconds${NC}\n"

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ Blog Generated Successfully!${NC}\n"
    
    # Parse response using jq if available, otherwise use grep
    if command -v jq &> /dev/null; then
        TITLE=$(echo "$RESPONSE_BODY" | jq -r '.title // empty')
        CONTENT=$(echo "$RESPONSE_BODY" | jq -r '.content // empty')
        META_TITLE=$(echo "$RESPONSE_BODY" | jq -r '.meta_title // empty')
        META_DESC=$(echo "$RESPONSE_BODY" | jq -r '.meta_description // empty')
        WORD_COUNT=$(echo "$CONTENT" | wc -w | tr -d ' ')
        READABILITY=$(echo "$RESPONSE_BODY" | jq -r '.readability_score // 0')
        SEO_SCORE=$(echo "$RESPONSE_BODY" | jq -r '.seo_score // 0')
        TOTAL_TOKENS=$(echo "$RESPONSE_BODY" | jq -r '.total_tokens // 0')
        TOTAL_COST=$(echo "$RESPONSE_BODY" | jq -r '.total_cost // 0')
        SUBTOPICS=$(echo "$RESPONSE_BODY" | jq -r '.subtopics[]? // empty' 2>/dev/null | head -10)
    else
        # Fallback parsing with grep
        TITLE=$(echo "$RESPONSE_BODY" | grep -o '"title":"[^"]*"' | sed 's/"title":"//;s/"$//' | head -1)
        CONTENT=$(echo "$RESPONSE_BODY" | grep -o '"content":"[^"]*"' | sed 's/"content":"//;s/"$//' | head -1)
        META_TITLE=$(echo "$RESPONSE_BODY" | grep -o '"meta_title":"[^"]*"' | sed 's/"meta_title":"//;s/"$//' | head -1)
        META_DESC=$(echo "$RESPONSE_BODY" | grep -o '"meta_description":"[^"]*"' | sed 's/"meta_description":"//;s/"$//' | head -1)
        WORD_COUNT=$(echo "$CONTENT" | wc -w | tr -d ' ')
    fi
    
    echo -e "${BOLD}Generated Blog:${NC}"
    echo -e "${BLUE}============================================================${NC}"
    echo -e "${BOLD}Title:${NC} ${TITLE}"
    echo -e "${BOLD}Word Count:${NC} ${WORD_COUNT} words (target: 100)"
    if [ -n "$READABILITY" ]; then
        echo -e "${BOLD}Readability Score:${NC} ${READABILITY}/100"
    fi
    if [ -n "$SEO_SCORE" ]; then
        echo -e "${BOLD}SEO Score:${NC} ${SEO_SCORE}/100"
    fi
    echo -e "${BLUE}============================================================${NC}\n"
    
    if [ -n "$META_TITLE" ]; then
        echo -e "${BOLD}Meta Title:${NC}"
        echo -e "${BLUE}${META_TITLE}${NC}\n"
    fi
    
    if [ -n "$META_DESC" ]; then
        echo -e "${BOLD}Meta Description:${NC}"
        echo -e "${BLUE}${META_DESC}${NC}\n"
    fi
    
    if [ -n "$SUBTOPICS" ]; then
        echo -e "${BOLD}Subtopics Generated:${NC}"
        echo "$SUBTOPICS" | nl -w2 -s'. '
        echo
    fi
    
    echo -e "${BOLD}Blog Content:${NC}"
    echo -e "${BLUE}${CONTENT}${NC}\n"
    
    if [ -n "$TOTAL_TOKENS" ] && [ "$TOTAL_TOKENS" != "0" ]; then
        echo -e "${BOLD}Performance Metrics:${NC}"
        echo -e "${CYAN}Total Tokens: ${TOTAL_TOKENS}${NC}"
        if [ -n "$TOTAL_COST" ]; then
            echo -e "${CYAN}Total Cost: \$${TOTAL_COST}${NC}"
        fi
        echo -e "${CYAN}Generation Time: ${ELAPSED_TIME} seconds${NC}\n"
    fi
    
    # Word count check
    if [ "$WORD_COUNT" -gt 0 ]; then
        DIFF=$((WORD_COUNT - 100))
        if [ $DIFF -lt 0 ]; then
            DIFF=$((-$DIFF))
        fi
        DIFF_PERCENT=$((DIFF * 100 / 100))
        if [ $DIFF_PERCENT -le 25 ]; then
            echo -e "${GREEN}✓ Word count within acceptable range (${DIFF_PERCENT}% difference)${NC}"
        else
            echo -e "${YELLOW}⚠ Word count differs by ${DIFF_PERCENT}% from target${NC}"
        fi
    fi
    
    # Save to file
    OUTPUT_FILE="generated_blog_dog_grooming.md"
    cat > "$OUTPUT_FILE" <<EOF
# ${TITLE}

**Meta Description:** ${META_DESC}

---

${CONTENT}

---

## Blog Details

- **Topic:** Dog Grooming Tips for Pet Owners
- **Word Count:** ${WORD_COUNT} words (target: 100)
- **Generated:** $(date +"%Y-%m-%d %H:%M:%S")
- **API:** DataForSEO Content Generation API
EOF

    if [ -n "$TOTAL_COST" ] && [ "$TOTAL_COST" != "0" ]; then
        echo "- **Cost:** \$${TOTAL_COST}" >> "$OUTPUT_FILE"
    fi
    if [ -n "$TOTAL_TOKENS" ] && [ "$TOTAL_TOKENS" != "0" ]; then
        echo "- **Tokens Used:** ${TOTAL_TOKENS}" >> "$OUTPUT_FILE"
    fi
    
    echo -e "\n${GREEN}✓ Blog saved to: ${OUTPUT_FILE}${NC}\n"
    
    echo -e "${GREEN}============================================================${NC}"
    echo -e "${GREEN}Test completed successfully!${NC}"
    echo -e "${GREEN}============================================================${NC}\n"
    
else
    echo -e "${RED}❌ Request failed with status ${HTTP_CODE}${NC}"
    echo -e "${YELLOW}Response: ${RESPONSE_BODY:0:500}...${NC}"
    exit 1
fi

