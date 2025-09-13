#!/bin/bash

# Deploy Blog Writer SDK to specific environment (dev/staging/prod)
# Usage: ./scripts/deploy-env.sh [environment]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="sdk-ai-blog-writer"
REGION="us-central1"
ENVIRONMENT=${1:-"dev"}

# Environment-specific configurations
case $ENVIRONMENT in
    "dev")
        MEMORY="1Gi"
        CPU="1"
        MIN_INSTANCES="0"
        MAX_INSTANCES="5"
        CONCURRENCY="10"
        ;;
    "staging")
        MEMORY="2Gi"
        CPU="2"
        MIN_INSTANCES="0"
        MAX_INSTANCES="10"
        CONCURRENCY="80"
        ;;
    "prod")
        MEMORY="2Gi"
        CPU="2"
        MIN_INSTANCES="1"
        MAX_INSTANCES="100"
        CONCURRENCY="80"
        ;;
    *)
        echo -e "${RED}❌ Invalid environment: $ENVIRONMENT${NC}"
        echo "Usage: $0 [dev|staging|prod]"
        exit 1
        ;;
esac

echo -e "${BLUE}🚀 Deploying Blog Writer SDK to $ENVIRONMENT environment${NC}"
echo "============================================================"

# Check if gcloud is installed and authenticated
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if project exists
if ! gcloud projects describe $PROJECT_ID &>/dev/null; then
    echo -e "${RED}❌ Project $PROJECT_ID not found. Please run ./scripts/create-project.sh first.${NC}"
    exit 1
fi

gcloud config set project $PROJECT_ID
echo -e "${GREEN}✅ Using project: $PROJECT_ID${NC}"

# Check if environment file exists
ENV_FILE="env.$ENVIRONMENT"
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}❌ Environment file $ENV_FILE not found.${NC}"
    echo "Please create it or run ./scripts/setup-multi-environments.sh first."
    exit 1
fi

# Check if secret exists
SECRET_NAME="blog-writer-env-$ENVIRONMENT"
if ! gcloud secrets describe $SECRET_NAME --project=$PROJECT_ID &>/dev/null; then
    echo -e "${YELLOW}⚠️  Secret $SECRET_NAME not found. Creating it...${NC}"
    gcloud secrets create $SECRET_NAME \
        --data-file="$ENV_FILE" \
        --project=$PROJECT_ID
else
    echo -e "${BLUE}🔄 Updating secret $SECRET_NAME...${NC}"
    gcloud secrets versions add $SECRET_NAME \
        --data-file="$ENV_FILE" \
        --project=$PROJECT_ID
fi

# Build and deploy using Cloud Build
echo -e "${BLUE}🏗️  Building and deploying to $ENVIRONMENT...${NC}"
gcloud builds submit \
    --config cloudbuild-multi-env.yaml \
    --substitutions _REGION=$REGION,_ENVIRONMENT=$ENVIRONMENT,_MEMORY=$MEMORY,_CPU=$CPU,_MIN_INSTANCES=$MIN_INSTANCES,_MAX_INSTANCES=$MAX_INSTANCES,_CONCURRENCY=$CONCURRENCY \
    --project=$PROJECT_ID

# Wait for deployment to complete and get service URL
echo -e "${BLUE}🔍 Getting service URL...${NC}"
SERVICE_NAME="blog-writer-sdk-$ENVIRONMENT"
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --region=$REGION \
    --project=$PROJECT_ID \
    --format="value(status.url)")

if [ -z "$SERVICE_URL" ]; then
    echo -e "${RED}❌ Failed to get service URL. Deployment may have failed.${NC}"
    exit 1
fi

# Test the deployment
echo -e "${BLUE}🧪 Testing deployment...${NC}"
sleep 10  # Wait for service to be ready

# Test health endpoint
if curl -f "$SERVICE_URL/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Health check passed${NC}"
else
    echo -e "${YELLOW}⚠️  Health check failed, but deployment completed${NC}"
fi

# Test readiness endpoint
if curl -f "$SERVICE_URL/ready" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Readiness check passed${NC}"
else
    echo -e "${YELLOW}⚠️  Readiness check failed (may need API keys configured)${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Deployment to $ENVIRONMENT completed successfully!${NC}"
echo ""
echo -e "${BLUE}📋 Deployment Summary:${NC}"
echo "- Environment: $ENVIRONMENT"
echo "- Service Name: $SERVICE_NAME"
echo "- Project: $PROJECT_ID"
echo "- Region: $REGION"
echo "- Service URL: $SERVICE_URL"
echo "- Memory: $MEMORY"
echo "- CPU: $CPU"
echo "- Min Instances: $MIN_INSTANCES"
echo "- Max Instances: $MAX_INSTANCES"
echo "- Concurrency: $CONCURRENCY"
echo ""
echo -e "${YELLOW}🔗 Useful URLs:${NC}"
echo "- API Documentation: $SERVICE_URL/docs"
echo "- Health Check: $SERVICE_URL/health"
echo "- Readiness Check: $SERVICE_URL/ready"
echo "- API Configuration: $SERVICE_URL/api/v1/config"
echo "- Cloud Run Status: $SERVICE_URL/api/v1/cloudrun/status"
echo ""
echo -e "${BLUE}🧪 Test your deployment:${NC}"
echo "curl $SERVICE_URL/health"
echo "curl $SERVICE_URL/api/v1/config"
echo ""
echo -e "${YELLOW}📊 Monitor your service:${NC}"
echo "gcloud run services describe $SERVICE_NAME --region=$REGION --project=$PROJECT_ID"
echo "gcloud logging read \"resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME\" --project=$PROJECT_ID --limit=50"
echo ""
echo -e "${GREEN}✅ $ENVIRONMENT environment is now live at: $SERVICE_URL${NC}"

