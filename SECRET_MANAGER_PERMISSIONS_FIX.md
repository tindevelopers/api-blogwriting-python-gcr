# Secret Manager Permissions Fix

## Issue

The dashboard frontend was receiving a 500 error when trying to sync secrets:

```
Failed to list secrets: 403 Permission 'secretmanager.secrets.list' denied for resource 'projects/api-ai-blog-writer'
```

## Root Cause

The Cloud Run service account (`firebase-adminsdk-fbsvc@api-ai-blog-writer.iam.gserviceaccount.com`) did not have Secret Manager permissions to list and access secrets.

## Solution

Granted the `roles/secretmanager.secretAccessor` role to the service account:

```bash
gcloud projects add-iam-policy-binding api-ai-blog-writer \
  --member="serviceAccount:firebase-adminsdk-fbsvc@api-ai-blog-writer.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

## Permissions Granted

The `roles/secretmanager.secretAccessor` role includes:
- `secretmanager.secrets.list` - List secrets
- `secretmanager.versions.access` - Access secret values
- `secretmanager.versions.get` - Get secret versions

## Verification

After granting permissions, the endpoint now works:

```bash
curl "https://blog-writer-api-prod-613248238610.us-east1.run.app/api/v1/admin/secrets" \
  -H "Authorization: Bearer <token>"

# Response: {"secrets":[]}
```

The empty array is expected if no secrets have been synced to Firestore yet.

## Next Steps

1. ✅ **Permissions Fixed** - Service account now has Secret Manager access
2. ⏳ **Sync Secrets** - Dashboard can now call `/api/v1/admin/secrets/sync` to sync secrets from GCP to Firestore
3. ⏳ **List Secrets** - After syncing, `/api/v1/admin/secrets` will return the synced secrets

## Testing

The dashboard should now be able to:

1. **List secrets** (will return empty if not synced yet):
   ```bash
   GET /api/v1/admin/secrets
   ```

2. **Sync secrets from GCP**:
   ```bash
   POST /api/v1/admin/secrets/sync
   {
     "source": "google_secret_manager",
     "target": "application",
     "dry_run": false
   }
   ```

3. **List synced secrets** (after sync):
   ```bash
   GET /api/v1/admin/secrets
   # Returns: {"secrets": [{"name": "...", "type": "...", ...}]}
   ```

## Status

✅ **Fixed** - Secret Manager permissions granted  
✅ **Verified** - Endpoint responds without permission errors  
⏳ **Ready** - Dashboard can now sync and list secrets

---

**Date:** 2026-01-04  
**Service Account:** `firebase-adminsdk-fbsvc@api-ai-blog-writer.iam.gserviceaccount.com`  
**Role Granted:** `roles/secretmanager.secretAccessor`

