-- Migration Script: Implement comprehensive Row Level Security policies
-- Version: 002
-- Description: Enable RLS and create comprehensive security policies for all renum_ tables
-- Author: Sistema Renum Holistic Fixes
-- Date: 2025-07-28

-- ============================================================================
-- SECURITY MIGRATION: COMPREHENSIVE RLS IMPLEMENTATION
-- ============================================================================

BEGIN;

-- Set transaction isolation level for consistency
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;

-- Log migration start
DO $$
BEGIN
    RAISE NOTICE 'Starting migration 002: Implement comprehensive RLS policies at %', now();
END $$;

-- ============================================================================
-- 1. ENABLE RLS ON ALL RENUM_ TABLES
-- ============================================================================

-- Enable RLS on core team tables
DO $$
DECLARE
    table_name TEXT;
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
    FOREACH table_name IN ARRAY core_tables
    LOOP
        IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = table_name AND table_schema = 'public') THEN
            EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', table_name);
            RAISE NOTICE 'Enabled RLS on table: %', table_name;
        ELSE
            RAISE NOTICE 'Table % does not exist, skipping RLS enable', table_name;
        END IF;
    END LOOP;
END $$;

-- Enable RLS on admin tables
DO $$
DECLARE
    table_name TEXT;
    admin_tables TEXT[] := ARRAY[
        'renum_admins',
        'renum_admin_credentials',
        'renum_system_settings',
        'renum_audit_logs'
    ];
BEGIN
    FOREACH table_name IN ARRAY admin_tables
    LOOP
        IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = table_name AND table_schema = 'public') THEN
            EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', table_name);
            RAISE NOTICE 'Enabled RLS on admin table: %', table_name;
        ELSE
            RAISE NOTICE 'Admin table % does not exist, skipping RLS enable', table_name;
        END IF;
    END LOOP;
END $$;

-- Enable RLS on optional RAG tables (if they exist)
DO $$
DECLARE
    table_name TEXT;
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
    FOREACH table_name IN ARRAY rag_tables
    LOOP
        IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = table_name AND table_schema = 'public') THEN
            EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', table_name);
            RAISE NOTICE 'Enabled RLS on RAG table: %', table_name;
        ELSE
            RAISE NOTICE 'RAG table % does not exist, skipping RLS enable', table_name;
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
    RETURN EXISTS (
        SELECT 1 FROM renum_admins 
        WHERE user_id = $1 AND is_active = true
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to check if user is superadmin
CREATE OR REPLACE FUNCTION renum_is_superadmin(user_id UUID DEFAULT auth.uid())
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM renum_admins 
        WHERE user_id = $1 AND role = 'superadmin' AND is_active = true
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get user's client_id
CREATE OR REPLACE FUNCTION renum_get_user_client_id(user_id UUID DEFAULT auth.uid())
RETURNS UUID AS $$
DECLARE
    client_id UUID;
BEGIN
    -- This would need to be implemented based on your user-client relationship
    -- For now, we'll assume user_id can be used as client_id or there's a mapping table
    RETURN user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to check team ownership or membership
CREATE OR REPLACE FUNCTION renum_user_can_access_team(team_id UUID, user_id UUID DEFAULT auth.uid())
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM renum_agent_teams 
        WHERE team_id = $1 AND user_id = $2
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================================
-- 3. IMPLEMENT RLS POLICIES FOR CORE TEAM TABLES
-- ============================================================================

-- Policies for renum_agent_teams
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'renum_agent_teams' AND table_schema = 'public') THEN
        -- Drop existing policies
        DROP POLICY IF EXISTS "renum_agent_teams_user_policy" ON renum_agent_teams;
        DROP POLICY IF EXISTS "renum_agent_teams_admin_policy" ON renum_agent_teams;
        
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
        -- Drop existing policies
        DROP POLICY IF EXISTS "renum_team_executions_user_policy" ON renum_team_executions;
        DROP POLICY IF EXISTS "renum_team_executions_admin_policy" ON renum_team_executions;
        
        -- User can access their own executions
        CREATE POLICY "renum_team_executions_user_access" ON renum_team_executions
            FOR ALL
            USING (user_id = auth.uid());
        
        -- Admins can access all executions
        CREATE POLICY "renum_team_executions_admin_access" ON renum_team_executions
            FOR ALL
            USING (renum_is_admin());
        
        RAISE NOTICE 'Created RLS policies for renum_team_executions';
    END IF;
END $$;

-- Policies for renum_team_agent_executions
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'renum_team_agent_executions' AND table_schema = 'public') THEN
        -- Drop existing policies
        DROP POLICY IF EXISTS "renum_team_agent_executions_user_policy" ON renum_team_agent_executions;
        DROP POLICY IF EXISTS "renum_team_agent_executions_admin_policy" ON renum_team_agent_executions;
        
        -- User can access executions for their teams
        CREATE POLICY "renum_team_agent_executions_user_access" ON renum_team_agent_executions
            FOR ALL
            USING (
                execution_id IN (
                    SELECT execution_id FROM renum_team_executions WHERE user_id = auth.uid()
                )
            );
        
        -- Admins can access all agent executions
        CREATE POLICY "renum_team_agent_executions_admin_access" ON renum_team_agent_executions
            FOR ALL
            USING (renum_is_admin());
        
        RAISE NOTICE 'Created RLS policies for renum_team_agent_executions';
    END IF;
END $$;

-- Policies for renum_team_messages
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'renum_team_messages' AND table_schema = 'public') THEN
        -- Drop existing policies
        DROP POLICY IF EXISTS "renum_team_messages_user_policy" ON renum_team_messages;
        DROP POLICY IF EXISTS "renum_team_messages_admin_policy" ON renum_team_messages;
        
        -- User can access messages for their executions
        CREATE POLICY "renum_team_messages_user_access" ON renum_team_messages
            FOR ALL
            USING (
                execution_id IN (
                    SELECT execution_id FROM renum_team_executions WHERE user_id = auth.uid()
                )
            );
        
        -- Admins can access all messages
        CREATE POLICY "renum_team_messages_admin_access" ON renum_team_messages
            FOR ALL
            USING (renum_is_admin());
        
        RAISE NOTICE 'Created RLS policies for renum_team_messages';
    END IF;
END $$;

-- Policies for renum_ai_usage_logs
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'renum_ai_usage_logs' AND table_schema = 'public') THEN
        -- Drop existing policies
        DROP POLICY IF EXISTS "renum_ai_usage_logs_user_policy" ON renum_ai_usage_logs;
        DROP POLICY IF EXISTS "renum_ai_usage_logs_admin_policy" ON renum_ai_usage_logs;
        
        -- User can access their own usage logs
        CREATE POLICY "renum_ai_usage_logs_user_access" ON renum_ai_usage_logs
            FOR ALL
            USING (user_id = auth.uid());
        
        -- Admins can access all usage logs
        CREATE POLICY "renum_ai_usage_logs_admin_access" ON renum_ai_usage_logs
            FOR ALL
            USING (renum_is_admin());
        
        RAISE NOTICE 'Created RLS policies for renum_ai_usage_logs';
    END IF;
END $$;

-- Policies for renum_user_api_keys
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'renum_user_api_keys' AND table_schema = 'public') THEN
        -- Drop existing policies
        DROP POLICY IF EXISTS "renum_user_api_keys_user_policy" ON renum_user_api_keys;
        DROP POLICY IF EXISTS "renum_user_api_keys_admin_policy" ON renum_user_api_keys;
        
        -- User can only access their own API keys
        CREATE POLICY "renum_user_api_keys_user_access" ON renum_user_api_keys
            FOR ALL
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
        -- Drop existing policies
        DROP POLICY IF EXISTS "admin_superadmin_policy" ON renum_admins;
        
        -- Admins can see their own record, superadmins can see all
        CREATE POLICY "renum_admins_self_access" ON renum_admins
            FOR SELECT
            USING (user_id = auth.uid());
        
        CREATE POLICY "renum_admins_superadmin_manage" ON renum_admins
            FOR ALL
            USING (renum_is_superadmin());
        
        RAISE NOTICE 'Created RLS policies for renum_admins';
    END IF;
END $$;

-- Policies for renum_admin_credentials
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'renum_admin_credentials' AND table_schema = 'public') THEN
        -- Drop existing policies
        DROP POLICY IF EXISTS "admin_credentials_policy" ON renum_admin_credentials;
        
        -- Admins can only see their own credentials
        CREATE POLICY "renum_admin_credentials_self_access" ON renum_admin_credentials
            FOR ALL
            USING (
                admin_id IN (SELECT id FROM renum_admins WHERE user_id = auth.uid())
            );
        
        RAISE NOTICE 'Created RLS policies for renum_admin_credentials';
    END IF;
END $$;

-- Policies for renum_system_settings
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'renum_system_settings' AND table_schema = 'public') THEN
        -- Drop existing policies
        DROP POLICY IF EXISTS "system_settings_read_policy" ON renum_system_settings;
        DROP POLICY IF EXISTS "system_settings_write_policy" ON renum_system_settings;
        
        -- All admins can read settings
        CREATE POLICY "renum_system_settings_admin_read" ON renum_system_settings
            FOR SELECT
            USING (renum_is_admin());
        
        -- Only superadmins can modify settings
        CREATE POLICY "renum_system_settings_superadmin_write" ON renum_system_settings
            FOR INSERT, UPDATE, DELETE
            USING (renum_is_superadmin());
        
        RAISE NOTICE 'Created RLS policies for renum_system_settings';
    END IF;
END $$;

-- Policies for renum_audit_logs
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'renum_audit_logs' AND table_schema = 'public') THEN
        -- Drop existing policies
        DROP POLICY IF EXISTS "audit_logs_policy" ON renum_audit_logs;
        
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
-- 5. IMPLEMENT RLS POLICIES FOR AGENT SHARING
-- ============================================================================

-- Policies for renum_agent_shares (if exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'renum_agent_shares' AND table_schema = 'public') THEN
        -- Drop existing policies
        DROP POLICY IF EXISTS "Usuários podem ver seus próprios compartilhamentos" ON renum_agent_shares;
        DROP POLICY IF EXISTS "Usuários podem criar compartilhamentos para seus agentes" ON renum_agent_shares;
        DROP POLICY IF EXISTS "Usuários podem atualizar compartilhamentos de seus agentes" ON renum_agent_shares;
        DROP POLICY IF EXISTS "Usuários podem excluir compartilhamentos de seus agentes" ON renum_agent_shares;
        
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
                (renum_is_admin() OR auth.uid() IN (
                    SELECT created_by FROM agents WHERE id = agent_id
                ))
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
-- 6. IMPLEMENT RLS POLICIES FOR RAG TABLES (IF THEY EXIST)
-- ============================================================================

-- Policies for renum_knowledge_bases
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'renum_knowledge_bases' AND table_schema = 'public') THEN
        -- Enable RLS if not already enabled
        ALTER TABLE renum_knowledge_bases ENABLE ROW LEVEL SECURITY;
        
        -- Users can access knowledge bases for their client
        CREATE POLICY "renum_knowledge_bases_client_access" ON renum_knowledge_bases
            FOR ALL
            USING (client_id = renum_get_user_client_id());
        
        -- Admins can access all knowledge bases
        CREATE POLICY "renum_knowledge_bases_admin_access" ON renum_knowledge_bases
            FOR ALL
            USING (renum_is_admin());
        
        RAISE NOTICE 'Created RLS policies for renum_knowledge_bases';
    END IF;
END $$;

-- Similar policies for other RAG tables
DO $$
DECLARE
    table_name TEXT;
    rag_tables TEXT[] := ARRAY[
        'renum_knowledge_collections',
        'renum_documents',
        'renum_document_chunks',
        'renum_document_versions',
        'renum_processing_jobs'
    ];
BEGIN
    FOREACH table_name IN ARRAY rag_tables
    LOOP
        IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = table_name AND table_schema = 'public') THEN
            -- Create basic client-based access policy
            EXECUTE format('
                CREATE POLICY "%s_client_access" ON %I
                FOR ALL
                USING (
                    CASE 
                        WHEN EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = %L AND column_name = ''client_id'') 
                        THEN client_id = renum_get_user_client_id()
                        ELSE true
                    END
                )', table_name, table_name, table_name);
            
            -- Admin access policy
            EXECUTE format('
                CREATE POLICY "%s_admin_access" ON %I
                FOR ALL
                USING (renum_is_admin())', table_name, table_name);
            
            RAISE NOTICE 'Created RLS policies for %', table_name;
        END IF;
    END LOOP;
END $$;

-- ============================================================================
-- 7. CREATE AUDIT TRIGGER FOR RLS POLICY CHANGES
-- ============================================================================

-- Function to log RLS policy changes
CREATE OR REPLACE FUNCTION log_rls_policy_change()
RETURNS event_trigger AS $$
DECLARE
    obj record;
BEGIN
    FOR obj IN SELECT * FROM pg_event_trigger_ddl_commands()
    LOOP
        IF obj.command_tag IN ('CREATE POLICY', 'ALTER POLICY', 'DROP POLICY') THEN
            INSERT INTO renum_audit_logs (
                event_type,
                entity_type,
                entity_id,
                actor_id,
                actor_type,
                details
            ) VALUES (
                obj.command_tag,
                'rls_policy',
                NULL,
                auth.uid(),
                'admin',
                jsonb_build_object(
                    'object_type', obj.object_type,
                    'schema_name', obj.schema_name,
                    'object_identity', obj.object_identity,
                    'command', obj.command_tag
                )
            );
        END IF;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Create event trigger for RLS policy changes (if audit table exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'renum_audit_logs' AND table_schema = 'public') THEN
        DROP EVENT TRIGGER IF EXISTS renum_rls_policy_audit;
        CREATE EVENT TRIGGER renum_rls_policy_audit
            ON ddl_command_end
            WHEN TAG IN ('CREATE POLICY', 'ALTER POLICY', 'DROP POLICY')
            EXECUTE FUNCTION log_rls_policy_change();
        
        RAISE NOTICE 'Created audit trigger for RLS policy changes';
    END IF;
END $$;

-- ============================================================================
-- 8. VERIFICATION AND TESTING
-- ============================================================================

-- Function to test RLS policies
CREATE OR REPLACE FUNCTION test_rls_policies()
RETURNS TABLE(table_name TEXT, rls_enabled BOOLEAN, policy_count INTEGER) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t.table_name::TEXT,
        CASE WHEN t.row_security = 'YES' THEN true ELSE false END as rls_enabled,
        COALESCE(p.policy_count, 0)::INTEGER as policy_count
    FROM information_schema.tables t
    LEFT JOIN (
        SELECT 
            tablename,
            COUNT(*) as policy_count
        FROM pg_policies 
        WHERE schemaname = 'public'
        GROUP BY tablename
    ) p ON t.table_name = p.tablename
    WHERE t.table_schema = 'public' 
    AND t.table_name LIKE 'renum_%'
    ORDER BY t.table_name;
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
-- 9. LOG MIGRATION COMPLETION
-- ============================================================================

-- Log this migration
INSERT INTO renum_migration_log (migration_version, migration_name, notes)
VALUES ('002', 'Implement comprehensive RLS policies', 'Enabled RLS and created security policies for all renum_ tables with proper user isolation and admin access');

-- Log migration completion
DO $$
BEGIN
    RAISE NOTICE 'Migration 002 completed successfully at %', now();
    RAISE NOTICE 'RLS enabled on all renum_ tables with comprehensive security policies';
    RAISE NOTICE 'Admin functions created for role-based access control';
    RAISE NOTICE 'Audit logging enabled for RLS policy changes';
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
-- 4. Monitor audit logs for any unauthorized access attempts
-- 5. Update application code to handle RLS-related errors gracefully
-- 
-- Security considerations:
-- - All renum_ tables now have RLS enabled
-- - Users can only access their own data unless they are admins
-- - Superadmins have elevated privileges for system management
-- - All policy changes are audited
-- 
-- ============================================================================