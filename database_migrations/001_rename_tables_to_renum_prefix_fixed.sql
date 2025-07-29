-- Migration Script: Rename tables to use renum_ prefix (FIXED VERSION)
-- Version: 001_fixed
-- Description: Standardize table naming with renum_ prefix for all Renum-specific tables
-- Author: Sistema Renum Holistic Fixes
-- Date: 2025-07-28

-- ============================================================================
-- MIGRATION: RENAME TABLES TO USE RENUM_ PREFIX (FIXED)
-- ============================================================================

BEGIN;

-- Set transaction isolation level for consistency
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;

-- Log migration start
DO $$
BEGIN
    RAISE NOTICE 'Starting migration 001_fixed: Rename tables to renum_ prefix at %', now();
END $$;

-- ============================================================================
-- 1. RENAME RAG SYSTEM TABLES (FIXED VERSION)
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
-- 2. CREATE MIGRATION LOG TABLE IF NOT EXISTS
-- ============================================================================

-- Create migration log table
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
VALUES ('001', 'Rename tables to renum_ prefix (fixed)', 'Standardized table naming with renum_ prefix for all Renum-specific tables - fixed version');

-- Log migration completion
DO $$
BEGIN
    RAISE NOTICE 'Migration 001_fixed completed successfully at %', now();
    RAISE NOTICE 'Tables renamed to use renum_ prefix where they existed';
END $$;

COMMIT;

-- ============================================================================
-- POST-MIGRATION VERIFICATION
-- ============================================================================

-- Show renamed tables
DO $$
DECLARE
    table_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables 
    WHERE table_name LIKE 'renum_%' 
    AND table_schema = 'public';
    
    RAISE NOTICE 'Found % tables with renum_ prefix after migration', table_count;
END $$;