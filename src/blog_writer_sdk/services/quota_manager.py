"""
Quota Management Service

Manages per-organization quota tracking and limits.
"""

import logging
from typing import Dict, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class QuotaType(str, Enum):
    """Types of quota limits."""
    MONTHLY = "monthly"
    DAILY = "daily"
    HOURLY = "hourly"


@dataclass
class QuotaUsage:
    """Quota usage information."""
    quota_type: QuotaType
    limit: int
    used: int
    remaining: int
    reset_date: datetime
    breakdown: Dict[str, int] = field(default_factory=dict)  # e.g., {"keyword_analysis": 100, "content_generation": 50}


@dataclass
class QuotaInfo:
    """Complete quota information for an organization."""
    organization_id: str
    monthly_limit: int
    monthly_used: int
    monthly_remaining: int
    monthly_reset_date: datetime
    daily_limit: Optional[int] = None
    daily_used: int = 0
    daily_remaining: int = 0
    daily_reset_date: Optional[datetime] = None
    hourly_limit: Optional[int] = None
    hourly_used: int = 0
    hourly_remaining: int = 0
    hourly_reset_date: Optional[datetime] = None
    breakdown: Dict[str, int] = field(default_factory=dict)
    warnings: List[Dict[str, str]] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "organization_id": self.organization_id,
            "monthly_limit": self.monthly_limit,
            "monthly_used": self.monthly_used,
            "monthly_remaining": self.monthly_remaining,
            "monthly_reset_date": self.monthly_reset_date.isoformat(),
            "daily_limit": self.daily_limit,
            "daily_used": self.daily_used,
            "daily_remaining": self.daily_remaining,
            "daily_reset_date": self.daily_reset_date.isoformat() if self.daily_reset_date else None,
            "hourly_limit": self.hourly_limit,
            "hourly_used": self.hourly_used,
            "hourly_remaining": self.hourly_remaining,
            "hourly_reset_date": self.hourly_reset_date.isoformat() if self.hourly_reset_date else None,
            "breakdown": self.breakdown,
            "warnings": self.warnings
        }


class QuotaManager:
    """
    Manages quota tracking and limits for organizations.
    
    Features:
    - Per-organization quota tracking
    - Monthly, daily, and hourly limits
    - Usage breakdown by operation type
    - Automatic reset scheduling
    - Warning thresholds
    """
    
    def __init__(self, storage_backend=None):
        """
        Initialize quota manager.
        
        Args:
            storage_backend: Storage backend (database, Redis, etc.)
                If None, uses in-memory storage (for development)
        """
        self.storage = storage_backend
        self.in_memory_storage: Dict[str, QuotaInfo] = {}
        
        # Default quota limits (can be overridden per organization)
        self.default_limits = {
            "monthly": 10000,
            "daily": 1000,
            "hourly": 100
        }
    
    async def get_quota_info(self, organization_id: str) -> Optional[QuotaInfo]:
        """
        Get quota information for an organization.
        
        Args:
            organization_id: Organization identifier
            
        Returns:
            QuotaInfo or None if not found
        """
        if self.storage:
            # Use storage backend (database, Redis, etc.)
            return await self._get_from_storage(organization_id)
        else:
            # Use in-memory storage
            if organization_id not in self.in_memory_storage:
                # Initialize with default limits
                now = datetime.utcnow()
                next_month = (now.replace(day=1) + timedelta(days=32)).replace(day=1)
                
                quota_info = QuotaInfo(
                    organization_id=organization_id,
                    monthly_limit=self.default_limits["monthly"],
                    monthly_used=0,
                    monthly_remaining=self.default_limits["monthly"],
                    monthly_reset_date=next_month,
                    daily_limit=self.default_limits["daily"],
                    daily_used=0,
                    daily_remaining=self.default_limits["daily"],
                    daily_reset_date=(now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0),
                    hourly_limit=self.default_limits["hourly"],
                    hourly_used=0,
                    hourly_remaining=self.default_limits["hourly"],
                    hourly_reset_date=(now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
                )
                self.in_memory_storage[organization_id] = quota_info
            
            quota_info = self.in_memory_storage[organization_id]
            
            # Check if resets are needed
            await self._check_and_reset(quota_info)
            
            # Generate warnings
            quota_info.warnings = self._generate_warnings(quota_info)
            
            return quota_info
    
    async def check_quota(
        self,
        organization_id: str,
        operation_type: str = "general",
        amount: int = 1
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if operation is within quota limits.
        
        Args:
            organization_id: Organization identifier
            operation_type: Type of operation (e.g., "keyword_analysis", "content_generation")
            amount: Amount to consume
            
        Returns:
            Tuple of (is_allowed, error_message)
        """
        quota_info = await self.get_quota_info(organization_id)
        
        if not quota_info:
            return False, "Organization not found"
        
        # Check monthly limit
        if quota_info.monthly_used + amount > quota_info.monthly_limit:
            return False, f"Monthly quota exceeded ({quota_info.monthly_used}/{quota_info.monthly_limit})"
        
        # Check daily limit
        if quota_info.daily_limit and quota_info.daily_used + amount > quota_info.daily_limit:
            return False, f"Daily quota exceeded ({quota_info.daily_used}/{quota_info.daily_limit})"
        
        # Check hourly limit
        if quota_info.hourly_limit and quota_info.hourly_used + amount > quota_info.hourly_limit:
            return False, f"Hourly quota exceeded ({quota_info.hourly_used}/{quota_info.hourly_limit})"
        
        return True, None
    
    async def consume_quota(
        self,
        organization_id: str,
        operation_type: str = "general",
        amount: int = 1
    ) -> bool:
        """
        Consume quota for an operation.
        
        Args:
            organization_id: Organization identifier
            operation_type: Type of operation
            amount: Amount to consume
            
        Returns:
            True if successful, False if quota exceeded
        """
        is_allowed, error = await self.check_quota(organization_id, operation_type, amount)
        
        if not is_allowed:
            logger.warning(f"Quota exceeded for {organization_id}: {error}")
            return False
        
        quota_info = await self.get_quota_info(organization_id)
        
        if not quota_info:
            return False
        
        # Update usage
        quota_info.monthly_used += amount
        quota_info.monthly_remaining = quota_info.monthly_limit - quota_info.monthly_used
        
        if quota_info.daily_limit:
            quota_info.daily_used += amount
            quota_info.daily_remaining = quota_info.daily_limit - quota_info.daily_used
        
        if quota_info.hourly_limit:
            quota_info.hourly_used += amount
            quota_info.hourly_remaining = quota_info.hourly_limit - quota_info.hourly_used
        
        # Update breakdown
        quota_info.breakdown[operation_type] = quota_info.breakdown.get(operation_type, 0) + amount
        
        # Save back to storage
        if self.storage:
            await self._save_to_storage(quota_info)
        
        return True
    
    async def _check_and_reset(self, quota_info: QuotaInfo):
        """Check if quota resets are needed and reset if necessary."""
        now = datetime.utcnow()
        
        # Check monthly reset
        if now >= quota_info.monthly_reset_date:
            quota_info.monthly_used = 0
            quota_info.monthly_remaining = quota_info.monthly_limit
            quota_info.monthly_reset_date = (now.replace(day=1) + timedelta(days=32)).replace(day=1)
            quota_info.breakdown = {}  # Reset breakdown
        
        # Check daily reset
        if quota_info.daily_reset_date and now >= quota_info.daily_reset_date:
            quota_info.daily_used = 0
            quota_info.daily_remaining = quota_info.daily_limit or 0
            quota_info.daily_reset_date = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Check hourly reset
        if quota_info.hourly_reset_date and now >= quota_info.hourly_reset_date:
            quota_info.hourly_used = 0
            quota_info.hourly_remaining = quota_info.hourly_limit or 0
            quota_info.hourly_reset_date = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    
    def _generate_warnings(self, quota_info: QuotaInfo) -> List[Dict[str, str]]:
        """Generate quota warnings."""
        warnings = []
        
        # Monthly warnings
        monthly_usage_pct = (quota_info.monthly_used / quota_info.monthly_limit * 100) if quota_info.monthly_limit > 0 else 0
        if monthly_usage_pct >= 90:
            warnings.append({
                "threshold": "90%",
                "message": f"90% of monthly quota used ({quota_info.monthly_used}/{quota_info.monthly_limit})"
            })
        elif monthly_usage_pct >= 80:
            warnings.append({
                "threshold": "80%",
                "message": f"80% of monthly quota used ({quota_info.monthly_used}/{quota_info.monthly_limit})"
            })
        
        # Daily warnings
        if quota_info.daily_limit:
            daily_usage_pct = (quota_info.daily_used / quota_info.daily_limit * 100) if quota_info.daily_limit > 0 else 0
            if daily_usage_pct >= 90:
                warnings.append({
                    "threshold": "90%",
                    "message": f"90% of daily quota used ({quota_info.daily_used}/{quota_info.daily_limit})"
                })
        
        return warnings
    
    async def _get_from_storage(self, organization_id: str) -> Optional[QuotaInfo]:
        """Get quota info from storage backend."""
        # Placeholder for database/Redis implementation
        # Would query database or Redis here
        return None
    
    async def _save_to_storage(self, quota_info: QuotaInfo):
        """Save quota info to storage backend."""
        # Placeholder for database/Redis implementation
        # Would save to database or Redis here
        pass
    
    async def set_quota_limits(
        self,
        organization_id: str,
        monthly_limit: Optional[int] = None,
        daily_limit: Optional[int] = None,
        hourly_limit: Optional[int] = None
    ):
        """
        Set custom quota limits for an organization.
        
        Args:
            organization_id: Organization identifier
            monthly_limit: Monthly limit (None to use default)
            daily_limit: Daily limit (None to use default)
            hourly_limit: Hourly limit (None to use default)
        """
        quota_info = await self.get_quota_info(organization_id)
        
        if not quota_info:
            # Create new quota info
            now = datetime.utcnow()
            quota_info = QuotaInfo(
                organization_id=organization_id,
                monthly_limit=monthly_limit or self.default_limits["monthly"],
                monthly_used=0,
                monthly_remaining=monthly_limit or self.default_limits["monthly"],
                monthly_reset_date=(now.replace(day=1) + timedelta(days=32)).replace(day=1),
                daily_limit=daily_limit or self.default_limits["daily"],
                daily_used=0,
                daily_remaining=daily_limit or self.default_limits["daily"],
                daily_reset_date=(now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0),
                hourly_limit=hourly_limit or self.default_limits["hourly"],
                hourly_used=0,
                hourly_remaining=hourly_limit or self.default_limits["hourly"],
                hourly_reset_date=(now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
            )
        else:
            # Update existing limits
            if monthly_limit is not None:
                quota_info.monthly_limit = monthly_limit
                quota_info.monthly_remaining = monthly_limit - quota_info.monthly_used
            
            if daily_limit is not None:
                quota_info.daily_limit = daily_limit
                quota_info.daily_remaining = daily_limit - quota_info.daily_used
            
            if hourly_limit is not None:
                quota_info.hourly_limit = hourly_limit
                quota_info.hourly_remaining = hourly_limit - quota_info.hourly_used
        
        # Save to storage
        if self.storage:
            await self._save_to_storage(quota_info)
        else:
            self.in_memory_storage[organization_id] = quota_info

