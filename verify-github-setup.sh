#!/bin/bash

# GitHub Repository Secrets Verification Script
# This script helps verify that the GitHub repository is properly configured

echo "🔍 Verifying GitHub Repository Setup for AI Blog Writer SDK"
echo "=========================================================="

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

echo "✅ Project directory confirmed"

# Check if GitHub CLI is installed
if command -v gh &> /dev/null; then
    echo "✅ GitHub CLI is installed"
    
    # Check if user is authenticated
    if gh auth status &> /dev/null; then
        echo "✅ GitHub CLI is authenticated"
        
        # Get repository info
        REPO_INFO=$(gh repo view --json name,owner,url 2>/dev/null)
        if [ $? -eq 0 ]; then
            echo "✅ Repository access confirmed"
            echo "📋 Repository: $(echo $REPO_INFO | jq -r '.owner.login')/$(echo $REPO_INFO | jq -r '.name')"
            echo "🔗 URL: $(echo $REPO_INFO | jq -r '.url')"
        else
            echo "⚠️  Could not access repository information"
        fi
    else
        echo "⚠️  GitHub CLI is not authenticated. Run 'gh auth login'"
    fi
else
    echo "⚠️  GitHub CLI is not installed. Install it for easier repository management"
fi

echo ""
echo "📋 Required GitHub Repository Secrets:"
echo "======================================"
echo "1. GOOGLE_CLOUD_SA_KEY (Service Account JSON key)"
echo "2. GOOGLE_CLOUD_PROJECT (Project ID: sdk-ai-blog-writer)"
echo ""
echo "🔗 Add secrets at: https://github.com/tindevelopers/api-blogwriting-python-gcr/settings/secrets/actions"
echo ""

# Check if service account key exists locally
if [ -f "blog-writer-deploy-key.json" ]; then
    echo "✅ Service account key file found locally"
    echo "📋 Use the content of this file as the GOOGLE_CLOUD_SA_KEY secret"
else
    echo "⚠️  Service account key file not found locally"
    echo "📋 The key content is provided in setup-github-secrets.md"
fi

echo ""
echo "🧪 Testing Current Deployment:"
echo "=============================="

# Test the deployed service
SERVICE_URL="https://blog-writer-sdk-324019679988.us-central1.run.app"

echo "Testing health endpoint..."
if curl -s -f "$SERVICE_URL/health" > /dev/null; then
    echo "✅ Health check passed"
    echo "🌐 Service URL: $SERVICE_URL"
    echo "📚 API Docs: $SERVICE_URL/docs"
else
    echo "❌ Health check failed"
fi

echo ""
echo "📝 Next Steps:"
echo "=============="
echo "1. Add the required secrets to GitHub repository"
echo "2. Push a commit to trigger the deployment workflow"
echo "3. Check the Actions tab to verify successful deployment"
echo "4. Test the deployed service"

echo ""
echo "🎉 Setup verification complete!"
