#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para verificar a estrutura de diretórios e permissões dos serviços Renum e Suna.
Este script mapeia a estrutura de diretórios, verifica permissões e identifica discrepâncias
com a estrutura esperada.
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from typing import Dict, List, Tuple, Set, Any

# Estrutura esperada para os serviços
EXPECTED_STRUCTURE = {
    "renum": {
        "directories": [
            "/app",
            "/app/api",
            "/app/api/routes",
            "/app/api/schemas",
            "/app/core",
            "/app/db",
            "/app/models",
            "/app/repositories",
            "/app/services",
            "/app/utils",
            "/scripts",
            "/tests"
        ],
        "critical_files": [
            "/app/api/__init__.py",
            "/app/core/config.py",
            "/app/core/supabase_client.py",
            "/app/db/pg_pool.py",
            "/app/models/base.py",
            "/app/repositories/base.py",
            "/app/services/__init__.py",
            "/app/utils/retry.py"
        ]
    },
    "suna": {
        "directories": [
            "/agent",
            "/agentpress",
            "/knowledge_base",
            "/mcp_service",
            "/services",
            "/supabase",
            "/triggers",
            "/utils"
        ],
        "critical_files": [
            "/api.py",
            "/services/redis_service.py",
            "/services/supabase_service.py",
            "/utils/config.py",
            "/utils/logger.py"
        ]
    }
}

# Permissões esperadas para diretórios e arquivos
EXPECTED_PERMISSIONS = {
    "directories": {
        "owner": "rwx",
        "group": "r-x",
        "others": "r-x"
    },
    "files": {
        "owner": "rw-",
        "group": "r--",
        "others": "r--"
    },
    "executables": {
        "owner": "rwx",
        "group": "r-x",
        "others": "r-x"
    }
}

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

def get_directory_structure(container_id: str, base_path: str = "/") -> Dict[str, Any]:
    """
    Obtém a estrutura de diretórios de um contêiner.
    
    Args:
        container_id: ID do contêiner
        base_path: Caminho base para iniciar a busca
        
    Returns:
        Dicionário com a estrutura de diretórios
    """
    stdout, _, _ = run_command(f'docker exec {container_id} find {base_path} -type d -not -path "*/\\.*" | sort')
    directories = [line.strip() for line in stdout.splitlines() if line.strip()]
    
    stdout, _, _ = run_command(f'docker exec {container_id} find {base_path} -type f -not -path "*/\\.*" | sort')
    files = [line.strip() for line in stdout.splitlines() if line.strip()]
    
    return {
        "directories": directories,
        "files": files
    }

def get_file_permissions(container_id: str, path: str) -> Dict[str, str]:
    """
    Obtém as permissões de um arquivo ou diretório.
    
    Args:
        container_id: ID do contêiner
        path: Caminho do arquivo ou diretório
        
    Returns:
        Dicionário com as permissões
    """
    stdout, _, _ = run_command(f'docker exec {container_id} ls -la {path} | tail -n 1')
    
    if not stdout:
        return {
            "permissions": "unknown",
            "owner": "unknown",
            "group": "unknown"
        }
    
    parts = stdout.split()
    if len(parts) < 4:
        return {
            "permissions": "unknown",
            "owner": "unknown",
            "group": "unknown"
        }
    
    permissions = parts[0]
    owner = parts[2]
    group = parts[3]
    
    return {
        "permissions": permissions,
        "owner": owner,
        "group": group
    }

def parse_permissions(permissions_str: str) -> Dict[str, str]:
    """
    Analisa uma string de permissões no formato Unix.
    
    Args:
        permissions_str: String de permissões (ex: 'drwxr-xr-x')
        
    Returns:
        Dicionário com permissões separadas por owner, group e others
    """
    if len(permissions_str) < 10:
        return {
            "type": "unknown",
            "owner": "unknown",
            "group": "unknown",
            "others": "unknown"
        }
    
    file_type = "d" if permissions_str[0] == "d" else "f"
    owner = permissions_str[1:4]
    group = permissions_str[4:7]
    others = permissions_str[7:10]
    
    return {
        "type": file_type,
        "owner": owner,
        "group": group,
        "others": others
    }

def check_permissions(permissions: Dict[str, str], expected: Dict[str, str]) -> bool:
    """
    Verifica se as permissões correspondem às esperadas.
    
    Args:
        permissions: Permissões atuais
        expected: Permissões esperadas
        
    Returns:
        True se as permissões correspondem às esperadas, False caso contrário
    """
    for key, value in expected.items():
        if key not in permissions or permissions[key] != value:
            return False
    return True

def analyze_directory_structure(service_type: str, container: Dict[str, str]) -> Dict[str, Any]:
    """
    Analisa a estrutura de diretórios de um contêiner.
    
    Args:
        service_type: Tipo de serviço (renum ou suna)
        container: Dicionário com ID e nome do contêiner
        
    Returns:
        Dicionário com resultados da análise
    """
    container_id = container["id"]
    container_name = container["name"]
    
    # Obter estrutura de diretórios
    structure = get_directory_structure(container_id)
    
    # Obter estrutura esperada
    expected = EXPECTED_STRUCTURE.get(service_type, {"directories": [], "critical_files": []})
    
    # Verificar diretórios
    missing_directories = []
    for directory in expected["directories"]:
        if directory not in structure["directories"]:
            missing_directories.append(directory)
    
    # Verificar arquivos críticos
    missing_files = []
    for file in expected["critical_files"]:
        if file not in structure["files"]:
            missing_files.append(file)
    
    # Verificar permissões de diretórios
    directory_permissions = {}
    for directory in structure["directories"][:20]:  # Limitar para evitar sobrecarga
        perms = get_file_permissions(container_id, directory)
        parsed_perms = parse_permissions(perms["permissions"])
        directory_permissions[directory] = {
            "permissions": perms["permissions"],
            "owner": perms["owner"],
            "group": perms["group"],
            "parsed": parsed_perms
        }
    
    # Verificar permissões de arquivos críticos
    file_permissions = {}
    for file in structure["files"]:
        if file in expected["critical_files"]:
            perms = get_file_permissions(container_id, file)
            parsed_perms = parse_permissions(perms["permissions"])
            file_permissions[file] = {
                "permissions": perms["permissions"],
                "owner": perms["owner"],
                "group": perms["group"],
                "parsed": parsed_perms
            }
    
    # Identificar problemas de permissões
    permission_issues = []
    
    # Verificar permissões de diretórios
    for directory, perms in directory_permissions.items():
        parsed = perms["parsed"]
        if parsed["type"] == "d":
            expected_perms = EXPECTED_PERMISSIONS["directories"]
            if not (
                parsed["owner"].startswith("r") and 
                parsed["owner"].endswith("x") and
                "w" in parsed["owner"]
            ):
                permission_issues.append({
                    "path": directory,
                    "type": "directory",
                    "issue": "Permissões de proprietário insuficientes",
                    "current": parsed["owner"],
                    "expected": expected_perms["owner"]
                })
    
    # Verificar permissões de arquivos
    for file, perms in file_permissions.items():
        parsed = perms["parsed"]
        if parsed["type"] == "f":
            # Verificar se é um executável
            is_executable = file.endswith(".sh") or file.endswith(".py")
            expected_perms = EXPECTED_PERMISSIONS["executables"] if is_executable else EXPECTED_PERMISSIONS["files"]
            
            if is_executable and "x" not in parsed["owner"]:
                permission_issues.append({
                    "path": file,
                    "type": "file",
                    "issue": "Arquivo executável sem permissão de execução",
                    "current": parsed["owner"],
                    "expected": expected_perms["owner"]
                })
            elif not is_executable and not (
                parsed["owner"].startswith("r") and 
                "w" in parsed["owner"]
            ):
                permission_issues.append({
                    "path": file,
                    "type": "file",
                    "issue": "Permissões de proprietário insuficientes",
                    "current": parsed["owner"],
                    "expected": expected_perms["owner"]
                })
    
    return {
        "container_id": container_id,
        "container_name": container_name,
        "service_type": service_type,
        "total_directories": len(structure["directories"]),
        "total_files": len(structure["files"]),
        "missing_directories": missing_directories,
        "missing_files": missing_files,
        "permission_issues": permission_issues,
        "directory_permissions_sample": directory_permissions,
        "file_permissions": file_permissions
    }

def generate_report(results: Dict[str, List[Dict[str, Any]]]) -> str:
    """
    Gera um relatório formatado com os resultados da análise.
    
    Args:
        results: Dicionário com resultados por serviço
        
    Returns:
        Relatório formatado
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = [
        "# Relatório de Análise de Estrutura de Diretórios e Permissões",
        f"Data: {now}\n",
        "## Resumo",
    ]
    
    # Contadores para resumo
    total_containers = 0
    containers_with_issues = 0
    missing_directories_count = 0
    missing_files_count = 0
    permission_issues_count = 0
    
    # Processar resultados para resumo
    for service_results in results.values():
        total_containers += len(service_results)
        
        for result in service_results:
            has_issues = False
            
            if result["missing_directories"]:
                has_issues = True
                missing_directories_count += len(result["missing_directories"])
            
            if result["missing_files"]:
                has_issues = True
                missing_files_count += len(result["missing_files"])
            
            if result["permission_issues"]:
                has_issues = True
                permission_issues_count += len(result["permission_issues"])
            
            if has_issues:
                containers_with_issues += 1
    
    # Adicionar resumo ao relatório
    report.extend([
        f"- Total de contêineres analisados: {total_containers}",
        f"- Contêineres com problemas: {containers_with_issues}",
        f"- Diretórios ausentes: {missing_directories_count}",
        f"- Arquivos críticos ausentes: {missing_files_count}",
        f"- Problemas de permissões: {permission_issues_count}\n"
    ])
    
    # Adicionar detalhes por serviço
    for service_name, service_results in results.items():
        report.append(f"## Serviço: {service_name.upper()}")
        
        if not service_results:
            report.append(f"Nenhum contêiner {service_name} encontrado.\n")
            continue
        
        for result in service_results:
            container_name = result["container_name"]
            container_id = result["container_id"]
            
            report.append(f"### Contêiner: {container_name} ({container_id[:12]})")
            report.append(f"- Total de diretórios: {result['total_directories']}")
            report.append(f"- Total de arquivos: {result['total_files']}")
            
            # Diretórios ausentes
            if result["missing_directories"]:
                report.append("\n#### ❌ Diretórios ausentes:")
                for directory in result["missing_directories"]:
                    report.append(f"- {directory}")
            else:
                report.append("\n✅ Todos os diretórios esperados estão presentes.")
            
            # Arquivos ausentes
            if result["missing_files"]:
                report.append("\n#### ❌ Arquivos críticos ausentes:")
                for file in result["missing_files"]:
                    report.append(f"- {file}")
            else:
                report.append("\n✅ Todos os arquivos críticos estão presentes.")
            
            # Problemas de permissões
            if result["permission_issues"]:
                report.append("\n#### ❌ Problemas de permissões:")
                for issue in result["permission_issues"]:
                    report.append(f"- {issue['path']} ({issue['type']}):")
                    report.append(f"  - Problema: {issue['issue']}")
                    report.append(f"  - Atual: {issue['current']}")
                    report.append(f"  - Esperado: {issue['expected']}")
            else:
                report.append("\n✅ Nenhum problema de permissões identificado.")
            
            report.append("\n")
    
    # Adicionar recomendações
    report.append("## Recomendações")
    
    if containers_with_issues > 0:
        report.append("\n### Ações recomendadas:")
        
        if missing_directories_count > 0:
            report.append("1. **Criar diretórios ausentes** - Verificar se a estrutura do projeto está correta.")
        
        if missing_files_count > 0:
            report.append("2. **Adicionar arquivos críticos ausentes** - Verificar se os arquivos foram movidos ou renomeados.")
        
        if permission_issues_count > 0:
            report.append("3. **Corrigir problemas de permissões** - Ajustar permissões para garantir acesso adequado.")
            report.append("   - Para diretórios: `chmod -R 755 /caminho/do/diretorio`")
            report.append("   - Para arquivos: `chmod 644 /caminho/do/arquivo`")
            report.append("   - Para executáveis: `chmod 755 /caminho/do/executavel`")
    else:
        report.append("\n✅ A estrutura de diretórios e permissões parece estar configurada corretamente.")
    
    return "\n".join(report)

def main():
    """Função principal do script."""
    print("Analisando estrutura de diretórios e permissões dos contêineres Renum e Suna...")
    
    results = {
        "renum": [],
        "suna": []
    }
    
    # Analisar contêineres Renum
    renum_containers = get_container_ids("renum")
    if not renum_containers:
        print("Nenhum contêiner Renum encontrado.")
    
    for container in renum_containers:
        print(f"Analisando contêiner Renum: {container['name']}...")
        result = analyze_directory_structure("renum", container)
        results["renum"].append(result)
    
    # Analisar contêineres Suna
    suna_containers = get_container_ids("suna")
    if not suna_containers:
        print("Nenhum contêiner Suna encontrado.")
    
    for container in suna_containers:
        print(f"Analisando contêiner Suna: {container['name']}...")
        result = analyze_directory_structure("suna", container)
        results["suna"].append(result)
    
    # Gerar relatório
    report = generate_report(results)
    
    # Salvar relatório em arquivo
    report_path = os.path.join(os.path.dirname(__file__), "..", "reports")
    os.makedirs(report_path, exist_ok=True)
    
    report_file = os.path.join(report_path, "directory_structure_analysis.md")
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"Relatório salvo em: {report_file}")
    print("\nResumo da análise:")
    
    # Verificar se há problemas críticos
    has_critical_issues = False
    for service_results in results.values():
        for result in service_results:
            if result["missing_directories"] or result["missing_files"]:
                has_critical_issues = True
                break
    
    if has_critical_issues:
        print("⚠️ ATENÇÃO: Foram encontrados problemas críticos na estrutura de diretórios.")
        print("Recomenda-se corrigir esses problemas antes de prosseguir.")
    else:
        print("✅ A estrutura de diretórios parece estar configurada corretamente.")
    
    # Exibir o caminho do relatório
    print(f"\nPara mais detalhes, consulte o relatório: {report_file}")

if __name__ == "__main__":
    main()