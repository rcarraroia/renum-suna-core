#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para testar a comunicação entre os serviços Renum e Suna.
Este script executa testes de ping entre contêineres, verifica acesso a endpoints
internos e analisa logs de comunicação entre serviços.
"""

import os
import sys
import json
import time
import logging
import subprocess
import requests
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import traceback

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("service_communication_test")

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

def get_container_networks(container_id: str) -> Dict:
    """
    Obtém as redes às quais um contêiner está conectado.
    
    Args:
        container_id: ID do contêiner
        
    Returns:
        Dicionário com informações das redes
    """
    stdout, stderr, returncode = run_command(f'docker inspect --format "{{{{json .NetworkSettings.Networks}}}}" {container_id}')
    
    if returncode != 0:
        logger.error(f"Erro ao inspecionar redes do contêiner {container_id}: {stderr}")
        return {}
    
    try:
        networks = json.loads(stdout)
        return networks
    except json.JSONDecodeError:
        logger.error(f"Erro ao decodificar JSON para o contêiner {container_id}")
        return {}

def test_ping(source_id: str, target_ip: str, target_name: str) -> Dict:
    """
    Testa a comunicação entre dois contêineres usando ping.
    
    Args:
        source_id: ID do contêiner de origem
        target_ip: IP do contêiner de destino
        target_name: Nome do contêiner de destino
        
    Returns:
        Dicionário com resultados do teste
    """
    # Verificar se o contêiner tem o comando ping
    stdout, stderr, returncode = run_command(f'docker exec {source_id} which ping')
    
    if returncode != 0:
        # Tentar instalar ping
        logger.info(f"ping não encontrado no contêiner {source_id}, tentando instalar...")
        
        # Verificar se é uma imagem baseada em Debian/Ubuntu
        stdout, stderr, returncode = run_command(f'docker exec {source_id} which apt-get')
        
        if returncode == 0:
            run_command(f'docker exec {source_id} apt-get update -qq && apt-get install -y iputils-ping')
        else:
            # Verificar se é uma imagem baseada em Alpine
            stdout, stderr, returncode = run_command(f'docker exec {source_id} which apk')
            
            if returncode == 0:
                run_command(f'docker exec {source_id} apk add --no-cache iputils')
    
    # Testar ping
    stdout, stderr, returncode = run_command(f'docker exec {source_id} ping -c 3 -W 2 {target_ip}')
    
    if returncode == 0:
        # Extrair estatísticas de ping
        stats = {}
        for line in stdout.splitlines():
            if "min/avg/max" in line:
                parts = line.split("=")
                if len(parts) > 1:
                    stats_parts = parts[1].strip().split("/")
                    if len(stats_parts) >= 3:
                        stats = {
                            "min": stats_parts[0],
                            "avg": stats_parts[1],
                            "max": stats_parts[2].split(" ")[0]
                        }
        
        return {
            "success": True,
            "message": f"Ping bem-sucedido para {target_name} ({target_ip})",
            "details": stdout,
            "stats": stats
        }
    else:
        return {
            "success": False,
            "message": f"Falha no ping para {target_name} ({target_ip})",
            "details": stderr
        }

def test_http_endpoint(source_id: str, target_url: str, endpoint_name: str) -> Dict:
    """
    Testa o acesso a um endpoint HTTP.
    
    Args:
        source_id: ID do contêiner de origem
        target_url: URL do endpoint
        endpoint_name: Nome do endpoint
        
    Returns:
        Dicionário com resultados do teste
    """
    # Verificar se o contêiner tem o comando curl
    stdout, stderr, returncode = run_command(f'docker exec {source_id} which curl')
    
    if returncode != 0:
        # Tentar instalar curl
        logger.info(f"curl não encontrado no contêiner {source_id}, tentando instalar...")
        
        # Verificar se é uma imagem baseada em Debian/Ubuntu
        stdout, stderr, returncode = run_command(f'docker exec {source_id} which apt-get')
        
        if returncode == 0:
            run_command(f'docker exec {source_id} apt-get update -qq && apt-get install -y curl')
        else:
            # Verificar se é uma imagem baseada em Alpine
            stdout, stderr, returncode = run_command(f'docker exec {source_id} which apk')
            
            if returncode == 0:
                run_command(f'docker exec {source_id} apk add --no-cache curl')
    
    # Testar acesso ao endpoint
    start_time = time.time()
    stdout, stderr, returncode = run_command(f'docker exec {source_id} curl -s -o /dev/null -w "%{{http_code}}|%{{time_total}}" -m 5 {target_url}')
    
    if returncode == 0 and stdout:
        parts = stdout.strip().split("|")
        if len(parts) == 2:
            status_code = parts[0]
            response_time = parts[1]
            
            success = status_code.startswith("2") or status_code.startswith("3")
            
            return {
                "success": success,
                "message": f"Acesso {'bem-sucedido' if success else 'falhou'} ao endpoint {endpoint_name} ({target_url})",
                "status_code": status_code,
                "response_time": response_time
            }
    
    return {
        "success": False,
        "message": f"Falha ao acessar endpoint {endpoint_name} ({target_url})",
        "details": stderr
    }

def get_container_logs(container_id: str, since: str = "1h") -> List[str]:
    """
    Obtém os logs de um contêiner.
    
    Args:
        container_id: ID do contêiner
        since: Período de tempo para obter logs (ex: "1h", "30m")
        
    Returns:
        Lista de linhas de log
    """
    stdout, stderr, returncode = run_command(f'docker logs --since {since} {container_id}')
    
    if returncode != 0:
        logger.error(f"Erro ao obter logs do contêiner {container_id}: {stderr}")
        return []
    
    return stdout.splitlines()

def analyze_communication_logs(logs: List[str], target_service: str) -> List[Dict]:
    """
    Analisa logs em busca de mensagens relacionadas à comunicação com um serviço.
    
    Args:
        logs: Lista de linhas de log
        target_service: Nome do serviço alvo
        
    Returns:
        Lista de dicionários com mensagens relevantes
    """
    relevant_keywords = [
        "connect",
        "request",
        "response",
        "error",
        "failed",
        "timeout",
        "refused",
        "unreachable"
    ]
    
    target_service_lower = target_service.lower()
    relevant_logs = []
    
    for line in logs:
        line_lower = line.lower()
        
        # Verificar se a linha contém o nome do serviço alvo
        if target_service_lower in line_lower:
            # Verificar se a linha contém palavras-chave relevantes
            if any(keyword in line_lower for keyword in relevant_keywords):
                # Tentar extrair timestamp
                timestamp = None
                if line and len(line) > 20:  # Formato típico de timestamp
                    try:
                        timestamp = line[:23]  # Formato típico: "2023-07-18T12:34:56.789"
                    except:
                        pass
                
                relevant_logs.append({
                    "timestamp": timestamp,
                    "message": line
                })
    
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
        "# Relatório de Comunicação entre Serviços",
        f"Data: {now}\n",
        "## Resumo",
    ]
    
    # Adicionar resumo
    ping_tests = results.get("ping_tests", [])
    endpoint_tests = results.get("endpoint_tests", [])
    
    ping_success = sum(1 for test in ping_tests if test["result"]["success"])
    endpoint_success = sum(1 for test in endpoint_tests if test["result"]["success"])
    
    report.extend([
        f"- Testes de ping bem-sucedidos: {ping_success}/{len(ping_tests)}",
        f"- Testes de endpoint bem-sucedidos: {endpoint_success}/{len(endpoint_tests)}\n"
    ])
    
    # Adicionar resultados dos testes de ping
    report.append("## Testes de Ping")
    
    if ping_tests:
        for test in ping_tests:
            source = test["source"]
            target = test["target"]
            result = test["result"]
            
            status = "✅ Sucesso" if result["success"] else "❌ Falha"
            report.append(f"\n### {source} → {target}: {status}")
            report.append(f"- **Mensagem**: {result['message']}")
            
            if result["success"] and "stats" in result:
                stats = result["stats"]
                report.append(f"- **Estatísticas**: Min: {stats.get('min', 'N/A')}ms, Média: {stats.get('avg', 'N/A')}ms, Max: {stats.get('max', 'N/A')}ms")
            
            if "details" in result and result["details"]:
                details = result["details"].strip()
                if details:
                    report.append("- **Detalhes**:")
                    report.append("```")
                    report.append(details)
                    report.append("```")
    else:
        report.append("\nNenhum teste de ping realizado.")
    
    # Adicionar resultados dos testes de endpoint
    report.append("\n## Testes de Endpoint")
    
    if endpoint_tests:
        for test in endpoint_tests:
            source = test["source"]
            endpoint = test["endpoint"]
            result = test["result"]
            
            status = "✅ Sucesso" if result["success"] else "❌ Falha"
            report.append(f"\n### {source} → {endpoint}: {status}")
            report.append(f"- **Mensagem**: {result['message']}")
            
            if "status_code" in result:
                report.append(f"- **Código de Status**: {result['status_code']}")
            
            if "response_time" in result:
                report.append(f"- **Tempo de Resposta**: {result['response_time']}s")
            
            if "details" in result and result["details"]:
                details = result["details"].strip()
                if details:
                    report.append("- **Detalhes**:")
                    report.append("```")
                    report.append(details)
                    report.append("```")
    else:
        report.append("\nNenhum teste de endpoint realizado.")
    
    # Adicionar análise de logs
    report.append("\n## Análise de Logs de Comunicação")
    
    log_analysis = results.get("log_analysis", [])
    if log_analysis:
        for analysis in log_analysis:
            source = analysis["source"]
            target = analysis["target"]
            logs = analysis["logs"]
            
            report.append(f"\n### Logs de {source} relacionados a {target}")
            
            if logs:
                report.append(f"- **Total de mensagens relevantes**: {len(logs)}")
                report.append("\n**Mensagens mais recentes**:")
                report.append("```")
                
                # Mostrar até 10 mensagens mais recentes
                for log in logs[-10:]:
                    timestamp = log.get("timestamp", "")
                    message = log.get("message", "")
                    report.append(f"{timestamp} {message}")
                
                report.append("```")
            else:
                report.append("Nenhuma mensagem relevante encontrada nos logs.")
    else:
        report.append("\nNenhuma análise de logs realizada.")
    
    # Adicionar recomendações
    report.append("\n## Recomendações")
    
    if ping_success < len(ping_tests) or endpoint_success < len(endpoint_tests):
        report.append("\nForam detectados problemas na comunicação entre serviços:")
        
        if ping_success < len(ping_tests):
            report.append("\n### Problemas de Conectividade")
            report.append("1. **Verifique a configuração de rede Docker** - Certifique-se de que os contêineres estão na mesma rede")
            report.append("2. **Verifique as regras de firewall** - Certifique-se de que não há regras bloqueando a comunicação")
            report.append("3. **Verifique a resolução DNS** - Certifique-se de que os nomes dos contêineres podem ser resolvidos")
        
        if endpoint_success < len(endpoint_tests):
            report.append("\n### Problemas de Acesso a Endpoints")
            report.append("1. **Verifique se os serviços estão em execução** - Certifique-se de que os serviços estão ativos e respondendo")
            report.append("2. **Verifique as configurações de porta** - Certifique-se de que as portas estão expostas corretamente")
            report.append("3. **Verifique as URLs dos endpoints** - Certifique-se de que as URLs estão corretas")
            report.append("4. **Verifique os logs dos serviços** - Procure por erros relacionados aos endpoints")
    else:
        report.append("\n✅ A comunicação entre serviços parece estar funcionando corretamente. Todos os testes foram bem-sucedidos.")
    
    return "\n".join(report)

def main():
    """Função principal do script."""
    logger.info("Testando comunicação entre serviços Renum e Suna...")
    
    results = {
        "ping_tests": [],
        "endpoint_tests": [],
        "log_analysis": []
    }
    
    # Obter contêineres Renum e Suna
    renum_containers = get_container_ids("renum")
    suna_containers = get_container_ids("suna")
    
    if not renum_containers or not suna_containers:
        logger.warning("Contêineres Renum ou Suna não encontrados.")
        return
    
    # Testar ping entre contêineres
    logger.info("Testando ping entre contêineres...")
    
    # Testar ping de Renum para Suna
    for renum in renum_containers:
        renum_id = renum["id"]
        renum_name = renum["name"]
        
        for suna in suna_containers:
            suna_id = suna["id"]
            suna_name = suna["name"]
            
            # Obter IP do contêiner Suna
            suna_networks = get_container_networks(suna_id)
            suna_ip = None
            
            for network_name, network_info in suna_networks.items():
                if "IPAddress" in network_info and network_info["IPAddress"]:
                    suna_ip = network_info["IPAddress"]
                    break
            
            if not suna_ip:
                logger.warning(f"Não foi possível obter o IP do contêiner {suna_name}")
                continue
            
            logger.info(f"Testando ping de {renum_name} para {suna_name} ({suna_ip})...")
            result = test_ping(renum_id, suna_ip, suna_name)
            
            results["ping_tests"].append({
                "source": renum_name,
                "target": suna_name,
                "result": result
            })
    
    # Testar ping de Suna para Renum
    for suna in suna_containers:
        suna_id = suna["id"]
        suna_name = suna["name"]
        
        for renum in renum_containers:
            renum_id = renum["id"]
            renum_name = renum["name"]
            
            # Obter IP do contêiner Renum
            renum_networks = get_container_networks(renum_id)
            renum_ip = None
            
            for network_name, network_info in renum_networks.items():
                if "IPAddress" in network_info and network_info["IPAddress"]:
                    renum_ip = network_info["IPAddress"]
                    break
            
            if not renum_ip:
                logger.warning(f"Não foi possível obter o IP do contêiner {renum_name}")
                continue
            
            logger.info(f"Testando ping de {suna_name} para {renum_name} ({renum_ip})...")
            result = test_ping(suna_id, renum_ip, renum_name)
            
            results["ping_tests"].append({
                "source": suna_name,
                "target": renum_name,
                "result": result
            })
    
    # Testar acesso a endpoints
    logger.info("Testando acesso a endpoints...")
    
    # Obter URLs dos endpoints
    endpoints = []
    
    # Obter variáveis de ambiente dos contêineres Renum
    for renum in renum_containers:
        renum_id = renum["id"]
        renum_name = renum["name"]
        
        env_vars = get_container_env_vars(renum_id)
        
        # Verificar se há variáveis de ambiente relacionadas ao Suna
        suna_api_url = env_vars.get("SUNA_API_URL")
        if suna_api_url:
            endpoints.append({
                "source": renum_name,
                "target": "Suna API",
                "url": suna_api_url,
                "container_id": renum_id
            })
    
    # Obter variáveis de ambiente dos contêineres Suna
    for suna in suna_containers:
        suna_id = suna["id"]
        suna_name = suna["name"]
        
        env_vars = get_container_env_vars(suna_id)
        
        # Verificar se há variáveis de ambiente relacionadas ao Renum
        renum_api_url = env_vars.get("RENUM_API_URL")
        if renum_api_url:
            endpoints.append({
                "source": suna_name,
                "target": "Renum API",
                "url": renum_api_url,
                "container_id": suna_id
            })
    
    # Testar acesso aos endpoints
    for endpoint in endpoints:
        source = endpoint["source"]
        target = endpoint["target"]
        url = endpoint["url"]
        container_id = endpoint["container_id"]
        
        logger.info(f"Testando acesso de {source} ao endpoint {target} ({url})...")
        result = test_http_endpoint(container_id, url, target)
        
        results["endpoint_tests"].append({
            "source": source,
            "endpoint": target,
            "result": result
        })
    
    # Analisar logs de comunicação
    logger.info("Analisando logs de comunicação...")
    
    # Analisar logs dos contêineres Renum
    for renum in renum_containers:
        renum_id = renum["id"]
        renum_name = renum["name"]
        
        logger.info(f"Analisando logs do contêiner {renum_name}...")
        logs = get_container_logs(renum_id)
        
        # Analisar logs em busca de mensagens relacionadas ao Suna
        suna_logs = analyze_communication_logs(logs, "suna")
        
        results["log_analysis"].append({
            "source": renum_name,
            "target": "Suna",
            "logs": suna_logs
        })
    
    # Analisar logs dos contêineres Suna
    for suna in suna_containers:
        suna_id = suna["id"]
        suna_name = suna["name"]
        
        logger.info(f"Analisando logs do contêiner {suna_name}...")
        logs = get_container_logs(suna_id)
        
        # Analisar logs em busca de mensagens relacionadas ao Renum
        renum_logs = analyze_communication_logs(logs, "renum")
        
        results["log_analysis"].append({
            "source": suna_name,
            "target": "Renum",
            "logs": renum_logs
        })
    
    # Gerar relatório
    report = generate_report(results)
    
    # Salvar relatório em arquivo
    report_path = os.path.join(os.path.dirname(__file__), "..", "reports")
    os.makedirs(report_path, exist_ok=True)
    
    report_file = os.path.join(report_path, "service_communication_report.md")
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)
    
    logger.info(f"Relatório salvo em: {report_file}")
    
    # Exibir resumo
    ping_tests = results.get("ping_tests", [])
    endpoint_tests = results.get("endpoint_tests", [])
    
    ping_success = sum(1 for test in ping_tests if test["result"]["success"])
    endpoint_success = sum(1 for test in endpoint_tests if test["result"]["success"])
    
    if ping_success < len(ping_tests) or endpoint_success < len(endpoint_tests):
        logger.warning(f"⚠️ Foram detectados problemas na comunicação entre serviços:")
        logger.warning(f"- Testes de ping bem-sucedidos: {ping_success}/{len(ping_tests)}")
        logger.warning(f"- Testes de endpoint bem-sucedidos: {endpoint_success}/{len(endpoint_tests)}")
        logger.info(f"Para mais detalhes, consulte o relatório: {report_file}")
    else:
        logger.info("✅ A comunicação entre serviços parece estar funcionando corretamente. Todos os testes foram bem-sucedidos.")

if __name__ == "__main__":
    main()