#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para analisar variáveis de ambiente dos contêineres Renum e Suna.
Este script extrai as variáveis de ambiente dos contêineres, verifica a presença
das variáveis necessárias e valida os valores das variáveis críticas.
"""

import subprocess
import json
import os
import sys
from typing import Dict, List, Tuple, Optional

# Definição das variáveis de ambiente necessárias para cada serviço
REQUIRED_ENV_VARS = {
    "renum": [
        "SUPABASE_URL",
        "SUPABASE_KEY",
        "DATABASE_URL",
        "SUNA_API_URL",
        "SUNA_API_KEY",
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "PGVECTOR_ENABLED",
        "JWT_SECRET",
        "CORS_ORIGINS"
    ],
    "suna": [
        "SUPABASE_URL",
        "SUPABASE_KEY",
        "DATABASE_URL",
        "REDIS_URL",
        "RABBITMQ_URL",
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "SENTRY_DSN",
        "JWT_SECRET",
        "CORS_ORIGINS"
    ]
}

# Variáveis críticas que precisam ser validadas
CRITICAL_ENV_VARS = [
    "SUPABASE_URL",
    "SUPABASE_KEY",
    "DATABASE_URL",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "JWT_SECRET"
]

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

def get_container_ids(service_name: str) -> List[str]:
    """
    Obtém IDs dos contêineres com base no nome do serviço.
    
    Args:
        service_name: Nome do serviço (renum ou suna)
        
    Returns:
        Lista de IDs dos contêineres
    """
    stdout, _, _ = run_command(f'docker ps -a --filter "name={service_name}" --format "{{{{.ID}}}}"')
    return [line.strip() for line in stdout.splitlines() if line.strip()]

def get_container_env_vars(container_id: str) -> Dict[str, str]:
    """
    Obtém variáveis de ambiente de um contêiner.
    
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
        print(f"Erro ao decodificar JSON para o contêiner {container_id}")
        return {}

def validate_env_var(name: str, value: str) -> Tuple[bool, str]:
    """
    Valida o valor de uma variável de ambiente crítica.
    
    Args:
        name: Nome da variável
        value: Valor da variável
        
    Returns:
        Tuple contendo status (True se válido) e mensagem
    """
    if not value:
        return False, f"Valor vazio para {name}"
    
    if name == "SUPABASE_URL":
        if not (value.startswith("http://") or value.startswith("https://")):
            return False, f"URL do Supabase inválida: {value}"
    
    elif name == "SUPABASE_KEY":
        if len(value) < 20:  # Chaves Supabase são geralmente longas
            return False, f"Chave Supabase parece inválida (muito curta)"
    
    elif name == "DATABASE_URL":
        if not value.startswith("postgresql://"):
            return False, f"URL de banco de dados inválida: {value}"
    
    elif name in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY"]:
        if len(value) < 20:  # Chaves de API são geralmente longas
            return False, f"Chave de API parece inválida (muito curta)"
    
    elif name == "JWT_SECRET":
        if len(value) < 16:  # Segredos JWT devem ser suficientemente longos
            return False, f"Segredo JWT muito curto (menos de 16 caracteres)"
    
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
    if name in ["SUPABASE_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "JWT_SECRET"]:
        if len(value) > 8:
            return value[:4] + "..." + value[-4:]
        else:
            return "****"
    return value

def analyze_container_env_vars(service_name: str, container_id: str, env_vars: Dict[str, str]) -> Dict:
    """
    Analisa as variáveis de ambiente de um contêiner.
    
    Args:
        service_name: Nome do serviço
        container_id: ID do contêiner
        env_vars: Dicionário com variáveis de ambiente
        
    Returns:
        Dicionário com resultados da análise
    """
    required_vars = REQUIRED_ENV_VARS.get(service_name, [])
    
    # Verificar variáveis necessárias
    missing_vars = [var for var in required_vars if var not in env_vars]
    
    # Validar variáveis críticas
    validation_results = {}
    for var in CRITICAL_ENV_VARS:
        if var in env_vars:
            is_valid, message = validate_env_var(var, env_vars[var])
            validation_results[var] = {
                "valid": is_valid,
                "message": message,
                "value": mask_sensitive_value(var, env_vars[var])
            }
    
    return {
        "container_id": container_id,
        "service_name": service_name,
        "total_vars": len(env_vars),
        "missing_vars": missing_vars,
        "validation_results": validation_results
    }

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
    
    for container_id in renum_containers:
        env_vars = get_container_env_vars(container_id)
        result = analyze_container_env_vars("renum", container_id, env_vars)
        results["renum"].append(result)
    
    # Analisar contêineres Suna
    suna_containers = get_container_ids("suna")
    if not suna_containers:
        print("Nenhum contêiner Suna encontrado.")
    
    for container_id in suna_containers:
        env_vars = get_container_env_vars(container_id)
        result = analyze_container_env_vars("suna", container_id, env_vars)
        results["suna"].append(result)
    
    # Exibir resultados
    print("\n=== RESULTADOS DA ANÁLISE DE VARIÁVEIS DE AMBIENTE ===\n")
    
    for service_name, service_results in results.items():
        print(f"\n## Serviço: {service_name.upper()} ##")
        
        if not service_results:
            print(f"Nenhum contêiner {service_name} encontrado.")
            continue
        
        for result in service_results:
            container_id = result["container_id"]
            print(f"\nContêiner: {container_id}")
            print(f"Total de variáveis: {result['total_vars']}")
            
            if result["missing_vars"]:
                print("\nVariáveis necessárias ausentes:")
                for var in result["missing_vars"]:
                    print(f"  - {var}")
            else:
                print("\nTodas as variáveis necessárias estão presentes.")
            
            print("\nValidação de variáveis críticas:")
            for var, validation in result["validation_results"].items():
                status = "✅ Válido" if validation["valid"] else "❌ Inválido"
                print(f"  - {var}: {status}")
                print(f"    Valor: {validation['value']}")
                if not validation["valid"]:
                    print(f"    Problema: {validation['message']}")
    
    print("\n=== FIM DA ANÁLISE ===\n")
    
    # Verificar se há problemas críticos
    has_critical_issues = False
    for service_results in results.values():
        for result in service_results:
            if result["missing_vars"]:
                has_critical_issues = True
                break
            
            for validation in result["validation_results"].values():
                if not validation["valid"]:
                    has_critical_issues = True
                    break
    
    if has_critical_issues:
        print("⚠️ ATENÇÃO: Foram encontrados problemas críticos nas variáveis de ambiente.")
        print("Recomenda-se corrigir esses problemas antes de prosseguir.")
    else:
        print("✅ Todas as variáveis de ambiente parecem estar configuradas corretamente.")

if __name__ == "__main__":
    main()