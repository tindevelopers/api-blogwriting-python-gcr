#!/bin/bash
# Script to set up Google Custom Search API credentials in Google Secret Manager

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Google Custom Search API Secrets Setup${NC}"
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

# Determine environment (dev, staging, prod)
echo -e "${YELLOW}Select environment:${NC}"
echo "1) dev"
echo "2) staging"
echo "3) prod"
read -p "Enter choice (1-3): " ENV_CHOICE

case $ENV_CHOICE in
    1) ENV="dev" ;;
    2) ENV="staging" ;;
    3) ENV="prod" ;;
    *) echo -e "${RED}Invalid choice${NC}"; exit 1 ;;
esac

SECRET_NAME="blog-writer-env-${ENV}"
echo ""
echo -e "${YELLOW}Updating secret: ${SECRET_NAME}${NC}"
echo ""

# Check if secret exists
if ! gcloud secrets describe "${SECRET_NAME}" --project="${PROJECT_ID}" &>/dev/null; then
    echo -e "${YELLOW}Secret ${SECRET_NAME} does not exist. Creating...${NC}"
    echo "" | gcloud secrets create "${SECRET_NAME}" \
        --project="${PROJECT_ID}" \
        --data-file=-
fi

# Get current secret value
CURRENT_SECRET=$(gcloud secrets versions access latest --secret="${SECRET_NAME}" --project="${PROJECT_ID}" 2>/dev/null || echo "")

# Create temporary file with updated secrets
TEMP_FILE=$(mktemp)

if [ -n "$CURRENT_SECRET" ]; then
    # Update existing secrets
    echo "$CURRENT_SECRET" > "$TEMP_FILE"
    
    # Remove old Google Custom Search entries if they exist
    grep -v "GOOGLE_CUSTOM_SEARCH_API_KEY=" "$TEMP_FILE" > "${TEMP_FILE}.tmp" || true
    grep -v "GOOGLE_CUSTOM_SEARCH_ENGINE_ID=" "${TEMP_FILE}.tmp" > "${TEMP_FILE}.new" || true
    mv "${TEMP_FILE}.new" "$TEMP_FILE"
    rm -f "${TEMP_FILE}.tmp"
else
    # Create new secret file
    touch "$TEMP_FILE"
fi

# Add new Google Custom Search credentials
echo "GOOGLE_CUSTOM_SEARCH_API_KEY=${GOOGLE_CUSTOM_SEARCH_API_KEY}" >> "$TEMP_FILE"
echo "GOOGLE_CUSTOM_SEARCH_ENGINE_ID=${GOOGLE_CUSTOM_SEARCH_ENGINE_ID}" >> "$TEMP_FILE"

# Update secret
gcloud secrets versions add "${SECRET_NAME}" \
    --project="${PROJECT_ID}" \
    --data-file="${TEMP_FILE}"

# Clean up
rm -f "$TEMP_FILE"

echo ""
echo -e "${GREEN}✅ Google Custom Search API credentials added to ${SECRET_NAME}${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Update cloudbuild.yaml to mount these secrets"
echo "2. Redeploy the Cloud Run service"
echo "3. Verify the service can access the secrets"
echo ""

