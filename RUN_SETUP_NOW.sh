#!/bin/bash

# Quick setup script - Run this in your terminal
# It will prompt you for API keys securely

set -e

echo "🚀 AI Provider Secrets Setup"
echo "=============================="
echo ""

# Set configuration
export GOOGLE_CLOUD_PROJECT="api-ai-blog-writer"
export REGION="europe-west1"
export SERVICE_NAME="blog-writer-api-dev"

echo "Configuration:"
echo "  Project: $GOOGLE_CLOUD_PROJECT"
echo "  Region: $REGION"
echo "  Service: $SERVICE_NAME"
echo ""

# Run the interactive setup script
./scripts/setup-ai-provider-secrets.sh

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next: Test the enhanced endpoint to verify it works:"
echo "  curl -X POST 'https://blog-writer-api-dev-613248238610.europe-west1.run.app/api/v1/blog/generate-enhanced' \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"topic\":\"Test\",\"keywords\":[\"test\"],\"use_google_search\":true}'"

