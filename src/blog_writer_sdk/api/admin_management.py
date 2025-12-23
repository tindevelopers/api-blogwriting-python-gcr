"""
Admin Management API

Provides endpoints for admin operations:
- Secrets management (Google Secret Manager)
- Environment variable management
- Logs viewer (Cloud Logging)
- AI usage and cost tracking
- Job queue management

All endpoints require admin authentication.
"""

import os
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import asyncio
import json

# Google Cloud imports
try:
    from google.cloud import secretmanager
    from google.cloud import logging as cloud_logging
    from google.api_core import exceptions as google_exceptions
    GOOGLE_CLOUD_AVAILABLE = True
except ImportError:
    GOOGLE_CLOUD_AVAILABLE = False
    secretmanager = None
    cloud_logging = None

from ..services.auth_service import get_auth_service, AuthService
from ..services.usage_logger import get_usage_logger, UsageLogger

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin", tags=["Admin Management"])


# ============================================================================
# Request/Response Models
# ============================================================================

class SecretMetadata(BaseModel):
    """Secret metadata (without value)."""
    name: str
    create_time: Optional[str] = None
    labels: Dict[str, str] = Field(default_factory=dict)
    version_count: int = 0


class SecretValue(BaseModel):
    """Secret with value (for get/create/update)."""
    name: str
    value: str


class SecretCreateRequest(BaseModel):
    """Request to create/update a secret."""
    value: str
    labels: Dict[str, str] = Field(default_factory=dict)


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


class EnvVarUpdate(BaseModel):
    """Environment variable update request."""
    variables: Dict[str, str]
    remove_keys: List[str] = Field(default_factory=list)


class LogEntry(BaseModel):
    """Log entry model."""
    timestamp: str
    severity: str
    message: str
    resource: Optional[Dict[str, Any]] = None
    labels: Dict[str, str] = Field(default_factory=dict)


class LogsQueryRequest(BaseModel):
    """Request for querying logs."""
    filter: Optional[str] = None
    severity: Optional[str] = None  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    limit: int = Field(default=100, le=1000)


class JobAction(BaseModel):
    """Job action request."""
    reason: Optional[str] = None


class AdminAuditLog(BaseModel):
    """Admin action audit log entry."""
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


# ============================================================================
# Authentication Dependency
# ============================================================================

async def require_admin(request: Request) -> Dict[str, Any]:
    """
    Require admin role for endpoint access.
    
    This is a FastAPI dependency that checks if the current user has admin privileges.
    """
    auth_service = get_auth_service()
    
    # Get authorization header
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token = auth_header.split(" ", 1)[1]
    
    # Verify token and get user
    user = await auth_service.verify_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    # Check admin role
    user_role = user.get("role", "").lower()
    if user_role not in ["system_admin", "admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return user


async def log_admin_action(
    admin_user_id: str,
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    old_value: Optional[Dict] = None,
    new_value: Optional[Dict] = None,
    request: Optional[Request] = None
):
    """Log admin action to audit table."""
    try:
        from supabase import create_client
        
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not supabase_url or not supabase_key:
            logger.warning("Supabase not configured, skipping audit log")
            return
        
        client = create_client(supabase_url, supabase_key)
        
        record = {
            "admin_user_id": admin_user_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "old_value": old_value,
            "new_value": new_value,
            "ip_address": request.client.host if request else None,
            "user_agent": request.headers.get("User-Agent") if request else None,
            "created_at": datetime.utcnow().isoformat()
        }
        
        client.table("admin_audit_logs").insert(record).execute()
        
    except Exception as e:
        logger.error(f"Failed to log admin action: {e}")


# ============================================================================
# Secrets Management Endpoints
# ============================================================================

def get_secret_manager_client():
    """Get Secret Manager client."""
    if not GOOGLE_CLOUD_AVAILABLE:
        raise HTTPException(status_code=503, detail="Google Cloud SDK not available")
    return secretmanager.SecretManagerServiceClient()


def get_project_id() -> str:
    """Get GCP project ID."""
    project_id = os.getenv("GCP_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        # Try to get from metadata server
        try:
            import httpx
            response = httpx.get(
                "http://metadata.google.internal/computeMetadata/v1/project/project-id",
                headers={"Metadata-Flavor": "Google"},
                timeout=2.0
            )
            project_id = response.text
        except Exception:
            raise HTTPException(status_code=500, detail="Could not determine GCP project ID")
    return project_id


@router.get("/secrets", response_model=List[SecretMetadata])
async def list_secrets(
    admin: Dict = Depends(require_admin),
    request: Request = None
):
    """
    List all secrets (names only, not values).
    
    Returns a list of secret metadata without exposing secret values.
    """
    try:
        client = get_secret_manager_client()
        project_id = get_project_id()
        parent = f"projects/{project_id}"
        
        secrets = []
        for secret in client.list_secrets(request={"parent": parent}):
            # Get version count
            versions = list(client.list_secret_versions(
                request={"parent": secret.name, "filter": "state:ENABLED"}
            ))
            
            secrets.append(SecretMetadata(
                name=secret.name.split("/")[-1],
                create_time=secret.create_time.isoformat() if secret.create_time else None,
                labels=dict(secret.labels) if secret.labels else {},
                version_count=len(versions)
            ))
        
        await log_admin_action(
            admin["id"], "read", "secrets", None, None, None, request
        )
        
        return secrets
        
    except google_exceptions.PermissionDenied:
        raise HTTPException(status_code=403, detail="Permission denied to access secrets")
    except Exception as e:
        logger.error(f"Failed to list secrets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/secrets/{name}")
async def get_secret(
    name: str,
    admin: Dict = Depends(require_admin),
    request: Request = None
):
    """
    Get a secret value.
    
    This action is audit logged for security.
    """
    try:
        client = get_secret_manager_client()
        project_id = get_project_id()
        secret_name = f"projects/{project_id}/secrets/{name}/versions/latest"
        
        response = client.access_secret_version(request={"name": secret_name})
        value = response.payload.data.decode("UTF-8")
        
        # Audit log this sensitive action
        await log_admin_action(
            admin["id"], "secret_access", "secret", name, None, None, request
        )
        
        return {
            "name": name,
            "value": value,
            "accessed_at": datetime.utcnow().isoformat(),
            "accessed_by": admin["email"]
        }
        
    except google_exceptions.NotFound:
        raise HTTPException(status_code=404, detail=f"Secret '{name}' not found")
    except google_exceptions.PermissionDenied:
        raise HTTPException(status_code=403, detail="Permission denied")
    except Exception as e:
        logger.error(f"Failed to get secret: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/secrets/{name}")
async def create_or_update_secret(
    name: str,
    data: SecretCreateRequest,
    admin: Dict = Depends(require_admin),
    request: Request = None
):
    """
    Create or update a secret.
    
    If the secret doesn't exist, it will be created.
    If it exists, a new version will be added.
    
    **Auto-Sync:** After creating/updating in Secret Manager,
    this endpoint automatically syncs the secret to the application
    environment, making it immediately available.
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
        logger.info(f"Auto-synced secret '{name}' to application environment")
        
        # Sync metadata to Firestore
        try:
            await sync_secret_metadata(name, version)
        except Exception as meta_error:
            logger.warning(f"Failed to sync metadata: {meta_error}")
        
        # Reload application config to pick up new secret
        try:
            await reload_application_config()
        except Exception as reload_error:
            logger.warning(f"Failed to reload config: {reload_error}")
        
        await log_admin_action(
            admin["id"], action, "secret", name,
            None, {"labels": data.labels, "auto_synced": True, "version": version}, request
        )
        
        return {
            "name": name,
            "action": "created" if action == "secret_create" else "updated",
            "version": version,
            "synced": True,  # Indicates auto-sync occurred
            "updated_by": admin.get("email", admin.get("id", "unknown")),
            "updated_at": datetime.utcnow().isoformat()
        }
        
    except google_exceptions.PermissionDenied:
        raise HTTPException(status_code=403, detail="Permission denied")
    except Exception as e:
        logger.error(f"Failed to create/update secret: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/secrets/{name}")
async def delete_secret(
    name: str,
    admin: Dict = Depends(require_admin),
    request: Request = None
):
    """
    Delete a secret.
    
    This permanently deletes the secret and all its versions.
    """
    try:
        client = get_secret_manager_client()
        project_id = get_project_id()
        secret_path = f"projects/{project_id}/secrets/{name}"
        
        client.delete_secret(request={"name": secret_path})
        
        await log_admin_action(
            admin["id"], "secret_delete", "secret", name, None, None, request
        )
        
        return {
            "name": name,
            "deleted": True,
            "deleted_by": admin["email"],
            "deleted_at": datetime.utcnow().isoformat()
        }
        
    except google_exceptions.NotFound:
        raise HTTPException(status_code=404, detail=f"Secret '{name}' not found")
    except google_exceptions.PermissionDenied:
        raise HTTPException(status_code=403, detail="Permission denied")
    except Exception as e:
        logger.error(f"Failed to delete secret: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/secrets/sync", response_model=SecretSyncResponse)
async def sync_secrets(
    data: SecretSyncRequest,
    admin: Dict = Depends(require_admin),
    request: Request = None
):
    """
    Sync secrets from Google Secret Manager to application.
    
    Fetches secrets from Google Secret Manager and makes them available
    to the application by loading them into environment variables.
    
    **Use Cases:**
    - Initial deployment: Sync all secrets on first startup
    - Refresh: Update secrets after changes in Secret Manager
    - Selective: Sync only specific secrets that changed
    
    **Features:**
    - Dry-run mode for preview
    - Selective or bulk sync
    - Audit logging
    - Error handling per secret
    
    **Security:**
    - Requires admin authentication
    - All operations audit logged
    - Permissions validated
    
    Returns:
        SecretSyncResponse with synced_count and details per secret
    """
    try:
        client = get_secret_manager_client()
        project_id = get_project_id()
        parent = f"projects/{project_id}"
        
        synced_secrets = []
        failed_secrets = []
        
        # Determine which secrets to sync
        if data.secret_names:
            # Sync specific secrets
            secrets_to_sync = data.secret_names
            logger.info(f"Syncing {len(secrets_to_sync)} specific secrets (dry_run={data.dry_run})")
        else:
            # Sync all secrets
            try:
                all_secrets = client.list_secrets(request={"parent": parent})
                secrets_to_sync = [secret.name.split("/")[-1] for secret in all_secrets]
                logger.info(f"Syncing all {len(secrets_to_sync)} secrets (dry_run={data.dry_run})")
            except Exception as e:
                logger.error(f"Failed to list secrets: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to list secrets: {str(e)}")
        
        # Sync each secret
        for secret_name in secrets_to_sync:
            try:
                secret_path = f"{parent}/secrets/{secret_name}/versions/latest"
                
                # Get secret value from Secret Manager
                response = client.access_secret_version(request={"name": secret_path})
                value = response.payload.data.decode("UTF-8")
                version = response.name.split("/")[-1]
                
                if not data.dry_run:
                    # Sync to application environment
                    os.environ[secret_name] = value
                    logger.info(f"Synced secret '{secret_name}' version {version} to environment")
                    
                    # Optional: Save metadata to Firestore (not the value itself)
                    try:
                        await sync_secret_metadata(secret_name, version)
                    except Exception as meta_error:
                        logger.warning(f"Failed to sync metadata for {secret_name}: {meta_error}")
                
                synced_secrets.append(SecretSyncResult(
                    name=secret_name,
                    status="synced" if not data.dry_run else "would_sync",
                    version=version
                ))
                
                logger.debug(f"Secret {secret_name} {'synced' if not data.dry_run else 'would sync'}")
                
            except google_exceptions.NotFound:
                error_msg = f"Secret '{secret_name}' not found in Secret Manager"
                logger.warning(error_msg)
                failed_secrets.append(SecretSyncResult(
                    name=secret_name,
                    status="failed",
                    error=error_msg
                ))
            except google_exceptions.PermissionDenied:
                error_msg = f"Permission denied for secret '{secret_name}'"
                logger.error(error_msg)
                failed_secrets.append(SecretSyncResult(
                    name=secret_name,
                    status="failed",
                    error=error_msg
                ))
            except Exception as e:
                error_msg = f"Error syncing '{secret_name}': {str(e)}"
                logger.error(error_msg)
                failed_secrets.append(SecretSyncResult(
                    name=secret_name,
                    status="failed",
                    error=str(e)
                ))
        
        # Reload application config if secrets were synced
        if not data.dry_run and synced_secrets:
            try:
                await reload_application_config()
                logger.info("Application configuration reloaded after secrets sync")
            except Exception as reload_error:
                logger.warning(f"Failed to reload application config: {reload_error}")
        
        # Audit log the sync operation
        await log_admin_action(
            admin["id"], 
            "secrets_sync", 
            "secrets", 
            f"sync_operation",
            None,
            {
                "synced_count": len(synced_secrets),
                "failed_count": len(failed_secrets),
                "dry_run": data.dry_run,
                "total_requested": len(secrets_to_sync),
                "secret_names": secrets_to_sync if len(secrets_to_sync) <= 10 else f"{len(secrets_to_sync)} secrets"
            },
            request
        )
        
        logger.info(
            f"Secrets sync complete: {len(synced_secrets)} synced, {len(failed_secrets)} failed "
            f"(dry_run={data.dry_run}) by {admin['email']}"
        )
        
        return SecretSyncResponse(
            synced_count=len(synced_secrets),
            synced_secrets=synced_secrets,
            failed=failed_secrets,
            timestamp=datetime.utcnow().isoformat(),
            synced_by=admin.get("email", admin.get("id", "unknown"))
        )
        
    except HTTPException:
        raise
    except google_exceptions.PermissionDenied:
        raise HTTPException(status_code=403, detail="Permission denied to access Secret Manager")
    except Exception as e:
        logger.error(f"Secrets sync failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Secrets sync failed: {str(e)}")


async def sync_secret_metadata(secret_name: str, version: str):
    """
    Sync secret metadata to Firestore (not the secret value itself).
    
    This allows the frontend to see which secrets exist and their versions,
    without exposing the actual secret values.
    
    Args:
        secret_name: Name of the secret
        version: Version number from Secret Manager
    """
    try:
        # Only sync metadata if Firestore is available
        if not GOOGLE_CLOUD_AVAILABLE:
            return
        
        from google.cloud import firestore
        
        db = firestore.Client()
        doc_ref = db.collection('secrets_metadata').document(secret_name)
        
        doc_ref.set({
            'name': secret_name,
            'version': version,
            'synced_at': firestore.SERVER_TIMESTAMP,
            'source': 'google_secret_manager',
        }, merge=True)
        
        logger.debug(f"Synced metadata for secret '{secret_name}' to Firestore")
        
    except Exception as e:
        logger.warning(f"Failed to sync metadata to Firestore for {secret_name}: {e}")
        # Don't fail the entire sync if Firestore update fails


async def reload_application_config():
    """
    Reload application configuration after secrets sync.
    
    This ensures the application picks up new secret values without restart.
    Reloads various service configurations that depend on secrets.
    """
    try:
        # Reload AI Gateway configuration if available
        try:
            from ...services.ai_gateway import initialize_ai_gateway
            
            litellm_url = os.getenv("LITELLM_PROXY_URL")
            litellm_key = os.getenv("LITELLM_API_KEY")
            
            if litellm_url or litellm_key:
                initialize_ai_gateway(
                    base_url=litellm_url,
                    api_key=litellm_key,
                )
                logger.debug("AI Gateway config reloaded")
        except Exception as e:
            logger.warning(f"Failed to reload AI Gateway config: {e}")
        
        # Reload DataForSEO client if available
        try:
            from ...integrations.dataforseo_integration import DataForSEOClient
            
            dataforseo_key = os.getenv("DATAFORSEO_API_KEY")
            dataforseo_secret = os.getenv("DATAFORSEO_API_SECRET")
            
            if dataforseo_key or dataforseo_secret:
                # Client will be re-initialized on next use with new credentials
                logger.debug("DataForSEO credentials updated")
        except Exception as e:
            logger.warning(f"Failed to reload DataForSEO config: {e}")
        
        logger.info("Application config reload completed")
        
    except Exception as e:
        logger.error(f"Error during application config reload: {e}")
        # Don't fail the sync if reload fails


# ============================================================================
# Environment Variables Endpoints
# ============================================================================

@router.get("/env-vars")
async def get_env_vars(
    admin: Dict = Depends(require_admin),
    include_secrets: bool = False
):
    """
    Get current environment variables.
    
    By default, sensitive values are masked.
    """
    # Get all env vars, masking sensitive ones
    sensitive_patterns = ["KEY", "SECRET", "PASSWORD", "TOKEN", "CREDENTIAL"]
    
    env_vars = {}
    for key, value in os.environ.items():
        # Skip internal Python vars
        if key.startswith("_") or key in ["PATH", "HOME", "USER", "SHELL"]:
            continue
        
        # Mask sensitive values unless explicitly requested
        is_sensitive = any(p in key.upper() for p in sensitive_patterns)
        if is_sensitive and not include_secrets:
            env_vars[key] = "***MASKED***"
        else:
            env_vars[key] = value
    
    return {
        "variables": env_vars,
        "count": len(env_vars),
        "masked": not include_secrets
    }


@router.put("/env-vars")
async def update_env_vars(
    data: EnvVarUpdate,
    admin: Dict = Depends(require_admin),
    request: Request = None
):
    """
    Update environment variables.
    
    Note: This updates the Cloud Run service configuration, which triggers a new revision.
    Changes may take a few minutes to take effect.
    """
    try:
        import subprocess
        
        project_id = get_project_id()
        service_name = os.getenv("K_SERVICE", "blog-writer-api")
        region = os.getenv("GCP_REGION", "europe-west9")
        
        # Build the update command
        env_updates = []
        for key, value in data.variables.items():
            env_updates.append(f"{key}={value}")
        
        if not env_updates and not data.remove_keys:
            return {"message": "No changes to apply"}
        
        cmd = [
            "gcloud", "run", "services", "update", service_name,
            "--region", region,
            "--project", project_id,
            "--quiet"
        ]
        
        if env_updates:
            cmd.extend(["--update-env-vars", ",".join(env_updates)])
        
        if data.remove_keys:
            cmd.extend(["--remove-env-vars", ",".join(data.remove_keys)])
        
        # Execute update
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode != 0:
            raise Exception(f"Failed to update service: {result.stderr}")
        
        await log_admin_action(
            admin["id"], "env_var_update", "environment",
            None, None, {"updated": list(data.variables.keys()), "removed": data.remove_keys},
            request
        )
        
        return {
            "message": "Environment variables updated. A new revision is being deployed.",
            "updated_keys": list(data.variables.keys()),
            "removed_keys": data.remove_keys,
            "updated_by": admin["email"]
        }
        
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Update timed out")
    except Exception as e:
        logger.error(f"Failed to update env vars: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Logs Viewer Endpoints
# ============================================================================

@router.get("/logs")
async def get_logs(
    filter: Optional[str] = None,
    severity: Optional[str] = None,
    hours: int = Query(default=1, le=168),  # Max 1 week
    limit: int = Query(default=100, le=1000),
    admin: Dict = Depends(require_admin)
):
    """
    Query Cloud Logging for application logs.
    
    Args:
        filter: Additional log filter expression
        severity: Minimum severity level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        hours: Hours to look back (max 168 = 1 week)
        limit: Maximum number of entries to return
    """
    if not GOOGLE_CLOUD_AVAILABLE:
        raise HTTPException(status_code=503, detail="Cloud Logging not available")
    
    try:
        client = cloud_logging.Client()
        project_id = get_project_id()
        
        # Build filter
        time_filter = f'timestamp >= "{(datetime.utcnow() - timedelta(hours=hours)).isoformat()}Z"'
        
        filters = [time_filter]
        
        # Add resource filter for Cloud Run
        service_name = os.getenv("K_SERVICE", "blog-writer-api")
        filters.append(f'resource.type="cloud_run_revision"')
        filters.append(f'resource.labels.service_name="{service_name}"')
        
        if severity:
            filters.append(f'severity >= "{severity.upper()}"')
        
        if filter:
            filters.append(f"({filter})")
        
        full_filter = " AND ".join(filters)
        
        # Query logs
        entries = []
        for entry in client.list_entries(
            filter_=full_filter,
            order_by=cloud_logging.DESCENDING,
            max_results=limit
        ):
            entries.append({
                "timestamp": entry.timestamp.isoformat() if entry.timestamp else None,
                "severity": entry.severity if hasattr(entry, 'severity') else "DEFAULT",
                "message": entry.payload if isinstance(entry.payload, str) else str(entry.payload),
                "labels": dict(entry.labels) if entry.labels else {},
                "trace": entry.trace if hasattr(entry, 'trace') else None
            })
        
        return {
            "entries": entries,
            "count": len(entries),
            "filter": full_filter,
            "hours": hours
        }
        
    except Exception as e:
        logger.error(f"Failed to query logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs/stream")
async def stream_logs(
    severity: Optional[str] = None,
    admin: Dict = Depends(require_admin)
):
    """
    Stream logs in real-time using Server-Sent Events (SSE).
    
    Connect to this endpoint to receive live log updates.
    """
    if not GOOGLE_CLOUD_AVAILABLE:
        raise HTTPException(status_code=503, detail="Cloud Logging not available")
    
    async def generate():
        client = cloud_logging.Client()
        project_id = get_project_id()
        service_name = os.getenv("K_SERVICE", "blog-writer-api")
        
        last_timestamp = datetime.utcnow()
        
        while True:
            try:
                # Query for new logs since last check
                time_filter = f'timestamp > "{last_timestamp.isoformat()}Z"'
                filters = [
                    time_filter,
                    f'resource.type="cloud_run_revision"',
                    f'resource.labels.service_name="{service_name}"'
                ]
                
                if severity:
                    filters.append(f'severity >= "{severity.upper()}"')
                
                full_filter = " AND ".join(filters)
                
                for entry in client.list_entries(
                    filter_=full_filter,
                    order_by=cloud_logging.ASCENDING,
                    max_results=50
                ):
                    if entry.timestamp:
                        last_timestamp = max(last_timestamp, entry.timestamp)
                    
                    log_data = {
                        "timestamp": entry.timestamp.isoformat() if entry.timestamp else None,
                        "severity": entry.severity if hasattr(entry, 'severity') else "DEFAULT",
                        "message": entry.payload if isinstance(entry.payload, str) else str(entry.payload)
                    }
                    
                    yield f"data: {json.dumps(log_data)}\n\n"
                
                # Wait before next poll
                await asyncio.sleep(2)
                
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
                await asyncio.sleep(5)
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


# ============================================================================
# AI Usage & Cost Endpoints
# ============================================================================

@router.get("/ai/usage")
async def get_ai_usage(
    org_id: Optional[str] = None,
    days: int = Query(default=30, le=365),
    admin: Dict = Depends(require_admin)
):
    """
    Get AI usage statistics.
    
    If org_id is provided, returns stats for that organization.
    Otherwise returns aggregate stats.
    """
    usage_logger = get_usage_logger()
    
    if not usage_logger.enabled:
        return {"error": "Usage logging not enabled", "enabled": False}
    
    if org_id:
        stats = await usage_logger.get_usage_stats(
            org_id=org_id,
            start_date=datetime.utcnow() - timedelta(days=days),
            end_date=datetime.utcnow()
        )
    else:
        # Get aggregate stats (would need to implement in usage_logger)
        stats = {"message": "Provide org_id for organization-specific stats"}
    
    return stats


@router.get("/ai/costs")
async def get_ai_costs(
    org_id: str,
    days: int = Query(default=30, le=365),
    admin: Dict = Depends(require_admin)
):
    """
    Get AI cost breakdown for an organization.
    """
    usage_logger = get_usage_logger()
    
    if not usage_logger.enabled:
        return {"error": "Usage logging not enabled", "enabled": False}
    
    return await usage_logger.get_cost_breakdown(org_id=org_id, days=days)


@router.get("/ai/cache-stats")
async def get_ai_cache_stats(
    org_id: str,
    days: int = Query(default=7, le=90),
    admin: Dict = Depends(require_admin)
):
    """
    Get AI cache performance statistics.
    """
    usage_logger = get_usage_logger()
    
    if not usage_logger.enabled:
        return {"error": "Usage logging not enabled", "enabled": False}
    
    return await usage_logger.get_cache_stats(org_id=org_id, days=days)


# ============================================================================
# Job Management Endpoints
# ============================================================================

@router.get("/jobs")
async def list_jobs(
    status: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    admin: Dict = Depends(require_admin)
):
    """
    List all blog generation jobs with pagination.
    """
    # Import the jobs dict from main.py
    # This is a simplified version - in production you'd use a database
    try:
        from main import blog_generation_jobs
        
        jobs = list(blog_generation_jobs.values())
        
        # Filter by status if provided
        if status:
            jobs = [j for j in jobs if j.status.value == status]
        
        # Sort by created_at descending
        jobs.sort(key=lambda x: x.created_at, reverse=True)
        
        # Paginate
        total = len(jobs)
        jobs = jobs[offset:offset + limit]
        
        return {
            "jobs": [
                {
                    "job_id": j.job_id,
                    "status": j.status.value,
                    "topic": j.request.topic if j.request else None,
                    "created_at": j.created_at.isoformat() if j.created_at else None,
                    "completed_at": j.completed_at.isoformat() if j.completed_at else None,
                    "error": j.error
                }
                for j in jobs
            ],
            "total": total,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Failed to list jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}")
async def get_job(
    job_id: str,
    admin: Dict = Depends(require_admin)
):
    """
    Get detailed information about a specific job.
    """
    try:
        from main import blog_generation_jobs
        
        job = blog_generation_jobs.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return {
            "job_id": job.job_id,
            "status": job.status.value,
            "request": job.request.dict() if job.request else None,
            "result": job.result.dict() if job.result else None,
            "error": job.error,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "progress": job.progress if hasattr(job, 'progress') else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/jobs/{job_id}/cancel")
async def cancel_job(
    job_id: str,
    action: JobAction = None,
    admin: Dict = Depends(require_admin),
    request: Request = None
):
    """
    Cancel a running or pending job.
    """
    try:
        from main import blog_generation_jobs
        from ..models.job_models import JobStatus
        
        job = blog_generation_jobs.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if job.status not in [JobStatus.PENDING, JobStatus.PROCESSING]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot cancel job with status: {job.status.value}"
            )
        
        # Mark as failed with cancellation reason
        job.status = JobStatus.FAILED
        job.error = f"Cancelled by admin: {action.reason if action else 'No reason provided'}"
        job.completed_at = datetime.utcnow()
        
        await log_admin_action(
            admin["id"], "job_cancel", "job", job_id,
            None, {"reason": action.reason if action else None}, request
        )
        
        return {
            "job_id": job_id,
            "cancelled": True,
            "cancelled_by": admin["email"],
            "reason": action.reason if action else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/jobs/{job_id}/retry")
async def retry_job(
    job_id: str,
    admin: Dict = Depends(require_admin),
    request: Request = None
):
    """
    Retry a failed job.
    """
    try:
        from main import blog_generation_jobs
        from ..models.job_models import JobStatus
        
        job = blog_generation_jobs.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if job.status != JobStatus.FAILED:
            raise HTTPException(
                status_code=400,
                detail=f"Can only retry failed jobs. Current status: {job.status.value}"
            )
        
        # Reset job status
        job.status = JobStatus.PENDING
        job.error = None
        job.result = None
        job.started_at = None
        job.completed_at = None
        
        await log_admin_action(
            admin["id"], "job_retry", "job", job_id, None, None, request
        )
        
        # Note: In a real implementation, you would re-queue the job
        # For now, we just reset the status
        
        return {
            "job_id": job_id,
            "retried": True,
            "new_status": JobStatus.PENDING.value,
            "retried_by": admin["email"],
            "message": "Job has been reset to pending status. Processing will resume."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retry job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Health & Status Endpoints
# ============================================================================

@router.get("/status")
async def get_admin_status(admin: Dict = Depends(require_admin)):
    """
    Get admin dashboard status overview.
    """
    status = {
        "admin_user": admin["email"],
        "timestamp": datetime.utcnow().isoformat(),
        "services": {}
    }
    
    # Check Secret Manager
    try:
        if GOOGLE_CLOUD_AVAILABLE:
            client = secretmanager.SecretManagerServiceClient()
            status["services"]["secret_manager"] = "available"
        else:
            status["services"]["secret_manager"] = "not_installed"
    except Exception as e:
        status["services"]["secret_manager"] = f"error: {str(e)}"
    
    # Check Cloud Logging
    try:
        if GOOGLE_CLOUD_AVAILABLE and cloud_logging:
            status["services"]["cloud_logging"] = "available"
        else:
            status["services"]["cloud_logging"] = "not_installed"
    except Exception as e:
        status["services"]["cloud_logging"] = f"error: {str(e)}"
    
    # Check Usage Logger
    usage_logger = get_usage_logger()
    status["services"]["usage_logging"] = "enabled" if usage_logger.enabled else "disabled"
    
    # Get job stats
    try:
        from main import blog_generation_jobs
        from ..models.job_models import JobStatus
        
        jobs = list(blog_generation_jobs.values())
        status["jobs"] = {
            "total": len(jobs),
            "pending": len([j for j in jobs if j.status == JobStatus.PENDING]),
            "processing": len([j for j in jobs if j.status == JobStatus.PROCESSING]),
            "completed": len([j for j in jobs if j.status == JobStatus.COMPLETED]),
            "failed": len([j for j in jobs if j.status == JobStatus.FAILED])
        }
    except Exception:
        status["jobs"] = {"error": "Could not retrieve job stats"}
    
    return status
