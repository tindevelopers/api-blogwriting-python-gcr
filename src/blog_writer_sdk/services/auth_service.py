"""
Authentication Service for JWT Token Verification

This module provides JWT token verification using Supabase Auth.
"""

import os
import logging
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

try:
    from supabase import create_client, Client
    from supabase.lib.client_options import ClientOptions
except ImportError:
    create_client = None
    Client = None

logger = logging.getLogger(__name__)
security = HTTPBearer()


class AuthService:
    """Service for handling authentication with Supabase."""
    
    def __init__(self, supabase_url: Optional[str] = None, supabase_key: Optional[str] = None):
        """
        Initialize authentication service.
        
        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase anon key (for token verification)
        """
        self.supabase_url = supabase_url or os.getenv("SUPABASE_URL")
        self.supabase_key = supabase_key or os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            logger.warning("Supabase credentials not configured. Authentication will use placeholder.")
            self.supabase_client = None
        else:
            try:
                # Use anon key for token verification
                self.supabase_client = create_client(
                    self.supabase_url,
                    self.supabase_key,
                    options=ClientOptions(auto_refresh_token=False)
                )
                logger.info("Auth service initialized with Supabase")
            except Exception as e:
                logger.error(f"Failed to initialize Supabase client: {e}")
                self.supabase_client = None
    
    def _get_role(self, role_id: str) -> Optional[Dict[str, Any]]:
        """Get role by ID (synchronous helper)."""
        if not self.supabase_client:
            return None
        
        try:
            service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            if not service_key:
                return None
            
            service_client = create_client(self.supabase_url, service_key)
            response = service_client.table("roles").select("*").eq("id", role_id).execute()
            
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Failed to get role: {e}")
            return None
    
    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify JWT token and return user information.
        
        Args:
            token: JWT token string
            
        Returns:
            User information dict with 'id', 'email', 'role', etc., or None if invalid
        """
        if not self.supabase_client:
            # Fallback to placeholder for development
            logger.warning("Supabase not configured, using placeholder authentication")
            return {"id": "system_admin", "email": "systemadmin@example.com", "role": "system_admin"}
        
        try:
            # Verify token with Supabase
            # Set the session with the token
            self.supabase_client.auth.set_session(token, None)
            response = self.supabase_client.auth.get_user()
            
            if response.user:
                user = response.user
                # Get user profile from database
                profile = self._get_user_profile(user.id)
                
                if profile:
                    # Get role name from role_id
                    role_name = "user"
                    if profile.get("role_id"):
                        role = self._get_role(profile["role_id"])
                        if role:
                            role_name = role.get("name", "user").lower().replace(" ", "_")
                    
                    return {
                        "id": user.id,
                        "email": user.email,
                        "role": role_name,
                        "name": profile.get("name"),
                        "status": profile.get("status", "active")
                    }
                else:
                    return {
                        "id": user.id,
                        "email": user.email,
                        "role": "user",
                        "name": None,
                        "status": "active"
                    }
            
            return None
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            return None
    
    def _get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile from database."""
        if not self.supabase_client:
            return None
        
        try:
            # Use service role key for database access
            service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            if not service_key:
                return None
            
            service_client = create_client(self.supabase_url, service_key)
            response = service_client.table("user_profiles").select("*").eq("id", user_id).execute()
            
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Failed to get user profile: {e}")
            return None
    
    async def get_current_user(self, credentials: HTTPAuthorizationCredentials = security) -> Dict[str, Any]:
        """
        Get current user from JWT token (FastAPI dependency).
        
        Args:
            credentials: HTTP Bearer credentials
            
        Returns:
            User information dict
            
        Raises:
            HTTPException: If token is invalid or missing
        """
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        token = credentials.credentials
        user = await self.verify_token(token)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
    
    def require_admin(self, user: Dict[str, Any]) -> Dict[str, Any]:
        """
        Require admin role for endpoint access.
        
        Args:
            user: User information dict
            
        Returns:
            User information dict
            
        Raises:
            HTTPException: If user is not admin
        """
        user_role = user.get("role", "").lower()
        if user_role not in ["system_admin", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        return user
    
    def is_admin(self, user: Dict[str, Any]) -> bool:
        """
        Check if user has admin privileges.
        
        Args:
            user: User information dict
            
        Returns:
            True if user is admin, False otherwise
        """
        user_role = user.get("role", "").lower()
        return user_role in ["system_admin", "admin"]
    
    async def require_admin_async(self, credentials: HTTPAuthorizationCredentials = security) -> Dict[str, Any]:
        """
        Async dependency for requiring admin access.
        
        This can be used as a FastAPI dependency to protect admin endpoints.
        
        Args:
            credentials: HTTP Bearer credentials
            
        Returns:
            Admin user information dict
            
        Raises:
            HTTPException: If not authenticated or not admin
        """
        user = await self.get_current_user(credentials)
        return self.require_admin(user)


# Global auth service instance
_auth_service: Optional[AuthService] = None


def get_auth_service() -> AuthService:
    """Get or create global auth service instance."""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service

