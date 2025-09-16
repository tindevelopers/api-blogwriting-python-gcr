#!/bin/bash

# Google Cloud Run Deployment Script for BlogWriter SDK
echo "☁️ Deploying BlogWriter SDK to Google Cloud Run..."

# Check if gcloud CLI is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ Google Cloud CLI not found. Please install it first."
    echo "Visit: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if logged in to Google Cloud
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ Not logged in to Google Cloud. Please run 'gcloud auth login' first."
    exit 1
fi

echo "✅ Google Cloud CLI ready"

# Set project ID
PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-"api-ai-blog-writer"}
REGION=${GOOGLE_CLOUD_REGION:-"us-central1"}
SERVICE_NAME=${SERVICE_NAME:-"blog-writer-sdk"}

echo "📋 Project: $PROJECT_ID"
echo "🌍 Region: $REGION"
echo "🚀 Service: $SERVICE_NAME"

# Set environment variables
echo "🔧 Setting environment variables..."
gcloud run services update $SERVICE_NAME \
    --set-env-vars="PORT=8000,HOST=0.0.0.0,DEBUG=false" \
    --region=$REGION \
    --project=$PROJECT_ID || echo "⚠️ Service not found, will create during deployment"

gcloud run services update $SERVICE_NAME \
    --set-env-vars="API_TITLE=Blog Writer SDK API,API_VERSION=0.1.0" \
    --region=$REGION \
    --project=$PROJECT_ID || echo "⚠️ Service not found, will create during deployment"

gcloud run services update $SERVICE_NAME \
    --set-env-vars="DEFAULT_TONE=professional,DEFAULT_LENGTH=medium" \
    --region=$REGION \
    --project=$PROJECT_ID || echo "⚠️ Service not found, will create during deployment"

gcloud run services update $SERVICE_NAME \
    --set-env-vars="ENABLE_SEO_OPTIMIZATION=true,ENABLE_QUALITY_ANALYSIS=true" \
    --region=$REGION \
    --project=$PROJECT_ID || echo "⚠️ Service not found, will create during deployment"

gcloud run services update $SERVICE_NAME \
    --set-env-vars="ALLOWED_ORIGINS=http://localhost:3000,https://your-app.vercel.app" \
    --region=$REGION \
    --project=$PROJECT_ID || echo "⚠️ Service not found, will create during deployment"

# Deploy to Google Cloud Run
echo "🚀 Deploying to Google Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --source . \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --project $PROJECT_ID

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --project=$PROJECT_ID --format="value(status.url)")

echo "✅ Deployment complete!"
echo "📊 Check deployment status: gcloud run services describe $SERVICE_NAME --region=$REGION"
echo "🌐 Open dashboard: gcloud run services list"
echo "🔗 Your service: $SERVICE_URL"

echo ""
echo "📝 Next steps:"
echo "1. Add AI provider API keys in Google Cloud Console (Environment Variables)"
echo "2. Test the health endpoint: curl $SERVICE_URL/health"
echo "3. Update your frontend to use: $SERVICE_URL"
echo "4. Set up custom domain if needed"

echo ""
echo "🎉 BlogWriter SDK is now live on Google Cloud Run!"