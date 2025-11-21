#!/bin/bash
# Script to add Google Places API Key to Google Secret Manager
# Usage: ./scripts/add-google-places-secrets.sh [API_KEY]

set -e

PROJECT_ID="api-ai-blog-writer"
GOOGLE_PLACES_API_KEY="${1:-AIzaSyBgG-6xqHXs-CULw1nQWfC3ygypqFg1EgI}"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🗺️  Google Places API Key Setup${NC}"
echo "======================================"
echo ""

# Check if gcloud is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &>/dev/null; then
    echo -e "${RED}❌ Not authenticated to Google Cloud. Please run: gcloud auth login${NC}"
    exit 1
fi

# Function to add or update a secret value (handles both JSON and plain text formats)
add_secret_value() {
    local SECRET_NAME=$1
    local KEY=$2
    local VALUE=$3
    
    echo -e "${BLUE}📝 Adding $KEY to $SECRET_NAME...${NC}"
    
    if ! gcloud secrets describe "$SECRET_NAME" --project="$PROJECT_ID" &>/dev/null; then
        echo -e "${RED}❌ Secret $SECRET_NAME does not exist.${NC}"
        echo "Creating it now..."
        echo "" | gcloud secrets create "$SECRET_NAME" \
            --data-file=- \
            --project="$PROJECT_ID" \
            --replication-policy="automatic" \
            --quiet
    fi
    
    CURRENT_CONTENT=$(gcloud secrets versions access latest --secret="$SECRET_NAME" --project="$PROJECT_ID" 2>/dev/null || echo "")
    
    if [ -z "$CURRENT_CONTENT" ]; then
        # Empty secret, create new entry
        UPDATED_CONTENT="${KEY}=${VALUE}"
    elif echo "$CURRENT_CONTENT" | jq . >/dev/null 2>&1; then
        # JSON format
        UPDATED_CONTENT=$(echo "$CURRENT_CONTENT" | jq --arg key "$KEY" --arg value "$VALUE" '. + {($key): $value}')
    else
        # Plain text format (env file)
        if echo "$CURRENT_CONTENT" | grep -q "^${KEY}="; then
            # Update existing key
            UPDATED_CONTENT=$(echo "$CURRENT_CONTENT" | sed "s|^${KEY}=.*|${KEY}=${VALUE}|")
        else
            # Add new key
            UPDATED_CONTENT="${CURRENT_CONTENT}
${KEY}=${VALUE}"
        fi
    fi
    
    echo "$UPDATED_CONTENT" | gcloud secrets versions add "$SECRET_NAME" \
        --data-file=- \
        --project="$PROJECT_ID" \
        --quiet
    
    echo -e "${GREEN}✅ Updated $KEY in $SECRET_NAME${NC}"
}

# Display API key (masked)
MASKED_KEY="${GOOGLE_PLACES_API_KEY:0:10}...${GOOGLE_PLACES_API_KEY: -4}"
echo -e "${GREEN}✅ Using API Key: ${MASKED_KEY}${NC}"
echo ""

# Add to dev environment
echo -e "${BLUE}🔧 Adding to dev environment...${NC}"
add_secret_value "blog-writer-env-dev" "GOOGLE_PLACES_API_KEY" "$GOOGLE_PLACES_API_KEY"

# Also add as GOOGLE_MAPS_API_KEY for backward compatibility
add_secret_value "blog-writer-env-dev" "GOOGLE_MAPS_API_KEY" "$GOOGLE_PLACES_API_KEY"

# Ask about staging
echo ""
read -p "Add to staging environment? (y/n): " ADD_STAGING
if [[ "$ADD_STAGING" =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}🔧 Adding to staging environment...${NC}"
    add_secret_value "blog-writer-env-staging" "GOOGLE_PLACES_API_KEY" "$GOOGLE_PLACES_API_KEY"
    add_secret_value "blog-writer-env-staging" "GOOGLE_MAPS_API_KEY" "$GOOGLE_PLACES_API_KEY"
fi

# Ask about production
read -p "Add to production environment? (y/n): " ADD_PROD
if [[ "$ADD_PROD" =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}🔧 Adding to production environment...${NC}"
    add_secret_value "blog-writer-env-prod" "GOOGLE_PLACES_API_KEY" "$GOOGLE_PLACES_API_KEY"
    add_secret_value "blog-writer-env-prod" "GOOGLE_MAPS_API_KEY" "$GOOGLE_PLACES_API_KEY"
fi

# Grant service account access
echo ""
echo -e "${BLUE}🔐 Granting service account access...${NC}"
SERVICE_ACCOUNT="613248238610-compute@developer.gserviceaccount.com"

for SECRET_NAME in "blog-writer-env-dev" "blog-writer-env-staging" "blog-writer-env-prod"; do
    if gcloud secrets describe "$SECRET_NAME" --project="$PROJECT_ID" &>/dev/null; then
        gcloud secrets add-iam-policy-binding "$SECRET_NAME" \
            --member="serviceAccount:${SERVICE_ACCOUNT}" \
            --role="roles/secretmanager.secretAccessor" \
            --project="$PROJECT_ID" \
            --quiet 2>/dev/null || echo "Permissions already set for $SECRET_NAME"
    fi
done

echo ""
echo "======================================"
echo -e "${GREEN}✅ Google Places API key added successfully!${NC}"
echo ""
echo -e "${YELLOW}📝 Next steps:${NC}"
echo "   1. The secret is now in Secret Manager"
echo "   2. Redeploy Cloud Run service to load the new secret:"
echo "      git push origin develop"
echo ""
echo "   3. Or force a new revision (quick test):"
echo "      gcloud run services update blog-writer-api-dev \\"
echo "        --region europe-west9 \\"
echo "        --project $PROJECT_ID \\"
echo "        --update-env-vars DUMMY=\$(date +%s)"
echo ""
echo "   4. Verify the secret is accessible:"
echo "      gcloud logging read \"resource.type=cloud_run_revision AND resource.labels.service_name=blog-writer-api-dev AND textPayload=~'Google Places'\" --limit=10 --project=$PROJECT_ID"
echo ""
echo -e "${GREEN}🎉 Done!${NC}"

