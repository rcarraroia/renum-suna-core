-- Funções SQL para operações vetoriais no Supabase
-- Este script cria as funções necessárias para operações com vetores no módulo RAG

-- Habilitar a extensão pgvector se ainda não estiver habilitada
CREATE EXTENSION IF NOT EXISTS vector;

-- Função para buscar chunks por similaridade
CREATE OR REPLACE FUNCTION search_embeddings(
    query_embedding vector,
    match_threshold float,
    match_count int,
    collection_ids uuid[] DEFAULT NULL
)
RETURNS TABLE (
    id uuid,
    document_id uuid,
    content text,
    chunk_index int,
    metadata jsonb,
    embedding_id text,
    created_at timestamptz,
    document_name text,
    collection_id uuid,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.id,
        c.document_id,
        c.content,
        c.chunk_index,
        c.metadata,
        c.embedding_id,
        c.created_at,
        d.name as document_name,
        d.collection_id,
        1 - (c.embedding <=> query_embedding) as similarity
    FROM
        document_chunks c
    JOIN
        documents d ON c.document_id = d.id
    WHERE
        (collection_ids IS NULL OR d.collection_id = ANY(collection_ids))
        AND 1 - (c.embedding <=> query_embedding) > match_threshold
    ORDER BY
        c.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Função para criar índice de vetores
CREATE OR REPLACE FUNCTION create_vector_index(index_name text, table_name text, column_name text)
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
    EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON %I USING ivfflat (%I vector_cosine_ops) WITH (lists = 100)', 
                  index_name, table_name, column_name);
END;
$$;

-- Função para calcular a similaridade média entre dois conjuntos de embeddings
CREATE OR REPLACE FUNCTION avg_similarity(embeddings1 vector[], embeddings2 vector[])
RETURNS float
LANGUAGE plpgsql
AS $$
DECLARE
    total_similarity float := 0;
    count int := 0;
    i int;
    j int;
BEGIN
    IF array_length(embeddings1, 1) IS NULL OR array_length(embeddings2, 1) IS NULL THEN
        RETURN 0;
    END IF;
    
    FOR i IN 1..array_length(embeddings1, 1) LOOP
        FOR j IN 1..array_length(embeddings2, 1) LOOP
            total_similarity := total_similarity + (1 - (embeddings1[i] <=> embeddings2[j]));
            count := count + 1;
        END LOOP;
    END LOOP;
    
    IF count = 0 THEN
        RETURN 0;
    END IF;
    
    RETURN total_similarity / count;
END;
$$;

-- Função para buscar documentos similares com base na média de similaridade dos chunks
CREATE OR REPLACE FUNCTION search_similar_documents(
    query_embedding vector,
    match_threshold float,
    match_count int,
    collection_ids uuid[] DEFAULT NULL
)
RETURNS TABLE (
    id uuid,
    name text,
    collection_id uuid,
    source_type text,
    source_url text,
    file_type text,
    file_size int,
    status text,
    created_at timestamptz,
    updated_at timestamptz,
    avg_similarity float,
    chunk_count int
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        d.id,
        d.name,
        d.collection_id,
        d.source_type,
        d.source_url,
        d.file_type,
        d.file_size,
        d.status,
        d.created_at,
        d.updated_at,
        AVG(1 - (c.embedding <=> query_embedding)) as avg_similarity,
        COUNT(c.id) as chunk_count
    FROM
        documents d
    JOIN
        document_chunks c ON d.id = c.document_id
    WHERE
        (collection_ids IS NULL OR d.collection_id = ANY(collection_ids))
    GROUP BY
        d.id
    HAVING
        AVG(1 - (c.embedding <=> query_embedding)) > match_threshold
    ORDER BY
        avg_similarity DESC
    LIMIT match_count;
END;
$$;

-- Criar índice de vetores para a tabela document_chunks
SELECT create_vector_index('document_chunks_embedding_idx', 'document_chunks', 'embedding');

-- Função para executar consultas SQL seguras (para uso com MCP)
CREATE OR REPLACE FUNCTION exec_sql(sql text)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    result jsonb;
BEGIN
    -- Verificar se a consulta é segura (apenas SELECT)
    IF NOT (sql ~* '^SELECT\s.*') THEN
        RAISE EXCEPTION 'Apenas consultas SELECT são permitidas';
    END IF;
    
    -- Executar a consulta e retornar o resultado como JSON
    EXECUTE 'WITH result AS (' || sql || ') SELECT jsonb_agg(result) FROM result' INTO result;
    RETURN COALESCE(result, '[]'::jsonb);
EXCEPTION
    WHEN OTHERS THEN
        RETURN jsonb_build_object('error', SQLERRM);
END;
$$;

-- Função para listar tabelas acessíveis (para uso com MCP)
CREATE OR REPLACE FUNCTION list_tables()
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    result jsonb;
BEGIN
    -- Listar tabelas públicas
    WITH tables AS (
        SELECT
            table_name,
            table_schema
        FROM
            information_schema.tables
        WHERE
            table_schema = 'public'
            AND table_type = 'BASE TABLE'
        ORDER BY
            table_schema, table_name
    )
    SELECT jsonb_agg(tables) FROM tables INTO result;
    
    RETURN COALESCE(result, '[]'::jsonb);
END;
$$;