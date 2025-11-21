# Authentication Setup for Next.js Frontend Integration

## Current Status: ⚠️ No Authentication Implemented

Your API currently has **NO authentication** which is a security risk for production use.

## Recommended Solutions

### Option 1: API Key Authentication (Simple)
```python
# Add to main.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    expected_api_key = os.getenv("API_KEY")
    if not expected_api_key or credentials.credentials != expected_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    return credentials.credentials

# Apply to protected endpoints
@app.post("/api/v1/blog/generate")
async def generate_blog(
    request: BlogGenerationRequest,
    api_key: str = Depends(verify_api_key),
    # ... other dependencies
):
    # ... endpoint logic
```

### Option 2: JWT Token Authentication (Recommended)
```python
# Add JWT authentication
from jose import JWTError, jwt
from passlib.context import CryptContext

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"

async def verify_jwt_token(token: str = Depends(security)):
    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### Option 3: Supabase Auth Integration
Since you have Supabase configured, use Supabase Auth:
```python
# Add Supabase Auth verification
from supabase import create_client

async def verify_supabase_token(token: str = Depends(security)):
    supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    try:
        user = supabase.auth.get_user(token.credentials)
        return user
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid Supabase token")
```

## Environment Variables Needed
```bash
# Add to your .env file
API_KEY=your-secure-api-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
```

## Next.js Frontend Integration
```javascript
// In your Next.js app
const apiKey = process.env.NEXT_PUBLIC_API_KEY;

// For API key auth
const response = await fetch('/api/blog/generate', {
  headers: {
    'Authorization': `Bearer ${apiKey}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(data)
});

// For JWT auth
const token = localStorage.getItem('authToken');
const response = await fetch('/api/blog/generate', {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(data)
});
```

