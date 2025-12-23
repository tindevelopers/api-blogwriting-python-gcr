#!/bin/bash

# Check Vercel AI Gateway Connection Status
# This script verifies if requests are going through Vercel AI Gateway

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=================================${NC}"
echo -e "${BLUE}Vercel AI Gateway Connection Check${NC}"
echo -e "${BLUE}=================================${NC}\n"

# Configuration
BACKEND_URL="https://blog-writer-api-dev-613248238610.europe-west9.run.app"
LITELLM_URL="${LITELLM_PROXY_URL:-https://litellm-proxy-613248238610.europe-west9.run.app}"
PROJECT_ID="api-ai-blog-writer"

# Step 1: Check Backend Configuration
echo -e "${YELLOW}Step 1: Checking Backend Configuration${NC}"
echo "----------------------------------------"

echo "Checking if backend has LiteLLM configured..."
BACKEND_ENV=$(gcloud run services describe blog-writer-api-dev \
  --region=europe-west9 \
  --project=$PROJECT_ID \
  --format="value(spec.template.spec.containers[0].env)" 2>&1)

if echo "$BACKEND_ENV" | grep -q "LITELLM_PROXY_URL"; then
    LITELLM_PROXY=$(echo "$BACKEND_ENV" | grep "LITELLM_PROXY_URL" | cut -d'=' -f2 | tr -d '\n')
    echo -e "${GREEN}✓ Backend has LITELLM_PROXY_URL: $LITELLM_PROXY${NC}"
else
    echo -e "${RED}✗ Backend does NOT have LITELLM_PROXY_URL set${NC}"
    echo -e "${YELLOW}  → Backend is using DIRECT API connections (OpenAI/Anthropic)${NC}"
fi

if echo "$BACKEND_ENV" | grep -q "LITELLM_API_KEY"; then
    echo -e "${GREEN}✓ Backend has LITELLM_API_KEY configured${NC}"
else
    echo -e "${RED}✗ Backend does NOT have LITELLM_API_KEY set${NC}"
fi

# Step 2: Check if LiteLLM Service Exists
echo -e "\n${YELLOW}Step 2: Checking LiteLLM Proxy Service${NC}"
echo "----------------------------------------"

LITELLM_EXISTS=$(gcloud run services list \
  --region=europe-west9 \
  --project=$PROJECT_ID \
  --format="value(name)" 2>&1 | grep -c "litellm-proxy" || true)

if [ "$LITELLM_EXISTS" -gt 0 ]; then
    echo -e "${GREEN}✓ LiteLLM proxy service exists${NC}"
    
    # Check LiteLLM environment
    echo "Checking LiteLLM configuration..."
    LITELLM_ENV=$(gcloud run services describe litellm-proxy \
      --region=europe-west9 \
      --project=$PROJECT_ID \
      --format="value(spec.template.spec.containers[0].env)" 2>&1)
    
    if echo "$LITELLM_ENV" | grep -q "VERCEL_AI_GATEWAY_URL"; then
        VERCEL_URL=$(echo "$LITELLM_ENV" | grep "VERCEL_AI_GATEWAY_URL" | cut -d'=' -f2 | tr -d '\n')
        echo -e "${GREEN}✓ LiteLLM is configured to use Vercel AI Gateway${NC}"
        echo -e "${GREEN}  URL: $VERCEL_URL${NC}"
        HAS_VERCEL=true
    else
        echo -e "${YELLOW}✗ LiteLLM is NOT configured for Vercel AI Gateway${NC}"
        echo -e "${YELLOW}  → LiteLLM is using DIRECT API connections${NC}"
        HAS_VERCEL=false
    fi
    
    if echo "$LITELLM_ENV" | grep -q "VERCEL_AI_GATEWAY_KEY"; then
        echo -e "${GREEN}✓ LiteLLM has VERCEL_AI_GATEWAY_KEY${NC}"
    else
        if [ "$HAS_VERCEL" = true ]; then
            echo -e "${RED}✗ LiteLLM missing VERCEL_AI_GATEWAY_KEY${NC}"
        fi
    fi
else
    echo -e "${RED}✗ LiteLLM proxy service NOT found${NC}"
    echo -e "${YELLOW}  → Backend is using direct API connections${NC}"
fi

# Step 3: Check Backend Health
echo -e "\n${YELLOW}Step 3: Testing Backend Health${NC}"
echo "----------------------------------------"

HEALTH=$(curl -s "$BACKEND_URL/health" 2>&1)
if echo "$HEALTH" | grep -q "healthy"; then
    echo -e "${GREEN}✓ Backend is healthy${NC}"
    
    # Check if health response mentions AI Gateway
    if echo "$HEALTH" | grep -q "ai_gateway"; then
        echo -e "${GREEN}✓ Backend reports AI Gateway status${NC}"
        echo "$HEALTH" | jq '.ai_gateway' 2>/dev/null || echo "$HEALTH" | grep -o '"ai_gateway":{[^}]*}'
    fi
else
    echo -e "${RED}✗ Backend health check failed${NC}"
fi

# Step 4: Architecture Summary
echo -e "\n${BLUE}=================================${NC}"
echo -e "${BLUE}Current Architecture${NC}"
echo -e "${BLUE}=================================${NC}\n"

if [ "$LITELLM_EXISTS" -gt 0 ] && [ "$HAS_VERCEL" = true ]; then
    echo -e "${GREEN}✅ Using Vercel AI Gateway${NC}"
    echo ""
    echo "Request Flow:"
    echo "  Backend → LiteLLM Proxy → Vercel AI Gateway → AI Providers"
    echo ""
    echo "  1. Your Backend:      $BACKEND_URL"
    echo "  2. LiteLLM Proxy:     $LITELLM_PROXY"
    echo "  3. Vercel Gateway:    $VERCEL_URL"
    echo "  4. AI Providers:      OpenAI, Anthropic, etc."
    echo ""
    echo -e "${GREEN}Benefits:${NC}"
    echo "  • Edge caching for faster responses"
    echo "  • Centralized rate limiting"
    echo "  • Vercel analytics dashboard"
    echo "  • Multi-provider fallbacks"
    
elif [ "$LITELLM_EXISTS" -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Using LiteLLM (Direct to Providers)${NC}"
    echo ""
    echo "Request Flow:"
    echo "  Backend → LiteLLM Proxy → AI Providers (Direct)"
    echo ""
    echo "  1. Your Backend:      $BACKEND_URL"
    echo "  2. LiteLLM Proxy:     $LITELLM_PROXY"
    echo "  3. AI Providers:      OpenAI, Anthropic (Direct)"
    echo ""
    echo -e "${YELLOW}To enable Vercel AI Gateway:${NC}"
    echo "  See: VERCEL_AI_GATEWAY_SETUP.md"
    
else
    echo -e "${YELLOW}ℹ️  Using Direct API Connections${NC}"
    echo ""
    echo "Request Flow:"
    echo "  Backend → AI Providers (Direct)"
    echo ""
    echo "  1. Your Backend:      $BACKEND_URL"
    echo "  2. AI Providers:      OpenAI, Anthropic (Direct)"
    echo ""
    echo -e "${YELLOW}To enable AI Gateway:${NC}"
    echo "  1. Deploy LiteLLM: ./scripts/deploy-litellm.sh"
    echo "  2. Configure Vercel: See VERCEL_AI_GATEWAY_SETUP.md"
fi

# Step 5: Test Request (Optional)
echo -e "\n${YELLOW}Step 5: Live Request Test (Optional)${NC}"
echo "----------------------------------------"
echo "Would you like to send a test request? (y/n)"
read -r response

if [[ "$response" =~ ^[Yy]$ ]]; then
    echo "Sending test request..."
    
    TEST_RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/v1/blog/generate-gateway" \
      -H "Content-Type: application/json" \
      -d '{
        "topic": "Connection Test",
        "keywords": ["test"],
        "org_id": "test",
        "user_id": "test",
        "word_count": 100,
        "model": "gpt-4o-mini"
      }' 2>&1)
    
    if echo "$TEST_RESPONSE" | grep -q "content"; then
        CONTENT_LENGTH=$(echo "$TEST_RESPONSE" | jq -r '.content | length' 2>/dev/null || echo "unknown")
        echo -e "${GREEN}✓ Test request successful!${NC}"
        echo "  Content length: $CONTENT_LENGTH characters"
        
        # Check model used
        MODEL_USED=$(echo "$TEST_RESPONSE" | jq -r '.model_used' 2>/dev/null || echo "unknown")
        echo "  Model used: $MODEL_USED"
        
        echo ""
        echo -e "${BLUE}To verify where the request went:${NC}"
        echo "  1. Check backend logs:"
        echo "     gcloud logging read 'resource.labels.service_name=blog-writer-api-dev' --limit=5"
        
        if [ "$LITELLM_EXISTS" -gt 0 ]; then
            echo "  2. Check LiteLLM logs:"
            echo "     gcloud logging read 'resource.labels.service_name=litellm-proxy' --limit=5"
        fi
        
        if [ "$HAS_VERCEL" = true ]; then
            echo "  3. Check Vercel Dashboard:"
            echo "     https://vercel.com/dashboard → Your Project → Functions → Logs"
        fi
    else
        echo -e "${RED}✗ Test request failed${NC}"
        echo "Response: $TEST_RESPONSE"
    fi
fi

echo -e "\n${BLUE}=================================${NC}"
echo -e "${BLUE}Check Complete!${NC}"
echo -e "${BLUE}=================================${NC}\n"

# Recommendations
echo -e "${YELLOW}📋 Recommendations:${NC}\n"

if [ "$LITELLM_EXISTS" -eq 0 ]; then
    echo "1. Deploy LiteLLM proxy for better control:"
    echo "   ./scripts/deploy-litellm.sh"
    echo ""
fi

if [ "$HAS_VERCEL" = false ] && [ "$LITELLM_EXISTS" -gt 0 ]; then
    echo "2. Enable Vercel AI Gateway for edge caching:"
    echo "   See: VERCEL_AI_GATEWAY_SETUP.md"
    echo ""
fi

echo "3. For full setup guide, see:"
echo "   • VERCEL_AI_GATEWAY_SETUP.md - Complete configuration"
echo "   • BACKEND_AI_GATEWAY_IMPLEMENTATION.md - Backend setup"
echo ""

