"""
Script para executar SQL diretamente no Supabase usando a biblioteca supabase-py.
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client

def load_sql_file(file_path):
    """Carrega um arquivo SQL."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"Erro ao ler o arquivo SQL: {e}")
        sys.exit(1)

def main():
    """Função principal."""
    # Verificar argumentos
    if len(sys.argv) < 2:
        print("Uso: python execute_sql_direct.py <arquivo_sql>")
        sys.exit(1)
    
    sql_file = sys.argv[1]
    if not os.path.exists(sql_file):
        print(f"Erro: Arquivo SQL não encontrado: {sql_file}")
        sys.exit(1)
    
    # Carregar variáveis de ambiente
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"Variáveis de ambiente carregadas de {env_path}")
    else:
        print("Arquivo .env não encontrado, usando variáveis de ambiente existentes")
    
    # Obter credenciais do Supabase
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_SERVICE_KEY")  # Usar a chave de serviço
    
    if not supabase_url or not supabase_key:
        print("Erro: SUPABASE_URL e SUPABASE_SERVICE_KEY devem estar definidos no ambiente")
        sys.exit(1)
    
    # Carregar conteúdo SQL
    print(f"Carregando SQL de {sql_file}...")
    sql_content = load_sql_file(sql_file)
    
    # Conectar ao Supabase
    print("Conectando ao Supabase...")
    try:
        supabase = create_client(supabase_url, supabase_key)
        print("Conexão estabelecida com sucesso")
    except Exception as e:
        print(f"Erro ao conectar ao Supabase: {e}")
        sys.exit(1)
    
    # Executar SQL
    print("Executando SQL...")
    try:
        # Usar a função rpc para executar SQL
        result = supabase.rpc("exec_sql", {"sql": sql_content}).execute()
        print("SQL executado com sucesso!")
        print(f"Resultado: {result}")
    except Exception as e:
        print(f"Erro ao executar SQL: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()