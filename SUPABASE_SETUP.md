# Supabase Setup Guide for User Management

## Overview

The user management system is now integrated with Supabase for:
- **Persistent storage** - Users and roles stored in Supabase database
- **JWT authentication** - Token verification via Supabase Auth
- **User profiles** - Extended user data in `user_profiles` table

## Database Setup

### 1. Run the SQL Schema

Execute the SQL in `supabase_user_management_schema.sql` in your Supabase SQL Editor:

```sql
-- This creates:
-- - roles table
-- - user_profiles table (extends auth.users)
-- - Indexes and RLS policies
-- - Default roles (Admin, Manager, User)
```

### 2. Verify Tables Created

Check that these tables exist:
- `roles` - Stores role definitions
- `user_profiles` - Stores user profile data (linked to `auth.users`)

### 3. Verify Default Roles

After running the schema, you should have 3 default roles:
- **Admin** - Full system access
- **Manager** - Team management
- **User** - Basic blog creation

## Environment Variables

Set these in your Cloud Run service or `.env` file:

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here
```

### Where to Find These Values

1. **SUPABASE_URL**: 
   - Go to Supabase Dashboard → Settings → API
   - Copy "Project URL"

2. **SUPABASE_ANON_KEY**:
   - Same page → "anon" or "public" key
   - Used for token verification

3. **SUPABASE_SERVICE_ROLE_KEY**:
   - Same page → "service_role" key
   - ⚠️ **Keep this secret!** Only use in backend
   - Used for database operations

## Authentication Flow

### Frontend (Next.js Example)

```javascript
import { createClient } from '@supabase/supabase-js'

// Initialize Supabase client
const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
)

// Sign in user
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'password123'
})

// Get JWT token
const token = data.session.access_token

// Use token in API requests
const response = await fetch('https://api.example.com/api/v1/users', {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
})
```

### Backend Verification

1. Frontend sends JWT token in `Authorization: Bearer <token>` header
2. Backend `AuthService` verifies token with Supabase Auth
3. Backend retrieves user profile from `user_profiles` table
4. Backend checks user role and permissions
5. Request is authorized or rejected

## Creating the First Admin User

### Option 1: Via Supabase Dashboard

1. Go to Supabase Dashboard → Authentication → Users
2. Create a new user manually
3. Note the user's UUID
4. Insert into `user_profiles` table:

```sql
INSERT INTO user_profiles (id, email, name, role_id, status)
VALUES (
  'user-uuid-from-auth',
  'admin@example.com',
  'System Admin',
  (SELECT id FROM roles WHERE name = 'Admin'),
  'active'
);
```

### Option 2: Via API (After First Admin Created)

Use the `POST /api/v1/users` endpoint with an admin token:

```javascript
const response = await fetch('https://api.example.com/api/v1/users', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${adminToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    email: 'newadmin@example.com',
    password: 'SecureP@ss123',
    name: 'New Admin',
    role: 'admin',
    department: 'IT',
    status: 'active'
  })
})
```

## Row Level Security (RLS)

The schema includes RLS policies:

- **Roles**: Viewable by authenticated users, modifiable by service role only
- **User Profiles**: Users can view own profile, modifiable by service role only

These policies ensure:
- Users can only see their own data
- Only backend (service role) can modify data
- Frontend (anon key) has limited access

## Fallback Mode

If Supabase credentials are not configured, the system falls back to in-memory storage:
- Data is not persisted
- Useful for development/testing
- Logs will show: "Supabase credentials not configured"

## Testing

### 1. Test Database Connection

```bash
# Check if tables exist
psql -h db.your-project.supabase.co -U postgres -d postgres -c "\dt"
```

### 2. Test Authentication

```javascript
// Sign in and verify token
const { data } = await supabase.auth.signInWithPassword({
  email: 'test@example.com',
  password: 'password123'
})

console.log('Token:', data.session.access_token)
```

### 3. Test API Endpoints

```bash
# Get user stats (requires admin token)
curl -X GET \
  https://api.example.com/api/v1/users/stats \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Troubleshooting

### "Supabase credentials not configured"
- Check environment variables are set
- Verify `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` are correct

### "401 Unauthorized"
- Token is invalid or expired
- Check token is from Supabase Auth
- Verify `SUPABASE_ANON_KEY` is correct

### "User not found"
- User exists in `auth.users` but not in `user_profiles`
- Create user profile manually or via API

### "Role not found"
- Default roles not created
- Run the SQL schema again

## Next Steps

1. ✅ Run SQL schema in Supabase
2. ✅ Set environment variables in Cloud Run
3. ✅ Create first admin user
4. ✅ Test authentication flow
5. ✅ Connect frontend to API endpoints

