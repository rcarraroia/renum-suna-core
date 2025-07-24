#!/usr/bin/env python
"""
Script para executar o servidor.

Este script inicia o servidor FastAPI com o Uvicorn.
"""

import os
import sys
import logging
import uvicorn
from dotenv import load_dotenv

# Configura o logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """
    Função principal.
    
    Returns:
        int: 0 se o servidor foi iniciado com sucesso, 1 caso contrário
    """
    try:
        # Carrega as variáveis de ambiente
        load_dotenv()
        
        # Obtém as configurações
        host = os.environ.get("HOST", "0.0.0.0")
        port = int(os.environ.get("PORT", "9000"))
        reload = os.environ.get("ENV", "development").lower() == "development"
        
        logger.info(f"Iniciando o servidor em {host}:{port}...")
        logger.info(f"Ambiente: {os.environ.get('ENV', 'development')}")
        logger.info(f"Reload: {reload}")
        
        # Inicia o servidor
        uvicorn.run(
            "app.main:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )
        
        return 0
    
    except Exception as e:
        logger.error(f"Erro ao iniciar o servidor: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())