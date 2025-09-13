#!/bin/bash

# Create Google Cloud Project for SDK-AI-Blog Writer
# This script creates the project and enables all required APIs

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="sdk-ai-blog-writer"
PROJECT_NAME="SDK AI Blog Writer"
BILLING_ACCOUNT_ID=${BILLING_ACCOUNT_ID:-""}
REGION="us-central1"

echo -e "${BLUE}🚀 Creating Google Cloud Project: $PROJECT_NAME${NC}"
echo "============================================================"

# Check if gcloud is installed and authenticated
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI is not installed. Please install it first.${NC}"
    echo "Visit: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n 1 > /dev/null; then
    echo -e "${YELLOW}⚠️  Not authenticated with gcloud. Please run:${NC}"
    echo "gcloud auth login"
    exit 1
fi

echo -e "${GREEN}✅ gcloud CLI is installed and authenticated${NC}"

# Check if billing account is provided
if [ -z "$BILLING_ACCOUNT_ID" ]; then
    echo -e "${YELLOW}⚠️  BILLING_ACCOUNT_ID not set. You'll need to link billing manually.${NC}"
    echo "To find your billing account ID, run:"
    echo "gcloud billing accounts list"
    echo ""
    echo "Then set it: export BILLING_ACCOUNT_ID=your-billing-account-id"
    echo ""
    read -p "Continue without billing setup? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create the project
echo -e "${BLUE}📋 Creating project: $PROJECT_ID${NC}"
if gcloud projects create $PROJECT_ID --name="$PROJECT_NAME" 2>/dev/null; then
    echo -e "${GREEN}✅ Project created successfully${NC}"
else
    echo -e "${YELLOW}⚠️  Project may already exist, continuing...${NC}"
fi

# Set the project as default
echo -e "${BLUE}🔧 Setting project as default${NC}"
gcloud config set project $PROJECT_ID

# Link billing account if provided
if [ ! -z "$BILLING_ACCOUNT_ID" ]; then
    echo -e "${BLUE}💳 Linking billing account${NC}"
    gcloud billing projects link $PROJECT_ID --billing-account=$BILLING_ACCOUNT_ID
    echo -e "${GREEN}✅ Billing account linked${NC}"
fi

# Enable required APIs
echo -e "${BLUE}🔌 Enabling required Google Cloud APIs${NC}"
apis=(
    "cloudbuild.googleapis.com"
    "run.googleapis.com"
    "secretmanager.googleapis.com"
    "containerregistry.googleapis.com"
    "iam.googleapis.com"
    "cloudresourcemanager.googleapis.com"
    "logging.googleapis.com"
    "monitoring.googleapis.com"
    "artifactregistry.googleapis.com"
)

for api in "${apis[@]}"; do
    echo -e "  Enabling $api..."
    gcloud services enable $api --project=$PROJECT_ID
done

echo -e "${GREEN}✅ All APIs enabled successfully${NC}"

# Set default region
echo -e "${BLUE}🌍 Setting default region to $REGION${NC}"
gcloud config set run/region $REGION

# Create Artifact Registry repository for container images
echo -e "${BLUE}📦 Creating Artifact Registry repository${NC}"
gcloud artifacts repositories create blog-writer-sdk \
    --repository-format=docker \
    --location=$REGION \
    --description="Container images for Blog Writer SDK" \
    --project=$PROJECT_ID || echo "Repository may already exist"

# Configure Docker authentication for Artifact Registry
echo -e "${BLUE}🔐 Configuring Docker authentication${NC}"
gcloud auth configure-docker $REGION-docker.pkg.dev

echo ""
echo -e "${GREEN}🎉 Project setup completed successfully!${NC}"
echo ""
echo -e "${BLUE}📋 Project Information:${NC}"
echo "- Project ID: $PROJECT_ID"
echo "- Project Name: $PROJECT_NAME"
echo "- Default Region: $REGION"
echo "- Artifact Registry: $REGION-docker.pkg.dev/$PROJECT_ID/blog-writer-sdk"
echo ""
echo -e "${YELLOW}📝 Next Steps:${NC}"
echo "1. Run: ./scripts/setup-multi-environments.sh"
echo "2. Configure your environment variables in env files"
echo "3. Deploy to environments using: ./scripts/deploy-env.sh [environment]"
echo ""
echo -e "${BLUE}🔗 Useful Links:${NC}"
echo "- Cloud Console: https://console.cloud.google.com/home/dashboard?project=$PROJECT_ID"
echo "- Cloud Run: https://console.cloud.google.com/run?project=$PROJECT_ID"
echo "- Secret Manager: https://console.cloud.google.com/security/secret-manager?project=$PROJECT_ID"
echo ""
if [ -z "$BILLING_ACCOUNT_ID" ]; then
    echo -e "${YELLOW}⚠️  Don't forget to link a billing account:${NC}"
    echo "https://console.cloud.google.com/billing/linkedaccount?project=$PROJECT_ID"
fi

