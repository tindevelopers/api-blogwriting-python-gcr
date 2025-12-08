# Backend Publishing Guide - Multi-CMS, Target Selection, Role-Scoped Cost Visibility

**Version:** 1.0.0  
**Date:** 2025-01-15  
**Status:** ✅ **IMPLEMENTED**

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Data Model](#data-model)
3. [API Endpoints](#api-endpoints)
4. [Publish Flow](#publish-flow)
5. [Role-Based Access Control](#role-based-access-control)
6. [Cost Visibility](#cost-visibility)
7. [Validation & Scoping](#validation--scoping)
8. [Audit Logging](#audit-logging)
9. [Usage Analytics](#usage-analytics)
10. [Error Handling](#error-handling)
11. [Testing Checklist](#testing-checklist)

---

## 🎯 Overview

This system provides comprehensive multi-CMS publishing capabilities with:

- ✅ **Multiple CMS integrations per organization** (Webflow, Shopify, WordPress)
- ✅ **Target selection** (CMS + site + collection)
- ✅ **Role-based cost visibility** (costs only visible to admins/owners)
- ✅ **Org scoping** (all queries filtered by org_id)
- ✅ **Audit logging** (track all integration and publish changes)
- ✅ **Usage analytics** (cost tracking per org/site)

---

## 🏗 Data Model

### Integrations Table

```sql
CREATE TABLE integrations_{env} (
    id UUID PRIMARY KEY,
    org_id TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('webflow', 'shopify', 'wordpress', 'custom')),
    site_id TEXT NOT NULL,
    site_name TEXT NOT NULL,
    api_key TEXT,
    api_secret TEXT,
    collection_ids JSONB DEFAULT '[]'::jsonb,
    is_default BOOLEAN DEFAULT FALSE,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_verified_at TIMESTAMPTZ,
    error_message TEXT,
    
    UNIQUE(org_id, type, site_id)
);
```

**Indexes:**
- `(org_id, type)` - Fast filtering by provider
- `(org_id, site_id)` - Fast site lookup
- `(org_id, is_default)` - Fast default lookup

### Blog Posts Table (Extended)

```sql
ALTER TABLE blog_posts_{env} ADD COLUMN:
    cms_provider TEXT,
    site_id TEXT,
    collection_id TEXT,
    publishing_target JSONB,
    published_url TEXT,
    remote_id TEXT,
    published_at TIMESTAMPTZ,
    publish_status TEXT,
    publish_error TEXT,
    total_cost DECIMAL(10, 4) DEFAULT 0.0,
    cost_breakdown JSONB,
    org_id TEXT;
```

### Audit Logs Table

```sql
CREATE TABLE audit_logs_{env} (
    id UUID PRIMARY KEY,
    user_id TEXT NOT NULL,
    org_id TEXT NOT NULL,
    action TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);
```

### Usage Logs Table

```sql
CREATE TABLE usage_logs_{env} (
    id UUID PRIMARY KEY,
    org_id TEXT NOT NULL,
    site_id TEXT,
    user_id TEXT,
    resource_type TEXT NOT NULL,
    resource_id TEXT,
    total_cost DECIMAL(10, 4) NOT NULL,
    cost_breakdown JSONB,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 🔌 API Endpoints

### Integration Management

#### List Integrations
```
GET /api/v1/publishing/integrations?provider_type=webflow
```

**Required Role:** `admin`, `owner`, `system_admin`, `super_admin`

**Response:**
```json
[
  {
    "id": "uuid",
    "org_id": "org_123",
    "type": "webflow",
    "site_id": "wf_site_1",
    "site_name": "Marketing Site",
    "collection_ids": ["blog", "news"],
    "is_default": true,
    "status": "active"
  }
]
```

#### Create Integration
```
POST /api/v1/publishing/integrations
```

**Required Role:** `admin`, `owner`, `system_admin`, `super_admin`

**Request:**
```json
{
  "org_id": "org_123",
  "type": "webflow",
  "site_id": "wf_site_1",
  "site_name": "Marketing Site",
  "api_key": "wf_api_key",
  "api_secret": null,
  "collection_ids": ["blog", "news"],
  "is_default": true
}
```

**Response:** Created integration object

**Audit:** Logs `create_integration` action

#### Update Integration
```
PATCH /api/v1/publishing/integrations/{integration_id}
```

**Required Role:** `admin`, `owner`, `system_admin`, `super_admin`

**Request:**
```json
{
  "site_name": "Updated Site Name",
  "is_default": true,
  "status": "active"
}
```

**Response:** Updated integration object

**Audit:** Logs `update_integration` action

**Note:** Setting `is_default=true` automatically unsets other defaults for the same provider.

#### Delete Integration
```
DELETE /api/v1/publishing/integrations/{integration_id}
```

**Required Role:** `admin`, `owner`, `system_admin`, `super_admin`

**Response:**
```json
{
  "success": true,
  "message": "Integration disabled"
}
```

**Audit:** Logs `delete_integration` action

**Note:** Soft delete (sets status to `inactive`)

---

### Publishing Targets

#### Get Publishing Targets
```
GET /api/v1/publishing/targets
```

**Required Role:** Any authenticated user

**Response:**
```json
{
  "providers": ["webflow", "shopify", "wordpress"],
  "sites": [
    {
      "id": "wf_site_1",
      "name": "Marketing Site",
      "provider": "webflow",
      "collections": ["blog", "news"],
      "is_default": true
    },
    {
      "id": "wf_site_2",
      "name": "Product Site",
      "provider": "webflow",
      "collections": ["blog"],
      "is_default": false
    }
  ],
  "default": {
    "cms_provider": "webflow",
    "site_id": "wf_site_1",
    "collection_id": "blog"
  }
}
```

---

### Blog Post Management

#### Update Draft Publishing Target
```
PATCH /api/v1/publishing/drafts/{draft_id}/target
```

**Required Role:** `writer`, `editor`, `admin`, `owner`

**Request:**
```json
{
  "cms_provider": "webflow",
  "site_id": "wf_site_2",
  "collection_id": "blog",
  "site_name": "Product Site"
}
```

**Response:**
```json
{
  "success": true,
  "draft_id": "draft_123",
  "publishing_target": {
    "cms_provider": "webflow",
    "site_id": "wf_site_2",
    "collection_id": "blog"
  },
  "message": "Publishing target updated successfully"
}
```

**Audit:** Logs `update_publishing_target` action

**Validation:**
- Verifies site belongs to org
- Verifies collection exists for Webflow
- Verifies draft belongs to org

#### List Blog Posts
```
GET /api/v1/publishing/blog-posts?status=draft&limit=20&offset=0
```

**Required Role:** Any authenticated user

**Response:** Array of blog posts

**Cost Visibility:** Only admins/owners see `total_cost` and `cost_breakdown`

**Example Response (Admin):**
```json
[
  {
    "id": "post_123",
    "title": "My Blog Post",
    "content": "...",
    "status": "draft",
    "total_cost": 0.005143,
    "cost_breakdown": {
      "ai_generation": 0.003,
      "api_calls": 0.002143
    },
    "publishing_metadata": {
      "cms_provider": "webflow",
      "site_id": "wf_site_1",
      "collection_id": "blog"
    }
  }
]
```

**Example Response (Writer):**
```json
[
  {
    "id": "post_123",
    "title": "My Blog Post",
    "content": "...",
    "status": "draft",
    "total_cost": null,
    "cost_breakdown": null,
    "publishing_metadata": {
      "cms_provider": "webflow",
      "site_id": "wf_site_1",
      "collection_id": "blog"
    }
  }
]
```

#### Get Single Blog Post
```
GET /api/v1/publishing/blog-posts/{post_id}
```

**Required Role:** Any authenticated user

**Response:** Single blog post with role-based cost filtering

---

### Publishing

#### Publish Blog Post
```
POST /api/v1/publishing/publish
```

**Required Role:** `writer`, `editor`, `admin`, `owner`

**Request:**
```json
{
  "blog_id": "post_123",
  "cms_provider": "webflow",
  "site_id": "wf_site_2",
  "collection_id": "blog",
  "publish": true
}
```

**Target Resolution Priority:**
1. Request override (`cms_provider`, `site_id`, `collection_id`)
2. Stored target in blog post
3. Default integration for provider

**Response:**
```json
{
  "success": true,
  "cms_provider": "webflow",
  "site_id": "wf_site_2",
  "collection_id": "blog",
  "published_url": "https://site.com/blog/my-post",
  "remote_id": "wf_item_123"
}
```

**Error Response:**
```json
{
  "success": false,
  "cms_provider": "webflow",
  "site_id": "wf_site_2",
  "collection_id": "blog",
  "error_message": "Collection ID is required for Webflow publishing"
}
```

**Audit:** Logs `publish_blog` action

**Usage Log:** Logs cost if successful and cost available

**Blog Post Update:**
- Updates `cms_provider`, `site_id`, `collection_id`
- Updates `published_url`, `remote_id`
- Updates `published_at`, `publish_status`
- Updates `publishing_target` JSONB

---

## 🚚 Publish Flow

### Step-by-Step Process

1. **Fetch Blog Post**
   - Retrieve from `blog_posts_{env}` table
   - Verify `org_id` matches
   - Build `BlogGenerationResult` from stored data

2. **Resolve Publishing Target**
   - Priority: Request override → Stored target → Default
   - Validate target belongs to org
   - Validate collection exists (for Webflow)

3. **Get Integration**
   - Find integration by `site_id` and `provider`
   - Fallback to default if site_id doesn't match
   - Verify integration is active

4. **Publish to CMS**
   - Route to appropriate CMS client (Webflow/Shopify/WordPress)
   - Handle CMS-specific requirements (e.g., collection_id for Webflow)
   - Return publish response with `published_url` and `remote_id`

5. **Update Blog Post**
   - Store publish metadata
   - Update `publish_status` and `published_at`
   - Store `publishing_target` JSONB

6. **Logging**
   - Audit log: `publish_blog` action
   - Usage log: Cost tracking (if successful)

---

## 🔒 Role-Based Access Control

### Role Definitions

- **`owner`**: Full access, can view costs
- **`admin`**: Full access, can view costs
- **`system_admin`**: Full access, can view costs
- **`super_admin`**: Full access, can view costs
- **`editor`**: Can publish, cannot manage integrations, cannot view costs
- **`writer`**: Can publish, cannot manage integrations, cannot view costs

### Integration Management

**Create/Update/Delete Integrations:**
- Required: `admin`, `owner`, `system_admin`, `super_admin`
- Writers/Editors: ❌ Cannot create/update/delete

**Set Default Integration:**
- Required: `admin`, `owner`, `system_admin`, `super_admin`
- Writers/Editors: ❌ Cannot set defaults

### Publishing

**Publish Blog Posts:**
- Allowed: `writer`, `editor`, `admin`, `owner`
- Writers/Editors: ✅ Can publish

**Select Publishing Targets:**
- Allowed: `writer`, `editor`, `admin`, `owner`
- Writers/Editors: ✅ Can select targets on drafts

---

## 💰 Cost Visibility

### Role-Based Filtering

Costs (`total_cost`, `cost_breakdown`) are only included in responses for:
- `admin`
- `owner`
- `system_admin`
- `super_admin`

### Implementation

```python
# In BlogPostWithCosts.from_blog_post()
can_view_costs = user_role in [
    UserRole.admin,
    UserRole.owner,
    UserRole.system_admin,
    UserRole.super_admin
]

if can_view_costs:
    total_cost = blog_post.get("total_cost")
    cost_breakdown = blog_post.get("cost_breakdown")
else:
    total_cost = None
    cost_breakdown = None
```

### Usage Logging

All costs are logged to `usage_logs_{env}` table with:
- `org_id`
- `site_id`
- `user_id`
- `resource_type` (e.g., "blog_generation", "blog_publishing")
- `resource_id`
- `total_cost`
- `cost_breakdown`

**Analytics Query Example:**
```sql
SELECT 
    org_id,
    site_id,
    SUM(total_cost) as total_cost,
    COUNT(*) as usage_count
FROM usage_logs_dev
WHERE org_id = 'org_123'
GROUP BY org_id, site_id;
```

---

## ✅ Validation & Scoping

### Org Scoping

All queries are filtered by `org_id`:
- Integrations: `WHERE org_id = ?`
- Blog posts: `WHERE org_id = ?`
- Audit logs: `WHERE org_id = ?`
- Usage logs: `WHERE org_id = ?`

### Site Validation

When selecting a publishing target:
1. Verify `site_id` exists in integrations for the org
2. Verify `site_id` matches the `cms_provider`
3. Verify integration is `active`

### Collection Validation

For Webflow:
1. Verify `collection_id` is provided
2. Verify `collection_id` exists in integration's `collection_ids` array

### Error Messages

- `"Site {site_id} not found for this organization"`
- `"Collection {collection_id} not found for site {site_id}"`
- `"Collection ID is required for Webflow publishing"`
- `"No publishing target selected and no default configured for {provider}"`
- `"Integration disabled or missing credentials"`

---

## 📜 Audit Logging

### Integration Changes

All integration operations are logged:

**Create Integration:**
```json
{
  "action": "create_integration",
  "resource_type": "integration",
  "resource_id": "int_123",
  "metadata": {
    "type": "webflow",
    "site_id": "wf_site_1",
    "is_default": true
  }
}
```

**Update Integration:**
```json
{
  "action": "update_integration",
  "resource_type": "integration",
  "resource_id": "int_123",
  "metadata": {
    "updates": {"site_name": "New Name"},
    "is_default_changed": true
  }
}
```

**Delete Integration:**
```json
{
  "action": "delete_integration",
  "resource_type": "integration",
  "resource_id": "int_123",
  "metadata": {
    "site_id": "wf_site_1",
    "type": "webflow"
  }
}
```

### Publish Attempts

All publish operations are logged:

```json
{
  "action": "publish_blog",
  "resource_type": "blog_post",
  "resource_id": "post_123",
  "metadata": {
    "cms_provider": "webflow",
    "site_id": "wf_site_1",
    "success": true,
    "published_url": "https://site.com/blog/my-post"
  }
}
```

### Target Updates

```json
{
  "action": "update_publishing_target",
  "resource_type": "blog_post",
  "resource_id": "post_123",
  "metadata": {
    "cms_provider": "webflow",
    "site_id": "wf_site_2",
    "collection_id": "blog"
  }
}
```

---

## ⚡ Caching

### Integration Cache

Integrations are cached per org with 5-minute TTL:

```python
cache_key = f"{org_id}:{provider_type or 'all'}"
```

**Cache Invalidation:**
- On create/update/delete integration
- On set default integration
- Manual clear via `service.clear_cache(org_id)`

---

## 🚨 Error States

### Common Errors

1. **No Publishing Target**
   ```
   "No publishing target selected and no default configured for webflow"
   ```

2. **Site Not Found**
   ```
   "Site wf_site_2 not found for this organization"
   ```

3. **Collection Not Found**
   ```
   "Collection news not found for site wf_site_1"
   ```

4. **Collection Required**
   ```
   "Collection ID is required for Webflow publishing"
   ```

5. **Integration Disabled**
   ```
   "No active integration found for webflow and site wf_site_1"
   ```

6. **Org Mismatch**
   ```
   "Blog post does not belong to this organization"
   ```

---

## 🧪 Testing Checklist

### Integration Management

- [ ] Create two Webflow integrations for same org
- [ ] Set one as default
- [ ] Update integration (change site_name, set default)
- [ ] Verify setting default unsets other defaults
- [ ] Delete integration (verify soft delete)
- [ ] Verify role checks (writer cannot create)

### Publishing Targets

- [ ] Get publishing targets (verify all sites listed)
- [ ] Verify default target returned
- [ ] Filter by provider type

### Draft Target Selection

- [ ] Update draft with explicit target
- [ ] Verify target stored in blog post
- [ ] Verify validation (site belongs to org)
- [ ] Verify validation (collection exists for Webflow)
- [ ] Verify role checks (writer can update)

### Publishing

- [ ] Publish with explicit target → routes to chosen site/collection
- [ ] Publish with stored target → uses stored target
- [ ] Publish with no target → uses default
- [ ] Publish with no target and no default → error
- [ ] Verify blog post updated with publish status
- [ ] Verify audit log created
- [ ] Verify usage log created (if cost available)

### Cost Visibility

- [ ] Admin views blog post → sees costs
- [ ] Writer views blog post → costs are null
- [ ] Verify costs filtered in list endpoint

### Multi-Org

- [ ] User with two orgs only sees integrations of active org
- [ ] User cannot access blog posts from other org
- [ ] User cannot publish to sites from other org

### Error Handling

- [ ] Invalid site_id → error
- [ ] Invalid collection_id → error
- [ ] Missing collection_id for Webflow → error
- [ ] Disabled integration → error
- [ ] Missing credentials → error

---

## 📊 Response Examples

### Publishing Targets Response

```json
{
  "providers": ["webflow", "shopify"],
  "sites": [
    {
      "id": "wf_site_1",
      "name": "Marketing Site",
      "provider": "webflow",
      "collections": ["blog", "news"],
      "is_default": true
    }
  ],
  "default": {
    "cms_provider": "webflow",
    "site_id": "wf_site_1",
    "collection_id": "blog"
  }
}
```

### Publish Request Override

```json
{
  "blog_id": "post_123",
  "cms_provider": "webflow",
  "site_id": "wf_site_2",
  "collection_id": "blog",
  "publish": true
}
```

---

## 🔗 Related Documentation

- `migrations/001_add_multi_cms_publishing.sql` - Database schema
- `src/blog_writer_sdk/models/publishing_models.py` - Data models
- `src/blog_writer_sdk/services/publishing_service.py` - Service layer
- `src/blog_writer_sdk/api/publishing_management.py` - API endpoints

---

## ✅ Implementation Status

- ✅ Data model (integrations, blog_posts extensions, audit_logs, usage_logs)
- ✅ Integration management endpoints (CRUD)
- ✅ Publishing targets endpoint
- ✅ Draft target selection endpoint
- ✅ Publish endpoint with target resolution
- ✅ Role-based access control
- ✅ Role-based cost filtering
- ✅ Audit logging
- ✅ Usage logging
- ✅ Validation & scoping
- ✅ Caching
- ✅ Error handling

**All features from the requirements document have been implemented!**
