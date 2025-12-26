#!/bin/bash

# Comprehensive test script for both Quick Generate and Multi-Phase modes
# Tests all features including recent improvements (2025-01-15)

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

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="test-results-${TIMESTAMP}"
mkdir -p "$OUTPUT_DIR"

echo -e "${BOLD}${BLUE}============================================================${NC}"
echo -e "${BOLD}${BLUE}Comprehensive Blog Generation Test${NC}"
echo -e "${BOLD}${BLUE}Testing Both Quick Generate & Multi-Phase Modes${NC}"
echo -e "${BOLD}${BLUE}With Latest Improvements (2025-01-15)${NC}"
echo -e "${BOLD}${BLUE}============================================================${NC}\n"

# Test parameters
TOPIC="Benefits of Python Programming"
KEYWORDS='["python", "programming", "coding", "development"]'
WORD_COUNT=500
BLOG_TYPE="tutorial"

echo -e "${BOLD}Test Parameters:${NC}"
echo -e "${CYAN}Topic: ${TOPIC}${NC}"
echo -e "${CYAN}Keywords: ${KEYWORDS}${NC}"
echo -e "${CYAN}Target Word Count: ${WORD_COUNT} words${NC}"
echo -e "${CYAN}Blog Type: ${BLOG_TYPE}${NC}"
echo -e "${CYAN}Output Directory: ${OUTPUT_DIR}${NC}\n"

# ============================================================================
# TEST 1: Quick Generate Mode (DataForSEO)
# ============================================================================
echo -e "${BOLD}${BLUE}============================================================${NC}"
echo -e "${BOLD}${BLUE}TEST 1: Quick Generate Mode (DataForSEO)${NC}"
echo -e "${BOLD}${BLUE}============================================================${NC}\n"

echo -e "${CYAN}Features being tested:${NC}"
echo -e "  ✓ DataForSEO Content Generation API"
echo -e "  ✓ Fast generation (30-90 seconds)"
echo -e "  ✓ Cost-effective"
echo -e "  ✓ SEO optimization built-in"
echo -e "  ✓ Subtopics generation"
echo -e "  ✓ Meta tags generation"
echo ""

QUICK_PAYLOAD=$(cat <<EOF
{
  "topic": "${TOPIC}",
  "keywords": ${KEYWORDS},
  "blog_type": "${BLOG_TYPE}",
  "tone": "professional",
  "length": "medium",
  "word_count_target": ${WORD_COUNT},
  "mode": "quick_generate",
  "optimize_for_traffic": true,
  "use_dataforseo_content_generation": true,
  "async_mode": false
}
EOF
)

echo -e "${CYAN}📡 Sending Quick Generate request...${NC}\n"
echo -e "${YELLOW}Payload:${NC}"
echo "$QUICK_PAYLOAD" | jq '.' | head -15
echo ""

QUICK_START=$(date +%s)
QUICK_RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST "${ENDPOINT}?async_mode=false" \
  -H "Content-Type: application/json" \
  -d "${QUICK_PAYLOAD}" \
  --max-time 120)

QUICK_END=$(date +%s)
QUICK_DURATION=$((QUICK_END - QUICK_START))

HTTP_STATUS=$(echo "$QUICK_RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
QUICK_BODY=$(echo "$QUICK_RESPONSE" | sed '/HTTP_STATUS/d')

echo -e "${CYAN}Response Time: ${QUICK_DURATION} seconds${NC}"
echo -e "${CYAN}HTTP Status: ${HTTP_STATUS}${NC}\n"

if [ "$HTTP_STATUS" -eq 200 ]; then
    echo -e "${GREEN}✅ Quick Generate SUCCESS${NC}\n"
    
    # Save full response
    echo "$QUICK_BODY" | jq '.' > "${OUTPUT_DIR}/quick_generate_response.json"
    
    # Extract key metrics
    QUICK_TITLE=$(echo "$QUICK_BODY" | jq -r '.title // "N/A"')
    QUICK_WORD_COUNT=$(echo "$QUICK_BODY" | jq -r '.word_count // 0')
    QUICK_QUALITY_SCORE=$(echo "$QUICK_BODY" | jq -r '.quality_score // 0')
    QUICK_SEO_SCORE=$(echo "$QUICK_BODY" | jq -r '.seo_score // 0')
    QUICK_READABILITY_SCORE=$(echo "$QUICK_BODY" | jq -r '.readability_score // 0')
    QUICK_COST=$(echo "$QUICK_BODY" | jq -r '.total_cost // 0')
    QUICK_CITATIONS=$(echo "$QUICK_BODY" | jq -r '.citations | length // 0')
    
    # Extract quality dimensions
    QUICK_ENGAGEMENT=$(echo "$QUICK_BODY" | jq -r '.quality_dimensions.engagement.score // 0')
    QUICK_ACCESSIBILITY=$(echo "$QUICK_BODY" | jq -r '.quality_dimensions.accessibility.score // 0')
    QUICK_EEAT=$(echo "$QUICK_BODY" | jq -r '.quality_dimensions.eeat.score // 0')
    
    echo -e "${BOLD}Quick Generate Results:${NC}"
    echo -e "  Title: ${QUICK_TITLE}"
    echo -e "  Word Count: ${QUICK_WORD_COUNT}"
    echo -e "  Quality Score: ${QUICK_QUALITY_SCORE}"
    echo -e "  SEO Score: ${QUICK_SEO_SCORE}"
    echo -e "  Readability Score: ${QUICK_READABILITY_SCORE}"
    echo -e "  Engagement: ${QUICK_ENGAGEMENT}"
    echo -e "  Accessibility: ${QUICK_ACCESSIBILITY}"
    echo -e "  E-E-A-T: ${QUICK_EEAT}"
    echo -e "  Citations: ${QUICK_CITATIONS}"
    echo -e "  Total Cost: \$${QUICK_COST}"
    echo -e "  Generation Time: ${QUICK_DURATION}s"
    
    # Save summary
    cat > "${OUTPUT_DIR}/quick_summary.json" <<EOF
{
  "mode": "quick_generate",
  "title": "${QUICK_TITLE}",
  "word_count": ${QUICK_WORD_COUNT},
  "quality_score": ${QUICK_QUALITY_SCORE},
  "seo_score": ${QUICK_SEO_SCORE},
  "readability_score": ${QUICK_READABILITY_SCORE},
  "engagement": ${QUICK_ENGAGEMENT},
  "accessibility": ${QUICK_ACCESSIBILITY},
  "eeat": ${QUICK_EEAT},
  "citations": ${QUICK_CITATIONS},
  "total_cost": ${QUICK_COST},
  "generation_time_seconds": ${QUICK_DURATION}
}
EOF
else
    echo -e "${RED}❌ Quick Generate FAILED${NC}"
    echo "$QUICK_BODY" | jq '.' > "${OUTPUT_DIR}/quick_generate_error.json" 2>/dev/null || echo "$QUICK_BODY" > "${OUTPUT_DIR}/quick_generate_error.json"
    QUICK_WORD_COUNT=0
    QUICK_QUALITY_SCORE=0
    QUICK_SEO_SCORE=0
    QUICK_READABILITY_SCORE=0
    QUICK_COST=0
    QUICK_CITATIONS=0
    QUICK_ENGAGEMENT=0
    QUICK_ACCESSIBILITY=0
    QUICK_EEAT=0
fi

echo -e "\n${BOLD}${BLUE}============================================================${NC}\n"

# Wait between tests
echo -e "${YELLOW}Waiting 5 seconds before Multi-Phase test...${NC}\n"
sleep 5

# ============================================================================
# TEST 2: Multi-Phase Mode (With All Improvements)
# ============================================================================
echo -e "${BOLD}${BLUE}============================================================${NC}"
echo -e "${BOLD}${BLUE}TEST 2: Multi-Phase Mode (With Latest Improvements)${NC}"
echo -e "${BOLD}${BLUE}============================================================${NC}\n"

echo -e "${CYAN}Features being tested:${NC}"
echo -e "  ✓ Multi-stage pipeline (Research → Draft → Enhancement → SEO)"
echo -e "  ✓ Engagement instructions (questions, CTAs, examples)"
echo -e "  ✓ Accessibility instructions (heading hierarchy, TOC, alt text)"
echo -e "  ✓ Readability optimization (AI-powered post-processing)"
echo -e "  ✓ Engagement element injection"
echo -e "  ✓ Experience indicator injection (E-E-A-T)"
echo -e "  ✓ Consensus generation (enabled by default)"
echo -e "  ✓ Google Search integration"
echo -e "  ✓ Citations (5+ target)"
echo -e "  ✓ Fact-checking"
echo -e "  ✓ Knowledge Graph"
echo -e "  ✓ Semantic keywords"
echo -e "  ✓ Quality scoring"
echo ""

MULTI_PHASE_PAYLOAD=$(cat <<EOF
{
  "topic": "${TOPIC}",
  "keywords": ${KEYWORDS},
  "blog_type": "${BLOG_TYPE}",
  "tone": "professional",
  "length": "medium",
  "word_count_target": ${WORD_COUNT},
  "mode": "multi_phase",
  "optimize_for_traffic": true,
  "use_dataforseo_content_generation": false,
  "use_google_search": true,
  "use_fact_checking": true,
  "use_citations": true,
  "use_serp_optimization": true,
  "use_consensus_generation": true,
  "use_knowledge_graph": true,
  "use_semantic_keywords": true,
  "use_quality_scoring": true,
  "async_mode": false
}
EOF
)

echo -e "${CYAN}📡 Sending Multi-Phase request (may take 2-5 minutes)...${NC}\n"
echo -e "${YELLOW}Payload:${NC}"
echo "$MULTI_PHASE_PAYLOAD" | jq '.' | head -20
echo ""

MULTI_START=$(date +%s)
MULTI_RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST "${ENDPOINT}?async_mode=false" \
  -H "Content-Type: application/json" \
  -d "${MULTI_PHASE_PAYLOAD}" \
  --max-time 360)

MULTI_END=$(date +%s)
MULTI_DURATION=$((MULTI_END - MULTI_START))

HTTP_STATUS=$(echo "$MULTI_RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
MULTI_BODY=$(echo "$MULTI_RESPONSE" | sed '/HTTP_STATUS/d')

echo -e "${CYAN}Response Time: ${MULTI_DURATION} seconds${NC}"
echo -e "${CYAN}HTTP Status: ${HTTP_STATUS}${NC}\n"

if [ "$HTTP_STATUS" -eq 200 ]; then
    echo -e "${GREEN}✅ Multi-Phase SUCCESS${NC}\n"
    
    # Save full response
    echo "$MULTI_BODY" | jq '.' > "${OUTPUT_DIR}/multi_phase_response.json"
    
    # Extract key metrics
    MULTI_TITLE=$(echo "$MULTI_BODY" | jq -r '.title // "N/A"')
    MULTI_WORD_COUNT=$(echo "$MULTI_BODY" | jq -r '.word_count // 0')
    MULTI_QUALITY_SCORE=$(echo "$MULTI_BODY" | jq -r '.quality_score // 0')
    MULTI_SEO_SCORE=$(echo "$MULTI_BODY" | jq -r '.seo_score // 0')
    MULTI_READABILITY_SCORE=$(echo "$MULTI_BODY" | jq -r '.readability_score // 0')
    MULTI_COST=$(echo "$MULTI_BODY" | jq -r '.total_cost // 0')
    MULTI_CITATIONS=$(echo "$MULTI_BODY" | jq -r '.citations | length // 0')
    
    # Extract quality dimensions
    MULTI_ENGAGEMENT=$(echo "$MULTI_BODY" | jq -r '.quality_dimensions.engagement.score // 0')
    MULTI_ACCESSIBILITY=$(echo "$MULTI_BODY" | jq -r '.quality_dimensions.accessibility.score // 0')
    MULTI_EEAT=$(echo "$MULTI_BODY" | jq -r '.quality_dimensions.eeat.score // 0')
    
    echo -e "${BOLD}Multi-Phase Results:${NC}"
    echo -e "  Title: ${MULTI_TITLE}"
    echo -e "  Word Count: ${MULTI_WORD_COUNT}"
    echo -e "  Quality Score: ${MULTI_QUALITY_SCORE}"
    echo -e "  SEO Score: ${MULTI_SEO_SCORE}"
    echo -e "  Readability Score: ${MULTI_READABILITY_SCORE}"
    echo -e "  Engagement: ${MULTI_ENGAGEMENT}"
    echo -e "  Accessibility: ${MULTI_ACCESSIBILITY}"
    echo -e "  E-E-A-T: ${MULTI_EEAT}"
    echo -e "  Citations: ${MULTI_CITATIONS}"
    echo -e "  Total Cost: \$${MULTI_COST}"
    echo -e "  Generation Time: ${MULTI_DURATION}s"
    
    # Save summary
    cat > "${OUTPUT_DIR}/multi_phase_summary.json" <<EOF
{
  "mode": "multi_phase",
  "title": "${MULTI_TITLE}",
  "word_count": ${MULTI_WORD_COUNT},
  "quality_score": ${MULTI_QUALITY_SCORE},
  "seo_score": ${MULTI_SEO_SCORE},
  "readability_score": ${MULTI_READABILITY_SCORE},
  "engagement": ${MULTI_ENGAGEMENT},
  "accessibility": ${MULTI_ACCESSIBILITY},
  "eeat": ${MULTI_EEAT},
  "citations": ${MULTI_CITATIONS},
  "total_cost": ${MULTI_COST},
  "generation_time_seconds": ${MULTI_DURATION}
}
EOF
else
    echo -e "${RED}❌ Multi-Phase FAILED${NC}"
    echo "$MULTI_BODY" | jq '.' > "${OUTPUT_DIR}/multi_phase_error.json" 2>/dev/null || echo "$MULTI_BODY" > "${OUTPUT_DIR}/multi_phase_error.json"
    MULTI_WORD_COUNT=0
    MULTI_QUALITY_SCORE=0
    MULTI_SEO_SCORE=0
    MULTI_READABILITY_SCORE=0
    MULTI_COST=0
    MULTI_CITATIONS=0
    MULTI_ENGAGEMENT=0
    MULTI_ACCESSIBILITY=0
    MULTI_EEAT=0
fi

echo -e "\n${BOLD}${BLUE}============================================================${NC}"
echo -e "${BOLD}${BLUE}COMPARISON SUMMARY${NC}"
echo -e "${BOLD}${BLUE}============================================================${NC}\n"

if [ "$HTTP_STATUS" -eq 200 ] && [ -f "${OUTPUT_DIR}/quick_summary.json" ]; then
    echo -e "${BOLD}Metric Comparison:${NC}\n"
    
    printf "%-25s %-15s %-15s %-10s\n" "Metric" "Quick Generate" "Multi-Phase" "Winner"
    echo "─────────────────────────────────────────────────────────────────────────"
    
    # Quality Score
    if (( $(echo "$QUICK_QUALITY_SCORE > $MULTI_QUALITY_SCORE" | bc -l) )); then
        WINNER="🏆 Quick"
    elif (( $(echo "$MULTI_QUALITY_SCORE > $QUICK_QUALITY_SCORE" | bc -l) )); then
        WINNER="🏆 Multi"
    else
        WINNER="≈ Equal"
    fi
    printf "%-25s %-15s %-15s %-10s\n" "Quality Score" "${QUICK_QUALITY_SCORE}" "${MULTI_QUALITY_SCORE}" "${WINNER}"
    
    # SEO Score
    if (( $(echo "$QUICK_SEO_SCORE > $MULTI_SEO_SCORE" | bc -l) )); then
        WINNER="🏆 Quick"
    elif (( $(echo "$MULTI_SEO_SCORE > $QUICK_SEO_SCORE" | bc -l) )); then
        WINNER="🏆 Multi"
    else
        WINNER="≈ Equal"
    fi
    printf "%-25s %-15s %-15s %-10s\n" "SEO Score" "${QUICK_SEO_SCORE}" "${MULTI_SEO_SCORE}" "${WINNER}"
    
    # Readability Score
    if (( $(echo "$QUICK_READABILITY_SCORE > $MULTI_READABILITY_SCORE" | bc -l) )); then
        WINNER="🏆 Quick"
    elif (( $(echo "$MULTI_READABILITY_SCORE > $QUICK_READABILITY_SCORE" | bc -l) )); then
        WINNER="🏆 Multi"
    else
        WINNER="≈ Equal"
    fi
    printf "%-25s %-15s %-15s %-10s\n" "Readability Score" "${QUICK_READABILITY_SCORE}" "${MULTI_READABILITY_SCORE}" "${WINNER}"
    
    # Engagement
    if (( $(echo "$QUICK_ENGAGEMENT > $MULTI_ENGAGEMENT" | bc -l) )); then
        WINNER="🏆 Quick"
    elif (( $(echo "$MULTI_ENGAGEMENT > $QUICK_ENGAGEMENT" | bc -l) )); then
        WINNER="🏆 Multi"
    else
        WINNER="≈ Equal"
    fi
    printf "%-25s %-15s %-15s %-10s\n" "Engagement" "${QUICK_ENGAGEMENT}" "${MULTI_ENGAGEMENT}" "${WINNER}"
    
    # Accessibility
    if (( $(echo "$QUICK_ACCESSIBILITY > $MULTI_ACCESSIBILITY" | bc -l) )); then
        WINNER="🏆 Quick"
    elif (( $(echo "$MULTI_ACCESSIBILITY > $QUICK_ACCESSIBILITY" | bc -l) )); then
        WINNER="🏆 Multi"
    else
        WINNER="≈ Equal"
    fi
    printf "%-25s %-15s %-15s %-10s\n" "Accessibility" "${QUICK_ACCESSIBILITY}" "${MULTI_ACCESSIBILITY}" "${WINNER}"
    
    # E-E-A-T
    if (( $(echo "$QUICK_EEAT > $MULTI_EEAT" | bc -l) )); then
        WINNER="🏆 Quick"
    elif (( $(echo "$MULTI_EEAT > $QUICK_EEAT" | bc -l) )); then
        WINNER="🏆 Multi"
    else
        WINNER="≈ Equal"
    fi
    printf "%-25s %-15s %-15s %-10s\n" "E-E-A-T" "${QUICK_EEAT}" "${MULTI_EEAT}" "${WINNER}"
    
    # Citations
    if [ "$QUICK_CITATIONS" -gt "$MULTI_CITATIONS" ]; then
        WINNER="🏆 Quick"
    elif [ "$MULTI_CITATIONS" -gt "$QUICK_CITATIONS" ]; then
        WINNER="🏆 Multi"
    else
        WINNER="≈ Equal"
    fi
    printf "%-25s %-15s %-15s %-10s\n" "Citations" "${QUICK_CITATIONS}" "${MULTI_CITATIONS}" "${WINNER}"
    
    # Cost
    COST_DIFF=$(echo "$MULTI_COST - $QUICK_COST" | bc -l)
    COST_PERCENT=$(echo "scale=1; ($COST_DIFF / $QUICK_COST) * 100" | bc -l)
    if (( $(echo "$QUICK_COST < $MULTI_COST" | bc -l) )); then
        WINNER="🏆 Quick (${COST_PERCENT}% cheaper)"
    elif (( $(echo "$MULTI_COST < $QUICK_COST" | bc -l) )); then
        WINNER="🏆 Multi"
    else
        WINNER="≈ Equal"
    fi
    printf "%-25s %-15s %-15s %-10s\n" "Cost" "\$${QUICK_COST}" "\$${MULTI_COST}" "${WINNER}"
    
    # Generation Time
    TIME_DIFF=$((MULTI_DURATION - QUICK_DURATION))
    if [ "$QUICK_DURATION" -lt "$MULTI_DURATION" ]; then
        WINNER="🏆 Quick (${TIME_DIFF}s faster)"
    elif [ "$MULTI_DURATION" -lt "$QUICK_DURATION" ]; then
        WINNER="🏆 Multi"
    else
        WINNER="≈ Equal"
    fi
    printf "%-25s %-15s %-15s %-10s\n" "Generation Time" "${QUICK_DURATION}s" "${MULTI_DURATION}s" "${WINNER}"
    
    echo ""
    echo -e "${GREEN}✅ Test completed successfully!${NC}"
    echo -e "${CYAN}Results saved to: ${OUTPUT_DIR}/${NC}"
else
    echo -e "${RED}❌ Test failed - check error files in ${OUTPUT_DIR}/${NC}"
fi

echo ""







