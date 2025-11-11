# Frontend-Specific API Enhancements for Next.js

## Missing Endpoints for Frontend Integration

### 1. User Management Endpoints
```python
# Add to main.py
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    created_at: datetime
    subscription_tier: str = "free"

@app.post("/api/v1/auth/register", response_model=UserResponse)
async def register_user(user_data: UserCreate):
    """Register a new user."""
    # Implementation with Supabase Auth
    pass

@app.post("/api/v1/auth/login")
async def login_user(email: EmailStr, password: str):
    """Login user and return JWT token."""
    # Implementation with Supabase Auth
    pass

@app.get("/api/v1/user/profile", response_model=UserResponse)
async def get_user_profile(user_id: str = Depends(get_current_user)):
    """Get current user profile."""
    pass
```

### 2. Content Management Endpoints
```python
class BlogPostCreate(BaseModel):
    title: str
    topic: str
    keywords: List[str] = []
    tone: ContentTone = ContentTone.PROFESSIONAL
    length: ContentLength = ContentLength.MEDIUM

class BlogPostResponse(BaseModel):
    id: str
    title: str
    content: str
    status: str  # draft, published, archived
    created_at: datetime
    updated_at: datetime
    user_id: str
    seo_score: Optional[float] = None

@app.post("/api/v1/posts", response_model=BlogPostResponse)
async def create_blog_post(
    post_data: BlogPostCreate,
    user_id: str = Depends(get_current_user)
):
    """Create a new blog post."""
    pass

@app.get("/api/v1/posts", response_model=List[BlogPostResponse])
async def list_user_posts(
    user_id: str = Depends(get_current_user),
    page: int = 1,
    limit: int = 10
):
    """List user's blog posts with pagination."""
    pass

@app.get("/api/v1/posts/{post_id}", response_model=BlogPostResponse)
async def get_blog_post(
    post_id: str,
    user_id: str = Depends(get_current_user)
):
    """Get a specific blog post."""
    pass

@app.put("/api/v1/posts/{post_id}", response_model=BlogPostResponse)
async def update_blog_post(
    post_id: str,
    post_data: BlogPostCreate,
    user_id: str = Depends(get_current_user)
):
    """Update a blog post."""
    pass

@app.delete("/api/v1/posts/{post_id}")
async def delete_blog_post(
    post_id: str,
    user_id: str = Depends(get_current_user)
):
    """Delete a blog post."""
    pass
```

### 3. Subscription & Usage Tracking
```python
class UsageStats(BaseModel):
    posts_generated: int
    words_generated: int
    images_generated: int
    api_calls_made: int
    subscription_tier: str
    monthly_limit: int
    remaining_credits: int

@app.get("/api/v1/user/usage", response_model=UsageStats)
async def get_user_usage(user_id: str = Depends(get_current_user)):
    """Get user's usage statistics."""
    pass

@app.get("/api/v1/user/subscription")
async def get_subscription_info(user_id: str = Depends(get_current_user)):
    """Get user's subscription information."""
    pass
```

### 4. File Upload Endpoints
```python
from fastapi import File, UploadFile

@app.post("/api/v1/upload/image")
async def upload_image(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user)
):
    """Upload an image file."""
    # Implementation with Supabase Storage
    pass

@app.post("/api/v1/upload/bulk")
async def bulk_upload(
    files: List[UploadFile] = File(...),
    user_id: str = Depends(get_current_user)
):
    """Upload multiple files."""
    pass
```

## Next.js Frontend Integration Examples

### 1. Content Generation Hook
```javascript
// hooks/useBlogGeneration.js
import { useState } from 'react';

export const useBlogGeneration = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const generateBlog = async (data) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/v1/blog/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(data)
      });

      if (!response.ok) {
        throw new Error('Failed to generate blog');
      }

      const result = await response.json();
      return result;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return { generateBlog, loading, error };
};
```

### 2. Content Management Hook
```javascript
// hooks/useBlogPosts.js
export const useBlogPosts = () => {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchPosts = async (page = 1, limit = 10) => {
    setLoading(true);
    try {
      const response = await fetch(`/api/v1/posts?page=${page}&limit=${limit}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      const data = await response.json();
      setPosts(data);
    } catch (error) {
      console.error('Failed to fetch posts:', error);
    } finally {
      setLoading(false);
    }
  };

  const createPost = async (postData) => {
    const response = await fetch('/api/v1/posts', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify(postData)
    });
    
    if (response.ok) {
      fetchPosts(); // Refresh the list
    }
    
    return response.json();
  };

  return { posts, loading, fetchPosts, createPost };
};
```

### 3. Error Handling Component
```javascript
// components/ErrorBoundary.jsx
import React from 'react';

export const ApiErrorHandler = ({ error, onRetry }) => {
  if (!error) return null;

  const getErrorMessage = (error) => {
    if (error.status === 429) {
      return 'Rate limit exceeded. Please wait a moment and try again.';
    }
    if (error.status === 401) {
      return 'Authentication required. Please log in.';
    }
    if (error.status === 403) {
      return 'You do not have permission to perform this action.';
    }
    return error.message || 'An unexpected error occurred.';
  };

  return (
    <div className="error-container">
      <p>{getErrorMessage(error)}</p>
      {onRetry && (
        <button onClick={onRetry}>Try Again</button>
      )}
    </div>
  );
};
```

