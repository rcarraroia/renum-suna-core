#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para testar a resposta dos endpoints das APIs REST do Renum e Suna.
Este script executa requisições para endpoints principais, verifica códigos de status
e formatos de resposta, e identifica endpoints com problemas.
"""

import os
import sys
import json
import logging
import subprocess
import requests
import time
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
logger = logging.getLogger("endpoint_testing")

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

def test_endpoint(base_url: str, endpoint: Dict, auth_token: Optional[str] = None) -> Dict:
    """
    Testa um endpoint específico.
    
    Args:
        base_url: URL base da API
        endpoint: Dicionário com informações do endpoint
        auth_token: Token de autenticação (opcional)
        
    Returns:
        Dicionário com resultados do teste
    """
    method = endpoint.get("method", "GET").upper()
    path = endpoint.get("path", "")
    
    # Construir URL completa
    url = f"{base_url}{path}"
    
    # Preparar cabeçalhos
    headers = {}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    # Preparar parâmetros
    params = {}
    body = None
    
    # Verificar se o endpoint requer parâmetros
    parameters = endpoint.get("parameters", [])
    for param in parameters:
        param_name = param.get("name", "")
        param_in = param.get("in", "")
        param_required = param.get("required", False)
        param_schema = param.get("schema", {})
        param_type = param_schema.get("type", "string")
        
        # Gerar valor de exemplo para o parâmetro
        if param_required:
            if param_in == "query":
                if param_type == "string":
                    params[param_name] = "test"
                elif param_type == "integer" or param_type == "number":
                    params[param_name] = "1"
                elif param_type == "boolean":
                    params[param_name] = "true"
            elif param_in == "body":
                # Criar corpo da requisição
                if not body:
                    body = {}
                
                # Usar exemplo se disponível
                example = param_schema.get("example")
                if example:
                    body = example
                else:
                    # Criar corpo básico baseado no schema
                    properties = param_schema.get("properties", {})
                    for prop_name, prop_schema in properties.items():
                        prop_type = prop_schema.get("type", "string")
                        if prop_type == "string":
                            body[prop_name] = "test"
                        elif prop_type == "integer" or prop_type == "number":
                            body[prop_name] = 1
                        elif prop_type == "boolean":
                            body[prop_name] = True
                        elif prop_type == "object":
                            body[prop_name] = {}
                        elif prop_type == "array":
                            body[prop_name] = []
    
    # Executar requisição
    try:
        start_time = time.time()
        
        if method == "GET":
            response = requests.get(url, params=params, headers=headers, timeout=10)
        elif method == "POST":
            response = requests.post(url, params=params, json=body, headers=headers, timeout=10)
        elif method == "PUT":
            response = requests.put(url, params=params, json=body, headers=headers, timeout=10)
        elif method == "DELETE":
            response = requests.delete(url, params=params, headers=headers, timeout=10)
        elif method == "PATCH":
            response = requests.patch(url, params=params, json=body, headers=headers, timeout=10)
        elif method == "HEAD":
            response = requests.head(url, params=params, headers=headers, timeout=10)
        elif method == "OPTIONS":
            response = requests.options(url, params=params, headers=headers, timeout=10)
        else:
            return {
                "success": False,
                "message": f"Método HTTP não suportado: {method}",
                "status_code": None,
                "response_time": None,
                "response_body": None,
                "error": "Método não suportado"
            }
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # Analisar resposta
        status_code = response.status_code
        success = 200 <= status_code < 300
        
        # Tentar obter corpo da resposta como JSON
        try:
            response_body = response.json()
        except:
            response_body = response.text
        
        return {
            "success": success,
            "message": f"Status: {status_code}",
            "status_code": status_code,
            "response_time": response_time,
            "response_body": response_body,
            "headers": dict(response.headers)
        }
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "message": "Timeout ao acessar endpoint",
            "status_code": None,
            "response_time": None,
            "response_body": None,
            "error": "Timeout"
        }
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "message": "Erro de conexão ao acessar endpoint",
            "status_code": None,
            "response_time": None,
            "response_body": None,
            "error": "ConnectionError"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Erro ao acessar endpoint: {str(e)}",
            "status_code": None,
            "response_time": None,
            "response_body": None,
            "error": str(e)
        }

def get_auth_token(base_url: str, username: str, password: str) -> Optional[str]:
    """
    Obtém um token de autenticação.
    
    Args:
        base_url: URL base da API
        username: Nome de usuário
        password: Senha
        
    Returns:
        Token de autenticação ou None se falhar
    """
    # Tentar diferentes endpoints de autenticação
    auth_endpoints = [
        "/api/auth/login",
        "/auth/login",
        "/login",
        "/api/login"
    ]
    
    for endpoint in auth_endpoints:
        url = f"{base_url}{endpoint}"
        
        try:
            response = requests.post(
                url,
                json={"username": username, "password": password},
                timeout=10
            )
            
            if response.status_code == 200:
                # Tentar extrair token da resposta
                data = response.json()
                
                # Verificar diferentes formatos de resposta
                if "token" in data:
                    return data["token"]
                elif "access_token" in data:
                    return data["access_token"]
                elif "accessToken" in data:
                    return data["accessToken"]
                elif "data" in data and isinstance(data["data"], dict):
                    token_data = data["data"]
                    if "token" in token_data:
                        return token_data["token"]
                    elif "access_token" in token_data:
                        return token_data["access_token"]
                    elif "accessToken" in token_data:
                        return token_data["accessToken"]
        except:
            pass
    
    return None

def generate_report(results: Dict) -> str:
    """
    Gera um relatório formatado com os resultados dos testes de endpoint.
    
    Args:
        results: Dicionário com resultados dos testes
        
    Returns:
        Relatório formatado em Markdown
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = [
        "# Relatório de Teste de Endpoints",
        f"Data: {now}\n",
        "## Resumo",
    ]
    
    # Adicionar resumo
    total_services = len(results["services"])
    total_endpoints = sum(len(service["endpoints"]) for service in results["services"])
    successful_endpoints = sum(
        sum(1 for endpoint in service["endpoints"] if endpoint["result"]["success"])
        for service in results["services"]
    )
    
    report.extend([
        f"- Total de serviços testados: {total_services}",
        f"- Total de endpoints testados: {total_endpoints}",
        f"- Endpoints com sucesso: {successful_endpoints}/{total_endpoints} ({successful_endpoints/total_endpoints*100:.1f}%)\n"
    ])
    
    # Adicionar detalhes por serviço
    for service in results["services"]:
        service_name = service["name"]
        base_url = service["base_url"]
        endpoints = service["endpoints"]
        
        report.append(f"## Serviço: {service_name}")
        report.append(f"- **URL Base**: {base_url}")
        
        # Calcular estatísticas do serviço
        successful = sum(1 for endpoint in endpoints if endpoint["result"]["success"])
        
        report.append(f"- **Endpoints testados**: {len(endpoints)}")
        report.append(f"- **Endpoints com sucesso**: {successful}/{len(endpoints)} ({successful/len(endpoints)*100:.1f}%)\n")
        
        # Agrupar endpoints por status
        successful_endpoints = [e for e in endpoints if e["result"]["success"]]
        failed_endpoints = [e for e in endpoints if not e["result"]["success"]]
        
        # Mostrar endpoints com falha
        if failed_endpoints:
            report.append("### Endpoints com Falha")
            report.append("| Método | Caminho | Status | Mensagem | Tempo de Resposta |")
            report.append("| ------ | ------- | ------ | -------- | ----------------- |")
            
            for endpoint in failed_endpoints:
                method = endpoint["method"]
                path = endpoint["path"]
                result = endpoint["result"]
                status = result.get("status_code", "N/A")
                message = result.get("message", "").replace("\n", " ")
                response_time = f"{result.get('response_time', 'N/A'):.3f}s" if result.get('response_time') is not None else "N/A"
                
                report.append(f"| {method} | {path} | {status} | {message} | {response_time} |")
            
            report.append("")
        
        # Mostrar endpoints com sucesso
        if successful_endpoints:
            report.append("### Endpoints com Sucesso")
            report.append("| Método | Caminho | Status | Tempo de Resposta |")
            report.append("| ------ | ------- | ------ | ----------------- |")
            
            for endpoint in successful_endpoints:
                method = endpoint["method"]
                path = endpoint["path"]
                result = endpoint["result"]
                status = result.get("status_code", "N/A")
                response_time = f"{result.get('response_time', 'N/A'):.3f}s" if result.get('response_time') is not None else "N/A"
                
                report.append(f"| {method} | {path} | {status} | {response_time} |")
            
            report.append("")
    
    # Adicionar recomendações
    report.append("## Recomendações")
    
    if total_endpoints - successful_endpoints > 0:
        report.append("\n### Problemas Encontrados")
        report.append("1. **Verificar endpoints com falha** - Investigar por que alguns endpoints estão falhando")
        report.append("2. **Verificar autenticação** - Certificar-se de que os endpoints protegidos estão recebendo tokens válidos")
        report.append("3. **Verificar parâmetros** - Certificar-se de que os parâmetros obrigatórios estão sendo fornecidos corretamente")
        report.append("4. **Verificar logs do servidor** - Analisar logs do servidor para identificar erros")
    else:
        report.append("\n✅ Todos os endpoints testados estão funcionando corretamente.")
    
    return "\n".join(report)

def main():
    """Função principal do script."""
    logger.info("Testando resposta dos endpoints...")
    
    results = {
        "services": []
    }
    
    # Definir credenciais de teste
    test_credentials = {
        "username": "test@example.com",
        "password": "password123"
    }
    
    # Obter contêineres Renum e Suna
    renum_containers = get_container_ids("renum")
    suna_containers = get_container_ids("suna")
    
    # Testar endpoints do Renum
    for container in renum_containers:
        container_id = container["id"]
        container_name = container["name"]
        
        logger.info(f"Testando endpoints do contêiner: {container_name} ({container_id[:12]})")
        
        # Obter mapeamentos de portas
        port_mappings = get_container_port_mappings(container_id)
        
        # Encontrar porta HTTP
        http_port = None
        for mapping in port_mappings:
            container_port = mapping.get("container_port", "")
            if container_port.startswith(("80/tcp", "8000/tcp", "8080/tcp", "3000/tcp", "5000/tcp")):
                http_port = mapping.get("host_port", "")
                break
        
        if not http_port:
            logger.warning(f"Nenhuma porta HTTP encontrada para o contêiner {container_name}")
            continue
        
        # Construir URL base
        base_url = f"http://localhost:{http_port}"
        
        # Tentar obter documentação Swagger
        swagger_url = f"{base_url}/openapi.json"
        swagger_docs = get_swagger_docs(swagger_url)
        
        # Extrair endpoints da documentação Swagger
        endpoints = extract_endpoints_from_swagger(swagger_docs)
        
        # Se não encontrou endpoints via Swagger, usar endpoints padrão
        if not endpoints:
            endpoints = [
                {"path": "/api/health", "method": "GET", "description": "Verificação de saúde"},
                {"path": "/api/rag/search", "method": "GET", "description": "Busca semântica"},
                {"path": "/api/auth/me", "method": "GET", "description": "Informações do usuário"},
                {"path": "/api/auth/login", "method": "POST", "description": "Login"},
                {"path": "/api/agent/query", "method": "POST", "description": "Consulta ao agente"}
            ]
        
        # Obter token de autenticação
        auth_token = get_auth_token(base_url, test_credentials["username"], test_credentials["password"])
        
        # Testar cada endpoint
        tested_endpoints = []
        for endpoint in endpoints:
            method = endpoint.get("method", "GET")
            path = endpoint.get("path", "")
            
            logger.info(f"Testando endpoint: {method} {path}")
            
            result = test_endpoint(base_url, endpoint, auth_token)
            
            tested_endpoints.append({
                "method": method,
                "path": path,
                "description": endpoint.get("description", "") or endpoint.get("summary", ""),
                "result": result
            })
        
        # Adicionar resultados ao relatório
        results["services"].append({
            "name": container_name,
            "base_url": base_url,
            "endpoints": tested_endpoints
        })
    
    # Testar endpoints do Suna
    for container in suna_containers:
        container_id = container["id"]
        container_name = container["name"]
        
        logger.info(f"Testando endpoints do contêiner: {container_name} ({container_id[:12]})")
        
        # Obter mapeamentos de portas
        port_mappings = get_container_port_mappings(container_id)
        
        # Encontrar porta HTTP
        http_port = None
        for mapping in port_mappings:
            container_port = mapping.get("container_port", "")
            if container_port.startswith(("80/tcp", "8000/tcp", "8080/tcp", "3000/tcp", "5000/tcp")):
                http_port = mapping.get("host_port", "")
                break
        
        if not http_port:
            logger.warning(f"Nenhuma porta HTTP encontrada para o contêiner {container_name}")
            continue
        
        # Construir URL base
        base_url = f"http://localhost:{http_port}"
        
        # Tentar obter documentação Swagger
        swagger_url = f"{base_url}/openapi.json"
        swagger_docs = get_swagger_docs(swagger_url)
        
        # Extrair endpoints da documentação Swagger
        endpoints = extract_endpoints_from_swagger(swagger_docs)
        
        # Se não encontrou endpoints via Swagger, usar endpoints padrão
        if not endpoints:
            endpoints = [
                {"path": "/api/health", "method": "GET", "description": "Verificação de saúde"},
                {"path": "/api/agent/execute", "method": "POST", "description": "Executar agente"},
                {"path": "/api/agent/status", "method": "GET", "description": "Status do agente"},
                {"path": "/api/knowledge/search", "method": "POST", "description": "Busca na base de conhecimento"}
            ]
        
        # Obter token de autenticação
        auth_token = get_auth_token(base_url, test_credentials["username"], test_credentials["password"])
        
        # Testar cada endpoint
        tested_endpoints = []
        for endpoint in endpoints:
            method = endpoint.get("method", "GET")
            path = endpoint.get("path", "")
            
            logger.info(f"Testando endpoint: {method} {path}")
            
            result = test_endpoint(base_url, endpoint, auth_token)
            
            tested_endpoints.append({
                "method": method,
                "path": path,
                "description": endpoint.get("description", "") or endpoint.get("summary", ""),
                "result": result
            })
        
        # Adicionar resultados ao relatório
        results["services"].append({
            "name": container_name,
            "base_url": base_url,
            "endpoints": tested_endpoints
        })
    
    # Gerar relatório
    report = generate_report(results)
    
    # Salvar relatório em arquivo
    report_path = os.path.join(os.path.dirname(__file__), "..", "reports")
    os.makedirs(report_path, exist_ok=True)
    
    report_file = os.path.join(report_path, "endpoint_testing_report.md")
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)
    
    logger.info(f"Relatório salvo em: {report_file}")
    
    # Exibir resumo
    total_services = len(results["services"])
    total_endpoints = sum(len(service["endpoints"]) for service in results["services"])
    successful_endpoints = sum(
        sum(1 for endpoint in service["endpoints"] if endpoint["result"]["success"])
        for service in results["services"]
    )
    
    logger.info(f"Total de serviços testados: {total_services}")
    logger.info(f"Total de endpoints testados: {total_endpoints}")
    logger.info(f"Endpoints com sucesso: {successful_endpoints}/{total_endpoints} ({successful_endpoints/total_endpoints*100:.1f}%)")
    
    if total_endpoints - successful_endpoints > 0:
        logger.warning(f"⚠️ {total_endpoints - successful_endpoints} endpoints falharam nos testes")
        logger.info(f"Para mais detalhes, consulte o relatório: {report_file}")
    else:
        logger.info("✅ Todos os endpoints testados estão funcionando corretamente")

if __name__ == "__main__":
    main()