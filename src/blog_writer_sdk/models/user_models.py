"""
User and Role Management Models

This module contains Pydantic models for user and role management operations.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, EmailStr, Field


class UserRole(str, Enum):
    """User role types."""
    SYSTEM_ADMIN = "system_admin"
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"
    VIEWER = "viewer"


class UserStatus(str, Enum):
    """User status types."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    SUSPENDED = "suspended"


class Permission(str, Enum):
    """Permission types."""
    # User Management
    CREATE_USER = "create_user"
    READ_USER = "read_user"
    UPDATE_USER = "update_user"
    DELETE_USER = "delete_user"
    
    # Role Management
    CREATE_ROLE = "create_role"
    READ_ROLE = "read_role"
    UPDATE_ROLE = "update_role"
    DELETE_ROLE = "delete_role"
    
    # Blog Management
    CREATE_BLOG = "create_blog"
    READ_BLOG = "read_blog"
    UPDATE_BLOG = "update_blog"
    DELETE_BLOG = "delete_blog"
    
    # System
    MANAGE_SYSTEM = "manage_system"
    VIEW_ANALYTICS = "view_analytics"


class UserCreate(BaseModel):
    """Request model for creating a new user."""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password (min 8 characters)")
    name: Optional[str] = Field(None, description="User full name")
    role: UserRole = Field(default=UserRole.USER, description="User role")
    department: Optional[str] = Field(None, description="User department")
    status: UserStatus = Field(default=UserStatus.PENDING, description="User status")


class UserUpdate(BaseModel):
    """Request model for updating a user."""
    name: Optional[str] = Field(None, description="User full name")
    role: Optional[UserRole] = Field(None, description="User role")
    department: Optional[str] = Field(None, description="User department")
    status: Optional[UserStatus] = Field(None, description="User status")


class UserResponse(BaseModel):
    """Response model for user data."""
    id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    name: Optional[str] = Field(None, description="User full name")
    role: UserRole = Field(..., description="User role")
    department: Optional[str] = Field(None, description="User department")
    status: UserStatus = Field(..., description="User status")
    created_at: datetime = Field(..., description="User creation timestamp")
    updated_at: datetime = Field(..., description="User last update timestamp")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    
    class Config:
        from_attributes = True


class RoleCreate(BaseModel):
    """Request model for creating a new role."""
    name: str = Field(..., min_length=1, max_length=100, description="Role name")
    description: Optional[str] = Field(None, description="Role description")
    permissions: List[Permission] = Field(default_factory=list, description="List of permissions")


class RoleUpdate(BaseModel):
    """Request model for updating a role."""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Role name")
    description: Optional[str] = Field(None, description="Role description")
    permissions: Optional[List[Permission]] = Field(None, description="List of permissions")


class RoleResponse(BaseModel):
    """Response model for role data."""
    id: str = Field(..., description="Role ID")
    name: str = Field(..., description="Role name")
    description: Optional[str] = Field(None, description="Role description")
    permissions: List[Permission] = Field(default_factory=list, description="List of permissions")
    user_count: int = Field(default=0, description="Number of users with this role")
    created_at: datetime = Field(..., description="Role creation timestamp")
    updated_at: datetime = Field(..., description="Role last update timestamp")
    
    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """Response model for user list."""
    users: List[UserResponse] = Field(..., description="List of users")
    total: int = Field(..., description="Total number of users")
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Items per page")


class RoleListResponse(BaseModel):
    """Response model for role list."""
    roles: List[RoleResponse] = Field(..., description="List of roles")
    total: int = Field(..., description="Total number of roles")


class UserStatsResponse(BaseModel):
    """Response model for user statistics."""
    total_users: int = Field(..., description="Total number of users")
    active_users: int = Field(..., description="Number of active users")
    pending_invites: int = Field(..., description="Number of pending invites")
    roles: int = Field(..., description="Number of roles")

