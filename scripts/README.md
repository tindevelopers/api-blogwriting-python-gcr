# Scripts Directory

This directory contains utility scripts for deployment, testing, and database management.

---

## Available Scripts

### 🚀 `deploy.sh`

**Purpose:** Automated deployment script for the Blog Writer API to Google Cloud Run.

**Features:**
- Interactive deployment menu
- Build and push Docker images
- Deploy to Google Cloud Run
- Seed Firestore with default templates
- Multiple deployment modes

**Usage:**
```bash
# Make executable (first time only)
chmod +x scripts/deploy.sh

# Run deployment
./scripts/deploy.sh
```

**Options:**
1. **Full deployment** - Build, push, deploy to GCR, and seed Firestore
2. **Seed Firestore only** - Just populate Firestore with default templates
3. **Build and push** - Build Docker image and push to GCR only
4. **Deploy only** - Deploy to GCR using existing image

**Prerequisites:**
- Docker installed
- gcloud CLI authenticated
- Firebase credentials set (see below)
- GCP project with billing enabled

**Environment Variables:**
```bash
# Required (one of):
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
export FIREBASE_SERVICE_ACCOUNT_KEY_BASE64="<base64-encoded-json>"

# Optional:
export GCP_PROJECT_ID="your-project-id"      # Default: blog-writer-dev
export GCP_REGION="europe-west9"             # Default: europe-west9
export SERVICE_NAME="blog-writer-api"        # Default: blog-writer-api
```

---

### 🌱 `seed_default_prompts_firestore.py`

**Purpose:** Seeds Firestore with default prompt configurations and writing styles.

**What it does:**
- Creates "Natural Conversational" prompt configuration
- Creates corresponding writing style
- Updates existing configs if they already exist
- Safe to run multiple times (idempotent)

**Usage:**
```bash
# Set Firebase credentials
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"

# Run seed script
python3 scripts/seed_default_prompts_firestore.py
```

**What gets created:**

1. **Prompt Config**: `default_natural_conversational`
   - Formality Level: 6 (Balanced)
   - Contractions: Enabled
   - Avoids obvious AI transitions
   - Conversational engagement style
   - Friendly personality
   - Comprehensive writing instructions

2. **Writing Style**: `natural_conversational`
   - Links to the prompt config above
   - Set as default style
   - Available for all organizations

**Expected Output:**
```
Starting Firestore seeding process...
Initializing Firebase with Application Default Credentials.
Firebase Admin SDK initialized.
Creating PromptConfig 'default_natural_conversational'...
PromptConfig 'default_natural_conversational' seeded/updated.
Creating WritingStyle 'natural_conversational'...
WritingStyle 'natural_conversational' seeded/updated.
Firestore seeding process completed.
```

**Troubleshooting:**
- **"Firebase credentials not found"**: Set `GOOGLE_APPLICATION_CREDENTIALS`
- **"Permission denied"**: Ensure service account has Firestore Admin role
- **"Project not found"**: Verify Firebase project ID in service account JSON

---

## Firebase Credentials Setup

### Method 1: Application Default Credentials (Recommended)

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
```

**Where to get the service account key:**
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project
3. Go to **Project Settings** → **Service Accounts**
4. Click **Generate New Private Key**
5. Save the JSON file securely
6. Set the environment variable to the file path

### Method 2: Base64 Encoded Key

```bash
# Encode the key
cat /path/to/service-account.json | base64 > sa-base64.txt

# Set environment variable
export FIREBASE_SERVICE_ACCOUNT_KEY_BASE64="$(cat sa-base64.txt)"
```

### Method 3: File Path (Alternative)

```bash
export FIREBASE_SERVICE_ACCOUNT_KEY_PATH="/path/to/service-account.json"
```

---

## Quick Start Guide

### First Time Setup

```bash
# 1. Navigate to project directory
cd /Users/foo/projects/api-blogwriting-python-gcr-1

# 2. Set up Firebase credentials
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"

# 3. Authenticate with gcloud
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud auth configure-docker

# 4. Make deploy script executable
chmod +x scripts/deploy.sh

# 5. Run full deployment
./scripts/deploy.sh
# Select option 1 (Full deployment)
```

### Subsequent Deployments

```bash
# Quick redeploy
./scripts/deploy.sh
# Select option 1 or 4

# Or manual build and deploy
docker build -t blog-writer-api .
docker tag blog-writer-api gcr.io/YOUR_PROJECT_ID/blog-writer-api
docker push gcr.io/YOUR_PROJECT_ID/blog-writer-api
gcloud run deploy blog-writer-api \
  --image gcr.io/YOUR_PROJECT_ID/blog-writer-api \
  --region europe-west9
```

### Re-seed Firestore

```bash
# If you need to reset or update default templates
./scripts/deploy.sh
# Select option 2 (Seed Firestore only)

# Or run directly
python3 scripts/seed_default_prompts_firestore.py
```

---

## Common Tasks

### Test Locally Before Deploying

```bash
# Build Docker image
docker build -t blog-writer-api .

# Run locally
docker run -p 8080:8080 \
  -e GOOGLE_APPLICATION_CREDENTIALS=/path/in/container/sa.json \
  -v /path/on/host/sa.json:/path/in/container/sa.json \
  blog-writer-api

# Test health endpoint
curl http://localhost:8080/health
```

### Update Only Docker Image

```bash
./scripts/deploy.sh
# Select option 3 (Build and push only)
```

### Deploy Without Building

```bash
./scripts/deploy.sh
# Select option 4 (Deploy only)
```

### Add New Writing Styles

After initial deployment, you can add new writing styles programmatically:

```python
# create_custom_style.py
import asyncio
from src.blog_writer_sdk.integrations.firebase_config_client import FirebaseConfigClient
from src.blog_writer_sdk.models.prompt_config_models import PromptConfig, WritingStyle

async def create_custom_style():
    client = FirebaseConfigClient()
    
    # Create custom prompt config
    config = PromptConfig(
        config_id="professional_formal",
        name="Professional & Formal",
        description="Formal writing style for business content",
        config_data={
            "formality_level": 9,
            "use_contractions": False,
            "engagement_style": "professional",
            "personality": "authoritative",
            # ... more settings
        }
    )
    await client.create_prompt_config(config.config_id, config.dict())
    
    # Create writing style
    style = WritingStyle(
        style_id="professional_formal_style",
        name="Professional & Formal",
        description="Best for white papers and business reports",
        prompt_config_id="professional_formal"
    )
    await client.create_writing_style(style.style_id, style.dict())
    
    print("Custom style created!")

if __name__ == "__main__":
    asyncio.run(create_custom_style())
```

---

## Troubleshooting

### Issue: Permission denied when running deploy.sh

```bash
chmod +x scripts/deploy.sh
```

### Issue: Python command not found

Use `python3` instead:
```bash
python3 scripts/seed_default_prompts_firestore.py
```

### Issue: Module not found errors

Install dependencies:
```bash
pip install -r requirements.txt
```

### Issue: Docker build fails

Check Docker is running:
```bash
docker ps
```

If not running, start Docker Desktop or Docker daemon.

### Issue: gcloud command not found

Install gcloud CLI:
- macOS: `brew install google-cloud-sdk`
- Linux: [Install Guide](https://cloud.google.com/sdk/docs/install)

### Issue: Firestore connection timeout

Check network and firewall settings:
```bash
ping firestore.googleapis.com
```

---

## Best Practices

1. **Always test locally first** before deploying to production
2. **Use version tags** for Docker images in production
3. **Backup Firestore** before making schema changes
4. **Monitor logs** after deployment for errors
5. **Test API endpoints** immediately after deployment
6. **Keep credentials secure** - never commit to git
7. **Use CI/CD** for production deployments
8. **Set up monitoring** and alerts in Cloud Console

---

## CI/CD Integration

### GitHub Actions Example

See `DEPLOYMENT_GUIDE.md` for complete GitHub Actions workflow example.

### GitLab CI Example

```yaml
deploy:
  stage: deploy
  image: google/cloud-sdk:alpine
  script:
    - echo $GCP_SA_KEY | base64 -d > /tmp/sa-key.json
    - gcloud auth activate-service-account --key-file=/tmp/sa-key.json
    - gcloud config set project $GCP_PROJECT_ID
    - gcloud builds submit --tag gcr.io/$GCP_PROJECT_ID/blog-writer-api
    - gcloud run deploy blog-writer-api --image gcr.io/$GCP_PROJECT_ID/blog-writer-api
  only:
    - main
```

---

## Additional Resources

- **Deployment Guide**: `DEPLOYMENT_GUIDE.md` - Complete deployment documentation
- **Implementation Summary**: `IMPLEMENTATION_SUMMARY.md` - System overview
- **Frontend Guides**: 
  - `FRONTEND_WRITING_STYLE_CONFIGURATION.md` - Admin Dashboard specs
  - `FRONTEND_PER_BLOG_CUSTOMIZATION.md` - Consumer Frontend specs
- **API Documentation**: `https://your-service-url.run.app/docs`

---

## Script Maintenance

### Adding New Scripts

When adding new scripts to this directory:
1. Make scripts executable: `chmod +x script-name.sh`
2. Add shebang line: `#!/bin/bash` or `#!/usr/bin/env python3`
3. Add error handling: `set -e` for bash scripts
4. Document in this README
5. Add usage examples

### Versioning

Scripts follow the same version as the main application.
Current Version: **1.0**

---

**Last Updated:** January 1, 2026  
**Maintained By:** Project Team  
**Questions?** Check `DEPLOYMENT_GUIDE.md` or project documentation

