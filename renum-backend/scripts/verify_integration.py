"""
Script para verificar a integração entre o backend Renum e o sistema Suna.
Este script verifica:
1. Conexão com o Supabase
2. Existência das tabelas com prefixo renum_
3. Comunicação com o backend Suna
4. Configuração do NGINX
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv
from supabase import create_client, Client
from tabulate import tabulate

# Configurar cores para output
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
NC = '\033[0m'  # No Color

def print_success(message):
    """Imprime mensagem de sucesso."""
    print(f"{GREEN}✓ {message}{NC}")

def print_warning(message):
    """Imprime mensagem de aviso."""
    print(f"{YELLOW}⚠ {message}{NC}")

def print_error(message):
    """Imprime mensagem de erro."""
    print(f"{RED}✗ {message}{NC}")

def print_section(title):
    """Imprime título de seção."""
    print(f"\n{GREEN}=== {title} ==={NC}")

def check_supabase_connection():
    """Verifica a conexão com o Supabase."""
    print_section("Verificando conexão com o Supabase")
    
    try:
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            print_error("SUPABASE_URL ou SUPABASE_KEY não encontrados no arquivo .env")
            return False
        
        print(f"Conectando ao Supabase: {supabase_url}")
        supabase = create_client(supabase_url, supabase_key)
        
        # Testar conexão com uma consulta simples
        result = supabase.from_("agents").select("id").limit(1).execute()
        
        print_success(f"Conexão com o Supabase estabelecida com sucesso!")
        return supabase
    except Exception as e:
        print_error(f"Erro ao conectar com o Supabase: {str(e)}")
        return False

def check_renum_tables(supabase):
    """Verifica a existência das tabelas com prefixo renum_."""
    print_section("Verificando tabelas com prefixo renum_")
    
    if not supabase:
        print_error("Conexão com o Supabase não estabelecida")
        return False
    
    try:
        # Executar consulta SQL para listar tabelas
        result = supabase.rpc("exec_sql", {"sql": """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """}).execute()
        
        if not result.data:
            print_error("Não foi possível listar as tabelas")
            return False
        
        tables = [table["table_name"] for table in result.data]
        renum_tables = [table for table in tables if table.startswith("renum_")]
        other_tables = [table for table in tables if not table.startswith("renum_")]
        
        if not renum_tables:
            print_error("Nenhuma tabela com prefixo renum_ encontrada")
            return False
        
        print_success(f"Encontradas {len(renum_tables)} tabelas com prefixo renum_:")
        
        # Exibir tabelas em formato tabular
        table_data = []
        for table in renum_tables:
            # Obter contagem de registros
            count_result = supabase.rpc("exec_sql", {"sql": f"SELECT COUNT(*) FROM {table}"}).execute()
            count = count_result.data[0]["count"] if count_result.data else 0
            
            # Obter colunas
            columns_result = supabase.rpc("exec_sql", {"sql": f"""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = '{table}'
                ORDER BY ordinal_position
            """}).execute()
            
            columns = [col["column_name"] for col in columns_result.data] if columns_result.data else []
            
            table_data.append([table, count, ", ".join(columns[:3]) + ("..." if len(columns) > 3 else "")])
        
        print(tabulate(table_data, headers=["Tabela", "Registros", "Colunas (primeiras 3)"]))
        
        print(f"\nOutras tabelas no banco de dados: {len(other_tables)}")
        
        return True
    except Exception as e:
        print_error(f"Erro ao verificar tabelas: {str(e)}")
        return False

def check_suna_communication():
    """Verifica a comunicação com o backend Suna."""
    print_section("Verificando comunicação com o backend Suna")
    
    try:
        suna_url = os.environ.get("SUNA_API_URL")
        
        if not suna_url:
            print_error("SUNA_API_URL não encontrado no arquivo .env")
            return False
        
        print(f"Conectando ao backend Suna: {suna_url}")
        
        # Testar endpoint de health check
        health_url = f"{suna_url}/health"
        print(f"Testando endpoint: {health_url}")
        
        response = requests.get(health_url, timeout=5)
        
        if response.status_code == 200:
            print_success(f"Conexão com o backend Suna estabelecida com sucesso! Status: {response.status_code}")
            print(f"Resposta: {response.text}")
            return True
        else:
            print_error(f"Erro ao conectar com o backend Suna. Status: {response.status_code}")
            print(f"Resposta: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print_error(f"Erro ao conectar com o backend Suna: {str(e)}")
        return False

def check_nginx_configuration():
    """Verifica a configuração do NGINX."""
    print_section("Verificando configuração do NGINX")
    
    try:
        # Verificar se o NGINX está instalado
        result = os.system("nginx -v > /dev/null 2>&1")
        
        if result != 0:
            print_warning("NGINX não encontrado ou não está no PATH")
            print_warning("Pulando verificação da configuração do NGINX")
            return None
        
        # Verificar configuração do NGINX
        result = os.system("nginx -t > /dev/null 2>&1")
        
        if result == 0:
            print_success("Configuração do NGINX está válida")
            
            # Verificar se há configuração para o backend Renum
            renum_config_found = False
            
            # Locais comuns para arquivos de configuração do NGINX
            config_paths = [
                "/etc/nginx/sites-enabled",
                "/etc/nginx/conf.d",
                "/usr/local/etc/nginx/sites-enabled",
                "/usr/local/etc/nginx/conf.d"
            ]
            
            for path in config_paths:
                if os.path.exists(path):
                    for file in os.listdir(path):
                        if os.path.isfile(os.path.join(path, file)):
                            with open(os.path.join(path, file), 'r') as f:
                                content = f.read()
                                if "renum" in content.lower() or "9000" in content:
                                    print_success(f"Configuração para o backend Renum encontrada em {os.path.join(path, file)}")
                                    renum_config_found = True
            
            if not renum_config_found:
                print_warning("Nenhuma configuração para o backend Renum encontrada nos arquivos do NGINX")
                print_warning("Verifique se o proxy reverso está configurado corretamente")
            
            return True
        else:
            print_error("Configuração do NGINX está inválida")
            return False
    except Exception as e:
        print_error(f"Erro ao verificar configuração do NGINX: {str(e)}")
        return False

def main():
    """Função principal."""
    print_section("Verificação da Integração Renum-Suna")
    
    # Carregar variáveis de ambiente
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print_success(f"Variáveis de ambiente carregadas de {env_path}")
    else:
        print_error(f"Arquivo .env não encontrado em {env_path}")
        return False
    
    # Verificar conexão com o Supabase
    supabase = check_supabase_connection()
    
    # Verificar tabelas com prefixo renum_
    if supabase:
        check_renum_tables(supabase)
    
    # Verificar comunicação com o backend Suna
    check_suna_communication()
    
    # Verificar configuração do NGINX
    check_nginx_configuration()
    
    print_section("Verificação concluída")
    print("Para mais detalhes, consulte o arquivo INTEGRATION_SUMMARY.md")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nVerificação interrompida pelo usuário")
    except Exception as e:
        print_error(f"Erro inesperado: {str(e)}")
        sys.exit(1)