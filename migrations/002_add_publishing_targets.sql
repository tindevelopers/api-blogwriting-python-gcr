-- Migration: Add publishing_targets tables for multi-property publishing
-- Date: 2025-12-14
-- Description: Introduces publishing_targets tables (dev/staging/prod) to store multiple publishing targets per organization.

-- ============================================================================
-- 1. publishing_targets tables (environment-specific)
-- ============================================================================
CREATE TABLE IF NOT EXISTS publishing_targets_dev (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    org_id TEXT NOT NULL,
    name TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('webflow', 'shopify', 'wordpress', 'medium', 'custom')),
    site_url TEXT,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'archived')),
    is_default BOOLEAN DEFAULT FALSE,
    config JSONB DEFAULT '{}'::jsonb,
    credentials JSONB DEFAULT '{}'::jsonb,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,

    CONSTRAINT uq_publishing_targets_org_name UNIQUE (org_id, name)
);

CREATE INDEX IF NOT EXISTS idx_publishing_targets_org_id ON publishing_targets_dev (org_id);
CREATE INDEX IF NOT EXISTS idx_publishing_targets_status ON publishing_targets_dev (status);
CREATE INDEX IF NOT EXISTS idx_publishing_targets_org_status ON publishing_targets_dev (org_id, status);
CREATE INDEX IF NOT EXISTS idx_publishing_targets_is_default ON publishing_targets_dev (org_id, is_default) WHERE is_default = TRUE;

-- Staging and prod tables mirror dev definition
CREATE TABLE IF NOT EXISTS publishing_targets_staging (
    LIKE publishing_targets_dev INCLUDING ALL
);

CREATE TABLE IF NOT EXISTS publishing_targets_prod (
    LIKE publishing_targets_dev INCLUDING ALL
);

-- ============================================================================
-- Notes:
-- - credentials/config are JSONB to allow provider-specific settings
-- - Keep is_default optional; application logic should enforce one default per org/type if needed
-- ============================================================================



