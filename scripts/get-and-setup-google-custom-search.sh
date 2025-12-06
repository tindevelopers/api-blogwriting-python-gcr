#!/bin/bash
# Get Google Custom Search API credentials using gcloud CLI and set them up

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROJECT_ID=$(gcloud config get-value project 2>/dev/null || echo "api-ai-blog-writer")

echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Google Custom Search API - Get & Setup Credentials${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}Project: ${PROJECT_ID}${NC}"
echo ""

# Step 1: Enable Custom Search API
echo -e "${YELLOW}Step 1: Enabling Custom Search API...${NC}"
if gcloud services list --enabled --filter="name:customsearch.googleapis.com" --project="${PROJECT_ID}" --format="value(name)" 2>/dev/null | grep -q "customsearch.googleapis.com"; then
    echo -e "${GREEN}✓ Custom Search API is already enabled${NC}"
else
    echo "Enabling Custom Search API..."
    gcloud services enable customsearch.googleapis.com --project="${PROJECT_ID}" 2>&1 | grep -v "already enabled" || true
    echo -e "${GREEN}✓ Custom Search API enabled${NC}"
fi
echo ""

# Step 2: Check for existing API keys
echo -e "${YELLOW}Step 2: Checking for existing API keys...${NC}"
EXISTING_KEYS=$(gcloud services api-keys list --project="${PROJECT_ID}" --format="table(name,displayName)" 2>/dev/null | grep -v "DISPLAY_NAME" | wc -l | tr -d ' ')

if [ "$EXISTING_KEYS" -gt 0 ]; then
    echo -e "${GREEN}Found ${EXISTING_KEYS} existing API key(s):${NC}"
    gcloud services api-keys list --project="${PROJECT_ID}" --format="table(name,displayName)" 2>/dev/null | head -10
    echo ""
    read -p "Use existing API key? (y/N): " USE_EXISTING
    
    if [[ "$USE_EXISTING" =~ ^[Yy]$ ]]; then
        echo ""
        echo "Available API keys:"
        gcloud services api-keys list --project="${PROJECT_ID}" --format="table(name,displayName)" 2>/dev/null
        echo ""
        read -p "Enter API key name (full path, e.g., projects/.../apiKeys/...): " KEY_NAME
        
        if [ ! -z "$KEY_NAME" ]; then
            echo "Retrieving API key value..."
            API_KEY_VALUE=$(gcloud services api-keys get-key-string "${KEY_NAME}" --project="${PROJECT_ID}" --format="value(keyString)" 2>/dev/null || echo "")
            
            if [ ! -z "$API_KEY_VALUE" ]; then
                GOOGLE_CUSTOM_SEARCH_API_KEY="$API_KEY_VALUE"
                echo -e "${GREEN}✓ Retrieved API key: ${API_KEY_VALUE:0:20}...${NC}"
            else
                echo -e "${RED}✗ Could not retrieve API key value${NC}"
                GOOGLE_CUSTOM_SEARCH_API_KEY=""
            fi
        else
            GOOGLE_CUSTOM_SEARCH_API_KEY=""
        fi
    else
        GOOGLE_CUSTOM_SEARCH_API_KEY=""
    fi
else
    echo "No existing API keys found"
    GOOGLE_CUSTOM_SEARCH_API_KEY=""
fi
echo ""

# Step 3: Create new API key if needed
if [ -z "$GOOGLE_CUSTOM_SEARCH_API_KEY" ]; then
    echo -e "${YELLOW}Step 3: Creating new API key...${NC}"
    echo ""
    echo -e "${BLUE}Attempting to create API key via gcloud CLI (alpha feature)...${NC}"
    
    # Try to create API key via CLI
    KEY_RESOURCE=$(gcloud alpha services api-keys create \
        --display-name="Blog Writer Custom Search API Key" \
        --api-target=service=customsearch.googleapis.com \
        --project="${PROJECT_ID}" \
        --format="value(name)" 2>&1) || KEY_RESOURCE=""
    
    if [ ! -z "$KEY_RESOURCE" ] && [[ ! "$KEY_RESOURCE" =~ "error" ]] && [[ ! "$KEY_RESOURCE" =~ "ERROR" ]]; then
        echo -e "${GREEN}✓ API key created: ${KEY_RESOURCE}${NC}"
        
        # Get the actual key value
        API_KEY_VALUE=$(gcloud alpha services api-keys get-key-string "${KEY_RESOURCE}" --project="${PROJECT_ID}" --format="value(keyString)" 2>&1 || echo "")
        
        if [ ! -z "$API_KEY_VALUE" ] && [[ ! "$API_KEY_VALUE" =~ "error" ]]; then
            GOOGLE_CUSTOM_SEARCH_API_KEY="$API_KEY_VALUE"
            echo -e "${GREEN}✓ API key value retrieved: ${API_KEY_VALUE:0:20}...${NC}"
        else
            echo -e "${YELLOW}⚠ Could not retrieve key value automatically${NC}"
            echo "Please get the key value from: https://console.cloud.google.com/apis/credentials"
            read -p "Enter GOOGLE_CUSTOM_SEARCH_API_KEY: " GOOGLE_CUSTOM_SEARCH_API_KEY
        fi
    else
        echo -e "${YELLOW}⚠ Could not create API key via CLI${NC}"
        echo ""
        echo "Please create an API key manually:"
        echo "1. Go to: https://console.cloud.google.com/apis/credentials?project=${PROJECT_ID}"
        echo "2. Click 'Create Credentials' → 'API Key'"
        echo "3. (Optional) Click 'Restrict Key' → Restrict to 'Custom Search API'"
        echo "4. Copy the API key"
        echo ""
        read -p "Enter GOOGLE_CUSTOM_SEARCH_API_KEY: " GOOGLE_CUSTOM_SEARCH_API_KEY
    fi
    echo ""
fi

# Step 4: Get Custom Search Engine ID (CX)
echo -e "${YELLOW}Step 4: Get Custom Search Engine ID (CX)...${NC}"
echo ""
echo -e "${BLUE}Note: Custom Search Engine ID must be created manually${NC}"
echo ""
echo "To create a Custom Search Engine:"
echo "1. Go to: https://programmablesearchengine.google.com/"
echo "2. Click 'Add' to create a new search engine"
echo "3. Enter a name (e.g., 'Blog Writer Search')"
echo "4. In 'Sites to search', enter '*' to search the entire web"
echo "5. Click 'Create'"
echo "6. Copy the 'Search engine ID' (CX) from the Overview page"
echo ""
read -p "Enter GOOGLE_CUSTOM_SEARCH_ENGINE_ID (CX): " GOOGLE_CUSTOM_SEARCH_ENGINE_ID

# Validate inputs
if [ -z "$GOOGLE_CUSTOM_SEARCH_API_KEY" ]; then
    echo -e "${RED}Error: API key is required${NC}"
    exit 1
fi

if [ -z "$GOOGLE_CUSTOM_SEARCH_ENGINE_ID" ]; then
    echo -e "${RED}Error: Engine ID is required${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Credentials Retrieved:${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "API Key: ${GOOGLE_CUSTOM_SEARCH_API_KEY:0:20}..."
echo -e "Engine ID: ${GOOGLE_CUSTOM_SEARCH_ENGINE_ID}"
echo ""

# Step 5: Run setup script with credentials
echo -e "${YELLOW}Step 5: Setting up secrets...${NC}"
echo ""

# Determine environment
echo "Select environment:"
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
echo "Updating secret ${SECRET_NAME}..."
gcloud secrets versions add "${SECRET_NAME}" \
    --project="${PROJECT_ID}" \
    --data-file="${TEMP_FILE}"

# Clean up
rm -f "$TEMP_FILE"

echo ""
echo -e "${GREEN}✅ Google Custom Search API credentials added to ${SECRET_NAME}${NC}"
echo ""

# Grant service account access
echo -e "${YELLOW}Granting service account access...${NC}"
SERVICE_ACCOUNT="blog-writer-service-account@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud secrets add-iam-policy-binding "${SECRET_NAME}" \
    --project="${PROJECT_ID}" \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/secretmanager.secretAccessor" 2>/dev/null || echo "Policy binding may already exist"

echo -e "${GREEN}✅ Service account access granted${NC}"
echo ""

echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Redeploy Cloud Run service to load new credentials"
echo "2. Verify setup: ./scripts/verify-google-custom-search-setup.sh"
echo "3. Test Multi-Phase mode with citations"
echo ""

