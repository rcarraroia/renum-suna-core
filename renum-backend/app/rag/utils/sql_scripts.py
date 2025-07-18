"""
SQL scripts for the RAG module.

This module contains SQL scripts for creating tables and functions in the database.
"""

# Create tables
CREATE_TABLES_SQL = """
-- Knowledge bases table
CREATE TABLE IF NOT EXISTS knowledge_bases (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    client_id UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL
);

-- Knowledge collections table
CREATE TABLE IF NOT EXISTS knowledge_collections (
    id UUID PRIMARY KEY,
    knowledge_base_id UUID NOT NULL REFERENCES knowledge_bases(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL
);

-- Documents table
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY,
    collection_id UUID NOT NULL REFERENCES knowledge_collections(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    source_type TEXT NOT NULL,
    source_url TEXT,
    file_type TEXT,
    file_size INTEGER,
    status TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL
);

-- Document chunks table
CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY,
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    metadata JSONB,
    embedding_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL
);

-- Document versions table
CREATE TABLE IF NOT EXISTS document_versions (
    id UUID PRIMARY KEY,
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    change_type TEXT NOT NULL,
    changed_by UUID,
    change_description TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL
);

-- Document usage stats table
CREATE TABLE IF NOT EXISTS document_usage_stats (
    id UUID PRIMARY KEY,
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_id UUID REFERENCES document_chunks(id) ON DELETE CASCADE,
    agent_id UUID,
    client_id UUID NOT NULL,
    usage_count INTEGER NOT NULL DEFAULT 0,
    last_used_at TIMESTAMP WITH TIME ZONE,
    first_used_at TIMESTAMP WITH TIME ZONE NOT NULL
);

-- Retrieval feedback table
CREATE TABLE IF NOT EXISTS retrieval_feedback (
    id UUID PRIMARY KEY,
    thread_id UUID NOT NULL,
    message_id UUID NOT NULL,
    chunk_id UUID NOT NULL REFERENCES document_chunks(id) ON DELETE CASCADE,
    relevance_score INTEGER NOT NULL,
    user_id UUID,
    feedback_text TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL
);

-- Processing jobs table
CREATE TABLE IF NOT EXISTS processing_jobs (
    id UUID PRIMARY KEY,
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    status TEXT NOT NULL,
    progress FLOAT NOT NULL,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL
);

-- Client plans table
CREATE TABLE IF NOT EXISTS client_plans (
    id UUID PRIMARY KEY,
    client_id UUID NOT NULL,
    plan_type TEXT NOT NULL,
    max_documents INTEGER,
    max_storage_mb INTEGER,
    max_queries_per_day INTEGER,
    current_usage JSONB NOT NULL,
    plan_start_date TIMESTAMP WITH TIME ZONE NOT NULL,
    plan_end_date TIMESTAMP WITH TIME ZONE
);
"""

# Create functions
CREATE_FUNCTIONS_SQL = """
-- Function to count collections in a knowledge base
CREATE OR REPLACE FUNCTION count_collections_in_kb(p_knowledge_base_id UUID)
RETURNS TABLE (count BIGINT) AS $$
BEGIN
    RETURN QUERY
    SELECT COUNT(*)
    FROM knowledge_collections
    WHERE knowledge_base_id = p_knowledge_base_id;
END;
$$ LANGUAGE plpgsql;

-- Function to count documents in a knowledge base
CREATE OR REPLACE FUNCTION count_documents_in_kb(p_knowledge_base_id UUID)
RETURNS TABLE (count BIGINT) AS $$
BEGIN
    RETURN QUERY
    SELECT COUNT(d.*)
    FROM documents d
    JOIN knowledge_collections c ON d.collection_id = c.id
    WHERE c.knowledge_base_id = p_knowledge_base_id;
END;
$$ LANGUAGE plpgsql;

-- Function to count chunks in a knowledge base
CREATE OR REPLACE FUNCTION count_chunks_in_kb(p_knowledge_base_id UUID)
RETURNS TABLE (count BIGINT) AS $$
BEGIN
    RETURN QUERY
    SELECT COUNT(ch.*)
    FROM document_chunks ch
    JOIN documents d ON ch.document_id = d.id
    JOIN knowledge_collections c ON d.collection_id = c.id
    WHERE c.knowledge_base_id = p_knowledge_base_id;
END;
$$ LANGUAGE plpgsql;

-- Function to count documents in a collection
CREATE OR REPLACE FUNCTION count_documents_in_collection(p_collection_id UUID)
RETURNS TABLE (count BIGINT) AS $$
BEGIN
    RETURN QUERY
    SELECT COUNT(*)
    FROM documents
    WHERE collection_id = p_collection_id;
END;
$$ LANGUAGE plpgsql;

-- Function to count chunks in a collection
CREATE OR REPLACE FUNCTION count_chunks_in_collection(p_collection_id UUID)
RETURNS TABLE (count BIGINT) AS $$
BEGIN
    RETURN QUERY
    SELECT COUNT(ch.*)
    FROM document_chunks ch
    JOIN documents d ON ch.document_id = d.id
    WHERE d.collection_id = p_collection_id;
END;
$$ LANGUAGE plpgsql;

-- Function to count chunks in a document
CREATE OR REPLACE FUNCTION count_chunks_in_document(p_document_id UUID)
RETURNS TABLE (count BIGINT) AS $$
BEGIN
    RETURN QUERY
    SELECT COUNT(*)
    FROM document_chunks
    WHERE document_id = p_document_id;
END;
$$ LANGUAGE plpgsql;

-- Function to count versions in a document
CREATE OR REPLACE FUNCTION count_versions_in_document(p_document_id UUID)
RETURNS TABLE (count BIGINT) AS $$
BEGIN
    RETURN QUERY
    SELECT COUNT(*)
    FROM document_versions
    WHERE document_id = p_document_id;
END;
$$ LANGUAGE plpgsql;

-- Function to get document usage stats
CREATE OR REPLACE FUNCTION get_document_usage_stats(p_document_id UUID)
RETURNS TABLE (
    usage_count BIGINT,
    last_used_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT SUM(dus.usage_count)::BIGINT, MAX(dus.last_used_at)
    FROM document_usage_stats dus
    WHERE dus.document_id = p_document_id;
END;
$$ LANGUAGE plpgsql;

-- Function to delete embeddings
CREATE OR REPLACE FUNCTION delete_embeddings(p_embedding_ids TEXT[])
RETURNS VOID AS $$
BEGIN
    -- This is a placeholder. The actual implementation depends on the vector database used.
    -- For Supabase Vector, you would use the vector extension functions.
    -- For external vector databases, you would implement the deletion logic in the application code.
    RETURN;
END;
$$ LANGUAGE plpgsql;
"""

# Create RLS policies
CREATE_RLS_POLICIES_SQL = """
-- Enable RLS on tables
ALTER TABLE knowledge_bases ENABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge_collections ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_usage_stats ENABLE ROW LEVEL SECURITY;
ALTER TABLE retrieval_feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE processing_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE client_plans ENABLE ROW LEVEL SECURITY;

-- Create policies for knowledge_bases
CREATE POLICY knowledge_bases_select ON knowledge_bases
    FOR SELECT
    USING (client_id = auth.uid() OR client_id IN (
        SELECT client_id FROM user_clients WHERE user_id = auth.uid()
    ));

CREATE POLICY knowledge_bases_insert ON knowledge_bases
    FOR INSERT
    WITH CHECK (client_id = auth.uid() OR client_id IN (
        SELECT client_id FROM user_clients WHERE user_id = auth.uid()
    ));

CREATE POLICY knowledge_bases_update ON knowledge_bases
    FOR UPDATE
    USING (client_id = auth.uid() OR client_id IN (
        SELECT client_id FROM user_clients WHERE user_id = auth.uid()
    ));

CREATE POLICY knowledge_bases_delete ON knowledge_bases
    FOR DELETE
    USING (client_id = auth.uid() OR client_id IN (
        SELECT client_id FROM user_clients WHERE user_id = auth.uid()
    ));

-- Create policies for knowledge_collections
CREATE POLICY knowledge_collections_select ON knowledge_collections
    FOR SELECT
    USING (knowledge_base_id IN (
        SELECT id FROM knowledge_bases
        WHERE client_id = auth.uid() OR client_id IN (
            SELECT client_id FROM user_clients WHERE user_id = auth.uid()
        )
    ));

CREATE POLICY knowledge_collections_insert ON knowledge_collections
    FOR INSERT
    WITH CHECK (knowledge_base_id IN (
        SELECT id FROM knowledge_bases
        WHERE client_id = auth.uid() OR client_id IN (
            SELECT client_id FROM user_clients WHERE user_id = auth.uid()
        )
    ));

CREATE POLICY knowledge_collections_update ON knowledge_collections
    FOR UPDATE
    USING (knowledge_base_id IN (
        SELECT id FROM knowledge_bases
        WHERE client_id = auth.uid() OR client_id IN (
            SELECT client_id FROM user_clients WHERE user_id = auth.uid()
        )
    ));

CREATE POLICY knowledge_collections_delete ON knowledge_collections
    FOR DELETE
    USING (knowledge_base_id IN (
        SELECT id FROM knowledge_bases
        WHERE client_id = auth.uid() OR client_id IN (
            SELECT client_id FROM user_clients WHERE user_id = auth.uid()
        )
    ));

-- Similar policies for other tables would be created here
"""

# Agent integration SQL functions
AGENT_INTEGRATION_SQL = """
-- Function to get knowledge bases for a client
CREATE OR REPLACE FUNCTION get_client_knowledge_bases(p_client_id UUID)
RETURNS TABLE (
    id UUID,
    name TEXT,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        kb.id,
        kb.name,
        kb.description,
        kb.created_at,
        kb.updated_at
    FROM 
        knowledge_bases kb
    WHERE 
        kb.client_id = p_client_id;
END;
$$ LANGUAGE plpgsql;

-- Function to get collections for knowledge bases
CREATE OR REPLACE FUNCTION get_collections_for_knowledge_bases(p_knowledge_base_ids UUID[])
RETURNS TABLE (
    id UUID,
    knowledge_base_id UUID,
    name TEXT,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        kc.id,
        kc.knowledge_base_id,
        kc.name,
        kc.description,
        kc.created_at,
        kc.updated_at
    FROM 
        knowledge_collections kc
    WHERE 
        kc.knowledge_base_id = ANY(p_knowledge_base_ids);
END;
$$ LANGUAGE plpgsql;

-- Function to search embeddings
CREATE OR REPLACE FUNCTION search_embeddings(
    p_query_embedding VECTOR,
    p_top_k INTEGER DEFAULT 5,
    p_collection_ids UUID[] DEFAULT NULL,
    p_filters JSONB DEFAULT NULL
)
RETURNS TABLE (
    chunk_id UUID,
    document_id UUID,
    content TEXT,
    chunk_index INTEGER,
    metadata JSONB,
    similarity FLOAT,
    created_at TIMESTAMP WITH TIME ZONE,
    document_name TEXT,
    source_type TEXT,
    collection_id UUID,
    collection_name TEXT
) AS $$
DECLARE
    filter_condition TEXT := '';
BEGIN
    -- Build filter condition if filters are provided
    IF p_filters IS NOT NULL THEN
        -- Example: filter by metadata fields
        IF p_filters ? 'metadata' THEN
            filter_condition := filter_condition || ' AND dc.metadata @> ' || quote_literal(p_filters->'metadata');
        END IF;
        
        -- Example: filter by document status
        IF p_filters ? 'status' THEN
            filter_condition := filter_condition || ' AND d.status = ' || quote_literal(p_filters->>'status');
        END IF;
    END IF;

    RETURN QUERY EXECUTE '
        SELECT 
            dc.id AS chunk_id,
            dc.document_id,
            dc.content,
            dc.chunk_index,
            dc.metadata,
            1 - (dc.embedding <=> $1) AS similarity,
            dc.created_at,
            d.name AS document_name,
            d.source_type,
            d.collection_id,
            kc.name AS collection_name
        FROM 
            document_chunks dc
            JOIN documents d ON dc.document_id = d.id
            JOIN knowledge_collections kc ON d.collection_id = kc.id
        WHERE 
            dc.embedding IS NOT NULL
            ' || CASE WHEN p_collection_ids IS NOT NULL THEN 
                  ' AND d.collection_id = ANY($2)'
                ELSE 
                  ''
                END || 
            filter_condition || '
        ORDER BY 
            dc.embedding <=> $1
        LIMIT $3'
    USING 
        p_query_embedding,
        p_collection_ids,
        p_top_k;
END;
$$ LANGUAGE plpgsql;

-- Function to track chunk usage
CREATE OR REPLACE FUNCTION track_chunk_usage(
    p_chunk_id UUID,
    p_agent_id UUID,
    p_client_id UUID
)
RETURNS VOID AS $$
DECLARE
    v_document_id UUID;
BEGIN
    -- Get document ID for the chunk
    SELECT document_id INTO v_document_id
    FROM document_chunks
    WHERE id = p_chunk_id;
    
    IF v_document_id IS NULL THEN
        RAISE EXCEPTION 'Chunk not found: %', p_chunk_id;
    END IF;
    
    -- Update usage stats if entry exists
    UPDATE document_usage_stats
    SET 
        usage_count = usage_count + 1,
        last_used_at = NOW()
    WHERE 
        document_id = v_document_id AND
        chunk_id = p_chunk_id AND
        client_id = p_client_id AND
        (agent_id = p_agent_id OR (agent_id IS NULL AND p_agent_id IS NULL));
    
    -- Insert new entry if not exists
    IF NOT FOUND THEN
        INSERT INTO document_usage_stats (
            document_id,
            chunk_id,
            agent_id,
            client_id,
            usage_count,
            last_used_at,
            first_used_at
        ) VALUES (
            v_document_id,
            p_chunk_id,
            p_agent_id,
            p_client_id,
            1,
            NOW(),
            NOW()
        );
    END IF;
END;
$$ LANGUAGE plpgsql;
"""

# Initialize database
INITIALIZE_DATABASE_SQL = CREATE_TABLES_SQL + CREATE_FUNCTIONS_SQL + CREATE_RLS_POLICIES_SQL + AGENT_INTEGRATION_SQL