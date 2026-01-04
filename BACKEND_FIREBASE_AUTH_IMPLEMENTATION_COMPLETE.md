# Backend Firebase Authentication Implementation - Complete

## ✅ Implementation Summary

The backend has been updated to support Firebase ID token authentication for admin endpoints, specifically for the secrets management API used by the dashboard frontend.

---

## 🔧 Changes Made

### 1. Firebase Token Verification (`src/blog_writer_sdk/services/auth_service.py`)

**Added:**
- Firebase Admin SDK import and initialization check
- `verify_token()` method now supports both Firebase and Supabase tokens
- Firebase token verification tries first, falls back to Supabase
- `_get_firebase_user_profile()` method to get user roles from Firestore

**How it works:**
1. Receives token in `Authorization: Bearer <token>` header
2. Tries Firebase token verification first
3. If Firebase fails, falls back to Supabase verification
4. Gets user role from Firestore (`users/{userId}` collection)
5. Defaults to `admin` role for Firebase users without profile (for backward compatibility)

### 2. Secrets Storage in Firestore (`src/blog_writer_sdk/api/admin_management.py`)

**Added:**
- `sync_secret_to_firestore()` function to store secrets in Firestore
- Updated `sync_secrets()` endpoint to store secrets in Firestore during sync
- Updated `list_secrets()` endpoint to read from Firestore first, fallback to GCP

**Firestore Structure:**
```
/secrets/{secret_name}
  - name: string
  - value: string (stored for backend consumption tracking)
  - type: string (api_key, connection_string, password, token, other)
  - last_updated: timestamp
  - synced_from_gcp: boolean
  - gcp_secret_name: string
  - version: string
```

### 3. Response Format Updates

**GET `/api/v1/admin/secrets`**
- Now returns: `{"secrets": [...]}` format
- Each secret includes: `name`, `type`, `last_updated`, `synced`
- Reads from Firestore first, falls back to GCP Secret Manager

**POST `/api/v1/admin/secrets/sync`**
- Stores secrets in Firestore during sync
- Returns synced count and secret metadata
- Maintains backward compatibility with existing response format

---

## 🧪 Testing

### Prerequisites

1. **Firebase Admin SDK must be initialized:**
   - Firebase credentials must be available (via environment variables or default credentials)
   - Firestore must be enabled in the project

2. **User must exist in Firestore:**
   - User document at `users/{userId}` with `role` field
   - Role should be `admin` or `system_admin` for admin access

### Test Authentication

```bash
# Get Firebase ID token from dashboard frontend
TOKEN="<firebase-id-token>"

# Test list secrets endpoint
curl "https://blog-writer-api-dev-613248238610.europe-west9.run.app/api/v1/admin/secrets" \
  -H "Authorization: Bearer $TOKEN" \
  -H "x-usage-source: dashboard" \
  -H "x-usage-client: blogwriter-dashboard"

# Expected response:
# {
#   "secrets": [
#     {
#       "name": "OPENAI_API_KEY",
#       "type": "api_key",
#       "last_updated": "2026-01-04T20:16:00Z",
#       "synced": true
#     }
#   ]
# }
```

### Test Secrets Sync

```bash
# Sync secrets from GCP to Firestore
curl -X POST "https://blog-writer-api-dev-613248238610.europe-west9.run.app/api/v1/admin/secrets/sync" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "x-usage-source: dashboard" \
  -H "x-usage-client: blogwriter-dashboard" \
  -d '{
    "source": "google_secret_manager",
    "target": "application",
    "dry_run": false
  }'

# Expected response:
# {
#   "synced_count": 3,
#   "synced_secrets": [...],
#   "failed": [],
#   "timestamp": "2026-01-04T20:16:00Z",
#   "synced_by": "user@example.com"
# }
```

---

## 🔍 Troubleshooting

### Error: "Invalid or expired token"

**Possible causes:**
1. Token is not a valid Firebase ID token
2. Token has expired (Firebase tokens expire after 1 hour)
3. Firebase Admin SDK is not initialized

**Solutions:**
1. Verify token is a Firebase ID token (not a custom token)
2. Get a fresh token from the dashboard
3. Check Firebase credentials are configured

### Error: "Admin access required"

**Possible causes:**
1. User doesn't have admin role in Firestore
2. User document doesn't exist in Firestore

**Solutions:**
1. Check Firestore `users/{userId}` document exists
2. Ensure `role` field is set to `admin` or `system_admin`
3. If no profile exists, user defaults to `admin` role (for backward compatibility)

### Error: "Permission denied to access secrets"

**Possible causes:**
1. GCP service account doesn't have Secret Manager permissions
2. Wrong GCP project configured

**Solutions:**
1. Verify service account has `roles/secretmanager.secretAccessor` role
2. Check `GOOGLE_CLOUD_PROJECT` environment variable

### Secrets not appearing in list

**Possible causes:**
1. Secrets haven't been synced to Firestore yet
2. Firestore is not accessible

**Solutions:**
1. Run sync endpoint first: `POST /api/v1/admin/secrets/sync`
2. Check Firestore is enabled and accessible
3. Verify Firebase credentials are configured

---

## 📋 Next Steps

1. ✅ **Backend:** Firebase token verification implemented
2. ✅ **Backend:** Secrets storage in Firestore implemented
3. ✅ **Backend:** Response format updated to match dashboard expectations
4. ⏳ **Testing:** Test with dashboard frontend
5. ⏳ **Documentation:** Update API documentation

---

## 🔐 Security Notes

1. **Secret Values:** Secret values are stored in Firestore for consumption tracking. Ensure Firestore security rules restrict access to admin users only.

2. **Token Validation:** Firebase tokens are verified using Firebase Admin SDK, which validates:
   - Token signature
   - Token expiration
   - Token issuer

3. **Role Checking:** User roles are checked from Firestore. Default to `admin` for backward compatibility if no profile exists.

4. **Audit Logging:** All secret access is logged via `log_admin_action()` for audit trail.

---

## 📚 Related Documentation

- [Backend Secrets Requirements](./BACKEND_SECRETS_REQUIREMENTS.md) - Original requirements
- [Firebase Auth Implementation](./BACKEND_FIREBASE_AUTH_IMPLEMENTATION.md) - Implementation plan
- [Frontend Admin API Guide](./FRONTEND_ADMIN_API_GUIDE.md) - Frontend integration guide

---

**Status:** ✅ Implementation Complete  
**Last Updated:** 2026-01-04

