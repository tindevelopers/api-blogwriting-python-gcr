#!/bin/bash

# Compare Quick Generate vs Multi-Phase modes with same content parameters
# Tests quality scoring and compares results

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
echo -e "${BOLD}${BLUE}Comparing Quick Generate vs Multi-Phase Modes${NC}"
echo -e "${BOLD}${BLUE}Quality Score Comparison Test${NC}"
echo -e "${BOLD}${BLUE}============================================================${NC}\n"

# Test parameters (same for both modes)
TOPIC="Benefits of Python Programming"
KEYWORDS='["python", "programming", "coding", "development"]'
WORD_COUNT=100
BLOG_TYPE="tutorial"

echo -e "${BOLD}Test Parameters (Same for Both Modes):${NC}"
echo -e "${CYAN}Topic: ${TOPIC}${NC}"
echo -e "${CYAN}Keywords: ${KEYWORDS}${NC}"
echo -e "${CYAN}Target Word Count: ${WORD_COUNT} words${NC}"
echo -e "${CYAN}Blog Type: ${BLOG_TYPE}${NC}\n"

# ============================================================================
# TEST 1: Quick Generate Mode
# ============================================================================
echo -e "${BOLD}${BLUE}============================================================${NC}"
echo -e "${BOLD}${BLUE}TEST 1: Quick Generate Mode${NC}"
echo -e "${BOLD}${BLUE}============================================================${NC}\n"

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
  "async_mode": false
}
EOF
)

echo -e "${CYAN}📡 Sending Quick Generate request...${NC}\n"

QUICK_START=$(date +%s)
QUICK_RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST "${ENDPOINT}?async_mode=false" \
  -H "Content-Type: application/json" \
  -d "${QUICK_PAYLOAD}" \
  --max-time 120)
QUICK_END=$(date +%s)
QUICK_DURATION=$((QUICK_END - QUICK_START))

HTTP_STATUS=$(echo "$QUICK_RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
QUICK_BODY=$(echo "$QUICK_RESPONSE" | sed '/HTTP_STATUS/d')

if [ "$HTTP_STATUS" -eq 200 ]; then
    QUICK_TITLE=$(echo "$QUICK_BODY" | jq -r '.title // "N/A"')
    QUICK_CONTENT=$(echo "$QUICK_BODY" | jq -r '.content // ""')
    QUICK_WORD_COUNT=$(echo "$QUICK_CONTENT" | wc -w | xargs)
    QUICK_SEO_SCORE=$(echo "$QUICK_BODY" | jq -r '.seo_score // "N/A"')
    QUICK_QUALITY_SCORE=$(echo "$QUICK_BODY" | jq -r '.quality_score // "N/A"')
    QUICK_COST=$(echo "$QUICK_BODY" | jq -r '.total_cost // "N/A"')
    QUICK_READABILITY=$(echo "$QUICK_BODY" | jq -r '.readability_score // "N/A"')
    QUICK_SUBTOPICS=$(echo "$QUICK_BODY" | jq -r '.seo_metadata.subtopics | length // 0')
    QUICK_CITATIONS=$(echo "$QUICK_BODY" | jq -r '.citations | length // 0')
    QUICK_STAGES=$(echo "$QUICK_BODY" | jq -r '.stage_results | length // 0')
    
    # Extract quality dimensions if available
    QUICK_QUALITY_DIMS=$(echo "$QUICK_BODY" | jq -r '.quality_dimensions // {}')
    
    echo -e "${GREEN}✅ Quick Generate SUCCESS${NC}"
    echo -e "${CYAN}Duration: ${QUICK_DURATION}s${NC}"
    echo -e "${CYAN}Title: ${QUICK_TITLE}${NC}"
    echo -e "${CYAN}Word Count: ${QUICK_WORD_COUNT} words${NC}"
    echo -e "${CYAN}SEO Score: ${QUICK_SEO_SCORE}${NC}"
    echo -e "${CYAN}Quality Score: ${QUICK_QUALITY_SCORE}${NC}"
    echo -e "${CYAN}Readability Score: ${QUICK_READABILITY}${NC}"
    echo -e "${CYAN}Cost: \$${QUICK_COST}${NC}"
    echo -e "${CYAN}Subtopics: ${QUICK_SUBTOPICS}${NC}"
    echo -e "${CYAN}Citations: ${QUICK_CITATIONS}${NC}"
    echo -e "${CYAN}Pipeline Stages: ${QUICK_STAGES}${NC}"
    
    # Save response
    echo "$QUICK_BODY" | jq '.' > /tmp/quick_generate_comparison.json
else
    echo -e "${RED}❌ Quick Generate FAILED${NC}"
    QUICK_WORD_COUNT=0
    QUICK_SEO_SCORE=0
    QUICK_QUALITY_SCORE=0
    QUICK_COST=0
fi

echo -e "\n${BOLD}${BLUE}============================================================${NC}\n"

# ============================================================================
# TEST 2: Multi-Phase Mode
# ============================================================================
echo -e "${BOLD}${BLUE}============================================================${NC}"
echo -e "${BOLD}${BLUE}TEST 2: Multi-Phase Mode${NC}"
echo -e "${BOLD}${BLUE}============================================================${NC}\n"

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

echo -e "${CYAN}📡 Sending Multi-Phase request (may take 3-5 minutes)...${NC}\n"

MULTI_START=$(date +%s)
MULTI_RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST "${ENDPOINT}?async_mode=false" \
  -H "Content-Type: application/json" \
  -d "${MULTI_PHASE_PAYLOAD}" \
  --max-time 300)
MULTI_END=$(date +%s)
MULTI_DURATION=$((MULTI_END - MULTI_START))

HTTP_STATUS=$(echo "$MULTI_RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
MULTI_BODY=$(echo "$MULTI_RESPONSE" | sed '/HTTP_STATUS/d')

if [ "$HTTP_STATUS" -eq 200 ]; then
    MULTI_TITLE=$(echo "$MULTI_BODY" | jq -r '.title // "N/A"')
    MULTI_CONTENT=$(echo "$MULTI_BODY" | jq -r '.content // ""')
    MULTI_WORD_COUNT=$(echo "$MULTI_CONTENT" | wc -w | xargs)
    MULTI_SEO_SCORE=$(echo "$MULTI_BODY" | jq -r '.seo_score // "N/A"')
    MULTI_QUALITY_SCORE=$(echo "$MULTI_BODY" | jq -r '.quality_score // "N/A"')
    MULTI_COST=$(echo "$MULTI_BODY" | jq -r '.total_cost // "N/A"')
    MULTI_READABILITY=$(echo "$MULTI_BODY" | jq -r '.readability_score // "N/A"')
    MULTI_SUBTOPICS=$(echo "$MULTI_BODY" | jq -r '.seo_metadata.subtopics | length // 0')
    MULTI_CITATIONS=$(echo "$MULTI_BODY" | jq -r '.citations | length // 0')
    MULTI_STAGES=$(echo "$MULTI_BODY" | jq -r '.stage_results | length // 0')
    
    # Extract quality dimensions if available
    MULTI_QUALITY_DIMS=$(echo "$MULTI_BODY" | jq -r '.quality_dimensions // {}')
    
    echo -e "${GREEN}✅ Multi-Phase SUCCESS${NC}"
    echo -e "${CYAN}Duration: ${MULTI_DURATION}s${NC}"
    echo -e "${CYAN}Title: ${MULTI_TITLE}${NC}"
    echo -e "${CYAN}Word Count: ${MULTI_WORD_COUNT} words${NC}"
    echo -e "${CYAN}SEO Score: ${MULTI_SEO_SCORE}${NC}"
    echo -e "${CYAN}Quality Score: ${MULTI_QUALITY_SCORE}${NC}"
    echo -e "${CYAN}Readability Score: ${MULTI_READABILITY}${NC}"
    echo -e "${CYAN}Cost: \$${MULTI_COST}${NC}"
    echo -e "${CYAN}Subtopics: ${MULTI_SUBTOPICS}${NC}"
    echo -e "${CYAN}Citations: ${MULTI_CITATIONS}${NC}"
    echo -e "${CYAN}Pipeline Stages: ${MULTI_STAGES}${NC}"
    
    # Save response
    echo "$MULTI_BODY" | jq '.' > /tmp/multi_phase_comparison.json
else
    echo -e "${RED}❌ Multi-Phase FAILED${NC}"
    MULTI_WORD_COUNT=0
    MULTI_SEO_SCORE=0
    MULTI_QUALITY_SCORE=0
    MULTI_COST=0
fi

echo -e "\n${BOLD}${BLUE}============================================================${NC}"

# ============================================================================
# COMPARISON TABLE
# ============================================================================
echo -e "${BOLD}${BLUE}============================================================${NC}"
echo -e "${BOLD}${BLUE}QUALITY SCORE COMPARISON${NC}"
echo -e "${BOLD}${BLUE}============================================================${NC}\n"

printf "${BOLD}%-25s %-20s %-20s${NC}\n" "Metric" "Quick Generate" "Multi-Phase"
echo "----------------------------------------------------------------"

# Convert scores to numbers for comparison
QUICK_QS_NUM=$(echo "$QUICK_QUALITY_SCORE" | grep -oE '[0-9]+\.?[0-9]*' | head -1 || echo "0")
MULTI_QS_NUM=$(echo "$MULTI_QUALITY_SCORE" | grep -oE '[0-9]+\.?[0-9]*' | head -1 || echo "0")

QUICK_SEO_NUM=$(echo "$QUICK_SEO_SCORE" | grep -oE '[0-9]+\.?[0-9]*' | head -1 || echo "0")
MULTI_SEO_NUM=$(echo "$MULTI_SEO_SCORE" | grep -oE '[0-9]+\.?[0-9]*' | head -1 || echo "0")

QUICK_READ_NUM=$(echo "$QUICK_READABILITY" | grep -oE '[0-9]+\.?[0-9]*' | head -1 || echo "0")
MULTI_READ_NUM=$(echo "$MULTI_READABILITY" | grep -oE '[0-9]+\.?[0-9]*' | head -1 || echo "0")

printf "%-25s ${CYAN}%-20s${NC} ${CYAN}%-20s${NC}\n" "Quality Score" "$QUICK_QUALITY_SCORE" "$MULTI_QUALITY_SCORE"
printf "%-25s ${CYAN}%-20s${NC} ${CYAN}%-20s${NC}\n" "SEO Score" "$QUICK_SEO_SCORE" "$MULTI_SEO_SCORE"
printf "%-25s ${CYAN}%-20s${NC} ${CYAN}%-20s${NC}\n" "Readability Score" "$QUICK_READABILITY" "$MULTI_READABILITY"
printf "%-25s ${CYAN}%-20s${NC} ${CYAN}%-20s${NC}\n" "Word Count" "$QUICK_WORD_COUNT words" "$MULTI_WORD_COUNT words"
printf "%-25s ${CYAN}%-20s${NC} ${CYAN}%-20s${NC}\n" "Generation Time" "${QUICK_DURATION}s" "${MULTI_DURATION}s"
printf "%-25s ${CYAN}%-20s${NC} ${CYAN}%-20s${NC}\n" "Cost" "\$${QUICK_COST}" "\$${MULTI_COST}"
printf "%-25s ${CYAN}%-20s${NC} ${CYAN}%-20s${NC}\n" "Subtopics" "$QUICK_SUBTOPICS" "$MULTI_SUBTOPICS"
printf "%-25s ${CYAN}%-20s${NC} ${CYAN}%-20s${NC}\n" "Citations" "$QUICK_CITATIONS" "$MULTI_CITATIONS"
printf "%-25s ${CYAN}%-20s${NC} ${CYAN}%-20s${NC}\n" "Pipeline Stages" "$QUICK_STAGES" "$MULTI_STAGES"

echo ""
echo "----------------------------------------------------------------"

# Quality score comparison
if [ "$QUICK_QS_NUM" != "0" ] && [ "$MULTI_QS_NUM" != "0" ]; then
    if (( $(echo "$MULTI_QS_NUM > $QUICK_QS_NUM" | bc -l) )); then
        DIFF=$(echo "$MULTI_QS_NUM - $QUICK_QS_NUM" | bc -l)
        printf "${GREEN}Multi-Phase has higher quality score by %.2f points${NC}\n" "$DIFF"
    elif (( $(echo "$QUICK_QS_NUM > $MULTI_QS_NUM" | bc -l) )); then
        DIFF=$(echo "$QUICK_QS_NUM - $MULTI_QS_NUM" | bc -l)
        printf "${YELLOW}Quick Generate has higher quality score by %.2f points${NC}\n" "$DIFF"
    else
        echo -e "${CYAN}Quality scores are equal${NC}"
    fi
fi

# Cost comparison
if [ "$QUICK_COST" != "N/A" ] && [ "$MULTI_COST" != "N/A" ]; then
    QUICK_COST_NUM=$(echo "$QUICK_COST" | grep -oE '[0-9]+\.?[0-9]*' | head -1 || echo "0")
    MULTI_COST_NUM=$(echo "$MULTI_COST" | grep -oE '[0-9]+\.?[0-9]*' | head -1 || echo "0")
    if (( $(echo "$MULTI_COST_NUM > $QUICK_COST_NUM" | bc -l) )); then
        COST_DIFF=$(echo "$MULTI_COST_NUM - $QUICK_COST_NUM" | bc -l)
        COST_RATIO=$(echo "scale=2; $MULTI_COST_NUM / $QUICK_COST_NUM" | bc -l)
        printf "${YELLOW}Multi-Phase costs %.4f more (%.2fx)${NC}\n" "$COST_DIFF" "$COST_RATIO"
    fi
fi

# Time comparison
if [ "$QUICK_DURATION" -gt 0 ] && [ "$MULTI_DURATION" -gt 0 ]; then
    TIME_RATIO=$(echo "scale=2; $MULTI_DURATION / $QUICK_DURATION" | bc -l)
    printf "${CYAN}Multi-Phase takes %.2fx longer${NC}\n" "$TIME_RATIO"
fi

echo ""

# ============================================================================
# QUALITY DIMENSIONS COMPARISON
# ============================================================================
if [ -f /tmp/quick_generate_comparison.json ] && [ -f /tmp/multi_phase_comparison.json ]; then
    echo -e "${BOLD}${BLUE}============================================================${NC}"
    echo -e "${BOLD}${BLUE}QUALITY DIMENSIONS COMPARISON${NC}"
    echo -e "${BOLD}${BLUE}============================================================${NC}\n"
    
    QUICK_DIMS=$(cat /tmp/quick_generate_comparison.json | jq -r '.quality_dimensions // {}' 2>/dev/null)
    MULTI_DIMS=$(cat /tmp/multi_phase_comparison.json | jq -r '.quality_dimensions // {}' 2>/dev/null)
    
    if [ "$QUICK_DIMS" != "{}" ] && [ "$MULTI_DIMS" != "{}" ]; then
        echo -e "${BOLD}Quality Dimensions:${NC}"
        printf "${BOLD}%-20s %-15s %-15s${NC}\n" "Dimension" "Quick Generate" "Multi-Phase"
        echo "----------------------------------------------------------------"
        
        # Extract and compare each dimension
        for dim in readability seo structure factual uniqueness engagement eeat; do
            QUICK_VAL=$(echo "$QUICK_DIMS" | jq -r ".[\"$dim\"] // \"N/A\"" 2>/dev/null)
            MULTI_VAL=$(echo "$MULTI_DIMS" | jq -r ".[\"$dim\"] // \"N/A\"" 2>/dev/null)
            if [ "$QUICK_VAL" != "null" ] && [ "$MULTI_VAL" != "null" ]; then
                printf "%-20s ${CYAN}%-15s${NC} ${CYAN}%-15s${NC}\n" "$dim" "$QUICK_VAL" "$MULTI_VAL"
            fi
        done
        echo ""
    fi
fi

# ============================================================================
# SUMMARY
# ============================================================================
echo -e "${BOLD}${BLUE}============================================================${NC}"
echo -e "${BOLD}${BLUE}SUMMARY${NC}"
echo -e "${BOLD}${BLUE}============================================================${NC}\n"

echo -e "${BOLD}Quick Generate Mode:${NC}"
echo -e "  ${GREEN}✓ Fast: ${QUICK_DURATION}s${NC}"
echo -e "  ${GREEN}✓ Cost-effective: \$${QUICK_COST}${NC}"
echo -e "  ${CYAN}Quality Score: ${QUICK_QUALITY_SCORE}${NC}"
echo -e "  ${CYAN}SEO Score: ${QUICK_SEO_SCORE}${NC}"

echo ""
echo -e "${BOLD}Multi-Phase Mode:${NC}"
echo -e "  ${CYAN}Comprehensive: ${MULTI_DURATION}s${NC}"
echo -e "  ${CYAN}Cost: \$${MULTI_COST}${NC}"
echo -e "  ${CYAN}Quality Score: ${MULTI_QUALITY_SCORE}${NC}"
echo -e "  ${CYAN}SEO Score: ${MULTI_SEO_SCORE}${NC}"
echo -e "  ${CYAN}Citations: ${MULTI_CITATIONS}${NC}"
echo -e "  ${CYAN}Pipeline Stages: ${MULTI_STAGES}${NC}"

echo ""
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}Comparison Complete!${NC}"
echo -e "${GREEN}============================================================${NC}\n"

echo -e "${CYAN}Full responses saved:${NC}"
echo -e "${CYAN}  Quick Generate: /tmp/quick_generate_comparison.json${NC}"
echo -e "${CYAN}  Multi-Phase: /tmp/multi_phase_comparison.json${NC}"







