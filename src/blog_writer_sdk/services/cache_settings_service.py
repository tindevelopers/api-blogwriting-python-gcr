"""
Service for organization cache sharing settings.
"""

from __future__ import annotations

import logging
import time
from typing import Optional, Dict, Any

from ..integrations.firebase_config_client import get_firebase_config_client
from ..models.cache_settings_models import OrganizationCacheSettings

logger = logging.getLogger(__name__)


class CacheSettingsService:
    """Fetch and update org-level cache sharing settings."""

    def __init__(
        self,
        cache_ttl_seconds: int = 300,
        default_shared_enabled: bool = False,
        default_shared_categories: Optional[list[str]] = None,
    ):
        self.cache_ttl_seconds = cache_ttl_seconds
        self.default_shared_enabled = default_shared_enabled
        self.default_shared_categories = default_shared_categories or []
        self._cache: Dict[str, tuple[OrganizationCacheSettings, float]] = {}

    def _default_settings(self, org_id: str) -> OrganizationCacheSettings:
        return OrganizationCacheSettings(
            org_id=org_id,
            shared_cache_enabled=self.default_shared_enabled,
            shared_cache_categories=self.default_shared_categories,
        )

    def get_org_cache_settings(self, org_id: str) -> OrganizationCacheSettings:
        """Fetch settings (cached in-process for a short TTL)."""
        now = time.time()
        cached = self._cache.get(org_id)
        if cached:
            settings, ts = cached
            if now - ts < self.cache_ttl_seconds:
                return settings

        try:
            client = get_firebase_config_client()
            data = client.get_org_cache_settings(org_id)
            if not data:
                settings = self._default_settings(org_id)
            else:
                settings = OrganizationCacheSettings(
                    org_id=data.get("org_id") or org_id,
                    shared_cache_enabled=bool(data.get("shared_cache_enabled", False)),
                    shared_cache_categories=list(data.get("shared_cache_categories") or []),
                    updated_at=data.get("updated_at"),
                    updated_by=data.get("updated_by"),
                )
        except Exception as exc:
            logger.warning(f"Cache settings fetch failed for org {org_id}: {exc}")
            settings = self._default_settings(org_id)

        self._cache[org_id] = (settings, now)
        return settings

    def save_org_cache_settings(
        self,
        org_id: str,
        settings: Dict[str, Any],
        updated_by: str = "system",
        config_id: str = "default",
    ) -> bool:
        """Persist settings to Firestore and update local cache."""
        try:
            client = get_firebase_config_client()
            ok = client.save_org_cache_settings(
                org_id=org_id,
                settings=settings,
                config_id=config_id,
                updated_by=updated_by,
            )
            if ok:
                updated = self.get_org_cache_settings(org_id)
                self._cache[org_id] = (updated, time.time())
            return ok
        except Exception as exc:
            logger.error(f"Cache settings save failed for org {org_id}: {exc}")
            return False
