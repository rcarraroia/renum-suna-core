#!/usr/bin/env python3
"""
Script para validar e testar a configuração do Sentry
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional

def check_sentry_dsn() -> Dict[str, Any]:
    """Verifica se o SENTRY_DSN está configurado"""
    result = {
        "configured": False,
        "valid_format": False,
        "dsn": None,
        "environment": None
    }
    
    sentry_dsn = os.getenv("SENTRY_DSN")
    if sentry_dsn:
        result["configured"] = True
        result["dsn"] = sentry_dsn[:20] + "..." if len(sentry_dsn) > 20 else sentry_dsn
        
        # Verificar formato básico do DSN
        if sentry_dsn.startswith("https://") and "@" in sentry_dsn and "sentry.io" in sentry_dsn:
            result["valid_format"] = True
    
    result["environment"] = os.getenv("ENVIRONMENT", "development")
    return result

def check_sentry_imports() -> Dict[str, Any]:
    """Verifica se o Sentry pode ser importado e inicializado"""
    result = {
        "sentry_sdk_available": False,
        "sentry_module_available": False,
        "integrations_available": [],
        "import_errors": []
    }
    
    try:
        import sentry_sdk
        result["sentry_sdk_available"] = True
    except ImportError as e:
        result["import_errors"].append(f"sentry_sdk: {str(e)}")
    
    try:
        import sentry
        result["sentry_module_available"] = True
    except ImportError as e:
        result["import_errors"].append(f"sentry module: {str(e)}")
    
    # Verificar integrações disponíveis
    integrations_to_check = [
        "sentry_sdk.integrations.fastapi",
        "sentry_sdk.integrations.dramatiq", 
        "sentry_sdk.integrations.redis",
        "sentry_sdk.integrations.sqlalchemy",
        "sentry_sdk.integrations.logging"
    ]
    
    for integration in integrations_to_check:
        try:
            __import__(integration)
            result["integrations_available"].append(integration.split(".")[-1])
        except ImportError:
            pass
    
    return result

def check_sentry_configuration() -> Dict[str, Any]:
    """Verifica a configuração atual do Sentry"""
    result = {
        "config_file_exists": False,
        "config_valid": False,
        "current_config": {},
        "issues": []
    }
    
    config_file = Path(__file__).parent / "sentry.py"
    
    if config_file.exists():
        result["config_file_exists"] = True
        
        try:
            with open(config_file, 'r') as f:
                content = f.read()
            
            # Análise básica da configuração
            if "sentry_sdk.init" in content:
                result["config_valid"] = True
                
                # Extrair configurações
                if "traces_sample_rate" in content:
                    result["current_config"]["traces_sample_rate"] = "configured"
                if "send_default_pii" in content:
                    result["current_config"]["send_default_pii"] = "configured"
                if "integrations" in content:
                    result["current_config"]["integrations"] = "configured"
                if "environment" in content:
                    result["current_config"]["environment"] = "configured"
                else:
                    result["issues"].append("Environment not configured")
                
                if "release" not in content:
                    result["issues"].append("Release version not configured")
                
                if "before_send" not in content:
                    result["issues"].append("before_send filter not configured")
                    
        except Exception as e:
            result["issues"].append(f"Error reading config file: {str(e)}")
    
    return result

def check_sentry_usage() -> Dict[str, Any]:
    """Verifica como o Sentry está sendo usado no código"""
    result = {
        "files_using_sentry": [],
        "usage_patterns": {
            "set_user": 0,
            "set_tag": 0,
            "capture_exception": 0,
            "capture_message": 0,
            "add_breadcrumb": 0
        },
        "recommendations": []
    }
    
    backend_dir = Path(__file__).parent
    python_files = list(backend_dir.rglob("*.py"))
    
    for file_path in python_files:
        if "venv" in str(file_path) or "__pycache__" in str(file_path):
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if "sentry" in content.lower():
                result["files_using_sentry"].append(str(file_path.relative_to(backend_dir)))
                
                # Contar padrões de uso
                if "set_user" in content:
                    result["usage_patterns"]["set_user"] += 1
                if "set_tag" in content:
                    result["usage_patterns"]["set_tag"] += 1
                if "capture_exception" in content:
                    result["usage_patterns"]["capture_exception"] += 1
                if "capture_message" in content:
                    result["usage_patterns"]["capture_message"] += 1
                if "add_breadcrumb" in content:
                    result["usage_patterns"]["add_breadcrumb"] += 1
                    
        except Exception:
            continue
    
    # Gerar recomendações
    if result["usage_patterns"]["capture_exception"] == 0:
        result["recommendations"].append("Consider adding explicit exception capturing")
    
    if result["usage_patterns"]["add_breadcrumb"] == 0:
        result["recommendations"].append("Consider adding breadcrumbs for better debugging")
    
    if len(result["files_using_sentry"]) < 3:
        result["recommendations"].append("Sentry usage could be expanded to more modules")
    
    return result

def test_sentry_connection() -> Dict[str, Any]:
    """Testa a conexão com o Sentry"""
    result = {
        "connection_test": False,
        "test_message_sent": False,
        "error": None
    }
    
    try:
        import sentry_sdk
        
        # Verificar se o Sentry está inicializado
        client = sentry_sdk.Hub.current.client
        if client and client.dsn:
            result["connection_test"] = True
            
            # Tentar enviar uma mensagem de teste (apenas se DSN estiver configurado)
            if os.getenv("SENTRY_DSN"):
                sentry_sdk.capture_message("Sentry configuration validation test", level="info")
                result["test_message_sent"] = True
        else:
            result["error"] = "Sentry client not initialized or DSN not configured"
            
    except Exception as e:
        result["error"] = str(e)
    
    return result

def generate_recommendations() -> list:
    """Gera recomendações para melhorar a configuração do Sentry"""
    recommendations = []
    
    dsn_check = check_sentry_dsn()
    config_check = check_sentry_configuration()
    usage_check = check_sentry_usage()
    
    if not dsn_check["configured"]:
        recommendations.append({
            "priority": "HIGH",
            "category": "Configuration",
            "issue": "SENTRY_DSN not configured",
            "solution": "Set SENTRY_DSN environment variable with your Sentry project DSN"
        })
    
    if not dsn_check["valid_format"]:
        recommendations.append({
            "priority": "HIGH", 
            "category": "Configuration",
            "issue": "Invalid SENTRY_DSN format",
            "solution": "Ensure DSN follows format: https://key@sentry.io/project-id"
        })
    
    if "Environment not configured" in config_check.get("issues", []):
        recommendations.append({
            "priority": "MEDIUM",
            "category": "Configuration", 
            "issue": "Environment not set in Sentry config",
            "solution": "Add environment parameter to sentry_sdk.init()"
        })
    
    if "Release version not configured" in config_check.get("issues", []):
        recommendations.append({
            "priority": "MEDIUM",
            "category": "Configuration",
            "issue": "Release version not configured",
            "solution": "Add release parameter to track deployments"
        })
    
    if usage_check["usage_patterns"]["capture_exception"] == 0:
        recommendations.append({
            "priority": "MEDIUM",
            "category": "Usage",
            "issue": "No explicit exception capturing found",
            "solution": "Add sentry_sdk.capture_exception() in error handlers"
        })
    
    if len(usage_check["files_using_sentry"]) < 3:
        recommendations.append({
            "priority": "LOW",
            "category": "Usage", 
            "issue": "Limited Sentry usage across codebase",
            "solution": "Expand Sentry integration to more modules for better monitoring"
        })
    
    return recommendations

def main():
    """Função principal"""
    print("🔍 Validando Configuração do Sentry")
    print("=" * 50)
    
    # Verificar DSN
    print("\n📋 Verificação do DSN:")
    dsn_result = check_sentry_dsn()
    print(f"  • DSN Configurado: {'✅' if dsn_result['configured'] else '❌'}")
    if dsn_result['configured']:
        print(f"  • Formato Válido: {'✅' if dsn_result['valid_format'] else '❌'}")
        print(f"  • DSN: {dsn_result['dsn']}")
    print(f"  • Environment: {dsn_result['environment']}")
    
    # Verificar imports
    print("\n📦 Verificação de Imports:")
    import_result = check_sentry_imports()
    print(f"  • sentry_sdk disponível: {'✅' if import_result['sentry_sdk_available'] else '❌'}")
    print(f"  • sentry module disponível: {'✅' if import_result['sentry_module_available'] else '❌'}")
    
    if import_result['integrations_available']:
        print(f"  • Integrações disponíveis: {', '.join(import_result['integrations_available'])}")
    
    if import_result['import_errors']:
        print("  • Erros de import:")
        for error in import_result['import_errors']:
            print(f"    - {error}")
    
    # Verificar configuração
    print("\n⚙️  Verificação da Configuração:")
    config_result = check_sentry_configuration()
    print(f"  • Arquivo de config existe: {'✅' if config_result['config_file_exists'] else '❌'}")
    print(f"  • Configuração válida: {'✅' if config_result['config_valid'] else '❌'}")
    
    if config_result['current_config']:
        print("  • Configurações encontradas:")
        for key, value in config_result['current_config'].items():
            print(f"    - {key}: {value}")
    
    if config_result['issues']:
        print("  • Problemas encontrados:")
        for issue in config_result['issues']:
            print(f"    - {issue}")
    
    # Verificar uso
    print("\n📊 Verificação de Uso:")
    usage_result = check_sentry_usage()
    print(f"  • Arquivos usando Sentry: {len(usage_result['files_using_sentry'])}")
    
    if usage_result['files_using_sentry']:
        print("  • Arquivos:")
        for file in usage_result['files_using_sentry'][:5]:  # Mostrar apenas os primeiros 5
            print(f"    - {file}")
        if len(usage_result['files_using_sentry']) > 5:
            print(f"    ... e mais {len(usage_result['files_using_sentry']) - 5} arquivos")
    
    print("  • Padrões de uso:")
    for pattern, count in usage_result['usage_patterns'].items():
        print(f"    - {pattern}: {count}")
    
    # Testar conexão
    print("\n🔗 Teste de Conexão:")
    connection_result = test_sentry_connection()
    print(f"  • Conexão: {'✅' if connection_result['connection_test'] else '❌'}")
    print(f"  • Mensagem de teste enviada: {'✅' if connection_result['test_message_sent'] else '❌'}")
    
    if connection_result['error']:
        print(f"  • Erro: {connection_result['error']}")
    
    # Gerar recomendações
    print("\n💡 Recomendações:")
    recommendations = generate_recommendations()
    
    if not recommendations:
        print("  ✅ Configuração do Sentry está adequada!")
    else:
        for i, rec in enumerate(recommendations, 1):
            priority_icon = "🔴" if rec["priority"] == "HIGH" else "🟡" if rec["priority"] == "MEDIUM" else "🟢"
            print(f"  {i}. {priority_icon} [{rec['priority']}] {rec['category']}")
            print(f"     Problema: {rec['issue']}")
            print(f"     Solução: {rec['solution']}")
            print()
    
    # Resumo final
    print("📊 RESUMO FINAL")
    print("=" * 30)
    
    total_checks = 4
    passed_checks = 0
    
    if dsn_result['configured'] and dsn_result['valid_format']:
        passed_checks += 1
    if import_result['sentry_sdk_available']:
        passed_checks += 1
    if config_result['config_valid']:
        passed_checks += 1
    if connection_result['connection_test']:
        passed_checks += 1
    
    print(f"Verificações passadas: {passed_checks}/{total_checks}")
    print(f"Status: {'✅ BOM' if passed_checks >= 3 else '⚠️ PRECISA MELHORAR' if passed_checks >= 2 else '❌ CRÍTICO'}")
    
    return 0 if passed_checks >= 3 else 1

if __name__ == '__main__':
    sys.exit(main())