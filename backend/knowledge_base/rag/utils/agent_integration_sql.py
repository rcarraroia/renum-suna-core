"""
SQL functions for agent integration with the RAG module.

This module contains SQL functions needed for the agent integration with the RAG module.
"""

# Function to get knowledge bases for a client
GET_CLIENT_KNOWLEDGE_BASES_SQL = """
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
"""

# Function to get collections for knowledge bases
GET_COLLECTIONS_FOR_KNOWLEDGE_BASES_SQL = """
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
"""

# Function to search embeddings
SEARCH_EMBEDDINGS_SQL = """
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
"""

# Function to filter chunks by metadata
FILTER_CHUNKS_SQL = """
CREATE OR REPLACE FUNCTION filter_chunks(
    p_filters JSONB,
    p_top_k INTEGER DEFAULT 5,
    p_collection_ids UUID[] DEFAULT NULL
)
RETURNS TABLE (
    chunk_id UUID,
    document_id UUID,
    content TEXT,
    chunk_index INTEGER,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE,
    document_name TEXT,
    source_type TEXT,
    collection_id UUID,
    collection_name TEXT
) AS $$
DECLARE
    filter_condition TEXT := '';
BEGIN
    -- Build filter condition from filters
    IF p_filters ? 'metadata' THEN
        filter_condition := filter_condition || ' AND dc.metadata @> ' || quote_literal(p_filters->'metadata');
    END IF;
    
    IF p_filters ? 'status' THEN
        filter_condition := filter_condition || ' AND d.status = ' || quote_literal(p_filters->>'status');
    END IF;
    
    IF p_filters ? 'document_id' THEN
        filter_condition := filter_condition || ' AND d.id = ' || quote_literal(p_filters->>'document_id');
    END IF;
    
    IF p_filters ? 'source_type' THEN
        filter_condition := filter_condition || ' AND d.source_type = ' || quote_literal(p_filters->>'source_type');
    END IF;

    RETURN QUERY EXECUTE '
        SELECT 
            dc.id AS chunk_id,
            dc.document_id,
            dc.content,
            dc.chunk_index,
            dc.metadata,
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
            1=1
            ' || CASE WHEN p_collection_ids IS NOT NULL THEN 
                  ' AND d.collection_id = ANY($1)'
                ELSE 
                  ''
                END || 
            filter_condition || '
        LIMIT $2'
    USING 
        p_collection_ids,
        p_top_k;
END;
$$ LANGUAGE plpgsql;
"""

# Function to track chunk usage
TRACK_CHUNK_USAGE_SQL = """
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

# Combine all SQL functions
AGENT_INTEGRATION_SQL = (
    GET_CLIENT_KNOWLEDGE_BASES_SQL +
    GET_COLLECTIONS_FOR_KNOWLEDGE_BASES_SQL +
    SEARCH_EMBEDDINGS_SQL +
    FILTER_CHUNKS_SQL +
    TRACK_CHUNK_USAGE_SQL
)