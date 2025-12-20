#!/bin/bash
# Deploy LiteLLM Proxy to Cloud Run
# This script deploys the LiteLLM proxy as a standalone Cloud Run service

set -e

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-api-ai-blog-writer}"
REGION="${GCP_REGION:-europe-west9}"
SERVICE_NAME="litellm-proxy"
IMAGE="ghcr.io/berriai/litellm:main-latest"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== LiteLLM Proxy Deployment ===${NC}"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Service: $SERVICE_NAME"
echo ""

# Check if gcloud is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n 1 > /dev/null 2>&1; then
    echo -e "${RED}Error: Not authenticated with gcloud. Run 'gcloud auth login' first.${NC}"
    exit 1
fi

# Set the project
echo -e "${YELLOW}Setting project to $PROJECT_ID...${NC}"
gcloud config set project "$PROJECT_ID"

# Check if required secrets exist in Secret Manager
echo -e "${YELLOW}Checking required secrets...${NC}"
REQUIRED_SECRETS=("openai-api-key" "anthropic-api-key" "litellm-master-key")

for secret in "${REQUIRED_SECRETS[@]}"; do
    if ! gcloud secrets describe "$secret" --project="$PROJECT_ID" > /dev/null 2>&1; then
        echo -e "${RED}Error: Secret '$secret' not found in Secret Manager.${NC}"
        echo "Create it with: gcloud secrets create $secret --replication-policy=automatic"
        echo "Add value with: echo -n 'your-value' | gcloud secrets versions add $secret --data-file=-"
        exit 1
    fi
    echo -e "  ${GREEN}✓${NC} $secret exists"
done

# Optional: Check for Redis secrets
if gcloud secrets describe "redis-host" --project="$PROJECT_ID" > /dev/null 2>&1; then
    REDIS_CONFIGURED=true
    echo -e "  ${GREEN}✓${NC} Redis secrets found - caching will be enabled"
else
    REDIS_CONFIGURED=false
    echo -e "  ${YELLOW}!${NC} Redis secrets not found - caching will use in-memory fallback"
fi

# Build the deployment command
echo ""
echo -e "${YELLOW}Deploying LiteLLM to Cloud Run...${NC}"

DEPLOY_CMD="gcloud run deploy $SERVICE_NAME \
    --image $IMAGE \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --set-secrets OPENAI_API_KEY=openai-api-key:latest \
    --set-secrets ANTHROPIC_API_KEY=anthropic-api-key:latest \
    --set-secrets LITELLM_MASTER_KEY=litellm-master-key:latest \
    --memory 1Gi \
    --cpu 1 \
    --max-instances 10 \
    --min-instances 0 \
    --timeout 300 \
    --concurrency 80 \
    --set-env-vars LITELLM_MODE=production"

# Add Redis secrets if configured
if [ "$REDIS_CONFIGURED" = true ]; then
    DEPLOY_CMD="$DEPLOY_CMD \
    --set-secrets REDIS_HOST=redis-host:latest \
    --set-secrets REDIS_PASSWORD=redis-password:latest \
    --set-env-vars REDIS_PORT=6379"
fi

# Execute deployment
eval "$DEPLOY_CMD"

# Get the service URL
echo ""
echo -e "${YELLOW}Getting service URL...${NC}"
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --region="$REGION" --format="value(status.url)")

echo ""
echo -e "${GREEN}=== Deployment Complete ===${NC}"
echo -e "Service URL: ${GREEN}$SERVICE_URL${NC}"
echo ""
echo "Test the deployment with:"
echo "  curl $SERVICE_URL/health"
echo ""
echo "Test a completion with:"
echo "  curl $SERVICE_URL/v1/chat/completions \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -H 'Authorization: Bearer YOUR_LITELLM_MASTER_KEY' \\"
echo "    -d '{\"model\": \"gpt-4o-mini\", \"messages\": [{\"role\": \"user\", \"content\": \"Hello!\"}]}'"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Add LITELLM_PROXY_URL=$SERVICE_URL to your backend environment"
echo "2. Add LITELLM_API_KEY=your-master-key to your backend environment"
echo "3. Update the Python backend to use the AI Gateway"
