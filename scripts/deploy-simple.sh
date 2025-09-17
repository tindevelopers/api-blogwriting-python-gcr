#!/bin/bash

# Simple deployment script for Blog Writer SDK
# Usage: ./scripts/deploy-simple.sh [environment]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="api-ai-blog-writer"
ENVIRONMENT=${1:-"dev"}

# Environment-specific region configuration
case $ENVIRONMENT in
    "dev")
        REGION="europe-west9"  # Paris for European development
        ;;
    "staging"|"prod")
        REGION="us-east1"      # US-East-1 for global performance
        ;;
    *)
        echo -e "${RED}❌ Invalid environment: $ENVIRONMENT${NC}"
        echo "Usage: $0 [dev|staging|prod]"
        exit 1
        ;;
esac

# Generate a timestamp-based tag
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
IMAGE_TAG="$ENVIRONMENT-$TIMESTAMP"

# Environment-specific configurations
case $ENVIRONMENT in
    "dev")
        MEMORY="1Gi"
        CPU="1"
        MIN_INSTANCES="0"
        MAX_INSTANCES="5"
        CONCURRENCY="10"
        SERVICE_SUFFIX="-dev"
        ;;
    "staging")
        MEMORY="2Gi"
        CPU="2"
        MIN_INSTANCES="0"
        MAX_INSTANCES="10"
        CONCURRENCY="80"
        SERVICE_SUFFIX="-staging"
        ;;
    "prod")
        MEMORY="2Gi"
        CPU="2"
        MIN_INSTANCES="1"
        MAX_INSTANCES="100"
        CONCURRENCY="80"
        SERVICE_SUFFIX=""  # No suffix for production
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

# Update secret
SECRET_NAME="blog-writer-env-$ENVIRONMENT"
echo -e "${BLUE}🔄 Updating secret $SECRET_NAME...${NC}"
gcloud secrets versions add $SECRET_NAME \
    --data-file="$ENV_FILE" \
    --project=$PROJECT_ID

# Build image locally and push to Artifact Registry
IMAGE_NAME="$REGION-docker.pkg.dev/$PROJECT_ID/blog-writer-sdk/blog-writer-sdk:$IMAGE_TAG"
echo -e "${BLUE}🏗️  Building Docker image: $IMAGE_NAME${NC}"

docker build --platform linux/amd64 -t "$IMAGE_NAME" .

echo -e "${BLUE}📤 Pushing image to Artifact Registry...${NC}"
docker push "$IMAGE_NAME"

# Deploy to Cloud Run
echo -e "${BLUE}🚀 Deploying to Cloud Run...${NC}"
SERVICE_NAME="api-ai-blog-writer$SERVICE_SUFFIX"

gcloud run deploy $SERVICE_NAME \
    --image="$IMAGE_NAME" \
    --region="$REGION" \
    --platform="managed" \
    --allow-unauthenticated \
    --port="8000" \
    --memory="$MEMORY" \
    --cpu="$CPU" \
    --min-instances="$MIN_INSTANCES" \
    --max-instances="$MAX_INSTANCES" \
    --concurrency="$CONCURRENCY" \
    --timeout="900" \
    --service-account="blog-writer-$ENVIRONMENT@$PROJECT_ID.iam.gserviceaccount.com" \
    --set-env-vars="PYTHONUNBUFFERED=1,ENVIRONMENT=$ENVIRONMENT" \
    --set-secrets="/secrets/env=blog-writer-env-$ENVIRONMENT:latest" \
    --project="$PROJECT_ID"

# Get service URL
echo -e "${BLUE}🔍 Getting service URL...${NC}"
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

echo ""
echo -e "${GREEN}🎉 Deployment to $ENVIRONMENT completed successfully!${NC}"
echo ""
echo -e "${BLUE}📋 Deployment Summary:${NC}"
echo "- Environment: $ENVIRONMENT"
echo "- Service Name: $SERVICE_NAME"
echo "- Project: $PROJECT_ID"
echo "- Region: $REGION"
echo "- Service URL: $SERVICE_URL"
echo "- Image: $IMAGE_NAME"
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
echo ""
echo -e "${GREEN}✅ $ENVIRONMENT environment is now live at: $SERVICE_URL${NC}"




