# Backend Firebase Authentication Implementation

## Overview

This document outlines the implementation to support Firebase ID token authentication for admin endpoints, specifically for the secrets management API used by the dashboard frontend.

---

## Requirements

Based on `BACKEND_SECRETS_REQUIREMENTS.md`, the backend needs to:

1. ✅ Accept Firebase ID tokens in `Authorization: Bearer <token>` header
2. ✅ Validate Firebase tokens and check for admin role
3. ✅ Return proper response format for secrets endpoints
4. ✅ Store synced secrets in Firestore
5. ✅ Handle errors gracefully

---

## Implementation Plan

### 1. Add Firebase Token Verification

**File:** `src/blog_writer_sdk/services/auth_service.py`

Add Firebase token verification alongside Supabase support:

```python
try:
    import firebase_admin
    from firebase_admin import auth as firebase_auth
    FIREBASE_AUTH_AVAILABLE = True
except ImportError:
    FIREBASE_AUTH_AVAILABLE = False

async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
    """
    Verify token - supports both Supabase and Firebase tokens.
    Tries Firebase first, then falls back to Supabase.
    """
    # Try Firebase token verification first
    if FIREBASE_AUTH_AVAILABLE:
        try:
            decoded_token = firebase_auth.verify_id_token(token)
            user_id = decoded_token['uid']
            email = decoded_token.get('email', '')
            
            # Get user role from Firestore
            profile = await self._get_firebase_user_profile(user_id)
            
            if profile:
                role = profile.get('role', 'user').lower()
                return {
                    'id': user_id,
                    'email': email,
                    'role': role,
                    'name': profile.get('name'),
                    'status': profile.get('status', 'active')
                }
            else:
                # Default to admin if no profile found (for backward compatibility)
                return {
                    'id': user_id,
                    'email': email,
                    'role': 'admin',  # Default for Firebase users
                    'name': None,
                    'status': 'active'
                }
        except Exception as e:
            logger.debug(f"Firebase token verification failed: {e}, trying Supabase...")
    
    # Fall back to Supabase verification
    # ... existing Supabase code ...
```

### 2. Update Secrets Sync Endpoint

**File:** `src/blog_writer_sdk/api/admin_management.py`

Update the sync endpoint to:
- Store secrets in Firestore
- Return expected response format
- Handle errors properly

### 3. Update List Secrets Endpoint

**File:** `src/blog_writer_sdk/api/admin_management.py`

Update to return secrets from Firestore (synced secrets) instead of directly from GCP:

```python
@router.get("/secrets")
async def list_secrets(...):
    """
    List all secrets synced from Google Cloud Secrets Manager.
    Returns secrets stored in Firestore (synced secrets).
    """
    # Get synced secrets from Firestore
    # Return format matching dashboard expectations
```

---

## Response Format Updates

### GET `/api/v1/admin/secrets`

**Current:** Returns GCP Secret Manager metadata  
**Expected:** Returns synced secrets from Firestore

```json
{
  "secrets": [
    {
      "name": "OPENAI_API_KEY",
      "type": "api_key",
      "last_updated": "2026-01-04T20:16:00Z",
      "synced": true
    }
  ]
}
```

### POST `/api/v1/admin/secrets/sync`

**Current:** Syncs to environment variables  
**Expected:** Syncs to Firestore and returns synced count

```json
{
  "synced_count": 3,
  "secrets": [
    {
      "name": "OPENAI_API_KEY",
      "type": "api_key",
      "last_updated": "2026-01-04T20:16:00Z"
    }
  ]
}
```

---

## Firestore Structure

```
/secrets/{secret_name}
  - name: string
  - value: string (encrypted or in secure storage)
  - type: string (api_key, connection_string, password, token, other)
  - last_updated: timestamp
  - synced_from_gcp: boolean
  - gcp_secret_name: string
```

---

## Testing

After implementation, test with:

```bash
# Get Firebase token from dashboard
TOKEN="<firebase-id-token>"

# Test list endpoint
curl "https://blog-writer-api-dev-613248238610.europe-west9.run.app/api/v1/admin/secrets" \
  -H "Authorization: Bearer $TOKEN" \
  -H "x-usage-source: dashboard" \
  -H "x-usage-client: blogwriter-dashboard"

# Test sync endpoint
curl -X POST "https://blog-writer-api-dev-613248238610.europe-west9.run.app/api/v1/admin/secrets/sync" \
  -H "Authorization: Bearer $TOKEN" \
  -H "x-usage-source: dashboard" \
  -H "x-usage-client: blogwriter-dashboard"
```

---

## Next Steps

1. Implement Firebase token verification
2. Update secrets sync to store in Firestore
3. Update list secrets to read from Firestore
4. Test with dashboard frontend
5. Update documentation

