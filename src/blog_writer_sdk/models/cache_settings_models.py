"""
Models for organization-level cache sharing settings.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class OrganizationCacheSettings(BaseModel):
    """Organization cache sharing settings."""

    org_id: str = Field(..., description="Organization/tenant ID")
    shared_cache_enabled: bool = Field(
        default=False,
        description="Enable shared cache across orgs for approved categories"
    )
    shared_cache_categories: List[str] = Field(
        default_factory=list,
        description="Allowlist of categories eligible for shared caching"
    )
    updated_at: Optional[str] = Field(default=None, description="ISO timestamp of last update")
    updated_by: Optional[str] = Field(default=None, description="User/admin identifier")


class OrganizationCacheSettingsUpdate(BaseModel):
    """Update payload for organization cache settings."""

    shared_cache_enabled: Optional[bool] = None
    shared_cache_categories: Optional[List[str]] = None
