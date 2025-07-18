"""
Script to initialize the RAG database tables in Supabase.

This script connects to Supabase and creates the necessary tables, functions, and policies
for the RAG module. It uses the SQL scripts directly instead of importing them from the project.
"""

import os
import asyncio
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables from .env
load_dotenv()

# Get Supabase credentials
SUPABASE_URL = "https://uxxvoicxhkakpguvavba.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV4eHZvaWN4aGtha3BndXZhdmJhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTIzMzEzMDYsImV4cCI6MjA2NzkwNzMwNn0.5D4HDT35zNTuKO5R7HQODKZuSDN2YTilJdX07_wBsU0"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV4eHZvaWN4aGtha3BndXZhdmJhIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MjMzMTMwNiwiZXhwIjoyMDY3OTA3MzA2fQ.J0ErUCfrC862oy6RFKCUzCR80N75R3zeEN3o3FJE3Rk"

print(f"Conectando ao Supabase: {SUPABASE_URL}")

# Create Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# SQL para criar a função get_all_tables
CREATE_GET_ALL_TABLES_FUNCTION = """
CREATE OR REPLACE FUNCTION get_all_tables()
RETURNS TABLE(table_name text)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY SELECT t.table_name::text 
    FROM information_schema.tables t 
    WHERE t.table_schema = 'public';
END;
$$;
"""

# SQL para criar a função exec_sql
CREATE_EXEC_SQL_FUNCTION = """
CREATE OR REPLACE FUNCTION exec_sql(sql text)
RETURNS JSONB
LANGUAGE plpgsql
AS $$
DECLARE
    result JSONB;
BEGIN
    EXECUTE sql INTO result;
    RETURN result;
EXCEPTION WHEN OTHERS THEN
    RETURN jsonb_build_object('error', SQLERRM);
END;
$$;
"""

# SQL scripts for creating tables
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
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    embedding vector(1536)
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

# SQL scripts for creating functions
CREATE_FUNCTIONS_SQL = """
-- Function to count collections in a knowledge base
CREATE OR REPLACE FUNCTION count_collections_in_kb(p_knowledge_base_id UUID)
RETURNS TABLE (count BIGINT) AS $BODY$
BEGIN
    RETURN QUERY
    SELECT COUNT(*)
    FROM knowledge_collections
    WHERE knowledge_base_id = p_knowledge_base_id;
END;
$BODY$ LANGUAGE plpgsql;

-- Function to count documents in a knowledge base
CREATE OR REPLACE FUNCTION count_documents_in_kb(p_knowledge_base_id UUID)
RETURNS TABLE (count BIGINT) AS $BODY$
BEGIN
    RETURN QUERY
    SELECT COUNT(d.*)
    FROM documents d
    JOIN knowledge_collections c ON d.collection_id = c.id
    WHERE c.knowledge_base_id = p_knowledge_base_id;
END;
$BODY$ LANGUAGE plpgsql;

-- Function to count chunks in a knowledge base
CREATE OR REPLACE FUNCTION count_chunks_in_kb(p_knowledge_base_id UUID)
RETURNS TABLE (count BIGINT) AS $BODY$
BEGIN
    RETURN QUERY
    SELECT COUNT(ch.*)
    FROM document_chunks ch
    JOIN documents d ON ch.document_id = d.id
    JOIN knowledge_collections c ON d.collection_id = c.id
    WHERE c.knowledge_base_id = p_knowledge_base_id;
END;
$BODY$ LANGUAGE plpgsql;

-- Function to count documents in a collection
CREATE OR REPLACE FUNCTION count_documents_in_collection(p_collection_id UUID)
RETURNS TABLE (count BIGINT) AS $BODY$
BEGIN
    RETURN QUERY
    SELECT COUNT(*)
    FROM documents
    WHERE collection_id = p_collection_id;
END;
$BODY$ LANGUAGE plpgsql;

-- Function to count chunks in a collection
CREATE OR REPLACE FUNCTION count_chunks_in_collection(p_collection_id UUID)
RETURNS TABLE (count BIGINT) AS $BODY$
BEGIN
    RETURN QUERY
    SELECT COUNT(ch.*)
    FROM document_chunks ch
    JOIN documents d ON ch.document_id = d.id
    WHERE d.collection_id = p_collection_id;
END;
$BODY$ LANGUAGE plpgsql;

-- Function to count chunks in a document
CREATE OR REPLACE FUNCTION count_chunks_in_document(p_document_id UUID)
RETURNS TABLE (count BIGINT) AS $BODY$
BEGIN
    RETURN QUERY
    SELECT COUNT(*)
    FROM document_chunks
    WHERE document_id = p_document_id;
END;
$BODY$ LANGUAGE plpgsql;

-- Function to count versions in a document
CREATE OR REPLACE FUNCTION count_versions_in_document(p_document_id UUID)
RETURNS TABLE (count BIGINT) AS $BODY$
BEGIN
    RETURN QUERY
    SELECT COUNT(*)
    FROM document_versions
    WHERE document_id = p_document_id;
END;
$BODY$ LANGUAGE plpgsql;

-- Function to get document usage stats
CREATE OR REPLACE FUNCTION get_document_usage_stats(p_document_id UUID)
RETURNS TABLE (
    usage_count BIGINT,
    last_used_at TIMESTAMP WITH TIME ZONE
) AS $BODY$
BEGIN
    RETURN QUERY
    SELECT SUM(dus.usage_count)::BIGINT, MAX(dus.last_used_at)
    FROM document_usage_stats dus
    WHERE dus.document_id = p_document_id;
END;
$BODY$ LANGUAGE plpgsql;

-- Function to delete embeddings
CREATE OR REPLACE FUNCTION delete_embeddings(p_embedding_ids TEXT[])
RETURNS VOID AS $BODY$
BEGIN
    -- This is a placeholder. The actual implementation depends on the vector database used.
    -- For Supabase Vector, you would use the vector extension functions.
    -- For external vector databases, you would implement the deletion logic in the application code.
    RETURN;
END;
$BODY$ LANGUAGE plpgsql;
"""

# SQL scripts for creating RLS policies
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

-- Create policies for knowledge_bases (simplificado, sem referência a user_clients)
CREATE POLICY knowledge_bases_select ON knowledge_bases
    FOR SELECT
    USING (client_id = auth.uid());

CREATE POLICY knowledge_bases_insert ON knowledge_bases
    FOR INSERT
    WITH CHECK (client_id = auth.uid());

CREATE POLICY knowledge_bases_update ON knowledge_bases
    FOR UPDATE
    USING (client_id = auth.uid());

CREATE POLICY knowledge_bases_delete ON knowledge_bases
    FOR DELETE
    USING (client_id = auth.uid());

-- Create policies for knowledge_collections (simplificado, sem referência a user_clients)
CREATE POLICY knowledge_collections_select ON knowledge_collections
    FOR SELECT
    USING (knowledge_base_id IN (
        SELECT id FROM knowledge_bases
        WHERE client_id = auth.uid()
    ));

CREATE POLICY knowledge_collections_insert ON knowledge_collections
    FOR INSERT
    WITH CHECK (knowledge_base_id IN (
        SELECT id FROM knowledge_bases
        WHERE client_id = auth.uid()
    ));

CREATE POLICY knowledge_collections_update ON knowledge_collections
    FOR UPDATE
    USING (knowledge_base_id IN (
        SELECT id FROM knowledge_bases
        WHERE client_id = auth.uid()
    ));

CREATE POLICY knowledge_collections_delete ON knowledge_collections
    FOR DELETE
    USING (knowledge_base_id IN (
        SELECT id FROM knowledge_bases
        WHERE client_id = auth.uid()
    ));
"""

# SQL scripts for agent integration
AGENT_INTEGRATION_SQL = """
-- Function to get knowledge bases for a client
CREATE OR REPLACE FUNCTION get_client_knowledge_bases(p_client_id UUID)
RETURNS TABLE (
    id UUID,
    name TEXT,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE
) AS $BODY$
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
$BODY$ LANGUAGE plpgsql;

-- Function to get collections for knowledge bases
CREATE OR REPLACE FUNCTION get_collections_for_knowledge_bases(p_knowledge_base_ids UUID[])
RETURNS TABLE (
    id UUID,
    knowledge_base_id UUID,
    name TEXT,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE
) AS $BODY$
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
$BODY$ LANGUAGE plpgsql;

-- Function to search embeddings
CREATE OR REPLACE FUNCTION search_embeddings(
    p_query_embedding vector,
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
) AS $BODY$
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
$BODY$ LANGUAGE plpgsql;

-- Function to track chunk usage
CREATE OR REPLACE FUNCTION track_chunk_usage(
    p_chunk_id UUID,
    p_agent_id UUID,
    p_client_id UUID
)
RETURNS VOID AS $BODY$
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
            id,  -- Adicionando campo id que é obrigatório
            document_id,
            chunk_id,
            agent_id,
            client_id,
            usage_count,
            last_used_at,
            first_used_at
        ) VALUES (
            gen_random_uuid(),  -- Gerando UUID para o id
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
$BODY$ LANGUAGE plpgsql;

-- Function to update chunk embedding
CREATE OR REPLACE FUNCTION update_chunk_embedding(
    p_chunk_id UUID,
    p_embedding vector
)
RETURNS VOID AS $BODY$
BEGIN
    UPDATE document_chunks
    SET embedding = p_embedding
    WHERE id = p_chunk_id;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Chunk not found: %', p_chunk_id;
    END IF;
END;
$BODY$ LANGUAGE plpgsql;
"""

async def initialize_database():
    """Initialize the RAG database tables in Supabase."""
    print("Initializing RAG database...")
    
    try:
        # Usar o cliente Supabase com a chave de serviço para ter permissões de administrador
        supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        
        # Criar a função get_all_tables usando SQL direto
        print("Creating get_all_tables function...")
        # Usamos a API REST do Supabase para executar SQL diretamente
        # Isso requer permissões de administrador, por isso usamos a chave de serviço
        response = await supabase_admin.postgrest.schema("public").execute(CREATE_GET_ALL_TABLES_FUNCTION)
        print("get_all_tables function created successfully.")
        
        # Criar a função exec_sql
        print("Creating exec_sql function...")
        response = await supabase_admin.postgrest.schema("public").execute(CREATE_EXEC_SQL_FUNCTION)
        print("exec_sql function created successfully.")
        
        # Enable vector extension
        print("Enabling vector extension...")
        response = await supabase_admin.postgrest.schema("public").execute("CREATE EXTENSION IF NOT EXISTS vector;")
        print("Vector extension enabled successfully.")
        
        # Create tables
        print("Creating tables...")
        response = await supabase_admin.postgrest.schema("public").execute(CREATE_TABLES_SQL)
        print("Tables created successfully.")
        
        # Create functions
        print("Creating functions...")
        response = await supabase_admin.postgrest.schema("public").execute(CREATE_FUNCTIONS_SQL)
        print("Functions created successfully.")
        
        # Create RLS policies
        print("Creating RLS policies...")
        response = await supabase_admin.postgrest.schema("public").execute(CREATE_RLS_POLICIES_SQL)
        print("RLS policies created successfully.")
        
        # Create agent integration functions
        print("Creating agent integration functions...")
        response = await supabase_admin.postgrest.schema("public").execute(AGENT_INTEGRATION_SQL)
        print("Agent integration functions created successfully.")
        
        # Verificar tabelas criadas
        print("\nVerificando tabelas criadas:")
        result = await supabase.postgrest.rpc("get_all_tables").execute()
        
        if result.data:
            print("Tabelas disponíveis:")
            for table in result.data:
                print(f"- {table['table_name']}")
        else:
            print("Nenhuma tabela encontrada.")
        
        print("RAG database initialization completed successfully.")
        return True
    except Exception as e:
        print(f"Error initializing RAG database: {str(e)}")
        return False

if __name__ == "__main__":
    asyncio.run(initialize_database())