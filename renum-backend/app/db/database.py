"""
Módulo de conexão com o banco de dados.

Este módulo fornece funcionalidades para conexão com o banco de dados Supabase.
"""

import logging
from typing import Optional
import os
from supabase import create_client, Client

logger = logging.getLogger(__name__)


class Database:
    """Classe para gerenciamento de conexão com o banco de dados Supabase."""
    
    def __init__(self, url: str, key: str):
        """
        Inicializa a conexão com o banco de dados.
        
        Args:
            url: URL do Supabase
            key: Chave de API do Supabase
        """
        self.url = url
        self.key = key
        self._client: Optional[Client] = None
    
    @property
    async def client(self) -> Client:
        """
        Obtém o cliente Supabase, inicializando se necessário.
        
        Returns:
            Cliente Supabase
        """
        if self._client is None:
            self._client = create_client(self.url, self.key)
            logger.info("Initialized Supabase client")
        
        return self._client
    
    def table(self, table_name: str):
        """
        Obtém uma referência para uma tabela.
        
        Args:
            table_name: Nome da tabela
            
        Returns:
            Referência para a tabela
        """
        return self._client.table(table_name)
    
    async def close(self):
        """Fecha a conexão com o banco de dados."""
        self._client = None
        logger.info("Closed Supabase client")


# Singleton para acesso global
_db_instance: Optional[Database] = None


def get_db_instance() -> Database:
    """
    Obtém a instância global do banco de dados.
    
    Returns:
        Instância do banco de dados
    """
    global _db_instance
    
    if _db_instance is None:
        # Obtém as credenciais do ambiente
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")
        
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY environment variables are required")
        
        _db_instance = Database(url, key)
    
    return _db_instance


async def get_db() -> Database:
    """
    Obtém a instância do banco de dados para uso em dependências do FastAPI.
    
    Returns:
        Instância do banco de dados
    """
    db = get_db_instance()
    # Garante que o cliente está inicializado
    await db.client
    return db