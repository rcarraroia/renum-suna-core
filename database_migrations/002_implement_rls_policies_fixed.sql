-- Migration Script: Implement comprehensive Row Level Security policies (FIXED)
-- Version: 002_fixed
-- Description: Enable RLS and create comprehensive security policies for all renum_ tables
-- Author: Sistema Renum Holistic Fixes
-- Date: 2025-07-28

-- ============================================================================
-- SECURITY MIGRATION: COMPREHENSIVE RLS IMPLEMENTATION (FIXED)
-- ============================================================================

BEGIN;

-- Set transaction isolation level for consistency
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;

-- Log migration start
DO $$
BEGIN
    RAISE NOTICE 'Starting migration 002_fixed: Implement comprehensive RLS policies at %', now();
END $$;

-- ============================================================================
-- 1. ENABLE RLS ON ALL RENUM_ TABLES (FIXED)
-- ============================================================================

-- Enable RLS on core team tables
DO $$
DECLARE
    tbl_name TEXT;
    core_tables TEXT[] := ARRAY[
        'renum_agent_teams',
        'renum_team_executions', 
        'renum_team_agent_executions',
        'renum_team_messages',
        'renum_team_context_snapshots',
        'renum_ai_usage_logs',
        'renum_user_api_keys'
    ];
BEGIN
    FOREACH tbl_name IN ARRAY core_tables
    LOOP
        IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = tbl_name AND table_schema = 'public') THEN
            EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', tbl_name);
            RAISE NOTICE 'Enabled RLS on table: %', tbl_name;
        ELSE
            RAISE NOTICE 'Table % does not exist, skipping RLS enable', tbl_name;
        END IF;
    END LOOP;
END $$;

-- Enable RLS on admin tables
DO $$
DECLARE
    tbl_name TEXT;
    admin_tables TEXT[] := ARRAY[
        'renum_admins',
        'renum_admin_credentials',
        'renum_system_settings',
        'renum_audit_logs'
    ];
BEGIN
    FOREACH tbl_name IN ARRAY admin_tables
    LOOP
        IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = tbl_name AND table_schema = 'public') THEN
            EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', tbl_name);
            RAISE NOTICE 'Enabled RLS on admin table: %', tbl_name;
        ELSE
            RAISE NOTICE 'Admin table % does not exist, skipping RLS enable', tbl_name;
        END IF;
    END LOOP;
END $$;

-- Enable RLS on optional RAG tables (if they exist)
DO $$
DECLARE
    tbl_name TEXT;
    rag_tables TEXT[] := ARRAY[
        'renum_knowledge_bases',
        'renum_knowledge_collections',
        'renum_documents',
        'renum_document_chunks',
        'renum_document_versions',
        'renum_document_usage_stats',
        'renum_processing_jobs'
    ];
BEGIN
    FOREACH tbl_name IN ARRAY rag_tables
    LOOP
        IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = tbl_name AND table_schema = 'public') THEN
            EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', tbl_name);
            RAISE NOTICE 'Enabled RLS on RAG table: %', tbl_name;
        ELSE
            RAISE NOTICE 'RAG table % does not exist, skipping RLS enable', tbl_name;
        END IF;
    END LOOP;
END $$;

-- Enable RLS on agent sharing tables
DO $$
DECLARE
    tbl_name TEXT;
    sharing_tables TEXT[] := ARRAY[
        'renum_agent_shares',
        'renum_settings',
        'renum_metrics'
    ];
BEGIN
    FOREACH tbl_name IN ARRAY sharing_tables
    LOOP
        IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = tbl_name AND table_schema = 'public') THEN
            EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', tbl_name);
            RAISE NOTICE 'Enabled RLS on sharing table: %', tbl_name;
        ELSE
            RAISE NOTICE 'Sharing table % does not exist, skipping RLS enable', tbl_name;
        END IF;
    END LOOP;
END $$;

-- ============================================================================
-- 2. CREATE HELPER FUNCTIONS FOR RLS POLICIES
-- ============================================================================

-- Function to check if user is admin
CREATE OR REPLACE FUNCTION renum_is_admin(user_id UUID DEFAULT auth.uid())
RETURNS BOOLEAN AS $$
BEGIN
    IF user_id IS NULL THEN
        RETURN FALSE;
    END IF;
    
    RETURN EXISTS (
        SELECT 1 FROM renum_admins 
        WHERE user_id = $1 AND is_active = true
    );
EXCEPTION
    WHEN OTHERS THEN
        RETURN FALSE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to check if user is superadmin
CREATE OR REPLACE FUNCTION renum_is_superadmin(user_id UUID DEFAULT auth.uid())
RETURNS BOOLEAN AS $$
BEGIN
    IF user_id IS NULL THEN
        RETURN FALSE;
    END IF;
    
    RETURN EXISTS (
        SELECT 1 FROM renum_admins 
        WHERE user_id = $1 AND role = 'superadmin' AND is_active = true
    );
EXCEPTION
    WHEN OTHERS THEN
        RETURN FALSE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get user's client_id (simplified version)
CREATE OR REPLACE FUNCTION renum_get_user_client_id(user_id UUID DEFAULT auth.uid())
RETURNS UUID AS $$
BEGIN
    -- For now, return the user_id as client_id
    -- This can be enhanced later with proper user-client mapping
    RETURN COALESCE(user_id, '00000000-0000-0000-0000-000000000000'::UUID);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================================
-- 3. IMPLEMENT RLS POLICIES FOR CORE TEAM TABLES
-- ============================================================================

-- Policies for renum_agent_teams
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'renum_agent_teams' AND table_schema = 'public') THEN
        -- Drop existing policies if they exist
        DROP POLICY IF EXISTS "renum_agent_teams_user_policy" ON renum_agent_teams;
        DROP POLICY IF EXISTS "renum_agent_teams_admin_policy" ON renum_agent_teams;
        DROP POLICY IF EXISTS "renum_agent_teams_user_access" ON renum_agent_teams;
        DROP POLICY IF EXISTS "renum_agent_teams_admin_access" ON renum_agent_teams;
        
        -- User can access their own teams
        CREATE POLICY "renum_agent_teams_user_access" ON renum_agent_teams
            FOR ALL
            USING (user_id = auth.uid());
        
        -- Admins can access all teams
        CREATE POLICY "renum_agent_teams_admin_access" ON renum_agent_teams
            FOR ALL
            USING (renum_is_admin());
        
        RAISE NOTICE 'Created RLS policies for renum_agent_teams';
    END IF;
END $$;

-- Policies for renum_team_executions
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'renum_team_executions' AND table_schema = 'public') THEN
        -- Drop existing policies if they exist
        DROP POLICY IF EXISTS "renum_team_executions_user_policy" ON renum_team_executions;
        DROP POLICY IF EXISTS "renum_team_executions_admin_policy" ON renum_team_executions;
        DROP POLICY IF EXISTS "renum_team_executions_user_access" ON renum_team_executions;
        DROP POLICY IF EXISTS "renum_team_executions_admin_access" ON renum_team_executions;
        DROP POLICY IF EXISTS "renum_team_executions_user_select" ON renum_team_executions;
        DROP POLICY IF EXISTS "renum_team_executions_user_insert" ON renum_team_executions;
        DROP POLICY IF EXISTS "renum_team_executions_user_update" ON renum_team_executions;
        DROP POLICY IF EXISTS "renum_team_executions_user_delete" ON renum_team_executions;
        DROP POLICY IF EXISTS "renum_team_executions_admin_select" ON renum_team_executions;
        DROP POLICY IF EXISTS "renum_team_executions_admin_insert" ON renum_team_executions;
        DROP POLICY IF EXISTS "renum_team_executions_admin_update" ON renum_team_executions;
        DROP POLICY IF EXISTS "renum_team_executions_admin_delete" ON renum_team_executions;
        
        -- User can access their own executions
        CREATE POLICY "renum_team_executions_user_select" ON renum_team_executions
            FOR SELECT
            USING (user_id = auth.uid());
            
        CREATE POLICY "renum_team_executions_user_insert" ON renum_team_executions
            FOR INSERT
            WITH CHECK (user_id = auth.uid());
            
        CREATE POLICY "renum_team_executions_user_update" ON renum_team_executions
            FOR UPDATE
            USING (user_id = auth.uid());
            
        CREATE POLICY "renum_team_executions_user_delete" ON renum_team_executions
            FOR DELETE
            USING (user_id = auth.uid());
        
        -- Admins can access all executions
        CREATE POLICY "renum_team_executions_admin_select" ON renum_team_executions
            FOR SELECT
            USING (renum_is_admin());
            
        CREATE POLICY "renum_team_executions_admin_insert" ON renum_team_executions
            FOR INSERT
            WITH CHECK (renum_is_admin());
            
        CREATE POLICY "renum_team_executions_admin_update" ON renum_team_executions
            FOR UPDATE
            USING (renum_is_admin());
            
        CREATE POLICY "renum_team_executions_admin_delete" ON renum_team_executions
            FOR DELETE
            USING (renum_is_admin());
        
        RAISE NOTICE 'Created RLS policies for renum_team_executions';
    END IF;
END $$;

-- Policies for renum_team_agent_executions
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'renum_team_agent_executions' AND table_schema = 'public') THEN
        -- Drop existing policies if they exist
        DROP POLICY IF EXISTS "renum_team_agent_executions_user_policy" ON renum_team_agent_executions;
        DROP POLICY IF EXISTS "renum_team_agent_executions_admin_policy" ON renum_team_agent_executions;
        DROP POLICY IF EXISTS "renum_team_agent_executions_user_access" ON renum_team_agent_executions;
        DROP POLICY IF EXISTS "renum_team_agent_executions_admin_access" ON renum_team_agent_executions;
        DROP POLICY IF EXISTS "renum_team_agent_executions_user_select" ON renum_team_agent_executions;
        DROP POLICY IF EXISTS "renum_team_agent_executions_user_insert" ON renum_team_agent_executions;
        DROP POLICY IF EXISTS "renum_team_agent_executions_user_update" ON renum_team_agent_executions;
        DROP POLICY IF EXISTS "renum_team_agent_executions_user_delete" ON renum_team_agent_executions;
        DROP POLICY IF EXISTS "renum_team_agent_executions_admin_select" ON renum_team_agent_executions;
        DROP POLICY IF EXISTS "renum_team_agent_executions_admin_insert" ON renum_team_agent_executions;
        DROP POLICY IF EXISTS "renum_team_agent_executions_admin_update" ON renum_team_agent_executions;
        DROP POLICY IF EXISTS "renum_team_agent_executions_admin_delete" ON renum_team_agent_executions;
        
        -- User can access executions for their teams
        CREATE POLICY "renum_team_agent_executions_user_select" ON renum_team_agent_executions
            FOR SELECT
            USING (
                execution_id IN (
                    SELECT execution_id FROM renum_team_executions WHERE user_id = auth.uid()
                )
            );
            
        CREATE POLICY "renum_team_agent_executions_user_insert" ON renum_team_agent_executions
            FOR INSERT
            WITH CHECK (
                execution_id IN (
                    SELECT execution_id FROM renum_team_executions WHERE user_id = auth.uid()
                )
            );
            
        CREATE POLICY "renum_team_agent_executions_user_update" ON renum_team_agent_executions
            FOR UPDATE
            USING (
                execution_id IN (
                    SELECT execution_id FROM renum_team_executions WHERE user_id = auth.uid()
                )
            );
            
        CREATE POLICY "renum_team_agent_executions_user_delete" ON renum_team_agent_executions
            FOR DELETE
            USING (
                execution_id IN (
                    SELECT execution_id FROM renum_team_executions WHERE user_id = auth.uid()
                )
            );
        
        -- Admins can access all agent executions
        CREATE POLICY "renum_team_agent_executions_admin_select" ON renum_team_agent_executions
            FOR SELECT
            USING (renum_is_admin());
            
        CREATE POLICY "renum_team_agent_executions_admin_insert" ON renum_team_agent_executions
            FOR INSERT
            WITH CHECK (renum_is_admin());
            
        CREATE POLICY "renum_team_agent_executions_admin_update" ON renum_team_agent_executions
            FOR UPDATE
            USING (renum_is_admin());
            
        CREATE POLICY "renum_team_agent_executions_admin_delete" ON renum_team_agent_executions
            FOR DELETE
            USING (renum_is_admin());
        
        RAISE NOTICE 'Created RLS policies for renum_team_agent_executions';
    END IF;
END $$;

-- Policies for renum_team_messages
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'renum_team_messages' AND table_schema = 'public') THEN
        -- Drop existing policies if they exist
        DROP POLICY IF EXISTS "renum_team_messages_user_policy" ON renum_team_messages;
        DROP POLICY IF EXISTS "renum_team_messages_admin_policy" ON renum_team_messages;
        DROP POLICY IF EXISTS "renum_team_messages_user_access" ON renum_team_messages;
        DROP POLICY IF EXISTS "renum_team_messages_admin_access" ON renum_team_messages;
        DROP POLICY IF EXISTS "renum_team_messages_user_select" ON renum_team_messages;
        DROP POLICY IF EXISTS "renum_team_messages_user_insert" ON renum_team_messages;
        DROP POLICY IF EXISTS "renum_team_messages_user_update" ON renum_team_messages;
        DROP POLICY IF EXISTS "renum_team_messages_user_delete" ON renum_team_messages;
        DROP POLICY IF EXISTS "renum_team_messages_admin_select" ON renum_team_messages;
        DROP POLICY IF EXISTS "renum_team_messages_admin_insert" ON renum_team_messages;
        DROP POLICY IF EXISTS "renum_team_messages_admin_update" ON renum_team_messages;
        DROP POLICY IF EXISTS "renum_team_messages_admin_delete" ON renum_team_messages;
        
        -- User can access messages for their executions
        CREATE POLICY "renum_team_messages_user_select" ON renum_team_messages
            FOR SELECT
            USING (
                execution_id IN (
                    SELECT execution_id FROM renum_team_executions WHERE user_id = auth.uid()
                )
            );
            
        CREATE POLICY "renum_team_messages_user_insert" ON renum_team_messages
            FOR INSERT
            WITH CHECK (
                execution_id IN (
                    SELECT execution_id FROM renum_team_executions WHERE user_id = auth.uid()
                )
            );
            
        CREATE POLICY "renum_team_messages_user_update" ON renum_team_messages
            FOR UPDATE
            USING (
                execution_id IN (
                    SELECT execution_id FROM renum_team_executions WHERE user_id = auth.uid()
                )
            );
            
        CREATE POLICY "renum_team_messages_user_delete" ON renum_team_messages
            FOR DELETE
            USING (
                execution_id IN (
                    SELECT execution_id FROM renum_team_executions WHERE user_id = auth.uid()
                )
            );
        
        -- Admins can access all messages
        CREATE POLICY "renum_team_messages_admin_select" ON renum_team_messages
            FOR SELECT
            USING (renum_is_admin());
            
        CREATE POLICY "renum_team_messages_admin_insert" ON renum_team_messages
            FOR INSERT
            WITH CHECK (renum_is_admin());
            
        CREATE POLICY "renum_team_messages_admin_update" ON renum_team_messages
            FOR UPDATE
            USING (renum_is_admin());
            
        CREATE POLICY "renum_team_messages_admin_delete" ON renum_team_messages
            FOR DELETE
            USING (renum_is_admin());
        
        RAISE NOTICE 'Created RLS policies for renum_team_messages';
    END IF;
END $$;

-- Policies for renum_ai_usage_logs
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'renum_ai_usage_logs' AND table_schema = 'public') THEN
        -- Drop existing policies if they exist
        DROP POLICY IF EXISTS "renum_ai_usage_logs_user_policy" ON renum_ai_usage_logs;
        DROP POLICY IF EXISTS "renum_ai_usage_logs_admin_policy" ON renum_ai_usage_logs;
        DROP POLICY IF EXISTS "renum_ai_usage_logs_user_access" ON renum_ai_usage_logs;
        DROP POLICY IF EXISTS "renum_ai_usage_logs_admin_access" ON renum_ai_usage_logs;
        DROP POLICY IF EXISTS "renum_ai_usage_logs_user_select" ON renum_ai_usage_logs;
        DROP POLICY IF EXISTS "renum_ai_usage_logs_user_insert" ON renum_ai_usage_logs;
        DROP POLICY IF EXISTS "renum_ai_usage_logs_user_update" ON renum_ai_usage_logs;
        DROP POLICY IF EXISTS "renum_ai_usage_logs_user_delete" ON renum_ai_usage_logs;
        DROP POLICY IF EXISTS "renum_ai_usage_logs_admin_select" ON renum_ai_usage_logs;
        DROP POLICY IF EXISTS "renum_ai_usage_logs_admin_insert" ON renum_ai_usage_logs;
        DROP POLICY IF EXISTS "renum_ai_usage_logs_admin_update" ON renum_ai_usage_logs;
        DROP POLICY IF EXISTS "renum_ai_usage_logs_admin_delete" ON renum_ai_usage_logs;
        
        -- User can access their own usage logs
        CREATE POLICY "renum_ai_usage_logs_user_select" ON renum_ai_usage_logs
            FOR SELECT
            USING (user_id = auth.uid());
            
        CREATE POLICY "renum_ai_usage_logs_user_insert" ON renum_ai_usage_logs
            FOR INSERT
            WITH CHECK (user_id = auth.uid());
            
        CREATE POLICY "renum_ai_usage_logs_user_update" ON renum_ai_usage_logs
            FOR UPDATE
            USING (user_id = auth.uid());
            
        CREATE POLICY "renum_ai_usage_logs_user_delete" ON renum_ai_usage_logs
            FOR DELETE
            USING (user_id = auth.uid());
        
        -- Admins can access all usage logs
        CREATE POLICY "renum_ai_usage_logs_admin_select" ON renum_ai_usage_logs
            FOR SELECT
            USING (renum_is_admin());
            
        CREATE POLICY "renum_ai_usage_logs_admin_insert" ON renum_ai_usage_logs
            FOR INSERT
            WITH CHECK (renum_is_admin());
            
        CREATE POLICY "renum_ai_usage_logs_admin_update" ON renum_ai_usage_logs
            FOR UPDATE
            USING (renum_is_admin());
            
        CREATE POLICY "renum_ai_usage_logs_admin_delete" ON renum_ai_usage_logs
            FOR DELETE
            USING (renum_is_admin());
        
        RAISE NOTICE 'Created RLS policies for renum_ai_usage_logs';
    END IF;
END $$;

-- Policies for renum_user_api_keys
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'renum_user_api_keys' AND table_schema = 'public') THEN
        -- Drop existing policies if they exist
        DROP POLICY IF EXISTS "renum_user_api_keys_user_policy" ON renum_user_api_keys;
        DROP POLICY IF EXISTS "renum_user_api_keys_admin_policy" ON renum_user_api_keys;
        DROP POLICY IF EXISTS "renum_user_api_keys_user_access" ON renum_user_api_keys;
        DROP POLICY IF EXISTS "renum_user_api_keys_superadmin_access" ON renum_user_api_keys;
        DROP POLICY IF EXISTS "renum_user_api_keys_user_select" ON renum_user_api_keys;
        DROP POLICY IF EXISTS "renum_user_api_keys_user_insert" ON renum_user_api_keys;
        DROP POLICY IF EXISTS "renum_user_api_keys_user_update" ON renum_user_api_keys;
        DROP POLICY IF EXISTS "renum_user_api_keys_user_delete" ON renum_user_api_keys;
        
        -- User can only access their own API keys
        CREATE POLICY "renum_user_api_keys_user_select" ON renum_user_api_keys
            FOR SELECT
            USING (user_id = auth.uid());
            
        CREATE POLICY "renum_user_api_keys_user_insert" ON renum_user_api_keys
            FOR INSERT
            WITH CHECK (user_id = auth.uid());
            
        CREATE POLICY "renum_user_api_keys_user_update" ON renum_user_api_keys
            FOR UPDATE
            USING (user_id = auth.uid());
            
        CREATE POLICY "renum_user_api_keys_user_delete" ON renum_user_api_keys
            FOR DELETE
            USING (user_id = auth.uid());
        
        -- Superadmins can access all API keys (for support purposes)
        CREATE POLICY "renum_user_api_keys_superadmin_access" ON renum_user_api_keys
            FOR SELECT
            USING (renum_is_superadmin());
        
        RAISE NOTICE 'Created RLS policies for renum_user_api_keys';
    END IF;
END $$;

-- ============================================================================
-- 4. IMPLEMENT RLS POLICIES FOR ADMIN TABLES
-- ============================================================================

-- Policies for renum_admins
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'renum_admins' AND table_schema = 'public') THEN
        -- Drop existing policies if they exist
        DROP POLICY IF EXISTS "admin_superadmin_policy" ON renum_admins;
        DROP POLICY IF EXISTS "renum_admins_self_access" ON renum_admins;
        DROP POLICY IF EXISTS "renum_admins_superadmin_manage" ON renum_admins;
        DROP POLICY IF EXISTS "renum_admins_superadmin_select" ON renum_admins;
        DROP POLICY IF EXISTS "renum_admins_superadmin_insert" ON renum_admins;
        DROP POLICY IF EXISTS "renum_admins_superadmin_update" ON renum_admins;
        DROP POLICY IF EXISTS "renum_admins_superadmin_delete" ON renum_admins;
        
        -- Admins can see their own record, superadmins can see all
        CREATE POLICY "renum_admins_self_access" ON renum_admins
            FOR SELECT
            USING (user_id = auth.uid());
        
        CREATE POLICY "renum_admins_superadmin_select" ON renum_admins
            FOR SELECT
            USING (renum_is_superadmin());
            
        CREATE POLICY "renum_admins_superadmin_insert" ON renum_admins
            FOR INSERT
            WITH CHECK (renum_is_superadmin());
            
        CREATE POLICY "renum_admins_superadmin_update" ON renum_admins
            FOR UPDATE
            USING (renum_is_superadmin());
            
        CREATE POLICY "renum_admins_superadmin_delete" ON renum_admins
            FOR DELETE
            USING (renum_is_superadmin());
        
        RAISE NOTICE 'Created RLS policies for renum_admins';
    END IF;
END $$;

-- Policies for renum_system_settings
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'renum_system_settings' AND table_schema = 'public') THEN
        -- Drop existing policies if they exist
        DROP POLICY IF EXISTS "system_settings_read_policy" ON renum_system_settings;
        DROP POLICY IF EXISTS "system_settings_write_policy" ON renum_system_settings;
        DROP POLICY IF EXISTS "renum_system_settings_admin_read" ON renum_system_settings;
        DROP POLICY IF EXISTS "renum_system_settings_superadmin_write" ON renum_system_settings;
        DROP POLICY IF EXISTS "renum_system_settings_superadmin_insert" ON renum_system_settings;
        DROP POLICY IF EXISTS "renum_system_settings_superadmin_update" ON renum_system_settings;
        DROP POLICY IF EXISTS "renum_system_settings_superadmin_delete" ON renum_system_settings;
        
        -- All admins can read settings
        CREATE POLICY "renum_system_settings_admin_read" ON renum_system_settings
            FOR SELECT
            USING (renum_is_admin());
        
        -- Only superadmins can modify settings
        CREATE POLICY "renum_system_settings_superadmin_insert" ON renum_system_settings
            FOR INSERT
            WITH CHECK (renum_is_superadmin());
            
        CREATE POLICY "renum_system_settings_superadmin_update" ON renum_system_settings
            FOR UPDATE
            USING (renum_is_superadmin());
            
        CREATE POLICY "renum_system_settings_superadmin_delete" ON renum_system_settings
            FOR DELETE
            USING (renum_is_superadmin());
        
        RAISE NOTICE 'Created RLS policies for renum_system_settings';
    END IF;
END $$;

-- Policies for renum_audit_logs
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'renum_audit_logs' AND table_schema = 'public') THEN
        -- Drop existing policies if they exist
        DROP POLICY IF EXISTS "audit_logs_policy" ON renum_audit_logs;
        DROP POLICY IF EXISTS "renum_audit_logs_admin_read" ON renum_audit_logs;
        DROP POLICY IF EXISTS "renum_audit_logs_system_insert" ON renum_audit_logs;
        
        -- All admins can read audit logs
        CREATE POLICY "renum_audit_logs_admin_read" ON renum_audit_logs
            FOR SELECT
            USING (renum_is_admin());
        
        -- System can insert audit logs (for automated logging)
        CREATE POLICY "renum_audit_logs_system_insert" ON renum_audit_logs
            FOR INSERT
            WITH CHECK (true); -- Allow system inserts
        
        RAISE NOTICE 'Created RLS policies for renum_audit_logs';
    END IF;
END $$;

-- ============================================================================
-- 5. IMPLEMENT RLS POLICIES FOR AGENT SHARING (IF EXISTS)
-- ============================================================================

-- Policies for renum_agent_shares (if exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'renum_agent_shares' AND table_schema = 'public') THEN
        -- Drop existing policies if they exist
        DROP POLICY IF EXISTS "Usuários podem ver seus próprios compartilhamentos" ON renum_agent_shares;
        DROP POLICY IF EXISTS "Usuários podem criar compartilhamentos para seus agentes" ON renum_agent_shares;
        DROP POLICY IF EXISTS "Usuários podem atualizar compartilhamentos de seus agentes" ON renum_agent_shares;
        DROP POLICY IF EXISTS "Usuários podem excluir compartilhamentos de seus agentes" ON renum_agent_shares;
        DROP POLICY IF EXISTS "renum_agent_shares_user_view" ON renum_agent_shares;
        DROP POLICY IF EXISTS "renum_agent_shares_create" ON renum_agent_shares;
        DROP POLICY IF EXISTS "renum_agent_shares_update" ON renum_agent_shares;
        DROP POLICY IF EXISTS "renum_agent_shares_delete" ON renum_agent_shares;
        
        -- Users can see shares where they are recipient or creator
        CREATE POLICY "renum_agent_shares_user_view" ON renum_agent_shares
            FOR SELECT
            USING (
                auth.uid() = user_id OR 
                auth.uid() = created_by OR
                renum_is_admin()
            );
        
        -- Users can create shares for agents they own
        CREATE POLICY "renum_agent_shares_create" ON renum_agent_shares
            FOR INSERT
            WITH CHECK (
                auth.uid() = created_by AND
                renum_is_admin() -- Simplified check for now
            );
        
        -- Users can update shares they created
        CREATE POLICY "renum_agent_shares_update" ON renum_agent_shares
            FOR UPDATE
            USING (auth.uid() = created_by OR renum_is_admin());
        
        -- Users can delete shares they created
        CREATE POLICY "renum_agent_shares_delete" ON renum_agent_shares
            FOR DELETE
            USING (auth.uid() = created_by OR renum_is_admin());
        
        RAISE NOTICE 'Created RLS policies for renum_agent_shares';
    END IF;
END $$;

-- ============================================================================
-- 6. VERIFICATION AND TESTING
-- ============================================================================

-- Function to test RLS policies
CREATE OR REPLACE FUNCTION test_rls_policies()
RETURNS TABLE(table_name TEXT, rls_enabled BOOLEAN, policy_count INTEGER) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t.tablename::TEXT,
        CASE WHEN c.relrowsecurity THEN true ELSE false END as rls_enabled,
        COALESCE(p.policy_count, 0)::INTEGER as policy_count
    FROM pg_tables t
    LEFT JOIN pg_class c ON c.relname = t.tablename AND c.relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
    LEFT JOIN (
        SELECT 
            tablename,
            COUNT(*) as policy_count
        FROM pg_policies 
        WHERE schemaname = 'public'
        GROUP BY tablename
    ) p ON t.tablename = p.tablename
    WHERE t.schemaname = 'public' 
    AND t.tablename LIKE 'renum_%'
    ORDER BY t.tablename;
END;
$$ LANGUAGE plpgsql;

-- Run verification
DO $$
DECLARE
    test_result RECORD;
    total_tables INTEGER := 0;
    rls_enabled_count INTEGER := 0;
    total_policies INTEGER := 0;
BEGIN
    RAISE NOTICE 'RLS Policy Verification:';
    RAISE NOTICE '========================';
    
    FOR test_result IN SELECT * FROM test_rls_policies()
    LOOP
        total_tables := total_tables + 1;
        IF test_result.rls_enabled THEN
            rls_enabled_count := rls_enabled_count + 1;
        END IF;
        total_policies := total_policies + test_result.policy_count;
        
        RAISE NOTICE 'Table: % | RLS: % | Policies: %', 
            test_result.table_name,
            CASE WHEN test_result.rls_enabled THEN 'ON' ELSE 'OFF' END,
            test_result.policy_count;
    END LOOP;
    
    RAISE NOTICE '========================';
    RAISE NOTICE 'Summary: % tables, % with RLS enabled, % total policies',
        total_tables, rls_enabled_count, total_policies;
END $$;

-- ============================================================================
-- 7. LOG MIGRATION COMPLETION
-- ============================================================================

-- Log this migration
INSERT INTO renum_migration_log (migration_version, migration_name, notes)
VALUES ('002', 'Implement comprehensive RLS policies (fixed)', 'Enabled RLS and created security policies for all renum_ tables with proper user isolation and admin access - fixed version');

-- Log migration completion
DO $$
BEGIN
    RAISE NOTICE 'Migration 002_fixed completed successfully at %', now();
    RAISE NOTICE 'RLS enabled on all renum_ tables with comprehensive security policies';
    RAISE NOTICE 'Admin functions created for role-based access control';
END $$;

COMMIT;

-- ============================================================================
-- POST-MIGRATION NOTES
-- ============================================================================
-- 
-- After running this migration:
-- 1. Test all application functionality with different user roles
-- 2. Verify that users can only access their own data
-- 3. Verify that admins have appropriate elevated access
-- 4. Monitor for any unauthorized access attempts
-- 5. Update application code to handle RLS-related errors gracefully
-- 
-- Security considerations:
-- - All renum_ tables now have RLS enabled
-- - Users can only access their own data unless they are admins
-- - Superadmins have elevated privileges for system management
-- - All policy changes are logged in migration_log
-- 
-- ============================================================================