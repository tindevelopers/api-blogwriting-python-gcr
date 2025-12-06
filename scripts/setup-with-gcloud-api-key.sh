#!/bin/bash
# Setup Google Custom Search using API key retrieved via gcloud CLI

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROJECT_ID=$(gcloud config get-value project 2>/dev/null || echo "api-ai-blog-writer")
ENV="${1:-dev}"  # Default to dev if not specified

echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Google Custom Search API Setup (Using gcloud CLI)${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}Project: ${PROJECT_ID}${NC}"
echo -e "${BLUE}Environment: ${ENV}${NC}"
echo ""

# Step 1: Get API key via gcloud
echo -e "${YELLOW}Step 1: Retrieving API key via gcloud CLI...${NC}"
EXISTING_KEY=$(gcloud services api-keys list --project="${PROJECT_ID}" --filter="restrictions.apiTargets.service:customsearch.googleapis.com" --format="value(name)" 2>/dev/null | head -1)

if [ ! -z "$EXISTING_KEY" ]; then
    echo -e "${GREEN}✓ Found API key resource: ${EXISTING_KEY}${NC}"
    
    # Get the actual key value
    API_KEY_VALUE=$(gcloud services api-keys get-key-string "${EXISTING_KEY}" --project="${PROJECT_ID}" --format="value(keyString)" 2>/dev/null || echo "")
    
    if [ ! -z "$API_KEY_VALUE" ] && [[ ! "$API_KEY_VALUE" =~ "error" ]] && [[ ! "$API_KEY_VALUE" =~ "ERROR" ]]; then
        GOOGLE_CUSTOM_SEARCH_API_KEY="$API_KEY_VALUE"
        echo -e "${GREEN}✓ Retrieved API key: ${API_KEY_VALUE:0:20}...${NC}"
    else
        echo -e "${RED}✗ Could not retrieve API key value${NC}"
        exit 1
    fi
else
    echo -e "${RED}✗ No API key found for Custom Search API${NC}"
    echo "Please create one at: https://console.cloud.google.com/apis/credentials?project=${PROJECT_ID}"
    exit 1
fi
echo ""

# Step 2: Get Engine ID (must be provided by user)
echo -e "${YELLOW}Step 2: Custom Search Engine ID (CX)${NC}"
echo ""
echo -e "${BLUE}The Engine ID must be created manually:${NC}"
echo "1. Go to: https://programmablesearchengine.google.com/"
echo "2. Click 'Add' to create a new search engine"
echo "3. Enter a name (e.g., 'Blog Writer Search')"
echo "4. In 'Sites to search', enter '*' to search the entire web"
echo "5. Click 'Create'"
echo "6. Copy the 'Search engine ID' (CX) from the Overview page"
echo ""

if [ -z "$2" ]; then
    read -p "Enter GOOGLE_CUSTOM_SEARCH_ENGINE_ID (CX): " GOOGLE_CUSTOM_SEARCH_ENGINE_ID
else
    GOOGLE_CUSTOM_SEARCH_ENGINE_ID="$2"
    echo -e "${GREEN}Using provided Engine ID: ${GOOGLE_CUSTOM_SEARCH_ENGINE_ID}${NC}"
fi

if [ -z "$GOOGLE_CUSTOM_SEARCH_ENGINE_ID" ]; then
    echo -e "${RED}Error: Engine ID is required${NC}"
    exit 1
fi

echo ""

# Step 3: Update secret using the setup script approach
echo -e "${YELLOW}Step 3: Updating secret ${SECRET_NAME}...${NC}"
SECRET_NAME="blog-writer-env-${ENV}"

# Check if secret exists
if ! gcloud secrets describe "${SECRET_NAME}" --project="${PROJECT_ID}" &>/dev/null; then
    echo -e "${YELLOW}Creating secret ${SECRET_NAME}...${NC}"
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
    grep -v "GOOGLE_CUSTOM_SEARCH_API_KEY=" "$TEMP_FILE" > "${TEMP_FILE}.tmp" 2>/dev/null || true
    grep -v "GOOGLE_CUSTOM_SEARCH_ENGINE_ID=" "${TEMP_FILE}.tmp" > "${TEMP_FILE}.new" 2>/dev/null || true
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
echo "Adding credentials to secret..."
gcloud secrets versions add "${SECRET_NAME}" \
    --project="${PROJECT_ID}" \
    --data-file="${TEMP_FILE}" \
    --quiet

# Clean up
rm -f "$TEMP_FILE"

echo -e "${GREEN}✓ Credentials added to ${SECRET_NAME}${NC}"
echo ""

# Grant service account access
echo -e "${YELLOW}Step 4: Granting service account access...${NC}"
SERVICE_ACCOUNT="blog-writer-service-account@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud secrets add-iam-policy-binding "${SECRET_NAME}" \
    --project="${PROJECT_ID}" \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/secretmanager.secretAccessor" \
    --quiet 2>/dev/null || echo "Policy binding may already exist"

echo -e "${GREEN}✓ Service account access granted${NC}"
echo ""

echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}Summary:${NC}"
echo -e "  Secret: ${SECRET_NAME}"
echo -e "  API Key: ${GOOGLE_CUSTOM_SEARCH_API_KEY:0:20}..."
echo -e "  Engine ID: ${GOOGLE_CUSTOM_SEARCH_ENGINE_ID}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Redeploy Cloud Run service"
echo "2. Verify: ./scripts/verify-google-custom-search-setup.sh"
echo "3. Test Multi-Phase mode"
echo ""

