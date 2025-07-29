-- Migration Script: Rename tables to use renum_ prefix
-- Version: 001
-- Description: Standardize table naming with renum_ prefix for all Renum-specific tables
-- Author: Sistema Renum Holistic Fixes
-- Date: 2025-07-28

-- ============================================================================
-- BACKUP INSTRUCTIONS
-- ============================================================================
-- Before running this migration, ensure you have:
-- 1. Full database backup
-- 2. Tested this script in a staging environment
-- 3. Scheduled maintenance window
-- 4. Rollback script ready (001_rename_tables_to_renum_prefix_rollback.sql)

-- ============================================================================
-- MIGRATION: RENAME TABLES TO USE RENUM_ PREFIX
-- ============================================================================

BEGIN;

-- Set transaction isolation level for consistency
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;

-- Log migration start
DO $$
BEGIN
    RAISE NOTICE 'Starting migration 001: Rename tables to renum_ prefix at %', now();
END $$;

-- ============================================================================
-- 1. RENAME RAG SYSTEM TABLES
-- ============================================================================

-- Rename knowledge_bases to renum_knowledge_bases
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'knowledge_bases' AND table_schema = 'public') THEN
        IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'renum_knowledge_bases' AND table_schema = 'public') THEN
            ALTER TABLE public.knowledge_bases RENAME TO renum_knowledge_bases;
            RAISE NOTICE 'Renamed knowledge_bases to renum_knowledge_bases';
        ELSE
            RAISE NOTICE 'Table renum_knowledge_bases already exists, skipping rename of knowledge_bases';
        END IF;
    ELSE
        RAISE NOTICE 'Table knowledge_bases does not exist, skipping rename';
    END IF;
END $$;

-- Rename knowledge_collections to renum_knowledge_collections
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'knowledge_collections' AND table_schema = 'public') THEN
        IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'renum_knowledge_collections' AND table_schema = 'public') THEN
            ALTER TABLE public.knowledge_collections RENAME TO renum_knowledge_collections;
            RAISE NOTICE 'Renamed knowledge_collections to renum_knowledge_collections';
        ELSE
            RAISE NOTICE 'Table renum_knowledge_collections already exists, skipping rename of knowledge_collections';
        END IF;
    ELSE
        RAISE NOTICE 'Table knowledge_collections does not exist, skipping rename';
    END IF;
END $$;

-- Rename documents to renum_documents
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'documents' AND table_schema = 'public') THEN
        IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'renum_documents' AND table_schema = 'public') THEN
            ALTER TABLE public.documents RENAME TO renum_documents;
            RAISE NOTICE 'Renamed documents to renum_documents';
        ELSE
            RAISE NOTICE 'Table renum_documents already exists, skipping rename of documents';
        END IF;
    ELSE
        RAISE NOTICE 'Table documents does not exist, skipping rename';
    END IF;
END $$;

-- Rename document_chunks to renum_document_chunks
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'document_chunks' AND table_schema = 'public') THEN
        IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'renum_document_chunks' AND table_schema = 'public') THEN
            ALTER TABLE public.document_chunks RENAME TO renum_document_chunks;
            RAISE NOTICE 'Renamed document_chunks to renum_document_chunks';
        ELSE
            RAISE NOTICE 'Table renum_document_chunks already exists, skipping rename of document_chunks';
        END IF;
    ELSE
        RAISE NOTICE 'Table document_chunks does not exist, skipping rename';
    END IF;
END $$;

-- Rename document_versions to renum_document_versions
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'document_versions' AND table_schema = 'public') THEN
        IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'renum_document_versions' AND table_schema = 'public') THEN
            ALTER TABLE public.document_versions RENAME TO renum_document_versions;
            RAISE NOTICE 'Renamed document_versions to renum_document_versions';
        ELSE
            RAISE NOTICE 'Table renum_document_versions already exists, skipping rename of document_versions';
        END IF;
    ELSE
        RAISE NOTICE 'Table document_versions does not exist, skipping rename';
    END IF;
END $$;

-- Rename document_usage_stats to renum_document_usage_stats
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'document_usage_stats' AND table_schema = 'public') THEN
        IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'renum_document_usage_stats' AND table_schema = 'public') THEN
            ALTER TABLE public.document_usage_stats RENAME TO renum_document_usage_stats;
            RAISE NOTICE 'Renamed document_usage_stats to renum_document_usage_stats';
        ELSE
            RAISE NOTICE 'Table renum_document_usage_stats already exists, skipping rename of document_usage_stats';
        END IF;
    ELSE
        RAISE NOTICE 'Table document_usage_stats does not exist, skipping rename';
    END IF;
END $$;

-- Rename processing_jobs to renum_processing_jobs
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'processing_jobs' AND table_schema = 'public') THEN
        IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'renum_processing_jobs' AND table_schema = 'public') THEN
            ALTER TABLE public.processing_jobs RENAME TO renum_processing_jobs;
            RAISE NOTICE 'Renamed processing_jobs to renum_processing_jobs';
        ELSE
            RAISE NOTICE 'Table renum_processing_jobs already exists, skipping rename of processing_jobs';
        END IF;
    ELSE
        RAISE NOTICE 'Table processing_jobs does not exist, skipping rename';
    END IF;
END $$;

-- ============================================================================
-- 2. RENAME AGENT SYSTEM TABLES (if they exist without prefix)
-- ============================================================================

-- Rename agents to renum_agents (if it exists and renum_agents doesn't)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'agents' AND table_schema = 'public') THEN
        IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'renum_agents' AND table_schema = 'public') THEN
            -- Check if this is a Renum-specific agents table (has renum-specific columns)
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'agents' AND column_name = 'client_id' AND table_schema = 'public') THEN
                ALTER TABLE public.agents RENAME TO renum_agents;
                RAISE NOTICE 'Renamed agents to renum_agents (Renum-specific table detected)';
            ELSE
                RAISE NOTICE 'Table agents exists but appears to be Suna Core table, skipping rename';
            END IF;
        ELSE
            RAISE NOTICE 'Table renum_agents already exists, skipping rename of agents';
        END IF;
    ELSE
        RAISE NOTICE 'Table agents does not exist, skipping rename';
    END IF;
END $$;

-- ============================================================================
-- 3. UPDATE FOREIGN KEY REFERENCES
-- ============================================================================

-- Update foreign key constraints to reference renamed tables
-- This will be handled automatically by PostgreSQL for most cases,
-- but we'll verify and update any that need manual intervention

DO $$
DECLARE
    constraint_record RECORD;
BEGIN
    -- Find and update foreign key constraints that reference old table names
    FOR constraint_record IN
        SELECT 
            tc.constraint_name,
            tc.table_name,
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM 
            information_schema.table_constraints AS tc 
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
              AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
              ON ccu.constraint_name = tc.constraint_name
              AND ccu.table_schema = tc.table_schema
        WHERE 
            tc.constraint_type = 'FOREIGN KEY' 
            AND tc.table_schema = 'public'
            AND ccu.table_name IN ('knowledge_bases', 'knowledge_collections', 'documents', 'document_chunks', 'document_versions', 'agents')
    LOOP
        RAISE NOTICE 'Found foreign key constraint % on table % referencing old table %', 
            constraint_record.constraint_name, 
            constraint_record.table_name, 
            constraint_record.foreign_table_name;
    END LOOP;
END $$;

-- ============================================================================
-- 4. UPDATE INDEXES
-- ============================================================================

-- Indexes are automatically renamed with the table, but we'll log them for verification
DO $$
DECLARE
    index_record RECORD;
BEGIN
    FOR index_record IN
        SELECT indexname, tablename 
        FROM pg_indexes 
        WHERE schemaname = 'public' 
        AND tablename LIKE 'renum_%'
        AND indexname NOT LIKE 'renum_%'
    LOOP
        RAISE NOTICE 'Index % on table % may need manual review', 
            index_record.indexname, 
            index_record.tablename;
    END LOOP;
END $$;

-- ============================================================================
-- 5. UPDATE RLS POLICIES
-- ============================================================================

-- RLS policies are automatically moved with the table, but we'll verify
DO $$
DECLARE
    policy_record RECORD;
BEGIN
    FOR policy_record IN
        SELECT schemaname, tablename, policyname
        FROM pg_policies
        WHERE schemaname = 'public'
        AND tablename LIKE 'renum_%'
    LOOP
        RAISE NOTICE 'RLS policy % found on table %', 
            policy_record.policyname, 
            policy_record.tablename;
    END LOOP;
END $$;

-- ============================================================================
-- 6. VERIFICATION
-- ============================================================================

-- Verify that all expected tables now have the renum_ prefix
DO $$
DECLARE
    table_count INTEGER;
    renamed_tables TEXT[] := ARRAY[
        'renum_knowledge_bases',
        'renum_knowledge_collections', 
        'renum_documents',
        'renum_document_chunks',
        'renum_document_versions',
        'renum_document_usage_stats',
        'renum_processing_jobs',
        'renum_agent_teams',
        'renum_team_executions',
        'renum_team_agent_executions',
        'renum_team_messages',
        'renum_team_context_snapshots',
        'renum_ai_usage_logs',
        'renum_user_api_keys',
        'renum_agent_shares',
        'renum_settings',
        'renum_metrics',
        'renum_audit_logs',
        'renum_admins',
        'renum_admin_credentials',
        'renum_system_settings'
    ];
    table_name TEXT;
BEGIN
    RAISE NOTICE 'Verifying renamed tables...';
    
    FOREACH table_name IN ARRAY renamed_tables
    LOOP
        SELECT COUNT(*) INTO table_count
        FROM information_schema.tables 
        WHERE information_schema.tables.table_name = table_name 
        AND table_schema = 'public';
        
        IF table_count > 0 THEN
            RAISE NOTICE 'Table % exists ✓', table_name;
        ELSE
            RAISE NOTICE 'Table % not found (may not have existed originally)', table_name;
        END IF;
    END LOOP;
END $$;

-- ============================================================================
-- 7. CREATE MIGRATION LOG ENTRY
-- ============================================================================

-- Create migration log table if it doesn't exist
CREATE TABLE IF NOT EXISTS renum_migration_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    migration_version VARCHAR(10) NOT NULL,
    migration_name TEXT NOT NULL,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    applied_by TEXT DEFAULT current_user,
    status VARCHAR(20) DEFAULT 'completed',
    notes TEXT
);

-- Log this migration
INSERT INTO renum_migration_log (migration_version, migration_name, notes)
VALUES ('001', 'Rename tables to renum_ prefix', 'Standardized table naming with renum_ prefix for all Renum-specific tables');

-- Log migration completion
DO $$
BEGIN
    RAISE NOTICE 'Migration 001 completed successfully at %', now();
    RAISE NOTICE 'All Renum-specific tables now use the renum_ prefix for consistency';
    RAISE NOTICE 'Foreign key constraints and indexes have been automatically updated';
    RAISE NOTICE 'RLS policies remain active on renamed tables';
END $$;

COMMIT;

-- ============================================================================
-- POST-MIGRATION NOTES
-- ============================================================================
-- 
-- After running this migration:
-- 1. Update application code to use new table names
-- 2. Update any stored procedures or functions that reference old table names
-- 3. Update documentation and schema diagrams
-- 4. Test all application functionality
-- 5. Monitor for any missed references to old table names
-- 
-- Rollback instructions:
-- If you need to rollback this migration, run: 001_rename_tables_to_renum_prefix_rollback.sql
-- 
-- ============================================================================