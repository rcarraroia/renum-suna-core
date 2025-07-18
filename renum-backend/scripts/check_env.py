"""
Script para verificar a configuração das variáveis de ambiente.

Este script verifica se todas as variáveis de ambiente necessárias estão configuradas
corretamente e exibe um relatório detalhado.
"""

import os
import sys
import json
import logging
from pathlib import Path
from dotenv import load_dotenv

# Adicionar o diretório raiz ao path para importar módulos
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

# Carregar variáveis de ambiente
env_file = root_dir / ".env"
if env_file.exists():
    load_dotenv(dotenv_path=env_file)
    print(f"Carregando variáveis de ambiente de: {env_file}")
else:
    print(f"Arquivo .env não encontrado em: {env_file}")
    # Tentar carregar do diretório raiz do projeto
    parent_env_file = root_dir.parent / ".env"
    if parent_env_file.exists():
        load_dotenv(dotenv_path=parent_env_file)
        print(f"Carregando variáveis de ambiente de: {parent_env_file}")

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

from app.utils.env_validator import check_env_configuration

def main():
    """Função principal."""
    try:
        logger.info("Verificando configuração das variáveis de ambiente...")
        results = check_env_configuration()
        
        # Exibir resultados
        print("\n=== Relatório de Configuração de Ambiente ===\n")
        
        # Verificar Supabase (obrigatório)
        supabase_status = results["supabase"]["status"]
        print(f"Supabase (Obrigatório): {'✅ OK' if supabase_status == 'ok' else '❌ ERRO'}")
        if supabase_status == "ok":
            for var, details in results["supabase"]["details"].items():
                print(f"  - {var}: {details['value']}")
        else:
            print(f"  - Erro: {results['supabase'].get('error', 'Desconhecido')}")
        
        # Verificar variáveis opcionais
        optional_status = results["optional"]["status"]
        print(f"\nVariáveis Opcionais: {'✅ OK' if optional_status == 'ok' else '⚠️ AVISO'}")
        if results["optional"]["details"]:
            for var, details in results["optional"]["details"].items():
                status_icon = "✅" if details["status"] == "ok" else "⚠️"
                value = details["value"] if details["value"] else "Não configurado"
                print(f"  - {status_icon} {var}: {value}")
        else:
            print("  - Nenhuma variável opcional configurada")
        
        # Resumo
        print("\n=== Resumo ===")
        if supabase_status == "ok":
            print("✅ Configuração básica OK. A aplicação pode ser iniciada.")
        else:
            print("❌ Configuração incompleta. Corrija os erros antes de iniciar a aplicação.")
        
        # Retornar código de saída
        if supabase_status != "ok":
            return 1
        return 0
    
    except Exception as e:
        logger.error(f"Erro ao verificar configuração: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())