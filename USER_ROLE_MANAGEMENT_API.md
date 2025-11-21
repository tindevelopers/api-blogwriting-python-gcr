# User and Role Management API Documentation

## Overview

The User and Role Management API provides endpoints for managing users, roles, and permissions. All endpoints require admin authentication.

## Base URL

**Development:**
```
https://blog-writer-api-dev-613248238610.europe-west9.run.app
```

## Authentication

All endpoints require authentication via Bearer token:

```bash
Authorization: Bearer <token>
```

**Note:** Currently using placeholder authentication. In production, implement JWT token verification with Supabase Auth.

## Endpoints

### User Statistics

**GET** `/api/v1/users/stats`

Get user statistics summary.

**Response:**
```json
{
  "total_users": 24,
  "active_users": 18,
  "pending_invites": 3,
  "roles": 5
}
```

---

### List Users

**GET** `/api/v1/users`

List all users with pagination and filtering.

**Query Parameters:**
- `page` (int, default: 1): Page number
- `limit` (int, default: 10, max: 100): Items per page
- `status` (string, optional): Filter by status (active, inactive, pending, suspended)
- `role` (string, optional): Filter by role (system_admin, admin, manager, user, viewer)

**Example:**
```bash
GET /api/v1/users?page=1&limit=10&status=active&role=admin
```

**Response:**
```json
{
  "users": [
    {
      "id": "uuid",
      "email": "john.smith@company.com",
      "name": "John Smith",
      "role": "admin",
      "department": "Engineering",
      "status": "active",
      "created_at": "2024-01-15T00:00:00",
      "updated_at": "2024-12-19T14:30:25",
      "last_login": "2024-12-19T14:30:25"
    }
  ],
  "total": 24,
  "page": 1,
  "limit": 10
}
```

---

### Create User

**POST** `/api/v1/users`

Create a new user. **System admin only.**

**Request Body:**
```json
{
  "email": "john.smith@company.com",
  "password": "password123",
  "name": "John Smith",
  "role": "admin",
  "department": "Engineering",
  "status": "active"
}
```

**Response:**
```json
{
  "id": "uuid",
  "email": "john.smith@company.com",
  "name": "John Smith",
  "role": "admin",
  "department": "Engineering",
  "status": "active",
  "created_at": "2024-12-19T15:00:00",
  "updated_at": "2024-12-19T15:00:00",
  "last_login": null
}
```

**JavaScript Example:**
```javascript
const response = await fetch('https://blog-writer-api-dev-613248238610.europe-west9.run.app/api/v1/users', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_TOKEN',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    email: 'john.smith@company.com',
    password: 'password123',
    name: 'John Smith',
    role: 'admin',
    department: 'Engineering',
    status: 'active'
  })
});

const user = await response.json();
console.log('User created:', user);
```

---

### Get User

**GET** `/api/v1/users/{user_id}`

Get user by ID.

**Response:**
```json
{
  "id": "uuid",
  "email": "john.smith@company.com",
  "name": "John Smith",
  "role": "admin",
  "department": "Engineering",
  "status": "active",
  "created_at": "2024-01-15T00:00:00",
  "updated_at": "2024-12-19T14:30:25",
  "last_login": "2024-12-19T14:30:25"
}
```

---

### Update User

**PATCH** `/api/v1/users/{user_id}`

Update user information.

**Request Body:**
```json
{
  "name": "John Smith Updated",
  "role": "manager",
  "department": "Product",
  "status": "active"
}
```

**Response:** Updated user object

---

### Delete User

**DELETE** `/api/v1/users/{user_id}`

Delete a user permanently.

**Response:** 204 No Content

---

### Deactivate User

**POST** `/api/v1/users/{user_id}/deactivate`

Deactivate a user (sets status to inactive).

**Response:** Updated user object with status="inactive"

---

### List Roles

**GET** `/api/v1/users/roles`

List all roles with user counts.

**Response:**
```json
{
  "roles": [
    {
      "id": "uuid",
      "name": "Admin",
      "description": "Full system access and management capabilities",
      "permissions": ["create_user", "read_user", "update_user", "delete_user", ...],
      "user_count": 2,
      "created_at": "2024-01-15T00:00:00",
      "updated_at": "2024-01-15T00:00:00"
    }
  ],
  "total": 5
}
```

---

### Create Role

**POST** `/api/v1/users/roles`

Create a new role.

**Request Body:**
```json
{
  "name": "Editor",
  "description": "Can edit and publish blog posts",
  "permissions": ["create_blog", "read_blog", "update_blog", "delete_blog"]
}
```

**Response:** Created role object

---

### Get Role

**GET** `/api/v1/users/roles/{role_id}`

Get role by ID.

**Response:** Role object

---

### Update Role

**PATCH** `/api/v1/users/roles/{role_id}`

Update role information.

**Request Body:**
```json
{
  "name": "Editor Updated",
  "description": "Updated description",
  "permissions": ["create_blog", "read_blog", "update_blog"]
}
```

**Response:** Updated role object

---

### Delete Role

**DELETE** `/api/v1/users/roles/{role_id}`

Delete a role. Cannot delete if users still have this role.

**Response:** 204 No Content

---

## Default Data

On startup, the API initializes:

1. **Default Roles:**
   - **Admin**: Full system access
   - **Manager**: Team management and operational oversight
   - **User**: Standard user with basic blog creation access

2. **System Admin User:**
   - Email: `systemadmin@example.com`
   - Role: `system_admin`
   - Status: `active`

---

## User Roles

- `system_admin`: Full system access
- `admin`: Administrative access
- `manager`: Team management access
- `user`: Standard user access
- `viewer`: Read-only access

## User Status

- `active`: User is active
- `inactive`: User is deactivated
- `pending`: User invitation pending
- `suspended`: User is suspended

## Permissions

Available permissions:
- `create_user`, `read_user`, `update_user`, `delete_user`
- `create_role`, `read_role`, `update_role`, `delete_role`
- `create_blog`, `read_blog`, `update_blog`, `delete_blog`
- `manage_system`, `view_analytics`

---

## Frontend Integration Example

```javascript
class UserManagementAPI {
  constructor(baseUrl, token) {
    this.baseUrl = baseUrl;
    this.token = token;
  }

  async getStats() {
    const response = await fetch(`${this.baseUrl}/api/v1/users/stats`, {
      headers: { 'Authorization': `Bearer ${this.token}` }
    });
    return await response.json();
  }

  async listUsers(page = 1, limit = 10, filters = {}) {
    const params = new URLSearchParams({
      page: page.toString(),
      limit: limit.toString(),
      ...filters
    });
    const response = await fetch(`${this.baseUrl}/api/v1/users?${params}`, {
      headers: { 'Authorization': `Bearer ${this.token}` }
    });
    return await response.json();
  }

  async createUser(userData) {
    const response = await fetch(`${this.baseUrl}/api/v1/users`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(userData)
    });
    return await response.json();
  }

  async listRoles() {
    const response = await fetch(`${this.baseUrl}/api/v1/users/roles`, {
      headers: { 'Authorization': `Bearer ${this.token}` }
    });
    return await response.json();
  }
}

// Usage
const api = new UserManagementAPI(
  'https://blog-writer-api-dev-613248238610.europe-west9.run.app',
  'YOUR_TOKEN'
);

// Get stats
const stats = await api.getStats();
console.log('Total users:', stats.total_users);

// Create user
const newUser = await api.createUser({
  email: 'newuser@example.com',
  password: 'password123',
  name: 'New User',
  role: 'user',
  status: 'active'
});
```

---

## Next Steps

1. **Supabase Integration**: Replace in-memory storage with Supabase database
2. **JWT Authentication**: Implement proper JWT token verification
3. **Password Hashing**: Hash passwords before storing
4. **Email Verification**: Add email verification for new users
5. **Role-Based Access Control**: Implement fine-grained permission checking

---

## Deployment Status

✅ **Code Deployed**: User and role management endpoints are now available
✅ **Default Data**: System admin user and default roles initialized
⏳ **Supabase Integration**: Pending (currently using in-memory storage)

