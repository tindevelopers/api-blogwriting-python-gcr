#!/bin/bash

# Setup Google Cloud Secrets for Blog Writer SDK
# This script creates secrets in Google Secret Manager for Cloud Run deployment

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
SECRET_NAME="blog-writer-env"
SERVICE_ACCOUNT_NAME="blog-writer-service-account"

echo -e "${BLUE}🔐 Setting up Google Cloud Secrets for Blog Writer SDK${NC}"
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

# Enable required APIs
echo -e "${BLUE}🔧 Enabling required Google Cloud APIs...${NC}"
gcloud services enable cloudbuild.googleapis.com \
    run.googleapis.com \
    secretmanager.googleapis.com \
    containerregistry.googleapis.com \
    --project=$PROJECT_ID

# Create service account for Cloud Run
echo -e "${BLUE}👤 Creating service account...${NC}"
gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
    --display-name="Blog Writer SDK Service Account" \
    --description="Service account for Blog Writer SDK Cloud Run service" \
    --project=$PROJECT_ID || echo "Service account may already exist"

# Grant necessary permissions to service account
echo -e "${BLUE}🔑 Granting permissions to service account...${NC}"
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/cloudsql.client"

# Check if env.cloudrun file exists
if [ ! -f "env.cloudrun" ]; then
    echo -e "${RED}❌ env.cloudrun file not found. Please create it with your environment variables.${NC}"
    exit 1
fi

# Create the secret from env.cloudrun file
echo -e "${BLUE}🔒 Creating secret in Secret Manager...${NC}"
gcloud secrets create $SECRET_NAME \
    --data-file=env.cloudrun \
    --project=$PROJECT_ID || echo "Secret may already exist, updating..."

# If secret already exists, update it
gcloud secrets versions add $SECRET_NAME \
    --data-file=env.cloudrun \
    --project=$PROJECT_ID

echo -e "${GREEN}✅ Secret '$SECRET_NAME' created/updated successfully${NC}"

# Grant Cloud Run service account access to the secret
echo -e "${BLUE}🔐 Granting secret access to Cloud Run service account...${NC}"
gcloud secrets add-iam-policy-binding $SECRET_NAME \
    --member="serviceAccount:$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor" \
    --project=$PROJECT_ID

# Grant Cloud Build service account access to deploy to Cloud Run
echo -e "${BLUE}🏗️  Granting Cloud Build permissions...${NC}"
CLOUD_BUILD_SA=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")@cloudbuild.gserviceaccount.com

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$CLOUD_BUILD_SA" \
    --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$CLOUD_BUILD_SA" \
    --role="roles/iam.serviceAccountUser"

echo ""
echo -e "${GREEN}🎉 Setup completed successfully!${NC}"
echo ""
echo -e "${YELLOW}📝 Next steps:${NC}"
echo "1. Update env.cloudrun with your actual API keys and configuration"
echo "2. Run: ./scripts/deploy.sh to deploy to Cloud Run"
echo "3. Or set up GitHub Actions for automated deployment"
echo ""
echo -e "${BLUE}📋 Configuration Summary:${NC}"
echo "- Project ID: $PROJECT_ID"
echo "- Region: $REGION"
echo "- Secret Name: $SECRET_NAME"
echo "- Service Account: $SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com"
echo ""
echo -e "${YELLOW}⚠️  Important:${NC}"
echo "- Make sure to update env.cloudrun with your real API keys before deploying"
echo "- Keep your API keys secure and never commit them to version control"
echo "- Consider using different secrets for different environments (dev/staging/prod)"

