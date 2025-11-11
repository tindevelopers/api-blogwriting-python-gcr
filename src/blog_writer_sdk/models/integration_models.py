from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ContentSystemProvider(str, Enum):
    webflow = "webflow"
    wordpress = "wordpress"
    shopify = "shopify"
    medium = "medium"
    custom = "custom"


class IntegrationConnectAndRecommendRequest(BaseModel):
    tenant_id: Optional[str] = Field(None, description="Tenant or account identifier")
    provider: ContentSystemProvider = Field(..., description="Content system provider")
    connection: Dict[str, Any] = Field(
        default_factory=dict,
        description="Provider-specific connection/config payload (tokens, site IDs, etc.)"
    )
    keywords: List[str] = Field(..., min_items=1, max_items=50, description="Selected target keywords")


class KeywordRecommendation(BaseModel):
    keyword: str
    difficulty: Optional[float] = None
    suggested_backlinks: int
    suggested_interlinks: int


class IntegrationRecommendationResponse(BaseModel):
    provider: ContentSystemProvider
    tenant_id: Optional[str] = None
    saved_integration: bool = False
    recommended_backlinks: int
    recommended_interlinks: int
    per_keyword: List[KeywordRecommendation] = Field(default_factory=list)
    notes: Optional[str] = None


