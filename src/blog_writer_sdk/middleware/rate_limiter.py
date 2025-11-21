"""
Rate limiting middleware for the BlogWriter SDK API.

Provides configurable rate limiting to prevent abuse and ensure fair usage.
"""

import time
import asyncio
from typing import Dict, Optional, Tuple
from collections import defaultdict, deque
from datetime import datetime, timedelta
from enum import Enum
import logging

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse


logger = logging.getLogger(__name__)


class RateLimitTier(str, Enum):
    """Rate limit tiers."""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class RateLimiter:
    """
    Token bucket rate limiter with sliding window.
    
    Features:
    - Per-IP rate limiting
    - Per-user rate limiting (if authenticated)
    - Different limits for different endpoints
    - Tiered rate limiting (Free/Pro/Enterprise)
    - Configurable time windows
    - Automatic cleanup of old entries
    """
    
    # Tier-based rate limits
    TIER_LIMITS = {
        RateLimitTier.FREE: {
            'minute': 10,
            'hour': 100,
            'day': 1000,
            'keywords_per_batch': 20,
            'max_suggestions': 50
        },
        RateLimitTier.PRO: {
            'minute': 100,
            'hour': 1000,
            'day': 10000,
            'keywords_per_batch': 30,
            'max_suggestions': 150
        },
        RateLimitTier.ENTERPRISE: {
            'minute': -1,  # Unlimited
            'hour': -1,
            'day': -1,
            'keywords_per_batch': 50,
            'max_suggestions': 200
        }
    }
    
    def __init__(
        self,
        default_requests_per_minute: int = 60,
        default_requests_per_hour: int = 1000,
        default_requests_per_day: int = 10000,
        cleanup_interval: int = 300,  # 5 minutes
        default_tier: RateLimitTier = RateLimitTier.FREE
    ):
        """
        Initialize rate limiter.
        
        Args:
            default_requests_per_minute: Default requests per minute limit
            default_requests_per_hour: Default requests per hour limit  
            default_requests_per_day: Default requests per day limit
            cleanup_interval: Cleanup interval in seconds
        """
        self.default_limits = {
            'minute': default_requests_per_minute,
            'hour': default_requests_per_hour,
            'day': default_requests_per_day
        }
        
        self.default_tier = default_tier
        
        # Storage for request counts
        self.requests: Dict[str, Dict[str, deque]] = defaultdict(
            lambda: {
                'minute': deque(),
                'hour': deque(),
                'day': deque()
            }
        )
        
        # Tier mapping (client_id -> tier)
        self.client_tiers: Dict[str, RateLimitTier] = defaultdict(lambda: default_tier)
        
        # Custom limits for specific endpoints
        self.endpoint_limits = {
            '/api/v1/blog/generate': {
                'minute': 50,   # Increased from 10
                'hour': 500,    # Increased from 100
                'day': 2000     # Increased from 500
            },
            '/api/v1/keywords/analyze': {
                'minute': 30,
                'hour': 300,
                'day': 2000
            }
        }
        
        self.cleanup_interval = cleanup_interval
        self.last_cleanup = time.time()
    
    def set_client_tier(self, client_id: str, tier: RateLimitTier):
        """Set rate limit tier for a client."""
        self.client_tiers[client_id] = tier
    
    def get_client_tier(self, client_id: str) -> RateLimitTier:
        """Get rate limit tier for a client."""
        return self.client_tiers.get(client_id, self.default_tier)
    
    def _get_tier_limits(self, tier: RateLimitTier) -> Dict[str, int]:
        """Get rate limits for a tier."""
        return self.TIER_LIMITS.get(tier, self.TIER_LIMITS[RateLimitTier.FREE])
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier (IP or user ID)."""
        # Try to get user ID from headers (if authenticated)
        user_id = request.headers.get('X-User-ID')
        if user_id:
            return f"user:{user_id}"
        
        # Fall back to IP address
        client_ip = request.client.host
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            client_ip = forwarded_for.split(',')[0].strip()
        
        return f"ip:{client_ip}"
    
    def _get_limits_for_endpoint(self, endpoint: str, client_id: str = None) -> Dict[str, int]:
        """
        Get rate limits for specific endpoint, considering client tier.
        
        Args:
            endpoint: API endpoint path
            client_id: Client identifier (for tier-based limits)
        
        Returns:
            Rate limits dictionary
        """
        # Check if endpoint has custom limits
        if endpoint in self.endpoint_limits:
            base_limits = self.endpoint_limits[endpoint]
        else:
            base_limits = self.default_limits
        
        # Apply tier-based limits if client_id provided
        if client_id:
            tier = self.get_client_tier(client_id)
            tier_limits = self._get_tier_limits(tier)
            
            # Use tier limits if they're more restrictive (or unlimited)
            limits = {}
            for window in ['minute', 'hour', 'day']:
                tier_limit = tier_limits.get(window, base_limits[window])
                base_limit = base_limits.get(window, self.default_limits[window])
                
                if tier_limit == -1:  # Unlimited
                    limits[window] = -1
                elif base_limit == -1:
                    limits[window] = tier_limit
                else:
                    limits[window] = min(tier_limit, base_limit) if tier_limit > 0 else base_limit
            
            return limits
        
        return base_limits
    
    def _cleanup_old_requests(self):
        """Clean up old request records."""
        if time.time() - self.last_cleanup < self.cleanup_interval:
            return
        
        now = time.time()
        cutoffs = {
            'minute': now - 60,
            'hour': now - 3600,
            'day': now - 86400
        }
        
        for client_id in list(self.requests.keys()):
            client_requests = self.requests[client_id]
            
            for window, cutoff in cutoffs.items():
                # Remove old requests
                while client_requests[window] and client_requests[window][0] < cutoff:
                    client_requests[window].popleft()
            
            # Remove empty client records
            if all(not client_requests[window] for window in client_requests):
                del self.requests[client_id]
        
        self.last_cleanup = now
    
    def _is_rate_limited(self, client_id: str, endpoint: str) -> Tuple[bool, Dict[str, int]]:
        """
        Check if client is rate limited.
        
        Returns:
            Tuple of (is_limited, remaining_requests)
        """
        self._cleanup_old_requests()
        
        now = time.time()
        limits = self._get_limits_for_endpoint(endpoint, client_id)
        client_requests = self.requests[client_id]
        
        remaining = {}
        
        for window, limit in limits.items():
            # Skip unlimited limits
            if limit == -1:
                remaining[window] = -1
                continue
            
            # Count requests in current window
            if window == 'minute':
                cutoff = now - 60
            elif window == 'hour':
                cutoff = now - 3600
            else:  # day
                cutoff = now - 86400
            
            # Remove old requests
            while client_requests[window] and client_requests[window][0] < cutoff:
                client_requests[window].popleft()
            
            current_count = len(client_requests[window])
            remaining[window] = max(0, limit - current_count) if limit > 0 else -1
            
            if limit > 0 and current_count >= limit:
                return True, remaining
        
        return False, remaining
    
    def _record_request(self, client_id: str):
        """Record a new request."""
        now = time.time()
        client_requests = self.requests[client_id]
        
        for window in client_requests:
            client_requests[window].append(now)
    
    async def check_rate_limit(self, request: Request) -> Optional[JSONResponse]:
        """
        Check rate limit for request.
        
        Returns:
            JSONResponse if rate limited, None otherwise
        """
        try:
            client_id = self._get_client_id(request)
            endpoint = request.url.path
            
            is_limited, remaining = self._is_rate_limited(client_id, endpoint)
            
            if is_limited:
                # Find the most restrictive window
                reset_times = {}
                now = time.time()
                
                for window in remaining:
                    if window == 'minute':
                        reset_times[window] = int(now + 60)
                    elif window == 'hour':
                        reset_times[window] = int(now + 3600)
                    else:  # day
                        reset_times[window] = int(now + 86400)
                
                # Return rate limit error
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Rate limit exceeded",
                        "message": "Too many requests. Please try again later.",
                        "remaining": remaining,
                        "reset_times": reset_times,
                        "client_id": client_id.split(':')[0]  # Don't expose full client_id
                    },
                    headers={
                        "X-RateLimit-Remaining-Minute": str(remaining.get('minute', 0)),
                        "X-RateLimit-Remaining-Hour": str(remaining.get('hour', 0)),
                        "X-RateLimit-Remaining-Day": str(remaining.get('day', 0)),
                        "Retry-After": str(min(reset_times.values()) - int(now))
                    }
                )
            
            # Record the request
            self._record_request(client_id)
            
            # Add rate limit headers to response (will be added by middleware)
            request.state.rate_limit_remaining = remaining
            
            return None
            
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # Don't block requests if rate limiter fails
            return None


# Global rate limiter instance with higher limits for development
rate_limiter = RateLimiter(
    default_requests_per_minute=300,  # Increased from 60
    default_requests_per_hour=5000,   # Increased from 1000
    default_requests_per_day=50000    # Increased from 10000
)


async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware."""
    # Skip rate limiting for health checks during development
    if request.url.path in ['/health', '/docs', '/redoc', '/openapi.json']:
        response = await call_next(request)
        return response
    
    # Check rate limit for other endpoints
    rate_limit_response = await rate_limiter.check_rate_limit(request)
    if rate_limit_response:
        return rate_limit_response
    
    # Process request
    response = await call_next(request)
    
    # Add rate limit headers if available
    if hasattr(request.state, 'rate_limit_remaining'):
        remaining = request.state.rate_limit_remaining
        response.headers["X-RateLimit-Remaining-Minute"] = str(remaining.get('minute', 0))
        response.headers["X-RateLimit-Remaining-Hour"] = str(remaining.get('hour', 0))
        response.headers["X-RateLimit-Remaining-Day"] = str(remaining.get('day', 0))
    
    return response
