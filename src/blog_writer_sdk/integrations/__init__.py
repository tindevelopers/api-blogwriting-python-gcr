"""
Integration modules for the Blog Writer SDK.

This package contains integrations with external services
like databases and third-party APIs.
"""

from .supabase_client import SupabaseClient

__all__ = [
    "SupabaseClient",
]
