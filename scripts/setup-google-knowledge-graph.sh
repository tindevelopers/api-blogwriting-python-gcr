#!/bin/bash
# Setup Google Knowledge Graph API using gcloud CLI

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
echo -e "${GREEN}Google Knowledge Graph API Setup${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}Project: ${PROJECT_ID}${NC}"
echo -e "${BLUE}Environment: ${ENV}${NC}"
echo ""

# Step 1: Enable Knowledge Graph API
echo -e "${YELLOW}Step 1: Enabling Knowledge Graph API...${NC}"
if gcloud services list --enabled --filter="name:kgsearch.googleapis.com" --project="${PROJECT_ID}" --format="value(name)" 2>/dev/null | grep -q "kgsearch.googleapis.com"; then
    echo -e "${GREEN}✓ Knowledge Graph API is already enabled${NC}"
else
    echo "Enabling Knowledge Graph API..."
    gcloud services enable kgsearch.googleapis.com --project="${PROJECT_ID}" 2>&1 | grep -v "already enabled" || true
    echo -e "${GREEN}✓ Knowledge Graph API enabled${NC}"
fi
echo ""

# Step 2: Get existing API key or create new one
echo -e "${YELLOW}Step 2: Retrieving API key...${NC}"
EXISTING_KEY=$(gcloud services api-keys list --project="${PROJECT_ID}" --filter="restrictions.apiTargets.service:kgsearch.googleapis.com" --format="value(name)" 2>/dev/null | head -1)

if [ ! -z "$EXISTING_KEY" ]; then
    echo -e "${GREEN}✓ Found existing API key: ${EXISTING_KEY}${NC}"
    
    # Get the actual key value
    API_KEY_VALUE=$(gcloud services api-keys get-key-string "${EXISTING_KEY}" --project="${PROJECT_ID}" --format="value(keyString)" 2>/dev/null || echo "")
    
    if [ ! -z "$API_KEY_VALUE" ] && [[ ! "$API_KEY_VALUE" =~ "error" ]]; then
        GOOGLE_KNOWLEDGE_GRAPH_API_KEY="$API_KEY_VALUE"
        echo -e "${GREEN}✓ Retrieved API key: ${API_KEY_VALUE:0:20}...${NC}"
    else
        echo -e "${RED}✗ Could not retrieve API key value${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}No existing API key found. Creating new one...${NC}"
    
    # Try to create API key via CLI
    KEY_RESOURCE=$(gcloud alpha services api-keys create \
        --display-name="Blog Writer Knowledge Graph API Key" \
        --api-target=service=kgsearch.googleapis.com \
        --project="${PROJECT_ID}" \
        --format="value(name)" 2>&1) || KEY_RESOURCE=""
    
    if [ ! -z "$KEY_RESOURCE" ] && [[ ! "$KEY_RESOURCE" =~ "error" ]] && [[ ! "$KEY_RESOURCE" =~ "ERROR" ]]; then
        echo -e "${GREEN}✓ API key created: ${KEY_RESOURCE}${NC}"
        
        # Get the actual key value
        API_KEY_VALUE=$(gcloud alpha services api-keys get-key-string "${KEY_RESOURCE}" --project="${PROJECT_ID}" --format="value(keyString)" 2>&1 || echo "")
        
        if [ ! -z "$API_KEY_VALUE" ] && [[ ! "$API_KEY_VALUE" =~ "error" ]]; then
            GOOGLE_KNOWLEDGE_GRAPH_API_KEY="$API_KEY_VALUE"
            echo -e "${GREEN}✓ API key value retrieved: ${API_KEY_VALUE:0:20}...${NC}"
        else
            echo -e "${YELLOW}⚠ Could not retrieve key value automatically${NC}"
            echo "Please get the key value from: https://console.cloud.google.com/apis/credentials?project=${PROJECT_ID}"
            read -p "Enter GOOGLE_KNOWLEDGE_GRAPH_API_KEY: " GOOGLE_KNOWLEDGE_GRAPH_API_KEY
        fi
    else
        echo -e "${YELLOW}⚠ Could not create API key via CLI${NC}"
        echo ""
        echo "Please create an API key manually:"
        echo "1. Go to: https://console.cloud.google.com/apis/credentials?project=${PROJECT_ID}"
        echo "2. Click 'Create Credentials' → 'API Key'"
        echo "3. (Optional) Click 'Restrict Key' → Restrict to 'Knowledge Graph Search API'"
        echo "4. Copy the API key"
        echo ""
        read -p "Enter GOOGLE_KNOWLEDGE_GRAPH_API_KEY: " GOOGLE_KNOWLEDGE_GRAPH_API_KEY
    fi
fi

if [ -z "$GOOGLE_KNOWLEDGE_GRAPH_API_KEY" ]; then
    echo -e "${RED}Error: API key is required${NC}"
    exit 1
fi

echo ""

# Step 3: Update secret
echo -e "${YELLOW}Step 3: Updating secret...${NC}"
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
    
    # Remove old Google Knowledge Graph entry if it exists
    grep -v "GOOGLE_KNOWLEDGE_GRAPH_API_KEY=" "$TEMP_FILE" > "${TEMP_FILE}.tmp" 2>/dev/null || true
    mv "${TEMP_FILE}.tmp" "$TEMP_FILE"
else
    # Create new secret file
    touch "$TEMP_FILE"
fi

# Add new Google Knowledge Graph credential
echo "GOOGLE_KNOWLEDGE_GRAPH_API_KEY=${GOOGLE_KNOWLEDGE_GRAPH_API_KEY}" >> "$TEMP_FILE"

# Update secret
echo "Adding credential to secret..."
gcloud secrets versions add "${SECRET_NAME}" \
    --project="${PROJECT_ID}" \
    --data-file="${TEMP_FILE}" \
    --quiet

# Clean up
rm -f "$TEMP_FILE"

echo -e "${GREEN}✓ Credential added to ${SECRET_NAME}${NC}"
echo ""

# Step 4: Create separate secret for cloudbuild.yaml
echo -e "${YELLOW}Step 4: Creating separate secret for deployment...${NC}"
if gcloud secrets describe "GOOGLE_KNOWLEDGE_GRAPH_API_KEY" --project="${PROJECT_ID}" &>/dev/null; then
    echo -e "${YELLOW}Secret already exists. Updating...${NC}"
    echo -n "${GOOGLE_KNOWLEDGE_GRAPH_API_KEY}" | gcloud secrets versions add "GOOGLE_KNOWLEDGE_GRAPH_API_KEY" \
        --project="${PROJECT_ID}" \
        --data-file=- \
        --quiet
else
    echo -n "${GOOGLE_KNOWLEDGE_GRAPH_API_KEY}" | gcloud secrets create "GOOGLE_KNOWLEDGE_GRAPH_API_KEY" \
        --project="${PROJECT_ID}" \
        --data-file=-
fi

# Grant service account access
SERVICE_ACCOUNT="613248238610-compute@developer.gserviceaccount.com"
gcloud secrets add-iam-policy-binding "GOOGLE_KNOWLEDGE_GRAPH_API_KEY" \
    --project="${PROJECT_ID}" \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/secretmanager.secretAccessor" \
    --quiet 2>/dev/null || echo "Policy binding may already exist"

echo -e "${GREEN}✓ Separate secret created and access granted${NC}"
echo ""

echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}Summary:${NC}"
echo -e "  Secret: ${SECRET_NAME}"
echo -e "  API Key: ${GOOGLE_KNOWLEDGE_GRAPH_API_KEY:0:20}..."
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Update cloudbuild.yaml to mount GOOGLE_KNOWLEDGE_GRAPH_API_KEY"
echo "2. Update service.yaml to reference the secret"
echo "3. Redeploy Cloud Run service"
echo ""

