#!/usr/bin/env python
"""
Script para testar a instalação e configuração do sistema.

Este script verifica se todas as dependências estão instaladas e se o sistema está configurado corretamente.
"""

import os
import sys
import importlib
import logging
from pathlib import Path
import asyncio

# Configura o logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def check_python_version():
    """
    Verifica se a versão do Python é compatível.
    
    Returns:
        bool: True se a versão é compatível, False caso contrário
    """
    required_version = (3, 9)
    current_version = sys.version_info
    
    if current_version < required_version:
        logger.error(f"Python {required_version[0]}.{required_version[1]} ou superior é necessário")
        return False
    
    logger.info(f"Versão do Python: {current_version[0]}.{current_version[1]}.{current_version[2]}")
    return True


def check_dependencies():
    """
    Verifica se todas as dependências estão instaladas.
    
    Returns:
        bool: True se todas as dependências estão instaladas, False caso contrário
    """
    required_packages = [
        "fastapi",
        "uvicorn",
        "pydantic",
        "supabase",
        "postgrest",
        "aioredis",
        "pyjwt",
        "cryptography",
        "httpx",
        "aiohttp",
        "python-dotenv",
        "python-multipart",
        "structlog"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            importlib.import_module(package)
            logger.info(f"Pacote {package} está instalado")
        except ImportError:
            logger.error(f"Pacote {package} não está instalado")
            missing_packages.append(package)
    
    if missing_packages:
        logger.error(f"Pacotes faltando: {', '.join(missing_packages)}")
        logger.error("Execute 'pip install -r requirements.txt' para instalar as dependências")
        return False
    
    return True


def check_env_file():
    """
    Verifica se o arquivo .env existe e contém as variáveis necessárias.
    
    Returns:
        bool: True se o arquivo .env existe e contém as variáveis necessárias, False caso contrário
    """
    env_file = Path(".") / ".env"
    
    if not env_file.exists():
        logger.error("Arquivo .env não encontrado")
        logger.error("Crie um arquivo .env com base no arquivo .env.example")
        return False
    
    required_vars = [
        "ENV",
        "API_PREFIX",
        "PROJECT_NAME",
        "VERSION",
        "SECRET_KEY",
        "SUPABASE_URL",
        "SUPABASE_KEY",
        "REDIS_URL",
        "SUNA_API_URL"
    ]
    
    missing_vars = []
    
    with open(env_file, "r") as f:
        env_content = f.read()
        
        for var in required_vars:
            if f"{var}=" not in env_content:
                missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Variáveis de ambiente faltando: {', '.join(missing_vars)}")
        return False
    
    logger.info("Arquivo .env está configurado corretamente")
    return True


async def check_database_connection():
    """
    Verifica a conexão com o banco de dados.
    
    Returns:
        bool: True se a conexão foi bem-sucedida, False caso contrário
    """
    try:
        # Adiciona o diretório raiz ao path para importar módulos da aplicação
        sys.path.insert(0, str(Path(__file__).parent.parent))
        
        from app.db.database import get_db
        
        # Obtém a conexão com o banco de dados
        db = await get_db()
        
        # Testa a conexão
        result = await db.table('renum_agent_teams').select('count(*)', count='exact').limit(1).execute()
        
        logger.info(f"Conexão com o banco de dados bem-sucedida. {result.count} equipes encontradas.")
        return True
    
    except Exception as e:
        logger.error(f"Erro ao conectar ao banco de dados: {str(e)}")
        return False


async def check_redis_connection():
    """
    Verifica a conexão com o Redis.
    
    Returns:
        bool: True se a conexão foi bem-sucedida, False caso contrário
    """
    try:
        import aioredis
        from dotenv import load_dotenv
        
        # Carrega as variáveis de ambiente
        load_dotenv()
        
        # Obtém a URL do Redis
        redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        
        # Conecta ao Redis
        redis = await aioredis.from_url(redis_url)
        
        # Testa a conexão
        await redis.set("test_key", "test_value")
        value = await redis.get("test_key")
        await redis.delete("test_key")
        
        if value == b"test_value":
            logger.info("Conexão com o Redis bem-sucedida")
            return True
        else:
            logger.error("Erro ao testar a conexão com o Redis")
            return False
    
    except Exception as e:
        logger.error(f"Erro ao conectar ao Redis: {str(e)}")
        return False


async def check_suna_api():
    """
    Verifica a conexão com a API do Suna Core.
    
    Returns:
        bool: True se a conexão foi bem-sucedida, False caso contrário
    """
    try:
        import aiohttp
        from dotenv import load_dotenv
        
        # Carrega as variáveis de ambiente
        load_dotenv()
        
        # Obtém a URL e a API key do Suna Core
        suna_api_url = os.environ.get("SUNA_API_URL")
        suna_api_key = os.environ.get("SUNA_API_KEY")
        
        if not suna_api_url:
            logger.error("Variável de ambiente SUNA_API_URL não definida")
            return False
        
        # Cria a sessão HTTP
        async with aiohttp.ClientSession() as session:
            # Testa a conexão
            headers = {}
            if suna_api_key:
                headers["Authorization"] = f"Bearer {suna_api_key}"
            
            try:
                async with session.get(f"{suna_api_url}/health", headers=headers) as response:
                    if response.status == 200:
                        logger.info("Conexão com a API do Suna Core bem-sucedida")
                        return True
                    else:
                        logger.error(f"Erro ao conectar à API do Suna Core: {response.status}")
                        return False
            except aiohttp.ClientError as e:
                logger.error(f"Erro ao conectar à API do Suna Core: {str(e)}")
                return False
    
    except Exception as e:
        logger.error(f"Erro ao verificar a API do Suna Core: {str(e)}")
        return False


async def main():
    """
    Função principal.
    
    Returns:
        int: 0 se todos os testes passaram, 1 caso contrário
    """
    logger.info("Verificando a instalação e configuração do sistema...")
    
    # Verifica a versão do Python
    if not check_python_version():
        return 1
    
    # Verifica as dependências
    if not check_dependencies():
        return 1
    
    # Verifica o arquivo .env
    if not check_env_file():
        return 1
    
    # Verifica a conexão com o banco de dados
    if not await check_database_connection():
        return 1
    
    # Verifica a conexão com o Redis
    if not await check_redis_connection():
        return 1
    
    # Verifica a conexão com a API do Suna Core
    if not await check_suna_api():
        return 1
    
    logger.info("Todos os testes passaram! O sistema está configurado corretamente.")
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)