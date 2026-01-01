#!/bin/bash

# Comprehensive test script for both Quick Generate and Multi-Phase modes
# Tests all features of each generation mode with a small blog request (100 words)

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
echo -e "${BOLD}${BLUE}Comprehensive Blog Generation Test${NC}"
echo -e "${BOLD}${BLUE}Testing Both Quick Generate & Multi-Phase Modes${NC}"
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
echo -e "${CYAN}Blog Type: ${BLOG_TYPE}${NC}\n"

# ============================================================================
# TEST 1: Quick Generate Mode (DataForSEO)
# ============================================================================
echo -e "${BOLD}${BLUE}============================================================${NC}"
echo -e "${BOLD}${BLUE}TEST 1: Quick Generate Mode (DataForSEO)${NC}"
echo -e "${BOLD}${BLUE}============================================================${NC}\n"

echo -e "${CYAN}Features being tested:${NC}"
echo -e "  ✓ DataForSEO Content Generation API"
echo -e "  ✓ Fast generation (30-60 seconds)"
echo -e "  ✓ Cost-effective (~\$0.001-0.002)"
echo -e "  ✓ SEO optimization built-in"
echo -e "  ✓ Subtopics generation"
echo -e "  ✓ Meta tags generation"
echo -e "  ✓ Word count targeting"
echo -e "  ✓ Blog type support (tutorial)"
echo -e "  ✓ Tone customization"
echo ""

QUICK_PAYLOAD=$(cat <<EOF
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
echo "$QUICK_PAYLOAD" | jq '.'
echo ""
echo -e "${CYAN}📡 Sending request (synchronous)...${NC}\n"

QUICK_START=$(date +%s)
QUICK_RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST "${ENDPOINT}?async_mode=false" \
  -H "Content-Type: application/json" \
  -d "${QUICK_PAYLOAD}" \
  --max-time 120)
QUICK_END=$(date +%s)
QUICK_DURATION=$((QUICK_END - QUICK_START))

HTTP_STATUS=$(echo "$QUICK_RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
QUICK_BODY=$(echo "$QUICK_RESPONSE" | sed '/HTTP_STATUS/d')

echo -e "${BOLD}Response Status: ${HTTP_STATUS}${NC}"
echo -e "${CYAN}Duration: ${QUICK_DURATION} seconds${NC}\n"

if [ "$HTTP_STATUS" -eq 200 ]; then
    echo -e "${GREEN}✅ Quick Generate SUCCESS${NC}\n"
    
    # Extract key information
    QUICK_TITLE=$(echo "$QUICK_BODY" | jq -r '.title // "N/A"')
    QUICK_CONTENT=$(echo "$QUICK_BODY" | jq -r '.content // ""')
    QUICK_WORD_COUNT=$(echo "$QUICK_CONTENT" | wc -w | xargs)
    QUICK_SUBTOPICS=$(echo "$QUICK_BODY" | jq -r '.seo_metadata.subtopics // []')
    QUICK_SUBTOPICS_COUNT=$(echo "$QUICK_BODY" | jq -r '.seo_metadata.subtopics | length // 0')
    QUICK_SEO_SCORE=$(echo "$QUICK_BODY" | jq -r '.seo_score // "N/A"')
    QUICK_COST=$(echo "$QUICK_BODY" | jq -r '.total_cost // "N/A"')
    QUICK_META_TITLE=$(echo "$QUICK_BODY" | jq -r '.meta_title // "N/A"')
    QUICK_META_DESC=$(echo "$QUICK_BODY" | jq -r '.meta_description // "N/A"')
    
    echo -e "${BOLD}Results:${NC}"
    echo -e "${CYAN}Title: ${QUICK_TITLE}${NC}"
    echo -e "${CYAN}Word Count: ${QUICK_WORD_COUNT} words (target: ${WORD_COUNT})${NC}"
    echo -e "${CYAN}Subtopics Count: ${QUICK_SUBTOPICS_COUNT}${NC}"
    echo -e "${CYAN}SEO Score: ${QUICK_SEO_SCORE}${NC}"
    echo -e "${CYAN}Total Cost: \$${QUICK_COST}${NC}"
    echo -e "${CYAN}Meta Title: ${QUICK_META_TITLE}${NC}"
    echo ""
    
    if [ "$QUICK_SUBTOPICS_COUNT" -gt 0 ]; then
        echo -e "${GREEN}✓ Subtopics Generated:${NC}"
        echo "$QUICK_SUBTOPICS" | jq -r '.[]' | nl -w2 -s'. '
    else
        echo -e "${YELLOW}⚠ No subtopics generated${NC}"
    fi
    
    echo ""
    echo -e "${CYAN}Content Preview (first 200 chars):${NC}"
    echo "$QUICK_CONTENT" | head -c 200
    echo "..."
    
    # Save full response
    echo "$QUICK_BODY" | jq '.' > /tmp/quick_generate_response.json
    echo -e "\n${CYAN}Full response saved to: /tmp/quick_generate_response.json${NC}"
    
else
    echo -e "${RED}❌ Quick Generate FAILED${NC}"
    echo "$QUICK_BODY" | jq '.' 2>/dev/null || echo "$QUICK_BODY"
fi

echo -e "\n${BOLD}${BLUE}============================================================${NC}\n"

# ============================================================================
# TEST 2: Multi-Phase Mode (Comprehensive Pipeline)
# ============================================================================
echo -e "${BOLD}${BLUE}============================================================${NC}"
echo -e "${BOLD}${BLUE}TEST 2: Multi-Phase Mode (Comprehensive Pipeline)${NC}"
echo -e "${BOLD}${BLUE}============================================================${NC}\n"

echo -e "${CYAN}Features being tested:${NC}"
echo -e "  ✓ MultiStageGenerationPipeline (12 stages)"
echo -e "  ✓ Google Custom Search research"
echo -e "  ✓ Fact-checking"
echo -e "  ✓ Citations and sources"
echo -e "  ✓ SERP optimization"
echo -e "  ✓ Knowledge Graph integration"
echo -e "  ✓ Semantic keywords"
echo -e "  ✓ Quality scoring"
echo -e "  ✓ Premium content quality"
echo ""

MULTI_PHASE_PAYLOAD=$(cat <<EOF
{
  "topic": "${TOPIC}",
  "keywords": ${KEYWORDS},
  "blog_type": "${BLOG_TYPE}",
  "tone": "professional",
  "length": "short",
  "word_count_target": ${WORD_COUNT},
  "mode": "multi_phase",
  "optimize_for_traffic": true,
  "use_dataforseo_content_generation": false,
  "use_google_search": true,
  "use_fact_checking": true,
  "use_citations": true,
  "use_serp_optimization": true,
  "use_consensus_generation": false,
  "use_knowledge_graph": true,
  "use_semantic_keywords": true,
  "use_quality_scoring": true,
  "async_mode": false
}
EOF
)

echo -e "${CYAN}Request Payload:${NC}"
echo "$MULTI_PHASE_PAYLOAD" | jq '.'
echo ""
echo -e "${CYAN}📡 Sending request (synchronous, may take 3-5 minutes)...${NC}\n"

MULTI_START=$(date +%s)
MULTI_RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST "${ENDPOINT}?async_mode=false" \
  -H "Content-Type: application/json" \
  -d "${MULTI_PHASE_PAYLOAD}" \
  --max-time 300)
MULTI_END=$(date +%s)
MULTI_DURATION=$((MULTI_END - MULTI_START))

HTTP_STATUS=$(echo "$MULTI_RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
MULTI_BODY=$(echo "$MULTI_RESPONSE" | sed '/HTTP_STATUS/d')

echo -e "${BOLD}Response Status: ${HTTP_STATUS}${NC}"
echo -e "${CYAN}Duration: ${MULTI_DURATION} seconds${NC}\n"

if [ "$HTTP_STATUS" -eq 200 ]; then
    echo -e "${GREEN}✅ Multi-Phase SUCCESS${NC}\n"
    
    # Extract key information
    MULTI_TITLE=$(echo "$MULTI_BODY" | jq -r '.title // "N/A"')
    MULTI_CONTENT=$(echo "$MULTI_BODY" | jq -r '.content // ""')
    MULTI_WORD_COUNT=$(echo "$MULTI_CONTENT" | wc -w | xargs)
    MULTI_SUBTOPICS=$(echo "$MULTI_BODY" | jq -r '.seo_metadata.subtopics // []')
    MULTI_SUBTOPICS_COUNT=$(echo "$MULTI_BODY" | jq -r '.seo_metadata.subtopics | length // 0')
    MULTI_SEO_SCORE=$(echo "$MULTI_BODY" | jq -r '.seo_score // "N/A"')
    MULTI_COST=$(echo "$MULTI_BODY" | jq -r '.total_cost // "N/A"')
    MULTI_CITATIONS=$(echo "$MULTI_BODY" | jq -r '.citations // []')
    MULTI_CITATIONS_COUNT=$(echo "$MULTI_BODY" | jq -r '.citations | length // 0')
    MULTI_QUALITY_SCORE=$(echo "$MULTI_BODY" | jq -r '.quality_score // "N/A"')
    MULTI_STAGE_RESULTS=$(echo "$MULTI_BODY" | jq -r '.stage_results // []')
    MULTI_STAGE_COUNT=$(echo "$MULTI_BODY" | jq -r '.stage_results | length // 0')
    
    echo -e "${BOLD}Results:${NC}"
    echo -e "${CYAN}Title: ${MULTI_TITLE}${NC}"
    echo -e "${CYAN}Word Count: ${MULTI_WORD_COUNT} words (target: ${WORD_COUNT})${NC}"
    echo -e "${CYAN}Subtopics Count: ${MULTI_SUBTOPICS_COUNT}${NC}"
    echo -e "${CYAN}Citations Count: ${MULTI_CITATIONS_COUNT}${NC}"
    echo -e "${CYAN}Pipeline Stages: ${MULTI_STAGE_COUNT}${NC}"
    echo -e "${CYAN}SEO Score: ${MULTI_SEO_SCORE}${NC}"
    echo -e "${CYAN}Quality Score: ${MULTI_QUALITY_SCORE}${NC}"
    echo -e "${CYAN}Total Cost: \$${MULTI_COST}${NC}"
    echo ""
    
    if [ "$MULTI_SUBTOPICS_COUNT" -gt 0 ]; then
        echo -e "${GREEN}✓ Subtopics Generated:${NC}"
        echo "$MULTI_SUBTOPICS" | jq -r '.[]' | nl -w2 -s'. '
    else
        echo -e "${YELLOW}⚠ No subtopics generated${NC}"
    fi
    
    if [ "$MULTI_CITATIONS_COUNT" -gt 0 ]; then
        echo ""
        echo -e "${GREEN}✓ Citations:${NC}"
        echo "$MULTI_CITATIONS" | jq -r '.[] | "  - \(.title // .url)"' | head -5
    fi
    
    if [ "$MULTI_STAGE_COUNT" -gt 0 ]; then
        echo ""
        echo -e "${GREEN}✓ Pipeline Stages Executed:${NC}"
        echo "$MULTI_STAGE_RESULTS" | jq -r '.[] | "  - \(.stage_name): \(.status)"' | head -10
    fi
    
    echo ""
    echo -e "${CYAN}Content Preview (first 200 chars):${NC}"
    echo "$MULTI_CONTENT" | head -c 200
    echo "..."
    
    # Save full response
    echo "$MULTI_BODY" | jq '.' > /tmp/multi_phase_response.json
    echo -e "\n${CYAN}Full response saved to: /tmp/multi_phase_response.json${NC}"
    
else
    echo -e "${RED}❌ Multi-Phase FAILED${NC}"
    echo "$MULTI_BODY" | jq '.' 2>/dev/null || echo "$MULTI_BODY"
fi

echo -e "\n${BOLD}${BLUE}============================================================${NC}"

# ============================================================================
# SUMMARY COMPARISON
# ============================================================================
echo -e "${BOLD}${BLUE}============================================================${NC}"
echo -e "${BOLD}${BLUE}SUMMARY COMPARISON${NC}"
echo -e "${BOLD}${BLUE}============================================================${NC}\n"

echo -e "${BOLD}Quick Generate Mode:${NC}"
if [ "$HTTP_STATUS" -eq 200 ] && [ -n "$QUICK_CONTENT" ]; then
    echo -e "  ${GREEN}✓ Status: SUCCESS${NC}"
    echo -e "  ${CYAN}Duration: ${QUICK_DURATION}s${NC}"
    echo -e "  ${CYAN}Word Count: ${QUICK_WORD_COUNT} words${NC}"
    echo -e "  ${CYAN}Subtopics: ${QUICK_SUBTOPICS_COUNT}${NC}"
    echo -e "  ${CYAN}SEO Score: ${QUICK_SEO_SCORE}${NC}"
    echo -e "  ${CYAN}Cost: \$${QUICK_COST}${NC}"
else
    echo -e "  ${RED}✗ Status: FAILED${NC}"
fi

echo ""
echo -e "${BOLD}Multi-Phase Mode:${NC}"
if [ "$HTTP_STATUS" -eq 200 ] && [ -n "$MULTI_CONTENT" ]; then
    echo -e "  ${GREEN}✓ Status: SUCCESS${NC}"
    echo -e "  ${CYAN}Duration: ${MULTI_DURATION}s${NC}"
    echo -e "  ${CYAN}Word Count: ${MULTI_WORD_COUNT} words${NC}"
    echo -e "  ${CYAN}Subtopics: ${MULTI_SUBTOPICS_COUNT}${NC}"
    echo -e "  ${CYAN}Citations: ${MULTI_CITATIONS_COUNT}${NC}"
    echo -e "  ${CYAN}Pipeline Stages: ${MULTI_STAGE_COUNT}${NC}"
    echo -e "  ${CYAN}SEO Score: ${MULTI_SEO_SCORE}${NC}"
    echo -e "  ${CYAN}Quality Score: ${MULTI_QUALITY_SCORE}${NC}"
    echo -e "  ${CYAN}Cost: \$${MULTI_COST}${NC}"
else
    echo -e "  ${RED}✗ Status: FAILED${NC}"
fi

echo ""
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}Test completed!${NC}"
echo -e "${GREEN}============================================================${NC}\n"







