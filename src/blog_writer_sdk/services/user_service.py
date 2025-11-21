"""
User Service for Supabase Integration

This module provides database operations for user and role management using Supabase.
"""

import os
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

try:
    from supabase import create_client, Client
except ImportError:
    create_client = None
    Client = None

logger = logging.getLogger(__name__)


class UserService:
    """Service for managing users and roles in Supabase."""
    
    def __init__(self, supabase_url: Optional[str] = None, supabase_key: Optional[str] = None):
        """
        Initialize user service with Supabase.
        
        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase service role key
        """
        self.supabase_url = supabase_url or os.getenv("SUPABASE_URL")
        self.supabase_key = supabase_key or os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            logger.warning("Supabase credentials not configured. User service will use in-memory storage.")
            self.supabase_client = None
            self.use_supabase = False
        else:
            try:
                self.supabase_client = create_client(self.supabase_url, self.supabase_key)
                self.use_supabase = True
                logger.info("User service initialized with Supabase")
            except Exception as e:
                logger.error(f"Failed to initialize Supabase client: {e}")
                self.supabase_client = None
                self.use_supabase = False
    
    # Role Operations
    async def get_roles(self) -> List[Dict[str, Any]]:
        """Get all roles."""
        if not self.use_supabase:
            return []
        
        try:
            response = self.supabase_client.table("roles").select("*").order("name").execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Failed to get roles: {e}")
            return []
    
    async def get_role(self, role_id: str) -> Optional[Dict[str, Any]]:
        """Get role by ID."""
        if not self.use_supabase:
            return None
        
        try:
            response = self.supabase_client.table("roles").select("*").eq("id", role_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Failed to get role: {e}")
            return None
    
    async def create_role(self, name: str, description: Optional[str], permissions: List[str]) -> Optional[Dict[str, Any]]:
        """Create a new role."""
        if not self.use_supabase:
            return None
        
        try:
            data = {
                "name": name,
                "description": description,
                "permissions": permissions,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            response = self.supabase_client.table("roles").insert(data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Failed to create role: {e}")
            raise
    
    async def update_role(self, role_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Update role."""
        if not self.use_supabase:
            return None
        
        try:
            kwargs["updated_at"] = datetime.utcnow().isoformat()
            response = self.supabase_client.table("roles").update(kwargs).eq("id", role_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Failed to update role: {e}")
            raise
    
    async def delete_role(self, role_id: str) -> bool:
        """Delete role."""
        if not self.use_supabase:
            return False
        
        try:
            self.supabase_client.table("roles").delete().eq("id", role_id).execute()
            return True
        except Exception as e:
            logger.error(f"Failed to delete role: {e}")
            raise
    
    # User Operations
    async def get_users(
        self,
        page: int = 1,
        limit: int = 10,
        status_filter: Optional[str] = None,
        role_id: Optional[str] = None
    ) -> tuple[List[Dict[str, Any]], int]:
        """Get users with pagination and filtering."""
        if not self.use_supabase:
            return [], 0
        
        try:
            query = self.supabase_client.table("user_profiles").select("*, roles(*)")
            
            if status_filter:
                query = query.eq("status", status_filter)
            if role_id:
                query = query.eq("role_id", role_id)
            
            # Get total count (execute without pagination first)
            count_response = query.execute()
            total = len(count_response.data) if count_response.data else 0
            
            # Apply pagination
            start = (page - 1) * limit
            end = start + limit - 1
            response = query.range(start, end).order("created_at", desc=True).execute()
            
            users = response.data or []
            # Flatten role data
            for user in users:
                if user.get("roles") and isinstance(user["roles"], list) and len(user["roles"]) > 0:
                    role = user["roles"][0]
                    user["role_name"] = role.get("name")
                    user["role_permissions"] = role.get("permissions", [])
                user.pop("roles", None)
            
            return users, total
        except Exception as e:
            logger.error(f"Failed to get users: {e}")
            return [], 0
    
    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        if not self.use_supabase:
            return None
        
        try:
            response = self.supabase_client.table("user_profiles").select("*, roles(*)").eq("id", user_id).execute()
            if response.data:
                user = response.data[0]
                if user.get("roles") and isinstance(user["roles"], list) and len(user["roles"]) > 0:
                    role = user["roles"][0]
                    user["role_name"] = role.get("name")
                    user["role_permissions"] = role.get("permissions", [])
                user.pop("roles", None)
                return user
            return None
        except Exception as e:
            logger.error(f"Failed to get user: {e}")
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email."""
        if not self.use_supabase:
            return None
        
        try:
            response = self.supabase_client.table("user_profiles").select("*, roles(*)").eq("email", email).execute()
            if response.data:
                user = response.data[0]
                if user.get("roles") and isinstance(user["roles"], list) and len(user["roles"]) > 0:
                    role = user["roles"][0]
                    user["role_name"] = role.get("name")
                    user["role_permissions"] = role.get("permissions", [])
                user.pop("roles", None)
                return user
            return None
        except Exception as e:
            logger.error(f"Failed to get user by email: {e}")
            return None
    
    async def create_user(
        self,
        email: str,
        password: str,
        name: Optional[str],
        role_id: Optional[str],
        department: Optional[str],
        status: str
    ) -> Optional[Dict[str, Any]]:
        """Create a new user in Supabase Auth and user_profiles."""
        if not self.use_supabase:
            return None
        
        try:
            # First, create user in Supabase Auth
            auth_response = self.supabase_client.auth.admin.create_user({
                "email": email,
                "password": password,
                "email_confirm": True  # Auto-confirm email
            })
            
            if not auth_response.user:
                raise Exception("Failed to create user in Supabase Auth")
            
            user_id = auth_response.user.id
            
            # Then create user profile
            profile_data = {
                "id": user_id,
                "email": email,
                "name": name,
                "role_id": role_id,
                "department": department,
                "status": status,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            response = self.supabase_client.table("user_profiles").insert(profile_data).execute()
            
            if response.data:
                user = response.data[0]
                # Get role info
                if role_id:
                    role = await self.get_role(role_id)
                    if role:
                        user["role_name"] = role.get("name")
                        user["role_permissions"] = role.get("permissions", [])
                return user
            
            return None
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            raise
    
    async def update_user(self, user_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Update user."""
        if not self.use_supabase:
            return None
        
        try:
            kwargs["updated_at"] = datetime.utcnow().isoformat()
            response = self.supabase_client.table("user_profiles").update(kwargs).eq("id", user_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Failed to update user: {e}")
            raise
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete user (also deletes from auth)."""
        if not self.use_supabase:
            return False
        
        try:
            # Delete from user_profiles (cascade will handle auth.users)
            self.supabase_client.table("user_profiles").delete().eq("id", user_id).execute()
            # Also delete from auth
            self.supabase_client.auth.admin.delete_user(user_id)
            return True
        except Exception as e:
            logger.error(f"Failed to delete user: {e}")
            raise
    
    async def get_user_stats(self) -> Dict[str, int]:
        """Get user statistics."""
        if not self.use_supabase:
            return {"total_users": 0, "active_users": 0, "pending_invites": 0, "roles": 0}
        
        try:
            # Get total users
            total_response = self.supabase_client.table("user_profiles").select("id", count="exact").execute()
            total_users = total_response.count if hasattr(total_response, 'count') else 0
            
            # Get active users
            active_response = self.supabase_client.table("user_profiles").select("id", count="exact").eq("status", "active").execute()
            active_users = active_response.count if hasattr(active_response, 'count') else 0
            
            # Get pending invites
            pending_response = self.supabase_client.table("user_profiles").select("id", count="exact").eq("status", "pending").execute()
            pending_invites = pending_response.count if hasattr(pending_response, 'count') else 0
            
            # Get total roles
            roles_response = self.supabase_client.table("roles").select("id", count="exact").execute()
            total_roles = roles_response.count if hasattr(roles_response, 'count') else 0
            
            return {
                "total_users": total_users or 0,
                "active_users": active_users or 0,
                "pending_invites": pending_invites or 0,
                "roles": total_roles or 0
            }
        except Exception as e:
            logger.error(f"Failed to get user stats: {e}")
            return {"total_users": 0, "active_users": 0, "pending_invites": 0, "roles": 0}
    
    async def get_role_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get role by name."""
        if not self.use_supabase:
            return None
        
        try:
            response = self.supabase_client.table("roles").select("*").eq("name", name).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Failed to get role by name: {e}")
            return None


# Global user service instance
_user_service: Optional[UserService] = None


def get_user_service() -> UserService:
    """Get or create global user service instance."""
    global _user_service
    if _user_service is None:
        _user_service = UserService()
    return _user_service

