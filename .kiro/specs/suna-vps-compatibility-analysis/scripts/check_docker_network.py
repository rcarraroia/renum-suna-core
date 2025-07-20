#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para verificar a configuração de rede Docker.
Este script lista as redes Docker disponíveis, analisa a configuração de rede
dos contêineres e verifica a comunicação entre contêineres.
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
logger = logging.getLogger("docker_network_check")

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

def list_docker_networks() -> List[Dict]:
    """
    Lista as redes Docker disponíveis.
    
    Returns:
        Lista de dicionários com informações das redes
    """
    stdout, stderr, returncode = run_command('docker network ls --format "{{json .}}"')
    
    if returncode != 0:
        logger.error(f"Erro ao listar redes Docker: {stderr}")
        return []
    
    networks = []
    for line in stdout.splitlines():
        if line.strip():
            try:
                network = json.loads(line)
                networks.append(network)
            except json.JSONDecodeError:
                logger.error(f"Erro ao decodificar JSON: {line}")
    
    return networks

def get_network_details(network_id: str) -> Dict:
    """
    Obtém detalhes de uma rede Docker.
    
    Args:
        network_id: ID da rede
        
    Returns:
        Dicionário com detalhes da rede
    """
    stdout, stderr, returncode = run_command(f'docker network inspect {network_id}')
    
    if returncode != 0:
        logger.error(f"Erro ao inspecionar rede {network_id}: {stderr}")
        return {}
    
    try:
        details = json.loads(stdout)
        return details[0] if details else {}
    except json.JSONDecodeError:
        logger.error(f"Erro ao decodificar JSON para rede {network_id}")
        return {}

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

def test_container_communication(source_id: str, target_id: str, target_name: str) -> Dict:
    """
    Testa a comunicação entre dois contêineres usando ping.
    
    Args:
        source_id: ID do contêiner de origem
        target_id: ID do contêiner de destino
        target_name: Nome do contêiner de destino
        
    Returns:
        Dicionário com resultados do teste
    """
    # Obter endereço IP do contêiner de destino
    stdout, stderr, returncode = run_command(f'docker inspect --format "{{{{.NetworkSettings.IPAddress}}}}" {target_id}')
    
    if returncode != 0 or not stdout.strip():
        # Tentar obter IP de redes específicas
        stdout, stderr, returncode = run_command(f'docker inspect --format "{{{{json .NetworkSettings.Networks}}}}" {target_id}')
        
        if returncode != 0:
            logger.error(f"Erro ao obter IP do contêiner {target_id}: {stderr}")
            return {
                "success": False,
                "message": f"Não foi possível obter o IP do contêiner {target_name}"
            }
        
        try:
            networks = json.loads(stdout)
            target_ip = None
            
            # Tentar encontrar um IP em qualquer rede
            for network_name, network_info in networks.items():
                if "IPAddress" in network_info and network_info["IPAddress"]:
                    target_ip = network_info["IPAddress"]
                    break
            
            if not target_ip:
                return {
                    "success": False,
                    "message": f"Contêiner {target_name} não tem um IP atribuído"
                }
        except json.JSONDecodeError:
            logger.error(f"Erro ao decodificar JSON para o contêiner {target_id}")
            return {
                "success": False,
                "message": f"Erro ao obter informações de rede do contêiner {target_name}"
            }
    else:
        target_ip = stdout.strip()
        
        if not target_ip:
            return {
                "success": False,
                "message": f"Contêiner {target_name} não tem um IP atribuído"
            }
    
    # Testar ping
    stdout, stderr, returncode = run_command(f'docker exec {source_id} ping -c 3 -W 2 {target_ip}')
    
    if returncode == 0:
        return {
            "success": True,
            "message": f"Comunicação bem-sucedida com {target_name} ({target_ip})",
            "details": stdout
        }
    else:
        # Tentar ping pelo nome do contêiner
        stdout, stderr, returncode = run_command(f'docker exec {source_id} ping -c 3 -W 2 {target_name}')
        
        if returncode == 0:
            return {
                "success": True,
                "message": f"Comunicação bem-sucedida com {target_name} pelo nome",
                "details": stdout
            }
        else:
            return {
                "success": False,
                "message": f"Falha na comunicação com {target_name} ({target_ip})",
                "details": stderr
            }

def test_dns_resolution(container_id: str, target_name: str) -> Dict:
    """
    Testa a resolução DNS de um nome de contêiner.
    
    Args:
        container_id: ID do contêiner
        target_name: Nome do contêiner a ser resolvido
        
    Returns:
        Dicionário com resultados do teste
    """
    # Verificar se o contêiner tem o comando nslookup
    stdout, stderr, returncode = run_command(f'docker exec {container_id} which nslookup')
    
    if returncode != 0:
        # Tentar instalar dnsutils ou busybox
        logger.info(f"nslookup não encontrado no contêiner {container_id}, tentando instalar ferramentas DNS...")
        
        # Verificar se é uma imagem baseada em Debian/Ubuntu
        stdout, stderr, returncode = run_command(f'docker exec {container_id} which apt-get')
        
        if returncode == 0:
            run_command(f'docker exec {container_id} apt-get update -qq && apt-get install -y dnsutils')
        else:
            # Verificar se é uma imagem baseada em Alpine
            stdout, stderr, returncode = run_command(f'docker exec {container_id} which apk')
            
            if returncode == 0:
                run_command(f'docker exec {container_id} apk add --no-cache bind-tools')
    
    # Testar resolução DNS
    stdout, stderr, returncode = run_command(f'docker exec {container_id} nslookup {target_name}')
    
    if returncode == 0:
        return {
            "success": True,
            "message": f"Resolução DNS bem-sucedida para {target_name}",
            "details": stdout
        }
    else:
        # Tentar com o comando host
        stdout, stderr, returncode = run_command(f'docker exec {container_id} host {target_name}')
        
        if returncode == 0:
            return {
                "success": True,
                "message": f"Resolução DNS bem-sucedida para {target_name} usando host",
                "details": stdout
            }
        else:
            return {
                "success": False,
                "message": f"Falha na resolução DNS para {target_name}",
                "details": stderr
            }

def generate_report(results: Dict) -> str:
    """
    Gera um relatório formatado com os resultados da análise.
    
    Args:
        results: Dicionário com resultados da análise
        
    Returns:
        Relatório formatado em Markdown
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = [
        "# Relatório de Configuração de Rede Docker",
        f"Data: {now}\n",
        "## Resumo",
    ]
    
    # Adicionar resumo
    networks_count = len(results["networks"])
    containers_count = len(results["containers"])
    
    report.extend([
        f"- Total de redes Docker: {networks_count}",
        f"- Total de contêineres analisados: {containers_count}\n"
    ])
    
    # Adicionar informações sobre redes
    report.append("## Redes Docker")
    
    for network in results["networks"]:
        network_id = network["id"]
        network_name = network["name"]
        network_driver = network["driver"]
        
        report.append(f"\n### Rede: {network_name}")
        report.append(f"- **ID**: {network_id}")
        report.append(f"- **Driver**: {network_driver}")
        
        # Adicionar detalhes da rede
        network_details = network["details"]
        
        if network_details:
            # IPAM Config
            if "IPAM" in network_details and "Config" in network_details["IPAM"]:
                ipam_config = network_details["IPAM"]["Config"]
                if ipam_config:
                    report.append("- **Configuração IPAM**:")
                    for config in ipam_config:
                        subnet = config.get("Subnet", "N/A")
                        gateway = config.get("Gateway", "N/A")
                        report.append(f"  - Subnet: {subnet}, Gateway: {gateway}")
            
            # Contêineres conectados
            if "Containers" in network_details:
                containers = network_details["Containers"]
                if containers:
                    report.append("- **Contêineres conectados**:")
                    for container_id, container_info in containers.items():
                        name = container_info.get("Name", "N/A")
                        ip = container_info.get("IPv4Address", "N/A")
                        report.append(f"  - {name}: {ip}")
    
    # Adicionar informações sobre contêineres
    report.append("\n## Contêineres")
    
    for container in results["containers"]:
        container_id = container["id"]
        container_name = container["name"]
        
        report.append(f"\n### Contêiner: {container_name}")
        report.append(f"- **ID**: {container_id[:12]}")
        
        # Redes do contêiner
        container_networks = container["networks"]
        if container_networks:
            report.append("- **Redes**:")
            for network_name, network_info in container_networks.items():
                ip = network_info.get("IPAddress", "N/A")
                mac = network_info.get("MacAddress", "N/A")
                gateway = network_info.get("Gateway", "N/A")
                report.append(f"  - {network_name}: IP: {ip}, MAC: {mac}, Gateway: {gateway}")
        else:
            report.append("- **Redes**: Nenhuma rede encontrada")
    
    # Adicionar resultados dos testes de comunicação
    report.append("\n## Testes de Comunicação")
    
    communication_tests = results.get("communication_tests", [])
    if communication_tests:
        for test in communication_tests:
            source = test["source"]
            target = test["target"]
            result = test["result"]
            
            status = "✅ Sucesso" if result["success"] else "❌ Falha"
            report.append(f"\n### {source} → {target}: {status}")
            report.append(f"- **Mensagem**: {result['message']}")
            
            if "details" in result and result["details"]:
                details = result["details"].strip()
                if details:
                    report.append("- **Detalhes**:")
                    report.append("```")
                    report.append(details)
                    report.append("```")
    else:
        report.append("\nNenhum teste de comunicação realizado.")
    
    # Adicionar resultados dos testes de DNS
    report.append("\n## Testes de Resolução DNS")
    
    dns_tests = results.get("dns_tests", [])
    if dns_tests:
        for test in dns_tests:
            source = test["source"]
            target = test["target"]
            result = test["result"]
            
            status = "✅ Sucesso" if result["success"] else "❌ Falha"
            report.append(f"\n### {source} → {target}: {status}")
            report.append(f"- **Mensagem**: {result['message']}")
            
            if "details" in result and result["details"]:
                details = result["details"].strip()
                if details:
                    report.append("- **Detalhes**:")
                    report.append("```")
                    report.append(details)
                    report.append("```")
    else:
        report.append("\nNenhum teste de resolução DNS realizado.")
    
    # Adicionar recomendações
    report.append("\n## Recomendações")
    
    # Verificar se há problemas de comunicação
    communication_failures = sum(1 for test in results.get("communication_tests", []) if not test["result"]["success"])
    dns_failures = sum(1 for test in results.get("dns_tests", []) if not test["result"]["success"])
    
    if communication_failures > 0 or dns_failures > 0:
        report.append("\nForam detectados problemas na configuração de rede Docker:")
        
        if communication_failures > 0:
            report.append("\n### Problemas de Comunicação")
            report.append("1. **Verifique se os contêineres estão na mesma rede** - Contêineres em redes diferentes não podem se comunicar diretamente")
            report.append("2. **Verifique as regras de firewall** - Certifique-se de que não há regras bloqueando a comunicação")
            report.append("3. **Verifique a configuração de rede dos contêineres** - Certifique-se de que os contêineres têm IPs atribuídos")
        
        if dns_failures > 0:
            report.append("\n### Problemas de Resolução DNS")
            report.append("1. **Verifique a configuração DNS dos contêineres** - Certifique-se de que os contêineres estão usando o DNS do Docker")
            report.append("2. **Verifique se os nomes dos contêineres estão corretos** - Os nomes devem ser únicos e sem caracteres especiais")
            report.append("3. **Considere usar aliases de rede** - Defina aliases para os contêineres para facilitar a resolução DNS")
    else:
        report.append("\n✅ A configuração de rede Docker parece estar correta. Todos os testes de comunicação e resolução DNS foram bem-sucedidos.")
    
    return "\n".join(report)

def main():
    """Função principal do script."""
    logger.info("Verificando configuração de rede Docker...")
    
    results = {
        "networks": [],
        "containers": [],
        "communication_tests": [],
        "dns_tests": []
    }
    
    # Listar redes Docker
    logger.info("Listando redes Docker...")
    networks = list_docker_networks()
    
    for network in networks:
        network_id = network["ID"]
        network_details = get_network_details(network_id)
        
        results["networks"].append({
            "id": network_id,
            "name": network["Name"],
            "driver": network["Driver"],
            "details": network_details
        })
    
    # Obter contêineres Renum e Suna
    logger.info("Obtendo contêineres Renum e Suna...")
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
        
        # Obter redes do contêiner
        container_networks = get_container_networks(container_id)
        
        results["containers"].append({
            "id": container_id,
            "name": container_name,
            "networks": container_networks
        })
    
    # Testar comunicação entre contêineres
    logger.info("Testando comunicação entre contêineres...")
    
    # Separar contêineres por tipo
    renum_names = [c["name"] for c in renum_containers]
    suna_names = [c["name"] for c in suna_containers]
    
    # Testar comunicação de Renum para Suna
    for renum in renum_containers:
        for suna in suna_containers:
            logger.info(f"Testando comunicação de {renum['name']} para {suna['name']}...")
            result = test_container_communication(renum["id"], suna["id"], suna["name"])
            
            results["communication_tests"].append({
                "source": renum["name"],
                "target": suna["name"],
                "result": result
            })
    
    # Testar comunicação de Suna para Renum
    for suna in suna_containers:
        for renum in renum_containers:
            logger.info(f"Testando comunicação de {suna['name']} para {renum['name']}...")
            result = test_container_communication(suna["id"], renum["id"], renum["name"])
            
            results["communication_tests"].append({
                "source": suna["name"],
                "target": renum["name"],
                "result": result
            })
    
    # Testar resolução DNS
    logger.info("Testando resolução DNS...")
    
    # Testar resolução DNS de Renum para Suna
    for renum in renum_containers:
        for suna_name in suna_names:
            logger.info(f"Testando resolução DNS de {renum['name']} para {suna_name}...")
            result = test_dns_resolution(renum["id"], suna_name)
            
            results["dns_tests"].append({
                "source": renum["name"],
                "target": suna_name,
                "result": result
            })
    
    # Testar resolução DNS de Suna para Renum
    for suna in suna_containers:
        for renum_name in renum_names:
            logger.info(f"Testando resolução DNS de {suna['name']} para {renum_name}...")
            result = test_dns_resolution(suna["id"], renum_name)
            
            results["dns_tests"].append({
                "source": suna["name"],
                "target": renum_name,
                "result": result
            })
    
    # Gerar relatório
    report = generate_report(results)
    
    # Salvar relatório em arquivo
    report_path = os.path.join(os.path.dirname(__file__), "..", "reports")
    os.makedirs(report_path, exist_ok=True)
    
    report_file = os.path.join(report_path, "docker_network_report.md")
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)
    
    logger.info(f"Relatório salvo em: {report_file}")
    
    # Exibir resumo
    communication_failures = sum(1 for test in results["communication_tests"] if not test["result"]["success"])
    dns_failures = sum(1 for test in results["dns_tests"] if not test["result"]["success"])
    
    if communication_failures > 0 or dns_failures > 0:
        logger.warning(f"⚠️ Foram detectados problemas na configuração de rede Docker:")
        logger.warning(f"- Falhas de comunicação: {communication_failures}/{len(results['communication_tests'])}")
        logger.warning(f"- Falhas de resolução DNS: {dns_failures}/{len(results['dns_tests'])}")
        logger.info(f"Para mais detalhes, consulte o relatório: {report_file}")
    else:
        logger.info("✅ A configuração de rede Docker parece estar correta. Todos os testes foram bem-sucedidos.")

if __name__ == "__main__":
    main()