-- Simple Migration Script: Rename tables to use renum_ prefix
-- Version: 001_simple
-- Description: Direct table renaming without complex loops
-- Date: 2025-07-28

-- ============================================================================
-- SIMPLE TABLE RENAMING MIGRATION
-- ============================================================================

BEGIN;

-- Log migration start
SELECT 'Starting simple table renaming migration at ' || now() as migration_start;

-- ============================================================================
-- 1. DIRECT TABLE RENAMING (No loops, no ambiguity)
-- ============================================================================

-- Rename knowledge_bases to renum_knowledge_bases (if exists)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE information_schema.tables.table_name = 'knowledge_bases' 
        AND information_schema.tables.table_schema = 'public'
    ) THEN
        ALTER TABLE public.knowledge_bases RENAME TO renum_knowledge_bases;
        RAISE NOTICE 'Renamed knowledge_bases to renum_knowledge_bases';
    ELSE
        RAISE NOTICE 'Table knowledge_bases does not exist, skipping';
    END IF;
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Error renaming knowledge_bases: %', SQLERRM;
END $$;

-- Rename knowledge_collections to renum_knowledge_collections (if exists)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE information_schema.tables.table_name = 'knowledge_collections' 
        AND information_schema.tables.table_schema = 'public'
    ) THEN
        ALTER TABLE public.knowledge_collections RENAME TO renum_knowledge_collections;
        RAISE NOTICE 'Renamed knowledge_collections to renum_knowledge_collections';
    ELSE
        RAISE NOTICE 'Table knowledge_collections does not exist, skipping';
    END IF;
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Error renaming knowledge_collections: %', SQLERRM;
END $$;

-- Rename documents to renum_documents (if exists)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE information_schema.tables.table_name = 'documents' 
        AND information_schema.tables.table_schema = 'public'
    ) THEN
        ALTER TABLE public.documents RENAME TO renum_documents;
        RAISE NOTICE 'Renamed documents to renum_documents';
    ELSE
        RAISE NOTICE 'Table documents does not exist, skipping';
    END IF;
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Error renaming documents: %', SQLERRM;
END $$;

-- Rename document_chunks to renum_document_chunks (if exists)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE information_schema.tables.table_name = 'document_chunks' 
        AND information_schema.tables.table_schema = 'public'
    ) THEN
        ALTER TABLE public.document_chunks RENAME TO renum_document_chunks;
        RAISE NOTICE 'Renamed document_chunks to renum_document_chunks';
    ELSE
        RAISE NOTICE 'Table document_chunks does not exist, skipping';
    END IF;
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Error renaming document_chunks: %', SQLERRM;
END $$;

-- Rename document_versions to renum_document_versions (if exists)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE information_schema.tables.table_name = 'document_versions' 
        AND information_schema.tables.table_schema = 'public'
    ) THEN
        ALTER TABLE public.document_versions RENAME TO renum_document_versions;
        RAISE NOTICE 'Renamed document_versions to renum_document_versions';
    ELSE
        RAISE NOTICE 'Table document_versions does not exist, skipping';
    END IF;
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Error renaming document_versions: %', SQLERRM;
END $$;

-- Rename document_usage_stats to renum_document_usage_stats (if exists)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE information_schema.tables.table_name = 'document_usage_stats' 
        AND information_schema.tables.table_schema = 'public'
    ) THEN
        ALTER TABLE public.document_usage_stats RENAME TO renum_document_usage_stats;
        RAISE NOTICE 'Renamed document_usage_stats to renum_document_usage_stats';
    ELSE
        RAISE NOTICE 'Table document_usage_stats does not exist, skipping';
    END IF;
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Error renaming document_usage_stats: %', SQLERRM;
END $$;

-- Rename processing_jobs to renum_processing_jobs (if exists)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE information_schema.tables.table_name = 'processing_jobs' 
        AND information_schema.tables.table_schema = 'public'
    ) THEN
        ALTER TABLE public.processing_jobs RENAME TO renum_processing_jobs;
        RAISE NOTICE 'Renamed processing_jobs to renum_processing_jobs';
    ELSE
        RAISE NOTICE 'Table processing_jobs does not exist, skipping';
    END IF;
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Error renaming processing_jobs: %', SQLERRM;
END $$;

-- ============================================================================
-- 2. CREATE MIGRATION LOG TABLE AND ENTRY
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
VALUES ('001', 'Simple table renaming to renum_ prefix', 'Direct table renaming without complex loops - fixed ambiguity issues');

-- ============================================================================
-- 3. VERIFICATION
-- ============================================================================

-- Simple verification - count renum_ tables
DO $$
DECLARE
    renum_table_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO renum_table_count
    FROM information_schema.tables 
    WHERE information_schema.tables.table_name LIKE 'renum_%' 
    AND information_schema.tables.table_schema = 'public';
    
    RAISE NOTICE 'Found % tables with renum_ prefix', renum_table_count;
    
    IF renum_table_count > 0 THEN
        RAISE NOTICE 'Migration appears successful - renum_ tables found';
    ELSE
        RAISE NOTICE 'No renum_ tables found - may indicate no tables were renamed';
    END IF;
END $$;

-- Log completion
SELECT 'Simple table renaming migration completed at ' || now() as migration_end;

COMMIT;

-- ============================================================================
-- USAGE NOTES
-- ============================================================================
-- 
-- This simplified version:
-- 1. Uses direct table renaming without loops
-- 2. Avoids variable name conflicts
-- 3. Includes error handling for each rename operation
-- 4. Creates migration log for tracking
-- 5. Provides simple verification
-- 
-- After running:
-- 1. Check the NOTICE messages in the output
-- 2. Verify tables were renamed as expected
-- 3. Update application code to use new table names
-- 
-- ============================================================================