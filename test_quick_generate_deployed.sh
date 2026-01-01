#!/bin/bash

# Test Quick Generate mode on deployed Cloud Run service
# Tests the status code fix we just deployed

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

BASE_URL="https://blog-writer-api-dev-kq42l26tuq-od.a.run.app"
ENDPOINT="${BASE_URL}/api/v1/blog/generate-enhanced"

echo -e "${BOLD}${BLUE}============================================================${NC}"
echo -e "${BOLD}${BLUE}Testing Quick Generate Mode (DataForSEO)${NC}"
echo -e "${BOLD}${BLUE}Deployed Endpoint Test${NC}"
echo -e "${BOLD}${BLUE}============================================================${NC}\n"

# Test parameters
TOPIC="Benefits of Python Programming"
KEYWORDS='["python", "programming", "coding", "development"]'
WORD_COUNT=100
BLOG_TYPE="tutorial"

echo -e "${BOLD}Test Parameters:${NC}"
echo -e "${CYAN}Topic: ${TOPIC}${NC}"
echo -e "${CYAN}Keywords: ${KEYWORDS}${NC}"
echo -e "${CYAN}Target Word Count: ${WORD_COUNT} words${NC}"
echo -e "${CYAN}Blog Type: ${BLOG_TYPE}${NC}"
echo -e "${CYAN}Mode: quick_generate${NC}\n"

# Test payload
PAYLOAD=$(cat <<EOF
{
  "topic": "${TOPIC}",
  "keywords": ${KEYWORDS},
  "blog_type": "${BLOG_TYPE}",
  "tone": "professional",
  "length": "short",
  "word_count_target": ${WORD_COUNT},
  "mode": "quick_generate",
  "optimize_for_traffic": true,
  "use_dataforseo_content_generation": true,
  "use_google_search": false,
  "use_fact_checking": false,
  "use_citations": false,
  "use_serp_optimization": true,
  "use_consensus_generation": false,
  "use_knowledge_graph": false,
  "use_semantic_keywords": true,
  "use_quality_scoring": true,
  "async_mode": false
}
EOF
)

echo -e "${CYAN}Request Payload:${NC}"
echo "$PAYLOAD" | jq '.'
echo ""
echo -e "${CYAN}📡 Sending request to deployed endpoint...${NC}"
echo -e "${CYAN}Endpoint: ${ENDPOINT}${NC}\n"

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
    echo -e "${GREEN}✅ SUCCESS - Quick Generate Working!${NC}\n"
    
    # Extract key information
    TITLE=$(echo "$BODY" | jq -r '.title // "N/A"')
    CONTENT=$(echo "$BODY" | jq -r '.content // ""')
    WORD_COUNT=$(echo "$CONTENT" | wc -w | xargs)
    SUBTOPICS=$(echo "$BODY" | jq -r '.seo_metadata.subtopics // []')
    SUBTOPICS_COUNT=$(echo "$BODY" | jq -r '.seo_metadata.subtopics | length // 0')
    SEO_SCORE=$(echo "$BODY" | jq -r '.seo_score // "N/A"')
    COST=$(echo "$BODY" | jq -r '.total_cost // "N/A"')
    META_TITLE=$(echo "$BODY" | jq -r '.meta_title // "N/A"')
    META_DESC=$(echo "$BODY" | jq -r '.meta_description // "N/A"')
    
    echo -e "${BOLD}Results:${NC}"
    echo -e "${CYAN}Title: ${TITLE}${NC}"
    echo -e "${CYAN}Word Count: ${WORD_COUNT} words (target: ${WORD_COUNT})${NC}"
    echo -e "${CYAN}Subtopics Count: ${SUBTOPICS_COUNT}${NC}"
    echo -e "${CYAN}SEO Score: ${SEO_SCORE}${NC}"
    echo -e "${CYAN}Total Cost: \$${COST}${NC}"
    echo -e "${CYAN}Meta Title: ${META_TITLE}${NC}"
    echo ""
    
    if [ "$SUBTOPICS_COUNT" -gt 0 ]; then
        echo -e "${GREEN}✓ Subtopics Generated:${NC}"
        echo "$SUBTOPICS" | jq -r '.[]' | nl -w2 -s'. '
        echo ""
    else
        echo -e "${YELLOW}⚠ No subtopics generated${NC}"
        echo ""
    fi
    
    echo -e "${CYAN}Content Preview (first 300 chars):${NC}"
    echo "$CONTENT" | head -c 300
    echo "..."
    echo ""
    
    # Save full response
    echo "$BODY" | jq '.' > /tmp/quick_generate_deployed_response.json
    echo -e "${CYAN}Full response saved to: /tmp/quick_generate_deployed_response.json${NC}"
    
    echo ""
    echo -e "${GREEN}✅ Quick Generate Mode is working correctly!${NC}"
    
elif [ "$HTTP_STATUS" -eq 500 ]; then
    echo -e "${RED}❌ ERROR - Server Error${NC}\n"
    
    ERROR_MSG=$(echo "$BODY" | jq -r '.message // .detail // .error // "Unknown error"' 2>/dev/null || echo "$BODY")
    
    echo -e "${BOLD}Error Message:${NC}"
    echo -e "${RED}${ERROR_MSG}${NC}\n"
    
    # Check if error mentions status code (fix is working)
    if echo "$ERROR_MSG" | grep -qi "status_code"; then
        echo -e "${GREEN}✅ Status code fix is working!${NC}"
        echo -e "${CYAN}The error now shows the actual DataForSEO API status code${NC}"
        echo -e "${CYAN}instead of the generic 'empty content' error.${NC}\n"
        
        # Extract status code if present
        STATUS_CODE=$(echo "$ERROR_MSG" | grep -oE "status_code[=:]\s*[0-9]+" | grep -oE "[0-9]+" | head -1)
        if [ -n "$STATUS_CODE" ]; then
            echo -e "${BOLD}DataForSEO API Status Code: ${STATUS_CODE}${NC}"
            case "$STATUS_CODE" in
                40204)
                    echo -e "${YELLOW}⚠️  Status 40204: Subscription required${NC}"
                    echo -e "${CYAN}   Check DataForSEO plan includes Content Generation API${NC}"
                    ;;
                40501)
                    echo -e "${YELLOW}⚠️  Status 40501: Invalid field${NC}"
                    echo -e "${CYAN}   API format may have changed${NC}"
                    ;;
                *)
                    echo -e "${YELLOW}⚠️  Check DataForSEO API documentation for status code ${STATUS_CODE}${NC}"
                    ;;
            esac
        fi
    else
        echo -e "${YELLOW}⚠️  Error message doesn't mention status_code${NC}"
        echo -e "${CYAN}   Check Cloud Run logs for more details${NC}"
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

echo -e "${CYAN}To check Cloud Run logs:${NC}"
echo -e "${CYAN}  gcloud logging read \"resource.type=cloud_run_revision AND resource.labels.service_name=blog-writer-api-dev\" --project=api-ai-blog-writer --limit=50${NC}"







