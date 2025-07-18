#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para verificar as funções vetoriais no Supabase.
Este script verifica a presença da extensão pgvector, lista as extensões instaladas
e testa as funções de busca vetorial.
"""

import os
import sys
import json
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
logger = logging.getLogger("vector_functions_test")

# Tentar importar o cliente PostgreSQL
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_AVAILABLE = True
except ImportError:
    logger.warning("Cliente PostgreSQL (psycopg2) não encontrado. Tentando instalar...")
    PSYCOPG2_AVAILABLE = False
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "psycopg2-binary"])
        import psycopg2
        from psycopg2.extras import RealDictCursor
        PSYCOPG2_AVAILABLE = True
        logger.info("Cliente PostgreSQL instalado com sucesso.")
    except Exception as e:
        logger.error(f"Falha ao instalar cliente PostgreSQL: {e}")

# Tentar importar numpy para operações vetoriais
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    logger.warning("NumPy não encontrado. Tentando instalar...")
    NUMPY_AVAILABLE = False
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "numpy"])
        import numpy as np
        NUMPY_AVAILABLE = True
        logger.info("NumPy instalado com sucesso.")
    except Exception as e:
        logger.error(f"Falha ao instalar NumPy: {e}")

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

def extract_database_url(env_vars: Dict[str, str]) -> Optional[str]:
    """
    Extrai a URL do banco de dados das variáveis de ambiente.
    
    Args:
        env_vars: Dicionário com variáveis de ambiente
        
    Returns:
        URL do banco de dados ou None se não encontrada
    """
    if "DATABASE_URL" in env_vars:
        return env_vars["DATABASE_URL"]
    
    # Tentar construir a URL a partir de componentes
    if all(key in env_vars for key in ["POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_HOST", "POSTGRES_DB"]):
        port = env_vars.get("POSTGRES_PORT", "5432")
        return f"postgresql://{env_vars['POSTGRES_USER']}:{env_vars['POSTGRES_PASSWORD']}@{env_vars['POSTGRES_HOST']}:{port}/{env_vars['POSTGRES_DB']}"
    
    return None

def check_postgres_extensions(db_url: str) -> Dict:
    """
    Verifica as extensões instaladas no PostgreSQL.
    
    Args:
        db_url: URL de conexão com o PostgreSQL
        
    Returns:
        Dicionário com resultados da verificação
    """
    if not PSYCOPG2_AVAILABLE:
        return {
            "success": False,
            "message": "Cliente PostgreSQL não está disponível",
            "extensions": []
        }
    
    try:
        logger.info("Conectando ao PostgreSQL para verificar extensões...")
        
        # Conectar ao PostgreSQL
        conn = psycopg2.connect(db_url)
        
        # Listar extensões instaladas
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT name, default_version, installed_version, comment FROM pg_available_extensions ORDER BY name;")
            extensions = cur.fetchall()
        
        # Verificar se pgvector está instalado
        pgvector_installed = any(ext["name"] == "vector" for ext in extensions)
        
        # Fechar conexão
        conn.close()
        
        return {
            "success": True,
            "message": "Extensões verificadas com sucesso",
            "extensions": extensions,
            "pgvector_installed": pgvector_installed
        }
    except Exception as e:
        logger.error(f"Erro ao verificar extensões PostgreSQL: {e}")
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "message": f"Erro ao verificar extensões: {str(e)}",
            "extensions": []
        }

def test_vector_functions(db_url: str) -> Dict:
    """
    Testa as funções de busca vetorial no PostgreSQL.
    
    Args:
        db_url: URL de conexão com o PostgreSQL
        
    Returns:
        Dicionário com resultados dos testes
    """
    if not PSYCOPG2_AVAILABLE or not NUMPY_AVAILABLE:
        return {
            "success": False,
            "message": "Dependências necessárias não estão disponíveis",
            "tests": []
        }
    
    try:
        logger.info("Conectando ao PostgreSQL para testar funções vetoriais...")
        
        # Conectar ao PostgreSQL
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        
        tests = []
        
        # Teste 1: Verificar se a extensão vector está habilitada
        with conn.cursor() as cur:
            try:
                cur.execute("SELECT extname FROM pg_extension WHERE extname = 'vector';")
                result = cur.fetchone()
                tests.append({
                    "name": "Extensão vector habilitada",
                    "success": result is not None,
                    "message": "Extensão vector está habilitada" if result else "Extensão vector não está habilitada"
                })
            except Exception as e:
                tests.append({
                    "name": "Extensão vector habilitada",
                    "success": False,
                    "message": f"Erro ao verificar extensão: {str(e)}"
                })
        
        # Teste 2: Criar tabela temporária com coluna vetorial
        with conn.cursor() as cur:
            try:
                cur.execute("CREATE TEMP TABLE test_vectors (id serial PRIMARY KEY, embedding vector(3));")
                tests.append({
                    "name": "Criar tabela com coluna vetorial",
                    "success": True,
                    "message": "Tabela temporária criada com sucesso"
                })
            except Exception as e:
                tests.append({
                    "name": "Criar tabela com coluna vetorial",
                    "success": False,
                    "message": f"Erro ao criar tabela: {str(e)}"
                })
                # Se falhar aqui, não continuar com os outros testes
                conn.close()
                return {
                    "success": False,
                    "message": "Falha ao criar tabela vetorial",
                    "tests": tests
                }
        
        # Teste 3: Inserir vetores
        with conn.cursor() as cur:
            try:
                # Criar alguns vetores de teste
                vectors = [
                    [1.0, 2.0, 3.0],
                    [4.0, 5.0, 6.0],
                    [7.0, 8.0, 9.0]
                ]
                
                for vec in vectors:
                    cur.execute("INSERT INTO test_vectors (embedding) VALUES (%s);", (vec,))
                
                tests.append({
                    "name": "Inserir vetores",
                    "success": True,
                    "message": f"Inseridos {len(vectors)} vetores com sucesso"
                })
            except Exception as e:
                tests.append({
                    "name": "Inserir vetores",
                    "success": False,
                    "message": f"Erro ao inserir vetores: {str(e)}"
                })
                # Se falhar aqui, não continuar com os outros testes
                conn.close()
                return {
                    "success": False,
                    "message": "Falha ao inserir vetores",
                    "tests": tests
                }
        
        # Teste 4: Consulta de similaridade L2
        with conn.cursor() as cur:
            try:
                query_vector = [2.0, 3.0, 4.0]
                cur.execute(
                    "SELECT id, embedding <-> %s AS distance FROM test_vectors ORDER BY distance LIMIT 1;",
                    (query_vector,)
                )
                result = cur.fetchone()
                tests.append({
                    "name": "Consulta de similaridade L2",
                    "success": result is not None,
                    "message": f"Consulta L2 bem-sucedida, ID mais próximo: {result[0]}" if result else "Nenhum resultado encontrado"
                })
            except Exception as e:
                tests.append({
                    "name": "Consulta de similaridade L2",
                    "success": False,
                    "message": f"Erro na consulta L2: {str(e)}"
                })
        
        # Teste 5: Consulta de similaridade de produto interno
        with conn.cursor() as cur:
            try:
                query_vector = [2.0, 3.0, 4.0]
                cur.execute(
                    "SELECT id, embedding <#> %s AS distance FROM test_vectors ORDER BY distance LIMIT 1;",
                    (query_vector,)
                )
                result = cur.fetchone()
                tests.append({
                    "name": "Consulta de similaridade de produto interno",
                    "success": result is not None,
                    "message": f"Consulta de produto interno bem-sucedida, ID mais próximo: {result[0]}" if result else "Nenhum resultado encontrado"
                })
            except Exception as e:
                tests.append({
                    "name": "Consulta de similaridade de produto interno",
                    "success": False,
                    "message": f"Erro na consulta de produto interno: {str(e)}"
                })
        
        # Teste 6: Consulta de similaridade de cosseno
        with conn.cursor() as cur:
            try:
                query_vector = [2.0, 3.0, 4.0]
                cur.execute(
                    "SELECT id, embedding <=> %s AS distance FROM test_vectors ORDER BY distance LIMIT 1;",
                    (query_vector,)
                )
                result = cur.fetchone()
                tests.append({
                    "name": "Consulta de similaridade de cosseno",
                    "success": result is not None,
                    "message": f"Consulta de cosseno bem-sucedida, ID mais próximo: {result[0]}" if result else "Nenhum resultado encontrado"
                })
            except Exception as e:
                tests.append({
                    "name": "Consulta de similaridade de cosseno",
                    "success": False,
                    "message": f"Erro na consulta de cosseno: {str(e)}"
                })
        
        # Teste 7: Criar índice vetorial
        with conn.cursor() as cur:
            try:
                cur.execute("CREATE INDEX ON test_vectors USING ivfflat (embedding vector_l2_ops);")
                tests.append({
                    "name": "Criar índice vetorial",
                    "success": True,
                    "message": "Índice vetorial criado com sucesso"
                })
            except Exception as e:
                tests.append({
                    "name": "Criar índice vetorial",
                    "success": False,
                    "message": f"Erro ao criar índice: {str(e)}"
                })
        
        # Limpar tabela temporária
        with conn.cursor() as cur:
            try:
                cur.execute("DROP TABLE test_vectors;")
            except:
                pass
        
        # Fechar conexão
        conn.close()
        
        # Verificar se todos os testes foram bem-sucedidos
        all_success = all(test["success"] for test in tests)
        
        return {
            "success": all_success,
            "message": "Todos os testes de funções vetoriais foram bem-sucedidos" if all_success else "Alguns testes de funções vetoriais falharam",
            "tests": tests
        }
    except Exception as e:
        logger.error(f"Erro ao testar funções vetoriais: {e}")
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "message": f"Erro ao testar funções vetoriais: {str(e)}",
            "tests": []
        }

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
        "# Relatório de Verificação de Funções Vetoriais no Supabase",
        f"Data: {now}\n",
        "## Resumo",
    ]
    
    # Adicionar resumo
    total_containers = len(results["containers"])
    pgvector_installed_count = sum(1 for c in results["containers"] if c.get("extensions_check", {}).get("pgvector_installed", False))
    vector_functions_working = sum(1 for c in results["containers"] if c.get("vector_tests", {}).get("success", False))
    
    report.extend([
        f"- Total de contêineres analisados: {total_containers}",
        f"- Contêineres com pgvector instalado: {pgvector_installed_count}/{total_containers}",
        f"- Contêineres com funções vetoriais funcionando: {vector_functions_working}/{total_containers}\n"
    ])
    
    # Adicionar detalhes por contêiner
    for container in results["containers"]:
        container_name = container["name"]
        container_id = container["id"]
        
        report.append(f"## Contêiner: {container_name} ({container_id[:12]})")
        
        # Verificação de extensões
        report.append("\n### Extensões PostgreSQL")
        
        extensions_check = container.get("extensions_check", {})
        if extensions_check.get("success", False):
            pgvector_status = "✅ Instalada" if extensions_check.get("pgvector_installed", False) else "❌ Não instalada"
            report.append(f"- Extensão pgvector: {pgvector_status}")
            
            report.append("\n#### Lista de Extensões Instaladas")
            extensions = extensions_check.get("extensions", [])
            if extensions:
                report.append("| Nome | Versão Padrão | Versão Instalada | Descrição |")
                report.append("| ---- | ------------- | ---------------- | --------- |")
                for ext in extensions:
                    name = ext.get("name", "")
                    default_version = ext.get("default_version", "")
                    installed_version = ext.get("installed_version", "")
                    comment = ext.get("comment", "").replace("\n", " ")
                    report.append(f"| {name} | {default_version} | {installed_version} | {comment} |")
            else:
                report.append("Nenhuma extensão encontrada.")
        else:
            report.append(f"❌ **Falha**: {extensions_check.get('message', 'Erro desconhecido')}")
        
        # Testes de funções vetoriais
        report.append("\n### Testes de Funções Vetoriais")
        
        vector_tests = container.get("vector_tests", {})
        if vector_tests.get("success", False):
            report.append("✅ **Todos os testes de funções vetoriais foram bem-sucedidos**")
        else:
            report.append(f"❌ **Falha**: {vector_tests.get('message', 'Erro desconhecido')}")
        
        # Detalhes dos testes
        tests = vector_tests.get("tests", [])
        if tests:
            report.append("\n#### Detalhes dos Testes")
            report.append("| Teste | Resultado | Mensagem |")
            report.append("| ----- | --------- | -------- |")
            for test in tests:
                name = test.get("name", "")
                success = "✅ Sucesso" if test.get("success", False) else "❌ Falha"
                message = test.get("message", "").replace("\n", " ")
                report.append(f"| {name} | {success} | {message} |")
        
        report.append("\n---\n")
    
    # Adicionar recomendações
    report.append("## Recomendações")
    
    if pgvector_installed_count < total_containers:
        report.append("\n### Instalação da Extensão pgvector")
        report.append("Para instalar a extensão pgvector no Supabase:")
        report.append("1. Acesse o painel de administração do Supabase")
        report.append("2. Vá para a seção SQL")
        report.append("3. Execute o seguinte comando SQL:")
        report.append("```sql")
        report.append("CREATE EXTENSION IF NOT EXISTS vector;")
        report.append("```")
    
    if vector_functions_working < total_containers:
        report.append("\n### Configuração de Funções Vetoriais")
        report.append("Se as funções vetoriais não estiverem funcionando corretamente:")
        report.append("1. Verifique se a extensão pgvector está instalada")
        report.append("2. Certifique-se de que o tipo de dados `vector` está sendo usado corretamente")
        report.append("3. Teste as operações de similaridade (`<->`, `<#>`, `<=>`) com vetores simples")
        report.append("4. Verifique se há erros nos logs do PostgreSQL")
    
    return "\n".join(report)

def main():
    """Função principal do script."""
    logger.info("Verificando funções vetoriais no Supabase...")
    
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
        
        # Extrair URL do banco de dados
        db_url = extract_database_url(env_vars)
        
        container_result = {
            "id": container_id,
            "name": container_name,
            "db_url_found": db_url is not None
        }
        
        if db_url:
            # Verificar extensões PostgreSQL
            extensions_check = check_postgres_extensions(db_url)
            container_result["extensions_check"] = extensions_check
            
            # Se pgvector estiver instalado, testar funções vetoriais
            if extensions_check.get("pgvector_installed", False):
                vector_tests = test_vector_functions(db_url)
                container_result["vector_tests"] = vector_tests
            else:
                container_result["vector_tests"] = {
                    "success": False,
                    "message": "Extensão pgvector não está instalada",
                    "tests": []
                }
        else:
            logger.warning(f"URL do banco de dados não encontrada para o contêiner {container_name}")
            container_result["extensions_check"] = {
                "success": False,
                "message": "URL do banco de dados não encontrada",
                "extensions": []
            }
        
        results["containers"].append(container_result)
    
    # Gerar relatório
    report = generate_report(results)
    
    # Salvar relatório em arquivo
    report_path = os.path.join(os.path.dirname(__file__), "..", "reports")
    os.makedirs(report_path, exist_ok=True)
    
    report_file = os.path.join(report_path, "vector_functions_report.md")
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)
    
    logger.info(f"Relatório salvo em: {report_file}")
    
    # Exibir resumo
    pgvector_installed_count = sum(1 for c in results["containers"] if c.get("extensions_check", {}).get("pgvector_installed", False))
    vector_functions_working = sum(1 for c in results["containers"] if c.get("vector_tests", {}).get("success", False))
    total_containers = len(results["containers"])
    
    if pgvector_installed_count == total_containers and vector_functions_working == total_containers:
        logger.info("✅ A extensão pgvector está instalada e as funções vetoriais estão funcionando corretamente em todos os contêineres.")
    else:
        if pgvector_installed_count < total_containers:
            logger.warning(f"⚠️ A extensão pgvector está instalada em apenas {pgvector_installed_count} de {total_containers} contêineres.")
        
        if vector_functions_working < total_containers:
            logger.warning(f"⚠️ As funções vetoriais estão funcionando corretamente em apenas {vector_functions_working} de {total_containers} contêineres.")
        
        logger.info(f"Para mais detalhes, consulte o relatório: {report_file}")

if __name__ == "__main__":
    main()