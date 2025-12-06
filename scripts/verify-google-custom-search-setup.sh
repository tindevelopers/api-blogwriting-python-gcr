#!/bin/bash
# Verify Google Custom Search API setup

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Google Custom Search API Setup Verification${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

PROJECT_ID=$(gcloud config get-value project 2>/dev/null || echo "")
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}Error: No Google Cloud project configured.${NC}"
    exit 1
fi

echo -e "${YELLOW}Project: ${PROJECT_ID}${NC}"
echo ""

# Check if secrets exist
echo -e "${YELLOW}Checking secrets...${NC}"

# Check Option A: blog-writer-env secrets
for ENV in dev staging prod; do
    SECRET_NAME="blog-writer-env-${ENV}"
    if gcloud secrets describe "${SECRET_NAME}" --project="${PROJECT_ID}" &>/dev/null; then
        echo -e "${GREEN}✓ ${SECRET_NAME} exists${NC}"
        
        # Check if it contains Google Custom Search keys
        SECRET_CONTENT=$(gcloud secrets versions access latest --secret="${SECRET_NAME}" --project="${PROJECT_ID}" 2>/dev/null || echo "")
        if echo "$SECRET_CONTENT" | grep -q "GOOGLE_CUSTOM_SEARCH_API_KEY"; then
            echo -e "  ${GREEN}✓ Contains GOOGLE_CUSTOM_SEARCH_API_KEY${NC}"
        else
            echo -e "  ${RED}✗ Missing GOOGLE_CUSTOM_SEARCH_API_KEY${NC}"
        fi
        
        if echo "$SECRET_CONTENT" | grep -q "GOOGLE_CUSTOM_SEARCH_ENGINE_ID"; then
            echo -e "  ${GREEN}✓ Contains GOOGLE_CUSTOM_SEARCH_ENGINE_ID${NC}"
        else
            echo -e "  ${RED}✗ Missing GOOGLE_CUSTOM_SEARCH_ENGINE_ID${NC}"
        fi
    else
        echo -e "${YELLOW}⚠ ${SECRET_NAME} does not exist${NC}"
    fi
done

echo ""

# Check Option B: Individual secrets
if gcloud secrets describe "GOOGLE_CUSTOM_SEARCH_API_KEY" --project="${PROJECT_ID}" &>/dev/null; then
    echo -e "${GREEN}✓ GOOGLE_CUSTOM_SEARCH_API_KEY secret exists${NC}"
else
    echo -e "${YELLOW}⚠ GOOGLE_CUSTOM_SEARCH_API_KEY secret does not exist${NC}"
fi

if gcloud secrets describe "GOOGLE_CUSTOM_SEARCH_ENGINE_ID" --project="${PROJECT_ID}" &>/dev/null; then
    echo -e "${GREEN}✓ GOOGLE_CUSTOM_SEARCH_ENGINE_ID secret exists${NC}"
else
    echo -e "${YELLOW}⚠ GOOGLE_CUSTOM_SEARCH_ENGINE_ID secret does not exist${NC}"
fi

echo ""

# Check service account permissions
echo -e "${YELLOW}Checking service account permissions...${NC}"
SERVICE_ACCOUNT="blog-writer-service-account@${PROJECT_ID}.iam.gserviceaccount.com"

for ENV in dev staging prod; do
    SECRET_NAME="blog-writer-env-${ENV}"
    if gcloud secrets get-iam-policy "${SECRET_NAME}" --project="${PROJECT_ID}" 2>/dev/null | grep -q "${SERVICE_ACCOUNT}"; then
        echo -e "${GREEN}✓ ${SERVICE_ACCOUNT} has access to ${SECRET_NAME}${NC}"
    else
        echo -e "${RED}✗ ${SERVICE_ACCOUNT} does NOT have access to ${SECRET_NAME}${NC}"
    fi
done

if gcloud secrets get-iam-policy "GOOGLE_CUSTOM_SEARCH_API_KEY" --project="${PROJECT_ID}" 2>/dev/null | grep -q "${SERVICE_ACCOUNT}"; then
    echo -e "${GREEN}✓ ${SERVICE_ACCOUNT} has access to GOOGLE_CUSTOM_SEARCH_API_KEY${NC}"
else
    echo -e "${YELLOW}⚠ ${SERVICE_ACCOUNT} may not have access to GOOGLE_CUSTOM_SEARCH_API_KEY${NC}"
fi

if gcloud secrets get-iam-policy "GOOGLE_CUSTOM_SEARCH_ENGINE_ID" --project="${PROJECT_ID}" 2>/dev/null | grep -q "${SERVICE_ACCOUNT}"; then
    echo -e "${GREEN}✓ ${SERVICE_ACCOUNT} has access to GOOGLE_CUSTOM_SEARCH_ENGINE_ID${NC}"
else
    echo -e "${YELLOW}⚠ ${SERVICE_ACCOUNT} may not have access to GOOGLE_CUSTOM_SEARCH_ENGINE_ID${NC}"
fi

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Verification complete!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

