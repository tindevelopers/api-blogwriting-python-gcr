# 🔐 API Access Control Guide

## Current Status: APIs are PUBLICLY ACCESSIBLE

Your APIs are currently deployed with `--allow-unauthenticated`, meaning anyone can access them without credentials.

## 🔑 Authentication Options

### Option 1: API Key Authentication (Recommended)

#### Step 1: Generate API Keys
```bash
# Generate a new API key
API_KEY=$(openssl rand -hex 32)
echo "Generated API Key: $API_KEY"

# Store in Secret Manager
echo "$API_KEY" | gcloud secrets versions add api-keys --data-file=- --project=api-ai-blog-writer
```

#### Step 2: Update Your API to Require API Keys
Add API key validation to your FastAPI application:

```python
from fastapi import HTTPException, Depends, Header
from typing import Optional

async def verify_api_key(x_api_key: Optional[str] = Header(None)):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    # Validate against stored keys in Secret Manager
    # Implementation depends on your validation logic
    
    return x_api_key

# Use in your endpoints
@app.get("/api/v1/generate")
async def generate_content(api_key: str = Depends(verify_api_key)):
    # Your existing logic
    pass
```

#### Step 3: Client Usage
```bash
# Using curl
curl -H "X-API-Key: YOUR_API_KEY" \
     https://api-ai-blog-writer-kq42l26tuq-ue.a.run.app/api/v1/generate

# Using Python requests
import requests

headers = {"X-API-Key": "YOUR_API_KEY"}
response = requests.get(
    "https://api-ai-blog-writer-kq42l26tuq-ue.a.run.app/api/v1/generate",
    headers=headers
)
```

### Option 2: Google Cloud IAM Authentication

#### Step 1: Remove Public Access
```bash
# Remove public access
gcloud run services remove-iam-policy-binding api-ai-blog-writer \
    --region=us-east1 \
    --member="allUsers" \
    --role="roles/run.invoker" \
    --project=api-ai-blog-writer
```

#### Step 2: Grant Access to Specific Users/Service Accounts
```bash
# Grant access to a specific user
gcloud run services add-iam-policy-binding api-ai-blog-writer \
    --region=us-east1 \
    --member="user:someone@example.com" \
    --role="roles/run.invoker" \
    --project=api-ai-blog-writer

# Grant access to a service account
gcloud run services add-iam-policy-binding api-ai-blog-writer \
    --region=us-east1 \
    --member="serviceAccount:external-app@project.iam.gserviceaccount.com" \
    --role="roles/run.invoker" \
    --project=api-ai-blog-writer
```

#### Step 3: Client Authentication
```bash
# Using gcloud auth
gcloud auth application-default login

# Using service account key
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account-key.json"

# Making authenticated requests
curl -H "Authorization: Bearer $(gcloud auth print-access-token)" \
     https://api-ai-blog-writer-kq42l26tuq-ue.a.run.app/api/v1/generate
```

### Option 3: OAuth 2.0 / JWT Authentication

For more sophisticated authentication, implement OAuth 2.0 or JWT token validation in your FastAPI application.

## 🛡️ Security Best Practices

### 1. Rate Limiting
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/api/v1/generate")
@limiter.limit("10/minute")
async def generate_content(request: Request):
    # Your logic
    pass
```

### 2. CORS Configuration
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific domains only
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

### 3. Environment-Specific Access
- **Development**: Keep open for testing
- **Staging**: API key authentication
- **Production**: Full IAM authentication

## 📋 Quick Setup Commands

### For API Key Authentication:
```bash
# 1. Generate and store API key
API_KEY=$(openssl rand -hex 32)
echo "$API_KEY" | gcloud secrets versions add api-keys --data-file=- --project=api-ai-blog-writer

# 2. Update your application code to validate API keys
# 3. Redeploy with authentication enabled
./scripts/deploy-simple.sh prod
```

### For IAM Authentication:
```bash
# 1. Remove public access
gcloud run services remove-iam-policy-binding api-ai-blog-writer \
    --region=us-east1 \
    --member="allUsers" \
    --role="roles/run.invoker" \
    --project=api-ai-blog-writer

# 2. Add specific users/service accounts
gcloud run services add-iam-policy-binding api-ai-blog-writer \
    --region=us-east1 \
    --member="user:client@example.com" \
    --role="roles/run.invoker" \
    --project=api-ai-blog-writer
```

## 🔍 Monitoring and Logging

```bash
# View access logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=api-ai-blog-writer" \
    --project=api-ai-blog-writer \
    --limit=50

# Monitor API usage
gcloud run services describe api-ai-blog-writer \
    --region=us-east1 \
    --project=api-ai-blog-writer
```

## 🚨 Important Security Notes

1. **Never commit API keys to version control**
2. **Use environment variables for sensitive data**
3. **Implement proper error handling for authentication failures**
4. **Monitor API usage and set up alerts for unusual activity**
5. **Regularly rotate API keys**
6. **Use HTTPS only (already configured with Cloud Run)**

## 📞 Support

For questions about implementing authentication, refer to:
- [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/)
- [Google Cloud Run IAM Documentation](https://cloud.google.com/run/docs/authenticating)
- [Cloud Secret Manager Documentation](https://cloud.google.com/secret-manager/docs)

