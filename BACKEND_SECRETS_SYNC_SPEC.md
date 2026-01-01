# Backend Secrets Sync Endpoint Specification

**Feature:** Secrets synchronization between Firestore and Google Secret Manager  
**Endpoint:** `POST /api/v1/admin/secrets/sync`  
**Priority:** High  
**Status:** To be implemented

---

## Requirement

Implement a secrets sync endpoint that:
1. Syncs secrets from Google Secret Manager to make them available to the application
2. Returns `synced_count` indicating how many secrets were synced
3. Automatically syncs when secrets are created/updated via the admin dashboard

---

## API Specification

### Endpoint

```
POST /api/v1/admin/secrets/sync
```

### Authentication

Requires admin role (uses existing `require_admin` dependency)

### Request Body

```json
{
  "source": "google_secret_manager",
  "target": "application",
  "secret_names": ["OPENAI_API_KEY", "ANTHROPIC_API_KEY"],  // Optional: specific secrets
  "dry_run": false  // Optional: preview without actually syncing
}
```

**Parameters:**
- `source` (optional): Source of secrets, default: `"google_secret_manager"`
- `target` (optional): Target destination, default: `"application"`
- `secret_names` (optional): Array of specific secret names to sync. If empty, syncs all.
- `dry_run` (optional): If true, returns what would be synced without actually syncing

### Response

```json
{
  "synced_count": 5,
  "synced_secrets": [
    {
      "name": "OPENAI_API_KEY",
      "status": "synced",
      "version": "2"
    },
    {
      "name": "ANTHROPIC_API_KEY",
      "status": "synced",
      "version": "1"
    },
    {
      "name": "LITELLM_MASTER_KEY",
      "status": "synced",
      "version": "3"
    },
    {
      "name": "DEEPSEEK_API_KEY",
      "status": "synced",
      "version": "1"
    },
    {
      "name": "FIREBASE_PRIVATE_KEY",
      "status": "synced",
      "version": "1"
    }
  ],
  "failed": [],
  "timestamp": "2025-12-21T18:30:00Z",
  "synced_by": "admin@example.com"
}
```

### Error Responses

**401 Unauthorized:**
```json
{
  "detail": "Admin access required"
}
```

**403 Forbidden:**
```json
{
  "detail": "Permission denied to access Secret Manager"
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Failed to sync secrets: {error_message}"
}
```

---

## Implementation

### File Location

Add to: `src/blog_writer_sdk/api/admin_management.py`

### Code Implementation

```python
from typing import List, Optional
from pydantic import BaseModel

class SecretSyncRequest(BaseModel):
    """Request model for secrets sync."""
    source: str = Field(default="google_secret_manager", description="Source of secrets")
    target: str = Field(default="application", description="Target destination")
    secret_names: Optional[List[str]] = Field(default=None, description="Specific secrets to sync (None = all)")
    dry_run: bool = Field(default=False, description="Preview without syncing")


class SecretSyncResult(BaseModel):
    """Result of a single secret sync."""
    name: str
    status: str  # 'synced', 'failed', 'skipped'
    version: Optional[str] = None
    error: Optional[str] = None


class SecretSyncResponse(BaseModel):
    """Response model for secrets sync."""
    synced_count: int
    synced_secrets: List[SecretSyncResult]
    failed: List[SecretSyncResult]
    timestamp: str
    synced_by: str


@router.post("/secrets/sync", response_model=SecretSyncResponse)
async def sync_secrets(
    data: SecretSyncRequest,
    admin: Dict = Depends(require_admin),
    request: Request = None
):
    """
    Sync secrets from Google Secret Manager.
    
    This endpoint fetches secrets from Google Secret Manager and makes them
    available to the application. It can sync all secrets or specific ones.
    
    **Use Cases:**
    - Initial setup: Sync all secrets on first deployment
    - Refresh: Update secrets after changes in Secret Manager
    - Selective: Sync only specific secrets that changed
    
    **Security:**
    - Requires admin authentication
    - All actions are audit logged
    - Supports dry-run mode for safety
    """
    try:
        client = get_secret_manager_client()
        project_id = get_project_id()
        parent = f"projects/{project_id}"
        
        synced_secrets = []
        failed_secrets = []
        
        # Get list of secrets to sync
        if data.secret_names:
            # Sync specific secrets
            secrets_to_sync = data.secret_names
        else:
            # Sync all secrets
            all_secrets = client.list_secrets(request={"parent": parent})
            secrets_to_sync = [secret.name.split("/")[-1] for secret in all_secrets]
        
        logger.info(f"Syncing {len(secrets_to_sync)} secrets (dry_run={data.dry_run})")
        
        # Sync each secret
        for secret_name in secrets_to_sync:
            try:
                secret_path = f"{parent}/secrets/{secret_name}/versions/latest"
                
                # Get secret value from Secret Manager
                response = client.access_secret_version(request={"name": secret_path})
                value = response.payload.data.decode("UTF-8")
                version = response.name.split("/")[-1]
                
                if not data.dry_run:
                    # Actually sync the secret to application environment
                    # This could mean:
                    # 1. Update in-memory environment variables
                    # 2. Write to Cloud Run environment
                    # 3. Update configuration in Firestore
                    # 4. Reload application config
                    
                    os.environ[secret_name] = value
                    
                    # Optional: Also save to Firestore for frontend access
                    # (Store metadata only, not the actual secret value)
                    await sync_to_firestore_metadata(secret_name, version)
                
                synced_secrets.append(SecretSyncResult(
                    name=secret_name,
                    status="synced" if not data.dry_run else "would_sync",
                    version=version
                ))
                
            except google_exceptions.NotFound:
                failed_secrets.append(SecretSyncResult(
                    name=secret_name,
                    status="failed",
                    error=f"Secret '{secret_name}' not found in Secret Manager"
                ))
            except Exception as e:
                logger.error(f"Failed to sync secret {secret_name}: {e}")
                failed_secrets.append(SecretSyncResult(
                    name=secret_name,
                    status="failed",
                    error=str(e)
                ))
        
        # Audit log the sync operation
        await log_admin_action(
            admin["id"], 
            "secrets_sync", 
            "secrets", 
            f"synced_{len(synced_secrets)}_failed_{len(failed_secrets)}",
            None,
            {
                "synced_count": len(synced_secrets),
                "failed_count": len(failed_secrets),
                "dry_run": data.dry_run,
                "secret_names": secrets_to_sync
            },
            request
        )
        
        return SecretSyncResponse(
            synced_count=len(synced_secrets),
            synced_secrets=synced_secrets,
            failed=failed_secrets,
            timestamp=datetime.utcnow().isoformat(),
            synced_by=admin["email"]
        )
        
    except google_exceptions.PermissionDenied:
        raise HTTPException(status_code=403, detail="Permission denied to access Secret Manager")
    except Exception as e:
        logger.error(f"Secrets sync failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Secrets sync failed: {str(e)}")


async def sync_to_firestore_metadata(secret_name: str, version: str):
    """
    Sync secret metadata to Firestore (not the secret value itself).
    
    This allows the frontend to see which secrets exist and their versions,
    without exposing the actual secret values.
    """
    try:
        from google.cloud import firestore
        
        db = firestore.Client()
        doc_ref = db.collection('secrets_metadata').document(secret_name)
        
        await doc_ref.set({
            'name': secret_name,
            'version': version,
            'synced_at': datetime.utcnow(),
            'source': 'google_secret_manager',
        }, merge=True)
        
    except Exception as e:
        logger.warning(f"Failed to sync metadata to Firestore: {e}")
        # Don't fail the entire sync if Firestore update fails


# Update existing create_or_update_secret to auto-sync
@router.put("/secrets/{name}")
async def create_or_update_secret(
    name: str,
    data: SecretCreateRequest,
    admin: Dict = Depends(require_admin),
    request: Request = None
):
    """
    Create or update a secret.
    
    **Automatic Sync:** After creating/updating in Secret Manager,
    this endpoint automatically syncs the secret to the application.
    """
    try:
        client = get_secret_manager_client()
        project_id = get_project_id()
        parent = f"projects/{project_id}"
        secret_path = f"{parent}/secrets/{name}"
        
        # Check if secret exists
        try:
            client.get_secret(request={"name": secret_path})
            action = "secret_update"
        except google_exceptions.NotFound:
            # Create new secret
            client.create_secret(
                request={
                    "parent": parent,
                    "secret_id": name,
                    "secret": {
                        "replication": {"automatic": {}},
                        "labels": data.labels
                    }
                }
            )
            action = "secret_create"
        
        # Add new version
        version_response = client.add_secret_version(
            request={
                "parent": secret_path,
                "payload": {"data": data.value.encode("UTF-8")}
            }
        )
        
        version = version_response.name.split("/")[-1]
        
        # AUTO-SYNC: Make secret available to application immediately
        os.environ[name] = data.value
        await sync_to_firestore_metadata(name, version)
        
        # Trigger application config reload (if needed)
        await reload_application_config()
        
        await log_admin_action(
            admin["id"], action, "secret", name,
            None, {"labels": data.labels, "auto_synced": True}, request
        )
        
        return {
            "name": name,
            "action": "created" if action == "secret_create" else "updated",
            "version": version,
            "synced": True,  # Indicates auto-sync occurred
            "updated_by": admin["email"],
            "updated_at": datetime.utcnow().isoformat()
        }
        
    except google_exceptions.PermissionDenied:
        raise HTTPException(status_code=403, detail="Permission denied")
    except Exception as e:
        logger.error(f"Failed to create/update secret: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def reload_application_config():
    """
    Reload application configuration after secrets sync.
    
    This ensures the application picks up new secret values without restart.
    """
    try:
        # Reload AI Gateway configuration
        from ...services.ai_gateway import get_ai_gateway, initialize_ai_gateway
        
        # Re-initialize with new environment variables
        initialize_ai_gateway(
            base_url=os.getenv("LITELLM_PROXY_URL"),
            api_key=os.getenv("LITELLM_API_KEY"),
        )
        
        logger.info("Application config reloaded after secrets sync")
        
    except Exception as e:
        logger.warning(f"Failed to reload application config: {e}")
        # Don't fail the sync if reload fails
```

---

## Usage Examples

### Frontend Usage (When Admin Saves Config)

```typescript
// When admin saves API key in dashboard
async function saveOpenAIKey(apiKey: string) {
  // 1. Save to Firestore (frontend)
  await configService.saveAIProviderConfig('test-org', 'openai', {
    apiKey: apiKey,
    enabled: true,
  });
  
  // 2. Call backend to sync to Secret Manager
  const response = await fetch('/api/v1/admin/secrets/sync', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify({
      secret_names: ['OPENAI_API_KEY'],
      dry_run: false,
    }),
  });
  
  const result = await response.json();
  
  if (result.synced_count > 0) {
    toast.success('API key synced to backend successfully!');
  }
}
```

### Backend Usage (Create/Update Secret)

```python
# Existing endpoint automatically syncs
PUT /api/v1/admin/secrets/OPENAI_API_KEY
{
  "value": "sk-...",
  "labels": {"provider": "openai"}
}

# Response
{
  "name": "OPENAI_API_KEY",
  "action": "updated",
  "version": "2",
  "synced": true,  # ← Indicates auto-sync occurred
  "updated_by": "admin@example.com",
  "updated_at": "2025-12-21T18:30:00Z"
}
```

### Manual Sync All Secrets

```bash
# Sync all secrets from Secret Manager
curl -X POST https://blog-writer-api-dev-613248238610.europe-west9.run.app/api/v1/admin/secrets/sync \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json" \
  -d '{"dry_run": false}'

# Response
{
  "synced_count": 5,
  "synced_secrets": [
    {"name": "OPENAI_API_KEY", "status": "synced", "version": "2"},
    {"name": "ANTHROPIC_API_KEY", "status": "synced", "version": "1"},
    {"name": "LITELLM_MASTER_KEY", "status": "synced", "version": "3"},
    {"name": "DEEPSEEK_API_KEY", "status": "synced", "version": "1"},
    {"name": "FIREBASE_PRIVATE_KEY", "status": "synced", "version": "1"}
  ],
  "failed": [],
  "timestamp": "2025-12-21T18:30:00Z",
  "synced_by": "admin@example.com"
}
```

---

## Data Flow

### Scenario 1: Admin Updates API Key in Dashboard

```
1. Admin enters new OpenAI API key in dashboard
         ↓
2. Frontend saves to Firestore (encrypted)
         ↓
3. Frontend calls PUT /api/v1/admin/secrets/OPENAI_API_KEY
         ↓
4. Backend saves to Google Secret Manager
         ↓
5. Backend AUTO-SYNCS to application (os.environ)
         ↓
6. Backend reloads AI Gateway config
         ↓
7. Application immediately uses new key
         ↓
8. Response confirms: synced=true
```

### Scenario 2: Manual Sync on Deployment

```
1. New Cloud Run instance starts
         ↓
2. Initialization calls POST /api/v1/admin/secrets/sync
         ↓
3. Backend fetches all secrets from Secret Manager
         ↓
4. Backend loads into os.environ
         ↓
5. Response: synced_count=5
         ↓
6. Application ready with all secrets
```

---

## Implementation Checklist

### Backend Tasks

- [ ] Add `SecretSyncRequest` model to admin_management.py
- [ ] Add `SecretSyncResult` model
- [ ] Add `SecretSyncResponse` model
- [ ] Implement `POST /api/v1/admin/secrets/sync` endpoint
- [ ] Add `sync_to_firestore_metadata()` helper function
- [ ] Add `reload_application_config()` helper function
- [ ] Update `PUT /api/v1/admin/secrets/{name}` to auto-sync
- [ ] Add audit logging for sync operations
- [ ] Add error handling for permission issues
- [ ] Add dry-run support for testing

### Testing Tasks

- [ ] Test manual sync of all secrets
- [ ] Test selective sync of specific secrets
- [ ] Test auto-sync on secret create/update
- [ ] Test dry-run mode
- [ ] Test with missing permissions (should fail gracefully)
- [ ] Test with non-existent secrets
- [ ] Verify audit logs are created
- [ ] Verify Firestore metadata is updated

### Documentation Tasks

- [ ] Update API documentation
- [ ] Add to OpenAPI schema (auto-generated)
- [ ] Document usage examples
- [ ] Add to admin API guide

---

## Frontend Integration

### Update Frontend API Client

**File:** `frontend-starter/lib/api/client.ts`

Add to api object:

```typescript
export const api = {
  // ... existing methods
  
  // Secrets Management
  syncSecrets: (body: SecretSyncRequest) =>
    client.POST('/api/v1/admin/secrets/sync', { body }),
  
  createOrUpdateSecret: (name: string, body: SecretCreateRequest) =>
    client.PUT('/api/v1/admin/secrets/{name}', {
      params: { path: { name } },
      body,
    }),
};

export type SecretSyncRequest = {
  source?: string;
  target?: string;
  secret_names?: string[];
  dry_run?: boolean;
};

export type SecretSyncResponse = {
  synced_count: number;
  synced_secrets: Array<{
    name: string;
    status: string;
    version?: string;
    error?: string;
  }>;
  failed: Array<{
    name: string;
    status: string;
    error?: string;
  }>;
  timestamp: string;
  synced_by: string;
};
```

### Frontend Component

**File:** `components/configuration/SecretsSyncButton.tsx`

```typescript
'use client';

import { Button } from '@/components/catalyst/button';
import { Badge } from '@/components/catalyst/badge';
import { Alert, AlertTitle, AlertDescription } from '@/components/catalyst/alert';
import { useState } from 'react';
import { toast } from 'react-hot-toast';

export function SecretsSyncButton() {
  const [isSyncing, setIsSyncing] = useState(false);
  const [lastSync, setLastSync] = useState<any>(null);
  
  const handleSync = async () => {
    setIsSyncing(true);
    
    try {
      const response = await fetch('/api/v1/admin/secrets/sync', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${sessionToken}`,
        },
        body: JSON.stringify({
          dry_run: false,
        }),
      });
      
      if (!response.ok) throw new Error('Sync failed');
      
      const result = await response.json();
      setLastSync(result);
      
      toast.success(`Synced ${result.synced_count} secrets!`);
      
    } catch (error) {
      toast.error('Failed to sync secrets');
    } finally {
      setIsSyncing(false);
    }
  };
  
  return (
    <div className="space-y-4">
      <Button
        color="blue"
        onClick={handleSync}
        disabled={isSyncing}
      >
        {isSyncing ? 'Syncing...' : 'Sync Secrets from Google'}
      </Button>
      
      {lastSync && (
        <Alert color="green">
          <AlertTitle>Sync Successful</AlertTitle>
          <AlertDescription>
            Synced {lastSync.synced_count} secrets at {new Date(lastSync.timestamp).toLocaleString()}
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
}
```

---

## Security Considerations

### 1. Secrets in Transit
- ✅ HTTPS only (enforced by Cloud Run)
- ✅ Admin authentication required
- ✅ Audit logging for all access

### 2. Secrets at Rest
- ✅ Google Secret Manager encryption (automatic)
- ✅ Firestore stores metadata only, not values
- ✅ In-memory secrets cleared on restart

### 3. Access Control
- ✅ Only admins can sync secrets
- ✅ Permission denied if insufficient IAM roles
- ✅ All actions audit logged

### 4. Best Practices
- ✅ Dry-run mode for testing
- ✅ Selective sync (specific secrets only)
- ✅ Version tracking
- ✅ Automatic sync on create/update

---

## Deployment Notes

### Required IAM Permissions

The Cloud Run service account needs:

```bash
# Grant Secret Manager access
gcloud projects add-iam-policy-binding api-ai-blog-writer \
  --member="serviceAccount:blog-writer-api-dev@api-ai-blog-writer.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding api-ai-blog-writer \
  --member="serviceAccount:blog-writer-api-dev@api-ai-blog-writer.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretVersionManager"
```

### Environment Variables

Ensure these are set:

```bash
GOOGLE_CLOUD_PROJECT=api-ai-blog-writer
# Service account credentials are automatic in Cloud Run
```

---

## Testing

### Test Script

**File:** `test_secrets_sync.sh`

```bash
#!/bin/bash

BACKEND_URL="https://blog-writer-api-dev-613248238610.europe-west9.run.app"
ADMIN_TOKEN="your-admin-token"

echo "Testing Secrets Sync Endpoint"
echo "=============================="

# Test 1: Dry run (preview)
echo -e "\n1. Dry Run (Preview Only)"
curl -X POST "$BACKEND_URL/api/v1/admin/secrets/sync" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"dry_run": true}' | jq

# Test 2: Sync specific secrets
echo -e "\n2. Sync Specific Secrets"
curl -X POST "$BACKEND_URL/api/v1/admin/secrets/sync" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "secret_names": ["OPENAI_API_KEY", "ANTHROPIC_API_KEY"],
    "dry_run": false
  }' | jq

# Test 3: Sync all secrets
echo -e "\n3. Sync All Secrets"
curl -X POST "$BACKEND_URL/api/v1/admin/secrets/sync" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"dry_run": false}' | jq

echo -e "\nDone! Check synced_count in responses."
```

---

## Summary

### Implementation Required:

1. **Add sync endpoint:** `POST /api/v1/admin/secrets/sync`
2. **Response includes:** `synced_count` field
3. **Auto-sync on create/update:** Existing `PUT /secrets/{name}` automatically syncs
4. **Security:** Admin auth, audit logging, permission checks
5. **Features:** Dry-run mode, selective sync, error handling

### Files to Modify:

- `src/blog_writer_sdk/api/admin_management.py` - Add sync endpoint and auto-sync logic
- `test_secrets_sync.sh` - Add test script
- Frontend API client - Add sync method

### Timeline:

- Implementation: 2-3 hours
- Testing: 1 hour
- Documentation: 30 minutes
- **Total: ~4 hours**

---

## Next Steps

1. Implement the sync endpoint in `admin_management.py`
2. Update the `PUT /secrets/{name}` endpoint to auto-sync
3. Test with the provided test script
4. Update frontend API client
5. Deploy and verify

**Ready to implement?** Let me know if you want me to add this code to the backend! 🚀

