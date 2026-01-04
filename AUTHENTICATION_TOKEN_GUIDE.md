# Authentication Token Guide for Admin Endpoints

## Overview

Admin endpoints require **Supabase JWT Bearer Token** authentication. The token must be from a user with `admin` or `system_admin` role.

---

## Authorization Type

**Type:** `Bearer Token` (JWT)

**Header Format:**
```
Authorization: Bearer <your-jwt-token>
```

---

## How to Get a Token

### Option 1: Sign In via Supabase Auth (Recommended)

This is the standard way to get a token for testing.

#### Step 1: Get Supabase Credentials

You need:
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_ANON_KEY` - Supabase anonymous/public key

**Where to find them:**
1. Go to [Supabase Dashboard](https://app.supabase.com)
2. Select your project
3. Go to **Settings** → **API**
4. Copy:
   - **Project URL** → `SUPABASE_URL`
   - **anon/public key** → `SUPABASE_ANON_KEY`

#### Step 2: Sign In with Supabase Client

**Using JavaScript/Node.js:**
```javascript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  'https://your-project.supabase.co',  // SUPABASE_URL
  'your-anon-key-here'                  // SUPABASE_ANON_KEY
)

// Sign in with email/password
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'admin@example.com',
  password: 'your-password'
})

if (error) {
  console.error('Sign in error:', error)
} else {
  // Get the JWT token
  const token = data.session.access_token
  console.log('Token:', token)
  
  // Use in API requests
  const response = await fetch('https://blog-writer-api-prod-613248238610.us-east1.run.app/api/v1/admin/ai/costs?org_id=default&days=30', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  })
}
```

**Using Python:**
```python
from supabase import create_client, Client

supabase_url = "https://your-project.supabase.co"
supabase_key = "your-anon-key-here"

supabase: Client = create_client(supabase_url, supabase_key)

# Sign in
response = supabase.auth.sign_in_with_password({
    "email": "admin@example.com",
    "password": "your-password"
})

if response.session:
    token = response.session.access_token
    print(f"Token: {token}")
    
    # Use in requests
    import requests
    response = requests.get(
        "https://blog-writer-api-prod-613248238610.us-east1.run.app/api/v1/admin/ai/costs",
        params={"org_id": "default", "days": 30},
        headers={"Authorization": f"Bearer {token}"}
    )
```

**Using cURL (via Supabase REST API):**
```bash
# Sign in and get token
RESPONSE=$(curl -s -X POST \
  "https://your-project.supabase.co/auth/v1/token?grant_type=password" \
  -H "apikey: your-anon-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "your-password"
  }')

# Extract token (requires jq)
TOKEN=$(echo $RESPONSE | jq -r '.access_token')

# Use token
curl "https://blog-writer-api-prod-613248238610.us-east1.run.app/api/v1/admin/ai/costs?org_id=default&days=30" \
  -H "Authorization: Bearer $TOKEN"
```

---

### Option 2: Create Admin User First (If No Admin Exists)

If you don't have an admin user yet, create one:

#### Via Supabase Dashboard:

1. **Create Auth User:**
   - Go to Supabase Dashboard → **Authentication** → **Users**
   - Click **Add User** → **Create New User**
   - Enter email and password
   - Note the User UUID

2. **Create User Profile with Admin Role:**
   - Go to **SQL Editor**
   - Run this SQL (replace with your user UUID and email):

```sql
-- First, get the Admin role ID
SELECT id FROM roles WHERE name = 'Admin';

-- Then insert user profile (replace USER_UUID and email)
INSERT INTO user_profiles (id, email, name, role_id, status)
VALUES (
  'USER_UUID_FROM_AUTH',  -- Replace with UUID from step 1
  'admin@example.com',    -- Replace with your email
  'System Admin',
  (SELECT id FROM roles WHERE name = 'Admin'),
  'active'
);
```

3. **Sign in** using Option 1 above

---

### Option 3: Fallback Mode (Development Only)

**⚠️ Note:** This only works if Supabase is **not configured** on the backend.

If the backend doesn't have Supabase credentials set, it uses a fallback mode that accepts **any token** and returns a placeholder admin user.

**Test with any token:**
```bash
curl "https://blog-writer-api-prod-613248238610.us-east1.run.app/api/v1/admin/ai/costs?org_id=default&days=30" \
  -H "Authorization: Bearer test"
```

**This works because:**
- Backend logs: `"Supabase credentials not configured, using placeholder authentication"`
- Returns: `{"id": "system_admin", "email": "systemadmin@example.com", "role": "system_admin"}`

**⚠️ Warning:** This is for development/testing only. Production should have Supabase configured.

---

## Token Requirements

### For Admin Endpoints:

1. **Token Type:** Supabase JWT Bearer Token
2. **User Role:** Must have `admin` or `system_admin` role in `user_profiles` table
3. **Token Format:** `Bearer <token>` in Authorization header

### Role Check:

The backend checks:
```python
user_role = user.get("role", "").lower()
if user_role not in ["system_admin", "admin"]:
    raise HTTPException(status_code=403, detail="Admin access required")
```

So the role must be:
- `admin` (from roles table where name = 'Admin')
- `system_admin` (from roles table where name = 'System Admin')

---

## Testing Examples

### Example 1: Test Cost Endpoint

```bash
# Set your token
export ADMIN_TOKEN="your-jwt-token-here"

# Test cost endpoint
curl "https://blog-writer-api-prod-613248238610.us-east1.run.app/api/v1/admin/ai/costs?org_id=default&days=30" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### Example 2: Test Admin Status

```bash
curl "https://blog-writer-api-prod-613248238610.us-east1.run.app/api/v1/admin/status" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### Example 3: Test Usage Stats

```bash
curl "https://blog-writer-api-prod-613248238610.us-east1.run.app/api/v1/admin/ai/usage?org_id=default&days=30" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

---

## Troubleshooting

### Error: "Missing or invalid authorization header"

**Problem:** Token not provided or header format incorrect

**Solution:**
```bash
# Wrong
curl ... -H "Authorization: $TOKEN"

# Correct
curl ... -H "Authorization: Bearer $TOKEN"
```

### Error: "Invalid or expired token"

**Problem:** Token is invalid, expired, or not from Supabase

**Solutions:**
1. Get a fresh token by signing in again
2. Check token expiration (Supabase tokens expire after 1 hour by default)
3. Verify `SUPABASE_ANON_KEY` is correct on backend

### Error: "Admin access required"

**Problem:** User doesn't have admin role

**Solutions:**
1. Check user's role in `user_profiles` table:
   ```sql
   SELECT up.email, r.name as role_name
   FROM user_profiles up
   JOIN roles r ON up.role_id = r.id
   WHERE up.email = 'your-email@example.com';
   ```

2. Update user role to Admin:
   ```sql
   UPDATE user_profiles
   SET role_id = (SELECT id FROM roles WHERE name = 'Admin')
   WHERE email = 'your-email@example.com';
   ```

### Error: "Supabase credentials not configured"

**Problem:** Backend doesn't have Supabase configured

**This means:**
- Fallback mode is active
- Any token will work (for testing only)
- You should configure Supabase for production

---

## Quick Test Script

Save this as `get_admin_token.sh`:

```bash
#!/bin/bash

# Configuration
SUPABASE_URL="${SUPABASE_URL:-https://your-project.supabase.co}"
SUPABASE_ANON_KEY="${SUPABASE_ANON_KEY:-your-anon-key}"
EMAIL="${EMAIL:-admin@example.com}"
PASSWORD="${PASSWORD:-your-password}"

# Sign in and get token
echo "Signing in to Supabase..."
RESPONSE=$(curl -s -X POST \
  "${SUPABASE_URL}/auth/v1/token?grant_type=password" \
  -H "apikey: ${SUPABASE_ANON_KEY}" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"${EMAIL}\",
    \"password\": \"${PASSWORD}\"
  }")

# Check for errors
if echo "$RESPONSE" | grep -q "error"; then
  echo "Error signing in:"
  echo "$RESPONSE" | jq '.'
  exit 1
fi

# Extract token
TOKEN=$(echo "$RESPONSE" | jq -r '.access_token')

if [ "$TOKEN" = "null" ] || [ -z "$TOKEN" ]; then
  echo "Failed to get token"
  echo "$RESPONSE" | jq '.'
  exit 1
fi

echo "Token obtained successfully!"
echo ""
echo "Export this token:"
echo "export ADMIN_TOKEN=\"$TOKEN\""
echo ""
echo "Or use directly:"
echo "curl ... -H \"Authorization: Bearer $TOKEN\""
```

Usage:
```bash
chmod +x get_admin_token.sh
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_ANON_KEY="your-anon-key"
export EMAIL="admin@example.com"
export PASSWORD="your-password"
./get_admin_token.sh
```

---

## Summary

1. **Get Supabase credentials** (URL and anon key)
2. **Sign in** using Supabase Auth with admin user credentials
3. **Extract token** from `session.access_token`
4. **Use token** in `Authorization: Bearer <token>` header
5. **Ensure user has admin role** in `user_profiles` table

For production, always use proper Supabase authentication. The fallback mode is only for development/testing when Supabase is not configured.

