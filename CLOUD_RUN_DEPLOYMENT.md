# Google Cloud Run Deployment Guide

This guide walks you through deploying the Blog Writer SDK to Google Cloud Run, providing a scalable, serverless solution for your AI-powered blog generation service.

## 🎯 Why Cloud Run?

- **Serverless & Auto-scaling**: Pay only when generating content
- **Global availability**: Serve applications worldwide
- **Container-native**: Uses your existing Docker setup
- **Cost-effective**: Perfect for variable AI workloads
- **Enterprise-ready**: Built-in monitoring, logging, and security

## 📋 Prerequisites

1. **Google Cloud Account**: [Create one here](https://cloud.google.com/)
2. **Google Cloud CLI**: [Install gcloud](https://cloud.google.com/sdk/docs/install)
3. **Docker**: For local testing (optional)
4. **API Keys**: OpenAI, Anthropic, DataForSEO, etc.

## 🚀 Quick Deployment

### Step 1: Setup Google Cloud Project

```bash
# Set your project ID
export GOOGLE_CLOUD_PROJECT="your-project-id"

# Authenticate with Google Cloud
gcloud auth login

# Set the project
gcloud config set project $GOOGLE_CLOUD_PROJECT

# Enable required APIs
gcloud services enable cloudbuild.googleapis.com run.googleapis.com secretmanager.googleapis.com
```

### Step 2: Configure Environment Variables

1. **Copy the Cloud Run environment template:**
   ```bash
   cp env.cloudrun env.cloudrun.local
   ```

2. **Edit `env.cloudrun.local` with your actual API keys:**
   ```bash
   # Required: Supabase Configuration
   SUPABASE_URL=https://your-project-id.supabase.co
   SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here
   
   # Required: At least one AI provider
   OPENAI_API_KEY=your_openai_api_key
   # OR
   ANTHROPIC_API_KEY=your_anthropic_api_key
   
   # Optional: Enhanced keyword analysis
   DATAFORSEO_API_KEY=your_dataforseo_api_key
   DATAFORSEO_API_SECRET=your_dataforseo_api_secret
   ```

### Step 3: Setup Secrets and Deploy

```bash
# Make scripts executable
chmod +x scripts/setup-secrets.sh scripts/deploy.sh scripts/setup-ai-provider-secrets.sh

# Setup Google Cloud secrets (general configuration)
./scripts/setup-secrets.sh

# Setup AI Provider secrets (CRITICAL for enhanced blog generation)
./scripts/setup-ai-provider-secrets.sh

# Deploy to Cloud Run
./scripts/deploy.sh
```

**⚠️ IMPORTANT:** The AI provider secrets setup is **REQUIRED** for the enhanced blog generation endpoint (`/api/v1/blog/generate-enhanced`) to work. Without it, the system falls back to template-based generation.

That's it! Your service will be deployed and accessible at the provided URL.

## ✅ Post-Deployment Verification (Versioned)

After a deployment, verify the new revision and API version:

```bash
# Check service URL (develop)
gcloud run services describe blog-writer-api-dev \
  --region=europe-west1 \
  --project=api-ai-blog-writer \
  --format="value(status.url)"

# Verify health shows version
curl -s https://<SERVICE_URL>/health | jq
# Expect: {"status":"healthy","version":"1.3.0-cloudrun", ...}

# Verify OpenAPI version
curl -s https://<SERVICE_URL>/openapi.json | jq -r '.info.version'
# Expect: 1.3.0
```

If your browser caches docs, force refresh or fetch `/openapi.json?ts=$(date +%s)`.

## 🆕 Latest Updates (Version 1.3.0 - 2025-11-13)

### New DataForSEO Endpoints
- **Google Trends Explore**: Real-time trend data for timely content (30-40% relevance improvement)
- **Keyword Ideas**: Category-based keyword discovery (25% more coverage)
- **Relevant Pages**: Content structure analysis (20-30% better structure)
- **Enhanced SERP Analysis**: Full SERP feature extraction (40-50% better targeting)

### AI-Powered Enhancements
- **SERP AI Summary**: LLM-powered SERP analysis (30-40% better structure)
- **LLM Responses API**: Multi-model fact-checking (25-35% better accuracy)
- **AI-Optimized Format**: Streamlined JSON responses (10-15% faster processing)

### Cost Impact
- Additional cost: ~$19-52/month for 1000 blogs
- Significant ROI through improved content quality and rankings

See [FRONTEND_API_IMPROVEMENTS_SUMMARY.md](FRONTEND_API_IMPROVEMENTS_SUMMARY.md) for complete details.

## 🔧 Manual Deployment

If you prefer manual control over the deployment process:

### 1. Create Service Account

```bash
# Create service account
gcloud iam service-accounts create blog-writer-service-account \
    --display-name="Blog Writer SDK Service Account"

# Grant permissions
gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
    --member="serviceAccount:blog-writer-service-account@$GOOGLE_CLOUD_PROJECT.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

### 2. Create Secrets

```bash
# Create secret from your environment file
gcloud secrets create blog-writer-env \
    --data-file=env.cloudrun.local

# Grant access to service account
gcloud secrets add-iam-policy-binding blog-writer-env \
    --member="serviceAccount:blog-writer-service-account@$GOOGLE_CLOUD_PROJECT.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

### 3. Build and Deploy

```bash
# Build with Cloud Build
gcloud builds submit --tag gcr.io/$GOOGLE_CLOUD_PROJECT/blog-writer-sdk

# Deploy to Cloud Run
gcloud run deploy blog-writer-sdk \
    --image gcr.io/$GOOGLE_CLOUD_PROJECT/blog-writer-sdk \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated \
    --port 8000 \
    --memory 2Gi \
    --cpu 2 \
    --min-instances 0 \
    --max-instances 100 \
    --concurrency 80 \
    --timeout 900 \
    --service-account blog-writer-service-account@$GOOGLE_CLOUD_PROJECT.iam.gserviceaccount.com \
    --set-env-vars PORT=8000,PYTHONUNBUFFERED=1 \
    --set-secrets /secrets/env=blog-writer-env:latest
```

## 🔄 GitHub Actions CI/CD

For automated deployments, set up GitHub Actions:

### 1. Create Service Account Key

```bash
# Create service account key
gcloud iam service-accounts keys create key.json \
    --iam-account blog-writer-service-account@$GOOGLE_CLOUD_PROJECT.iam.gserviceaccount.com

# Grant Cloud Build permissions
gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
    --member="serviceAccount:blog-writer-service-account@$GOOGLE_CLOUD_PROJECT.iam.gserviceaccount.com" \
    --role="roles/cloudbuild.builds.editor"

gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
    --member="serviceAccount:blog-writer-service-account@$GOOGLE_CLOUD_PROJECT.iam.gserviceaccount.com" \
    --role="roles/run.admin"

gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
    --member="serviceAccount:blog-writer-service-account@$GOOGLE_CLOUD_PROJECT.iam.gserviceaccount.com" \
    --role="roles/iam.serviceAccountUser"
```

### 2. Add GitHub Secrets

In your GitHub repository settings, add these secrets:

- `GOOGLE_CLOUD_PROJECT`: Your Google Cloud project ID
- `GOOGLE_CLOUD_SA_KEY`: Contents of the `key.json` file

### 3. Workflow Configuration

The workflow file `.github/workflows/deploy-cloudrun.yml` is already configured and will:

- Deploy to production on pushes to `main`
- Create staging environments for pull requests
- Run health checks after deployment
- Clean up staging environments when PRs are closed

## 📊 Monitoring and Observability

### Health Check Endpoints

Your deployed service includes several health check endpoints:

- **`/health`**: Basic health check for load balancers
- **`/ready`**: Readiness probe (checks AI providers, database)
- **`/live`**: Liveness probe (simple responsiveness check)
- **`/api/v1/cloudrun/status`**: Detailed Cloud Run status and metrics

### Monitoring Commands

```bash
# View service details
gcloud run services describe blog-writer-sdk --region=us-central1

# View logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=blog-writer-sdk" --limit=50

# Monitor metrics
gcloud monitoring metrics list --filter="resource.type=cloud_run_revision"
```

### Cloud Console

Monitor your service in the [Google Cloud Console](https://console.cloud.google.com/run):

- **Metrics**: Request count, latency, error rate
- **Logs**: Application and system logs
- **Revisions**: Traffic splitting and rollback
- **Security**: IAM and VPC settings

## 🔒 Security Best Practices

### 1. Service Account Permissions

Use the principle of least privilege:

```bash
# Only grant necessary permissions
gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
    --member="serviceAccount:blog-writer-service-account@$GOOGLE_CLOUD_PROJECT.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

### 2. Network Security

For enhanced security, consider:

```bash
# Deploy with ingress control
gcloud run services update blog-writer-sdk \
    --ingress=internal-and-cloud-load-balancing \
    --region=us-central1
```

### 3. VPC Connector (Optional)

For private network access:

```bash
# Create VPC connector
gcloud compute networks vpc-access connectors create blog-writer-connector \
    --region=us-central1 \
    --subnet=default \
    --subnet-project=$GOOGLE_CLOUD_PROJECT \
    --min-instances=2 \
    --max-instances=10

# Update service to use VPC connector
gcloud run services update blog-writer-sdk \
    --vpc-connector=blog-writer-connector \
    --vpc-egress=private-ranges-only \
    --region=us-central1
```

## 💰 Cost Optimization

### Resource Configuration

Optimize costs by right-sizing your service:

```bash
# For light workloads
gcloud run services update blog-writer-sdk \
    --memory=1Gi \
    --cpu=1 \
    --max-instances=10

# For heavy workloads
gcloud run services update blog-writer-sdk \
    --memory=4Gi \
    --cpu=2 \
    --max-instances=100
```

### Auto-scaling Settings

```bash
# Minimize cold starts for production
gcloud run services update blog-writer-sdk \
    --min-instances=1 \
    --max-instances=50

# Cost-optimized for development
gcloud run services update blog-writer-sdk \
    --min-instances=0 \
    --max-instances=10
```

## 🧪 Testing Your Deployment

### Basic Health Check

```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe blog-writer-sdk \
    --region=us-central1 \
    --format="value(status.url)")

# Test health endpoint
curl $SERVICE_URL/health

# Test API configuration
curl $SERVICE_URL/api/v1/config
```

### Generate a Blog Post

```bash
# Test blog generation
curl -X POST $SERVICE_URL/api/v1/generate \
    -H "Content-Type: application/json" \
    -d '{
        "topic": "Getting Started with Cloud Run",
        "keywords": ["cloud run", "serverless", "google cloud"],
        "tone": "professional",
        "length": "medium"
    }'
```

### Load Testing

```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Run load test
ab -n 100 -c 10 $SERVICE_URL/health
```

## 🔧 Troubleshooting

### Common Issues

1. **Secret Access Denied**
   ```bash
   # Check service account permissions
   gcloud secrets get-iam-policy blog-writer-env
   ```

2. **Memory Limits**
   ```bash
   # Increase memory allocation
   gcloud run services update blog-writer-sdk --memory=4Gi
   ```

3. **Cold Start Timeouts**
   ```bash
   # Increase timeout and min instances
   gcloud run services update blog-writer-sdk \
       --timeout=900 \
       --min-instances=1
   ```

### Debug Commands

```bash
# View detailed service configuration
gcloud run services describe blog-writer-sdk \
    --region=us-central1 \
    --format=export

# Check recent deployments
gcloud run revisions list \
    --service=blog-writer-sdk \
    --region=us-central1

# View build history
gcloud builds list --limit=10
```

## 📈 Scaling and Performance

### Horizontal Scaling

Cloud Run automatically scales based on:
- **Request volume**: More requests = more instances
- **CPU utilization**: High CPU = new instances
- **Memory usage**: Memory pressure triggers scaling

### Performance Tuning

1. **Concurrency Settings**
   ```bash
   # Optimize for CPU-bound tasks
   gcloud run services update blog-writer-sdk --concurrency=10
   
   # Optimize for I/O-bound tasks
   gcloud run services update blog-writer-sdk --concurrency=100
   ```

2. **Resource Allocation**
   ```bash
   # For AI-heavy workloads
   gcloud run services update blog-writer-sdk \
       --memory=4Gi \
       --cpu=2
   ```

3. **Caching Strategy**
   - Use Redis (Cloud Memorystore) for keyword analysis caching
   - Enable HTTP caching headers for static responses
   - Cache AI provider responses when appropriate

## 🌍 Multi-Region Deployment

Deploy to multiple regions for global availability:

```bash
# Deploy to multiple regions
for region in us-central1 europe-west1 asia-southeast1; do
    gcloud run deploy blog-writer-sdk \
        --image gcr.io/$GOOGLE_CLOUD_PROJECT/blog-writer-sdk \
        --region=$region \
        --platform=managed \
        --allow-unauthenticated
done

# Use Global Load Balancer for traffic distribution
gcloud compute backend-services create blog-writer-backend \
    --global \
    --load-balancing-scheme=EXTERNAL_MANAGED
```

## 🔄 Blue-Green Deployments

Implement zero-downtime deployments:

```bash
# Deploy new revision without traffic
gcloud run deploy blog-writer-sdk \
    --image gcr.io/$GOOGLE_CLOUD_PROJECT/blog-writer-sdk:new-version \
    --no-traffic \
    --tag=blue

# Test the new revision
curl https://blue---blog-writer-sdk-xxx-uc.a.run.app/health

# Gradually shift traffic
gcloud run services update-traffic blog-writer-sdk \
    --to-tags=blue=50

# Complete the migration
gcloud run services update-traffic blog-writer-sdk \
    --to-tags=blue=100
```

## 📞 Support and Resources

- **Documentation**: [Cloud Run Docs](https://cloud.google.com/run/docs)
- **Pricing**: [Cloud Run Pricing](https://cloud.google.com/run/pricing)
- **Monitoring**: [Cloud Monitoring](https://cloud.google.com/monitoring)
- **Support**: [Google Cloud Support](https://cloud.google.com/support)

## 🎉 Next Steps

After successful deployment:

1. **Set up monitoring alerts** for error rates and latency
2. **Configure custom domains** for production use
3. **Implement API authentication** for production security
4. **Set up backup and disaster recovery** procedures
5. **Optimize costs** based on usage patterns

Your Blog Writer SDK is now running on Google Cloud Run, ready to serve AI-powered blog generation requests at scale!

