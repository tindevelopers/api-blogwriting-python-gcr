#!/bin/bash

# Deploy Blog Writer SDK to Google Cloud Run
# This script builds and deploys the application using Cloud Build

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-""}
REGION=${REGION:-"us-central1"}
SERVICE_NAME="blog-writer-sdk"

echo -e "${BLUE}🚀 Deploying Blog Writer SDK to Google Cloud Run${NC}"
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

# Check if cloudbuild.yaml exists
if [ ! -f "cloudbuild.yaml" ]; then
    echo -e "${RED}❌ cloudbuild.yaml not found. Please make sure you're in the project root.${NC}"
    exit 1
fi

# Check if secrets are set up
echo -e "${BLUE}🔍 Checking if secrets are configured...${NC}"
if ! gcloud secrets describe blog-writer-env --project=$PROJECT_ID &>/dev/null; then
    echo -e "${YELLOW}⚠️  Secrets not found. Running setup-secrets.sh first...${NC}"
    if [ -f "scripts/setup-secrets.sh" ]; then
        ./scripts/setup-secrets.sh
    else
        echo -e "${RED}❌ setup-secrets.sh not found. Please run it manually first.${NC}"
        exit 1
    fi
fi

# Build and deploy using Cloud Build
echo -e "${BLUE}🏗️  Starting Cloud Build deployment...${NC}"
gcloud builds submit \
    --config cloudbuild.yaml \
    --substitutions _REGION=$REGION \
    --project=$PROJECT_ID

# Wait for deployment to complete and get service URL
echo -e "${BLUE}🔍 Getting service URL...${NC}"
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --region=$REGION \
    --project=$PROJECT_ID \
    --format="value(status.url)")

if [ -z "$SERVICE_URL" ]; then
    echo -e "${RED}❌ Failed to get service URL. Deployment may have failed.${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo ""
echo -e "${BLUE}📋 Deployment Summary:${NC}"
echo "- Service Name: $SERVICE_NAME"
echo "- Project: $PROJECT_ID"
echo "- Region: $REGION"
echo "- Service URL: $SERVICE_URL"
echo ""
echo -e "${YELLOW}🔗 Useful URLs:${NC}"
echo "- API Documentation: $SERVICE_URL/docs"
echo "- Health Check: $SERVICE_URL/health"
echo "- API Configuration: $SERVICE_URL/api/v1/config"
echo ""
echo -e "${BLUE}🧪 Test your deployment:${NC}"
echo "curl $SERVICE_URL/health"
echo ""
echo -e "${YELLOW}📊 Monitor your service:${NC}"
echo "gcloud run services describe $SERVICE_NAME --region=$REGION --project=$PROJECT_ID"
echo "gcloud logging read \"resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME\" --project=$PROJECT_ID --limit=50"
echo ""
echo -e "${GREEN}✅ Your Blog Writer SDK is now live at: $SERVICE_URL${NC}"

