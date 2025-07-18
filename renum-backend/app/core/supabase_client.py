"""
Módulo que implementa o cliente Supabase centralizado para a Plataforma Renum.

Este módulo fornece uma interface unificada para interagir com o Supabase,
incluindo acesso ao banco de dados, autenticação e armazenamento.
"""

import logging
from typing import Optional, Dict, Any, List, Union

from supabase import create_client, Client

from app.core.config import settings
from app.utils.retry import retry, async_retry

# Configurar logger
logger = logging.getLogger(__name__)

class SupabaseClient:
    """Cliente centralizado para o Supabase."""
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """Implementação de Singleton para o cliente Supabase."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        """Inicializa o cliente Supabase."""
        self.url = settings.SUPABASE_URL
        self.key = settings.SUPABASE_KEY
        self.service_key = settings.SUPABASE_SERVICE_KEY
        
        # Configurações de segurança e resiliência
        self.max_retries = 3
        self.retry_delay = 1  # segundos
        self.timeout = 30  # segundos
        
        # Cliente para API REST
        try:
            # Configurar cliente com opções de segurança
            self.client = create_client(
                self.url, 
                self.key
            )
            logger.info("Cliente Supabase inicializado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao inicializar cliente Supabase: {str(e)}")
            raise
        
        # Cliente com chave de serviço para operações administrativas
        try:
            # Configurar cliente admin com opções de segurança
            self.admin_client = create_client(
                self.url, 
                self.service_key
            )
            logger.info("Cliente Supabase Admin inicializado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao inicializar cliente Supabase Admin: {str(e)}")
            raise
    
    def get_client(self, use_admin: bool = False) -> Client:
        """Retorna o cliente Supabase apropriado.
        
        Args:
            use_admin: Se True, retorna o cliente com a chave de serviço.
                      Se False, retorna o cliente com a chave anônima.
        
        Returns:
            Cliente Supabase configurado.
        """
        return self.admin_client if use_admin else self.client
    
    @retry(max_retries=3, delay=1.0, backoff_factor=2.0, exceptions=(Exception,))
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None, use_admin: bool = False) -> List[Dict]:
        """Executa uma consulta SQL via API REST do Supabase.
        
        Args:
            query: Consulta SQL a ser executada.
            params: Parâmetros para a consulta.
            use_admin: Se True, usa o cliente com a chave de serviço.
        
        Returns:
            Resultado da consulta.
        """
        try:
            client = self.get_client(use_admin)
            result = client.rpc("exec_sql", {"sql": query}).execute()
            return result.data
        except Exception as e:
            logger.error(f"Erro ao executar consulta SQL: {str(e)}")
            raise
    
    def table(self, table_name: str, use_admin: bool = False):
        """Acessa uma tabela no Supabase.
        
        Args:
            table_name: Nome da tabela.
            use_admin: Se True, usa o cliente com a chave de serviço.
        
        Returns:
            Objeto para interagir com a tabela.
        """
        client = self.get_client(use_admin)
        return client.table(table_name)
    
    def from_(self, table_name: str, use_admin: bool = False):
        """Acessa uma tabela no Supabase (alias para table).
        
        Args:
            table_name: Nome da tabela.
            use_admin: Se True, usa o cliente com a chave de serviço.
        
        Returns:
            Objeto para interagir com a tabela.
        """
        client = self.get_client(use_admin)
        return client.from_(table_name)
    
    @retry(max_retries=3, delay=1.0, backoff_factor=2.0, exceptions=(Exception,))
    def create(self, table_name: str, data: Union[Dict, List[Dict]], use_admin: bool = False):
        """Cria um ou mais registros em uma tabela.
        
        Args:
            table_name: Nome da tabela.
            data: Dados a serem inseridos (dicionário ou lista de dicionários).
            use_admin: Se True, usa o cliente com a chave de serviço.
        
        Returns:
            Resultado da operação.
        """
        try:
            client = self.get_client(use_admin)
            return client.from_(table_name).insert(data).execute()
        except Exception as e:
            logger.error(f"Erro ao criar registro(s) na tabela {table_name}: {str(e)}")
            raise
    
    @retry(max_retries=3, delay=1.0, backoff_factor=2.0, exceptions=(Exception,))
    def read(self, table_name: str, columns: str = "*", filters: Optional[Dict] = None, limit: int = 100, use_admin: bool = False):
        """Lê registros de uma tabela.
        
        Args:
            table_name: Nome da tabela.
            columns: Colunas a serem retornadas.
            filters: Filtros a serem aplicados.
            limit: Limite de registros a serem retornados.
            use_admin: Se True, usa o cliente com a chave de serviço.
        
        Returns:
            Resultado da operação.
        """
        try:
            client = self.get_client(use_admin)
            query = client.from_(table_name).select(columns).limit(limit)
            
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            
            return query.execute()
        except Exception as e:
            logger.error(f"Erro ao ler registros da tabela {table_name}: {str(e)}")
            raise
    
    @retry(max_retries=3, delay=1.0, backoff_factor=2.0, exceptions=(Exception,))
    def update(self, table_name: str, data: Dict, filters: Dict, use_admin: bool = False):
        """Atualiza registros em uma tabela.
        
        Args:
            table_name: Nome da tabela.
            data: Dados a serem atualizados.
            filters: Filtros para identificar os registros a serem atualizados.
            use_admin: Se True, usa o cliente com a chave de serviço.
        
        Returns:
            Resultado da operação.
        """
        try:
            client = self.get_client(use_admin)
            query = client.from_(table_name).update(data)
            
            for key, value in filters.items():
                query = query.eq(key, value)
            
            return query.execute()
        except Exception as e:
            logger.error(f"Erro ao atualizar registros na tabela {table_name}: {str(e)}")
            raise
    
    @retry(max_retries=3, delay=1.0, backoff_factor=2.0, exceptions=(Exception,))
    def delete(self, table_name: str, filters: Dict, use_admin: bool = False):
        """Exclui registros de uma tabela.
        
        Args:
            table_name: Nome da tabela.
            filters: Filtros para identificar os registros a serem excluídos.
            use_admin: Se True, usa o cliente com a chave de serviço.
        
        Returns:
            Resultado da operação.
        """
        try:
            client = self.get_client(use_admin)
            query = client.from_(table_name).delete()
            
            for key, value in filters.items():
                query = query.eq(key, value)
            
            return query.execute()
        except Exception as e:
            logger.error(f"Erro ao excluir registros da tabela {table_name}: {str(e)}")
            raise


# Instância global do cliente Supabase
supabase = SupabaseClient.get_instance()