"""
Script para testar a conexão direta com o PostgreSQL do Supabase usando SSL.

Este script tenta se conectar ao Supabase usando a conexão PostgreSQL direta
com SSL ativado e a chave de serviço para operações administrativas.
"""

import os
import asyncio
import psycopg2
from supabase import create_client, Client
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configurações do Supabase
SUPABASE_URL = "https://uxxvoicxhkakpguvavba.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV4eHZvaWN4aGtha3BndXZhdmJhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTIzMzEzMDYsImV4cCI6MjA2NzkwNzMwNn0.5D4HDT35zNTuKO5R7HQODKZuSDN2YTilJdX07_wBsU0"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV4eHZvaWN4aGtha3BndXZhdmJhIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MjMzMTMwNiwiZXhwIjoyMDY3OTA3MzA2fQ.J0ErUCfrC862oy6RFKCUzCR80N75R3zeEN3o3FJE3Rk"

# Parâmetros de conexão PostgreSQL
PG_HOST = "db.uxxvoicxhkakpguvavba.supabase.co"
PG_PORT = "5432"
PG_DATABASE = "postgres"
PG_USER = "postgres"
PG_PASSWORD = "Renum@2024"  # Senha obtida do arquivo de credenciais

# String de conexão PostgreSQL com SSL ativado
PG_CONNECTION_STRING = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DATABASE}?sslmode=require"

print(f"Testando conexão com o Supabase PostgreSQL: {PG_HOST}")

async def test_supabase_api_connection():
    """Testar a conexão com a API do Supabase."""
    try:
        print("\n1. Testando conexão com a API do Supabase...")
        
        # Criar cliente Supabase com a chave de serviço
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        
        # Tentar uma operação simples - verificar se conseguimos acessar alguma tabela
        # Primeiro, vamos tentar listar as tabelas disponíveis
        try:
            # Tentar acessar a tabela knowledge_bases (se existir)
            response = await supabase.from_("knowledge_bases").select("*").limit(1).execute()
            print("✅ Conexão com a API do Supabase bem-sucedida! (knowledge_bases)")
            return True
        except Exception as e1:
            print(f"   - Não foi possível acessar knowledge_bases: {str(e1)}")
            
            try:
                # Tentar acessar a tabela documents (se existir)
                response = await supabase.from_("documents").select("*").limit(1).execute()
                print("✅ Conexão com a API do Supabase bem-sucedida! (documents)")
                return True
            except Exception as e2:
                print(f"   - Não foi possível acessar documents: {str(e2)}")
                
                try:
                    # Última tentativa - qualquer tabela que possa existir
                    response = await supabase.from_("users").select("*").limit(1).execute()
                    print("✅ Conexão com a API do Supabase bem-sucedida! (users)")
                    return True
                except Exception as e3:
                    print(f"   - Não foi possível acessar users: {str(e3)}")
                    print("❌ Não foi possível acessar nenhuma tabela conhecida")
                    return False
    except Exception as e:
        print(f"❌ Erro na conexão com a API do Supabase: {str(e)}")
        return False

def test_postgres_direct_connection():
    """Testar a conexão direta com o PostgreSQL."""
    try:
        print("\n2. Testando conexão direta com o PostgreSQL...")
        
        # Conectar diretamente ao PostgreSQL
        conn = psycopg2.connect(PG_CONNECTION_STRING)
        
        # Verificar se a conexão está ativa
        if conn.closed == 0:
            print("✅ Conexão direta com o PostgreSQL bem-sucedida!")
            
            # Executar uma consulta simples
            with conn.cursor() as cur:
                cur.execute("SELECT current_database(), current_user")
                db, user = cur.fetchone()
                print(f"   - Banco de dados: {db}")
                print(f"   - Usuário: {user}")
                
                # Listar algumas tabelas
                cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public' LIMIT 5")
                tables = cur.fetchall()
                if tables:
                    print("   - Tabelas disponíveis (primeiras 5):")
                    for table in tables:
                        print(f"     * {table[0]}")
                else:
                    print("   - Nenhuma tabela pública encontrada")
            
            # Fechar a conexão
            conn.close()
            return True
        else:
            print("❌ Conexão direta com o PostgreSQL falhou: Conexão fechada")
            return False
    except Exception as e:
        print(f"❌ Erro na conexão direta com o PostgreSQL: {str(e)}")
        return False

async def test_transaction_pooler_connection():
    """Testar a conexão com o Transaction Pooler."""
    try:
        print("\n3. Testando conexão com o Transaction Pooler...")
        
        # Parâmetros do Transaction Pooler
        pooler_host = "aws-0-sa-east-1-pooler.supabase.co"
        pooler_port = "6543"
        
        # String de conexão do Transaction Pooler
        pooler_connection_string = f"postgresql://{PG_USER}:{PG_PASSWORD}@{pooler_host}:{pooler_port}/{PG_DATABASE}?sslmode=require&pool_mode=transaction"
        
        # Conectar ao Transaction Pooler
        conn = psycopg2.connect(pooler_connection_string)
        
        # Verificar se a conexão está ativa
        if conn.closed == 0:
            print("✅ Conexão com o Transaction Pooler bem-sucedida!")
            
            # Executar uma consulta simples
            with conn.cursor() as cur:
                cur.execute("SELECT current_database(), current_user")
                db, user = cur.fetchone()
                print(f"   - Banco de dados: {db}")
                print(f"   - Usuário: {user}")
            
            # Fechar a conexão
            conn.close()
            return True
        else:
            print("❌ Conexão com o Transaction Pooler falhou: Conexão fechada")
            return False
    except Exception as e:
        print(f"❌ Erro na conexão com o Transaction Pooler: {str(e)}")
        return False

async def main():
    """Função principal para testar todas as conexões."""
    print("Iniciando testes de conexão com o Supabase...\n")
    
    # Testar conexão com a API do Supabase
    api_success = await test_supabase_api_connection()
    
    # Testar conexão direta com o PostgreSQL
    pg_success = test_postgres_direct_connection()
    
    # Testar conexão com o Transaction Pooler
    pooler_success = await test_transaction_pooler_connection()
    
    # Resumo dos resultados
    print("\n=== Resumo dos Testes de Conexão ===")
    print(f"API do Supabase: {'✅ Sucesso' if api_success else '❌ Falha'}")
    print(f"PostgreSQL Direto: {'✅ Sucesso' if pg_success else '❌ Falha'}")
    print(f"Transaction Pooler: {'✅ Sucesso' if pooler_success else '❌ Falha'}")
    
    # Recomendações baseadas nos resultados
    print("\n=== Recomendações ===")
    if pg_success:
        print("✅ Use a conexão PostgreSQL direta para operações administrativas e de longa duração.")
    elif pooler_success:
        print("⚠️ A conexão direta falhou, mas o Transaction Pooler está funcionando. Use-o como alternativa.")
    else:
        print("❌ Todas as conexões PostgreSQL falharam. Verifique as credenciais e configurações de rede.")
    
    if api_success:
        print("✅ Use a API do Supabase para operações simples e consultas básicas.")
    else:
        print("❌ A API do Supabase falhou. Verifique a chave de API e a URL.")
    
    # Configuração recomendada para o .env
    print("\n=== Configuração Recomendada para .env ===")
    print("SUPABASE_URL=https://uxxvoicxhkakpguvavba.supabase.co")
    print("SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
    print("SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
    if pg_success:
        print(f"SUPABASE_DB_URL={PG_CONNECTION_STRING}")
    elif pooler_success:
        print("SUPABASE_DB_URL=postgresql://postgres:******@aws-0-sa-east-1-pooler.supabase.co:6543/postgres?sslmode=require&pool_mode=transaction")

if __name__ == "__main__":
    asyncio.run(main())