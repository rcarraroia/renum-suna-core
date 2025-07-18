"""
Script para testar a conexão direta com o Supabase.

Este script tenta se conectar ao Supabase usando as credenciais corretas
e lista as tabelas disponíveis.
"""

import asyncio
from supabase import create_client, Client

# Configurações do Supabase
SUPABASE_URL = "https://uxxvoicxhkakpguvavba.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV4eHZvaWN4aGtha3BndXZhdmJhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTIzMzEzMDYsImV4cCI6MjA2NzkwNzMwNn0.5D4HDT35zNTuKO5R7HQODKZuSDN2YTilJdX07_wBsU0"

print(f"Conectando ao Supabase: {SUPABASE_URL}")

# Criar cliente Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

async def test_connection():
    """Testar a conexão com o Supabase."""
    try:
        # Listar tabelas
        print("Tentando listar tabelas...")
        
        # Tentar uma consulta direta para listar tabelas
        query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        """
        
        result = await supabase.rpc("exec_sql", {"sql": query}).execute()
        
        if result.data:
            print("Conexão bem-sucedida!")
            print("Tabelas disponíveis:")
            for table in result.data:
                print(f"- {table['table_name']}")
        else:
            print("Conexão bem-sucedida, mas nenhuma tabela encontrada.")
            
        # Verificar se as tabelas do RAG existem
        print("\nVerificando tabelas do RAG:")
        rag_tables = [
            "knowledge_bases",
            "knowledge_collections",
            "documents",
            "document_chunks",
            "document_versions",
            "document_usage_stats",
            "retrieval_feedback",
            "processing_jobs"
        ]
        
        for table in rag_tables:
            query = f"""
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = '{table}'
            )
            """
            result = await supabase.rpc("exec_sql", {"sql": query}).execute()
            exists = result.data[0]['exists'] if result.data else False
            print(f"Tabela {table}: {'✅ Existe' if exists else '❌ Não existe'}")
            
        return True
    except Exception as e:
        print(f"Erro ao conectar ao Supabase: {str(e)}")
        return False

if __name__ == "__main__":
    asyncio.run(test_connection())