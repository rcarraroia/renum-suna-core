"""
Script para testar a conexão com o Supabase e listar as tabelas.

Este script se conecta ao Supabase usando as credenciais fornecidas e lista as tabelas disponíveis.
"""

import os
import asyncio
from dotenv import load_dotenv
from supabase import create_client, Client

# Carregar variáveis de ambiente
load_dotenv("renum-backend/.env")

# Obter credenciais do Supabase
SUPABASE_URL = "https://jmkmnwhxbtyxssxhrcsy.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Impta21ud2h4YnR5eHNzeGhyY3N5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTIwMTQyMDgsImV4cCI6MjA2NzU5MDIwOH0.pnqBU7nXYCdAOr1K4a8aKJQoXGMa4QtudkoTjBufXuI"

print(f"Conectando ao Supabase: {SUPABASE_URL}")

# Criar cliente Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

async def test_connection():
    """Testar a conexão com o Supabase e listar as tabelas."""
    try:
        # Listar tabelas
        print("Tentando listar tabelas...")
        
        # Consulta SQL para listar tabelas
        query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name;
        """
        
        result = await supabase.rpc("exec_sql", {"sql": query}).execute()
        
        if result.data:
            print("Conexão bem-sucedida!")
            print("Tabelas disponíveis:")
            for table in result.data:
                print(f"- {table['table_name']}")
        else:
            print("Conexão bem-sucedida, mas nenhuma tabela encontrada.")
        
        # Verificar tabelas específicas do RAG
        rag_tables = [
            "knowledge_bases",
            "knowledge_collections",
            "documents",
            "document_chunks",
            "document_versions",
            "document_usage_stats",
            "retrieval_feedback",
            "processing_jobs",
            "client_plans"
        ]
        
        print("\nVerificando tabelas do RAG:")
        for table in rag_tables:
            query = f"SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = '{table}');"
            result = await supabase.rpc("exec_sql", {"sql": query}).execute()
            exists = result.data[0]['exists'] if result.data else False
            status = "✅ Existe" if exists else "❌ Não existe"
            print(f"- {table}: {status}")
        
        return True
    except Exception as e:
        print(f"Erro ao conectar ao Supabase: {str(e)}")
        return False

if __name__ == "__main__":
    asyncio.run(test_connection())