# GitHub Repository Secrets Setup Guide

This guide will help you configure the necessary secrets in your GitHub repository to enable automatic deployment to Google Cloud Run.

## Required GitHub Repository Secrets

You need to add the following secrets to your GitHub repository:

### 1. Google Cloud Service Account Key
- **Secret Name**: `GOOGLE_CLOUD_SA_KEY`
- **Description**: Service account JSON key for Google Cloud authentication
- **Value**: The complete JSON key for the service account

### 2. Google Cloud Project ID
- **Secret Name**: `GOOGLE_CLOUD_PROJECT`
- **Description**: Google Cloud project ID
- **Value**: `api-ai-blog-writer`

## How to Add Secrets to GitHub Repository

1. **Navigate to Repository Settings**:
   - Go to: https://github.com/tindevelopers/api-blogwriting-python-gcr/settings/secrets/actions

2. **Add Each Secret**:
   - Click "New repository secret"
   - Enter the secret name
   - Enter the secret value
   - Click "Add secret"

## Service Account Key

The service account key has already been generated and configured. You need to add this key as the `GOOGLE_CLOUD_SA_KEY` secret.

**⚠️ IMPORTANT**: The service account key contains sensitive information and cannot be included in this documentation due to GitHub's security policies.

**To get the service account key:**

1. **If you have access to the Google Cloud Console**:
   - Go to: https://console.cloud.google.com/iam-admin/serviceaccounts?project=api-ai-blog-writer
   - Find the service account: `blog-writer-deploy@api-ai-blog-writer.iam.gserviceaccount.com`
   - Click on the service account → Keys tab → Add Key → Create new key → JSON
   - Download the JSON file

2. **If you have the gcloud CLI**:
   ```bash
   gcloud iam service-accounts keys create blog-writer-deploy-key.json \
     --iam-account=blog-writer-deploy@api-ai-blog-writer.iam.gserviceaccount.com
   ```

3. **Use the generated key**:
   - Copy the entire JSON content from the downloaded file
   - Add it as the `GOOGLE_CLOUD_SA_KEY` secret in GitHub

## Optional Environment Variables

You can also add these optional secrets for enhanced functionality:

### AI Provider Keys (Optional)
- `OPENAI_API_KEY`: Your OpenAI API key
- `ANTHROPIC_API_KEY`: Your Anthropic API key
- `DEEPSEEK_API_KEY`: Your DeepSeek API key

### Database Configuration (Optional)
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY`: Your Supabase service role key

### External Services (Optional)
- `DATAFORSEO_API_KEY`: DataForSEO API key for enhanced keyword analysis
- `DATAFORSEO_API_SECRET`: DataForSEO API secret

## Verification

After adding the secrets:

1. **Check the secrets are added**:
   - Go to: https://github.com/tindevelopers/api-blogwriting-python-gcr/settings/secrets/actions
   - You should see `GOOGLE_CLOUD_SA_KEY` and `GOOGLE_CLOUD_PROJECT` in the list

2. **Test the deployment**:
   - Push a commit to the main branch
   - Check the Actions tab to see if the deployment workflow runs successfully

3. **Manual deployment test**:
   - Go to: https://github.com/tindevelopers/api-blogwriting-python-gcr/actions
   - Click on "Deploy to Google Cloud Run" workflow
   - Click "Run workflow" to test manually

## Current Deployment Status

✅ **Service Account Created**: `blog-writer-deploy@api-ai-blog-writer.iam.gserviceaccount.com`  
✅ **Required APIs Enabled**: Cloud Run, Cloud Build, Artifact Registry  
✅ **Application Deployed**: https://blog-writer-sdk-324019679988.us-central1.run.app  
⏳ **GitHub Secrets**: Need to be configured manually  

Once the secrets are added, the GitHub Actions will automatically deploy on every push to the main branch!
