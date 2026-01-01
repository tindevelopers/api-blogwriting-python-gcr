"""
Models for multi-CMS publishing system with target selection and role-based cost visibility.
"""
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, validator
from uuid import UUID


class CMSProvider(str, Enum):
    """CMS provider types."""
    webflow = "webflow"
    shopify = "shopify"
    wordpress = "wordpress"
    medium = "medium"
    custom = "custom"


class IntegrationStatus(str, Enum):
    """Integration status."""
    active = "active"
    inactive = "inactive"
    error = "error"


class PublishingTargetStatus(str, Enum):
    """Publishing target lifecycle state."""
    active = "active"
    inactive = "inactive"
    archived = "archived"


class UserRole(str, Enum):
    """User roles for access control."""
    owner = "owner"
    admin = "admin"
    editor = "editor"
    writer = "writer"
    system_admin = "system_admin"
    super_admin = "super_admin"


# Integration Models
class CMSIntegration(BaseModel):
    """CMS integration model."""
    id: Optional[str] = Field(None, description="Integration ID")
    org_id: str = Field(..., description="Organization ID")
    type: CMSProvider = Field(..., description="CMS provider type")
    site_id: str = Field(..., description="Site ID from CMS provider")
    site_name: str = Field(..., description="Human-readable site name")
    api_key: Optional[str] = Field(None, description="API key (encrypted)")
    api_secret: Optional[str] = Field(None, description="API secret (encrypted)")
    collection_ids: List[str] = Field(default_factory=list, description="Collection IDs (JSON array)")
    is_default: bool = Field(default=False, description="Is default integration for this provider")
    status: IntegrationStatus = Field(default=IntegrationStatus.active, description="Integration status")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    last_verified_at: Optional[datetime] = Field(None, description="Last verification timestamp")
    error_message: Optional[str] = Field(None, description="Error message if status is error")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "int_123",
                "org_id": "org_456",
                "type": "webflow",
                "site_id": "wf_site_1",
                "site_name": "Marketing Site",
                "collection_ids": ["blog", "news"],
                "is_default": True,
                "status": "active"
            }
        }


class CreateIntegrationRequest(BaseModel):
    """Request to create a new integration."""
    org_id: str = Field(..., description="Organization ID")
    type: CMSProvider = Field(..., description="CMS provider type")
    site_id: str = Field(..., description="Site ID from CMS provider")
    site_name: str = Field(..., description="Human-readable site name")
    api_key: str = Field(..., description="API key")
    api_secret: Optional[str] = Field(None, description="API secret (if required)")
    collection_ids: List[str] = Field(default_factory=list, description="Collection IDs")
    is_default: bool = Field(default=False, description="Set as default for this provider")


class UpdateIntegrationRequest(BaseModel):
    """Request to update an integration."""
    site_name: Optional[str] = Field(None, description="Update site name")
    api_key: Optional[str] = Field(None, description="Update API key")
    api_secret: Optional[str] = Field(None, description="Update API secret")
    collection_ids: Optional[List[str]] = Field(None, description="Update collection IDs")
    is_default: Optional[bool] = Field(None, description="Set as default")
    status: Optional[IntegrationStatus] = Field(None, description="Update status")


# Publishing Target Models
class PublishingTarget(BaseModel):
    """Publishing target selection."""
    cms_provider: CMSProvider = Field(..., description="CMS provider")
    site_id: str = Field(..., description="Site ID")
    collection_id: Optional[str] = Field(None, description="Collection ID (required for Webflow)")
    site_name: Optional[str] = Field(None, description="Site name (for display)")


class PublishingTargetRecord(BaseModel):
    """Stored publishing target for an organization."""
    id: Optional[str] = Field(None, description="Publishing target ID")
    org_id: str = Field(..., description="Organization ID")
    name: str = Field(..., description="Friendly target name")
    type: CMSProvider = Field(..., description="CMS provider type")
    site_url: Optional[str] = Field(None, description="Base URL of the property/site")
    status: PublishingTargetStatus = Field(default=PublishingTargetStatus.active, description="Target status")
    is_default: bool = Field(default=False, description="Default target for org/type")
    config: Dict[str, Any] = Field(default_factory=dict, description="Provider-specific config (collections, IDs, etc.)")
    credentials: Dict[str, Any] = Field(default_factory=dict, description="Provider credentials (stored securely)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    deleted_at: Optional[datetime] = Field(None, description="Soft-delete timestamp")


class CreatePublishingTargetRequest(BaseModel):
    """Request payload for creating a publishing target."""
    org_id: str = Field(..., description="Organization ID")
    name: str = Field(..., description="Friendly target name")
    type: CMSProvider = Field(..., description="CMS provider type")
    site_url: Optional[str] = Field(None, description="Base URL of the property/site")
    is_default: bool = Field(default=False, description="Set as default for provider")
    status: PublishingTargetStatus = Field(default=PublishingTargetStatus.active, description="Initial status")
    config: Dict[str, Any] = Field(default_factory=dict, description="Provider-specific config")
    credentials: Dict[str, Any] = Field(default_factory=dict, description="Provider credentials")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class UpdatePublishingTargetRequest(BaseModel):
    """Request payload for updating a publishing target."""
    name: Optional[str] = Field(None, description="Friendly target name")
    site_url: Optional[str] = Field(None, description="Base URL of the property/site")
    is_default: Optional[bool] = Field(None, description="Set as default for provider")
    status: Optional[PublishingTargetStatus] = Field(None, description="Update status")
    config: Optional[Dict[str, Any]] = Field(None, description="Provider-specific config")
    credentials: Optional[Dict[str, Any]] = Field(None, description="Provider credentials")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class PublishingSite(BaseModel):
    """Site information for publishing targets."""
    id: str = Field(..., description="Site ID")
    name: str = Field(..., description="Site name")
    provider: CMSProvider = Field(..., description="CMS provider")
    collections: List[str] = Field(default_factory=list, description="Available collections")
    is_default: bool = Field(default=False, description="Is default site for this provider")


class PublishingTargetsResponse(BaseModel):
    """Response with available publishing targets."""
    providers: List[str] = Field(..., description="Available CMS providers")
    sites: List[PublishingSite] = Field(..., description="Available sites")
    default: Optional[PublishingTarget] = Field(None, description="Default publishing target")


# Blog Post Publishing Metadata
class PublishingMetadata(BaseModel):
    """Publishing metadata stored with blog posts."""
    cms_provider: Optional[CMSProvider] = Field(None, description="CMS provider")
    site_id: Optional[str] = Field(None, description="Site ID")
    collection_id: Optional[str] = Field(None, description="Collection ID")
    publishing_target: Optional[PublishingTarget] = Field(None, description="Full publishing target")
    published_url: Optional[str] = Field(None, description="Published URL")
    remote_id: Optional[str] = Field(None, description="Remote post/item ID")
    published_at: Optional[datetime] = Field(None, description="Publication timestamp")
    publish_status: Optional[str] = Field(None, description="Publish status (success/failed)")
    publish_error: Optional[str] = Field(None, description="Error message if publish failed")


# Cost Tracking Models
class CostBreakdown(BaseModel):
    """Cost breakdown for blog generation."""
    ai_generation: float = Field(default=0.0, description="AI generation cost")
    api_calls: float = Field(default=0.0, description="API calls cost")
    dataforseo: float = Field(default=0.0, description="DataForSEO cost")
    image_generation: float = Field(default=0.0, description="Image generation cost")
    other: float = Field(default=0.0, description="Other costs")


class BlogCostMetadata(BaseModel):
    """Cost metadata for blog posts."""
    total_cost: float = Field(default=0.0, description="Total cost")
    cost_breakdown: Optional[CostBreakdown] = Field(None, description="Cost breakdown")
    org_id: str = Field(..., description="Organization ID")
    site_id: Optional[str] = Field(None, description="Site ID (for analytics)")


# Publish Request Models
class PublishBlogRequest(BaseModel):
    """Request to publish a blog post."""
    blog_id: str = Field(..., description="Blog post ID")
    cms_provider: Optional[CMSProvider] = Field(None, description="Override CMS provider")
    site_id: Optional[str] = Field(None, description="Override site ID")
    collection_id: Optional[str] = Field(None, description="Override collection ID")
    publish: bool = Field(default=True, description="Publish immediately")


class PublishBlogResponse(BaseModel):
    """Response from publishing a blog post."""
    success: bool = Field(..., description="Whether publish was successful")
    cms_provider: CMSProvider = Field(..., description="CMS provider used")
    site_id: str = Field(..., description="Site ID")
    collection_id: Optional[str] = Field(None, description="Collection ID")
    published_url: Optional[str] = Field(None, description="Published URL")
    remote_id: Optional[str] = Field(None, description="Remote post/item ID")
    error_message: Optional[str] = Field(None, description="Error message if failed")


# Audit Log Models
class AuditLogEntry(BaseModel):
    """Audit log entry."""
    id: Optional[str] = Field(None, description="Log entry ID")
    user_id: str = Field(..., description="User ID")
    org_id: str = Field(..., description="Organization ID")
    action: str = Field(..., description="Action performed")
    resource_type: str = Field(..., description="Resource type (integration/blog_post)")
    resource_id: Optional[str] = Field(None, description="Resource ID")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp")


# Response Models with Role-Based Cost Visibility
class BlogPostWithCosts(BaseModel):
    """Blog post with costs (only visible to admins/owners)."""
    id: str
    title: str
    content: str
    status: str
    total_cost: Optional[float] = Field(None, description="Total cost (only for admins/owners)")
    cost_breakdown: Optional[CostBreakdown] = Field(None, description="Cost breakdown (only for admins/owners)")
    publishing_metadata: Optional[PublishingMetadata] = None
    
    @classmethod
    def from_blog_post(
        cls,
        blog_post: Dict[str, Any],
        user_role: Optional[UserRole] = None,
        include_costs: bool = False
    ):
        """Create from blog post dict with role-based cost visibility."""
        # Only include costs if user is admin/owner or explicitly requested
        can_view_costs = include_costs or (
            user_role in [UserRole.admin, UserRole.owner, UserRole.system_admin, UserRole.super_admin]
        )
        
        return cls(
            id=blog_post.get("id", ""),
            title=blog_post.get("title", ""),
            content=blog_post.get("content", ""),
            status=blog_post.get("status", "draft"),
            total_cost=blog_post.get("total_cost") if can_view_costs else None,
            cost_breakdown=blog_post.get("cost_breakdown") if can_view_costs else None,
            publishing_metadata=blog_post.get("publishing_metadata")
        )

