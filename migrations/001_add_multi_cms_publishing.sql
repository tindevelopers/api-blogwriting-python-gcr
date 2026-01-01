-- Migration: Add Multi-CMS Publishing Support
-- Date: 2025-01-15
-- Description: Adds tables and columns for multi-CMS integrations, publishing targets, and cost tracking

-- ============================================================================
-- 1. Integrations Table (multi per org)
-- ============================================================================
CREATE TABLE IF NOT EXISTS integrations_dev (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    org_id TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('webflow', 'shopify', 'wordpress', 'custom')),
    site_id TEXT NOT NULL,
    site_name TEXT NOT NULL,
    api_key TEXT,  -- TODO: Encrypt in production
    api_secret TEXT,  -- TODO: Encrypt in production
    collection_ids JSONB DEFAULT '[]'::jsonb,
    is_default BOOLEAN DEFAULT FALSE,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'error')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_verified_at TIMESTAMPTZ,
    error_message TEXT,
    
    -- Constraints
    UNIQUE(org_id, type, site_id),
    
    -- Indexes
    CONSTRAINT idx_integrations_org_type UNIQUE(org_id, type, is_default) WHERE is_default = TRUE
);

CREATE INDEX IF NOT EXISTS idx_integrations_org_id ON integrations_dev(org_id);
CREATE INDEX IF NOT EXISTS idx_integrations_type ON integrations_dev(type);
CREATE INDEX IF NOT EXISTS idx_integrations_org_type ON integrations_dev(org_id, type);
CREATE INDEX IF NOT EXISTS idx_integrations_site_id ON integrations_dev(org_id, site_id);
CREATE INDEX IF NOT EXISTS idx_integrations_is_default ON integrations_dev(org_id, is_default) WHERE is_default = TRUE;
CREATE INDEX IF NOT EXISTS idx_integrations_status ON integrations_dev(status) WHERE status = 'active';

-- Create same tables for staging and prod
CREATE TABLE IF NOT EXISTS integrations_staging (
    LIKE integrations_dev INCLUDING ALL
);

CREATE TABLE IF NOT EXISTS integrations_prod (
    LIKE integrations_dev INCLUDING ALL
);

-- ============================================================================
-- 2. Add Publishing Metadata to Blog Posts
-- ============================================================================
-- Add columns to existing blog_posts tables
DO $$
BEGIN
    -- Dev environment
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'blog_posts_dev' AND column_name = 'cms_provider'
    ) THEN
        ALTER TABLE blog_posts_dev ADD COLUMN cms_provider TEXT CHECK (cms_provider IN ('webflow', 'shopify', 'wordpress', 'custom'));
        ALTER TABLE blog_posts_dev ADD COLUMN site_id TEXT;
        ALTER TABLE blog_posts_dev ADD COLUMN collection_id TEXT;
        ALTER TABLE blog_posts_dev ADD COLUMN publishing_target JSONB;
        ALTER TABLE blog_posts_dev ADD COLUMN published_url TEXT;
        ALTER TABLE blog_posts_dev ADD COLUMN remote_id TEXT;
        ALTER TABLE blog_posts_dev ADD COLUMN published_at TIMESTAMPTZ;
        ALTER TABLE blog_posts_dev ADD COLUMN publish_status TEXT;
        ALTER TABLE blog_posts_dev ADD COLUMN publish_error TEXT;
        ALTER TABLE blog_posts_dev ADD COLUMN total_cost DECIMAL(10, 4) DEFAULT 0.0;
        ALTER TABLE blog_posts_dev ADD COLUMN cost_breakdown JSONB;
        ALTER TABLE blog_posts_dev ADD COLUMN org_id TEXT;
        
        CREATE INDEX IF NOT EXISTS idx_blog_posts_org_id ON blog_posts_dev(org_id);
        CREATE INDEX IF NOT EXISTS idx_blog_posts_cms_provider ON blog_posts_dev(cms_provider);
        CREATE INDEX IF NOT EXISTS idx_blog_posts_site_id ON blog_posts_dev(org_id, site_id);
        CREATE INDEX IF NOT EXISTS idx_blog_posts_publish_status ON blog_posts_dev(publish_status);
    END IF;
    
    -- Staging environment
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'blog_posts_staging' AND column_name = 'cms_provider'
    ) THEN
        ALTER TABLE blog_posts_staging ADD COLUMN cms_provider TEXT CHECK (cms_provider IN ('webflow', 'shopify', 'wordpress', 'custom'));
        ALTER TABLE blog_posts_staging ADD COLUMN site_id TEXT;
        ALTER TABLE blog_posts_staging ADD COLUMN collection_id TEXT;
        ALTER TABLE blog_posts_staging ADD COLUMN publishing_target JSONB;
        ALTER TABLE blog_posts_staging ADD COLUMN published_url TEXT;
        ALTER TABLE blog_posts_staging ADD COLUMN remote_id TEXT;
        ALTER TABLE blog_posts_staging ADD COLUMN published_at TIMESTAMPTZ;
        ALTER TABLE blog_posts_staging ADD COLUMN publish_status TEXT;
        ALTER TABLE blog_posts_staging ADD COLUMN publish_error TEXT;
        ALTER TABLE blog_posts_staging ADD COLUMN total_cost DECIMAL(10, 4) DEFAULT 0.0;
        ALTER TABLE blog_posts_staging ADD COLUMN cost_breakdown JSONB;
        ALTER TABLE blog_posts_staging ADD COLUMN org_id TEXT;
        
        CREATE INDEX IF NOT EXISTS idx_blog_posts_org_id_staging ON blog_posts_staging(org_id);
        CREATE INDEX IF NOT EXISTS idx_blog_posts_cms_provider_staging ON blog_posts_staging(cms_provider);
        CREATE INDEX IF NOT EXISTS idx_blog_posts_site_id_staging ON blog_posts_staging(org_id, site_id);
        CREATE INDEX IF NOT EXISTS idx_blog_posts_publish_status_staging ON blog_posts_staging(publish_status);
    END IF;
    
    -- Prod environment
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'blog_posts_prod' AND column_name = 'cms_provider'
    ) THEN
        ALTER TABLE blog_posts_prod ADD COLUMN cms_provider TEXT CHECK (cms_provider IN ('webflow', 'shopify', 'wordpress', 'custom'));
        ALTER TABLE blog_posts_prod ADD COLUMN site_id TEXT;
        ALTER TABLE blog_posts_prod ADD COLUMN collection_id TEXT;
        ALTER TABLE blog_posts_prod ADD COLUMN publishing_target JSONB;
        ALTER TABLE blog_posts_prod ADD COLUMN published_url TEXT;
        ALTER TABLE blog_posts_prod ADD COLUMN remote_id TEXT;
        ALTER TABLE blog_posts_prod ADD COLUMN published_at TIMESTAMPTZ;
        ALTER TABLE blog_posts_prod ADD COLUMN publish_status TEXT;
        ALTER TABLE blog_posts_prod ADD COLUMN publish_error TEXT;
        ALTER TABLE blog_posts_prod ADD COLUMN total_cost DECIMAL(10, 4) DEFAULT 0.0;
        ALTER TABLE blog_posts_prod ADD COLUMN cost_breakdown JSONB;
        ALTER TABLE blog_posts_prod ADD COLUMN org_id TEXT;
        
        CREATE INDEX IF NOT EXISTS idx_blog_posts_org_id_prod ON blog_posts_prod(org_id);
        CREATE INDEX IF NOT EXISTS idx_blog_posts_cms_provider_prod ON blog_posts_prod(cms_provider);
        CREATE INDEX IF NOT EXISTS idx_blog_posts_site_id_prod ON blog_posts_prod(org_id, site_id);
        CREATE INDEX IF NOT EXISTS idx_blog_posts_publish_status_prod ON blog_posts_prod(publish_status);
    END IF;
END $$;

-- ============================================================================
-- 3. Add Publishing Metadata to Blog Generation Queue
-- ============================================================================
DO $$
BEGIN
    -- Check if blog_generation_queue table exists, if not create it
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'blog_generation_queue_dev') THEN
        CREATE TABLE blog_generation_queue_dev (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            job_id UUID NOT NULL UNIQUE,
            org_id TEXT NOT NULL,
            user_id TEXT,
            topic TEXT NOT NULL,
            keywords TEXT[],
            status TEXT DEFAULT 'pending',
            result JSONB,
            error_message TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            
            -- Publishing metadata
            cms_provider TEXT CHECK (cms_provider IN ('webflow', 'shopify', 'wordpress', 'custom')),
            site_id TEXT,
            collection_id TEXT,
            publishing_target JSONB,
            total_cost DECIMAL(10, 4) DEFAULT 0.0,
            cost_breakdown JSONB
        );
        
        CREATE INDEX IF NOT EXISTS idx_blog_queue_org_id ON blog_generation_queue_dev(org_id);
        CREATE INDEX IF NOT EXISTS idx_blog_queue_job_id ON blog_generation_queue_dev(job_id);
        CREATE INDEX IF NOT EXISTS idx_blog_queue_status ON blog_generation_queue_dev(status);
    ELSE
        -- Add columns if table exists
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'blog_generation_queue_dev' AND column_name = 'cms_provider'
        ) THEN
            ALTER TABLE blog_generation_queue_dev ADD COLUMN cms_provider TEXT CHECK (cms_provider IN ('webflow', 'shopify', 'wordpress', 'custom'));
            ALTER TABLE blog_generation_queue_dev ADD COLUMN site_id TEXT;
            ALTER TABLE blog_generation_queue_dev ADD COLUMN collection_id TEXT;
            ALTER TABLE blog_generation_queue_dev ADD COLUMN publishing_target JSONB;
            ALTER TABLE blog_generation_queue_dev ADD COLUMN total_cost DECIMAL(10, 4) DEFAULT 0.0;
            ALTER TABLE blog_generation_queue_dev ADD COLUMN cost_breakdown JSONB;
        END IF;
    END IF;
END $$;

-- ============================================================================
-- 4. Audit Log Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS audit_logs_dev (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id TEXT NOT NULL,
    org_id TEXT NOT NULL,
    action TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs_dev(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_org_id ON audit_logs_dev(org_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs_dev(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON audit_logs_dev(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs_dev(timestamp DESC);

-- Create same tables for staging and prod
CREATE TABLE IF NOT EXISTS audit_logs_staging (
    LIKE audit_logs_dev INCLUDING ALL
);

CREATE TABLE IF NOT EXISTS audit_logs_prod (
    LIKE audit_logs_dev INCLUDING ALL
);

-- ============================================================================
-- 5. User Organizations Table (if multi-org support needed)
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_organizations_dev (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id TEXT NOT NULL,
    org_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('owner', 'admin', 'editor', 'writer', 'system_admin', 'super_admin')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(user_id, org_id)
);

CREATE INDEX IF NOT EXISTS idx_user_orgs_user_id ON user_organizations_dev(user_id);
CREATE INDEX IF NOT EXISTS idx_user_orgs_org_id ON user_organizations_dev(org_id);
CREATE INDEX IF NOT EXISTS idx_user_orgs_role ON user_organizations_dev(org_id, role);

-- Create same tables for staging and prod
CREATE TABLE IF NOT EXISTS user_organizations_staging (
    LIKE user_organizations_dev INCLUDING ALL
);

CREATE TABLE IF NOT EXISTS user_organizations_prod (
    LIKE user_organizations_dev INCLUDING ALL
);

-- ============================================================================
-- 6. Usage Logs Table (for cost analytics)
-- ============================================================================
CREATE TABLE IF NOT EXISTS usage_logs_dev (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    org_id TEXT NOT NULL,
    site_id TEXT,
    user_id TEXT,
    resource_type TEXT NOT NULL,  -- 'blog_generation', 'image_generation', etc.
    resource_id TEXT,
    total_cost DECIMAL(10, 4) NOT NULL,
    cost_breakdown JSONB,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_usage_logs_org_id ON usage_logs_dev(org_id);
CREATE INDEX IF NOT EXISTS idx_usage_logs_site_id ON usage_logs_dev(org_id, site_id);
CREATE INDEX IF NOT EXISTS idx_usage_logs_created_at ON usage_logs_dev(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_usage_logs_resource ON usage_logs_dev(resource_type, resource_id);

-- Create same tables for staging and prod
CREATE TABLE IF NOT EXISTS usage_logs_staging (
    LIKE usage_logs_dev INCLUDING ALL
);

CREATE TABLE IF NOT EXISTS usage_logs_prod (
    LIKE usage_logs_dev INCLUDING ALL
);

-- ============================================================================
-- Migration Complete
-- ============================================================================
-- Notes:
-- 1. API keys and secrets should be encrypted in production
-- 2. Consider adding RLS (Row Level Security) policies for multi-tenant isolation
-- 3. Add triggers to update updated_at timestamps automatically
-- 4. Consider adding foreign key constraints if relationships are needed

