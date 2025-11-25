#!/bin/bash

# Script to add Cloudinary credentials to Google Secret Manager
# Usage: ./scripts/add-cloudinary-secrets.sh [dev|staging|prod]

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get environment (default: dev)
ENV=${1:-dev}
PROJECT_ID="api-ai-blog-writer"
SECRET_NAME="blog-writer-env-${ENV}"

echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}Add Cloudinary Credentials to Google Secret Manager${NC}"
echo -e "${BLUE}Environment: ${ENV}${NC}"
echo -e "${BLUE}Secret: ${SECRET_NAME}${NC}"
echo -e "${BLUE}============================================================${NC}"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ Error: gcloud CLI is not installed${NC}"
    echo -e "${YELLOW}Please install gcloud CLI: https://cloud.google.com/sdk/docs/install${NC}"
    exit 1
fi

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo -e "${RED}❌ Error: jq is not installed${NC}"
    echo -e "${YELLOW}Please install jq: brew install jq (macOS) or apt-get install jq (Linux)${NC}"
    exit 1
fi

# Get current secret value
echo -e "${BLUE}📥 Fetching current secret...${NC}"
CURRENT_SECRET=$(gcloud secrets versions access latest --secret="$SECRET_NAME" --project="$PROJECT_ID" 2>/dev/null || echo "{}")

# Check if secret exists
if [ "$CURRENT_SECRET" == "{}" ] || [ -z "$CURRENT_SECRET" ]; then
    echo -e "${YELLOW}⚠️  Secret not found or empty. Creating new secret structure...${NC}"
    CURRENT_SECRET="{}"
fi

# Parse current secret as JSON
SECRET_JSON=$(echo "$CURRENT_SECRET" | jq .)

# Prompt for Cloudinary credentials
echo -e "\n${BLUE}Enter Cloudinary Credentials:${NC}"
echo -e "${YELLOW}(Leave empty to keep existing value or skip)${NC}\n"

# Cloud Name
CURRENT_CLOUD_NAME=$(echo "$SECRET_JSON" | jq -r '.CLOUDINARY_CLOUD_NAME // empty')
if [ -n "$CURRENT_CLOUD_NAME" ] && [ "$CURRENT_CLOUD_NAME" != "null" ]; then
    echo -e "${BLUE}Current Cloudinary Cloud Name: ${CURRENT_CLOUD_NAME}${NC}"
    read -p "Enter new Cloudinary Cloud Name (or press Enter to keep current): " CLOUDINARY_CLOUD_NAME
    if [ -z "$CLOUDINARY_CLOUD_NAME" ]; then
        CLOUDINARY_CLOUD_NAME="$CURRENT_CLOUD_NAME"
    fi
else
    read -p "Enter Cloudinary Cloud Name: " CLOUDINARY_CLOUD_NAME
fi

# API Key
CURRENT_API_KEY=$(echo "$SECRET_JSON" | jq -r '.CLOUDINARY_API_KEY // empty')
if [ -n "$CURRENT_API_KEY" ] && [ "$CURRENT_API_KEY" != "null" ]; then
    echo -e "${BLUE}Current Cloudinary API Key: ${CURRENT_API_KEY:0:10}...${NC}"
    read -p "Enter new Cloudinary API Key (or press Enter to keep current): " CLOUDINARY_API_KEY
    if [ -z "$CLOUDINARY_API_KEY" ]; then
        CLOUDINARY_API_KEY="$CURRENT_API_KEY"
    fi
else
    read -p "Enter Cloudinary API Key: " CLOUDINARY_API_KEY
fi

# API Secret
CURRENT_API_SECRET=$(echo "$SECRET_JSON" | jq -r '.CLOUDINARY_API_SECRET // empty')
if [ -n "$CURRENT_API_SECRET" ] && [ "$CURRENT_API_SECRET" != "null" ]; then
    echo -e "${BLUE}Current Cloudinary API Secret: ${CURRENT_API_SECRET:0:10}...${NC}"
    read -sp "Enter new Cloudinary API Secret (or press Enter to keep current): " CLOUDINARY_API_SECRET
    echo ""
    if [ -z "$CLOUDINARY_API_SECRET" ]; then
        CLOUDINARY_API_SECRET="$CURRENT_API_SECRET"
    fi
else
    read -sp "Enter Cloudinary API Secret: " CLOUDINARY_API_SECRET
    echo ""
fi

# Optional: Folder
CURRENT_FOLDER=$(echo "$SECRET_JSON" | jq -r '.CLOUDINARY_FOLDER // empty')
if [ -n "$CURRENT_FOLDER" ] && [ "$CURRENT_FOLDER" != "null" ]; then
    echo -e "${BLUE}Current Cloudinary Folder: ${CURRENT_FOLDER}${NC}"
    read -p "Enter new Cloudinary Folder (or press Enter to keep current, default: blog-content): " CLOUDINARY_FOLDER
    if [ -z "$CLOUDINARY_FOLDER" ]; then
        CLOUDINARY_FOLDER="$CURRENT_FOLDER"
    fi
else
    read -p "Enter Cloudinary Folder (or press Enter for default: blog-content): " CLOUDINARY_FOLDER
    if [ -z "$CLOUDINARY_FOLDER" ]; then
        CLOUDINARY_FOLDER="blog-content"
    fi
fi

# Validate required fields
if [ -z "$CLOUDINARY_CLOUD_NAME" ] || [ -z "$CLOUDINARY_API_KEY" ] || [ -z "$CLOUDINARY_API_SECRET" ]; then
    echo -e "${RED}❌ Error: Cloudinary Cloud Name, API Key, and API Secret are required${NC}"
    exit 1
fi

# Update secret JSON
echo -e "\n${BLUE}📝 Updating secret JSON...${NC}"
UPDATED_SECRET=$(echo "$SECRET_JSON" | jq \
    --arg cloud_name "$CLOUDINARY_CLOUD_NAME" \
    --arg api_key "$CLOUDINARY_API_KEY" \
    --arg api_secret "$CLOUDINARY_API_SECRET" \
    --arg folder "$CLOUDINARY_FOLDER" \
    '. + {
        CLOUDINARY_CLOUD_NAME: $cloud_name,
        CLOUDINARY_API_KEY: $api_key,
        CLOUDINARY_API_SECRET: $api_secret,
        CLOUDINARY_FOLDER: $folder
    }')

# Create temporary file for secret
TEMP_SECRET_FILE=$(mktemp)
echo "$UPDATED_SECRET" > "$TEMP_SECRET_FILE"

# Update secret in Google Secret Manager
echo -e "${BLUE}📤 Uploading updated secret to Google Secret Manager...${NC}"
gcloud secrets versions add "$SECRET_NAME" \
    --data-file="$TEMP_SECRET_FILE" \
    --project="$PROJECT_ID"

# Clean up temp file
rm -f "$TEMP_SECRET_FILE"

echo -e "\n${GREEN}✅ Cloudinary credentials added successfully!${NC}"
echo -e "${BLUE}Secret: ${SECRET_NAME}${NC}"
echo -e "${BLUE}Environment: ${ENV}${NC}"
echo -e "\n${YELLOW}Note:${NC} The secret will be automatically loaded on next deployment."
echo -e "${YELLOW}To apply immediately, restart the Cloud Run service:${NC}"
echo -e "${BLUE}gcloud run services update blog-writer-api-${ENV} --region=europe-west9 --project=${PROJECT_ID}${NC}"

