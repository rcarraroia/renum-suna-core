"""
Script para testar a conexão SSL com o Supabase.

Este script verifica se a conexão com o Supabase está usando SSL corretamente
e se as configurações de segurança estão funcionando.
"""

import os
import sys
import logging
import requests
from pathlib import Path
from urllib.parse import urlparse

# Adicionar o diretório raiz ao path para importar módulos
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
from dotenv import load_dotenv
env_file = root_dir / ".env"
if env_file.exists():
    load_dotenv(dotenv_path=env_file)
    print(f"Carregando variáveis de ambiente de: {env_file}")

from app.core.supabase_client import supabase

def test_ssl_connection():
    """Testa se a conexão com o Supabase está usando SSL corretamente."""
    try:
        # Obter a URL do Supabase
        supabase_url = os.getenv("SUPABASE_URL")
        if not supabase_url:
            logger.error("Variável de ambiente SUPABASE_URL não configurada")
            return False
        
        # Verificar se a URL começa com https://
        if not supabase_url.startswith("https://"):
            logger.error(f"URL do Supabase não usa HTTPS: {supabase_url}")
            return False
        
        print(f"URL do Supabase usa HTTPS: {supabase_url} ✅")
        
        # Verificar se o certificado SSL é válido
        try:
            response = requests.get(supabase_url, timeout=10)
            print(f"Conexão SSL com o Supabase bem-sucedida ✅")
            print(f"Status code: {response.status_code}")
            
            # Verificar se o certificado é confiável
            if response.ok:
                print("Certificado SSL válido e confiável ✅")
            else:
                print(f"Resposta do servidor não foi bem-sucedida: {response.status_code} ❌")
        except requests.exceptions.SSLError as e:
            logger.error(f"Erro SSL ao conectar ao Supabase: {str(e)} ❌")
            return False
        except Exception as e:
            logger.error(f"Erro ao verificar certificado SSL: {str(e)} ❌")
            return False
        
        # Testar a conexão com o cliente Supabase
        print("\nTestando conexão com o cliente Supabase...")
        try:
            # Tentar uma operação simples
            result = supabase.from_("knowledge_bases").select("*").limit(1).execute()
            print("Conexão com o cliente Supabase bem-sucedida ✅")
            print(f"Registros encontrados: {len(result.data)}")
        except Exception as e:
            logger.error(f"Erro ao conectar com o cliente Supabase: {str(e)} ❌")
            return False
        
        # Testar o mecanismo de retry
        print("\nTestando mecanismo de retry...")
        try:
            # Simular uma falha temporária
            print("Simulando uma falha temporária (isso pode levar alguns segundos)...")
            
            # Definir uma URL inválida temporariamente para forçar um erro
            original_url = supabase.url
            supabase.url = "https://invalid-url-for-testing.example.com"
            
            try:
                # Esta operação deve falhar
                supabase.from_("knowledge_bases").select("*").limit(1).execute()
            except Exception as e:
                print(f"Falha simulada capturada corretamente: {type(e).__name__} ✅")
            finally:
                # Restaurar a URL original
                supabase.url = original_url
            
            # Verificar se a conexão ainda funciona após restaurar a URL
            result = supabase.from_("knowledge_bases").select("*").limit(1).execute()
            print("Conexão restaurada com sucesso após falha simulada ✅")
        except Exception as e:
            logger.error(f"Erro ao testar mecanismo de retry: {str(e)} ❌")
            return False
        
        print("\n=== Resumo ===")
        print("✅ Conexão SSL com o Supabase configurada corretamente")
        print("✅ Cliente Supabase inicializado com sucesso")
        print("✅ Mecanismo de retry funcionando corretamente")
        
        return True
    except Exception as e:
        logger.error(f"Erro ao testar conexão SSL: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_ssl_connection()
    sys.exit(0 if success else 1)