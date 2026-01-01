#!/bin/bash

# Blog Writer API - Deployment Script
# This script deploys the backend to Google Cloud Run and seeds Firestore

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Blog Writer API - Deployment Script${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if required environment variables are set
if [ -z "$GOOGLE_APPLICATION_CREDENTIALS" ] && [ -z "$FIREBASE_SERVICE_ACCOUNT_KEY_BASE64" ]; then
    echo -e "${RED}ERROR: Firebase credentials not found!${NC}"
    echo ""
    echo "Please set one of the following:"
    echo "  - GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json"
    echo "  - FIREBASE_SERVICE_ACCOUNT_KEY_BASE64=<base64-encoded-json>"
    echo ""
    exit 1
fi

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-blog-writer-dev}"
REGION="${GCP_REGION:-europe-west9}"
SERVICE_NAME="${SERVICE_NAME:-blog-writer-api}"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo -e "${YELLOW}Configuration:${NC}"
echo "  Project ID: $PROJECT_ID"
echo "  Region: $REGION"
echo "  Service Name: $SERVICE_NAME"
echo "  Image: $IMAGE_NAME"
echo ""

# Prompt for deployment type
echo -e "${YELLOW}Select deployment option:${NC}"
echo "  1) Full deployment (build, push, deploy to GCR, seed Firestore)"
echo "  2) Seed Firestore only (no deployment)"
echo "  3) Build and push Docker image only"
echo "  4) Deploy to GCR only (using existing image)"
echo ""
read -p "Enter option (1-4): " DEPLOY_OPTION

case $DEPLOY_OPTION in
    1)
        echo -e "${GREEN}==> Full deployment selected${NC}"
        DEPLOY_FULL=true
        DEPLOY_SEED=true
        ;;
    2)
        echo -e "${GREEN}==> Seed Firestore only${NC}"
        DEPLOY_FULL=false
        DEPLOY_SEED=true
        ;;
    3)
        echo -e "${GREEN}==> Build and push image only${NC}"
        DEPLOY_FULL=false
        DEPLOY_SEED=false
        BUILD_ONLY=true
        ;;
    4)
        echo -e "${GREEN}==> Deploy to GCR only${NC}"
        DEPLOY_FULL=false
        DEPLOY_SEED=false
        DEPLOY_ONLY=true
        ;;
    *)
        echo -e "${RED}Invalid option${NC}"
        exit 1
        ;;
esac

echo ""

# Step 1: Build Docker image (if needed)
if [ "$DEPLOY_FULL" = true ] || [ "$BUILD_ONLY" = true ]; then
    echo -e "${GREEN}Step 1: Building Docker image...${NC}"
    docker build -t $SERVICE_NAME .
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}ERROR: Docker build failed${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Docker image built successfully${NC}"
    echo ""
    
    # Step 2: Tag image
    echo -e "${GREEN}Step 2: Tagging image for GCR...${NC}"
    docker tag $SERVICE_NAME $IMAGE_NAME
    
    echo -e "${GREEN}✓ Image tagged${NC}"
    echo ""
    
    # Step 3: Push to GCR
    echo -e "${GREEN}Step 3: Pushing image to Google Container Registry...${NC}"
    docker push $IMAGE_NAME
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}ERROR: Docker push failed${NC}"
        echo ""
        echo "Make sure you're authenticated with gcloud:"
        echo "  gcloud auth configure-docker"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Image pushed to GCR${NC}"
    echo ""
fi

# Step 4: Deploy to Cloud Run (if needed)
if [ "$DEPLOY_FULL" = true ] || [ "$DEPLOY_ONLY" = true ]; then
    echo -e "${GREEN}Step 4: Deploying to Google Cloud Run...${NC}"
    
    # Check if service exists
    SERVICE_EXISTS=$(gcloud run services list --platform managed --region $REGION --format="value(metadata.name)" --filter="metadata.name=$SERVICE_NAME" 2>/dev/null)
    
    if [ -z "$SERVICE_EXISTS" ]; then
        echo "Creating new Cloud Run service..."
        CREATE_SERVICE=true
    else
        echo "Updating existing Cloud Run service..."
        CREATE_SERVICE=false
    fi
    
    # Deploy command
    gcloud run deploy $SERVICE_NAME \
        --image $IMAGE_NAME \
        --platform managed \
        --region $REGION \
        --allow-unauthenticated \
        --memory 2Gi \
        --cpu 2 \
        --timeout 900 \
        --concurrency 80 \
        --min-instances 0 \
        --max-instances 10 \
        --set-env-vars "ENVIRONMENT=production" \
        --set-env-vars "LOG_LEVEL=INFO"
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}ERROR: Cloud Run deployment failed${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Deployed to Cloud Run${NC}"
    echo ""
    
    # Get service URL
    SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format="value(status.url)")
    echo -e "${GREEN}Service URL: $SERVICE_URL${NC}"
    echo ""
fi

# Step 5: Seed Firestore (if needed)
if [ "$DEPLOY_SEED" = true ]; then
    echo -e "${GREEN}Step 5: Seeding Firestore with default templates...${NC}"
    
    # Check if script exists
    if [ ! -f "scripts/seed_default_prompts_firestore.py" ]; then
        echo -e "${RED}ERROR: Seed script not found at scripts/seed_default_prompts_firestore.py${NC}"
        exit 1
    fi
    
    # Run seed script
    python scripts/seed_default_prompts_firestore.py
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}ERROR: Firestore seeding failed${NC}"
        echo ""
        echo "Make sure Firebase credentials are set correctly:"
        echo "  - GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json"
        echo "  - OR FIREBASE_SERVICE_ACCOUNT_KEY_BASE64=<base64>"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Firestore seeded successfully${NC}"
    echo ""
fi

# Summary
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Summary${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

if [ "$DEPLOY_FULL" = true ]; then
    echo -e "${GREEN}✓ Docker image built and pushed${NC}"
    echo -e "${GREEN}✓ Service deployed to Cloud Run${NC}"
    echo -e "${GREEN}✓ Firestore seeded with default templates${NC}"
    echo ""
    echo -e "${YELLOW}Service URL:${NC} $SERVICE_URL"
    echo -e "${YELLOW}API Docs:${NC} $SERVICE_URL/docs"
elif [ "$BUILD_ONLY" = true ]; then
    echo -e "${GREEN}✓ Docker image built and pushed${NC}"
    echo ""
    echo "Image: $IMAGE_NAME"
elif [ "$DEPLOY_ONLY" = true ]; then
    echo -e "${GREEN}✓ Service deployed to Cloud Run${NC}"
    echo ""
    echo -e "${YELLOW}Service URL:${NC} $SERVICE_URL"
    echo -e "${YELLOW}API Docs:${NC} $SERVICE_URL/docs"
elif [ "$DEPLOY_SEED" = true ]; then
    echo -e "${GREEN}✓ Firestore seeded with default templates${NC}"
fi

echo ""
echo -e "${GREEN}Next steps:${NC}"
echo "  1. Test API endpoints: curl $SERVICE_URL/health"
echo "  2. View API docs: $SERVICE_URL/docs"
echo "  3. Test prompt management: curl $SERVICE_URL/api/v1/prompts/styles"
echo ""

echo -e "${GREEN}Deployment complete! 🎉${NC}"
