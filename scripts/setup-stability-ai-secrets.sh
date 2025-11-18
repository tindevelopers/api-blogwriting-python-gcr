#!/bin/bash

# Setup Stability AI Secrets for Cloud Run
# This script creates individual secrets in Google Secret Manager for Stability AI
# Required for image generation in blog posts

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-"api-ai-blog-writer"}
REGION=${REGION:-"europe-west9"}
SERVICE_NAME=${SERVICE_NAME:-"blog-writer-api-dev"}

echo -e "${BLUE}🎨 Setting up Stability AI Secrets for Cloud Run${NC}"
echo "=================================================="

# Check if gcloud is installed and authenticated
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if project ID is set
if [ -z "$PROJECT_ID" ]; then
    echo -e "${YELLOW}⚠️  PROJECT_ID not set. Please set it:${NC}"
    echo "export GOOGLE_CLOUD_PROJECT=your-project-id"
    echo "or run: gcloud config set project your-project-id"
    exit 1
fi

echo -e "${GREEN}✅ Using project: $PROJECT_ID${NC}"
echo -e "${GREEN}✅ Using region: $REGION${NC}"
echo -e "${GREEN}✅ Service name: $SERVICE_NAME${NC}"

# Enable Secret Manager API
echo -e "${BLUE}🔧 Enabling Secret Manager API...${NC}"
gcloud services enable secretmanager.googleapis.com --project=$PROJECT_ID

# Function to create or update a secret
create_or_update_secret() {
    local SECRET_NAME=$1
    local SECRET_VALUE=$2
    local DESCRIPTION=$3
    
    echo -e "${BLUE}🔒 Creating/updating secret: $SECRET_NAME${NC}"
    
    # Check if secret exists
    if gcloud secrets describe $SECRET_NAME --project=$PROJECT_ID &>/dev/null; then
        echo -e "${YELLOW}   Secret exists, updating...${NC}"
        echo -n "$SECRET_VALUE" | gcloud secrets versions add $SECRET_NAME \
            --data-file=- \
            --project=$PROJECT_ID
    else
        echo -e "${GREEN}   Creating new secret...${NC}"
        echo -n "$SECRET_VALUE" | gcloud secrets create $SECRET_NAME \
            --data-file=- \
            --replication-policy="automatic" \
            --project=$PROJECT_ID
    fi
    
    # Add description if provided
    if [ ! -z "$DESCRIPTION" ]; then
        gcloud secrets update $SECRET_NAME \
            --update-labels="description=$DESCRIPTION" \
            --project=$PROJECT_ID 2>/dev/null || true
    fi
    
    echo -e "${GREEN}✅ Secret '$SECRET_NAME' ready${NC}"
}

# Prompt for Stability AI API Key
echo ""
echo -e "${YELLOW}📝 Stability AI API Key Setup${NC}"
echo "Get your API key from: https://platform.stability.ai/account/keys"
echo ""
read -sp "Enter Stability AI API Key (or press Enter to skip): " STABILITY_KEY
echo ""

if [ ! -z "$STABILITY_KEY" ]; then
    create_or_update_secret "STABILITY_AI_API_KEY" "$STABILITY_KEY" "Stability AI API key for image generation"
else
    echo -e "${YELLOW}⚠️  Skipping Stability AI API key${NC}"
    echo -e "${RED}❌ Image generation will not work without this key${NC}"
    exit 1
fi

# Grant Cloud Run service account access to secrets
echo ""
echo -e "${BLUE}🔐 Granting Cloud Run service account access to secrets...${NC}"

# Get the Cloud Run service account
SERVICE_ACCOUNT=$(gcloud run services describe $SERVICE_NAME \
    --region=$REGION \
    --project=$PROJECT_ID \
    --format="value(spec.template.spec.serviceAccountName)" 2>/dev/null || echo "")

if [ -z "$SERVICE_ACCOUNT" ]; then
    # Try default compute service account
    SERVICE_ACCOUNT="${PROJECT_ID}@${PROJECT_ID}.iam.gserviceaccount.com"
    echo -e "${YELLOW}⚠️  Could not find service account, using default: $SERVICE_ACCOUNT${NC}"
fi

echo -e "${BLUE}   Using service account: $SERVICE_ACCOUNT${NC}"

# Grant access to Stability AI secret
if [ ! -z "$STABILITY_KEY" ]; then
    echo -e "${BLUE}   Granting access to STABILITY_AI_API_KEY...${NC}"
    gcloud secrets add-iam-policy-binding STABILITY_AI_API_KEY \
        --member="serviceAccount:$SERVICE_ACCOUNT" \
        --role="roles/secretmanager.secretAccessor" \
        --project=$PROJECT_ID || echo -e "${YELLOW}   Warning: Could not grant access (may already exist)${NC}"
fi

# Update Cloud Run service to use secrets
echo ""
echo -e "${BLUE}🚀 Updating Cloud Run service to use secrets...${NC}"

if [ ! -z "$STABILITY_KEY" ]; then
    echo -e "${BLUE}   Updating service with STABILITY_AI_API_KEY secret...${NC}"
    gcloud run services update $SERVICE_NAME \
        --region=$REGION \
        --project=$PROJECT_ID \
        --update-secrets=STABILITY_AI_API_KEY=STABILITY_AI_API_KEY:latest || {
        echo -e "${YELLOW}⚠️  Could not update service automatically. You may need to update manually.${NC}"
        echo -e "${YELLOW}   Run this command manually:${NC}"
        echo "   gcloud run services update $SERVICE_NAME \\"
        echo "     --region=$REGION \\"
        echo "     --project=$PROJECT_ID \\"
        echo "     --update-secrets=STABILITY_AI_API_KEY=STABILITY_AI_API_KEY:latest"
    }
else
    echo -e "${YELLOW}⚠️  No secrets to update (key was skipped)${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Stability AI Secrets Setup Complete!${NC}"
echo ""
echo -e "${BLUE}📋 Summary:${NC}"
echo "- Project ID: $PROJECT_ID"
echo "- Region: $REGION"
echo "- Service: $SERVICE_NAME"
if [ ! -z "$STABILITY_KEY" ]; then
    echo -e "${GREEN}✅ STABILITY_AI_API_KEY: Configured${NC}"
else
    echo -e "${YELLOW}⚠️  STABILITY_AI_API_KEY: Not configured${NC}"
fi
echo ""
echo -e "${YELLOW}📝 Next Steps:${NC}"
echo "1. Verify secrets are accessible:"
echo "   gcloud secrets list --project=$PROJECT_ID"
echo ""
echo "2. Test image generation endpoint:"
echo "   curl -X POST https://$SERVICE_NAME-$PROJECT_ID.$REGION.run.app/api/v1/images/generate \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"prompt\":\"A beautiful sunset\",\"provider\":\"stability_ai\"}'"
echo ""
echo "3. Test blog generation with images:"
echo "   curl -X POST https://$SERVICE_NAME-$PROJECT_ID.$REGION.run.app/api/v1/blog/generate-enhanced \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"topic\":\"Best Products 2025\",\"keywords\":[\"products\"],\"use_google_search\":true}'"
echo ""
echo "4. Check service logs if issues occur:"
echo "   gcloud run services logs read $SERVICE_NAME --region=$REGION --project=$PROJECT_ID"
echo ""
echo -e "${YELLOW}⚠️  Important:${NC}"
echo "- Image generation requires STABILITY_AI_API_KEY to be configured"
echo "- Images are automatically generated for topics containing: best, top, review, compare, guide"
echo "- Generated images appear in the 'generated_images' field of the response"
echo "- Images are automatically inserted into markdown content"

