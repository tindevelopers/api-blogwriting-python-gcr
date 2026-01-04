# Deployment Guide - Blog Writer API

**Version:** 1.0  
**Date:** January 1, 2026  
**Status:** Production Ready

---

## Quick Start

### Prerequisites

1. **Google Cloud Project** with billing enabled
2. **Firebase Project** (can be the same as GCP project)
3. **Firestore Database** created in Firebase Console
4. **Service Account** with Firestore permissions
5. **Docker** installed locally
6. **gcloud CLI** installed and authenticated

### Step 1: Configure Firebase Credentials

Choose one of the following methods:

**Option A: Application Default Credentials (Recommended for GCR)**
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your-service-account-key.json"
```

**Option B: Base64 Encoded Credentials**
```bash
# First, encode your service account key
cat /path/to/service-account-key.json | base64 > service-account-base64.txt

# Then export it
export FIREBASE_SERVICE_ACCOUNT_KEY_BASE64="$(cat service-account-base64.txt)"
```

**Option C: File Path (Alternative)**
```bash
export FIREBASE_SERVICE_ACCOUNT_KEY_PATH="/path/to/service-account-key.json"
```

### Step 2: Configure GCP Settings (Optional)

```bash
# Set your GCP project ID (default: blog-writer-dev)
export GCP_PROJECT_ID="your-project-id"

# Set your preferred region (default: europe-west9)
export GCP_REGION="europe-west9"

# Set service name (default: blog-writer-api)
export SERVICE_NAME="blog-writer-api"
```

### Step 3: Authenticate with Google Cloud

```bash
# Login to gcloud
gcloud auth login

# Set your project
gcloud config set project $GCP_PROJECT_ID

# Configure Docker to use gcloud credentials
gcloud auth configure-docker
```

### Step 4: Run Deployment Script

```bash
# Navigate to project directory
cd /Users/foo/projects/api-blogwriting-python-gcr-1

# Run the deployment script
./scripts/deploy.sh
```

The script will prompt you to select a deployment option:
- **Option 1**: Full deployment (build, push, deploy to GCR, seed Firestore)
- **Option 2**: Seed Firestore only
- **Option 3**: Build and push Docker image only
- **Option 4**: Deploy to GCR only

For first-time deployment, choose **Option 1**.

---

## Manual Deployment Steps

If you prefer to deploy manually or troubleshoot issues, follow these steps:

### 1. Build Docker Image

```bash
cd /Users/foo/projects/api-blogwriting-python-gcr-1
docker build -t blog-writer-api .
```

**Expected Output:**
```
Successfully built abc123def456
Successfully tagged blog-writer-api:latest
```

### 2. Tag Image for Google Container Registry

```bash
# Replace YOUR_PROJECT_ID with your actual project ID
docker tag blog-writer-api gcr.io/YOUR_PROJECT_ID/blog-writer-api:latest
```

### 3. Push Image to GCR

```bash
docker push gcr.io/YOUR_PROJECT_ID/blog-writer-api:latest
```

**Troubleshooting:**
- If you get permission denied, run: `gcloud auth configure-docker`
- If push fails, verify your project ID is correct

### 4. Deploy to Cloud Run

```bash
gcloud run deploy blog-writer-api \
  --image gcr.io/YOUR_PROJECT_ID/blog-writer-api:latest \
  --platform managed \
  --region europe-west9 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 900 \
  --concurrency 80 \
  --min-instances 0 \
  --max-instances 10 \
  --set-env-vars "ENVIRONMENT=production,LOG_LEVEL=INFO"
```

**Expected Output:**
```
Service [blog-writer-api] revision [blog-writer-api-00001-xxx] has been deployed
Service URL: https://blog-writer-api-xxxx-ew.a.run.app
```

### 5. Seed Firestore with Default Templates

```bash
# Make sure Firebase credentials are set
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"

# Run seed script
python scripts/seed_default_prompts_firestore.py
```

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

---

## Verification Steps

### 1. Check Service Health

```bash
# Get your service URL
SERVICE_URL=$(gcloud run services describe blog-writer-api \
  --platform managed \
  --region europe-west9 \
  --format="value(status.url)")

# Test health endpoint
curl $SERVICE_URL/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-01-01T12:00:00Z"
}
```

### 2. View API Documentation

Open in browser:
```
https://your-service-url.run.app/docs
```

You should see the interactive Swagger UI with all API endpoints.

### 3. Test Prompt Management API

```bash
# List writing styles
curl $SERVICE_URL/api/v1/prompts/styles

# Get merged config
curl "$SERVICE_URL/api/v1/prompts/merged-config?style_id=natural_conversational"
```

### 4. Test Blog Generation

```bash
curl -X POST "$SERVICE_URL/api/v1/blog/generate-enhanced" \
  -H "Content-Type: application/json" \
  -d '{
    "primary_keyword": "test keyword",
    "target_word_count": 1000,
    "tone": "friendly",
    "writing_style_id": "natural_conversational"
  }'
```

**Expected Response:**
```json
{
  "job_id": "job_abc123",
  "status": "processing",
  "message": "Blog generation started"
}
```

---

## Environment Variables

### Required for Backend

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to Firebase service account key | `/path/to/key.json` | Yes* |
| `FIREBASE_SERVICE_ACCOUNT_KEY_BASE64` | Base64-encoded service account key | `eyJwcm9qZWN0X2lk...` | Yes* |
| `FIREBASE_SERVICE_ACCOUNT_KEY_PATH` | Alternative path to service account key | `/app/keys/sa.json` | Yes* |

*One of these three is required

### Optional Configuration

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `ENVIRONMENT` | Deployment environment | `development` | `production` |
| `LOG_LEVEL` | Logging level | `INFO` | `DEBUG` |
| `GCP_PROJECT_ID` | Google Cloud project ID | - | `my-project-123` |
| `PORT` | Server port | `8080` | `8080` |

---

## Firestore Setup

### 1. Create Firestore Database

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project
3. Navigate to **Firestore Database**
4. Click **Create Database**
5. Choose **Production Mode** (we'll use security rules)
6. Select your preferred region

### 2. Deploy Security Rules

```bash
# Deploy Firestore security rules
firebase deploy --only firestore:rules
```

Or manually copy rules from `firestore.rules` to Firebase Console:
1. Go to Firestore Database → Rules
2. Copy contents of `firestore.rules`
3. Publish rules

### 3. Create Service Account

1. Go to [GCP Console](https://console.cloud.google.com/)
2. Navigate to **IAM & Admin → Service Accounts**
3. Click **Create Service Account**
4. Name: `blog-writer-firebase-admin`
5. Grant roles:
   - **Cloud Datastore User**
   - **Firebase Admin SDK Administrator Service Agent**
6. Create and download JSON key
7. Save securely and set as environment variable

---

## Troubleshooting

### Issue: "Firebase credentials not found"

**Symptoms:**
```
Error: Firebase credentials not found. Set GOOGLE_APPLICATION_CREDENTIALS...
```

**Solutions:**
1. Verify environment variable is set:
   ```bash
   echo $GOOGLE_APPLICATION_CREDENTIALS
   ```
2. Verify file exists:
   ```bash
   ls -la $GOOGLE_APPLICATION_CREDENTIALS
   ```
3. Verify file is valid JSON:
   ```bash
   cat $GOOGLE_APPLICATION_CREDENTIALS | jq .
   ```

### Issue: "Permission denied" when pushing to GCR

**Symptoms:**
```
denied: Permission "storage.buckets.get" denied on resource
```

**Solutions:**
1. Configure Docker authentication:
   ```bash
   gcloud auth configure-docker
   ```
2. Verify project ID is correct:
   ```bash
   gcloud config get-value project
   ```
3. Verify you have necessary permissions:
   ```bash
   gcloud projects get-iam-policy YOUR_PROJECT_ID
   ```

### Issue: "Service already exists" error

**Symptoms:**
```
ERROR: Service [blog-writer-api] already exists
```

**Solutions:**
1. Update existing service instead of creating new one
2. Use `--update` flag or run deploy command again
3. Or delete existing service first:
   ```bash
   gcloud run services delete blog-writer-api --region europe-west9
   ```

### Issue: Seed script fails with Firestore errors

**Symptoms:**
```
Error: Could not reach Firestore backend
```

**Solutions:**
1. Verify Firestore database is created
2. Check service account has correct permissions
3. Verify network connectivity:
   ```bash
   ping firestore.googleapis.com
   ```
4. Check Firebase project ID matches:
   ```bash
   cat $GOOGLE_APPLICATION_CREDENTIALS | jq .project_id
   ```

### Issue: Cloud Run deployment fails

**Symptoms:**
```
ERROR: (gcloud.run.deploy) INVALID_ARGUMENT: The request has errors
```

**Solutions:**
1. Check Docker image exists in GCR:
   ```bash
   gcloud container images list --repository=gcr.io/YOUR_PROJECT_ID
   ```
2. Verify region is supported:
   ```bash
   gcloud run regions list
   ```
3. Check quotas and billing:
   - Verify billing is enabled
   - Check Cloud Run quotas

---

## CI/CD Integration

### GitHub Actions

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Cloud Run

on:
  push:
    branches:
      - main
      - production

env:
  GCP_PROJECT_ID: ${{ secrets.GCP_PROJECT_ID }}
  GCP_REGION: europe-west9
  SERVICE_NAME: blog-writer-api

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Setup Cloud SDK
        uses: google-github-actions/setup-gcloud@v1
        with:
          service_account_key: ${{ secrets.GCP_SA_KEY }}
          project_id: ${{ secrets.GCP_PROJECT_ID }}
          export_default_credentials: true
      
      - name: Configure Docker
        run: gcloud auth configure-docker
      
      - name: Build Docker image
        run: docker build -t gcr.io/$GCP_PROJECT_ID/$SERVICE_NAME:$GITHUB_SHA .
      
      - name: Push to GCR
        run: docker push gcr.io/$GCP_PROJECT_ID/$SERVICE_NAME:$GITHUB_SHA
      
      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy $SERVICE_NAME \
            --image gcr.io/$GCP_PROJECT_ID/$SERVICE_NAME:$GITHUB_SHA \
            --platform managed \
            --region $GCP_REGION \
            --allow-unauthenticated \
            --memory 2Gi \
            --cpu 2
      
      - name: Seed Firestore
        run: |
          echo "${{ secrets.FIREBASE_SA_KEY_BASE64 }}" | base64 -d > /tmp/sa-key.json
          export GOOGLE_APPLICATION_CREDENTIALS=/tmp/sa-key.json
          python scripts/seed_default_prompts_firestore.py
```

**Required Secrets:**
- `GCP_PROJECT_ID`: Your Google Cloud project ID
- `GCP_SA_KEY`: Service account key JSON (base64 encoded)
- `FIREBASE_SA_KEY_BASE64`: Firebase service account key (base64 encoded)

---

## Rollback Procedures

### Rollback Cloud Run Deployment

```bash
# List revisions
gcloud run revisions list --service blog-writer-api --region europe-west9

# Rollback to previous revision
gcloud run services update-traffic blog-writer-api \
  --to-revisions REVISION_NAME=100 \
  --region europe-west9
```

### Restore Firestore Configuration

```bash
# Export current configuration
gcloud firestore export gs://YOUR_BACKUP_BUCKET/firestore-backup

# Import previous configuration
gcloud firestore import gs://YOUR_BACKUP_BUCKET/firestore-backup/TIMESTAMP
```

---

## Monitoring

### Cloud Run Metrics

View in GCP Console:
1. Navigate to **Cloud Run**
2. Click on service name
3. View **Metrics** tab

Key metrics:
- Request count
- Request latency (p50, p95, p99)
- Error rate
- CPU utilization
- Memory utilization

### Logs

```bash
# View recent logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=blog-writer-api" \
  --limit 50 \
  --format json

# Stream logs in real-time
gcloud logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=blog-writer-api"
```

### Alerts

Set up alerts in Cloud Monitoring:
1. Error rate > 5%
2. P95 latency > 5 seconds
3. Memory usage > 80%
4. Request count drops to 0

---

## Cost Optimization

### Cloud Run

- **Min instances**: Set to 0 to scale to zero when idle
- **Max instances**: Limit based on expected traffic
- **Memory**: Start with 2Gi, adjust based on usage
- **CPU**: Use 2 CPUs for better performance

### Firestore

- **Read/Write optimization**: Cache frequently accessed configs
- **Index management**: Only create necessary indexes
- **Batch operations**: Use batch writes where possible

### Estimated Costs (Monthly)

| Service | Usage | Cost |
|---------|-------|------|
| Cloud Run | 100K requests, 1GB-sec avg | ~$5-10 |
| Firestore | 1M reads, 100K writes | ~$2-5 |
| Cloud Storage (logs) | 10GB | ~$0.20 |
| **Total** | | **~$7-15/month** |

---

## Security Best Practices

1. **Service Account Permissions**: Use principle of least privilege
2. **API Authentication**: Implement API key or OAuth for production
3. **Firestore Security Rules**: Regularly audit and update
4. **Environment Variables**: Never commit secrets to git
5. **Network Security**: Use VPC connector if accessing private resources
6. **HTTPS Only**: Cloud Run enforces this by default
7. **Rate Limiting**: Implement rate limiting for public endpoints

---

## Support

### Getting Help

- **Documentation**: Check API docs at `/docs` endpoint
- **Logs**: Check Cloud Run logs for errors
- **Status**: Monitor service health at `/health` endpoint

### Useful Commands

```bash
# Get service URL
gcloud run services describe blog-writer-api --region europe-west9 --format="value(status.url)"

# View service configuration
gcloud run services describe blog-writer-api --region europe-west9

# Update service environment variables
gcloud run services update blog-writer-api \
  --region europe-west9 \
  --update-env-vars KEY=VALUE

# Scale service
gcloud run services update blog-writer-api \
  --region europe-west9 \
  --min-instances 1 \
  --max-instances 20
```

---

## Next Steps

After successful deployment:

1. ✅ **Test API endpoints** - Verify all endpoints work correctly
2. ✅ **Configure monitoring** - Set up alerts and dashboards
3. ✅ **Deploy frontend** - Deploy Admin Dashboard and Consumer Frontend
4. ✅ **Load test** - Test with expected traffic patterns
5. ✅ **Document for team** - Share deployment guide with team

---

**Last Updated:** January 1, 2026  
**Version:** 1.0  
**Status:** Production Ready 🚀




