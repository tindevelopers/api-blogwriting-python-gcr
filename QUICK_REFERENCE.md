# Quick Reference Guide - Blog Writer API

**Version:** 1.0 | **Date:** January 1, 2026 | **Status:** ✅ Production Ready

---

## 🚀 Quick Deploy (3 Steps)

```bash
# 1. Set Firebase credentials
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"

# 2. Authenticate with Google Cloud
gcloud auth login
gcloud auth configure-docker

# 3. Run deployment
./scripts/deploy.sh
# → Select option 1 (Full deployment)
```

**That's it!** Your API will be live in ~5-10 minutes.

---

## 📋 Prerequisites Checklist

Before deploying, ensure you have:

- [ ] Google Cloud project with billing enabled
- [ ] Firebase project created (can be same as GCP)
- [ ] Firestore database created in Firebase Console
- [ ] Service account JSON key downloaded
- [ ] Docker installed and running
- [ ] gcloud CLI installed and configured
- [ ] Required environment variables set

---

## 🔑 Essential Commands

### Deployment

```bash
# Full deployment (first time)
./scripts/deploy.sh

# Quick redeploy (after code changes)
./scripts/deploy.sh  # Option 4 (Deploy only)

# Seed Firestore only
python3 scripts/seed_default_prompts_firestore.py
```

### Testing

```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe blog-writer-api \
  --region europe-west9 --format="value(status.url)")

# Test health
curl $SERVICE_URL/health

# Test API
curl $SERVICE_URL/docs
curl $SERVICE_URL/api/v1/prompts/styles
```

### Monitoring

```bash
# View logs
gcloud logging tail "resource.type=cloud_run_revision AND \
  resource.labels.service_name=blog-writer-api"

# Check service status
gcloud run services describe blog-writer-api --region europe-west9
```

---

## 🔧 Environment Variables

### Required (pick one)

```bash
# Option 1: File path (recommended)
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/sa-key.json"

# Option 2: Base64 encoded
export FIREBASE_SERVICE_ACCOUNT_KEY_BASE64="eyJwcm9qZWN0..."

# Option 3: Alternative file path
export FIREBASE_SERVICE_ACCOUNT_KEY_PATH="/path/to/sa-key.json"
```

### Optional

```bash
export GCP_PROJECT_ID="your-project-id"        # Default: blog-writer-dev
export GCP_REGION="europe-west9"               # Default: europe-west9
export SERVICE_NAME="blog-writer-api"          # Default: blog-writer-api
```

---

## 📊 API Endpoints

### Prompt Management

```bash
# List all writing styles
GET /api/v1/prompts/styles

# Get specific style
GET /api/v1/prompts/styles/{style_id}

# Create new style
POST /api/v1/prompts/styles

# Update style
PUT /api/v1/prompts/styles/{style_id}

# Get merged config
GET /api/v1/prompts/merged-config?style_id={style_id}

# List prompt configs
GET /api/v1/prompts/configs

# Create prompt config
POST /api/v1/prompts/configs
```

### Blog Generation

```bash
# Generate blog with default style
POST /api/v1/blog/generate-enhanced
{
  "primary_keyword": "your keyword",
  "target_word_count": 2000,
  "tone": "friendly"
}

# Generate with specific style
POST /api/v1/blog/generate-enhanced
{
  "primary_keyword": "your keyword",
  "target_word_count": 2000,
  "writing_style_id": "natural_conversational"
}

# Generate with overrides
POST /api/v1/blog/generate-enhanced
{
  "primary_keyword": "your keyword",
  "target_word_count": 2000,
  "writing_style_overrides": {
    "formality_level": 4,
    "use_contractions": true,
    "engagement_style": "conversational"
  }
}
```

---

## 🗄️ Firestore Collections

### `prompt_configs`

Default config: `default_natural_conversational`

**Key Fields:**
- `config_id` (string)
- `name` (string)
- `config_data` (map) - Contains all writing settings
- `is_default` (boolean)
- `tenant_id` (string, optional)

### `writing_styles`

Default style: `natural_conversational`

**Key Fields:**
- `style_id` (string)
- `name` (string)
- `prompt_config_id` (string) - Links to config
- `is_default` (boolean)
- `tenant_id` (string, optional)

---

## ⚙️ Configuration Options

| Setting | Type | Range | Default |
|---------|------|-------|---------|
| `formality_level` | number | 1-10 | 6 |
| `use_contractions` | boolean | - | true |
| `avoid_obvious_transitions` | boolean | - | true |
| `conclusion_style` | string | natural_wrap_up, summary, call_to_action, open_ended | natural_wrap_up |
| `engagement_style` | string | conversational, professional, authoritative, analytical | conversational |
| `personality` | string | friendly, authoritative, analytical, conversational | friendly |
| `use_first_person` | boolean | - | false |

---

## 🐛 Quick Troubleshooting

### Firebase errors
```bash
# Verify credentials
echo $GOOGLE_APPLICATION_CREDENTIALS
cat $GOOGLE_APPLICATION_CREDENTIALS | jq .project_id
```

### Docker errors
```bash
# Check Docker is running
docker ps

# Rebuild image
docker build -t blog-writer-api . --no-cache
```

### GCR errors
```bash
# Re-authenticate
gcloud auth configure-docker
gcloud config set project YOUR_PROJECT_ID
```

### Deployment fails
```bash
# Check logs
gcloud logging read "resource.type=cloud_run_revision" --limit 50

# Check service status
gcloud run services describe blog-writer-api --region europe-west9
```

---

## 📁 Project Structure

```
/Users/foo/projects/api-blogwriting-python-gcr-1/
├── main.py                          # FastAPI application
├── requirements.txt                 # Python dependencies
├── Dockerfile                       # Container definition
├── firestore_schema.md              # Database schema
├── firestore.rules                  # Security rules
│
├── src/blog_writer_sdk/
│   ├── integrations/
│   │   └── firebase_config_client.py    # Firestore client
│   ├── models/
│   │   └── prompt_config_models.py      # Pydantic models
│   ├── services/
│   │   └── prompt_config_service.py     # Business logic
│   ├── api/
│   │   └── prompt_management.py         # API endpoints
│   └── ai/
│       └── enhanced_prompts.py          # Natural writing prompts
│
├── scripts/
│   ├── deploy.sh                        # Deployment script
│   ├── seed_default_prompts_firestore.py  # Seed script
│   └── README.md                        # Scripts documentation
│
└── docs/
    ├── DEPLOYMENT_GUIDE.md              # Full deployment guide
    ├── IMPLEMENTATION_SUMMARY.md        # System overview
    ├── FRONTEND_WRITING_STYLE_CONFIGURATION.md  # Admin Dashboard
    ├── FRONTEND_PER_BLOG_CUSTOMIZATION.md       # Consumer Frontend
    └── QUICK_REFERENCE.md              # This file
```

---

## 🎯 Next Steps After Deployment

1. **Verify Deployment**
   ```bash
   curl $SERVICE_URL/health
   curl $SERVICE_URL/docs
   ```

2. **Test Prompt Management**
   ```bash
   curl $SERVICE_URL/api/v1/prompts/styles
   ```

3. **Generate Test Blog**
   ```bash
   curl -X POST $SERVICE_URL/api/v1/blog/generate-enhanced \
     -H "Content-Type: application/json" \
     -d '{"primary_keyword": "test", "target_word_count": 1000}'
   ```

4. **Deploy Frontends**
   - Admin Dashboard: Use `FRONTEND_WRITING_STYLE_CONFIGURATION.md`
   - Consumer App: Use `FRONTEND_PER_BLOG_CUSTOMIZATION.md`

5. **Set Up Monitoring**
   - Cloud Run metrics in GCP Console
   - Set up alerts for errors and latency
   - Monitor Firestore usage

6. **Configure CI/CD**
   - See `DEPLOYMENT_GUIDE.md` for GitHub Actions example
   - Set up automated deployments

---

## 📚 Documentation Index

| Document | Purpose | Audience |
|----------|---------|----------|
| `QUICK_REFERENCE.md` | Quick commands and reference | Everyone |
| `DEPLOYMENT_GUIDE.md` | Complete deployment instructions | DevOps |
| `IMPLEMENTATION_SUMMARY.md` | System architecture and overview | Developers |
| `FRONTEND_WRITING_STYLE_CONFIGURATION.md` | Admin Dashboard specs | Frontend Team |
| `FRONTEND_PER_BLOG_CUSTOMIZATION.md` | Consumer Frontend specs | Frontend Team |
| `firestore_schema.md` | Database schema | Backend Team |
| `scripts/README.md` | Scripts documentation | Everyone |

---

## 🆘 Getting Help

### Documentation
- **API Docs**: `https://your-service-url.run.app/docs`
- **Project Docs**: See documentation index above

### Logs
```bash
# View recent errors
gcloud logging read "resource.type=cloud_run_revision \
  AND severity>=ERROR" --limit 20

# Stream live logs
gcloud logging tail "resource.type=cloud_run_revision"
```

### Service Status
```bash
# Get service URL and status
gcloud run services describe blog-writer-api \
  --region europe-west9 \
  --format="value(status.url, status.conditions)"
```

---

## 🔐 Security Checklist

- [ ] Service account has minimal required permissions
- [ ] Firestore security rules deployed
- [ ] Credentials stored securely (not in git)
- [ ] API authentication implemented (if needed)
- [ ] HTTPS enforced (automatic with Cloud Run)
- [ ] Rate limiting configured
- [ ] Monitoring and alerts set up
- [ ] Regular security audits scheduled

---

## 💰 Cost Estimates

**Monthly costs for moderate usage:**

| Service | Expected Cost |
|---------|---------------|
| Cloud Run | $5-10 |
| Firestore | $2-5 |
| Logs & Monitoring | $0.20 |
| **Total** | **~$7-15/month** |

---

## 📝 Common Workflows

### Update Backend Code

```bash
# 1. Make code changes
# 2. Test locally
docker build -t blog-writer-api .
docker run -p 8080:8080 blog-writer-api

# 3. Deploy
./scripts/deploy.sh  # Option 1 or 4
```

### Add New Writing Style

```bash
# Use API or admin dashboard
curl -X POST $SERVICE_URL/api/v1/prompts/configs \
  -H "Content-Type: application/json" \
  -d '{
    "config_id": "new_style",
    "name": "New Style",
    "config_data": {...}
  }'
```

### Update Default Template

```bash
# 1. Edit scripts/seed_default_prompts_firestore.py
# 2. Re-run seed script
python3 scripts/seed_default_prompts_firestore.py
```

### Rollback Deployment

```bash
# List revisions
gcloud run revisions list --service blog-writer-api --region europe-west9

# Route traffic to previous revision
gcloud run services update-traffic blog-writer-api \
  --to-revisions PREVIOUS_REVISION=100 \
  --region europe-west9
```

---

## ✅ Success Criteria

Your deployment is successful when:

- ✅ Health endpoint returns 200 OK
- ✅ API docs load at `/docs`
- ✅ Prompt management endpoints work
- ✅ Blog generation completes successfully
- ✅ Firestore contains default templates
- ✅ No errors in Cloud Run logs
- ✅ Service URL accessible from browser

---

## 🎉 Deployment Complete!

**What you've achieved:**
- ✅ Natural, human-like blog writing
- ✅ Dashboard-controlled prompts via Firestore
- ✅ Scalable Cloud Run deployment
- ✅ Flexible per-blog customization
- ✅ Production-ready API

**Ready to generate amazing blogs!** 🚀

---

**Version:** 1.0  
**Last Updated:** January 1, 2026  
**Status:** Production Ready ✅

