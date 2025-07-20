"""
Script para executar comandos SQL no Supabase.
Este script lê um arquivo SQL e o executa no Supabase usando a biblioteca supabase-py.
"""

import os
import sys
import argparse
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

def execute_sql(supabase_url, supabase_key, sql_content):
    """Executa comandos SQL no Supabase."""
    try:
        # Inicializar cliente Supabase
        supabase: Client = create_client(supabase_url, supabase_key)
        
        # Executar SQL
        print("Executando SQL no Supabase...")
        result = supabase.rpc('exec_sql', {'sql': sql_content}).execute()
        
        # Verificar resultado
        if hasattr(result, 'error') and result.error:
            print(f"Erro ao executar SQL: {result.error}")
            return False
        
        print("SQL executado com sucesso!")
        return True
    except Exception as e:
        print(f"Erro ao executar SQL no Supabase: {e}")
        return False

def main():
    """Função principal."""
    parser = argparse.ArgumentParser(description='Executa comandos SQL no Supabase.')
    parser.add_argument('--file', required=True, help='Caminho para o arquivo SQL')
    parser.add_argument('--url', help='URL do projeto Supabase')
    parser.add_argument('--key', help='Chave de serviço do Supabase')
    parser.add_argument('--env', help='Arquivo .env com as credenciais do Supabase')
    
    args = parser.parse_args()
    
    # Carregar variáveis de ambiente se especificado
    if args.env:
        load_dotenv(args.env)
    
    # Obter credenciais do Supabase
    supabase_url = args.url or os.environ.get('SUPABASE_URL')
    supabase_key = args.key or os.environ.get('SUPABASE_SERVICE_KEY')
    
    if not supabase_url or not supabase_key:
        print("Erro: URL e chave do Supabase são obrigatórios.")
        print("Forneça-os como argumentos ou em um arquivo .env.")
        sys.exit(1)
    
    # Carregar conteúdo SQL
    sql_content = load_sql_file(args.file)
    
    # Executar SQL
    success = execute_sql(supabase_url, supabase_key, sql_content)
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()