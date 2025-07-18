#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para validar as variáveis de ambiente dos contêineres Renum e Suna
e comparar com as variáveis esperadas conforme a documentação.
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from typing import Dict, List, Tuple, Set

# Mapeamento de variáveis esperadas por serviço
EXPECTED_ENV_VARS = {
    "renum": {
        "required": [
            "SUPABASE_URL",
            "SUPABASE_KEY",
            "DATABASE_URL",
            "SUNA_API_URL",
            "SUNA_API_KEY",
            "OPENAI_API_KEY",
            "JWT_SECRET",
            "CORS_ORIGINS"
        ],
        "optional": [
            "ANTHROPIC_API_KEY",
            "PGVECTOR_ENABLED",
            "LOG_LEVEL",
            "ENVIRONMENT",
            "PORT",
            "HOST",
            "DEBUG"
        ]
    },
    "suna": {
        "required": [
            "SUPABASE_URL",
            "SUPABASE_KEY",
            "DATABASE_URL",
            "REDIS_URL",
            "RABBITMQ_URL",
            "OPENAI_API_KEY",
            "JWT_SECRET"
        ],
        "optional": [
            "ANTHROPIC_API_KEY",
            "SENTRY_DSN",
            "CORS_ORIGINS",
            "LOG_LEVEL",
            "ENVIRONMENT",
            "PORT",
            "HOST",
            "DEBUG",
            "GROQ_API_KEY",
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "AWS_REGION"
        ]
    }
}

# Regras de validação para variáveis específicas
VALIDATION_RULES = {
    "SUPABASE_URL": lambda v: v.startswith(("http://", "https://")),
    "DATABASE_URL": lambda v: v.startswith("postgresql://"),
    "REDIS_URL": lambda v: v.startswith("redis://"),
    "RABBITMQ_URL": lambda v: v.startswith(("amqp://", "amqps://")),
    "SUNA_API_URL": lambda v: v.startswith(("http://", "https://")),
    "JWT_SECRET": lambda v: len(v) >= 16,
    "CORS_ORIGINS": lambda v: "*" in v or v.startswith(("http://", "https://"))
}

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

def validate_env_var(name: str, value: str) -> Tuple[bool, str]:
    """
    Valida o valor de uma variável de ambiente.
    
    Args:
        name: Nome da variável
        value: Valor da variável
        
    Returns:
        Tuple com status de validação e mensagem
    """
    if not value:
        return False, "Valor vazio"
    
    # Aplicar regra de validação específica, se existir
    if name in VALIDATION_RULES:
        if not VALIDATION_RULES[name](value):
            return False, f"Formato inválido para {name}"
    
    # Validações específicas para chaves de API
    if name.endswith("_API_KEY") and len(value) < 20:
        return False, "Chave de API muito curta"
    
    return True, "Válido"

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

def analyze_container_env_vars(service_type: str, container: Dict[str, str]) -> Dict:
    """
    Analisa as variáveis de ambiente de um contêiner.
    
    Args:
        service_type: Tipo de serviço (renum ou suna)
        container: Dicionário com ID e nome do contêiner
        
    Returns:
        Dicionário com resultados da análise
    """
    container_id = container["id"]
    container_name = container["name"]
    
    env_vars = get_container_env_vars(container_id)
    
    # Obter variáveis esperadas
    expected_vars = EXPECTED_ENV_VARS.get(service_type, {"required": [], "optional": []})
    required_vars = set(expected_vars["required"])
    optional_vars = set(expected_vars["optional"])
    all_expected_vars = required_vars.union(optional_vars)
    
    # Verificar variáveis
    present_vars = set(env_vars.keys())
    missing_required = required_vars - present_vars
    missing_optional = optional_vars - present_vars
    unexpected_vars = present_vars - all_expected_vars
    
    # Validar variáveis presentes
    validation_results = {}
    for var_name, var_value in env_vars.items():
        is_valid, message = validate_env_var(var_name, var_value)
        validation_results[var_name] = {
            "valid": is_valid,
            "message": message,
            "value": mask_sensitive_value(var_name, var_value),
            "is_required": var_name in required_vars
        }
    
    return {
        "container_id": container_id,
        "container_name": container_name,
        "service_type": service_type,
        "total_vars": len(env_vars),
        "missing_required": sorted(list(missing_required)),
        "missing_optional": sorted(list(missing_optional)),
        "unexpected_vars": sorted(list(unexpected_vars)),
        "validation_results": validation_results
    }

def generate_report(results: Dict[str, List[Dict]]) -> str:
    """
    Gera um relatório formatado com os resultados da análise.
    
    Args:
        results: Dicionário com resultados por serviço
        
    Returns:
        Relatório formatado
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = [
        "# Relatório de Análise de Variáveis de Ambiente",
        f"Data: {now}\n",
        "## Resumo",
    ]
    
    # Contadores para resumo
    total_containers = 0
    containers_with_issues = 0
    missing_required_count = 0
    invalid_vars_count = 0
    
    # Processar resultados para resumo
    for service_results in results.values():
        total_containers += len(service_results)
        
        for result in service_results:
            has_issues = False
            
            if result["missing_required"]:
                has_issues = True
                missing_required_count += len(result["missing_required"])
            
            for var_info in result["validation_results"].values():
                if not var_info["valid"]:
                    has_issues = True
                    invalid_vars_count += 1
            
            if has_issues:
                containers_with_issues += 1
    
    # Adicionar resumo ao relatório
    report.extend([
        f"- Total de contêineres analisados: {total_containers}",
        f"- Contêineres com problemas: {containers_with_issues}",
        f"- Variáveis obrigatórias ausentes: {missing_required_count}",
        f"- Variáveis com valores inválidos: {invalid_vars_count}\n"
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
            report.append(f"- Total de variáveis: {result['total_vars']}")
            
            # Variáveis ausentes
            if result["missing_required"]:
                report.append("\n#### ❌ Variáveis obrigatórias ausentes:")
                for var in result["missing_required"]:
                    report.append(f"- {var}")
            else:
                report.append("\n✅ Todas as variáveis obrigatórias estão presentes.")
            
            if result["missing_optional"]:
                report.append("\n#### Variáveis opcionais ausentes:")
                for var in result["missing_optional"]:
                    report.append(f"- {var}")
            
            # Variáveis inesperadas
            if result["unexpected_vars"]:
                report.append("\n#### Variáveis não documentadas:")
                for var in result["unexpected_vars"]:
                    report.append(f"- {var}")
            
            # Validação de variáveis
            report.append("\n#### Validação de variáveis:")
            
            # Primeiro listar variáveis com problemas
            invalid_vars = [(name, info) for name, info in result["validation_results"].items() if not info["valid"]]
            if invalid_vars:
                report.append("\n##### ❌ Variáveis com problemas:")
                for var_name, var_info in invalid_vars:
                    required_mark = "(Obrigatória)" if var_info["is_required"] else "(Opcional)"
                    report.append(f"- {var_name} {required_mark}")
                    report.append(f"  - Valor: {var_info['value']}")
                    report.append(f"  - Problema: {var_info['message']}")
            
            # Depois listar variáveis válidas
            valid_vars = [(name, info) for name, info in result["validation_results"].items() if info["valid"]]
            if valid_vars:
                report.append("\n##### ✅ Variáveis válidas:")
                for var_name, var_info in valid_vars:
                    required_mark = "(Obrigatória)" if var_info["is_required"] else "(Opcional)"
                    report.append(f"- {var_name} {required_mark}: {var_info['value']}")
            
            report.append("\n")
    
    # Adicionar recomendações
    report.append("## Recomendações")
    
    if containers_with_issues > 0:
        report.append("\n### Ações recomendadas:")
        
        if missing_required_count > 0:
            report.append("1. **Adicionar variáveis obrigatórias ausentes** - Verificar a documentação para os valores corretos.")
        
        if invalid_vars_count > 0:
            report.append("2. **Corrigir valores inválidos** - Atualizar as variáveis com formato incorreto.")
        
        report.append("3. **Revisar variáveis não documentadas** - Verificar se são realmente necessárias.")
        report.append("4. **Atualizar a documentação** - Garantir que todas as variáveis necessárias estejam documentadas.")
    else:
        report.append("\n✅ Todas as variáveis de ambiente parecem estar configuradas corretamente.")
    
    return "\n".join(report)

def main():
    """Função principal do script."""
    print("Analisando variáveis de ambiente dos contêineres Renum e Suna...")
    
    results = {
        "renum": [],
        "suna": []
    }
    
    # Analisar contêineres Renum
    renum_containers = get_container_ids("renum")
    if not renum_containers:
        print("Nenhum contêiner Renum encontrado.")
    
    for container in renum_containers:
        result = analyze_container_env_vars("renum", container)
        results["renum"].append(result)
    
    # Analisar contêineres Suna
    suna_containers = get_container_ids("suna")
    if not suna_containers:
        print("Nenhum contêiner Suna encontrado.")
    
    for container in suna_containers:
        result = analyze_container_env_vars("suna", container)
        results["suna"].append(result)
    
    # Gerar relatório
    report = generate_report(results)
    
    # Salvar relatório em arquivo
    report_path = os.path.join(os.path.dirname(__file__), "..", "reports")
    os.makedirs(report_path, exist_ok=True)
    
    report_file = os.path.join(report_path, "env_variables_analysis.md")
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"Relatório salvo em: {report_file}")
    print("\nResumo da análise:")
    
    # Verificar se há problemas críticos
    has_critical_issues = False
    for service_results in results.values():
        for result in service_results:
            if result["missing_required"]:
                has_critical_issues = True
                break
            
            for var_info in result["validation_results"].values():
                if not var_info["valid"] and var_info["is_required"]:
                    has_critical_issues = True
                    break
    
    if has_critical_issues:
        print("⚠️ ATENÇÃO: Foram encontrados problemas críticos nas variáveis de ambiente.")
        print("Recomenda-se corrigir esses problemas antes de prosseguir.")
    else:
        print("✅ Todas as variáveis de ambiente obrigatórias estão configuradas corretamente.")
    
    # Exibir o caminho do relatório
    print(f"\nPara mais detalhes, consulte o relatório: {report_file}")

if __name__ == "__main__":
    main()