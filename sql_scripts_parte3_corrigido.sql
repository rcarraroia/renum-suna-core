-- PARTE 3: CRIAÇÃO DE POLÍTICAS RLS (CORRIGIDO)
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

-- Policies for documents
CREATE POLICY documents_select ON documents
    FOR SELECT
    USING (collection_id IN (
        SELECT id FROM knowledge_collections
        WHERE knowledge_base_id IN (
            SELECT id FROM knowledge_bases
            WHERE client_id = auth.uid()
        )
    ));

CREATE POLICY documents_insert ON documents
    FOR INSERT
    WITH CHECK (collection_id IN (
        SELECT id FROM knowledge_collections
        WHERE knowledge_base_id IN (
            SELECT id FROM knowledge_bases
            WHERE client_id = auth.uid()
        )
    ));

CREATE POLICY documents_update ON documents
    FOR UPDATE
    USING (collection_id IN (
        SELECT id FROM knowledge_collections
        WHERE knowledge_base_id IN (
            SELECT id FROM knowledge_bases
            WHERE client_id = auth.uid()
        )
    ));

CREATE POLICY documents_delete ON documents
    FOR DELETE
    USING (collection_id IN (
        SELECT id FROM knowledge_collections
        WHERE knowledge_base_id IN (
            SELECT id FROM knowledge_bases
            WHERE client_id = auth.uid()
        )
    ));

-- Policies for document_chunks
CREATE POLICY document_chunks_select ON document_chunks
    FOR SELECT
    USING (document_id IN (
        SELECT id FROM documents
        WHERE collection_id IN (
            SELECT id FROM knowledge_collections
            WHERE knowledge_base_id IN (
                SELECT id FROM knowledge_bases
                WHERE client_id = auth.uid()
            )
        )
    ));

CREATE POLICY document_chunks_insert ON document_chunks
    FOR INSERT
    WITH CHECK (document_id IN (
        SELECT id FROM documents
        WHERE collection_id IN (
            SELECT id FROM knowledge_collections
            WHERE knowledge_base_id IN (
                SELECT id FROM knowledge_bases
                WHERE client_id = auth.uid()
            )
        )
    ));

CREATE POLICY document_chunks_update ON document_chunks
    FOR UPDATE
    USING (document_id IN (
        SELECT id FROM documents
        WHERE collection_id IN (
            SELECT id FROM knowledge_collections
            WHERE knowledge_base_id IN (
                SELECT id FROM knowledge_bases
                WHERE client_id = auth.uid()
            )
        )
    ));

CREATE POLICY document_chunks_delete ON document_chunks
    FOR DELETE
    USING (document_id IN (
        SELECT id FROM documents
        WHERE collection_id IN (
            SELECT id FROM knowledge_collections
            WHERE knowledge_base_id IN (
                SELECT id FROM knowledge_bases
                WHERE client_id = auth.uid()
            )
        )
    ));