"""
User and Role Management API Endpoints

This module provides REST API endpoints for managing users and roles.
Integrated with Supabase for persistent storage and JWT authentication.
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
from ..services.auth_service import get_auth_service
from ..services.user_service import get_user_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/users", tags=["User Management"])
security = HTTPBearer()

# Fallback in-memory storage (used if Supabase not configured)
users_db: Dict[str, Dict[str, Any]] = {}
roles_db: Dict[str, Dict[str, Any]] = {}


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Get current user from JWT token using Supabase Auth.
    
    Returns:
        User information dict with 'id', 'email', 'role', etc.
    """
    auth_service = get_auth_service()
    user = await auth_service.get_current_user(credentials)
    return user


async def require_admin(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Require admin role for endpoint access."""
    auth_service = get_auth_service()
    return auth_service.require_admin(current_user)


@router.get("/stats", response_model=UserStatsResponse)
async def get_user_stats(current_user: Dict[str, Any] = Depends(require_admin)):
    """Get user statistics."""
    user_service = get_user_service()
    
    if user_service.use_supabase:
        stats = await user_service.get_user_stats()
        return UserStatsResponse(**stats)
    else:
        # Fallback to in-memory
        total_users = len(users_db)
        active_users = sum(1 for u in users_db.values() if u.get("status") == UserStatus.ACTIVE.value)
        pending_invites = sum(1 for u in users_db.values() if u.get("status") == UserStatus.PENDING.value)
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
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """List all users with pagination and filtering."""
    user_service = get_user_service()
    
    if user_service.use_supabase:
        # Get role_id if role filter is provided
        role_id = None
        if role_filter:
            role = await user_service.get_role_by_name(role_filter.value.replace("_", " ").title())
            if role:
                role_id = role["id"]
        
        users, total = await user_service.get_users(
            page=page,
            limit=limit,
            status_filter=status_filter.value if status_filter else None,
            role_id=role_id
        )
        
        # Convert to response models
        user_responses = []
        for u in users:
            # Map role_name to UserRole enum
            role_name = u.get("role_name", "user")
            try:
                role_enum = UserRole(role_name.lower().replace(" ", "_"))
            except ValueError:
                role_enum = UserRole.USER
            
            user_responses.append(UserResponse(
                id=str(u["id"]),
                email=u["email"],
                name=u.get("name"),
                role=role_enum,
                department=u.get("department"),
                status=UserStatus(u.get("status", "active")),
                created_at=datetime.fromisoformat(u["created_at"].replace("Z", "+00:00")) if isinstance(u.get("created_at"), str) else u.get("created_at", datetime.utcnow()),
                updated_at=datetime.fromisoformat(u["updated_at"].replace("Z", "+00:00")) if isinstance(u.get("updated_at"), str) else u.get("updated_at", datetime.utcnow()),
                last_login=datetime.fromisoformat(u["last_login"].replace("Z", "+00:00")) if u.get("last_login") and isinstance(u.get("last_login"), str) else u.get("last_login")
            ))
        
        return UserListResponse(
            users=user_responses,
            total=total,
            page=page,
            limit=limit
        )
    else:
        # Fallback to in-memory
        filtered_users = list(users_db.values())
        
        if status_filter:
            filtered_users = [u for u in filtered_users if u.get("status") == status_filter.value]
        if role_filter:
            filtered_users = [u for u in filtered_users if u.get("role") == role_filter.value]
        
        total = len(filtered_users)
        start = (page - 1) * limit
        end = start + limit
        paginated_users = filtered_users[start:end]
        
        user_responses = [
            UserResponse(
                id=u["id"],
                email=u["email"],
                name=u.get("name"),
                role=UserRole(u["role"]),
                department=u.get("department"),
                status=UserStatus(u["status"]),
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
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """Create a new user."""
    user_service = get_user_service()
    
    if user_service.use_supabase:
        # Check if user already exists
        existing_user = await user_service.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with email {user_data.email} already exists"
            )
        
        # Get role_id from role name
        role_id = None
        if user_data.role:
            role = await user_service.get_role_by_name(user_data.role.value.replace("_", " ").title())
            if role:
                role_id = role["id"]
        
        # Create user in Supabase
        user = await user_service.create_user(
            email=user_data.email,
            password=user_data.password,
            name=user_data.name,
            role_id=role_id,
            department=user_data.department,
            status=user_data.status.value
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user"
            )
        
        logger.info(f"User created: {user['id']} ({user_data.email}) by {current_user.get('email')}")
        
        # Map role_name to UserRole enum
        role_name = user.get("role_name", "user")
        try:
            role_enum = UserRole(role_name.lower().replace(" ", "_"))
        except ValueError:
            role_enum = UserRole.USER
        
        return UserResponse(
            id=str(user["id"]),
            email=user["email"],
            name=user.get("name"),
            role=role_enum,
            department=user.get("department"),
            status=UserStatus(user.get("status", "active")),
            created_at=datetime.fromisoformat(user["created_at"].replace("Z", "+00:00")) if isinstance(user.get("created_at"), str) else datetime.utcnow(),
            updated_at=datetime.fromisoformat(user["updated_at"].replace("Z", "+00:00")) if isinstance(user.get("updated_at"), str) else datetime.utcnow(),
            last_login=None
        )
    else:
        # Fallback to in-memory
        existing_user = next(
            (u for u in users_db.values() if u["email"] == user_data.email),
            None
        )
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with email {user_data.email} already exists"
            )
        
        user_id = str(uuid4())
        now = datetime.utcnow()
        
        user_record = {
            "id": user_id,
            "email": user_data.email,
            "password": user_data.password,
            "name": user_data.name,
            "role": user_data.role.value,
            "department": user_data.department,
            "status": user_data.status.value,
            "created_at": now,
            "updated_at": now,
            "last_login": None
        }
        
        users_db[user_id] = user_record
        
        logger.info(f"User created: {user_id} ({user_data.email}) by {current_user.get('email', 'unknown')}")
        
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
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """Get user by ID."""
    user_service = get_user_service()
    
    if user_service.use_supabase:
        user = await user_service.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found"
            )
        
        role_name = user.get("role_name", "user")
        try:
            role_enum = UserRole(role_name.lower().replace(" ", "_"))
        except ValueError:
            role_enum = UserRole.USER
        
        return UserResponse(
            id=str(user["id"]),
            email=user["email"],
            name=user.get("name"),
            role=role_enum,
            department=user.get("department"),
            status=UserStatus(user.get("status", "active")),
            created_at=datetime.fromisoformat(user["created_at"].replace("Z", "+00:00")) if isinstance(user.get("created_at"), str) else datetime.utcnow(),
            updated_at=datetime.fromisoformat(user["updated_at"].replace("Z", "+00:00")) if isinstance(user.get("updated_at"), str) else datetime.utcnow(),
            last_login=datetime.fromisoformat(user["last_login"].replace("Z", "+00:00")) if user.get("last_login") and isinstance(user.get("last_login"), str) else user.get("last_login")
        )
    else:
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
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """Update user information."""
    user_service = get_user_service()
    
    if user_service.use_supabase:
        user = await user_service.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found"
            )
        
        # Prepare update data
        update_data = {}
        if user_data.name is not None:
            update_data["name"] = user_data.name
        if user_data.department is not None:
            update_data["department"] = user_data.department
        if user_data.status is not None:
            update_data["status"] = user_data.status.value
        if user_data.role is not None:
            role = await user_service.get_role_by_name(user_data.role.value.replace("_", " ").title())
            if role:
                update_data["role_id"] = role["id"]
        
        updated_user = await user_service.update_user(user_id, **update_data)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update user"
            )
        
        # Get updated user with role info
        updated_user = await user_service.get_user(user_id)
        
        role_name = updated_user.get("role_name", "user")
        try:
            role_enum = UserRole(role_name.lower().replace(" ", "_"))
        except ValueError:
            role_enum = UserRole.USER
        
        logger.info(f"User updated: {user_id} by {current_user.get('email')}")
        
        return UserResponse(
            id=str(updated_user["id"]),
            email=updated_user["email"],
            name=updated_user.get("name"),
            role=role_enum,
            department=updated_user.get("department"),
            status=UserStatus(updated_user.get("status", "active")),
            created_at=datetime.fromisoformat(updated_user["created_at"].replace("Z", "+00:00")) if isinstance(updated_user.get("created_at"), str) else datetime.utcnow(),
            updated_at=datetime.fromisoformat(updated_user["updated_at"].replace("Z", "+00:00")) if isinstance(updated_user.get("updated_at"), str) else datetime.utcnow(),
            last_login=datetime.fromisoformat(updated_user["last_login"].replace("Z", "+00:00")) if updated_user.get("last_login") and isinstance(updated_user.get("last_login"), str) else updated_user.get("last_login")
        )
    else:
        user = users_db.get(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found"
            )
        
        if user_data.name is not None:
            user["name"] = user_data.name
        if user_data.role is not None:
            user["role"] = user_data.role.value
        if user_data.department is not None:
            user["department"] = user_data.department
        if user_data.status is not None:
            user["status"] = user_data.status.value
        
        user["updated_at"] = datetime.utcnow()
        
        logger.info(f"User updated: {user_id} by {current_user.get('email', 'unknown')}")
        
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
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """Delete a user."""
    user_service = get_user_service()
    
    if user_service.use_supabase:
        user = await user_service.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found"
            )
        
        success = await user_service.delete_user(user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete user"
            )
        
        logger.info(f"User deleted: {user_id} by {current_user.get('email')}")
    else:
        if user_id not in users_db:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found"
            )
        
        del users_db[user_id]
        logger.info(f"User deleted: {user_id} by {current_user.get('email', 'unknown')}")
    
    return None


@router.post("/{user_id}/deactivate", response_model=UserResponse)
async def deactivate_user(
    user_id: str,
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """Deactivate a user."""
    user_service = get_user_service()
    
    if user_service.use_supabase:
        user = await user_service.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found"
            )
        
        updated_user = await user_service.update_user(user_id, status="inactive")
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to deactivate user"
            )
        
        updated_user = await user_service.get_user(user_id)
        
        role_name = updated_user.get("role_name", "user")
        try:
            role_enum = UserRole(role_name.lower().replace(" ", "_"))
        except ValueError:
            role_enum = UserRole.USER
        
        logger.info(f"User deactivated: {user_id} by {current_user.get('email')}")
        
        return UserResponse(
            id=str(updated_user["id"]),
            email=updated_user["email"],
            name=updated_user.get("name"),
            role=role_enum,
            department=updated_user.get("department"),
            status=UserStatus(updated_user.get("status", "inactive")),
            created_at=datetime.fromisoformat(updated_user["created_at"].replace("Z", "+00:00")) if isinstance(updated_user.get("created_at"), str) else datetime.utcnow(),
            updated_at=datetime.fromisoformat(updated_user["updated_at"].replace("Z", "+00:00")) if isinstance(updated_user.get("updated_at"), str) else datetime.utcnow(),
            last_login=datetime.fromisoformat(updated_user["last_login"].replace("Z", "+00:00")) if updated_user.get("last_login") and isinstance(updated_user.get("last_login"), str) else updated_user.get("last_login")
        )
    else:
        user = users_db.get(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found"
            )
        
        user["status"] = UserStatus.INACTIVE.value
        user["updated_at"] = datetime.utcnow()
        
        logger.info(f"User deactivated: {user_id} by {current_user.get('email', 'unknown')}")
        
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
async def list_roles(current_user: Dict[str, Any] = Depends(require_admin)):
    """List all roles."""
    user_service = get_user_service()
    
    if user_service.use_supabase:
        roles = await user_service.get_roles()
        
        # Count users per role
        role_responses = []
        for role in roles:
            # Count users with this role
            users_with_role, _ = await user_service.get_users(role_id=role["id"], page=1, limit=1)
            user_count = len(users_with_role) if users_with_role else 0
            
            role_responses.append(RoleResponse(
                id=str(role["id"]),
                name=role["name"],
                description=role.get("description"),
                permissions=[Permission(p) for p in (role.get("permissions") or [])],
                user_count=user_count,
                created_at=datetime.fromisoformat(role["created_at"].replace("Z", "+00:00")) if isinstance(role.get("created_at"), str) else datetime.utcnow(),
                updated_at=datetime.fromisoformat(role["updated_at"].replace("Z", "+00:00")) if isinstance(role.get("updated_at"), str) else datetime.utcnow()
            ))
        
        return RoleListResponse(
            roles=role_responses,
            total=len(role_responses)
        )
    else:
        # Fallback to in-memory
        role_counts = {}
        for user in users_db.values():
            role = user.get("role", "user")
            role_counts[role] = role_counts.get(role, 0) + 1
        
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
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """Create a new role."""
    user_service = get_user_service()
    
    if user_service.use_supabase:
        # Check if role already exists
        existing_role = await user_service.get_role_by_name(role_data.name)
        if existing_role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Role '{role_data.name}' already exists"
            )
        
        role = await user_service.create_role(
            name=role_data.name,
            description=role_data.description,
            permissions=[p.value for p in role_data.permissions]
        )
        
        if not role:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create role"
            )
        
        logger.info(f"Role created: {role['id']} ({role_data.name}) by {current_user.get('email')}")
        
        return RoleResponse(
            id=str(role["id"]),
            name=role["name"],
            description=role.get("description"),
            permissions=[Permission(p) for p in (role.get("permissions") or [])],
            user_count=0,
            created_at=datetime.fromisoformat(role["created_at"].replace("Z", "+00:00")) if isinstance(role.get("created_at"), str) else datetime.utcnow(),
            updated_at=datetime.fromisoformat(role["updated_at"].replace("Z", "+00:00")) if isinstance(role.get("updated_at"), str) else datetime.utcnow()
        )
    else:
        # Fallback to in-memory
        existing_role = next(
            (r for r in roles_db.values() if r.get("name", "").lower() == role_data.name.lower()),
            None
        )
        if existing_role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Role '{role_data.name}' already exists"
            )
        
        role_id = str(uuid4())
        now = datetime.utcnow()
        
        role_record = {
            "id": role_id,
            "name": role_data.name,
            "description": role_data.description,
            "permissions": [p.value for p in role_data.permissions],
            "created_at": now,
            "updated_at": now
        }
        
        roles_db[role_id] = role_record
        
        logger.info(f"Role created: {role_id} ({role_data.name}) by {current_user.get('email', 'unknown')}")
        
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
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """Get role by ID."""
    user_service = get_user_service()
    
    if user_service.use_supabase:
        role = await user_service.get_role(role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role {role_id} not found"
            )
        
        # Count users with this role
        users_with_role, _ = await user_service.get_users(role_id=role_id, page=1, limit=1)
        user_count = len(users_with_role) if users_with_role else 0
        
        return RoleResponse(
            id=str(role["id"]),
            name=role["name"],
            description=role.get("description"),
            permissions=[Permission(p) for p in (role.get("permissions") or [])],
            user_count=user_count,
            created_at=datetime.fromisoformat(role["created_at"].replace("Z", "+00:00")) if isinstance(role.get("created_at"), str) else datetime.utcnow(),
            updated_at=datetime.fromisoformat(role["updated_at"].replace("Z", "+00:00")) if isinstance(role.get("updated_at"), str) else datetime.utcnow()
        )
    else:
        role = roles_db.get(role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role {role_id} not found"
            )
        
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
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """Update role information."""
    user_service = get_user_service()
    
    if user_service.use_supabase:
        role = await user_service.get_role(role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role {role_id} not found"
            )
        
        update_data = {}
        if role_data.name is not None:
            update_data["name"] = role_data.name
        if role_data.description is not None:
            update_data["description"] = role_data.description
        if role_data.permissions is not None:
            update_data["permissions"] = [p.value for p in role_data.permissions]
        
        updated_role = await user_service.update_role(role_id, **update_data)
        if not updated_role:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update role"
            )
        
        # Count users with this role
        users_with_role, _ = await user_service.get_users(role_id=role_id, page=1, limit=1)
        user_count = len(users_with_role) if users_with_role else 0
        
        logger.info(f"Role updated: {role_id} by {current_user.get('email')}")
        
        return RoleResponse(
            id=str(updated_role["id"]),
            name=updated_role["name"],
            description=updated_role.get("description"),
            permissions=[Permission(p) for p in (updated_role.get("permissions") or [])],
            user_count=user_count,
            created_at=datetime.fromisoformat(updated_role["created_at"].replace("Z", "+00:00")) if isinstance(updated_role.get("created_at"), str) else datetime.utcnow(),
            updated_at=datetime.fromisoformat(updated_role["updated_at"].replace("Z", "+00:00")) if isinstance(updated_role.get("updated_at"), str) else datetime.utcnow()
        )
    else:
        role = roles_db.get(role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role {role_id} not found"
            )
        
        if role_data.name is not None:
            role["name"] = role_data.name
        if role_data.description is not None:
            role["description"] = role_data.description
        if role_data.permissions is not None:
            role["permissions"] = [p.value for p in role_data.permissions]
        
        role["updated_at"] = datetime.utcnow()
        
        role_name = role.get("name", "")
        user_count = sum(1 for u in users_db.values() if u.get("role") == role_name.lower().replace(" ", "_"))
        
        logger.info(f"Role updated: {role_id} by {current_user.get('email', 'unknown')}")
        
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
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """Delete a role."""
    user_service = get_user_service()
    
    if user_service.use_supabase:
        role = await user_service.get_role(role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role {role_id} not found"
            )
        
        # Check if any users have this role
        users_with_role, _ = await user_service.get_users(role_id=role_id, page=1, limit=1)
        if users_with_role and len(users_with_role) > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete role: {len(users_with_role)} user(s) still have this role"
            )
        
        success = await user_service.delete_role(role_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete role"
            )
        
        logger.info(f"Role deleted: {role_id} by {current_user.get('email')}")
    else:
        if role_id not in roles_db:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role {role_id} not found"
            )
        
        role_name = roles_db[role_id].get("name", "")
        users_with_role = sum(1 for u in users_db.values() if u.get("role") == role_name.lower().replace(" ", "_"))
        
        if users_with_role > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete role: {users_with_role} user(s) still have this role"
            )
        
        del roles_db[role_id]
        logger.info(f"Role deleted: {role_id} by {current_user.get('email', 'unknown')}")
    
    return None


def initialize_default_data():
    """Initialize default roles and system admin user."""
    from datetime import datetime
    from uuid import uuid4
    from ..models.user_models import UserRole, UserStatus, Permission
    
    now = datetime.utcnow()
    
    # Only initialize if databases are empty
    if roles_db or users_db:
        return
    
    # Initialize default roles
    default_roles = [
        {
            "id": str(uuid4()),
            "name": "Admin",
            "description": "Full system access and management capabilities",
            "permissions": [p.value for p in Permission],
            "created_at": now,
            "updated_at": now
        },
        {
            "id": str(uuid4()),
            "name": "Manager",
            "description": "Team management and operational oversight",
            "permissions": [
                Permission.CREATE_BLOG.value,
                Permission.READ_BLOG.value,
                Permission.UPDATE_BLOG.value,
                Permission.READ_USER.value,
                Permission.VIEW_ANALYTICS.value
            ],
            "created_at": now,
            "updated_at": now
        },
        {
            "id": str(uuid4()),
            "name": "User",
            "description": "Standard user with basic blog creation access",
            "permissions": [
                Permission.CREATE_BLOG.value,
                Permission.READ_BLOG.value,
                Permission.UPDATE_BLOG.value
            ],
            "created_at": now,
            "updated_at": now
        }
    ]
    
    for role in default_roles:
        roles_db[role["id"]] = role
    
    # Initialize system admin user
    system_admin_id = str(uuid4())
    users_db[system_admin_id] = {
        "id": system_admin_id,
        "email": "systemadmin@example.com",
        "password": "admin123",  # In production, hash this
        "name": "System Admin",
        "role": UserRole.SYSTEM_ADMIN.value,
        "department": "IT",
        "status": UserStatus.ACTIVE.value,
        "created_at": now,
        "updated_at": now,
        "last_login": now
    }
    
    logger.info("Default roles and system admin user initialized")

