-- Rollback Script: Rename tables back from renum_ prefix
-- Version: 001_rollback
-- Description: Rollback migration 001 - rename tables back to original names
-- Author: Sistema Renum Holistic Fixes
-- Date: 2025-07-28

-- ============================================================================
-- ROLLBACK INSTRUCTIONS
-- ============================================================================
-- This script will rollback migration 001 by renaming tables back to their
-- original names. Only run this if you need to undo the migration.
-- 
-- WARNING: Ensure all applications are stopped before running this rollback!
-- ============================================================================

BEGIN;

-- Set transaction isolation level for consistency
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;

-- Log rollback start
DO $$
BEGIN
    RAISE NOTICE 'Starting rollback of migration 001: Rename tables back from renum_ prefix at %', now();
END $$;

-- ============================================================================
-- 1. ROLLBACK RAG SYSTEM TABLES
-- ============================================================================

-- Rename renum_knowledge_bases back to knowledge_bases
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'renum_knowledge_bases' AND table_schema = 'public') THEN
        IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'knowledge_bases' AND table_schema = 'public') THEN
            ALTER TABLE public.renum_knowledge_bases RENAME TO knowledge_bases;
            RAISE NOTICE 'Rolled back renum_knowledge_bases to knowledge_bases';
        ELSE
            RAISE NOTICE 'Table knowledge_bases already exists, cannot rollback renum_knowledge_bases';
        END IF;
    ELSE
        RAISE NOTICE 'Table renum_knowledge_bases does not exist, skipping rollback';
    END IF;
END $$;

-- Rename renum_knowledge_collections back to knowledge_collections
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'renum_knowledge_collections' AND table_schema = 'public') THEN
        IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'knowledge_collections' AND table_schema = 'public') THEN
            ALTER TABLE public.renum_knowledge_collections RENAME TO knowledge_collections;
            RAISE NOTICE 'Rolled back renum_knowledge_collections to knowledge_collections';
        ELSE
            RAISE NOTICE 'Table knowledge_collections already exists, cannot rollback renum_knowledge_collections';
        END IF;
    ELSE
        RAISE NOTICE 'Table renum_knowledge_collections does not exist, skipping rollback';
    END IF;
END $$;

-- Rename renum_documents back to documents
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'renum_documents' AND table_schema = 'public') THEN
        IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'documents' AND table_schema = 'public') THEN
            ALTER TABLE public.renum_documents RENAME TO documents;
            RAISE NOTICE 'Rolled back renum_documents to documents';
        ELSE
            RAISE NOTICE 'Table documents already exists, cannot rollback renum_documents';
        END IF;
    ELSE
        RAISE NOTICE 'Table renum_documents does not exist, skipping rollback';
    END IF;
END $$;

-- Rename renum_document_chunks back to document_chunks
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'renum_document_chunks' AND table_schema = 'public') THEN
        IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'document_chunks' AND table_schema = 'public') THEN
            ALTER TABLE public.renum_document_chunks RENAME TO document_chunks;
            RAISE NOTICE 'Rolled back renum_document_chunks to document_chunks';
        ELSE
            RAISE NOTICE 'Table document_chunks already exists, cannot rollback renum_document_chunks';
        END IF;
    ELSE
        RAISE NOTICE 'Table renum_document_chunks does not exist, skipping rollback';
    END IF;
END $$;

-- Rename renum_document_versions back to document_versions
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'renum_document_versions' AND table_schema = 'public') THEN
        IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'document_versions' AND table_schema = 'public') THEN
            ALTER TABLE public.renum_document_versions RENAME TO document_versions;
            RAISE NOTICE 'Rolled back renum_document_versions to document_versions';
        ELSE
            RAISE NOTICE 'Table document_versions already exists, cannot rollback renum_document_versions';
        END IF;
    ELSE
        RAISE NOTICE 'Table renum_document_versions does not exist, skipping rollback';
    END IF;
END $$;

-- Rename renum_document_usage_stats back to document_usage_stats
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'renum_document_usage_stats' AND table_schema = 'public') THEN
        IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'document_usage_stats' AND table_schema = 'public') THEN
            ALTER TABLE public.renum_document_usage_stats RENAME TO document_usage_stats;
            RAISE NOTICE 'Rolled back renum_document_usage_stats to document_usage_stats';
        ELSE
            RAISE NOTICE 'Table document_usage_stats already exists, cannot rollback renum_document_usage_stats';
        END IF;
    ELSE
        RAISE NOTICE 'Table renum_document_usage_stats does not exist, skipping rollback';
    END IF;
END $$;

-- Rename renum_processing_jobs back to processing_jobs
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'renum_processing_jobs' AND table_schema = 'public') THEN
        IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'processing_jobs' AND table_schema = 'public') THEN
            ALTER TABLE public.renum_processing_jobs RENAME TO processing_jobs;
            RAISE NOTICE 'Rolled back renum_processing_jobs to processing_jobs';
        ELSE
            RAISE NOTICE 'Table processing_jobs already exists, cannot rollback renum_processing_jobs';
        END IF;
    ELSE
        RAISE NOTICE 'Table renum_processing_jobs does not exist, skipping rollback';
    END IF;
END $$;

-- ============================================================================
-- 2. ROLLBACK AGENT SYSTEM TABLES
-- ============================================================================

-- Rename renum_agents back to agents (only if it was renamed in the migration)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'renum_agents' AND table_schema = 'public') THEN
        -- Check if there's also a Suna Core agents table
        IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'agents' AND table_schema = 'public') THEN
            -- Check if this was originally a Renum-specific agents table
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'renum_agents' AND column_name = 'client_id' AND table_schema = 'public') THEN
                ALTER TABLE public.renum_agents RENAME TO agents;
                RAISE NOTICE 'Rolled back renum_agents to agents';
            ELSE
                RAISE NOTICE 'Table renum_agents does not appear to be original Renum agents table, skipping rollback';
            END IF;
        ELSE
            RAISE NOTICE 'Table agents already exists (likely Suna Core), cannot rollback renum_agents';
        END IF;
    ELSE
        RAISE NOTICE 'Table renum_agents does not exist, skipping rollback';
    END IF;
END $$;

-- ============================================================================
-- 3. VERIFICATION
-- ============================================================================

-- Verify rollback by checking for old table names
DO $$
DECLARE
    table_count INTEGER;
    original_tables TEXT[] := ARRAY[
        'knowledge_bases',
        'knowledge_collections', 
        'documents',
        'document_chunks',
        'document_versions',
        'document_usage_stats',
        'processing_jobs'
    ];
    table_name TEXT;
BEGIN
    RAISE NOTICE 'Verifying rollback...';
    
    FOREACH table_name IN ARRAY original_tables
    LOOP
        SELECT COUNT(*) INTO table_count
        FROM information_schema.tables 
        WHERE table_name = table_name 
        AND table_schema = 'public';
        
        IF table_count > 0 THEN
            RAISE NOTICE 'Table % restored ✓', table_name;
        ELSE
            RAISE NOTICE 'Table % not found (may not have been renamed originally)', table_name;
        END IF;
    END LOOP;
END $$;

-- ============================================================================
-- 4. UPDATE MIGRATION LOG
-- ============================================================================

-- Log the rollback
INSERT INTO renum_migration_log (migration_version, migration_name, status, notes)
VALUES ('001', 'Rollback: Rename tables back from renum_ prefix', 'rolled_back', 'Migration 001 has been rolled back - tables renamed back to original names');

-- Log rollback completion
DO $$
BEGIN
    RAISE NOTICE 'Rollback of migration 001 completed successfully at %', now();
    RAISE NOTICE 'Tables have been renamed back to their original names';
    RAISE NOTICE 'Foreign key constraints and indexes have been automatically updated';
    RAISE NOTICE 'RLS policies remain active on renamed tables';
    RAISE NOTICE 'Remember to update application code to use original table names';
END $$;

COMMIT;

-- ============================================================================
-- POST-ROLLBACK NOTES
-- ============================================================================
-- 
-- After running this rollback:
-- 1. Update application code to use original table names
-- 2. Update any stored procedures or functions that reference renum_ table names
-- 3. Update documentation and schema diagrams
-- 4. Test all application functionality
-- 5. Consider why the rollback was necessary and plan accordingly
-- 
-- ============================================================================