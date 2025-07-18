"""
Script simplificado para testar a conexão com o Supabase usando o cliente oficial.
"""

import os
from supabase import create_client, Client

# Configurações do Supabase
SUPABASE_URL = "https://uxxvoicxhkakpguvavba.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV4eHZvaWN4aGtha3BndXZhdmJhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTIzMzEzMDYsImV4cCI6MjA2NzkwNzMwNn0.5D4HDT35zNTuKO5R7HQODKZuSDN2YTilJdX07_wBsU0"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV4eHZvaWN4aGtha3BndXZhdmJhIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MjMzMTMwNiwiZXhwIjoyMDY3OTA3MzA2fQ.J0ErUCfrC862oy6RFKCUzCR80N75R3zeEN3o3FJE3Rk"

print(f"Conectando ao Supabase: {SUPABASE_URL}")

# Criar cliente Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def test_connection():
    """Testar a conexão com o Supabase."""
    try:
        # Testar conexão com chave anônima
        print("\n1. Testando conexão com chave anônima...")
        try:
            # Tentar uma operação simples
            response = supabase.table("pg_tables").select("*").limit(1).execute()
            print("✅ Conexão com chave anônima bem-sucedida!")
            print(f"   Resposta: {response}")
        except Exception as e:
            print(f"❌ Erro na conexão com chave anônima: {str(e)}")
            
            # Tentar outra tabela
            try:
                response = supabase.table("knowledge_bases").select("*").limit(1).execute()
                print("✅ Conexão com chave anônima bem-sucedida (knowledge_bases)!")
                print(f"   Resposta: {response}")
            except Exception as e2:
                print(f"❌ Erro ao acessar knowledge_bases: {str(e2)}")
        
        # Testar conexão com chave de serviço
        print("\n2. Testando conexão com chave de serviço...")
        try:
            # Tentar uma operação simples
            response = supabase_admin.table("pg_tables").select("*").limit(1).execute()
            print("✅ Conexão com chave de serviço bem-sucedida!")
            print(f"   Resposta: {response}")
        except Exception as e:
            print(f"❌ Erro na conexão com chave de serviço: {str(e)}")
            
            # Tentar outra tabela
            try:
                response = supabase_admin.table("knowledge_bases").select("*").limit(1).execute()
                print("✅ Conexão com chave de serviço bem-sucedida (knowledge_bases)!")
                print(f"   Resposta: {response}")
            except Exception as e2:
                print(f"❌ Erro ao acessar knowledge_bases: {str(e2)}")
        
        # Listar tabelas disponíveis
        print("\n3. Tentando listar tabelas disponíveis...")
        try:
            # Usar a API REST para listar tabelas
            response = supabase_admin.table("information_schema.tables").select("table_name").eq("table_schema", "public").execute()
            
            if hasattr(response, 'data') and response.data:
                print("✅ Listagem de tabelas bem-sucedida!")
                print("   Tabelas disponíveis:")
                for table in response.data:
                    print(f"   - {table.get('table_name')}")
            else:
                print("❌ Nenhuma tabela encontrada ou resposta inválida.")
        except Exception as e:
            print(f"❌ Erro ao listar tabelas: {str(e)}")
        
        return True
    except Exception as e:
        print(f"❌ Erro geral: {str(e)}")
        return False

if __name__ == "__main__":
    test_connection()