#!/bin/bash
# test_new_features.sh
# Test script for new features: include_eeat, additional_resources, word count, conclusion, and additional resources sections

set -e

# Configuration
BASE_URL="${BASE_URL:-http://localhost:8000}"  # Change to your deployed URL
ENDPOINT="${BASE_URL}/api/v1/blog/generate-enhanced"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}Testing New Blog Generation Features${NC}"
echo -e "${BLUE}============================================================${NC}\n"

# Test 1: Default behavior (E-E-A-T disabled)
echo -e "${YELLOW}Test 1: Default behavior (include_eeat=false)${NC}"
PAYLOAD1=$(cat <<EOF
{
  "topic": "Python Programming Basics",
  "keywords": ["python", "programming", "coding"],
  "tone": "professional",
  "length": "short",
  "word_count_target": 800,
  "blog_type": "tutorial"
}
EOF
)

echo "  Sending request..."
RESPONSE1=$(curl -s -X POST "${ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d "${PAYLOAD1}" \
  --max-time 300)

# Check E-E-A-T score (should be neutral ~50.0 when disabled)
EEAT_SCORE1=$(echo "$RESPONSE1" | jq -r '.quality_dimensions.eeat.score // "N/A"')
WORD_COUNT1=$(echo "$RESPONSE1" | jq -r '.word_count // 0')
CONTENT1=$(echo "$RESPONSE1" | jq -r '.content // ""')
HAS_CONCLUSION1=$(echo "$CONTENT1" | grep -c "## Conclusion" || echo "0")
HAS_RESOURCES1=$(echo "$CONTENT1" | grep -c "## Additional Resources" || echo "0")

echo "  Word Count: ${WORD_COUNT1} (target: 800)"
echo "  E-E-A-T Score: ${EEAT_SCORE1} (should be ~50.0 when disabled)"
if [ "$HAS_CONCLUSION1" -gt 0 ]; then
  echo -e "  Has Conclusion: ${GREEN}✅${NC}"
else
  echo -e "  Has Conclusion: ${RED}❌${NC}"
fi
if [ "$HAS_RESOURCES1" -gt 0 ]; then
  echo -e "  Has Additional Resources: ${GREEN}✅${NC}"
else
  echo -e "  Has Additional Resources: ${RED}❌${NC}"
fi
echo ""

# Test 2: E-E-A-T enabled
echo -e "${YELLOW}Test 2: E-E-A-T enabled (include_eeat=true)${NC}"
PAYLOAD2=$(cat <<EOF
{
  "topic": "Medical Advice for Diabetes",
  "keywords": ["diabetes", "medical advice", "health"],
  "tone": "professional",
  "length": "medium",
  "word_count_target": 1500,
  "blog_type": "guide",
  "include_eeat": true
}
EOF
)

echo "  Sending request..."
RESPONSE2=$(curl -s -X POST "${ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d "${PAYLOAD2}" \
  --max-time 300)

EEAT_SCORE2=$(echo "$RESPONSE2" | jq -r '.quality_dimensions.eeat.score // "N/A"')
WORD_COUNT2=$(echo "$RESPONSE2" | jq -r '.word_count // 0')
CONTENT2=$(echo "$RESPONSE2" | jq -r '.content // ""')
HAS_EXPERIENCE=$(echo "$CONTENT2" | grep -iE "(I have|In my experience|Based on my|I've)" | wc -l | tr -d ' ' || echo "0")

echo "  Word Count: ${WORD_COUNT2} (target: 1500)"
echo "  E-E-A-T Score: ${EEAT_SCORE2} (should be >50.0 when enabled)"
echo "  Experience Indicators: ${HAS_EXPERIENCE} found"
if [ "$HAS_EXPERIENCE" -gt 0 ]; then
  echo -e "  Status: ${GREEN}✅ PASS${NC}"
else
  echo -e "  Status: ${YELLOW}⚠️  No experience indicators found${NC}"
fi
echo ""

# Test 3: Additional Resources provided
echo -e "${YELLOW}Test 3: Additional Resources provided${NC}"
PAYLOAD3=$(cat <<EOF
{
  "topic": "Web Development Best Practices",
  "keywords": ["web development", "best practices", "coding"],
  "tone": "professional",
  "length": "short",
  "word_count_target": 800,
  "blog_type": "guide",
  "additional_resources": [
    {
      "title": "MDN Web Docs",
      "url": "https://developer.mozilla.org",
      "description": "Comprehensive web development documentation"
    },
    {
      "title": "W3C Standards",
      "url": "https://www.w3.org",
      "description": "Web standards and guidelines"
    }
  ]
}
EOF
)

echo "  Sending request..."
RESPONSE3=$(curl -s -X POST "${ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d "${PAYLOAD3}" \
  --max-time 300)

CONTENT3=$(echo "$RESPONSE3" | jq -r '.content // ""')
HAS_RESOURCES3=$(echo "$CONTENT3" | grep -c "## Additional Resources" || echo "0")
HAS_MDN=$(echo "$CONTENT3" | grep -c "developer.mozilla.org" || echo "0")

if [ "$HAS_RESOURCES3" -gt 0 ]; then
  echo -e "  Has Additional Resources Section: ${GREEN}✅${NC}"
else
  echo -e "  Has Additional Resources Section: ${RED}❌${NC}"
fi
if [ "$HAS_MDN" -gt 0 ]; then
  echo -e "  Contains provided resource (MDN): ${GREEN}✅${NC}"
else
  echo -e "  Contains provided resource (MDN): ${YELLOW}⚠️${NC}"
fi
echo ""

# Test 4: Word count enforcement (LONG)
echo -e "${YELLOW}Test 4: Word count enforcement (LONG = 2500 words)${NC}"
PAYLOAD4=$(cat <<EOF
{
  "topic": "Complete Guide to Machine Learning",
  "keywords": ["machine learning", "AI", "data science"],
  "tone": "professional",
  "length": "long",
  "blog_type": "guide"
}
EOF
)

echo "  Sending request..."
RESPONSE4=$(curl -s -X POST "${ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d "${PAYLOAD4}" \
  --max-time 300)

WORD_COUNT4=$(echo "$RESPONSE4" | jq -r '.word_count // 0')
TARGET4=2500
if command -v bc &> /dev/null; then
  PERCENTAGE4=$(echo "scale=2; ($WORD_COUNT4 / $TARGET4) * 100" | bc)
else
  PERCENTAGE4=$(awk "BEGIN {printf \"%.2f\", ($WORD_COUNT4 / $TARGET4) * 100}")
fi

echo "  Word Count: ${WORD_COUNT4} (target: ${TARGET4})"
echo "  Percentage: ${PERCENTAGE4}%"
if command -v bc &> /dev/null; then
  if (( $(echo "$PERCENTAGE4 >= 80" | bc -l) )); then
    echo -e "  Status: ${GREEN}✅ PASS${NC} (>80% of target)"
  else
    echo -e "  Status: ${RED}❌ FAIL${NC} (<80% of target)"
  fi
else
  PERCENT_INT=$(echo "$PERCENTAGE4" | cut -d. -f1)
  if [ "$PERCENT_INT" -ge 80 ]; then
    echo -e "  Status: ${GREEN}✅ PASS${NC} (>80% of target)"
  else
    echo -e "  Status: ${RED}❌ FAIL${NC} (<80% of target)"
  fi
fi
echo ""

# Test 5: Section-by-section with placeholder links
echo -e "${YELLOW}Test 5: Section-by-section writing with link placement${NC}"
PAYLOAD5=$(cat <<EOF
{
  "topic": "SEO Optimization Techniques",
  "keywords": ["SEO", "optimization", "search engine"],
  "tone": "professional",
  "length": "medium",
  "word_count_target": 1500,
  "blog_type": "guide",
  "site_domain": "example.com",
  "internal_link_targets": [
    {"slug": "seo-basics", "title": "SEO Basics"},
    {"slug": "keyword-research", "title": "Keyword Research"},
    {"slug": "content-optimization", "title": "Content Optimization"}
  ]
}
EOF
)

echo "  Sending request..."
RESPONSE5=$(curl -s -X POST "${ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d "${PAYLOAD5}" \
  --max-time 300)

CONTENT5=$(echo "$RESPONSE5" | jq -r '.content // ""')
HAS_INTERNAL_LINKS=$(echo "$CONTENT5" | grep -c "example.com" || echo "0")

# Extract conclusion section and check for links
CONCLUSION_SECTION=$(echo "$CONTENT5" | sed -n '/## Conclusion/,/## Additional Resources/p' | head -n -1)
NO_LINKS_IN_CONCLUSION=$(echo "$CONCLUSION_SECTION" | grep -c "\[.*\](" || echo "0")

echo "  Internal links found: ${HAS_INTERNAL_LINKS}"
echo "  Links in conclusion: ${NO_LINKS_IN_CONCLUSION} (should be 0)"
if [ "$NO_LINKS_IN_CONCLUSION" -eq 0 ]; then
  echo -e "  Status: ${GREEN}✅ PASS${NC} (no links in conclusion)"
else
  echo -e "  Status: ${RED}❌ FAIL${NC} (links found in conclusion)"
fi
echo ""

# Test 6: All word count targets
echo -e "${YELLOW}Test 6: All word count targets${NC}"
declare -A TARGETS=(
  ["short"]=800
  ["medium"]=1500
  ["long"]=2500
  ["extended"]=4000
)

for length in short medium long extended; do
  echo "  Testing ${length} (target: ${TARGETS[$length]})..."
  PAYLOAD=$(cat <<EOF
{
  "topic": "Test Topic for ${length} content",
  "keywords": ["test", "topic"],
  "tone": "professional",
  "length": "${length}",
  "blog_type": "guide"
}
EOF
)
  
  RESPONSE=$(curl -s -X POST "${ENDPOINT}" \
    -H "Content-Type: application/json" \
    -d "${PAYLOAD}" \
    --max-time 300)
  
  WORD_COUNT=$(echo "$RESPONSE" | jq -r '.word_count // 0')
  TARGET=${TARGETS[$length]}
  
  if command -v bc &> /dev/null; then
    PERCENTAGE=$(echo "scale=2; ($WORD_COUNT / $TARGET) * 100" | bc)
    if (( $(echo "$PERCENTAGE >= 80" | bc -l) )); then
      echo -e "    ${length}: ${WORD_COUNT} words (${PERCENTAGE}%) ${GREEN}✅${NC}"
    else
      echo -e "    ${length}: ${WORD_COUNT} words (${PERCENTAGE}%) ${RED}❌${NC}"
    fi
  else
    PERCENTAGE=$(awk "BEGIN {printf \"%.2f\", ($WORD_COUNT / $TARGET) * 100}")
    PERCENT_INT=$(echo "$PERCENTAGE" | cut -d. -f1)
    if [ "$PERCENT_INT" -ge 80 ]; then
      echo -e "    ${length}: ${WORD_COUNT} words (${PERCENTAGE}%) ${GREEN}✅${NC}"
    else
      echo -e "    ${length}: ${WORD_COUNT} words (${PERCENTAGE}%) ${RED}❌${NC}"
    fi
  fi
done
echo ""

# Summary
echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}Test Summary${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""
echo "✅ All tests completed. Review the outputs above to verify:"
echo "  1. E-E-A-T is disabled by default (score ~50.0)"
echo "  2. E-E-A-T works when enabled (score >50.0, experience indicators present)"
echo "  3. Additional Resources section is included"
echo "  4. Word counts meet targets (SHORT: 800, MEDIUM: 1500, LONG: 2500, EXTENDED: 4000)"
echo "  5. Conclusion section has no links"
echo "  6. Internal links are properly placed in body sections"
echo ""
echo -e "${CYAN}To test with a different URL, set BASE_URL:${NC}"
echo -e "${CYAN}  BASE_URL=https://your-api-url.com ./test_new_features.sh${NC}"
echo ""
