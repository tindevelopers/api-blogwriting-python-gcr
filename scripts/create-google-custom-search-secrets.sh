#!/bin/bash
# Create separate secrets for Google Custom Search API credentials
# This is an alternative approach - creating individual secrets instead of adding to blog-writer-env

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Create Google Custom Search API Secrets${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Get project ID
PROJECT_ID=$(gcloud config get-value project 2>/dev/null || echo "")
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}Error: No Google Cloud project configured.${NC}"
    echo "Please run: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo -e "${YELLOW}Project: ${PROJECT_ID}${NC}"
echo ""

# Prompt for API Key
echo -e "${YELLOW}Enter your Google Custom Search API Key:${NC}"
read -s GOOGLE_CUSTOM_SEARCH_API_KEY
echo ""

if [ -z "$GOOGLE_CUSTOM_SEARCH_API_KEY" ]; then
    echo -e "${RED}Error: API Key cannot be empty${NC}"
    exit 1
fi

# Prompt for Engine ID
echo -e "${YELLOW}Enter your Google Custom Search Engine ID (CX):${NC}"
read GOOGLE_CUSTOM_SEARCH_ENGINE_ID
echo ""

if [ -z "$GOOGLE_CUSTOM_SEARCH_ENGINE_ID" ]; then
    echo -e "${RED}Error: Engine ID cannot be empty${NC}"
    exit 1
fi

# Create secrets
echo -e "${YELLOW}Creating secrets...${NC}"

# Create API Key secret
if gcloud secrets describe "GOOGLE_CUSTOM_SEARCH_API_KEY" --project="${PROJECT_ID}" &>/dev/null; then
    echo -e "${YELLOW}Secret GOOGLE_CUSTOM_SEARCH_API_KEY already exists. Adding new version...${NC}"
    echo -n "${GOOGLE_CUSTOM_SEARCH_API_KEY}" | gcloud secrets versions add "GOOGLE_CUSTOM_SEARCH_API_KEY" \
        --project="${PROJECT_ID}" \
        --data-file=-
else
    echo -n "${GOOGLE_CUSTOM_SEARCH_API_KEY}" | gcloud secrets create "GOOGLE_CUSTOM_SEARCH_API_KEY" \
        --project="${PROJECT_ID}" \
        --data-file=-
fi

# Create Engine ID secret
if gcloud secrets describe "GOOGLE_CUSTOM_SEARCH_ENGINE_ID" --project="${PROJECT_ID}" &>/dev/null; then
    echo -e "${YELLOW}Secret GOOGLE_CUSTOM_SEARCH_ENGINE_ID already exists. Adding new version...${NC}"
    echo -n "${GOOGLE_CUSTOM_SEARCH_ENGINE_ID}" | gcloud secrets versions add "GOOGLE_CUSTOM_SEARCH_ENGINE_ID" \
        --project="${PROJECT_ID}" \
        --data-file=-
else
    echo -n "${GOOGLE_CUSTOM_SEARCH_ENGINE_ID}" | gcloud secrets create "GOOGLE_CUSTOM_SEARCH_ENGINE_ID" \
        --project="${PROJECT_ID}" \
        --data-file=-
fi

echo ""
echo -e "${GREEN}✅ Secrets created successfully${NC}"
echo ""
echo -e "${YELLOW}Granting Cloud Run service account access...${NC}"

# Grant Cloud Run service account access
SERVICE_ACCOUNT="blog-writer-service-account@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud secrets add-iam-policy-binding "GOOGLE_CUSTOM_SEARCH_API_KEY" \
    --project="${PROJECT_ID}" \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/secretmanager.secretAccessor" 2>/dev/null || echo "Policy binding may already exist"

gcloud secrets add-iam-policy-binding "GOOGLE_CUSTOM_SEARCH_ENGINE_ID" \
    --project="${PROJECT_ID}" \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/secretmanager.secretAccessor" 2>/dev/null || echo "Policy binding may already exist"

echo ""
echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. The secrets are now available in Secret Manager"
echo "2. cloudbuild.yaml has been updated to mount these secrets"
echo "3. Redeploy the Cloud Run service to apply changes"
echo ""

