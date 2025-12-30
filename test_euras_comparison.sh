#!/bin/bash
# Test both Quick Generate and Multi-Phase modes for Euras Technology leak fixing
# Target: 250 words

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# API URL
API_URL="${API_URL:-https://blog-writer-api-dev-kq42l26tuq-od.a.run.app}"
ENDPOINT="${API_URL}/api/v1/blog/generate-enhanced"

TOPIC="Using Euras Technology to Fix Leaks in Critical Infrastructure, Basements and Garages"
KEYWORDS='["Euras Technology", "leak repair", "critical infrastructure", "basement leaks", "garage leaks", "waterproofing", "leak detection"]'
CUSTOM_INSTRUCTIONS="Focus on Euras Technology (www.eurastechnology.com) solutions for leak detection and repair in critical infrastructure, basements, and garages. Include specific benefits and applications."

echo -e "${BOLD}${BLUE}============================================================${NC}"
echo -e "${BOLD}${BLUE}Euras Technology Leak Fixing - Mode Comparison Test${NC}"
echo -e "${BOLD}${BLUE}Topic: ${TOPIC}${NC}"
echo -e "${BOLD}${BLUE}Target: 250 words${NC}"
echo -e "${BOLD}${BLUE}============================================================${NC}\n"

# Test 1: Quick Generate Mode
echo -e "${BOLD}${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}${CYAN}TEST 1: Quick Generate Mode (DataForSEO)${NC}"
echo -e "${BOLD}${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

QUICK_PAYLOAD=$(cat <<EOF
{
  "topic": "${TOPIC}",
  "keywords": ${KEYWORDS},
  "tone": "professional",
  "length": "short",
  "mode": "quick_generate",
  "use_citations": false,
  "use_dataforseo_content_generation": true,
  "custom_instructions": "${CUSTOM_INSTRUCTIONS}",
  "async_mode": false
}
EOF
)

echo -e "${CYAN}📡 Sending Quick Generate request...${NC}\n"
START_TIME=$(date +%s)

QUICK_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
  "${ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d "${QUICK_PAYLOAD}")

QUICK_HTTP_CODE=$(echo "$QUICK_RESPONSE" | tail -n1)
QUICK_BODY=$(echo "$QUICK_RESPONSE" | sed '$d')
QUICK_TIME=$(($(date +%s) - START_TIME))

echo "$QUICK_BODY" > test_euras_quick_result.json

if [ "$QUICK_HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ Quick Generate completed in ${QUICK_TIME}s${NC}"
    QUICK_WORDS=$(echo "$QUICK_BODY" | jq -r '.content' 2>/dev/null | wc -w | tr -d ' ')
    QUICK_TITLE=$(echo "$QUICK_BODY" | jq -r '.title' 2>/dev/null)
    echo -e "${GREEN}  Title: ${QUICK_TITLE}${NC}"
    echo -e "${GREEN}  Word Count: ${QUICK_WORDS} words${NC}"
else
    echo -e "${RED}✗ Quick Generate failed (HTTP ${QUICK_HTTP_CODE})${NC}"
    echo "$QUICK_BODY" | jq '.' 2>/dev/null || echo "$QUICK_BODY"
fi

echo ""

# Test 2: Multi-Phase Mode
echo -e "${BOLD}${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}${CYAN}TEST 2: Multi-Phase Mode (Comprehensive Pipeline)${NC}"
echo -e "${BOLD}${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

MULTI_PAYLOAD=$(cat <<EOF
{
  "topic": "${TOPIC}",
  "keywords": ${KEYWORDS},
  "tone": "professional",
  "length": "short",
  "mode": "multi_phase",
  "use_citations": false,
  "use_dataforseo_content_generation": false,
  "custom_instructions": "${CUSTOM_INSTRUCTIONS}"
}
EOF
)

echo -e "${CYAN}📡 Sending Multi-Phase request (synchronous, async_mode=false, citations disabled)...${NC}\n"
START_TIME=$(date +%s)

MULTI_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
  "${ENDPOINT}?async_mode=0" \
  -H "Content-Type: application/json" \
  -d "${MULTI_PAYLOAD}" \
  --max-time 300)

MULTI_HTTP_CODE=$(echo "$MULTI_RESPONSE" | tail -n1)
MULTI_BODY=$(echo "$MULTI_RESPONSE" | sed '$d')
MULTI_TIME=$(($(date +%s) - START_TIME))

echo "$MULTI_BODY" > test_euras_multi_phase_result.json

if [ "$MULTI_HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ Multi-Phase completed in ${MULTI_TIME}s${NC}"
    MULTI_WORDS=$(echo "$MULTI_BODY" | jq -r '.content' 2>/dev/null | wc -w | tr -d ' ')
    MULTI_TITLE=$(echo "$MULTI_BODY" | jq -r '.title' 2>/dev/null)
    MULTI_CITATIONS=$(echo "$MULTI_BODY" | jq -r '.citations | length' 2>/dev/null)
    MULTI_QUALITY=$(echo "$MULTI_BODY" | jq -r '.quality_score' 2>/dev/null)
    echo -e "${GREEN}  Title: ${MULTI_TITLE}${NC}"
    echo -e "${GREEN}  Word Count: ${MULTI_WORDS} words${NC}"
    echo -e "${GREEN}  Citations: ${MULTI_CITATIONS}${NC}"
    echo -e "${GREEN}  Quality Score: ${MULTI_QUALITY}${NC}"
else
    echo -e "${RED}✗ Multi-Phase failed (HTTP ${MULTI_HTTP_CODE})${NC}"
    echo "$MULTI_BODY" | jq '.' 2>/dev/null || echo "$MULTI_BODY"
fi

echo ""

# Comparison Summary
echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}${BLUE}COMPARISON SUMMARY${NC}"
echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

echo -e "${BOLD}Quick Generate Mode:${NC}"
echo -e "  Status: $([ "$QUICK_HTTP_CODE" = "200" ] && echo -e "${GREEN}✓ Success${NC}" || echo -e "${RED}✗ Failed${NC}")"
echo -e "  Time: ${QUICK_TIME}s"
[ "$QUICK_HTTP_CODE" = "200" ] && echo -e "  Words: ${QUICK_WORDS}"
[ "$QUICK_HTTP_CODE" = "200" ] && echo -e "  Title: ${QUICK_TITLE}"

echo ""
echo -e "${BOLD}Multi-Phase Mode:${NC}"
echo -e "  Status: $([ "$MULTI_HTTP_CODE" = "200" ] && echo -e "${GREEN}✓ Success${NC}" || echo -e "${RED}✗ Failed${NC}")"
echo -e "  Time: ${MULTI_TIME}s"
[ "$MULTI_HTTP_CODE" = "200" ] && echo -e "  Words: ${MULTI_WORDS}"
[ "$MULTI_HTTP_CODE" = "200" ] && echo -e "  Title: ${MULTI_TITLE}"
[ "$MULTI_HTTP_CODE" = "200" ] && echo -e "  Citations: ${MULTI_CITATIONS}"
[ "$MULTI_HTTP_CODE" = "200" ] && echo -e "  Quality Score: ${MULTI_QUALITY}"

echo ""
echo -e "${BOLD}Results saved to:${NC}"
echo -e "  - test_euras_quick_result.json"
echo -e "  - test_euras_multi_phase_result.json"

