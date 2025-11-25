#!/bin/bash
# Test DataForSEO Content Generation API for 100-word blog with subtopics
# Uses curl for direct API testing

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
echo -e "${BOLD}${BLUE}DataForSEO Content Generation - 100 Word Blog Test${NC}"
echo -e "${BOLD}${BLUE}============================================================${NC}\n"

# Get credentials from environment or Google Secret Manager
API_KEY="${DATAFORSEO_API_KEY:-${DATAFORSEO_API_LOGIN}}"
API_SECRET="${DATAFORSEO_API_SECRET:-${DATAFORSEO_API_PASSWORD}}"

# Try to get from Google Secret Manager if not in env
if [ -z "$API_KEY" ] || [ -z "$API_SECRET" ]; then
    echo -e "${YELLOW}⚠ Trying to get credentials from Google Secret Manager...${NC}"
    if command -v gcloud &> /dev/null; then
        API_KEY=$(gcloud secrets versions access latest --secret=DATAFORSEO_API_KEY 2>/dev/null || echo "")
        API_SECRET=$(gcloud secrets versions access latest --secret=DATAFORSEO_API_SECRET 2>/dev/null || echo "")
    fi
fi

if [ -z "$API_KEY" ] || [ -z "$API_SECRET" ]; then
    echo -e "${RED}❌ Error: DataForSEO credentials not found!${NC}"
    echo -e "${YELLOW}Please set DATAFORSEO_API_KEY and DATAFORSEO_API_SECRET environment variables.${NC}"
    exit 1
fi

# Create Basic Auth
CREDENTIALS="${API_KEY}:${API_SECRET}"
AUTH_HEADER=$(echo -n "$CREDENTIALS" | base64)

BASE_URL="https://api.dataforseo.com/v3"

# Test parameters
TOPIC="Benefits of Python Programming"
KEYWORDS="Python, programming, coding, development"
WORD_COUNT=100

echo -e "${BOLD}Test Parameters:${NC}"
echo -e "${CYAN}Topic: ${TOPIC}${NC}"
echo -e "${CYAN}Keywords: ${KEYWORDS}${NC}"
echo -e "${CYAN}Target Word Count: ${WORD_COUNT} words${NC}\n"

# Step 1: Generate subtopics
echo -e "${BOLD}${BLUE}============================================================${NC}"
echo -e "${BOLD}${BLUE}STEP 1: Generate Subtopics from Main Topic${NC}"
echo -e "${BOLD}${BLUE}============================================================${NC}\n"

SUBTOPIC_PROMPT="Topic: ${TOPIC}. Keywords: ${KEYWORDS}"
echo -e "${CYAN}Prompt: ${SUBTOPIC_PROMPT}${NC}\n"

# Create JSON payload with correct API parameters (topic, creativity_index)
SUBTOPICS_PAYLOAD=$(jq -n \
  --arg topic "$TOPIC" \
  '[{
    "topic": $topic,
    "creativity_index": 0.7
  }]' 2>/dev/null || echo "[{\"topic\":\"${TOPIC}\",\"creativity_index\":0.7}]")

echo -e "${CYAN}📡 Requesting subtopics...${NC}\n"

SUBTOPICS_RESPONSE=$(curl -s -X POST \
  "${BASE_URL}/content_generation/generate_sub_topics/live" \
  -H "Authorization: Basic ${AUTH_HEADER}" \
  -H "Content-Type: application/json" \
  -d "${SUBTOPICS_PAYLOAD}")

# Parse subtopics response using jq if available, otherwise grep
if command -v jq &> /dev/null; then
    TASK_STATUS=$(echo "$SUBTOPICS_RESPONSE" | jq -r '.tasks[0].status_code // empty')
    if [ "$TASK_STATUS" = "20000" ]; then
        SUBTOPICS=$(echo "$SUBTOPICS_RESPONSE" | jq -r '.tasks[0].result[0].sub_topics[]? // empty' 2>/dev/null)
        if [ -n "$SUBTOPICS" ]; then
            echo -e "${GREEN}✓ Subtopics Generated Successfully!${NC}"
            echo -e "${CYAN}Subtopics:${NC}"
            echo "$SUBTOPICS" | nl -w2 -s'. '
            SUBTOPICS_LIST=$(echo "$SUBTOPICS" | tr '\n' ',' | sed 's/,$//')
        else
            echo -e "${YELLOW}⚠ No subtopics in response${NC}"
            SUBTOPICS_LIST=""
        fi
    else
        echo -e "${YELLOW}⚠ Subtopics generation failed (status: $TASK_STATUS)${NC}"
        SUBTOPICS_LIST=""
    fi
else
    # Fallback parsing with grep
    SUBTOPICS=$(echo "$SUBTOPICS_RESPONSE" | grep -o '"sub_topics":\[[^]]*\]' | grep -o '\[.*\]' | sed 's/\[//;s/\]//' | sed 's/"//g' | tr ',' '\n' | sed 's/^/  /')
    if echo "$SUBTOPICS_RESPONSE" | grep -q '"status_code":20000' && [ -n "$SUBTOPICS" ]; then
        echo -e "${GREEN}✓ Subtopics Generated Successfully!${NC}"
        echo -e "${CYAN}Subtopics:${NC}"
        echo "$SUBTOPICS" | nl -w2 -s'. '
        SUBTOPICS_LIST=$(echo "$SUBTOPICS" | tr '\n' ',' | sed 's/,$//')
    else
        echo -e "${YELLOW}⚠ Subtopics generation failed or no subtopics returned${NC}"
        SUBTOPICS_LIST=""
    fi
fi

# Step 2: Generate 100-word content
echo -e "\n${BOLD}${BLUE}============================================================${NC}"
echo -e "${BOLD}${BLUE}STEP 2: Generate 100-Word Blog Content${NC}"
echo -e "${BOLD}${BLUE}============================================================${NC}\n"

CONTENT_PROMPT="Write a concise blog post about ${TOPIC}.

Keywords to include: ${KEYWORDS}
Target word count: exactly ${WORD_COUNT} words
Tone: professional and engaging
Structure: Brief introduction, main points, and short conclusion

"

if [ -n "$SUBTOPICS_LIST" ]; then
    CONTENT_PROMPT="${CONTENT_PROMPT}Cover these subtopics:
${SUBTOPICS_LIST}
"
fi

# Create JSON payload with correct API parameters (topic, word_count, creativity_index)
CONTENT_TOPIC="${TOPIC}"
if [ -n "$SUBTOPICS_LIST" ]; then
    FIRST_SUBTOPIC=$(echo "$SUBTOPICS" | head -1 | sed 's/^  //')
    CONTENT_TOPIC="${TOPIC}: ${FIRST_SUBTOPIC}"
fi

CONTENT_PAYLOAD=$(jq -n \
  --arg topic "$CONTENT_TOPIC" \
  '[{
    "topic": $topic,
    "word_count": 100,
    "creativity_index": 0.7
  }]' 2>/dev/null || echo "[{\"topic\":\"${CONTENT_TOPIC}\",\"word_count\":100,\"creativity_index\":0.7}]")

echo -e "${CYAN}📡 Generating content...${NC}\n"

CONTENT_RESPONSE=$(curl -s -X POST \
  "${BASE_URL}/content_generation/generate_text/live" \
  -H "Authorization: Basic ${AUTH_HEADER}" \
  -H "Content-Type: application/json" \
  -d "${CONTENT_PAYLOAD}")

# Extract generated text using jq if available (API returns "generated_text")
if command -v jq &> /dev/null; then
    TASK_STATUS=$(echo "$CONTENT_RESPONSE" | jq -r '.tasks[0].status_code // empty')
    if [ "$TASK_STATUS" = "20000" ]; then
        GENERATED_TEXT=$(echo "$CONTENT_RESPONSE" | jq -r '.tasks[0].result[0].generated_text // empty' 2>/dev/null)
        WORD_COUNT=$(echo "$GENERATED_TEXT" | wc -w | tr -d ' ')
    else
        GENERATED_TEXT=""
        WORD_COUNT=0
    fi
else
    # Fallback parsing
    GENERATED_TEXT=$(echo "$CONTENT_RESPONSE" | grep -o '"generated_text":"[^"]*"' | sed 's/"generated_text":"//;s/"$//' | head -1)
    WORD_COUNT=$(echo "$GENERATED_TEXT" | wc -w | tr -d ' ')
fi

TOKENS_USED=0  # API doesn't return tokens_used for generate_text endpoint

if [ -n "$GENERATED_TEXT" ] && [ "$WORD_COUNT" -gt 0 ]; then
    WORD_COUNT=$(echo "$GENERATED_TEXT" | wc -w | tr -d ' ')
    echo -e "${GREEN}✓ Content Generated Successfully!${NC}"
    echo -e "${CYAN}Tokens Used: ${TOKENS_USED:-0}${NC}"
    echo -e "${CYAN}Word Count: ${WORD_COUNT} words${NC}"
    echo -e "\n${BOLD}Generated Content:${NC}"
    echo -e "${BLUE}${GENERATED_TEXT}${NC}\n"
else
    echo -e "${RED}❌ Content generation failed${NC}"
    echo -e "${YELLOW}Response: ${CONTENT_RESPONSE:0:300}...${NC}"
    GENERATED_TEXT=""
    WORD_COUNT=0
    TOKENS_USED=0
fi

# Step 3: Generate meta tags
echo -e "${BOLD}${BLUE}============================================================${NC}"
echo -e "${BOLD}${BLUE}STEP 3: Generate Meta Tags${NC}"
echo -e "${BOLD}${BLUE}============================================================${NC}\n"

if [ -n "$GENERATED_TEXT" ]; then
    # Limit content length for meta generation
    CONTENT_FOR_META=$(echo "$GENERATED_TEXT" | head -c 1000)
    
    # Create JSON payload properly escaped
    META_PAYLOAD=$(jq -n \
      --arg title "$TOPIC" \
      --arg text "$CONTENT_FOR_META" \
      '[{
        "title": $title,
        "text": $text,
        "language": "en"
      }]' 2>/dev/null || echo "[{\"title\":\"${TOPIC}\",\"text\":\"${CONTENT_FOR_META}\",\"language\":\"en\"}]")

    echo -e "${CYAN}📡 Generating meta tags...${NC}\n"
    
    META_RESPONSE=$(curl -s -X POST \
      "${BASE_URL}/content_generation/generate_meta_tags/live" \
      -H "Authorization: Basic ${AUTH_HEADER}" \
      -H "Content-Type: application/json" \
      -d "${META_PAYLOAD}")
    
    # Parse meta tags using jq if available
    if command -v jq &> /dev/null; then
        TASK_STATUS=$(echo "$META_RESPONSE" | jq -r '.tasks[0].status_code // empty')
        if [ "$TASK_STATUS" = "20000" ]; then
            META_TITLE=$(echo "$META_RESPONSE" | jq -r '.tasks[0].result[0].title // empty' 2>/dev/null)
            META_DESC=$(echo "$META_RESPONSE" | jq -r '.tasks[0].result[0].description // empty' 2>/dev/null)
        else
            META_TITLE="$TOPIC"
            META_DESC=""
        fi
    else
        # Fallback parsing
        META_TITLE=$(echo "$META_RESPONSE" | grep -o '"title":"[^"]*"' | sed 's/"title":"//;s/"$//' | head -1)
        META_DESC=$(echo "$META_RESPONSE" | grep -o '"description":"[^"]*"' | sed 's/"description":"//;s/"$//' | head -1)
    fi
    
    if [ -n "$META_DESC" ]; then
        echo -e "${GREEN}✓ Meta Tags Generated Successfully!${NC}"
        echo -e "\n${BOLD}Meta Title:${NC}"
        echo -e "${BLUE}${META_TITLE:-$TOPIC}${NC}"
        echo -e "\n${BOLD}Meta Description:${NC}"
        echo -e "${BLUE}${META_DESC}${NC}"
    else
        echo -e "${YELLOW}⚠ Meta tags generation failed${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Skipping meta tags (no content generated)${NC}"
fi

# Summary
echo -e "\n${BOLD}${BLUE}============================================================${NC}"
echo -e "${BOLD}${BLUE}SUMMARY${NC}"
echo -e "${BOLD}${BLUE}============================================================${NC}\n"

echo -e "${BOLD}Results:${NC}"
echo -e "${CYAN}Topic: ${TOPIC}${NC}"
echo -e "${CYAN}Subtopics Generated: $(echo "$SUBTOPICS" | wc -l | tr -d ' ')${NC}"
echo -e "${CYAN}Content Word Count: ${WORD_COUNT} words (target: ${WORD_COUNT})${NC}"

if [ "$WORD_COUNT" -gt 0 ]; then
    DIFF=$((WORD_COUNT - WORD_COUNT))
    if [ $DIFF -lt 0 ]; then
        DIFF=$((-$DIFF))
    fi
    DIFF_PERCENT=$((DIFF * 100 / WORD_COUNT))
    if [ $DIFF_PERCENT -le 25 ]; then
        echo -e "${GREEN}✓ Word count within acceptable range${NC}"
    else
        echo -e "${YELLOW}⚠ Word count differs by ${DIFF_PERCENT}%${NC}"
    fi
fi

# Cost estimate
SUBTOPICS_COST=0.0001
CONTENT_COST=$(echo "scale=5; ${TOKENS_USED:-0} * 0.00005" | bc 2>/dev/null || echo "0")
META_COST=0.001
TOTAL_COST=$(echo "scale=5; $SUBTOPICS_COST + $CONTENT_COST + $META_COST" | bc 2>/dev/null || echo "0")

echo -e "\n${BOLD}Estimated Cost:${NC}"
echo -e "${CYAN}Subtopics: \$${SUBTOPICS_COST}${NC}"
echo -e "${CYAN}Content: \$${CONTENT_COST}${NC}"
echo -e "${CYAN}Meta Tags: \$${META_COST}${NC}"
echo -e "${BOLD}Total: \$${TOTAL_COST}${NC}"

echo -e "\n${GREEN}============================================================${NC}"
echo -e "${GREEN}Test completed!${NC}"
echo -e "${GREEN}============================================================${NC}\n"
