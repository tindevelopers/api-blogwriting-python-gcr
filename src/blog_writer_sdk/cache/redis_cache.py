"""
Redis caching layer for the BlogWriter SDK.

Provides intelligent caching for expensive operations like keyword analysis,
SEO scoring, and AI-generated content.
"""

import json
import hashlib
import logging
from typing import Any, Optional, Union, Dict, List
from datetime import timedelta
import asyncio

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

from ..models.blog_models import BlogPost, SEOMetrics, ContentQuality


logger = logging.getLogger(__name__)


class CacheManager:
    """
    Intelligent caching manager with Redis backend.
    
    Features:
    - Automatic serialization/deserialization
    - TTL management
    - Cache invalidation
    - Fallback to in-memory cache if Redis unavailable
    - Smart cache keys based on content hashes
    """
    
    def __init__(
        self,
        redis_url: Optional[str] = None,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        redis_password: Optional[str] = None,
        redis_db: int = 0,
        default_ttl: int = 3600,  # 1 hour
        max_memory_cache_size: int = 1000
    ):
        """
        Initialize cache manager.
        
        Args:
            redis_url: Redis connection URL
            redis_host: Redis host
            redis_port: Redis port
            redis_password: Redis password
            redis_db: Redis database number
            default_ttl: Default TTL in seconds
            max_memory_cache_size: Max items in memory cache fallback
        """
        self.default_ttl = default_ttl
        self.redis_client: Optional[redis.Redis] = None
        self.memory_cache: Dict[str, Any] = {}
        self.max_memory_cache_size = max_memory_cache_size
        
        # TTL configurations for different content types
        self.ttl_config = {
            'keyword_analysis': 86400,      # 24 hours
            'seo_metrics': 3600,            # 1 hour
            'content_quality': 7200,        # 2 hours
            'blog_generation': 1800,        # 30 minutes
            'ai_response': 3600,            # 1 hour
            'dataforseo_result': 86400,     # 24 hours
        }
        
        if REDIS_AVAILABLE:
            try:
                if redis_url:
                    self.redis_client = redis.from_url(redis_url)
                else:
                    self.redis_client = redis.Redis(
                        host=redis_host,
                        port=redis_port,
                        password=redis_password,
                        db=redis_db,
                        decode_responses=True
                    )
                logger.info("✅ Redis cache initialized")
            except Exception as e:
                logger.warning(f"⚠️ Redis connection failed, using memory cache: {e}")
                self.redis_client = None
        else:
            logger.warning("⚠️ Redis not available, using memory cache fallback")
    
    def _generate_cache_key(self, prefix: str, data: Union[str, Dict, List]) -> str:
        """Generate a cache key based on data hash."""
        if isinstance(data, str):
            content = data
        else:
            content = json.dumps(data, sort_keys=True)
        
        content_hash = hashlib.md5(content.encode()).hexdigest()[:12]
        return f"blogwriter:{prefix}:{content_hash}"
    
    def _serialize_data(self, data: Any) -> str:
        """Serialize data for caching."""
        if isinstance(data, (BlogPost, SEOMetrics, ContentQuality)):
            return data.model_dump_json()
        return json.dumps(data, default=str)
    
    def _deserialize_data(self, data: str, data_type: Optional[str] = None) -> Any:
        """Deserialize cached data."""
        try:
            parsed = json.loads(data)
            
            # Try to reconstruct Pydantic models
            if data_type == 'blog_post' and isinstance(parsed, dict):
                return BlogPost.model_validate(parsed)
            elif data_type == 'seo_metrics' and isinstance(parsed, dict):
                return SEOMetrics.model_validate(parsed)
            elif data_type == 'content_quality' and isinstance(parsed, dict):
                return ContentQuality.model_validate(parsed)
            
            return parsed
        except Exception as e:
            logger.warning(f"Failed to deserialize cached data: {e}")
            return None
    
    async def get(
        self,
        key: str,
        data_type: Optional[str] = None
    ) -> Optional[Any]:
        """Get value from cache."""
        try:
            if self.redis_client:
                # Try Redis first
                try:
                    value = await self.redis_client.get(key)
                    if value:
                        return self._deserialize_data(value, data_type)
                except Exception as e:
                    logger.warning(f"Redis get failed: {e}")
            
            # Fall back to memory cache
            if key in self.memory_cache:
                return self.memory_cache[key]
            
            return None
            
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        cache_type: Optional[str] = None
    ) -> bool:
        """Set value in cache."""
        try:
            # Determine TTL
            if ttl is None:
                ttl = self.ttl_config.get(cache_type, self.default_ttl)
            
            serialized_value = self._serialize_data(value)
            
            if self.redis_client:
                # Try Redis first
                try:
                    await self.redis_client.setex(key, ttl, serialized_value)
                    return True
                except Exception as e:
                    logger.warning(f"Redis set failed: {e}")
            
            # Fall back to memory cache
            self.memory_cache[key] = value
            
            # Limit memory cache size
            if len(self.memory_cache) > self.max_memory_cache_size:
                # Remove oldest entries (simple FIFO)
                keys_to_remove = list(self.memory_cache.keys())[:100]
                for old_key in keys_to_remove:
                    del self.memory_cache[old_key]
            
            return True
            
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        try:
            if self.redis_client:
                try:
                    await self.redis_client.delete(key)
                except Exception as e:
                    logger.warning(f"Redis delete failed: {e}")
            
            # Also remove from memory cache
            if key in self.memory_cache:
                del self.memory_cache[key]
            
            return True
            
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern."""
        try:
            count = 0
            
            if self.redis_client:
                try:
                    keys = await self.redis_client.keys(pattern)
                    if keys:
                        count = await self.redis_client.delete(*keys)
                except Exception as e:
                    logger.warning(f"Redis pattern clear failed: {e}")
            
            # Clear from memory cache
            keys_to_remove = [k for k in self.memory_cache.keys() if pattern.replace('*', '') in k]
            for key in keys_to_remove:
                del self.memory_cache[key]
                count += 1
            
            return count
            
        except Exception as e:
            logger.error(f"Cache pattern clear error: {e}")
            return 0
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        stats = {
            "redis_available": self.redis_client is not None,
            "memory_cache_size": len(self.memory_cache),
            "max_memory_cache_size": self.max_memory_cache_size
        }
        
        if self.redis_client:
            try:
                info = await self.redis_client.info()
                stats.update({
                    "redis_used_memory": info.get("used_memory_human", "unknown"),
                    "redis_connected_clients": info.get("connected_clients", 0),
                    "redis_total_commands_processed": info.get("total_commands_processed", 0)
                })
            except Exception as e:
                stats["redis_error"] = str(e)
        
        return stats


# Cache decorators for common operations
def cache_keyword_analysis(cache_manager: CacheManager):
    """Decorator for caching keyword analysis results."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key from keywords
            keywords = kwargs.get('keywords') or (args[1] if len(args) > 1 else None)
            if not keywords:
                return await func(*args, **kwargs)
            
            cache_key = cache_manager._generate_cache_key('keyword_analysis', keywords)
            
            # Try to get from cache
            cached_result = await cache_manager.get(cache_key)
            if cached_result:
                logger.debug(f"Cache hit for keyword analysis: {keywords}")
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache_manager.set(cache_key, result, cache_type='keyword_analysis')
            
            return result
        return wrapper
    return decorator


def cache_seo_analysis(cache_manager: CacheManager):
    """Decorator for caching SEO analysis results."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key from content
            content = kwargs.get('content') or (args[1] if len(args) > 1 else None)
            if not content:
                return await func(*args, **kwargs)
            
            cache_key = cache_manager._generate_cache_key('seo_analysis', content)
            
            # Try to get from cache
            cached_result = await cache_manager.get(cache_key, 'seo_metrics')
            if cached_result:
                logger.debug("Cache hit for SEO analysis")
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache_manager.set(cache_key, result, cache_type='seo_metrics')
            
            return result
        return wrapper
    return decorator


# Global cache manager instance
cache_manager: Optional[CacheManager] = None


def initialize_cache(
    redis_url: Optional[str] = None,
    redis_host: str = "localhost",
    redis_port: int = 6379,
    redis_password: Optional[str] = None,
    **kwargs
) -> CacheManager:
    """Initialize global cache manager."""
    global cache_manager
    cache_manager = CacheManager(
        redis_url=redis_url,
        redis_host=redis_host,
        redis_port=redis_port,
        redis_password=redis_password,
        **kwargs
    )
    return cache_manager


def get_cache_manager() -> Optional[CacheManager]:
    """Get global cache manager instance."""
    return cache_manager
