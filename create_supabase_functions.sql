-- Este arquivo contém o SQL necessário para criar as funções utilizadas pelo MCP
-- Execute este SQL no SQL Editor do painel do Supabase

-- Função para listar todas as tabelas
CREATE OR REPLACE FUNCTION list_tables()
RETURNS TABLE(table_name text)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY SELECT t.table_name::text 
    FROM information_schema.tables t 
    WHERE t.table_schema = 'public';
END;
$$;

-- Função para executar SQL dinâmico
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

-- Teste para verificar se as funções foram criadas corretamente
SELECT * FROM list_tables();
SELECT exec_sql('SELECT COUNT(*) FROM information_schema.tables');