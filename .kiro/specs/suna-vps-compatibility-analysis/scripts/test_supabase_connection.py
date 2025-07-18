#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para verificar a configuração de conexão com o Supabase.
Este script testa a conexão direta com o Supabase usando o cliente oficial,
verifica as variáveis de ambiente de conexão e analisa os logs de conexão.
"""

import os
import sys
import json
import time
import logging
import subprocess
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import traceback

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("supabase_connection_test")

# Tentar importar o cliente Supabase
try:
    from supabase import create_client, Client
    SUPABASE_CLIENT_AVAILABLE = True
except ImportError:
    logger.warning("Cliente Supabase não encontrado. Tentando instalar...")
    SUPABASE_CLIENT_AVAILABLE = False
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "supabase"])
        from supabase import create_client, Client
        SUPABASE_CLIENT_AVAILABLE = True
        logger.info("Cliente Supabase instalado com sucesso.")
    except Exception as e:
        logger.error(f"Falha ao instalar cliente Supabase: {e}")

# Tentar importar o cliente PostgreSQL
try:
    import psycopg2
    PSYCOPG2_AVAILABLE = True
except ImportError:
    logger.warning("Cliente PostgreSQL (psycopg2) não encontrado. Tentando instalar...")
    PSYCOPG2_AVAILABLE = False
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "psycopg2-binary"])
        import psycopg2
        PSYCOPG2_AVAILABLE = True
        logger.info("Cliente PostgreSQL instalado com sucesso.")
    except Exception as e:
        logger.error(f"Falha ao instalar cliente PostgreSQL: {e}")

def run_command(command: str) -> Tuple[str, str, int]:
    """
    Executa um comando shell e retorna stdout, stderr e código de saída.
    
    Args:
        command: Comando a ser executado
        
    Returns:
        Tuple contendo stdout, stderr e código de saída
    """
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
        text=True
    )
    stdout, stderr = process.communicate()
    return stdout, stderr, process.returncode

def get_container_ids(service_name: str) -> List[Dict[str, str]]:
    """
    Obtém IDs e nomes dos contêineres que correspondem ao padrão.
    
    Args:
        service_name: Nome do serviço (renum ou suna)
        
    Returns:
        Lista de dicionários com ID e nome dos contêineres
    """
    stdout, _, _ = run_command(f'docker ps -a --filter "name={service_name}" --format "{{{{.ID}}}}|{{{{.Names}}}}"')
    containers = []
    
    for line in stdout.splitlines():
        if not line.strip():
            continue
        parts = line.split("|")
        if len(parts) == 2:
            containers.append({"id": parts[0], "name": parts[1]})
    
    return containers

def get_container_env_vars(container_id: str) -> Dict[str, str]:
    """
    Obtém as variáveis de ambiente de um contêiner.
    
    Args:
        container_id: ID do contêiner
        
    Returns:
        Dicionário com as variáveis de ambiente
    """
    stdout, _, _ = run_command(f'docker inspect --format "{{{{json .Config.Env}}}}" {container_id}')
    
    try:
        env_list = json.loads(stdout)
        env_dict = {}
        for item in env_list:
            if "=" in item:
                key, value = item.split("=", 1)
                env_dict[key] = value
        return env_dict
    except json.JSONDecodeError:
        logger.error(f"Erro ao decodificar JSON para o contêiner {container_id}")
        return {}

def extract_supabase_config(env_vars: Dict[str, str]) -> Dict[str, str]:
    """
    Extrai a configuração do Supabase das variáveis de ambiente.
    
    Args:
        env_vars: Dicionário com variáveis de ambiente
        
    Returns:
        Dicionário com configuração do Supabase
    """
    supabase_config = {}
    
    # Variáveis relacionadas ao Supabase
    supabase_vars = [
        "SUPABASE_URL",
        "SUPABASE_KEY",
        "DATABASE_URL",
        "SUPABASE_SERVICE_KEY",
        "SUPABASE_JWT_SECRET",
        "SUPABASE_ANON_KEY",
        "POSTGRES_PASSWORD",
        "POSTGRES_USER",
        "POSTGRES_DB",
        "POSTGRES_HOST",
        "POSTGRES_PORT"
    ]
    
    for var in supabase_vars:
        if var in env_vars:
            supabase_config[var] = env_vars[var]
    
    # Tentar extrair informações da URL do banco de dados
    if "DATABASE_URL" in supabase_config:
        db_url = supabase_config["DATABASE_URL"]
        try:
            # Formato esperado: postgresql://user:password@host:port/dbname
            if db_url.startswith("postgresql://"):
                # Remover o prefixo
                db_url = db_url[len("postgresql://"):]
                
                # Extrair usuário e senha
                auth_part, rest = db_url.split("@", 1)
                if ":" in auth_part:
                    user, password = auth_part.split(":", 1)
                    supabase_config["EXTRACTED_DB_USER"] = user
                    supabase_config["EXTRACTED_DB_PASSWORD"] = password
                
                # Extrair host, porta e nome do banco
                host_part, db_name = rest.split("/", 1)
                if ":" in host_part:
                    host, port = host_part.split(":", 1)
                    supabase_config["EXTRACTED_DB_HOST"] = host
                    supabase_config["EXTRACTED_DB_PORT"] = port
                else:
                    supabase_config["EXTRACTED_DB_HOST"] = host_part
                    supabase_config["EXTRACTED_DB_PORT"] = "5432"  # Porta padrão
                
                supabase_config["EXTRACTED_DB_NAME"] = db_name
        except Exception as e:
            logger.warning(f"Não foi possível extrair informações da URL do banco de dados: {e}")
    
    return supabase_config

def test_supabase_connection(url: str, key: str) -> Tuple[bool, str]:
    """
    Testa a conexão com o Supabase usando o cliente oficial.
    
    Args:
        url: URL do Supabase
        key: Chave de API do Supabase
        
    Returns:
        Tuple com status da conexão e mensagem
    """
    if not SUPABASE_CLIENT_AVAILABLE:
        return False, "Cliente Supabase não está disponível"
    
    try:
        logger.info(f"Tentando conectar ao Supabase: {url}")
        start_time = time.time()
        
        # Criar cliente Supabase
        supabase: Client = create_client(url, key)
        
        # Testar conexão com uma consulta simples
        response = supabase.table("_test_connection").select("*").limit(1).execute()
        
        end_time = time.time()
        duration = end_time - start_time
        
        return True, f"Conexão bem-sucedida em {duration:.2f} segundos"
    except Exception as e:
        logger.error(f"Erro ao conectar ao Supabase: {e}")
        logger.error(traceback.format_exc())
        return False, f"Erro de conexão: {str(e)}"

def test_postgres_connection(db_url: str) -> Tuple[bool, str]:
    """
    Testa a conexão direta com o PostgreSQL.
    
    Args:
        db_url: URL de conexão com o PostgreSQL
        
    Returns:
        Tuple com status da conexão e mensagem
    """
    if not PSYCOPG2_AVAILABLE:
        return False, "Cliente PostgreSQL não está disponível"
    
    try:
        logger.info(f"Tentando conectar diretamente ao PostgreSQL")
        start_time = time.time()
        
        # Conectar ao PostgreSQL
        conn = psycopg2.connect(db_url)
        
        # Executar consulta simples
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            version = cur.fetchone()[0]
        
        # Fechar conexão
        conn.close()
        
        end_time = time.time()
        duration = end_time - start_time
        
        return True, f"Conexão PostgreSQL bem-sucedida em {duration:.2f} segundos. Versão: {version}"
    except Exception as e:
        logger.error(f"Erro ao conectar ao PostgreSQL: {e}")
        logger.error(traceback.format_exc())
        return False, f"Erro de conexão PostgreSQL: {str(e)}"

def check_container_logs(container_id: str, lines: int = 50) -> List[str]:
    """
    Verifica os logs de um contêiner em busca de mensagens relacionadas ao Supabase.
    
    Args:
        container_id: ID do contêiner
        lines: Número de linhas a serem recuperadas
        
    Returns:
        Lista de linhas de log relevantes
    """
    stdout, _, _ = run_command(f'docker logs --tail {lines} {container_id}')
    
    # Filtrar linhas relevantes
    relevant_keywords = [
        "supabase",
        "postgres",
        "database",
        "connection",
        "ssl",
        "error",
        "failed",
        "timeout"
    ]
    
    relevant_logs = []
    for line in stdout.splitlines():
        if any(keyword in line.lower() for keyword in relevant_keywords):
            relevant_logs.append(line)
    
    return relevant_logs

def generate_report(results: Dict) -> str:
    """
    Gera um relatório formatado com os resultados dos testes.
    
    Args:
        results: Dicionário com resultados dos testes
        
    Returns:
        Relatório formatado em Markdown
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = [
        "# Relatório de Conexão com Supabase",
        f"Data: {now}\n",
        "## Resumo",
    ]
    
    # Adicionar resumo
    total_containers = len(results["containers"])
    successful_connections = sum(1 for c in results["containers"] if c["supabase_connection"]["success"])
    
    report.extend([
        f"- Total de contêineres analisados: {total_containers}",
        f"- Conexões bem-sucedidas com Supabase: {successful_connections}/{total_containers}",
        f"- Conexões diretas com PostgreSQL bem-sucedidas: {sum(1 for c in results['containers'] if c.get('postgres_connection', {}).get('success', False))}/{total_containers}\n"
    ])
    
    # Adicionar detalhes por contêiner
    for container in results["containers"]:
        container_name = container["name"]
        container_id = container["id"]
        
        report.append(f"## Contêiner: {container_name} ({container_id[:12]})")
        
        # Configuração do Supabase
        report.append("\n### Configuração do Supabase")
        
        supabase_config = container["supabase_config"]
        if supabase_config:
            # Mascarar valores sensíveis
            masked_config = {}
            for key, value in supabase_config.items():
                if any(sensitive in key.upper() for sensitive in ["KEY", "PASSWORD", "SECRET"]):
                    if value and len(value) > 8:
                        masked_config[key] = value[:4] + "..." + value[-4:]
                    else:
                        masked_config[key] = "****"
                else:
                    masked_config[key] = value
            
            for key, value in masked_config.items():
                report.append(f"- **{key}**: {value}")
        else:
            report.append("Nenhuma configuração do Supabase encontrada.")
        
        # Resultado da conexão com Supabase
        report.append("\n### Teste de Conexão com Supabase")
        
        supabase_connection = container["supabase_connection"]
        if supabase_connection["success"]:
            report.append(f"✅ **Sucesso**: {supabase_connection['message']}")
        else:
            report.append(f"❌ **Falha**: {supabase_connection['message']}")
        
        # Resultado da conexão direta com PostgreSQL
        if "postgres_connection" in container:
            report.append("\n### Teste de Conexão Direta com PostgreSQL")
            
            postgres_connection = container["postgres_connection"]
            if postgres_connection["success"]:
                report.append(f"✅ **Sucesso**: {postgres_connection['message']}")
            else:
                report.append(f"❌ **Falha**: {postgres_connection['message']}")
        
        # Logs relevantes
        if container["relevant_logs"]:
            report.append("\n### Logs Relevantes")
            report.append("```")
            for log in container["relevant_logs"]:
                report.append(log)
            report.append("```")
        
        report.append("\n---\n")
    
    # Adicionar recomendações
    report.append("## Recomendações")
    
    if successful_connections < total_containers:
        report.append("\n### Problemas de Conexão com Supabase")
        report.append("Se houver problemas de conexão com o Supabase, verifique:")
        report.append("1. **URL e chave do Supabase** - Confirme se estão corretos e válidos")
        report.append("2. **Configuração de rede** - Verifique se a VPS pode acessar o Supabase")
        report.append("3. **Configuração SSL** - Certifique-se de que a conexão SSL está configurada corretamente")
        report.append("4. **Firewall** - Verifique se o firewall permite conexões de saída para o Supabase")
    else:
        report.append("\n✅ Todas as conexões com o Supabase estão funcionando corretamente.")
    
    return "\n".join(report)

def main():
    """Função principal do script."""
    logger.info("Verificando configuração de conexão com Supabase...")
    
    results = {
        "containers": []
    }
    
    # Obter contêineres Renum e Suna
    containers = []
    containers.extend(get_container_ids("renum"))
    containers.extend(get_container_ids("suna"))
    
    if not containers:
        logger.warning("Nenhum contêiner Renum ou Suna encontrado.")
        return
    
    # Analisar cada contêiner
    for container in containers:
        container_id = container["id"]
        container_name = container["name"]
        
        logger.info(f"Analisando contêiner: {container_name} ({container_id[:12]})")
        
        # Obter variáveis de ambiente
        env_vars = get_container_env_vars(container_id)
        
        # Extrair configuração do Supabase
        supabase_config = extract_supabase_config(env_vars)
        
        container_result = {
            "id": container_id,
            "name": container_name,
            "supabase_config": supabase_config
        }
        
        # Testar conexão com Supabase
        if "SUPABASE_URL" in supabase_config and "SUPABASE_KEY" in supabase_config:
            success, message = test_supabase_connection(
                supabase_config["SUPABASE_URL"],
                supabase_config["SUPABASE_KEY"]
            )
            container_result["supabase_connection"] = {
                "success": success,
                "message": message
            }
        else:
            container_result["supabase_connection"] = {
                "success": False,
                "message": "Configuração do Supabase incompleta"
            }
        
        # Testar conexão direta com PostgreSQL
        if "DATABASE_URL" in supabase_config:
            success, message = test_postgres_connection(supabase_config["DATABASE_URL"])
            container_result["postgres_connection"] = {
                "success": success,
                "message": message
            }
        
        # Verificar logs do contêiner
        container_result["relevant_logs"] = check_container_logs(container_id)
        
        results["containers"].append(container_result)
    
    # Gerar relatório
    report = generate_report(results)
    
    # Salvar relatório em arquivo
    report_path = os.path.join(os.path.dirname(__file__), "..", "reports")
    os.makedirs(report_path, exist_ok=True)
    
    report_file = os.path.join(report_path, "supabase_connection_report.md")
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)
    
    logger.info(f"Relatório salvo em: {report_file}")
    
    # Exibir resumo
    successful_connections = sum(1 for c in results["containers"] if c["supabase_connection"]["success"])
    total_containers = len(results["containers"])
    
    if successful_connections == total_containers:
        logger.info("✅ Todas as conexões com o Supabase estão funcionando corretamente.")
    else:
        logger.warning(f"⚠️ Apenas {successful_connections} de {total_containers} contêineres conseguiram conectar ao Supabase.")
        logger.info(f"Para mais detalhes, consulte o relatório: {report_file}")

if __name__ == "__main__":
    main()