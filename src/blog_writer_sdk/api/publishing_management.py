"""
API endpoints for multi-CMS publishing management.
"""
import logging
from typing import List, Optional, Dict, Any, Tuple
from fastapi import APIRouter, HTTPException, Depends, Header, Query
from datetime import datetime

from ..models.publishing_models import (
    CMSIntegration,
    CreateIntegrationRequest,
    UpdateIntegrationRequest,
    PublishingTargetsResponse,
    PublishingTarget,
    PublishBlogRequest,
    PublishBlogResponse,
    UserRole,
    BlogPostWithCosts,
    CMSProvider,
    IntegrationStatus,
)
from ..services.publishing_service import PublishingService
from ..integrations.supabase_client import SupabaseClient
from ..models.blog_models import BlogGenerationResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/publishing", tags=["Publishing"])


# Dependencies
def get_supabase_client() -> Optional[SupabaseClient]:
    """Get Supabase client."""
    try:
        return SupabaseClient()
    except Exception:
        return None


def get_publishing_service() -> PublishingService:
    """Get publishing service."""
    supabase = get_supabase_client()
    return PublishingService(supabase_client=supabase)


def get_user_role(
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    x_org_id: Optional[str] = Header(None, alias="X-Org-ID"),
) -> Tuple[Optional[UserRole], Optional[str], Optional[str]]:
    """
    Extract user role and context from headers.
    
    Returns:
        Tuple of (role, user_id, org_id)
    """
    role = None
    if x_user_role:
        try:
            role = UserRole(x_user_role.lower())
        except ValueError:
            pass
    
    return role, x_user_id, x_org_id


def require_role(allowed_roles: List[UserRole]):
    """Dependency to require specific roles."""
    def check_role(
        role_ctx: Tuple[Optional[UserRole], Optional[str], Optional[str]] = Depends(get_user_role)
    ):
        role, user_id, org_id = role_ctx
        
        if not role:
            raise HTTPException(status_code=401, detail="User role required")
        
        if role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied. Required roles: {[r.value for r in allowed_roles]}"
            )
        
        if not org_id:
            raise HTTPException(status_code=400, detail="Organization ID required")
        
        return role, user_id, org_id
    
    return check_role


# Integration Management Endpoints
@router.get("/integrations", response_model=List[CMSIntegration])
async def list_integrations(
    provider_type: Optional[CMSProvider] = Query(None, description="Filter by provider type"),
    role_ctx: Tuple[UserRole, str, str] = Depends(require_role([UserRole.admin, UserRole.owner, UserRole.system_admin, UserRole.super_admin])),
    service: PublishingService = Depends(get_publishing_service),
):
    """
    List integrations for the organization.
    
    Requires: admin, owner, system_admin, or super_admin role.
    """
    role, user_id, org_id = role_ctx
    
    try:
        integrations = await service.get_integrations(org_id, provider_type)
        return integrations
    except Exception as e:
        logger.error(f"Failed to list integrations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list integrations: {str(e)}")


@router.post("/integrations", response_model=CMSIntegration)
async def create_integration(
    request: CreateIntegrationRequest,
    role_ctx: Tuple[UserRole, str, str] = Depends(require_role([UserRole.admin, UserRole.owner, UserRole.system_admin, UserRole.super_admin])),
    service: PublishingService = Depends(get_publishing_service),
):
    """
    Create a new integration.
    
    Requires: admin, owner, system_admin, or super_admin role.
    """
    role, user_id, org_id = role_ctx
    
    # Verify org_id matches
    if request.org_id != org_id:
        raise HTTPException(status_code=403, detail="Cannot create integration for different organization")
    
    if not service.supabase_client:
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        env = service.supabase_client.environment
        table = f"integrations_{env}"
        
        # Check if default already exists for this provider
        if request.is_default:
            existing = await service.get_integrations(org_id, request.type)
            for existing_int in existing:
                if existing_int.is_default and existing_int.type == request.type:
                    # Unset existing default
                    service.supabase_client.client.table(table).update({
                        "is_default": False
                    }).eq("id", existing_int.id).execute()
        
        # Create integration
        integration_data = {
            "org_id": request.org_id,
            "type": request.type.value,
            "site_id": request.site_id,
            "site_name": request.site_name,
            "api_key": request.api_key,  # TODO: Encrypt
            "api_secret": request.api_secret,  # TODO: Encrypt
            "collection_ids": request.collection_ids,
            "is_default": request.is_default,
            "status": IntegrationStatus.active.value,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        
        response = service.supabase_client.client.table(table).insert(integration_data).execute()
        
        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to create integration")
        
        # Clear cache
        service.clear_cache(org_id)
        
        # Audit log
        await service.log_audit(
            user_id=user_id,
            org_id=org_id,
            action="create_integration",
            resource_type="integration",
            resource_id=response.data[0]["id"],
            metadata={
                "type": request.type.value,
                "site_id": request.site_id,
                "is_default": request.is_default
            }
        )
        
        return CMSIntegration(**response.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create integration: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create integration: {str(e)}")


@router.patch("/integrations/{integration_id}", response_model=CMSIntegration)
async def update_integration(
    integration_id: str,
    request: UpdateIntegrationRequest,
    role_ctx: Tuple[UserRole, str, str] = Depends(require_role([UserRole.admin, UserRole.owner, UserRole.system_admin, UserRole.super_admin])),
    service: PublishingService = Depends(get_publishing_service),
):
    """
    Update an integration.
    
    Requires: admin, owner, system_admin, or super_admin role.
    """
    role, user_id, org_id = role_ctx
    
    if not service.supabase_client:
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        env = service.supabase_client.environment
        table = f"integrations_{env}"
        
        # Verify integration belongs to org
        existing = service.supabase_client.client.table(table).select("*").eq("id", integration_id).eq("org_id", org_id).execute()
        
        if not existing.data:
            raise HTTPException(status_code=404, detail="Integration not found")
        
        existing_integration = CMSIntegration(**existing.data[0])
        
        # Handle default change
        if request.is_default is not None and request.is_default:
            # Unset other defaults for this provider
            other_defaults = service.supabase_client.client.table(table).select("id").eq("org_id", org_id).eq("type", existing_integration.type.value).eq("is_default", True).neq("id", integration_id).execute()
            
            for other in other_defaults.data:
                service.supabase_client.client.table(table).update({
                    "is_default": False
                }).eq("id", other["id"]).execute()
        
        # Build update data
        update_data = {"updated_at": datetime.utcnow().isoformat()}
        
        if request.site_name is not None:
            update_data["site_name"] = request.site_name
        if request.api_key is not None:
            update_data["api_key"] = request.api_key  # TODO: Encrypt
        if request.api_secret is not None:
            update_data["api_secret"] = request.api_secret  # TODO: Encrypt
        if request.collection_ids is not None:
            update_data["collection_ids"] = request.collection_ids
        if request.is_default is not None:
            update_data["is_default"] = request.is_default
        if request.status is not None:
            update_data["status"] = request.status.value
        
        # Update
        response = service.supabase_client.client.table(table).update(update_data).eq("id", integration_id).eq("org_id", org_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to update integration")
        
        # Clear cache
        service.clear_cache(org_id)
        
        # Audit log
        await service.log_audit(
            user_id=user_id,
            org_id=org_id,
            action="update_integration",
            resource_type="integration",
            resource_id=integration_id,
            metadata={
                "updates": update_data,
                "is_default_changed": request.is_default is not None
            }
        )
        
        return CMSIntegration(**response.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update integration: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update integration: {str(e)}")


@router.delete("/integrations/{integration_id}")
async def delete_integration(
    integration_id: str,
    role_ctx: Tuple[UserRole, str, str] = Depends(require_role([UserRole.admin, UserRole.owner, UserRole.system_admin, UserRole.super_admin])),
    service: PublishingService = Depends(get_publishing_service),
):
    """
    Delete (disable) an integration.
    
    Requires: admin, owner, system_admin, or super_admin role.
    """
    role, user_id, org_id = role_ctx
    
    if not service.supabase_client:
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        env = service.supabase_client.environment
        table = f"integrations_{env}"
        
        # Verify integration belongs to org
        existing = service.supabase_client.client.table(table).select("*").eq("id", integration_id).eq("org_id", org_id).execute()
        
        if not existing.data:
            raise HTTPException(status_code=404, detail="Integration not found")
        
        # Soft delete (set status to inactive)
        service.supabase_client.client.table(table).update({
            "status": IntegrationStatus.inactive.value,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", integration_id).eq("org_id", org_id).execute()
        
        # Clear cache
        service.clear_cache(org_id)
        
        # Audit log
        await service.log_audit(
            user_id=user_id,
            org_id=org_id,
            action="delete_integration",
            resource_type="integration",
            resource_id=integration_id,
            metadata={
                "site_id": existing.data[0].get("site_id"),
                "type": existing.data[0].get("type")
            }
        )
        
        return {"success": True, "message": "Integration disabled"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete integration: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete integration: {str(e)}")


# Publishing Targets Endpoint
@router.get("/targets", response_model=PublishingTargetsResponse)
async def get_publishing_targets(
    role_ctx: Tuple[Optional[UserRole], Optional[str], Optional[str]] = Depends(get_user_role),
    service: PublishingService = Depends(get_publishing_service),
):
    """
    Get available publishing targets for the organization.
    
    Available to all authenticated users.
    """
    role, user_id, org_id = role_ctx
    
    if not org_id:
        raise HTTPException(status_code=400, detail="Organization ID required")
    
    try:
        targets_data = await service.get_publishing_targets(org_id)
        
        # Convert to response model
        sites = [
            {
                "id": site["id"],
                "name": site["name"],
                "provider": CMSProvider(site["provider"]),
                "collections": site["collections"],
                "is_default": site["is_default"]
            }
            for site in targets_data["sites"]
        ]
        
        default = None
        if targets_data.get("default"):
            default = PublishingTarget(
                cms_provider=CMSProvider(targets_data["default"]["provider"]),
                site_id=targets_data["default"]["site_id"],
                collection_id=targets_data["default"].get("collection_id"),
                site_name=None
            )
        
        return PublishingTargetsResponse(
            providers=targets_data["providers"],
            sites=sites,
            default=default
        )
        
    except Exception as e:
        logger.error(f"Failed to get publishing targets: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get publishing targets: {str(e)}")


# Publishing Endpoint
@router.post("/publish", response_model=PublishBlogResponse)
async def publish_blog(
    request: PublishBlogRequest,
    role_ctx: Tuple[Optional[UserRole], Optional[str], Optional[str]] = Depends(get_user_role),
    service: PublishingService = Depends(get_publishing_service),
    supabase: Optional[SupabaseClient] = Depends(get_supabase_client),
):
    """
    Publish a blog post to the selected CMS target.
    
    Available to writers, editors, admins, and owners.
    
    Flow:
    1. Fetch blog post from database
    2. Resolve publishing target (use stored target or request override, fallback to default)
    3. Validate target belongs to org
    4. Publish to CMS
    5. Update blog post with publish status and remote IDs
    6. Log audit and usage
    """
    role, user_id, org_id = role_ctx
    
    if not org_id:
        raise HTTPException(status_code=400, detail="Organization ID required")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID required")
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        # Fetch blog post from database
        blog_post = await supabase.get_blog_post(request.blog_id, user_id=user_id)
        
        if not blog_post:
            raise HTTPException(status_code=404, detail="Blog post not found")
        
        # Verify org_id matches
        if blog_post.get("org_id") != org_id:
            raise HTTPException(status_code=403, detail="Blog post does not belong to this organization")
        
        # Build BlogGenerationResult from stored data
        blog_result = BlogGenerationResult(
            title=blog_post.get("title", ""),
            content=blog_post.get("content", ""),
            excerpt=blog_post.get("excerpt"),
            meta_title=blog_post.get("meta_title"),
            meta_description=blog_post.get("meta_description"),
            keywords=blog_post.get("keywords", []),
            citations=blog_post.get("citations", []),
            seo_metadata=blog_post.get("seo_metadata", {}),
            structured_data=blog_post.get("structured_data", {}),
            quality_score=blog_post.get("quality_score"),
            seo_score=blog_post.get("seo_score"),
            readability_score=blog_post.get("readability_score"),
            word_count=blog_post.get("word_count"),
            total_cost=blog_post.get("total_cost", 0.0),
            cost_breakdown=blog_post.get("cost_breakdown")
        )
        
        # Resolve publishing target
        # Priority: request override > stored target > default
        target = None
        provider_type = None
        
        if request.cms_provider:
            provider_type = request.cms_provider
            target = PublishingTarget(
                cms_provider=request.cms_provider,
                site_id=request.site_id or blog_post.get("site_id") or "",
                collection_id=request.collection_id or blog_post.get("collection_id")
            )
        elif blog_post.get("cms_provider"):
            provider_type = CMSProvider(blog_post["cms_provider"])
            target = PublishingTarget(
                cms_provider=provider_type,
                site_id=blog_post.get("site_id", ""),
                collection_id=blog_post.get("collection_id")
            )
        
        # Validate target if provided
        if target and target.site_id:
            # Verify site belongs to org
            integration = await service.get_integration_by_site_id(
                org_id, target.cms_provider, target.site_id
            )
            if not integration:
                raise HTTPException(
                    status_code=400,
                    detail=f"Site {target.site_id} not found for this organization"
                )
            
            # Validate collection_id for Webflow
            if target.cms_provider == CMSProvider.webflow and not target.collection_id:
                raise HTTPException(
                    status_code=400,
                    detail="Collection ID is required for Webflow publishing"
                )
            
            # Verify collection exists in integration
            if target.collection_id and target.collection_id not in integration.collection_ids:
                raise HTTPException(
                    status_code=400,
                    detail=f"Collection {target.collection_id} not found for site {target.site_id}"
                )
        
        # Publish
        publish_response = await service.publish_blog(
            blog_result=blog_result,
            org_id=org_id,
            target=target,
            provider_type=provider_type,
            publish=request.publish
        )
        
        # Update blog post with publish status
        update_data = {
            "cms_provider": publish_response.cms_provider.value,
            "site_id": publish_response.site_id,
            "collection_id": publish_response.collection_id,
            "published_url": publish_response.published_url,
            "remote_id": publish_response.remote_id,
            "publish_status": "success" if publish_response.success else "failed",
            "publish_error": publish_response.error_message,
        }
        
        if publish_response.success:
            update_data["published_at"] = datetime.utcnow().isoformat()
            update_data["publishing_target"] = {
                "cms_provider": publish_response.cms_provider.value,
                "site_id": publish_response.site_id,
                "collection_id": publish_response.collection_id
            }
        
        await supabase.update_blog_post(request.blog_id, update_data, user_id=user_id)
        
        # Log audit
        await service.log_audit(
            user_id=user_id,
            org_id=org_id,
            action="publish_blog",
            resource_type="blog_post",
            resource_id=request.blog_id,
            metadata={
                "cms_provider": publish_response.cms_provider.value,
                "site_id": publish_response.site_id,
                "success": publish_response.success,
                "published_url": publish_response.published_url
            }
        )
        
        # Log usage (only if successful and cost available)
        if publish_response.success and blog_post.get("total_cost"):
            await service.log_usage(
                org_id=org_id,
                site_id=publish_response.site_id,
                user_id=user_id,
                resource_type="blog_publishing",
                resource_id=request.blog_id,
                total_cost=blog_post.get("total_cost", 0.0),
                cost_breakdown=blog_post.get("cost_breakdown"),
                metadata={
                    "cms_provider": publish_response.cms_provider.value,
                    "published_url": publish_response.published_url
                }
            )
        
        return publish_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to publish blog: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to publish blog: {str(e)}")


# Blog Post/Draft Publishing Target Management
@router.patch("/drafts/{draft_id}/target", response_model=Dict[str, Any])
async def update_draft_publishing_target(
    draft_id: str,
    target: PublishingTarget,
    role_ctx: Tuple[Optional[UserRole], Optional[str], Optional[str]] = Depends(get_user_role),
    service: PublishingService = Depends(get_publishing_service),
    supabase: Optional[SupabaseClient] = Depends(get_supabase_client),
):
    """
    Update publishing target for a draft/blog post.
    
    Available to writers, editors, admins, and owners.
    """
    role, user_id, org_id = role_ctx
    
    if not org_id:
        raise HTTPException(status_code=400, detail="Organization ID required")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID required")
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        # Verify draft exists and belongs to org
        draft = await supabase.get_blog_post(draft_id, user_id=user_id)
        
        if not draft:
            raise HTTPException(status_code=404, detail="Draft not found")
        
        if draft.get("org_id") != org_id:
            raise HTTPException(status_code=403, detail="Draft does not belong to this organization")
        
        # Validate target
        integration = await service.get_integration_by_site_id(
            org_id, target.cms_provider, target.site_id
        )
        
        if not integration:
            raise HTTPException(
                status_code=400,
                detail=f"Site {target.site_id} not found for this organization"
            )
        
        # Validate collection for Webflow
        if target.cms_provider == CMSProvider.webflow:
            if not target.collection_id:
                raise HTTPException(
                    status_code=400,
                    detail="Collection ID is required for Webflow"
                )
            if target.collection_id not in integration.collection_ids:
                raise HTTPException(
                    status_code=400,
                    detail=f"Collection {target.collection_id} not found for site {target.site_id}"
                )
        
        # Update draft with target
        update_data = {
            "cms_provider": target.cms_provider.value,
            "site_id": target.site_id,
            "collection_id": target.collection_id,
            "publishing_target": {
                "cms_provider": target.cms_provider.value,
                "site_id": target.site_id,
                "collection_id": target.collection_id,
                "site_name": target.site_name
            }
        }
        
        updated = await supabase.update_blog_post(draft_id, update_data, user_id=user_id)
        
        # Audit log
        await service.log_audit(
            user_id=user_id,
            org_id=org_id,
            action="update_publishing_target",
            resource_type="blog_post",
            resource_id=draft_id,
            metadata={
                "cms_provider": target.cms_provider.value,
                "site_id": target.site_id,
                "collection_id": target.collection_id
            }
        )
        
        return {
            "success": True,
            "draft_id": draft_id,
            "publishing_target": target.dict(),
            "message": "Publishing target updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update publishing target: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update publishing target: {str(e)}")


# Blog Posts List with Role-Based Cost Filtering
@router.get("/blog-posts", response_model=List[BlogPostWithCosts])
async def list_blog_posts(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    role_ctx: Tuple[Optional[UserRole], Optional[str], Optional[str]] = Depends(get_user_role),
    supabase: Optional[SupabaseClient] = Depends(get_supabase_client),
):
    """
    List blog posts with role-based cost visibility.
    
    Costs are only visible to admins, owners, system_admin, and super_admin.
    """
    role, user_id, org_id = role_ctx
    
    if not org_id:
        raise HTTPException(status_code=400, detail="Organization ID required")
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        # Determine if user can view costs
        can_view_costs = role in [
            UserRole.admin,
            UserRole.owner,
            UserRole.system_admin,
            UserRole.super_admin
        ]
        
        # Fetch blog posts (filtered by org_id)
        table_name = supabase._get_table_name("blog_posts")
        query = supabase.client.table(table_name).select("*").eq("org_id", org_id)
        
        if status:
            query = query.eq("status", status)
        
        query = query.order("created_at", desc=True).range(offset, offset + limit - 1)
        result = query.execute()
        
        # Convert to response models with role-based cost filtering
        posts = []
        for post_data in result.data:
            post = BlogPostWithCosts.from_blog_post(
                post_data,
                user_role=role,
                include_costs=can_view_costs
            )
            posts.append(post)
        
        return posts
        
    except Exception as e:
        logger.error(f"Failed to list blog posts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list blog posts: {str(e)}")


# Get Single Blog Post with Role-Based Cost Filtering
@router.get("/blog-posts/{post_id}", response_model=BlogPostWithCosts)
async def get_blog_post(
    post_id: str,
    role_ctx: Tuple[Optional[UserRole], Optional[str], Optional[str]] = Depends(get_user_role),
    supabase: Optional[SupabaseClient] = Depends(get_supabase_client),
):
    """
    Get a single blog post with role-based cost visibility.
    
    Costs are only visible to admins, owners, system_admin, and super_admin.
    """
    role, user_id, org_id = role_ctx
    
    if not org_id:
        raise HTTPException(status_code=400, detail="Organization ID required")
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        # Fetch blog post
        post_data = await supabase.get_blog_post(post_id, user_id=user_id)
        
        if not post_data:
            raise HTTPException(status_code=404, detail="Blog post not found")
        
        # Verify org_id matches
        if post_data.get("org_id") != org_id:
            raise HTTPException(status_code=403, detail="Blog post does not belong to this organization")
        
        # Determine if user can view costs
        can_view_costs = role in [
            UserRole.admin,
            UserRole.owner,
            UserRole.system_admin,
            UserRole.super_admin
        ]
        
        # Convert to response model with role-based cost filtering
        post = BlogPostWithCosts.from_blog_post(
            post_data,
            user_role=role,
            include_costs=can_view_costs
        )
        
        return post
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get blog post: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get blog post: {str(e)}")

