#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para mapear endpoints disponíveis nas APIs REST do Renum e Suna.
Este script lista todos os endpoints definidos, verifica a documentação OpenAPI/Swagger
e compara com a especificação esperada.
"""

import os
import sys
import json
import logging
import subprocess
import requests
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
logger = logging.getLogger("endpoint_mapping")

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

def get_container_ids(service_pattern: str = "") -> List[Dict[str, str]]:
    """
    Obtém IDs e nomes dos contêineres que correspondem ao padrão.
    
    Args:
        service_pattern: Padrão para filtrar contêineres (opcional)
        
    Returns:
        Lista de dicionários com ID e nome dos contêineres
    """
    filter_arg = f'--filter "name={service_pattern}"' if service_pattern else ""
    stdout, stderr, returncode = run_command(f'docker ps -a {filter_arg} --format "{{{{.ID}}}}|{{{{.Names}}}}"')
    
    if returncode != 0:
        logger.error(f"Erro ao listar contêineres: {stderr}")
        return []
    
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
    stdout, stderr, returncode = run_command(f'docker inspect --format "{{{{json .Config.Env}}}}" {container_id}')
    
    if returncode != 0:
        logger.error(f"Erro ao obter variáveis de ambiente do contêiner {container_id}: {stderr}")
        return {}
    
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

def get_container_port_mappings(container_id: str) -> List[Dict]:
    """
    Obtém os mapeamentos de portas de um contêiner.
    
    Args:
        container_id: ID do contêiner
        
    Returns:
        Lista de dicionários com mapeamentos de portas
    """
    stdout, stderr, returncode = run_command(f'docker inspect --format "{{{{json .NetworkSettings.Ports}}}}" {container_id}')
    
    if returncode != 0:
        logger.error(f"Erro ao obter mapeamentos de portas do contêiner {container_id}: {stderr}")
        return []
    
    try:
        ports_json = json.loads(stdout)
        port_mappings = []
        
        for container_port, host_bindings in ports_json.items():
            if host_bindings:
                for binding in host_bindings:
                    port_mappings.append({
                        "container_port": container_port,
                        "host_ip": binding.get("HostIp", "0.0.0.0"),
                        "host_port": binding.get("HostPort", "")
                    })
        
        return port_mappings
    except json.JSONDecodeError:
        logger.error(f"Erro ao decodificar JSON para o contêiner {container_id}")
        return []

def get_swagger_docs(url: str) -> Dict:
    """
    Obtém a documentação Swagger/OpenAPI de uma URL.
    
    Args:
        url: URL da documentação Swagger/OpenAPI
        
    Returns:
        Dicionário com a documentação Swagger/OpenAPI
    """
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            logger.warning(f"Falha ao obter documentação Swagger: {response.status_code}")
            return {}
    except Exception as e:
        logger.error(f"Erro ao obter documentação Swagger: {e}")
        return {}

def extract_endpoints_from_swagger(swagger_docs: Dict) -> List[Dict]:
    """
    Extrai endpoints da documentação Swagger/OpenAPI.
    
    Args:
        swagger_docs: Documentação Swagger/OpenAPI
        
    Returns:
        Lista de dicionários com informações dos endpoints
    """
    endpoints = []
    
    if not swagger_docs:
        return endpoints
    
    # Verificar versão do OpenAPI
    if "swagger" in swagger_docs and swagger_docs["swagger"].startswith("2."):
        # OpenAPI 2.0 (Swagger)
        paths = swagger_docs.get("paths", {})
        
        for path, methods in paths.items():
            for method, details in methods.items():
                if method.lower() not in ["get", "post", "put", "delete", "patch", "options", "head"]:
                    continue
                
                endpoint = {
                    "path": path,
                    "method": method.upper(),
                    "summary": details.get("summary", ""),
                    "description": details.get("description", ""),
                    "tags": details.get("tags", []),
                    "parameters": details.get("parameters", []),
                    "responses": details.get("responses", {})
                }
                
                endpoints.append(endpoint)
    
    elif "openapi" in swagger_docs and swagger_docs["openapi"].startswith("3."):
        # OpenAPI 3.0
        paths = swagger_docs.get("paths", {})
        
        for path, methods in paths.items():
            for method, details in methods.items():
                if method.lower() not in ["get", "post", "put", "delete", "patch", "options", "head"]:
                    continue
                
                endpoint = {
                    "path": path,
                    "method": method.upper(),
                    "summary": details.get("summary", ""),
                    "description": details.get("description", ""),
                    "tags": details.get("tags", []),
                    "parameters": details.get("parameters", []),
                    "responses": details.get("responses", {})
                }
                
                endpoints.append(endpoint)
    
    return endpoints

def extract_endpoints_from_fastapi_routes(container_id: str) -> List[Dict]:
    """
    Extrai endpoints das rotas do FastAPI executando um script no contêiner.
    
    Args:
        container_id: ID do contêiner
        
    Returns:
        Lista de dicionários com informações dos endpoints
    """
    # Criar script temporário para extrair rotas
    script_content = """
import sys
import json
from importlib import import_module

try:
    # Tentar importar a aplicação FastAPI
    from fastapi import FastAPI
    import inspect
    import os
    
    # Procurar por arquivos que podem conter a aplicação FastAPI
    app = None
    app_files = ["api.py", "main.py", "app.py", "server.py"]
    
    for app_file in app_files:
        if os.path.exists(app_file):
            try:
                # Tentar importar o módulo
                module_name = app_file.replace(".py", "")
                module = import_module(module_name)
                
                # Procurar por instâncias de FastAPI
                for name, obj in inspect.getmembers(module):
                    if isinstance(obj, FastAPI):
                        app = obj
                        break
                
                if app:
                    break
            except Exception as e:
                print(f"Erro ao importar {app_file}: {e}", file=sys.stderr)
    
    if not app:
        # Tentar encontrar a aplicação em subdiretórios
        for root, dirs, files in os.walk("."):
            for file in files:
                if file in app_files:
                    try:
                        # Construir caminho de importação
                        import_path = os.path.join(root, file).replace("/", ".").replace("\\\\", ".").replace(".py", "")
                        if import_path.startswith("."):
                            import_path = import_path[1:]
                        
                        module = import_module(import_path)
                        
                        # Procurar por instâncias de FastAPI
                        for name, obj in inspect.getmembers(module):
                            if isinstance(obj, FastAPI):
                                app = obj
                                break
                        
                        if app:
                            break
                    except Exception as e:
                        print(f"Erro ao importar {os.path.join(root, file)}: {e}", file=sys.stderr)
            
            if app:
                break
    
    if app:
        # Extrair rotas
        routes = []
        for route in app.routes:
            route_info = {
                "path": getattr(route, "path", ""),
                "methods": getattr(route, "methods", []),
                "name": getattr(route, "name", ""),
                "endpoint": str(getattr(route, "endpoint", ""))
            }
            routes.append(route_info)
        
        print(json.dumps(routes))
    else:
        print("Aplicação FastAPI não encontrada", file=sys.stderr)
        sys.exit(1)

except ImportError as e:
    print(f"Erro de importação: {e}", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f"Erro: {e}", file=sys.stderr)
    sys.exit(1)
"""
    
    # Criar arquivo temporário no contêiner
    script_path = "/tmp/extract_fastapi_routes.py"
    stdout, stderr, returncode = run_command(f'docker exec {container_id} bash -c "cat > {script_path} << \\'EOF\\'\n{script_content}\nEOF"')
    
    if returncode != 0:
        logger.error(f"Erro ao criar script temporário no contêiner {container_id}: {stderr}")
        return []
    
    # Executar script
    stdout, stderr, returncode = run_command(f'docker exec {container_id} python {script_path}')
    
    # Limpar arquivo temporário
    run_command(f'docker exec {container_id} rm {script_path}')
    
    if returncode != 0:
        logger.error(f"Erro ao executar script no contêiner {container_id}: {stderr}")
        return []
    
    try:
        routes = json.loads(stdout)
        
        # Converter para o formato padrão
        endpoints = []
        for route in routes:
            path = route.get("path", "")
            methods = route.get("methods", [])
            
            for method in methods:
                endpoints.append({
                    "path": path,
                    "method": method,
                    "name": route.get("name", ""),
                    "endpoint": route.get("endpoint", "")
                })
        
        return endpoints
    except json.JSONDecodeError:
        logger.error(f"Erro ao decodificar JSON das rotas: {stdout}")
        return []

def extract_endpoints_from_files(container_id: str) -> List[Dict]:
    """
    Extrai endpoints analisando arquivos de código-fonte no contêiner.
    
    Args:
        container_id: ID do contêiner
        
    Returns:
        Lista de dicionários com informações dos endpoints
    """
    # Procurar por arquivos de rotas
    stdout, stderr, returncode = run_command(f'docker exec {container_id} find /app -type f -name "*.py" | grep -E "routes|api|endpoints"')
    
    if returncode != 0 and not stdout:
        # Tentar procurar em outros diretórios
        stdout, stderr, returncode = run_command(f'docker exec {container_id} find / -type f -name "*.py" | grep -E "routes|api|endpoints" | grep -v "venv|site-packages"')
    
    if not stdout:
        logger.warning(f"Nenhum arquivo de rotas encontrado no contêiner {container_id}")
        return []
    
    route_files = stdout.splitlines()
    endpoints = []
    
    for file_path in route_files:
        # Ler conteúdo do arquivo
        stdout, stderr, returncode = run_command(f'docker exec {container_id} cat {file_path}')
        
        if returncode != 0:
            logger.warning(f"Erro ao ler arquivo {file_path}: {stderr}")
            continue
        
        file_content = stdout
        
        # Procurar por padrões de definição de rotas
        # FastAPI
        fastapi_patterns = [
            r'@app\.([a-z]+)\("([^"]+)"',  # @app.get("/path")
            r'@router\.([a-z]+)\("([^"]+)"',  # @router.get("/path")
            r'@api\.([a-z]+)\("([^"]+)"'  # @api.get("/path")
        ]
        
        for pattern in fastapi_patterns:
            import re
            matches = re.findall(pattern, file_content)
            
            for match in matches:
                method, path = match
                endpoints.append({
                    "path": path,
                    "method": method.upper(),
                    "file": file_path,
                    "source": "file_analysis"
                })
    
    return endpoints

def compare_with_expected_endpoints(found_endpoints: List[Dict], expected_endpoints: List[Dict]) -> Dict:
    """
    Compara os endpoints encontrados com os endpoints esperados.
    
    Args:
        found_endpoints: Lista de endpoints encontrados
        expected_endpoints: Lista de endpoints esperados
        
    Returns:
        Dicionário com resultados da comparação
    """
    # Normalizar endpoints encontrados
    normalized_found = {}
    for endpoint in found_endpoints:
        key = f"{endpoint['method']}:{endpoint['path']}"
        normalized_found[key] = endpoint
    
    # Normalizar endpoints esperados
    normalized_expected = {}
    for endpoint in expected_endpoints:
        key = f"{endpoint['method']}:{endpoint['path']}"
        normalized_expected[key] = endpoint
    
    # Encontrar endpoints em comum, ausentes e extras
    common_keys = set(normalized_found.keys()) & set(normalized_expected.keys())
    missing_keys = set(normalized_expected.keys()) - set(normalized_found.keys())
    extra_keys = set(normalized_found.keys()) - set(normalized_expected.keys())
    
    return {
        "common": [normalized_found[key] for key in common_keys],
        "missing": [normalized_expected[key] for key in missing_keys],
        "extra": [normalized_found[key] for key in extra_keys]
    }

def generate_report(results: Dict) -> str:
    """
    Gera um relatório formatado com os resultados do mapeamento de endpoints.
    
    Args:
        results: Dicionário com resultados do mapeamento
        
    Returns:
        Relatório formatado em Markdown
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = [
        "# Relatório de Mapeamento de Endpoints",
        f"Data: {now}\n",
        "## Resumo",
    ]
    
    # Adicionar resumo
    total_services = len(results["services"])
    total_endpoints = sum(len(service["endpoints"]) for service in results["services"])
    
    report.extend([
        f"- Total de serviços analisados: {total_services}",
        f"- Total de endpoints encontrados: {total_endpoints}\n"
    ])
    
    # Adicionar detalhes por serviço
    for service in results["services"]:
        service_name = service["name"]
        endpoints = service["endpoints"]
        
        report.append(f"## Serviço: {service_name}")
        
        # Informações do serviço
        if "container_id" in service:
            report.append(f"- **Container ID**: {service['container_id'][:12]}")
        
        if "port_mappings" in service and service["port_mappings"]:
            report.append("- **Mapeamentos de Portas**:")
            for mapping in service["port_mappings"]:
                container_port = mapping.get("container_port", "")
                host_port = mapping.get("host_port", "")
                host_ip = mapping.get("host_ip", "0.0.0.0")
                report.append(f"  - {container_port} -> {host_ip}:{host_port}")
        
        # Documentação Swagger
        if "swagger_url" in service:
            swagger_status = "✅ Disponível" if service.get("swagger_available", False) else "❌ Não disponível"
            report.append(f"- **Documentação Swagger**: {swagger_status}")
            report.append(f"  - URL: {service['swagger_url']}")
        
        # Endpoints
        if endpoints:
            report.append(f"\n### Endpoints ({len(endpoints)})")
            report.append("| Método | Caminho | Descrição |")
            report.append("| ------ | ------- | --------- |")
            
            # Ordenar endpoints por método e caminho
            sorted_endpoints = sorted(endpoints, key=lambda e: (e.get("method", ""), e.get("path", "")))
            
            for endpoint in sorted_endpoints:
                method = endpoint.get("method", "")
                path = endpoint.get("path", "")
                description = endpoint.get("summary", "") or endpoint.get("description", "") or ""
                report.append(f"| {method} | {path} | {description} |")
        else:
            report.append("\nNenhum endpoint encontrado.")
        
        report.append("\n")
    
    # Adicionar comparação com endpoints esperados
    if "comparison" in results:
        comparison = results["comparison"]
        
        report.append("## Comparação com Endpoints Esperados")
        
        common = comparison.get("common", [])
        missing = comparison.get("missing", [])
        extra = comparison.get("extra", [])
        
        report.append(f"- **Endpoints em comum**: {len(common)}")
        report.append(f"- **Endpoints ausentes**: {len(missing)}")
        report.append(f"- **Endpoints extras**: {len(extra)}")
        
        if missing:
            report.append("\n### Endpoints Ausentes")
            report.append("| Método | Caminho | Descrição |")
            report.append("| ------ | ------- | --------- |")
            
            for endpoint in missing:
                method = endpoint.get("method", "")
                path = endpoint.get("path", "")
                description = endpoint.get("description", "")
                report.append(f"| {method} | {path} | {description} |")
        
        if extra:
            report.append("\n### Endpoints Extras")
            report.append("| Método | Caminho | Descrição |")
            report.append("| ------ | ------- | --------- |")
            
            for endpoint in extra:
                method = endpoint.get("method", "")
                path = endpoint.get("path", "")
                description = endpoint.get("summary", "") or endpoint.get("description", "") or ""
                report.append(f"| {method} | {path} | {description} |")
    
    # Adicionar recomendações
    report.append("\n## Recomendações")
    
    if "comparison" in results and results["comparison"].get("missing"):
        report.append("\n### Endpoints Ausentes")
        report.append("1. **Verificar implementação** - Certifique-se de que os endpoints ausentes estão implementados")
        report.append("2. **Atualizar documentação** - Atualize a documentação Swagger/OpenAPI para incluir os endpoints ausentes")
        report.append("3. **Verificar rotas** - Certifique-se de que as rotas estão registradas corretamente")
    
    if not any(service.get("swagger_available", False) for service in results["services"]):
        report.append("\n### Documentação Swagger/OpenAPI")
        report.append("1. **Habilitar documentação** - Considere habilitar a documentação Swagger/OpenAPI para facilitar o desenvolvimento e testes")
        report.append("2. **Expor endpoints de documentação** - Certifique-se de que os endpoints de documentação estão expostos corretamente")
    
    return "\n".join(report)

def main():
    """Função principal do script."""
    logger.info("Mapeando endpoints disponíveis...")
    
    results = {
        "services": []
    }
    
    # Definir endpoints esperados (baseado na especificação)
    expected_endpoints = [
        # Renum API
        {"method": "GET", "path": "/api/health", "description": "Verificação de saúde da API"},
        {"method": "GET", "path": "/api/rag/search", "description": "Busca semântica no RAG"},
        {"method": "POST", "path": "/api/rag/index", "description": "Indexar documento no RAG"},
        {"method": "GET", "path": "/api/auth/me", "description": "Obter informações do usuário autenticado"},
        {"method": "POST", "path": "/api/auth/login", "description": "Login de usuário"},
        {"method": "POST", "path": "/api/auth/register", "description": "Registro de usuário"},
        {"method": "POST", "path": "/api/agent/query", "description": "Consulta ao agente"},
        
        # Suna API
        {"method": "GET", "path": "/api/health", "description": "Verificação de saúde da API"},
        {"method": "POST", "path": "/api/agent/execute", "description": "Executar agente"},
        {"method": "GET", "path": "/api/agent/status", "description": "Status do agente"},
        {"method": "POST", "path": "/api/knowledge/search", "description": "Busca na base de conhecimento"}
    ]
    
    # Obter contêineres Renum e Suna
    renum_containers = get_container_ids("renum")
    suna_containers = get_container_ids("suna")
    
    all_endpoints = []
    
    # Analisar contêineres Renum
    for container in renum_containers:
        container_id = container["id"]
        container_name = container["name"]
        
        logger.info(f"Analisando contêiner: {container_name} ({container_id[:12]})")
        
        # Obter mapeamentos de portas
        port_mappings = get_container_port_mappings(container_id)
        
        # Obter variáveis de ambiente
        env_vars = get_container_env_vars(container_id)
        
        # Tentar encontrar URL da documentação Swagger
        swagger_url = None
        swagger_docs = {}
        swagger_available = False
        
        # Verificar portas HTTP comuns
        http_ports = ["80", "8000", "8080", "8888", "3000", "5000"]
        
        for mapping in port_mappings:
            container_port = mapping.get("container_port", "")
            if container_port.startswith(tuple(f"{port}/tcp" for port in http_ports)):
                host_port = mapping.get("host_port", "")
                if host_port:
                    # Tentar URLs comuns de documentação Swagger
                    swagger_paths = [
                        "/docs",
                        "/swagger",
                        "/api/docs",
                        "/api/swagger",
                        "/swagger-ui",
                        "/openapi.json"
                    ]
                    
                    for path in swagger_paths:
                        url = f"http://localhost:{host_port}{path}"
                        try:
                            response = requests.get(url, timeout=2)
                            if response.status_code == 200:
                                if path.endswith(".json"):
                                    # Tentar analisar como JSON
                                    try:
                                        swagger_docs = response.json()
                                        swagger_url = url
                                        swagger_available = True
                                        break
                                    except:
                                        pass
                                else:
                                    # Verificar se é uma página HTML de documentação Swagger
                                    content = response.text.lower()
                                    if "swagger" in content or "openapi" in content:
                                        # Tentar obter o JSON da documentação
                                        json_url = f"http://localhost:{host_port}/openapi.json"
                                        try:
                                            json_response = requests.get(json_url, timeout=2)
                                            if json_response.status_code == 200:
                                                swagger_docs = json_response.json()
                                                swagger_url = url
                                                swagger_available = True
                                                break
                                        except:
                                            pass
                        except:
                            pass
        
        # Extrair endpoints da documentação Swagger
        swagger_endpoints = extract_endpoints_from_swagger(swagger_docs)
        
        # Tentar extrair endpoints das rotas do FastAPI
        fastapi_endpoints = extract_endpoints_from_fastapi_routes(container_id)
        
        # Tentar extrair endpoints analisando arquivos
        file_endpoints = extract_endpoints_from_files(container_id)
        
        # Combinar endpoints de todas as fontes
        all_container_endpoints = swagger_endpoints + fastapi_endpoints + file_endpoints
        
        # Remover duplicatas
        unique_endpoints = []
        seen_keys = set()
        
        for endpoint in all_container_endpoints:
            key = f"{endpoint.get('method', '')}:{endpoint.get('path', '')}"
            if key not in seen_keys:
                seen_keys.add(key)
                unique_endpoints.append(endpoint)
        
        # Adicionar endpoints ao resultado
        service_result = {
            "name": container_name,
            "container_id": container_id,
            "port_mappings": port_mappings,
            "swagger_url": swagger_url,
            "swagger_available": swagger_available,
            "endpoints": unique_endpoints
        }
        
        results["services"].append(service_result)
        all_endpoints.extend(unique_endpoints)
    
    # Analisar contêineres Suna
    for container in suna_containers:
        container_id = container["id"]
        container_name = container["name"]
        
        logger.info(f"Analisando contêiner: {container_name} ({container_id[:12]})")
        
        # Obter mapeamentos de portas
        port_mappings = get_container_port_mappings(container_id)
        
        # Obter variáveis de ambiente
        env_vars = get_container_env_vars(container_id)
        
        # Tentar encontrar URL da documentação Swagger
        swagger_url = None
        swagger_docs = {}
        swagger_available = False
        
        # Verificar portas HTTP comuns
        http_ports = ["80", "8000", "8080", "8888", "3000", "5000"]
        
        for mapping in port_mappings:
            container_port = mapping.get("container_port", "")
            if container_port.startswith(tuple(f"{port}/tcp" for port in http_ports)):
                host_port = mapping.get("host_port", "")
                if host_port:
                    # Tentar URLs comuns de documentação Swagger
                    swagger_paths = [
                        "/docs",
                        "/swagger",
                        "/api/docs",
                        "/api/swagger",
                        "/swagger-ui",
                        "/openapi.json"
                    ]
                    
                    for path in swagger_paths:
                        url = f"http://localhost:{host_port}{path}"
                        try:
                            response = requests.get(url, timeout=2)
                            if response.status_code == 200:
                                if path.endswith(".json"):
                                    # Tentar analisar como JSON
                                    try:
                                        swagger_docs = response.json()
                                        swagger_url = url
                                        swagger_available = True
                                        break
                                    except:
                                        pass
                                else:
                                    # Verificar se é uma página HTML de documentação Swagger
                                    content = response.text.lower()
                                    if "swagger" in content or "openapi" in content:
                                        # Tentar obter o JSON da documentação
                                        json_url = f"http://localhost:{host_port}/openapi.json"
                                        try:
                                            json_response = requests.get(json_url, timeout=2)
                                            if json_response.status_code == 200:
                                                swagger_docs = json_response.json()
                                                swagger_url = url
                                                swagger_available = True
                                                break
                                        except:
                                            pass
                        except:
                            pass
        
        # Extrair endpoints da documentação Swagger
        swagger_endpoints = extract_endpoints_from_swagger(swagger_docs)
        
        # Tentar extrair endpoints das rotas do FastAPI
        fastapi_endpoints = extract_endpoints_from_fastapi_routes(container_id)
        
        # Tentar extrair endpoints analisando arquivos
        file_endpoints = extract_endpoints_from_files(container_id)
        
        # Combinar endpoints de todas as fontes
        all_container_endpoints = swagger_endpoints + fastapi_endpoints + file_endpoints
        
        # Remover duplicatas
        unique_endpoints = []
        seen_keys = set()
        
        for endpoint in all_container_endpoints:
            key = f"{endpoint.get('method', '')}:{endpoint.get('path', '')}"
            if key not in seen_keys:
                seen_keys.add(key)
                unique_endpoints.append(endpoint)
        
        # Adicionar endpoints ao resultado
        service_result = {
            "name": container_name,
            "container_id": container_id,
            "port_mappings": port_mappings,
            "swagger_url": swagger_url,
            "swagger_available": swagger_available,
            "endpoints": unique_endpoints
        }
        
        results["services"].append(service_result)
        all_endpoints.extend(unique_endpoints)
    
    # Comparar com endpoints esperados
    comparison = compare_with_expected_endpoints(all_endpoints, expected_endpoints)
    results["comparison"] = comparison
    
    # Gerar relatório
    report = generate_report(results)
    
    # Salvar relatório em arquivo
    report_path = os.path.join(os.path.dirname(__file__), "..", "reports")
    os.makedirs(report_path, exist_ok=True)
    
    report_file = os.path.join(report_path, "endpoints_mapping_report.md")
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)
    
    logger.info(f"Relatório salvo em: {report_file}")
    
    # Exibir resumo
    total_services = len(results["services"])
    total_endpoints = sum(len(service["endpoints"]) for service in results["services"])
    
    logger.info(f"Total de serviços analisados: {total_services}")
    logger.info(f"Total de endpoints encontrados: {total_endpoints}")
    
    if "comparison" in results:
        missing_count = len(results["comparison"].get("missing", []))
        if missing_count > 0:
            logger.warning(f"⚠️ {missing_count} endpoints esperados não foram encontrados")
            logger.info(f"Para mais detalhes, consulte o relatório: {report_file}")
        else:
            logger.info("✅ Todos os endpoints esperados foram encontrados")

if __name__ == "__main__":
    main()