"""
Publishing service for multi-CMS support with target selection and routing.
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from ..models.publishing_models import (
    CMSProvider,
    PublishingTarget,
    PublishingMetadata,
    PublishBlogRequest,
    PublishBlogResponse,
    IntegrationStatus,
    CMSIntegration,
    PublishingTargetRecord,
    CreatePublishingTargetRequest,
    UpdatePublishingTargetRequest,
    PublishingTargetStatus,
)
from ..models.blog_models import BlogGenerationResult
from ..integrations.webflow_integration import WebflowClient, WebflowPublisher
from ..integrations.shopify_integration import ShopifyClient, ShopifyPublisher
from ..integrations.supabase_client import SupabaseClient

logger = logging.getLogger(__name__)


class PublishingService:
    """
    Service for managing multi-CMS publishing with target selection.
    
    Handles:
    - Integration management
    - Publishing target selection
    - CMS routing
    - Default fallback logic
    """
    
    def __init__(self, supabase_client: Optional[SupabaseClient] = None):
        """
        Initialize publishing service.
        
        Args:
            supabase_client: Supabase client for database operations
        """
        self.supabase_client = supabase_client
        self.logger = logging.getLogger(__name__)
        self._integration_cache: Dict[str, List[CMSIntegration]] = {}
        self._cache_ttl = 300  # 5 minutes
    
    async def get_integrations(
        self,
        org_id: str,
        provider_type: Optional[CMSProvider] = None
    ) -> List[CMSIntegration]:
        """
        Get integrations for an organization.
        
        Args:
            org_id: Organization ID
            provider_type: Optional filter by provider type
            
        Returns:
            List of integrations
        """
        cache_key = f"{org_id}:{provider_type.value if provider_type else 'all'}"
        
        # Check cache
        if cache_key in self._integration_cache:
            return self._integration_cache[cache_key]
        
        if not self.supabase_client:
            self.logger.warning("Supabase client not available, returning empty list")
            return []
        
        try:
            env = self.supabase_client.environment
            table = f"integrations_{env}"
            
            query = self.supabase_client.client.table(table).select("*").eq("org_id", org_id)
            
            if provider_type:
                query = query.eq("type", provider_type.value)
            
            response = query.execute()
            
            integrations = [
                CMSIntegration(**item) for item in response.data
            ]
            
            # Cache results
            self._integration_cache[cache_key] = integrations
            
            return integrations
            
        except Exception as e:
            self.logger.error(f"Failed to fetch integrations: {e}", exc_info=True)
            return []
    
    async def get_default_integration(
        self,
        org_id: str,
        provider_type: CMSProvider
    ) -> Optional[CMSIntegration]:
        """
        Get default integration for a provider.
        
        Args:
            org_id: Organization ID
            provider_type: CMS provider type
            
        Returns:
            Default integration or None
        """
        integrations = await self.get_integrations(org_id, provider_type)
        
        # Find default
        for integration in integrations:
            if integration.is_default and integration.status == IntegrationStatus.active:
                return integration
        
        # If no default, return first active integration
        for integration in integrations:
            if integration.status == IntegrationStatus.active:
                return integration
        
        return None
    
    async def get_publishing_targets(
        self,
        org_id: str
    ) -> Dict[str, Any]:
        """
        Get available publishing targets for an organization.
        
        Args:
            org_id: Organization ID
            
        Returns:
            Publishing targets response
        """
        integrations = await self.get_integrations(org_id)
        
        providers = set()
        sites = []
        default_target = None
        
        for integration in integrations:
            if integration.status != IntegrationStatus.active:
                continue
            
            providers.add(integration.type.value)
            
            # Create site entry
            site = {
                "id": integration.site_id,
                "name": integration.site_name,
                "provider": integration.type.value,
                "collections": integration.collection_ids,
                "is_default": integration.is_default
            }
            sites.append(site)
            
            # Set default target
            if integration.is_default and not default_target:
                default_target = {
                    "provider": integration.type.value,
                    "site_id": integration.site_id,
                    "collection_id": integration.collection_ids[0] if integration.collection_ids else None
                }
        
        return {
            "providers": list(providers),
            "sites": sites,
            "default": default_target
        }

    async def list_publishing_targets(
        self,
        org_id: str,
        include_inactive: bool = False,
    ) -> List[PublishingTargetRecord]:
        """
        List publishing targets stored in the publishing_targets table.
        """
        if not self.supabase_client:
            self.logger.warning("Supabase client not available, returning empty publishing targets list")
            return []

        records = await self.supabase_client.list_publishing_targets(org_id, include_inactive=include_inactive)
        return [PublishingTargetRecord(**item) for item in records]

    async def get_publishing_target(self, target_id: str, org_id: str) -> Optional[PublishingTargetRecord]:
        """Fetch a single publishing target by id/org."""
        if not self.supabase_client:
            self.logger.warning("Supabase client not available, cannot fetch publishing target")
            return None
        record = await self.supabase_client.get_publishing_target(target_id, org_id)
        return PublishingTargetRecord(**record) if record else None

    async def _unset_other_defaults(self, org_id: str, target_type: CMSProvider, exclude_id: Optional[str] = None):
        """Unset other defaults for the same provider when a new default is set."""
        if not self.supabase_client:
            return
        table = self.supabase_client._get_table_name("publishing_targets")
        query = (
            self.supabase_client.client.table(table)
            .update({"is_default": False, "updated_at": datetime.utcnow().isoformat()})
            .eq("org_id", org_id)
            .eq("type", target_type.value)
            .eq("is_default", True)
        )
        if exclude_id:
            query = query.neq("id", exclude_id)
        query.execute()

    async def create_publishing_target(
        self,
        request: CreatePublishingTargetRequest,
    ) -> PublishingTargetRecord:
        """Create a publishing target in Supabase."""
        if not self.supabase_client:
            raise ValueError("Supabase client not available")

        now = datetime.utcnow().isoformat()
        target_data = {
            "org_id": request.org_id,
            "name": request.name,
            "type": request.type.value,
            "site_url": request.site_url,
            "status": request.status.value,
            "is_default": request.is_default,
            "config": request.config,
            "credentials": request.credentials,
            "metadata": request.metadata,
            "created_at": now,
            "updated_at": now,
        }

        if request.is_default:
            await self._unset_other_defaults(request.org_id, request.type)

        record = await self.supabase_client.create_publishing_target(target_data)
        created = PublishingTargetRecord(**record)

        created_by = request.metadata.get("created_by") if request.metadata else None
        if created_by:
            await self.log_audit(
                user_id=created_by,
                org_id=request.org_id,
                action="create_publishing_target",
                resource_type="publishing_target",
                resource_id=created.id,
                metadata={"type": request.type.value, "is_default": request.is_default},
            )

        return created

    async def update_publishing_target(
        self,
        target_id: str,
        org_id: str,
        request: UpdatePublishingTargetRequest,
    ) -> PublishingTargetRecord:
        """Update a publishing target."""
        if not self.supabase_client:
            raise ValueError("Supabase client not available")

        existing = await self.get_publishing_target(target_id, org_id)
        if not existing:
            raise ValueError("Publishing target not found")

        updates: Dict[str, Any] = {"updated_at": datetime.utcnow().isoformat()}
        if request.name is not None:
            updates["name"] = request.name
        if request.site_url is not None:
            updates["site_url"] = request.site_url
        if request.status is not None:
            updates["status"] = request.status.value
        if request.is_default is not None:
            updates["is_default"] = request.is_default
        if request.config is not None:
            updates["config"] = request.config
        if request.credentials is not None:
            updates["credentials"] = request.credentials
        if request.metadata is not None:
            updates["metadata"] = request.metadata

        # Handle default promotion
        if request.is_default:
            await self._unset_other_defaults(org_id, existing.type, exclude_id=target_id)

        record = await self.supabase_client.update_publishing_target(target_id, org_id, updates)
        updated = PublishingTargetRecord(**record)

        updated_by = (request.metadata or {}).get("updated_by") if request.metadata else None
        if updated_by:
            await self.log_audit(
                user_id=updated_by,
                org_id=org_id,
                action="update_publishing_target",
                resource_type="publishing_target",
                resource_id=target_id,
                metadata={"updates": updates},
            )

        return updated

    async def delete_publishing_target(self, target_id: str, org_id: str) -> bool:
        """Soft-delete a publishing target."""
        if not self.supabase_client:
            raise ValueError("Supabase client not available")

        existing = await self.get_publishing_target(target_id, org_id)
        if not existing:
            raise ValueError("Publishing target not found")

        deleted = await self.supabase_client.soft_delete_publishing_target(target_id, org_id)

        if deleted:
            deleted_by = existing.metadata.get("updated_by") if existing.metadata else None
            if deleted_by:
                await self.log_audit(
                    user_id=deleted_by,
                    org_id=org_id,
                    action="delete_publishing_target",
                    resource_type="publishing_target",
                    resource_id=target_id,
                    metadata={"type": existing.type.value},
                )

        return deleted
    
    async def resolve_publishing_target(
        self,
        org_id: str,
        target: Optional[PublishingTarget] = None,
        provider_type: Optional[CMSProvider] = None
    ) -> PublishingTarget:
        """
        Resolve publishing target with fallback to default.
        
        Args:
            org_id: Organization ID
            target: Explicit target (optional)
            provider_type: Provider type if target not specified
            
        Returns:
            Resolved publishing target
            
        Raises:
            ValueError: If no target and no default available
        """
        if target:
            # Validate target belongs to org
            integrations = await self.get_integrations(org_id, target.cms_provider)
            site_exists = any(
                i.site_id == target.site_id and i.status == IntegrationStatus.active
                for i in integrations
            )
            
            if not site_exists:
                raise ValueError(f"Site {target.site_id} not found for organization {org_id}")
            
            return target
        
        # Fallback to default
        if not provider_type:
            raise ValueError("No publishing target specified and no provider type provided")
        
        default_integration = await self.get_default_integration(org_id, provider_type)
        
        if not default_integration:
            raise ValueError(
                f"No publishing target selected and no default configured for {provider_type.value}"
            )
        
        return PublishingTarget(
            cms_provider=default_integration.type,
            site_id=default_integration.site_id,
            collection_id=default_integration.collection_ids[0] if default_integration.collection_ids else None,
            site_name=default_integration.site_name
        )
    
    async def publish_blog(
        self,
        blog_result: BlogGenerationResult,
        org_id: str,
        target: Optional[PublishingTarget] = None,
        provider_type: Optional[CMSProvider] = None,
        publish: bool = True
    ) -> PublishBlogResponse:
        """
        Publish blog to CMS using resolved target.
        
        Args:
            blog_result: Generated blog content
            org_id: Organization ID
            target: Publishing target (optional)
            provider_type: Provider type if target not specified
            publish: Whether to publish immediately
            
        Returns:
            Publish response
        """
        # Resolve target
        resolved_target = await self.resolve_publishing_target(org_id, target, provider_type)
        
        # Get integration for credentials - find by site_id, not just default
        integrations = await self.get_integrations(org_id, resolved_target.cms_provider)
        integration = None
        
        # Find integration matching the target site_id
        for intg in integrations:
            if intg.site_id == resolved_target.site_id and intg.status == IntegrationStatus.active:
                integration = intg
                break
        
        # Fallback to default if site_id doesn't match
        if not integration:
            integration = await self.get_default_integration(org_id, resolved_target.cms_provider)
        
        if not integration:
            raise ValueError(f"No active integration found for {resolved_target.cms_provider.value} and site {resolved_target.site_id}")
        
        # Route to appropriate CMS client
        try:
            if resolved_target.cms_provider == CMSProvider.webflow:
                return await self._publish_to_webflow(
                    blog_result,
                    integration,
                    resolved_target,
                    publish
                )
            elif resolved_target.cms_provider == CMSProvider.shopify:
                return await self._publish_to_shopify(
                    blog_result,
                    integration,
                    resolved_target,
                    publish
                )
            elif resolved_target.cms_provider == CMSProvider.wordpress:
                return await self._publish_to_wordpress(
                    blog_result,
                    integration,
                    resolved_target,
                    publish
                )
            else:
                raise ValueError(f"Unsupported CMS provider: {resolved_target.cms_provider.value}")
                
        except Exception as e:
            self.logger.error(f"Failed to publish blog: {e}", exc_info=True)
            return PublishBlogResponse(
                success=False,
                cms_provider=resolved_target.cms_provider,
                site_id=resolved_target.site_id,
                collection_id=resolved_target.collection_id,
                error_message=str(e)
            )
    
    async def _publish_to_webflow(
        self,
        blog_result: BlogGenerationResult,
        integration: CMSIntegration,
        target: PublishingTarget,
        publish: bool
    ) -> PublishBlogResponse:
        """Publish to Webflow."""
        if not target.collection_id:
            raise ValueError("Collection ID is required for Webflow publishing")
        
        client = WebflowClient(
            api_token=integration.api_key,
            site_id=target.site_id,
            collection_id=target.collection_id
        )
        
        publisher = WebflowPublisher(client)
        
        result = await publisher.publish_with_media(
            blog_result=blog_result,
            media_files=[],
            publish=publish
        )
        
        return PublishBlogResponse(
            success=True,
            cms_provider=CMSProvider.webflow,
            site_id=target.site_id,
            collection_id=target.collection_id,
            published_url=result.get("published_url"),
            remote_id=result.get("item_id")
        )
    
    async def _publish_to_shopify(
        self,
        blog_result: BlogGenerationResult,
        integration: CMSIntegration,
        target: PublishingTarget,
        publish: bool
    ) -> PublishBlogResponse:
        """Publish to Shopify."""
        client = ShopifyClient(
            shop_domain=target.site_id,  # Shopify uses shop domain as site_id
            access_token=integration.api_key
        )
        
        publisher = ShopifyPublisher(client)
        
        result = await publisher.publish_blog_post(
            blog_result=blog_result,
            publish=publish
        )
        
        return PublishBlogResponse(
            success=True,
            cms_provider=CMSProvider.shopify,
            site_id=target.site_id,
            published_url=result.get("published_url"),
            remote_id=result.get("article_id")
        )
    
    async def _publish_to_wordpress(
        self,
        blog_result: BlogGenerationResult,
        integration: CMSIntegration,
        target: PublishingTarget,
        publish: bool
    ) -> PublishBlogResponse:
        """Publish to WordPress."""
        # WordPress integration would go here
        # For now, raise not implemented
        raise NotImplementedError("WordPress publishing not yet implemented")
    
    def clear_cache(self, org_id: Optional[str] = None):
        """Clear integration cache."""
        if org_id:
            # Clear specific org cache
            keys_to_remove = [k for k in self._integration_cache.keys() if k.startswith(f"{org_id}:")]
            for key in keys_to_remove:
                del self._integration_cache[key]
        else:
            # Clear all cache
            self._integration_cache.clear()
    
    async def get_integration_by_site_id(
        self,
        org_id: str,
        provider_type: CMSProvider,
        site_id: str
    ) -> Optional[CMSIntegration]:
        """
        Get integration by site ID.
        
        Args:
            org_id: Organization ID
            provider_type: CMS provider type
            site_id: Site ID
            
        Returns:
            Integration or None
        """
        integrations = await self.get_integrations(org_id, provider_type)
        
        for integration in integrations:
            if integration.site_id == site_id and integration.status == IntegrationStatus.active:
                return integration
        
        return None
    
    async def log_usage(
        self,
        org_id: str,
        site_id: Optional[str],
        user_id: Optional[str],
        resource_type: str,
        resource_id: str,
        total_cost: float,
        cost_breakdown: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log usage for cost analytics.
        
        Args:
            org_id: Organization ID
            site_id: Site ID
            user_id: User ID
            resource_type: Resource type (blog_generation, image_generation, etc.)
            resource_id: Resource ID
            total_cost: Total cost
            cost_breakdown: Optional cost breakdown
            metadata: Optional metadata
        """
        if not self.supabase_client:
            self.logger.warning("Supabase client not available, skipping usage log")
            return
        
        try:
            env = self.supabase_client.environment
            table = f"usage_logs_{env}"
            
            log_entry = {
                "org_id": org_id,
                "site_id": site_id,
                "user_id": user_id,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "total_cost": total_cost,
                "cost_breakdown": cost_breakdown or {},
                "metadata": metadata or {},
                "created_at": datetime.utcnow().isoformat()
            }
            
            self.supabase_client.client.table(table).insert(log_entry).execute()
            
        except Exception as e:
            self.logger.error(f"Failed to log usage: {e}", exc_info=True)
    
    async def log_audit(
        self,
        user_id: str,
        org_id: str,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log audit entry.
        
        Args:
            user_id: User ID
            org_id: Organization ID
            action: Action performed
            resource_type: Resource type (integration/blog_post)
            resource_id: Resource ID
            metadata: Additional metadata
        """
        if not self.supabase_client:
            self.logger.warning("Supabase client not available, skipping audit log")
            return
        
        try:
            env = self.supabase_client.environment
            table = f"audit_logs_{env}"
            
            log_entry = {
                "user_id": user_id,
                "org_id": org_id,
                "action": action,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "metadata": metadata or {},
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.supabase_client.client.table(table).insert(log_entry).execute()
            
        except Exception as e:
            self.logger.error(f"Failed to log audit: {e}", exc_info=True)

