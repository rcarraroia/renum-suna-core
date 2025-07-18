#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para comparar as variáveis de ambiente definidas nos arquivos .env
com as variáveis de ambiente presentes nos contêineres em execução.
"""

import os
import sys
import re
import json
import subprocess
from typing import Dict, List, Set, Tuple

def parse_env_file(file_path: str) -> Dict[str, str]:
    """
    Analisa um arquivo .env e retorna as variáveis definidas.
    
    Args:
        file_path: Caminho para o arquivo .env
        
    Returns:
        Dicionário com as variáveis de ambiente
    """
    env_vars = {}
    
    if not os.path.exists(file_path):
        print(f"Arquivo não encontrado: {file_path}")
        return env_vars
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                
                # Ignorar comentários e linhas vazias
                if not line or line.startswith('#'):
                    continue
                
                # Tentar extrair variável e valor
                match = re.match(r'^([A-Za-z0-9_]+)=(.*)$', line)
                if match:
                    key = match.group(1)
                    value = match.group(2)
                    
                    # Remover aspas se presentes
                    if (value.startswith('"') and value.endswith('"')) or \
                       (value.startswith("'") and value.endswith("'")):
                        value = value[1:-1]
                    
                    env_vars[key] = value
    
    except Exception as e:
        print(f"Erro ao ler arquivo {file_path}: {e}")
    
    return env_vars

def run_docker_command(command: str) -> str:
    """Executa um comando Docker e retorna a saída."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar comando Docker: {e}")
        print(f"Stderr: {e.stderr}")
        return ""

def get_container_ids(service_pattern: str) -> List[Dict[str, str]]:
    """
    Obtém IDs e nomes dos contêineres que correspondem ao padrão.
    
    Args:
        service_pattern: Padrão para filtrar contêineres
        
    Returns:
        Lista de dicionários com ID e nome dos contêineres
    """
    output = run_docker_command(f'docker ps -a --filter "name={service_pattern}" --format "{{{{.ID}}}}|{{{{.Names}}}}"')
    containers = []
    
    for line in output.splitlines():
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
    output = run_docker_command(f'docker inspect --format "{{{{json .Config.Env}}}}" {container_id}')
    
    try:
        env_list = json.loads(output)
        env_dict = {}
        for item in env_list:
            if "=" in item:
                key, value = item.split("=", 1)
                env_dict[key] = value
        return env_dict
    except json.JSONDecodeError:
        print(f"Erro ao decodificar JSON para o contêiner {container_id}")
        return {}

def mask_sensitive_value(name: str, value: str) -> str:
    """
    Mascara valores sensíveis para exibição segura.
    
    Args:
        name: Nome da variável
        value: Valor da variável
        
    Returns:
        Valor mascarado
    """
    sensitive_vars = [
        "KEY", "SECRET", "PASSWORD", "TOKEN", "CREDENTIAL"
    ]
    
    is_sensitive = any(pattern in name.upper() for pattern in sensitive_vars)
    
    if is_sensitive:
        if len(value) > 8:
            return value[:4] + "..." + value[-4:]
        else:
            return "****"
    return value

def compare_env_vars(file_vars: Dict[str, str], container_vars: Dict[str, str]) -> Dict:
    """
    Compara variáveis de ambiente do arquivo .env com as do contêiner.
    
    Args:
        file_vars: Variáveis do arquivo .env
        container_vars: Variáveis do contêiner
        
    Returns:
        Dicionário com resultados da comparação
    """
    file_keys = set(file_vars.keys())
    container_keys = set(container_vars.keys())
    
    # Variáveis presentes em ambos
    common_keys = file_keys.intersection(container_keys)
    
    # Variáveis apenas no arquivo
    only_in_file = file_keys - container_keys
    
    # Variáveis apenas no contêiner
    only_in_container = container_keys - file_keys
    
    # Variáveis com valores diferentes
    different_values = {}
    for key in common_keys:
        if file_vars[key] != container_vars[key]:
            different_values[key] = {
                "file_value": mask_sensitive_value(key, file_vars[key]),
                "container_value": mask_sensitive_value(key, container_vars[key])
            }
    
    return {
        "common_count": len(common_keys),
        "only_in_file": sorted(list(only_in_file)),
        "only_in_container": sorted(list(only_in_container)),
        "different_values": different_values
    }

def main():
    """Função principal do script."""
    print("Comparando variáveis de ambiente dos arquivos .env com os contêineres...")
    
    # Caminhos para os arquivos .env
    renum_env_path = "renum-backend/.env"
    suna_env_path = "Suna backend/.env"
    
    # Ler variáveis dos arquivos .env
    renum_file_vars = parse_env_file(renum_env_path)
    suna_file_vars = parse_env_file(suna_env_path)
    
    print(f"Variáveis encontradas no arquivo {renum_env_path}: {len(renum_file_vars)}")
    print(f"Variáveis encontradas no arquivo {suna_env_path}: {len(suna_file_vars)}")
    
    # Obter contêineres
    renum_containers = get_container_ids("renum")
    suna_containers = get_container_ids("suna")
    
    results = {
        "renum": [],
        "suna": []
    }
    
    # Comparar variáveis do Renum
    for container in renum_containers:
        container_id = container["id"]
        container_name = container["name"]
        
        container_vars = get_container_env_vars(container_id)
        comparison = compare_env_vars(renum_file_vars, container_vars)
        
        results["renum"].append({
            "container_id": container_id,
            "container_name": container_name,
            "comparison": comparison
        })
    
    # Comparar variáveis do Suna
    for container in suna_containers:
        container_id = container["id"]
        container_name = container["name"]
        
        container_vars = get_container_env_vars(container_id)
        comparison = compare_env_vars(suna_file_vars, container_vars)
        
        results["suna"].append({
            "container_id": container_id,
            "container_name": container_name,
            "comparison": comparison
        })
    
    # Gerar relatório
    report = ["# Relatório de Comparação de Variáveis de Ambiente", ""]
    
    for service_name, service_results in results.items():
        report.append(f"## Serviço: {service_name.upper()}")
        
        if not service_results:
            report.append(f"Nenhum contêiner {service_name} encontrado.\n")
            continue
        
        for result in service_results:
            container_name = result["container_name"]
            container_id = result["container_id"]
            comparison = result["comparison"]
            
            report.append(f"### Contêiner: {container_name} ({container_id[:12]})")
            report.append(f"- Variáveis em comum: {comparison['common_count']}")
            
            if comparison["only_in_file"]:
                report.append("\n#### Variáveis presentes apenas no arquivo .env:")
                for var in comparison["only_in_file"]:
                    report.append(f"- {var}")
            
            if comparison["only_in_container"]:
                report.append("\n#### Variáveis presentes apenas no contêiner:")
                for var in comparison["only_in_container"]:
                    report.append(f"- {var}")
            
            if comparison["different_values"]:
                report.append("\n#### Variáveis com valores diferentes:")
                for var, values in comparison["different_values"].items():
                    report.append(f"- {var}:")
                    report.append(f"  - No arquivo: {values['file_value']}")
                    report.append(f"  - No contêiner: {values['container_value']}")
            
            report.append("")
    
    # Adicionar recomendações
    report.append("## Recomendações")
    report.append("")
    report.append("### Ações recomendadas:")
    report.append("1. **Sincronizar variáveis** - Garantir que as variáveis nos arquivos .env e nos contêineres estejam sincronizadas.")
    report.append("2. **Verificar diferenças de valores** - Investigar por que algumas variáveis têm valores diferentes.")
    report.append("3. **Documentar variáveis adicionais** - Adicionar à documentação quaisquer variáveis presentes apenas nos contêineres.")
    report.append("4. **Remover variáveis não utilizadas** - Considerar remover variáveis presentes apenas nos arquivos .env se não forem necessárias.")
    
    # Salvar relatório em arquivo
    report_path = os.path.join(os.path.dirname(__file__), "..", "reports")
    os.makedirs(report_path, exist_ok=True)
    
    report_file = os.path.join(report_path, "env_comparison_report.md")
    with open(report_file, "w", encoding="utf-8") as f:
        f.write("\n".join(report))
    
    print(f"Relatório salvo em: {report_file}")

if __name__ == "__main__":
    main()