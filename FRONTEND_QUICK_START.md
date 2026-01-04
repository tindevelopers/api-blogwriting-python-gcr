# Frontend Quick Start Guide

**Quick reference for integrating with the Blog Writer Admin API**

---

## 🚀 3-Step Setup

### 1. Install & Configure

```bash
npm install @supabase/supabase-js
```

```env
# .env.local
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
NEXT_PUBLIC_API_URL_PROD=https://blog-writer-api-prod-613248238610.us-east1.run.app
```

### 2. Sign In & Get Token

```typescript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)

// Sign in
const { data } = await supabase.auth.signInWithPassword({
  email: 'admin@example.com',
  password: 'your-password'
})

const token = data.session.access_token
```

### 3. Make API Call

```typescript
const response = await fetch(
  'https://blog-writer-api-prod-613248238610.us-east1.run.app/api/v1/admin/ai/costs?org_id=default&days=30',
  {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  }
)

const costs = await response.json()
console.log('Total cost:', costs.total_cost)
```

---

## 📍 API Endpoints

### AI Cost Tracking

```typescript
GET /api/v1/admin/ai/costs?org_id={orgId}&days={days}
// Returns: { org_id, days, total_cost, by_source, by_client }
```

### AI Usage Stats

```typescript
GET /api/v1/admin/ai/usage?org_id={orgId}&days={days}
// Returns: Usage statistics by operation, model, and time
```

### Admin Status

```typescript
GET /api/v1/admin/status
// Returns: System status and service health
```

### Job Management

```typescript
GET /api/v1/admin/jobs?status={status}&limit={limit}
GET /api/v1/admin/jobs/{jobId}
POST /api/v1/admin/jobs/{jobId}/cancel
POST /api/v1/admin/jobs/{jobId}/retry
```

---

## 🔑 Authentication

**Header Format:**
```
Authorization: Bearer <supabase-jwt-token>
```

**Requirements:**
- User must be signed in via Supabase Auth
- User must have `admin` or `system_admin` role in `user_profiles` table

---

## 🌍 Environment URLs

- **Production**: `https://blog-writer-api-prod-613248238610.us-east1.run.app`
- **Staging**: `https://blog-writer-api-staging-613248238610.europe-west9.run.app`
- **Development**: `https://blog-writer-api-dev-613248238610.europe-west9.run.app`

---

## ✅ What's Enabled

- ✅ Firestore usage logging enabled on all environments
- ✅ AI cost tracking available
- ✅ Usage statistics available
- ✅ Cache statistics available
- ✅ Job management available

---

## 📚 Full Documentation

See [FRONTEND_ADMIN_API_GUIDE.md](./FRONTEND_ADMIN_API_GUIDE.md) for:
- Complete TypeScript types
- React components examples
- Error handling
- Authentication context setup
- Full API reference

---

## 🆘 Troubleshooting

**"Not authenticated"**
→ Sign in via Supabase Auth first

**"Admin access required"**
→ User needs admin role in database

**"Usage logging not enabled"**
→ Should be enabled now, but check backend logs if persists

**401/403 Errors**
→ Check token is valid and user has admin role

---

**Need help?** Check the full guide: `FRONTEND_ADMIN_API_GUIDE.md`

