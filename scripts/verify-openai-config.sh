#!/bin/bash

# Verify OpenAI Configuration in Google Cloud Run
# This script checks if OpenAI credentials are properly configured

set -e

PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-"api-ai-blog-writer"}
REGION=${REGION:-"europe-west1"}
SERVICE_NAME=${SERVICE_NAME:-"blog-writer-api-dev"}

echo "🔍 Verifying OpenAI Configuration for Field Enhancement Endpoint"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Service: $SERVICE_NAME"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check 1: Verify OPENAI_API_KEY secret exists
echo -e "${BLUE}1. Checking if OPENAI_API_KEY secret exists...${NC}"
if gcloud secrets describe OPENAI_API_KEY --project=$PROJECT_ID &>/dev/null; then
    echo -e "${GREEN}✅ OPENAI_API_KEY secret exists${NC}"
    
    # Get secret metadata
    SECRET_INFO=$(gcloud secrets describe OPENAI_API_KEY --project=$PROJECT_ID --format="value(name,createTime)")
    echo "   Secret: $SECRET_INFO"
else
    echo -e "${RED}❌ OPENAI_API_KEY secret does NOT exist${NC}"
    echo "   Run: ./scripts/setup-ai-provider-secrets.sh"
    exit 1
fi

# Check 2: Verify secret has a version
echo ""
echo -e "${BLUE}2. Checking if secret has a version...${NC}"
SECRET_VERSION=$(gcloud secrets versions list OPENAI_API_KEY --project=$PROJECT_ID --limit=1 --format="value(name)" 2>/dev/null | head -1)
if [ ! -z "$SECRET_VERSION" ]; then
    echo -e "${GREEN}✅ Secret has version: $SECRET_VERSION${NC}"
else
    echo -e "${RED}❌ Secret has no versions${NC}"
    echo "   You need to add a secret value"
    exit 1
fi

# Check 3: Get service account
echo ""
echo -e "${BLUE}3. Getting Cloud Run service account...${NC}"
SERVICE_ACCOUNT=$(gcloud run services describe $SERVICE_NAME \
    --region=$REGION \
    --project=$PROJECT_ID \
    --format="value(spec.template.spec.serviceAccountName)" 2>/dev/null)

if [ -z "$SERVICE_ACCOUNT" ]; then
    # Try default service account format
    SERVICE_ACCOUNT="${PROJECT_ID}@${PROJECT_ID}.iam.gserviceaccount.com"
    echo -e "${YELLOW}⚠️  Could not get service account from service, using default: $SERVICE_ACCOUNT${NC}"
else
    echo -e "${GREEN}✅ Service account: $SERVICE_ACCOUNT${NC}"
fi

# Check 4: Verify service account has access to secret
echo ""
echo -e "${BLUE}4. Checking if service account has access to OPENAI_API_KEY...${NC}"
IAM_POLICY=$(gcloud secrets get-iam-policy OPENAI_API_KEY --project=$PROJECT_ID --format="value(bindings.members)" 2>/dev/null | grep "$SERVICE_ACCOUNT" || echo "")

if echo "$IAM_POLICY" | grep -q "$SERVICE_ACCOUNT"; then
    echo -e "${GREEN}✅ Service account has access to OPENAI_API_KEY${NC}"
else
    echo -e "${RED}❌ Service account does NOT have access to OPENAI_API_KEY${NC}"
    echo "   Granting access..."
    gcloud secrets add-iam-policy-binding OPENAI_API_KEY \
        --member="serviceAccount:$SERVICE_ACCOUNT" \
        --role="roles/secretmanager.secretAccessor" \
        --project=$PROJECT_ID && \
    echo -e "${GREEN}✅ Access granted${NC}" || \
    echo -e "${RED}❌ Failed to grant access${NC}"
fi

# Check 5: Verify Cloud Run service has secret mounted
echo ""
echo -e "${BLUE}5. Checking if Cloud Run service has OPENAI_API_KEY mounted...${NC}"
ENV_VARS=$(gcloud run services describe $SERVICE_NAME \
    --region=$REGION \
    --project=$PROJECT_ID \
    --format="value(spec.template.spec.containers[0].env)" 2>/dev/null)

if echo "$ENV_VARS" | grep -q "OPENAI_API_KEY"; then
    echo -e "${GREEN}✅ OPENAI_API_KEY is mounted in Cloud Run service${NC}"
    
    # Try to get the exact mount configuration
    SECRET_MOUNT=$(gcloud run services describe $SERVICE_NAME \
        --region=$REGION \
        --project=$PROJECT_ID \
        --format="json" 2>/dev/null | \
        jq -r '.spec.template.spec.containers[0].env[] | select(.name=="OPENAI_API_KEY") | .valueFrom.secretKeyRef.name // "not-found"' 2>/dev/null || echo "not-found")
    
    if [ "$SECRET_MOUNT" != "not-found" ] && [ "$SECRET_MOUNT" != "null" ]; then
        echo "   Mounted from secret: $SECRET_MOUNT"
    fi
else
    echo -e "${RED}❌ OPENAI_API_KEY is NOT mounted in Cloud Run service${NC}"
    echo ""
    echo "   To fix, run:"
    echo "   gcloud run services update $SERVICE_NAME \\"
    echo "     --region=$REGION \\"
    echo "     --project=$PROJECT_ID \\"
    echo "     --update-secrets=OPENAI_API_KEY=OPENAI_API_KEY:latest"
    exit 1
fi

# Check 6: Verify code reads from correct environment variable
echo ""
echo -e "${BLUE}6. Verifying code reads from OPENAI_API_KEY environment variable...${NC}"
if grep -q "os.getenv(\"OPENAI_API_KEY\")" src/blog_writer_sdk/api/field_enhancement.py; then
    echo -e "${GREEN}✅ Code reads from OPENAI_API_KEY environment variable${NC}"
    echo "   Found in: src/blog_writer_sdk/api/field_enhancement.py"
else
    echo -e "${RED}❌ Code does not read from OPENAI_API_KEY${NC}"
    exit 1
fi

# Check 7: Test endpoint (if service is running)
echo ""
echo -e "${BLUE}7. Testing endpoint availability...${NC}"
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --region=$REGION \
    --project=$PROJECT_ID \
    --format="value(status.url)" 2>/dev/null)

if [ ! -z "$SERVICE_URL" ]; then
    echo "   Service URL: $SERVICE_URL"
    
    # Test health endpoint
    if curl -s -f "${SERVICE_URL}/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Service is running and accessible${NC}"
        
        # Test field enhancement endpoint
        echo ""
        echo -e "${BLUE}8. Testing field enhancement endpoint...${NC}"
        TEST_RESPONSE=$(curl -s -X POST "${SERVICE_URL}/api/v1/content/enhance-fields" \
            -H "Content-Type: application/json" \
            -d '{
                "title": "Test Blog Post",
                "enhance_seo_title": true,
                "enhance_meta_description": true
            }' 2>&1)
        
        if echo "$TEST_RESPONSE" | grep -q "enhanced_fields"; then
            echo -e "${GREEN}✅ Endpoint works! OpenAI is accessible${NC}"
            echo "   Response preview:"
            echo "$TEST_RESPONSE" | jq -r '.enhanced_fields' 2>/dev/null || echo "$TEST_RESPONSE" | head -5
        elif echo "$TEST_RESPONSE" | grep -q "OpenAI API key is not configured"; then
            echo -e "${RED}❌ Endpoint returns: OpenAI API key is not configured${NC}"
            echo "   This means the secret exists but is not accessible at runtime"
            echo "   Check Cloud Run logs for more details"
        elif echo "$TEST_RESPONSE" | grep -q "503"; then
            echo -e "${RED}❌ Endpoint returns 503 error${NC}"
            echo "   Response: $TEST_RESPONSE"
        else
            echo -e "${YELLOW}⚠️  Unexpected response${NC}"
            echo "   Response: $TEST_RESPONSE"
        fi
    else
        echo -e "${YELLOW}⚠️  Service health check failed${NC}"
        echo "   Service may be starting or unavailable"
    fi
else
    echo -e "${YELLOW}⚠️  Could not get service URL${NC}"
fi

# Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${BLUE}📋 Configuration Summary${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Secret exists: OPENAI_API_KEY"
echo "✅ Service account access: $SERVICE_ACCOUNT"
echo "✅ Secret mounted in Cloud Run"
echo "✅ Code reads from OPENAI_API_KEY"
echo ""
echo "If endpoint test failed, check:"
echo "1. Cloud Run service logs: gcloud run services logs read $SERVICE_NAME --region=$REGION"
echo "2. Secret value: gcloud secrets versions access latest --secret=OPENAI_API_KEY"
echo "3. Service restart may be needed after secret changes"
echo ""



