"""
Utilitário para validar variáveis de ambiente.

Este módulo fornece funções para validar se todas as variáveis de ambiente
necessárias estão configuradas corretamente.
"""

import os
import logging
from typing import List, Dict, Any, Optional

# Configurar logger
logger = logging.getLogger(__name__)

def validate_required_env_vars(required_vars: List[str]) -> Dict[str, Any]:
    """Valida se todas as variáveis de ambiente necessárias estão configuradas.
    
    Args:
        required_vars: Lista de nomes de variáveis de ambiente necessárias.
    
    Returns:
        Dicionário com o status de cada variável de ambiente.
    
    Raises:
        ValueError: Se alguma variável de ambiente necessária não estiver configurada.
    """
    results = {}
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if value is None or value.strip() == "":
            results[var] = {"status": "missing", "value": None}
            missing_vars.append(var)
        else:
            # Mascarar valores sensíveis
            masked_value = mask_sensitive_value(var, value)
            results[var] = {"status": "ok", "value": masked_value}
    
    if missing_vars:
        error_msg = f"Variáveis de ambiente necessárias não configuradas: {', '.join(missing_vars)}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    return results

def mask_sensitive_value(var_name: str, value: str) -> str:
    """Mascara valores sensíveis para exibição em logs.
    
    Args:
        var_name: Nome da variável de ambiente.
        value: Valor da variável de ambiente.
    
    Returns:
        Valor mascarado se a variável for sensível, ou o valor original caso contrário.
    """
    sensitive_vars = [
        "KEY", "SECRET", "PASSWORD", "TOKEN", "CREDENTIAL", "API_KEY"
    ]
    
    # Verificar se o nome da variável contém alguma palavra sensível
    is_sensitive = any(s in var_name.upper() for s in sensitive_vars)
    
    if is_sensitive:
        if len(value) <= 8:
            return "****"
        else:
            return value[:4] + "****" + value[-4:]
    
    return value

def check_env_configuration() -> Dict[str, Any]:
    """Verifica a configuração das variáveis de ambiente.
    
    Returns:
        Dicionário com o status de cada grupo de variáveis de ambiente.
    """
    results = {
        "supabase": {"status": "unknown", "details": {}},
        "optional": {"status": "unknown", "details": {}}
    }
    
    # Verificar variáveis obrigatórias do Supabase
    try:
        supabase_vars = ["SUPABASE_URL", "SUPABASE_KEY", "SUPABASE_SERVICE_KEY"]
        results["supabase"]["details"] = validate_required_env_vars(supabase_vars)
        results["supabase"]["status"] = "ok"
    except ValueError as e:
        results["supabase"]["status"] = "error"
        results["supabase"]["error"] = str(e)
    
    # Verificar variáveis opcionais
    optional_vars = ["SUPABASE_DB_URL"]
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            masked_value = mask_sensitive_value(var, value)
            results["optional"]["details"][var] = {"status": "ok", "value": masked_value}
        else:
            results["optional"]["details"][var] = {"status": "missing", "value": None}
    
    # Variáveis opcionais são sempre consideradas ok
    results["optional"]["status"] = "ok"
    
    return results