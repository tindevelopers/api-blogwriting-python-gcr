"""
User and Role Management API Endpoints

This module provides REST API endpoints for managing users and roles.
"""

import os
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Depends, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import ValidationError

from ..models.user_models import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
    UserStatsResponse,
    RoleCreate,
    RoleUpdate,
    RoleResponse,
    RoleListResponse,
    UserRole,
    UserStatus,
    Permission
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/users", tags=["User Management"])
security = HTTPBearer()

# In-memory storage (in production, use Supabase)
users_db: Dict[str, Dict[str, Any]] = {}
roles_db: Dict[str, Dict[str, Any]] = {}


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    Get current user from JWT token.
    In production, verify JWT token with Supabase Auth.
    """
    # For now, accept any token (implement proper JWT verification)
    token = credentials.credentials
    # TODO: Verify JWT token with Supabase Auth
    # For development, we'll use a simple check
    return "system_admin"  # Placeholder


def require_admin(current_user: str = Depends(get_current_user)) -> str:
    """Require admin role for endpoint access."""
    # TODO: Check user role from database
    if current_user != "system_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


@router.get("/stats", response_model=UserStatsResponse)
async def get_user_stats(current_user: str = Depends(require_admin)):
    """Get user statistics."""
    total_users = len(users_db)
    active_users = sum(1 for u in users_db.values() if u.get("status") == UserStatus.ACTIVE)
    pending_invites = sum(1 for u in users_db.values() if u.get("status") == UserStatus.PENDING)
    total_roles = len(roles_db)
    
    return UserStatsResponse(
        total_users=total_users,
        active_users=active_users,
        pending_invites=pending_invites,
        roles=total_roles
    )


@router.get("", response_model=UserListResponse)
async def list_users(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    status_filter: Optional[UserStatus] = Query(None, alias="status"),
    role_filter: Optional[UserRole] = Query(None, alias="role"),
    current_user: str = Depends(require_admin)
):
    """List all users with pagination and filtering."""
    filtered_users = list(users_db.values())
    
    # Apply filters
    if status_filter:
        filtered_users = [u for u in filtered_users if u.get("status") == status_filter]
    if role_filter:
        filtered_users = [u for u in filtered_users if u.get("role") == role_filter]
    
    # Pagination
    total = len(filtered_users)
    start = (page - 1) * limit
    end = start + limit
    paginated_users = filtered_users[start:end]
    
    # Convert to response models
    user_responses = [
        UserResponse(
            id=u["id"],
            email=u["email"],
            name=u.get("name"),
            role=u["role"],
            department=u.get("department"),
            status=u["status"],
            created_at=u["created_at"],
            updated_at=u["updated_at"],
            last_login=u.get("last_login")
        )
        for u in paginated_users
    ]
    
    return UserListResponse(
        users=user_responses,
        total=total,
        page=page,
        limit=limit
    )


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: str = Depends(require_admin)
):
    """Create a new user."""
    # Check if user already exists
    existing_user = next(
        (u for u in users_db.values() if u["email"] == user_data.email),
        None
    )
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with email {user_data.email} already exists"
        )
    
    # Create user ID
    user_id = str(uuid4())
    now = datetime.utcnow()
    
    # Create user record
    user_record = {
        "id": user_id,
        "email": user_data.email,
        "password": user_data.password,  # In production, hash this
        "name": user_data.name,
        "role": user_data.role.value,
        "department": user_data.department,
        "status": user_data.status.value,
        "created_at": now,
        "updated_at": now,
        "last_login": None
    }
    
    users_db[user_id] = user_record
    
    logger.info(f"User created: {user_id} ({user_data.email}) by {current_user}")
    
    return UserResponse(
        id=user_id,
        email=user_data.email,
        name=user_data.name,
        role=user_data.role,
        department=user_data.department,
        status=user_data.status,
        created_at=now,
        updated_at=now,
        last_login=None
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: str = Depends(require_admin)
):
    """Get user by ID."""
    user = users_db.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )
    
    return UserResponse(
        id=user["id"],
        email=user["email"],
        name=user.get("name"),
        role=UserRole(user["role"]),
        department=user.get("department"),
        status=UserStatus(user["status"]),
        created_at=user["created_at"],
        updated_at=user["updated_at"],
        last_login=user.get("last_login")
    )


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_user: str = Depends(require_admin)
):
    """Update user information."""
    user = users_db.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )
    
    # Update fields
    if user_data.name is not None:
        user["name"] = user_data.name
    if user_data.role is not None:
        user["role"] = user_data.role.value
    if user_data.department is not None:
        user["department"] = user_data.department
    if user_data.status is not None:
        user["status"] = user_data.status.value
    
    user["updated_at"] = datetime.utcnow()
    
    logger.info(f"User updated: {user_id} by {current_user}")
    
    return UserResponse(
        id=user["id"],
        email=user["email"],
        name=user.get("name"),
        role=UserRole(user["role"]),
        department=user.get("department"),
        status=UserStatus(user["status"]),
        created_at=user["created_at"],
        updated_at=user["updated_at"],
        last_login=user.get("last_login")
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    current_user: str = Depends(require_admin)
):
    """Delete a user."""
    if user_id not in users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )
    
    del users_db[user_id]
    logger.info(f"User deleted: {user_id} by {current_user}")
    
    return None


@router.post("/{user_id}/deactivate", response_model=UserResponse)
async def deactivate_user(
    user_id: str,
    current_user: str = Depends(require_admin)
):
    """Deactivate a user."""
    user = users_db.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )
    
    user["status"] = UserStatus.INACTIVE.value
    user["updated_at"] = datetime.utcnow()
    
    logger.info(f"User deactivated: {user_id} by {current_user}")
    
    return UserResponse(
        id=user["id"],
        email=user["email"],
        name=user.get("name"),
        role=UserRole(user["role"]),
        department=user.get("department"),
        status=UserStatus(user["status"]),
        created_at=user["created_at"],
        updated_at=user["updated_at"],
        last_login=user.get("last_login")
    )


# Role Management Endpoints

@router.get("/roles", response_model=RoleListResponse)
async def list_roles(current_user: str = Depends(require_admin)):
    """List all roles."""
    # Count users per role
    role_counts = {}
    for user in users_db.values():
        role = user.get("role", "user")
        role_counts[role] = role_counts.get(role, 0) + 1
    
    # Convert to response models
    role_responses = []
    for role_id, role_data in roles_db.items():
        role_name = role_data.get("name", role_id)
        user_count = role_counts.get(role_name.lower().replace(" ", "_"), 0)
        
        role_responses.append(RoleResponse(
            id=role_id,
            name=role_name,
            description=role_data.get("description"),
            permissions=[Permission(p) for p in role_data.get("permissions", [])],
            user_count=user_count,
            created_at=role_data.get("created_at", datetime.utcnow()),
            updated_at=role_data.get("updated_at", datetime.utcnow())
        ))
    
    return RoleListResponse(
        roles=role_responses,
        total=len(role_responses)
    )


@router.post("/roles", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: RoleCreate,
    current_user: str = Depends(require_admin)
):
    """Create a new role."""
    # Check if role already exists
    existing_role = next(
        (r for r in roles_db.values() if r.get("name", "").lower() == role_data.name.lower()),
        None
    )
    if existing_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role '{role_data.name}' already exists"
        )
    
    # Create role ID
    role_id = str(uuid4())
    now = datetime.utcnow()
    
    # Create role record
    role_record = {
        "id": role_id,
        "name": role_data.name,
        "description": role_data.description,
        "permissions": [p.value for p in role_data.permissions],
        "created_at": now,
        "updated_at": now
    }
    
    roles_db[role_id] = role_record
    
    logger.info(f"Role created: {role_id} ({role_data.name}) by {current_user}")
    
    return RoleResponse(
        id=role_id,
        name=role_data.name,
        description=role_data.description,
        permissions=role_data.permissions,
        user_count=0,
        created_at=now,
        updated_at=now
    )


@router.get("/roles/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: str,
    current_user: str = Depends(require_admin)
):
    """Get role by ID."""
    role = roles_db.get(role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role {role_id} not found"
        )
    
    # Count users with this role
    role_name = role.get("name", "")
    user_count = sum(1 for u in users_db.values() if u.get("role") == role_name.lower().replace(" ", "_"))
    
    return RoleResponse(
        id=role["id"],
        name=role["name"],
        description=role.get("description"),
        permissions=[Permission(p) for p in role.get("permissions", [])],
        user_count=user_count,
        created_at=role.get("created_at", datetime.utcnow()),
        updated_at=role.get("updated_at", datetime.utcnow())
    )


@router.patch("/roles/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: str,
    role_data: RoleUpdate,
    current_user: str = Depends(require_admin)
):
    """Update role information."""
    role = roles_db.get(role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role {role_id} not found"
        )
    
    # Update fields
    if role_data.name is not None:
        role["name"] = role_data.name
    if role_data.description is not None:
        role["description"] = role_data.description
    if role_data.permissions is not None:
        role["permissions"] = [p.value for p in role_data.permissions]
    
    role["updated_at"] = datetime.utcnow()
    
    logger.info(f"Role updated: {role_id} by {current_user}")
    
    # Count users with this role
    role_name = role.get("name", "")
    user_count = sum(1 for u in users_db.values() if u.get("role") == role_name.lower().replace(" ", "_"))
    
    return RoleResponse(
        id=role["id"],
        name=role["name"],
        description=role.get("description"),
        permissions=[Permission(p) for p in role.get("permissions", [])],
        user_count=user_count,
        created_at=role.get("created_at", datetime.utcnow()),
        updated_at=role["updated_at"]
    )


@router.delete("/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: str,
    current_user: str = Depends(require_admin)
):
    """Delete a role."""
    if role_id not in roles_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role {role_id} not found"
        )
    
    # Check if any users have this role
    role_name = roles_db[role_id].get("name", "")
    users_with_role = sum(1 for u in users_db.values() if u.get("role") == role_name.lower().replace(" ", "_"))
    
    if users_with_role > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete role: {users_with_role} user(s) still have this role"
        )
    
    del roles_db[role_id]
    logger.info(f"Role deleted: {role_id} by {current_user}")
    
    return None

