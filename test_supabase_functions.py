"""
Script para testar a criação e execução de funções SQL no Supabase.

Este script tenta criar a função get_all_tables no Supabase e depois chamá-la.
"""

import os
import asyncio
import httpx
from supabase import create_client, Client

# Configurações do Supabase
SUPABASE_URL = "https://uxxvoicxhkakpguvavba.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV4eHZvaWN4aGtha3BndXZhdmJhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTIzMzEzMDYsImV4cCI6MjA2NzkwNzMwNn0.5D4HDT35zNTuKO5R7HQODKZuSDN2YTilJdX07_wBsU0"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV4eHZvaWN4aGtha3BndXZhdmJhIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MjMzMTMwNiwiZXhwIjoyMDY3OTA3MzA2fQ.J0ErUCfrC862oy6RFKCUzCR80N75R3zeEN3o3FJE3Rk"

print(f"Conectando ao Supabase: {SUPABASE_URL}")

# Criar cliente Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

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

async def test_supabase_functions():
    """Testar a criação e execução de funções SQL no Supabase."""
    try:
        print("Testando diferentes métodos para criar e executar funções SQL no Supabase...")
        
        # Método 1: Usando a API REST diretamente
        print("\nMétodo 1: Usando a API REST diretamente")
        try:
            headers = {
                "apikey": SUPABASE_SERVICE_KEY,
                "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal"
            }
            
            # Criar a função get_all_tables
            print("Tentando criar a função get_all_tables via API REST...")
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{SUPABASE_URL}/rest/v1/rpc/exec_sql",
                    headers=headers,
                    json={"sql": CREATE_GET_ALL_TABLES_FUNCTION}
                )
                
                if response.status_code == 200:
                    print("Função get_all_tables criada com sucesso via API REST!")
                else:
                    print(f"Erro ao criar função via API REST: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Erro no Método 1: {str(e)}")
        
        # Método 2: Usando o SQL Editor via API
        print("\nMétodo 2: Usando o SQL Editor via API")
        try:
            # Criar um cliente Supabase com a chave de serviço
            supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
            
            # Tentar criar a função get_all_tables usando SQL direto
            print("Tentando criar a função get_all_tables via SQL...")
            
            # Verificar se a função já existe
            print("Verificando se a função get_all_tables já existe...")
            try:
                result = await supabase.rpc("get_all_tables").execute()
                if result.data:
                    print("A função get_all_tables já existe e está funcionando!")
                    print("Tabelas disponíveis:")
                    for table in result.data:
                        print(f"- {table['table_name']}")
                else:
                    print("A função get_all_tables existe, mas não retornou dados.")
            except Exception as e:
                print(f"A função get_all_tables não existe ou ocorreu um erro: {str(e)}")
                print("Tentando criar a função...")
                
                # Tentar diferentes métodos para criar a função
                try:
                    # Método 2.1: Usando o cliente Supabase diretamente
                    print("Método 2.1: Usando o cliente Supabase diretamente")
                    await supabase_admin.rpc("exec_sql", {"sql": CREATE_GET_ALL_TABLES_FUNCTION}).execute()
                    print("Função criada com sucesso usando exec_sql!")
                except Exception as e1:
                    print(f"Erro no Método 2.1: {str(e1)}")
                    
                    try:
                        # Método 2.2: Usando o cliente Supabase com SQL direto
                        print("Método 2.2: Usando o cliente Supabase com SQL direto")
                        # Esta é uma abordagem hipotética, pode não funcionar
                        await supabase_admin.from_("_sql").select("*").execute(CREATE_GET_ALL_TABLES_FUNCTION)
                        print("Função criada com sucesso usando SQL direto!")
                    except Exception as e2:
                        print(f"Erro no Método 2.2: {str(e2)}")
        except Exception as e:
            print(f"Erro no Método 2: {str(e)}")
        
        # Verificar se a função foi criada
        print("\nVerificando se a função get_all_tables foi criada...")
        try:
            result = await supabase.rpc("get_all_tables").execute()
            if result.data:
                print("A função get_all_tables foi criada com sucesso!")
                print("Tabelas disponíveis:")
                for table in result.data:
                    print(f"- {table['table_name']}")
            else:
                print("A função get_all_tables foi criada, mas não retornou dados.")
        except Exception as e:
            print(f"A função get_all_tables não foi criada ou ocorreu um erro: {str(e)}")
        
        return True
    except Exception as e:
        print(f"Erro geral: {str(e)}")
        return False

if __name__ == "__main__":
    asyncio.run(test_supabase_functions())