#!/bin/bash

# Setup Multi-Environment Infrastructure for SDK-AI-Blog Writer
# This script creates service accounts, secrets, and IAM for dev/staging/prod

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
ENVIRONMENTS=("dev" "staging" "prod")

echo -e "${BLUE}🏗️  Setting up Multi-Environment Infrastructure${NC}"
echo "=================================================="

# Check if project exists and is set
if ! gcloud projects describe $PROJECT_ID &>/dev/null; then
    echo -e "${RED}❌ Project $PROJECT_ID not found. Please run ./scripts/create-project.sh first.${NC}"
    exit 1
fi

gcloud config set project $PROJECT_ID
echo -e "${GREEN}✅ Using project: $PROJECT_ID${NC}"

# Create service accounts for each environment
echo -e "${BLUE}👤 Creating service accounts for each environment${NC}"
for env in "${ENVIRONMENTS[@]}"; do
    SA_NAME="blog-writer-$env"
    SA_EMAIL="$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com"
    
    echo -e "  Creating service account: $SA_NAME"
    gcloud iam service-accounts create $SA_NAME \
        --display-name="Blog Writer SDK - $env Environment" \
        --description="Service account for $env environment of Blog Writer SDK" \
        --project=$PROJECT_ID || echo "    Service account may already exist"
    
    # Wait for service account to be fully created
    echo -e "  Waiting for service account to be ready..."
    sleep 5
    
    # Grant necessary permissions
    echo -e "  Granting permissions to $SA_NAME"
    
    # Secret Manager access
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$SA_EMAIL" \
        --role="roles/secretmanager.secretAccessor" \
        --quiet
    
    # Cloud SQL client (if needed later)
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$SA_EMAIL" \
        --role="roles/cloudsql.client" \
        --quiet
    
    # Monitoring metric writer
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$SA_EMAIL" \
        --role="roles/monitoring.metricWriter" \
        --quiet
    
    # Logging writer
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$SA_EMAIL" \
        --role="roles/logging.logWriter" \
        --quiet
    
    echo -e "${GREEN}  ✅ Service account $SA_NAME configured${NC}"
done

# Grant Cloud Build service account permissions to deploy
echo -e "${BLUE}🏗️  Configuring Cloud Build permissions${NC}"
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
CLOUD_BUILD_SA="$PROJECT_NUMBER@cloudbuild.gserviceaccount.com"

# Grant Cloud Run admin to Cloud Build
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$CLOUD_BUILD_SA" \
    --role="roles/run.admin" \
    --quiet

# Grant service account user role to Cloud Build
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$CLOUD_BUILD_SA" \
    --role="roles/iam.serviceAccountUser" \
    --quiet

# Grant Artifact Registry writer
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$CLOUD_BUILD_SA" \
    --role="roles/artifactregistry.writer" \
    --quiet

echo -e "${GREEN}✅ Cloud Build permissions configured${NC}"

# Create environment-specific secrets
echo -e "${BLUE}🔐 Creating environment-specific secrets${NC}"
for env in "${ENVIRONMENTS[@]}"; do
    SECRET_NAME="blog-writer-env-$env"
    ENV_FILE="env.$env"
    
    # Check if environment file exists
    if [ ! -f "$ENV_FILE" ]; then
        echo -e "${YELLOW}⚠️  $ENV_FILE not found. Creating from template...${NC}"
        
        # Create environment-specific config from template
        cp env.cloudrun "$ENV_FILE"
        
        # Update environment-specific values
        sed -i.bak "s/DEBUG=false/DEBUG=$([ "$env" = "dev" ] && echo "true" || echo "false")/g" "$ENV_FILE"
        sed -i.bak "s/LOG_LEVEL=info/LOG_LEVEL=$([ "$env" = "dev" ] && echo "debug" || echo "info")/g" "$ENV_FILE"
        
        # Add environment identifier
        echo "" >> "$ENV_FILE"
        echo "# Environment Configuration" >> "$ENV_FILE"
        echo "ENVIRONMENT=$env" >> "$ENV_FILE"
        echo "DATABASE_ENVIRONMENT=$env" >> "$ENV_FILE"
        
        # Remove backup file
        rm "$ENV_FILE.bak" 2>/dev/null || true
        
        echo -e "${YELLOW}📝 Please edit $ENV_FILE with your $env environment configuration${NC}"
    fi
    
    # Create or update secret
    echo -e "  Creating secret: $SECRET_NAME"
    if gcloud secrets describe $SECRET_NAME --project=$PROJECT_ID &>/dev/null; then
        echo -e "    Updating existing secret..."
        gcloud secrets versions add $SECRET_NAME \
            --data-file="$ENV_FILE" \
            --project=$PROJECT_ID
    else
        echo -e "    Creating new secret..."
        gcloud secrets create $SECRET_NAME \
            --data-file="$ENV_FILE" \
            --project=$PROJECT_ID
    fi
    
    # Grant access to environment-specific service account
    SA_EMAIL="blog-writer-$env@$PROJECT_ID.iam.gserviceaccount.com"
    gcloud secrets add-iam-policy-binding $SECRET_NAME \
        --member="serviceAccount:$SA_EMAIL" \
        --role="roles/secretmanager.secretAccessor" \
        --project=$PROJECT_ID \
        --quiet
    
    echo -e "${GREEN}  ✅ Secret $SECRET_NAME configured for $env${NC}"
done

# Create Cloud Build configuration for multi-environment
echo -e "${BLUE}📋 Creating multi-environment Cloud Build configuration${NC}"
cat > cloudbuild-multi-env.yaml << 'EOF'
# Multi-environment Cloud Build configuration
steps:
  # Build the container image
  - name: 'gcr.io/cloud-builders/docker'
    args: [
      'build',
      '-t', '${_REGION}-docker.pkg.dev/$PROJECT_ID/blog-writer-sdk/blog-writer-sdk:${COMMIT_SHA}',
      '-t', '${_REGION}-docker.pkg.dev/$PROJECT_ID/blog-writer-sdk/blog-writer-sdk:${_ENVIRONMENT}-latest',
      '.'
    ]

  # Push the container images
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', '${_REGION}-docker.pkg.dev/$PROJECT_ID/blog-writer-sdk/blog-writer-sdk:${COMMIT_SHA}']

  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', '${_REGION}-docker.pkg.dev/$PROJECT_ID/blog-writer-sdk/blog-writer-sdk:${_ENVIRONMENT}-latest']

  # Deploy to Cloud Run
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args: [
      'run', 'deploy', 'blog-writer-sdk-${_ENVIRONMENT}',
      '--image', '${_REGION}-docker.pkg.dev/$PROJECT_ID/blog-writer-sdk/blog-writer-sdk:${COMMIT_SHA}',
      '--region', '${_REGION}',
      '--platform', 'managed',
      '--allow-unauthenticated',
      '--port', '8000',
      '--memory', '${_MEMORY}',
      '--cpu', '${_CPU}',
      '--min-instances', '${_MIN_INSTANCES}',
      '--max-instances', '${_MAX_INSTANCES}',
      '--concurrency', '${_CONCURRENCY}',
      '--timeout', '900',
      '--service-account', 'blog-writer-${_ENVIRONMENT}@$PROJECT_ID.iam.gserviceaccount.com',
      '--set-env-vars', 'PORT=8000,PYTHONUNBUFFERED=1,ENVIRONMENT=${_ENVIRONMENT}',
      '--set-secrets', '/secrets/env=blog-writer-env-${_ENVIRONMENT}:latest'
    ]

# Store images in Artifact Registry
images:
  - '${_REGION}-docker.pkg.dev/$PROJECT_ID/blog-writer-sdk/blog-writer-sdk:${COMMIT_SHA}'
  - '${_REGION}-docker.pkg.dev/$PROJECT_ID/blog-writer-sdk/blog-writer-sdk:${_ENVIRONMENT}-latest'

# Default substitution variables
substitutions:
  _REGION: 'us-central1'
  _ENVIRONMENT: 'dev'
  _MEMORY: '1Gi'
  _CPU: '1'
  _MIN_INSTANCES: '0'
  _MAX_INSTANCES: '5'
  _CONCURRENCY: '10'

# Build options
options:
  logging: CLOUD_LOGGING_ONLY
  machineType: 'E2_HIGHCPU_8'
  diskSizeGb: '100'

# Build timeout
timeout: '1200s'
EOF

echo -e "${GREEN}✅ Multi-environment Cloud Build configuration created${NC}"

echo ""
echo -e "${GREEN}🎉 Multi-environment infrastructure setup completed!${NC}"
echo ""
echo -e "${BLUE}📋 Infrastructure Summary:${NC}"
echo "- Project: $PROJECT_ID"
echo "- Environments: ${ENVIRONMENTS[*]}"
echo "- Service Accounts: blog-writer-{dev,staging,prod}@$PROJECT_ID.iam.gserviceaccount.com"
echo "- Secrets: blog-writer-env-{dev,staging,prod}"
echo "- Container Registry: $REGION-docker.pkg.dev/$PROJECT_ID/blog-writer-sdk"
echo ""
echo -e "${YELLOW}📝 Next Steps:${NC}"
echo "1. Edit environment files with your API keys:"
for env in "${ENVIRONMENTS[@]}"; do
    echo "   - env.$env"
done
echo ""
echo "2. Update secrets with your configuration:"
echo "   ./scripts/update-secrets.sh"
echo ""
echo "3. Deploy to environments:"
echo "   ./scripts/deploy-env.sh dev"
echo "   ./scripts/deploy-env.sh staging"
echo "   ./scripts/deploy-env.sh prod"
echo ""
echo -e "${BLUE}🔗 Useful Commands:${NC}"
echo "- View secrets: gcloud secrets list --project=$PROJECT_ID"
echo "- View service accounts: gcloud iam service-accounts list --project=$PROJECT_ID"
echo "- View Cloud Run services: gcloud run services list --project=$PROJECT_ID"
