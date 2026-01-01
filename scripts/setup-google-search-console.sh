#!/bin/bash
# Setup Google Search Console API

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
echo -e "${GREEN}Google Search Console API Setup${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}Project: ${PROJECT_ID}${NC}"
echo -e "${BLUE}Environment: ${ENV}${NC}"
echo ""

# Step 1: Enable Search Console API
echo -e "${YELLOW}Step 1: Enabling Search Console API...${NC}"
if gcloud services list --enabled --filter="name:searchconsole.googleapis.com" --project="${PROJECT_ID}" --format="value(name)" 2>/dev/null | grep -q "searchconsole.googleapis.com"; then
    echo -e "${GREEN}✓ Search Console API is already enabled${NC}"
else
    echo "Enabling Search Console API..."
    gcloud services enable searchconsole.googleapis.com --project="${PROJECT_ID}" 2>&1 | grep -v "already enabled" || true
    echo -e "${GREEN}✓ Search Console API enabled${NC}"
fi
echo ""

# Step 2: Get Site URL
echo -e "${YELLOW}Step 2: Site URL Configuration${NC}"
echo ""
echo -e "${BLUE}Google Search Console requires a site URL.${NC}"
echo "Format examples:"
echo "  - https://example.com"
echo "  - sc-domain:example.com (for domain properties)"
echo ""
read -p "Enter GSC_SITE_URL (or press Enter to skip): " GSC_SITE_URL

if [ -z "$GSC_SITE_URL" ]; then
    echo -e "${YELLOW}⚠ Site URL not provided. Skipping Search Console setup.${NC}"
    echo ""
    echo "To set up Search Console later:"
    echo "1. Go to: https://search.google.com/search-console"
    echo "2. Add your property"
    echo "3. Copy the site URL"
    echo "4. Run this script again with the site URL"
    exit 0
fi

echo ""

# Step 3: Service Account Setup
echo -e "${YELLOW}Step 3: Service Account Setup${NC}"
echo ""
echo -e "${BLUE}Google Search Console requires service account credentials.${NC}"
echo ""
echo "Options:"
echo "1. Use existing service account credentials"
echo "2. Create new service account"
echo ""
read -p "Enter choice (1-2): " SA_CHOICE

SERVICE_ACCOUNT_EMAIL=""
SERVICE_ACCOUNT_KEY_PATH=""

case $SA_CHOICE in
    1)
        echo ""
        echo "Existing service accounts:"
        gcloud iam service-accounts list --project="${PROJECT_ID}" --format="table(email)" 2>/dev/null | head -10
        echo ""
        read -p "Enter service account email: " SERVICE_ACCOUNT_EMAIL
        
        if [ -z "$SERVICE_ACCOUNT_EMAIL" ]; then
            echo -e "${RED}Error: Service account email is required${NC}"
            exit 1
        fi
        
        # Check if service account exists
        if ! gcloud iam service-accounts describe "${SERVICE_ACCOUNT_EMAIL}" --project="${PROJECT_ID}" &>/dev/null; then
            echo -e "${RED}Error: Service account not found${NC}"
            exit 1
        fi
        
        echo ""
        echo "Do you have a JSON key file for this service account?"
        read -p "Enter path to JSON key file (or press Enter to create new key): " SERVICE_ACCOUNT_KEY_PATH
        
        if [ -z "$SERVICE_ACCOUNT_KEY_PATH" ] || [ ! -f "$SERVICE_ACCOUNT_KEY_PATH" ]; then
            echo "Creating new key..."
            KEY_FILE="/tmp/${SERVICE_ACCOUNT_EMAIL//[@.]/_}_key.json"
            gcloud iam service-accounts keys create "${KEY_FILE}" \
                --iam-account="${SERVICE_ACCOUNT_EMAIL}" \
                --project="${PROJECT_ID}"
            SERVICE_ACCOUNT_KEY_PATH="${KEY_FILE}"
            echo -e "${GREEN}✓ Key created: ${KEY_FILE}${NC}"
        fi
        ;;
    2)
        echo ""
        read -p "Enter service account name (e.g., blog-writer-gsc): " SA_NAME
        SERVICE_ACCOUNT_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
        
        # Create service account
        gcloud iam service-accounts create "${SA_NAME}" \
            --project="${PROJECT_ID}" \
            --display-name="Blog Writer Google Search Console" \
            --description="Service account for Google Search Console API access" 2>/dev/null || echo "Service account may already exist"
        
        # Create key
        KEY_FILE="/tmp/${SA_NAME}_key.json"
        gcloud iam service-accounts keys create "${KEY_FILE}" \
            --iam-account="${SERVICE_ACCOUNT_EMAIL}" \
            --project="${PROJECT_ID}"
        
        SERVICE_ACCOUNT_KEY_PATH="${KEY_FILE}"
        echo -e "${GREEN}✓ Service account created: ${SERVICE_ACCOUNT_EMAIL}${NC}"
        echo -e "${GREEN}✓ Key created: ${KEY_FILE}${NC}"
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${YELLOW}Step 4: Grant Search Console Access${NC}"
echo ""
echo -e "${BLUE}Important: You need to grant this service account access in Google Search Console:${NC}"
echo "1. Go to: https://search.google.com/search-console"
echo "2. Select your property (${GSC_SITE_URL})"
echo "3. Go to Settings → Users and permissions"
echo "4. Click 'Add user'"
echo "5. Enter: ${SERVICE_ACCOUNT_EMAIL}"
echo "6. Grant 'Full' access"
echo "7. Click 'Add'"
echo ""
read -p "Press Enter after granting access in Search Console..."

echo ""

# Step 5: Store credentials in Secret Manager
echo -e "${YELLOW}Step 5: Storing credentials in Secret Manager...${NC}"

# Store site URL in blog-writer-env secret
SECRET_NAME="blog-writer-env-${ENV}"

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
    echo "$CURRENT_SECRET" > "$TEMP_FILE"
    grep -v "GSC_SITE_URL=" "$TEMP_FILE" > "${TEMP_FILE}.tmp" 2>/dev/null || true
    mv "${TEMP_FILE}.tmp" "$TEMP_FILE"
else
    touch "$TEMP_FILE"
fi

# Add GSC_SITE_URL
echo "GSC_SITE_URL=${GSC_SITE_URL}" >> "$TEMP_FILE"

# Update secret
gcloud secrets versions add "${SECRET_NAME}" \
    --project="${PROJECT_ID}" \
    --data-file="${TEMP_FILE}" \
    --quiet

rm -f "$TEMP_FILE"

# Store service account key as secret
SA_KEY_SECRET_NAME="GSC_SERVICE_ACCOUNT_KEY"
if gcloud secrets describe "${SA_KEY_SECRET_NAME}" --project="${PROJECT_ID}" &>/dev/null; then
    cat "${SERVICE_ACCOUNT_KEY_PATH}" | gcloud secrets versions add "${SA_KEY_SECRET_NAME}" \
        --project="${PROJECT_ID}" \
        --data-file=- \
        --quiet
else
    cat "${SERVICE_ACCOUNT_KEY_PATH}" | gcloud secrets create "${SA_KEY_SECRET_NAME}" \
        --project="${PROJECT_ID}" \
        --data-file=-
fi

# Grant service account access
CLOUD_RUN_SA="613248238610-compute@developer.gserviceaccount.com"
gcloud secrets add-iam-policy-binding "${SA_KEY_SECRET_NAME}" \
    --project="${PROJECT_ID}" \
    --member="serviceAccount:${CLOUD_RUN_SA}" \
    --role="roles/secretmanager.secretAccessor" \
    --quiet 2>/dev/null || echo "Policy binding may already exist"

echo -e "${GREEN}✓ Credentials stored in Secret Manager${NC}"
echo ""

# Clean up temporary key file if we created it
if [[ "$SERVICE_ACCOUNT_KEY_PATH" == /tmp/* ]]; then
    echo -e "${YELLOW}⚠ Temporary key file created: ${SERVICE_ACCOUNT_KEY_PATH}${NC}"
    echo "   Please save this file securely or delete it after verifying setup"
fi

echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}Summary:${NC}"
echo -e "  Site URL: ${GSC_SITE_URL}"
echo -e "  Service Account: ${SERVICE_ACCOUNT_EMAIL}"
echo -e "  Key Secret: ${SA_KEY_SECRET_NAME}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Update cloudbuild.yaml to mount GSC_SITE_URL and service account key"
echo "2. Update service.yaml to reference the secrets"
echo "3. Set GOOGLE_APPLICATION_CREDENTIALS environment variable in Cloud Run"
echo "4. Redeploy Cloud Run service"
echo ""

