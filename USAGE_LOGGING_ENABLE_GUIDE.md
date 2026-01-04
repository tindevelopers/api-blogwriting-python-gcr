# How to Enable Usage Logging

## Current Status

The production endpoint `/api/v1/admin/ai/costs` is returning:
```json
{
    "error": "Usage logging not enabled",
    "enabled": false
}
```

This means usage logging is currently disabled. Here's how to enable it.

---

## Option 1: Enable Firestore Usage Logging (Recommended for Cloud Run)

Firestore usage logging is recommended for Cloud Run deployments because:
- ✅ Uses Cloud Run's default service account (no additional credentials needed)
- ✅ Automatically available when Firebase is configured
- ✅ No Supabase dependency required

### Steps to Enable:

1. **Set Environment Variable in Cloud Run**

```bash
gcloud run services update blog-writer-api-prod \
  --region us-east1 \
  --project 613248238610 \
  --set-env-vars FIRESTORE_USAGE_LOGGING_ENABLED=true \
  --set-env-vars ENVIRONMENT=prod
```

Or if you prefer the alternative env var name:
```bash
gcloud run services update blog-writer-api-prod \
  --region us-east1 \
  --project 613248238610 \
  --set-env-vars USE_FIRESTORE_USAGE_LOGGING=true \
  --set-env-vars ENVIRONMENT=prod
```

2. **Verify Firebase Project ID is Set**

The service needs to know which Firebase project to use:
```bash
gcloud run services update blog-writer-api-prod \
  --region us-east1 \
  --project 613248238610 \
  --set-env-vars GOOGLE_CLOUD_PROJECT=613248238610
```

3. **Ensure Cloud Run Service Account has Firestore Permissions**

The Cloud Run service account needs these roles:
- `roles/datastore.user` (Cloud Datastore User)
- `roles/firebase.admin` (Firebase Admin SDK Administrator Service Agent)

Check current permissions:
```bash
gcloud projects get-iam-policy 613248238610 \
  --flatten="bindings[].members" \
  --filter="bindings.members:*@cloudbuild.gserviceaccount.com OR bindings.members:*compute@developer.gserviceaccount.com"
```

Grant permissions if needed:
```bash
# Get the service account email
SERVICE_ACCOUNT=$(gcloud run services describe blog-writer-api-prod \
  --region us-east1 \
  --project 613248238610 \
  --format="value(spec.template.spec.serviceAccountName)")

# Grant Firestore permissions
gcloud projects add-iam-policy-binding 613248238610 \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/datastore.user"

gcloud projects add-iam-policy-binding 613248238610 \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/firebase.admin"
```

4. **Verify Firestore Database Exists**

Ensure Firestore is enabled in your project:
```bash
gcloud firestore databases list --project=613248238610
```

If not enabled, create it:
```bash
gcloud firestore databases create --region=us-east1 --project=613248238610
```

---

## Option 2: Enable Supabase Usage Logging

If you prefer to use Supabase for usage logging:

### Steps to Enable:

1. **Set Supabase Environment Variables**

```bash
# First, get your Supabase credentials from Secret Manager or set them directly
gcloud run services update blog-writer-api-prod \
  --region us-east1 \
  --project 613248238610 \
  --set-env-vars SUPABASE_URL=https://your-project.supabase.co \
  --set-env-vars SUPABASE_SERVICE_ROLE_KEY=your-service-role-key \
  --set-env-vars ENVIRONMENT=prod
```

Or use secrets from Secret Manager:
```bash
gcloud run services update blog-writer-api-prod \
  --region us-east1 \
  --project 613248238610 \
  --update-secrets SUPABASE_URL=SUPABASE_URL:latest,SUPABASE_SERVICE_ROLE_KEY=SUPABASE_SERVICE_ROLE_KEY:latest \
  --set-env-vars ENVIRONMENT=prod
```

2. **Ensure Supabase Tables Exist**

Run the migration script to create the usage logs tables:
```bash
# The migration file is at: migrations/ai_usage_tracking.sql
# Execute it in your Supabase SQL Editor
```

The migration creates tables:
- `ai_usage_logs_dev`
- `ai_usage_logs_staging`
- `ai_usage_logs_prod`

---

## Verification

After enabling usage logging, verify it's working:

1. **Check Admin Status Endpoint**
```bash
curl "https://blog-writer-api-prod-613248238610.us-east1.run.app/api/v1/admin/status" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Look for:
```json
{
  "services": {
    "usage_logging": "enabled"
  }
}
```

2. **Test Cost Endpoint**
```bash
curl "https://blog-writer-api-prod-613248238610.us-east1.run.app/api/v1/admin/ai/costs?org_id=default&days=30" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

You should now get cost data instead of the "not enabled" error.

3. **Check Logs**
```bash
gcloud logging read "resource.type=cloud_run_revision AND \
  resource.labels.service_name=blog-writer-api-prod AND \
  jsonPayload.message=~'UsageLogger initialized'" \
  --limit 5 \
  --project 613248238610
```

---

## How It Works

### Firestore Usage Logger

- **Collection Name**: `ai_usage_logs_{environment}` (e.g., `ai_usage_logs_prod`)
- **Automatic Initialization**: Enabled when:
  - `FIRESTORE_USAGE_LOGGING_ENABLED=true` OR `USE_FIRESTORE_USAGE_LOGGING=true`
  - OR Supabase credentials are missing but Firebase is available
- **Credentials**: Uses Cloud Run's default service account automatically

### Supabase Usage Logger

- **Table Name**: `ai_usage_logs_{environment}` (e.g., `ai_usage_logs_prod`)
- **Automatic Initialization**: Enabled when:
  - `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` are set
  - Supabase package is installed
- **Credentials**: Requires explicit Supabase credentials

---

## Troubleshooting

### Issue: Still shows "Usage logging not enabled"

**Check:**
1. Environment variables are set correctly:
   ```bash
   gcloud run services describe blog-writer-api-prod \
     --region us-east1 \
     --project 613248238610 \
     --format="value(spec.template.spec.containers[0].env)"
   ```

2. Service was restarted after env var changes:
   ```bash
   # Force a new revision
   gcloud run services update blog-writer-api-prod \
     --region us-east1 \
     --project 613248238610 \
     --no-traffic
   ```

3. Check application logs for initialization errors:
   ```bash
   gcloud logging read "resource.type=cloud_run_revision AND \
     resource.labels.service_name=blog-writer-api-prod" \
     --limit 50 \
     --project 613248238610
   ```

### Issue: "Failed to initialize Firestore client"

**Solutions:**
1. Verify Firestore is enabled in the project
2. Check service account has correct permissions
3. Verify `GOOGLE_CLOUD_PROJECT` or `FIREBASE_PROJECT_ID` is set

### Issue: "Supabase credentials not configured"

**Solutions:**
1. Verify `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` are set
2. Check secrets are mounted correctly if using Secret Manager
3. Verify Supabase package is installed in requirements.txt

---

## Quick Enable Command (Firestore)

Run this single command to enable Firestore usage logging:

```bash
gcloud run services update blog-writer-api-prod \
  --region us-east1 \
  --project 613248238610 \
  --set-env-vars FIRESTORE_USAGE_LOGGING_ENABLED=true \
  --set-env-vars ENVIRONMENT=prod \
  --set-env-vars GOOGLE_CLOUD_PROJECT=613248238610
```

Then wait ~30 seconds for the new revision to deploy and test the endpoint again.

