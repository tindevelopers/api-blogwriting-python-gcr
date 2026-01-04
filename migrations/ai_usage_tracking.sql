-- AI Usage Tracking Migration
-- Tracks all AI API usage for cost monitoring, analytics, and optimization
-- 
-- Run this migration in Supabase Dashboard SQL Editor or via CLI
-- Creates tables for dev, staging, and prod environments

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- AI Usage Logs Tables (per environment)
-- ============================================================================

-- Function to create ai_usage_logs table for an environment
DO $$
DECLARE
    env TEXT;
    envs TEXT[] := ARRAY['dev', 'staging', 'prod'];
BEGIN
    FOREACH env IN ARRAY envs
    LOOP
        -- Create the ai_usage_logs table
        EXECUTE format('
            CREATE TABLE IF NOT EXISTS ai_usage_logs_%s (
                log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                org_id UUID,
                user_id UUID,
                operation TEXT NOT NULL,
                model TEXT NOT NULL,
                prompt_tokens INTEGER DEFAULT 0,
                completion_tokens INTEGER DEFAULT 0,
                total_tokens INTEGER DEFAULT 0,
                cost_usd DECIMAL(10, 6) DEFAULT 0,
                latency_ms INTEGER DEFAULT 0,
                cached BOOLEAN DEFAULT false,
                -- Usage attribution (for dashboard filtering)
                usage_source TEXT DEFAULT ''unknown'',
                usage_client TEXT DEFAULT ''unknown'',
                request_id TEXT DEFAULT ''unknown'',
                metadata JSONB DEFAULT ''{}''::jsonb,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                
                -- Constraints
                CONSTRAINT ai_usage_logs_%s_operation_check CHECK (
                    operation IN (
                        ''content_generation'',
                        ''content_polishing'',
                        ''quality_check'',
                        ''meta_tag_generation'',
                        ''keyword_analysis'',
                        ''topic_suggestion'',
                        ''other''
                    )
                )
            );
        ', env, env);
        
        -- Create indexes for performance
        EXECUTE format('
            CREATE INDEX IF NOT EXISTS idx_ai_usage_%s_org_date 
            ON ai_usage_logs_%s(org_id, created_at DESC);
        ', env, env);
        
        EXECUTE format('
            CREATE INDEX IF NOT EXISTS idx_ai_usage_%s_user 
            ON ai_usage_logs_%s(user_id, created_at DESC);
        ', env, env);
        
        EXECUTE format('
            CREATE INDEX IF NOT EXISTS idx_ai_usage_%s_operation 
            ON ai_usage_logs_%s(operation);
        ', env, env);
        
        EXECUTE format('
            CREATE INDEX IF NOT EXISTS idx_ai_usage_%s_model 
            ON ai_usage_logs_%s(model);
        ', env, env);
        
        EXECUTE format('
            CREATE INDEX IF NOT EXISTS idx_ai_usage_%s_cached 
            ON ai_usage_logs_%s(cached) WHERE cached = true;
        ', env, env);

        EXECUTE format('
            CREATE INDEX IF NOT EXISTS idx_ai_usage_%s_usage_source
            ON ai_usage_logs_%s(usage_source);
        ', env, env);

        EXECUTE format('
            CREATE INDEX IF NOT EXISTS idx_ai_usage_%s_usage_client
            ON ai_usage_logs_%s(usage_client);
        ', env, env);
        
        RAISE NOTICE 'Created ai_usage_logs_% table and indexes', env;
    END LOOP;
END $$;

-- ============================================================================
-- Daily Cost Summary Views (per environment)
-- ============================================================================

DO $$
DECLARE
    env TEXT;
    envs TEXT[] := ARRAY['dev', 'staging', 'prod'];
BEGIN
    FOREACH env IN ARRAY envs
    LOOP
        EXECUTE format('
            CREATE OR REPLACE VIEW ai_daily_costs_%s AS
            SELECT 
                org_id,
                DATE(created_at) as date,
                operation,
                model,
                COUNT(*) as request_count,
                SUM(prompt_tokens) as total_prompt_tokens,
                SUM(completion_tokens) as total_completion_tokens,
                SUM(total_tokens) as total_tokens,
                SUM(cost_usd) as total_cost_usd,
                COUNT(CASE WHEN cached THEN 1 END) as cached_requests,
                ROUND(AVG(latency_ms)::numeric, 2) as avg_latency_ms
            FROM ai_usage_logs_%s
            GROUP BY org_id, DATE(created_at), operation, model
            ORDER BY DATE(created_at) DESC, total_cost_usd DESC;
        ', env, env);
        
        RAISE NOTICE 'Created ai_daily_costs_% view', env;
    END LOOP;
END $$;

-- ============================================================================
-- Organization Usage Summary Views (per environment)
-- ============================================================================

DO $$
DECLARE
    env TEXT;
    envs TEXT[] := ARRAY['dev', 'staging', 'prod'];
BEGIN
    FOREACH env IN ARRAY envs
    LOOP
        EXECUTE format('
            CREATE OR REPLACE VIEW ai_org_usage_summary_%s AS
            SELECT 
                org_id,
                COUNT(*) as total_requests,
                SUM(total_tokens) as total_tokens,
                SUM(cost_usd) as total_cost_usd,
                COUNT(CASE WHEN cached THEN 1 END) as cached_requests,
                ROUND(
                    COUNT(CASE WHEN cached THEN 1 END)::numeric / 
                    NULLIF(COUNT(*)::numeric, 0) * 100, 
                    2
                ) as cache_hit_rate,
                ROUND(AVG(latency_ms)::numeric, 2) as avg_latency_ms,
                MIN(created_at) as first_request,
                MAX(created_at) as last_request
            FROM ai_usage_logs_%s
            GROUP BY org_id;
        ', env, env);
        
        RAISE NOTICE 'Created ai_org_usage_summary_% view', env;
    END LOOP;
END $$;

-- ============================================================================
-- Model Usage Statistics Views (per environment)
-- ============================================================================

DO $$
DECLARE
    env TEXT;
    envs TEXT[] := ARRAY['dev', 'staging', 'prod'];
BEGIN
    FOREACH env IN ARRAY envs
    LOOP
        EXECUTE format('
            CREATE OR REPLACE VIEW ai_model_stats_%s AS
            SELECT 
                model,
                COUNT(*) as request_count,
                SUM(total_tokens) as total_tokens,
                SUM(cost_usd) as total_cost_usd,
                ROUND(AVG(cost_usd)::numeric, 6) as avg_cost_per_request,
                ROUND(AVG(latency_ms)::numeric, 2) as avg_latency_ms,
                COUNT(DISTINCT org_id) as unique_orgs,
                COUNT(DISTINCT user_id) as unique_users
            FROM ai_usage_logs_%s
            GROUP BY model
            ORDER BY total_cost_usd DESC;
        ', env, env);
        
        RAISE NOTICE 'Created ai_model_stats_% view', env;
    END LOOP;
END $$;

-- ============================================================================
-- Admin Audit Log Table (shared across environments)
-- ============================================================================

CREATE TABLE IF NOT EXISTS admin_audit_logs (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    admin_user_id UUID NOT NULL,
    action TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id TEXT,
    old_value JSONB,
    new_value JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT admin_audit_action_check CHECK (
        action IN (
            'create', 'read', 'update', 'delete',
            'secret_access', 'secret_create', 'secret_update', 'secret_delete',
            'env_var_update', 'job_cancel', 'job_retry',
            'user_role_change', 'config_change'
        )
    )
);

CREATE INDEX IF NOT EXISTS idx_admin_audit_admin ON admin_audit_logs(admin_user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_admin_audit_action ON admin_audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_admin_audit_resource ON admin_audit_logs(resource_type, resource_id);

-- ============================================================================
-- Row Level Security (RLS) Policies
-- ============================================================================

DO $$
DECLARE
    env TEXT;
    envs TEXT[] := ARRAY['dev', 'staging', 'prod'];
BEGIN
    FOREACH env IN ARRAY envs
    LOOP
        -- Enable RLS
        EXECUTE format('ALTER TABLE ai_usage_logs_%s ENABLE ROW LEVEL SECURITY;', env);
        
        -- Policy: Service role can do everything
        EXECUTE format('
            DROP POLICY IF EXISTS "Service role full access %s" ON ai_usage_logs_%s;
            CREATE POLICY "Service role full access %s" ON ai_usage_logs_%s
                FOR ALL
                USING (auth.role() = ''service_role'');
        ', env, env, env, env);
        
        -- Policy: Users can view their org''s usage
        EXECUTE format('
            DROP POLICY IF EXISTS "Users can view org usage %s" ON ai_usage_logs_%s;
            CREATE POLICY "Users can view org usage %s" ON ai_usage_logs_%s
                FOR SELECT
                USING (
                    org_id IN (
                        SELECT org_id FROM user_profiles 
                        WHERE id = auth.uid()
                    )
                );
        ', env, env, env, env);
        
        RAISE NOTICE 'Created RLS policies for ai_usage_logs_%', env;
    END LOOP;
END $$;

-- RLS for admin audit logs
ALTER TABLE admin_audit_logs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Service role full access admin_audit" ON admin_audit_logs;
CREATE POLICY "Service role full access admin_audit" ON admin_audit_logs
    FOR ALL
    USING (auth.role() = 'service_role');

DROP POLICY IF EXISTS "Admins can view audit logs" ON admin_audit_logs;
CREATE POLICY "Admins can view audit logs" ON admin_audit_logs
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM user_profiles 
            WHERE id = auth.uid() 
            AND role IN ('admin', 'system_admin')
        )
    );

-- ============================================================================
-- Helper Functions
-- ============================================================================

-- Function to get usage stats for an org within a date range
CREATE OR REPLACE FUNCTION get_ai_usage_stats(
    p_org_id UUID,
    p_start_date TIMESTAMPTZ DEFAULT NOW() - INTERVAL '30 days',
    p_end_date TIMESTAMPTZ DEFAULT NOW(),
    p_environment TEXT DEFAULT 'dev'
)
RETURNS TABLE (
    total_requests BIGINT,
    total_tokens BIGINT,
    total_cost_usd NUMERIC,
    cached_requests BIGINT,
    cache_hit_rate NUMERIC,
    avg_latency_ms NUMERIC
) 
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY EXECUTE format('
        SELECT 
            COUNT(*)::BIGINT as total_requests,
            COALESCE(SUM(total_tokens), 0)::BIGINT as total_tokens,
            COALESCE(SUM(cost_usd), 0)::NUMERIC as total_cost_usd,
            COUNT(CASE WHEN cached THEN 1 END)::BIGINT as cached_requests,
            ROUND(
                COUNT(CASE WHEN cached THEN 1 END)::NUMERIC / 
                NULLIF(COUNT(*)::NUMERIC, 0) * 100, 
                2
            ) as cache_hit_rate,
            ROUND(AVG(latency_ms)::NUMERIC, 2) as avg_latency_ms
        FROM ai_usage_logs_%s
        WHERE org_id = $1
          AND created_at >= $2
          AND created_at <= $3
    ', p_environment)
    USING p_org_id, p_start_date, p_end_date;
END;
$$;

-- Function to get daily breakdown for an org
CREATE OR REPLACE FUNCTION get_ai_daily_breakdown(
    p_org_id UUID,
    p_days INTEGER DEFAULT 30,
    p_environment TEXT DEFAULT 'dev'
)
RETURNS TABLE (
    date DATE,
    requests BIGINT,
    tokens BIGINT,
    cost_usd NUMERIC
) 
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY EXECUTE format('
        SELECT 
            DATE(created_at) as date,
            COUNT(*)::BIGINT as requests,
            COALESCE(SUM(total_tokens), 0)::BIGINT as tokens,
            COALESCE(SUM(cost_usd), 0)::NUMERIC as cost_usd
        FROM ai_usage_logs_%s
        WHERE org_id = $1
          AND created_at >= NOW() - ($2 || '' days'')::INTERVAL
        GROUP BY DATE(created_at)
        ORDER BY date DESC
    ', p_environment)
    USING p_org_id, p_days;
END;
$$;

-- ============================================================================
-- Grant Permissions
-- ============================================================================

-- Grant access to authenticated users for the views
DO $$
DECLARE
    env TEXT;
    envs TEXT[] := ARRAY['dev', 'staging', 'prod'];
BEGIN
    FOREACH env IN ARRAY envs
    LOOP
        EXECUTE format('GRANT SELECT ON ai_daily_costs_%s TO authenticated;', env);
        EXECUTE format('GRANT SELECT ON ai_org_usage_summary_%s TO authenticated;', env);
        EXECUTE format('GRANT SELECT ON ai_model_stats_%s TO authenticated;', env);
    END LOOP;
END $$;

GRANT SELECT ON admin_audit_logs TO authenticated;
GRANT EXECUTE ON FUNCTION get_ai_usage_stats TO authenticated;
GRANT EXECUTE ON FUNCTION get_ai_daily_breakdown TO authenticated;

-- ============================================================================
-- Migration Complete
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '===========================================';
    RAISE NOTICE 'AI Usage Tracking Migration Complete!';
    RAISE NOTICE '===========================================';
    RAISE NOTICE 'Created tables:';
    RAISE NOTICE '  - ai_usage_logs_dev';
    RAISE NOTICE '  - ai_usage_logs_staging';
    RAISE NOTICE '  - ai_usage_logs_prod';
    RAISE NOTICE '  - admin_audit_logs';
    RAISE NOTICE '';
    RAISE NOTICE 'Created views:';
    RAISE NOTICE '  - ai_daily_costs_[env]';
    RAISE NOTICE '  - ai_org_usage_summary_[env]';
    RAISE NOTICE '  - ai_model_stats_[env]';
    RAISE NOTICE '';
    RAISE NOTICE 'Created functions:';
    RAISE NOTICE '  - get_ai_usage_stats()';
    RAISE NOTICE '  - get_ai_daily_breakdown()';
    RAISE NOTICE '===========================================';
END $$;
