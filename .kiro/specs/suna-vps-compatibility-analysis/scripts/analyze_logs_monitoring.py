#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para analisar a configuração de logs e monitoramento dos serviços Renum e Suna.
Este script verifica o sistema de logs implementado, analisa a rotação e retenção de logs,
e identifica lacunas no monitoramento.
"""

import os
import sys
import json
import logging
import subprocess
import re
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
logger = logging.getLogger("logs_monitoring_analysis")

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

def get_container_log_config(container_id: str) -> Dict:
    """
    Obtém a configuração de logs de um contêiner.
    
    Args:
        container_id: ID do contêiner
        
    Returns:
        Dicionário com configuração de logs
    """
    stdout, stderr, returncode = run_command(f'docker inspect --format "{{{{json .HostConfig.LogConfig}}}}" {container_id}')
    
    if returncode != 0:
        logger.error(f"Erro ao obter configuração de logs do contêiner {container_id}: {stderr}")
        return {}
    
    try:
        log_config = json.loads(stdout)
        return log_config
    except json.JSONDecodeError:
        logger.error(f"Erro ao decodificar JSON para o contêiner {container_id}")
        return {}

def get_container_log_size(container_id: str) -> Dict:
    """
    Obtém o tamanho dos logs de um contêiner.
    
    Args:
        container_id: ID do contêiner
        
    Returns:
        Dicionário com informações sobre o tamanho dos logs
    """
    # Obter caminho do arquivo de log
    stdout, stderr, returncode = run_command(f'docker inspect --format "{{{{.LogPath}}}}" {container_id}')
    
    if returncode != 0 or not stdout.strip():
        logger.error(f"Erro ao obter caminho do log do contêiner {container_id}: {stderr}")
        return {"size": 0, "size_human": "0 B", "path": None}
    
    log_path = stdout.strip()
    
    # Obter tamanho do arquivo de log
    stdout, stderr, returncode = run_command(f'ls -lh {log_path}')
    
    if returncode != 0:
        logger.error(f"Erro ao obter tamanho do log do contêiner {container_id}: {stderr}")
        return {"size": 0, "size_human": "0 B", "path": log_path}
    
    # Extrair tamanho do arquivo
    size_match = re.search(r'\s(\d+)\s', stdout)
    size_human_match = re.search(r'\s(\d+[KMGT]?)\s', stdout)
    
    size = int(size_match.group(1)) if size_match else 0
    size_human = size_human_match.group(1) if size_human_match else "0 B"
    
    return {"size": size, "size_human": size_human, "path": log_path}

def check_log_rotation(container_id: str) -> Dict:
    """
    Verifica a configuração de rotação de logs de um contêiner.
    
    Args:
        container_id: ID do contêiner
        
    Returns:
        Dicionário com informações sobre a rotação de logs
    """
    log_config = get_container_log_config(container_id)
    
    # Verificar se há configuração de rotação de logs
    log_driver = log_config.get("Type", "json-file")
    log_opts = log_config.get("Config", {})
    
    max_size = log_opts.get("max-size", "")
    max_file = log_opts.get("max-file", "")
    
    rotation_enabled = max_size != "" or max_file != ""
    
    return {
        "driver": log_driver,
        "rotation_enabled": rotation_enabled,
        "max_size": max_size,
        "max_file": max_file,
        "options": log_opts
    }

def check_monitoring_tools(container_id: str) -> Dict:
    """
    Verifica ferramentas de monitoramento instaladas no contêiner.
    
    Args:
        container_id: ID do contêiner
        
    Returns:
        Dicionário com informações sobre ferramentas de monitoramento
    """
    monitoring_tools = {
        "prometheus": False,
        "sentry": False,
        "datadog": False,
        "newrelic": False,
        "grafana": False,
        "elasticsearch": False,
        "fluentd": False,
        "logstash": False
    }
    
    # Verificar variáveis de ambiente relacionadas a monitoramento
    env_vars = get_container_env_vars(container_id)
    
    # Verificar Sentry
    if any(key.startswith("SENTRY_") for key in env_vars):
        monitoring_tools["sentry"] = True
    
    # Verificar Datadog
    if any(key.startswith("DD_") for key in env_vars):
        monitoring_tools["datadog"] = True
    
    # Verificar New Relic
    if any(key.startswith("NEW_RELIC_") for key in env_vars):
        monitoring_tools["newrelic"] = True
    
    # Verificar Prometheus
    if "PROMETHEUS_MULTIPROC_DIR" in env_vars or "PROMETHEUS_PORT" in env_vars:
        monitoring_tools["prometheus"] = True
    
    # Verificar pacotes instalados
    # Python
    stdout, stderr, returncode = run_command(f'docker exec {container_id} pip list 2>/dev/null || docker exec {container_id} pip3 list 2>/dev/null')
    
    if returncode == 0:
        if "sentry" in stdout.lower() or "sentry-sdk" in stdout.lower():
            monitoring_tools["sentry"] = True
        if "prometheus" in stdout.lower():
            monitoring_tools["prometheus"] = True
        if "datadog" in stdout.lower():
            monitoring_tools["datadog"] = True
        if "newrelic" in stdout.lower():
            monitoring_tools["newrelic"] = True
        if "elasticsearch" in stdout.lower():
            monitoring_tools["elasticsearch"] = True
        if "fluentd" in stdout.lower():
            monitoring_tools["fluentd"] = True
        if "logstash" in stdout.lower():
            monitoring_tools["logstash"] = True
    
    # Verificar arquivos de configuração
    stdout, stderr, returncode = run_command(f'docker exec {container_id} find /app -name "*.py" -o -name "*.js" -o -name "*.json" -o -name "*.yaml" -o -name "*.yml" | xargs grep -l "sentry\\|prometheus\\|datadog\\|newrelic\\|grafana\\|elasticsearch\\|fluentd\\|logstash" 2>/dev/null')
    
    if returncode == 0 and stdout:
        files = stdout.strip().split("\n")
        
        for file in files:
            file_content, _, _ = run_command(f'docker exec {container_id} cat {file}')
            
            if "sentry" in file_content.lower():
                monitoring_tools["sentry"] = True
            if "prometheus" in file_content.lower():
                monitoring_tools["prometheus"] = True
            if "datadog" in file_content.lower():
                monitoring_tools["datadog"] = True
            if "newrelic" in file_content.lower():
                monitoring_tools["newrelic"] = True
            if "grafana" in file_content.lower():
                monitoring_tools["grafana"] = True
            if "elasticsearch" in file_content.lower():
                monitoring_tools["elasticsearch"] = True
            if "fluentd" in file_content.lower():
                monitoring_tools["fluentd"] = True
            if "logstash" in file_content.lower():
                monitoring_tools["logstash"] = True
    
    return monitoring_tools

def check_log_levels(container_id: str) -> Dict:
    """
    Verifica os níveis de log configurados no contêiner.
    
    Args:
        container_id: ID do contêiner
        
    Returns:
        Dicionário com informações sobre níveis de log
    """
    env_vars = get_container_env_vars(container_id)
    
    # Verificar variáveis de ambiente relacionadas a níveis de log
    log_level = None
    log_level_vars = ["LOG_LEVEL", "LOGGING_LEVEL", "LOGLEVEL", "DEBUG"]
    
    for var in log_level_vars:
        if var in env_vars:
            log_level = env_vars[var]
            break
    
    # Verificar arquivos de configuração de logging
    stdout, stderr, returncode = run_command(f'docker exec {container_id} find /app -name "*.py" | xargs grep -l "logging\\.\\(basicConfig\\|config\\)" 2>/dev/null')
    
    log_config_files = []
    if returncode == 0 and stdout:
        log_config_files = stdout.strip().split("\n")
    
    # Analisar arquivos de configuração
    log_config_details = []
    for file in log_config_files:
        file_content, _, _ = run_command(f'docker exec {container_id} cat {file}')
        
        # Extrair nível de log
        level_match = re.search(r'level\s*=\s*logging\.(\w+)', file_content)
        if level_match:
            log_config_details.append({
                "file": file,
                "level": level_match.group(1)
            })
    
    return {
        "env_log_level": log_level,
        "config_files": log_config_files,
        "config_details": log_config_details
    }

def analyze_log_content(container_id: str, lines: int = 100) -> Dict:
    """
    Analisa o conteúdo dos logs de um contêiner.
    
    Args:
        container_id: ID do contêiner
        lines: Número de linhas a analisar
        
    Returns:
        Dicionário com análise do conteúdo dos logs
    """
    stdout, stderr, returncode = run_command(f'docker logs --tail {lines} {container_id}')
    
    if returncode != 0:
        logger.error(f"Erro ao obter logs do contêiner {container_id}: {stderr}")
        return {"error_count": 0, "warning_count": 0, "info_count": 0, "debug_count": 0, "sample_errors": []}
    
    log_lines = stdout.strip().split("\n")
    
    # Contar ocorrências de diferentes níveis de log
    error_count = sum(1 for line in log_lines if "error" in line.lower() or "exception" in line.lower() or "traceback" in line.lower())
    warning_count = sum(1 for line in log_lines if "warning" in line.lower() or "warn" in line.lower())
    info_count = sum(1 for line in log_lines if "info" in line.lower())
    debug_count = sum(1 for line in log_lines if "debug" in line.lower())
    
    # Extrair exemplos de erros
    error_lines = [line for line in log_lines if "error" in line.lower() or "exception" in line.lower() or "traceback" in line.lower()]
    sample_errors = error_lines[:5]  # Limitar a 5 exemplos
    
    return {
        "error_count": error_count,
        "warning_count": warning_count,
        "info_count": info_count,
        "debug_count": debug_count,
        "sample_errors": sample_errors
    }

def generate_report(results: Dict) -> str:
    """
    Gera um relatório formatado com os resultados da análise de logs e monitoramento.
    
    Args:
        results: Dicionário com resultados da análise
        
    Returns:
        Relatório formatado em Markdown
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = [
        "# Relatório de Análise de Logs e Monitoramento",
        f"Data: {now}\n",
        "## Resumo",
    ]
    
    # Adicionar resumo
    containers = results["containers"]
    
    # Contar contêineres com rotação de logs configurada
    rotation_enabled_count = sum(1 for c in containers if c["log_rotation"]["rotation_enabled"])
    
    # Contar contêineres com ferramentas de monitoramento
    monitoring_tools_count = sum(1 for c in containers if any(c["monitoring_tools"].values()))
    
    report.extend([
        f"- Total de contêineres analisados: {len(containers)}",
        f"- Contêineres com rotação de logs configurada: {rotation_enabled_count}/{len(containers)}",
        f"- Contêineres com ferramentas de monitoramento: {monitoring_tools_count}/{len(containers)}\n"
    ])
    
    # Adicionar detalhes por contêiner
    for container in containers:
        container_name = container["name"]
        container_id = container["id"]
        
        report.append(f"## Contêiner: {container_name}")
        report.append(f"- **ID**: {container_id[:12]}")
        
        # Configuração de logs
        log_config = container["log_config"]
        log_rotation = container["log_rotation"]
        log_size = container["log_size"]
        
        report.append("\n### Configuração de Logs")
        report.append(f"- **Driver**: {log_config.get('Type', 'N/A')}")
        report.append(f"- **Tamanho atual dos logs**: {log_size.get('size_human', 'N/A')}")
        report.append(f"- **Caminho do arquivo de log**: {log_size.get('path', 'N/A')}")
        
        # Rotação de logs
        rotation_status = "✅ Configurada" if log_rotation["rotation_enabled"] else "❌ Não configurada"
        report.append(f"- **Rotação de logs**: {rotation_status}")
        
        if log_rotation["rotation_enabled"]:
            report.append(f"  - **Tamanho máximo**: {log_rotation.get('max_size', 'N/A')}")
            report.append(f"  - **Número máximo de arquivos**: {log_rotation.get('max_file', 'N/A')}")
        
        # Níveis de log
        log_levels = container["log_levels"]
        
        report.append("\n### Níveis de Log")
        report.append(f"- **Nível de log configurado via ambiente**: {log_levels.get('env_log_level', 'N/A')}")
        
        if log_levels["config_details"]:
            report.append("- **Configurações de log encontradas em arquivos**:")
            for config in log_levels["config_details"]:
                report.append(f"  - {config['file']}: {config['level']}")
        
        # Análise de conteúdo dos logs
        log_content = container["log_content"]
        
        report.append("\n### Análise de Conteúdo dos Logs")
        report.append(f"- **Erros**: {log_content['error_count']}")
        report.append(f"- **Avisos**: {log_content['warning_count']}")
        report.append(f"- **Informações**: {log_content['info_count']}")
        report.append(f"- **Debug**: {log_content['debug_count']}")
        
        if log_content["sample_errors"]:
            report.append("\n**Exemplos de erros encontrados**:")
            report.append("```")
            for error in log_content["sample_errors"]:
                report.append(error)
            report.append("```")
        
        # Ferramentas de monitoramento
        monitoring_tools = container["monitoring_tools"]
        
        report.append("\n### Ferramentas de Monitoramento")
        
        if any(monitoring_tools.values()):
            for tool, enabled in monitoring_tools.items():
                status = "✅ Detectado" if enabled else "❌ Não detectado"
                report.append(f"- **{tool.capitalize()}**: {status}")
        else:
            report.append("❌ Nenhuma ferramenta de monitoramento detectada")
        
        report.append("\n")
    
    # Adicionar recomendações
    report.append("## Recomendações")
    
    # Recomendações para rotação de logs
    if rotation_enabled_count < len(containers):
        report.append("\n### Rotação de Logs")
        report.append("1. **Configurar rotação de logs** - Adicionar as seguintes opções ao Docker Compose:")
        report.append("```yaml")
        report.append("logging:")
        report.append("  driver: \"json-file\"")
        report.append("  options:")
        report.append("    max-size: \"10m\"")
        report.append("    max-file: \"3\"")
        report.append("```")
    
    # Recomendações para monitoramento
    if monitoring_tools_count < len(containers):
        report.append("\n### Monitoramento")
        report.append("1. **Implementar monitoramento com Sentry** - Para rastreamento de erros e exceções")
        report.append("2. **Configurar Prometheus e Grafana** - Para métricas de desempenho e dashboards")
        report.append("3. **Centralizar logs com ELK Stack ou Fluentd** - Para análise centralizada de logs")
    
    # Recomendações para níveis de log
    report.append("\n### Níveis de Log")
    report.append("1. **Padronizar níveis de log** - Usar variáveis de ambiente para configurar níveis de log")
    report.append("2. **Implementar logs estruturados** - Usar formato JSON para facilitar a análise")
    report.append("3. **Adicionar contexto aos logs** - Incluir informações como ID de requisição, usuário, etc.")
    
    return "\n".join(report)

def main():
    """Função principal do script."""
    logger.info("Analisando configuração de logs e monitoramento...")
    
    results = {
        "containers": []
    }
    
    # Obter contêineres Renum e Suna
    renum_containers = get_container_ids("renum")
    suna_containers = get_container_ids("suna")
    
    all_containers = renum_containers + suna_containers
    
    if not all_containers:
        logger.warning("Nenhum contêiner Renum ou Suna encontrado.")
        return
    
    # Analisar cada contêiner
    for container in all_containers:
        container_id = container["id"]
        container_name = container["name"]
        
        logger.info(f"Analisando contêiner: {container_name} ({container_id[:12]})")
        
        # Obter configuração de logs
        log_config = get_container_log_config(container_id)
        
        # Verificar rotação de logs
        log_rotation = check_log_rotation(container_id)
        
        # Obter tamanho dos logs
        log_size = get_container_log_size(container_id)
        
        # Verificar ferramentas de monitoramento
        monitoring_tools = check_monitoring_tools(container_id)
        
        # Verificar níveis de log
        log_levels = check_log_levels(container_id)
        
        # Analisar conteúdo dos logs
        log_content = analyze_log_content(container_id)
        
        # Adicionar resultados
        results["containers"].append({
            "id": container_id,
            "name": container_name,
            "log_config": log_config,
            "log_rotation": log_rotation,
            "log_size": log_size,
            "monitoring_tools": monitoring_tools,
            "log_levels": log_levels,
            "log_content": log_content
        })
    
    # Gerar relatório
    report = generate_report(results)
    
    # Salvar relatório em arquivo
    report_path = os.path.join(os.path.dirname(__file__), "..", "reports")
    os.makedirs(report_path, exist_ok=True)
    
    report_file = os.path.join(report_path, "logs_monitoring_report.md")
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)
    
    logger.info(f"Relatório salvo em: {report_file}")
    
    # Exibir resumo
    containers = results["containers"]
    rotation_enabled_count = sum(1 for c in containers if c["log_rotation"]["rotation_enabled"])
    monitoring_tools_count = sum(1 for c in containers if any(c["monitoring_tools"].values()))
    
    logger.info(f"Total de contêineres analisados: {len(containers)}")
    logger.info(f"Contêineres com rotação de logs configurada: {rotation_enabled_count}/{len(containers)}")
    logger.info(f"Contêineres com ferramentas de monitoramento: {monitoring_tools_count}/{len(containers)}")
    
    if rotation_enabled_count < len(containers) or monitoring_tools_count < len(containers):
        logger.warning("⚠️ Foram identificadas lacunas na configuração de logs e monitoramento")
        logger.info(f"Para mais detalhes, consulte o relatório: {report_file}")
    else:
        logger.info("✅ A configuração de logs e monitoramento parece adequada")

if __name__ == "__main__":
    main()