"""
Módulo que implementa o pool de conexões PostgreSQL para a Plataforma Renum.

Este módulo fornece uma interface para gerenciar conexões PostgreSQL de forma eficiente,
utilizando um pool de conexões para reutilização e melhor performance.
"""

import logging
import time
import asyncio
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager

import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import RealDictCursor

from app.core.config import settings
from app.utils.retry import retry

# Configurar logger
logger = logging.getLogger(__name__)

class PostgreSQLPool:
    """Gerenciador de pool de conexões PostgreSQL."""
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """Implementação de Singleton para o pool de conexões."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        """Inicializa o pool de conexões PostgreSQL."""
        self.db_url = settings.SUPABASE_DB_URL
        if not self.db_url:
            raise ValueError("SUPABASE_DB_URL não configurada nas variáveis de ambiente")
        
        # Configurações do pool
        self.min_conn = 1
        self.max_conn = 10
        self.pool = None
        self.active_connections = 0
        self.max_usage_count = 100  # Número máximo de usos de uma conexão antes de ser reciclada
        self.connection_usage = {}  # Contador de uso por conexão
        
        # Inicializar o pool
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Inicializa o pool de conexões."""
        try:
            logger.info("Inicializando pool de conexões PostgreSQL...")
            self.pool = ThreadedConnectionPool(
                self.min_conn,
                self.max_conn,
                self.db_url,
                cursor_factory=RealDictCursor
            )
            logger.info("Pool de conexões PostgreSQL inicializado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao inicializar pool de conexões PostgreSQL: {str(e)}")
            raise
    
    @retry(max_retries=3, delay=1.0, backoff_factor=2.0, exceptions=(Exception,))
    def get_connection(self):
        """Obtém uma conexão do pool.
        
        Returns:
            Conexão PostgreSQL.
        
        Raises:
            Exception: Se não for possível obter uma conexão.
        """
        try:
            conn = self.pool.getconn()
            self.active_connections += 1
            
            # Inicializar contador de uso para esta conexão se não existir
            conn_id = id(conn)
            if conn_id not in self.connection_usage:
                self.connection_usage[conn_id] = 0
            
            # Incrementar contador de uso
            self.connection_usage[conn_id] += 1
            
            # Se a conexão foi muito utilizada, reciclar
            if self.connection_usage[conn_id] >= self.max_usage_count:
                logger.info(f"Reciclando conexão após {self.connection_usage[conn_id]} usos")
                self.pool.putconn(conn, close=True)  # Fechar a conexão
                conn = self.pool.getconn()  # Obter uma nova
                self.connection_usage[conn_id] = 1  # Resetar contador
            
            logger.debug(f"Conexão obtida do pool. Conexões ativas: {self.active_connections}")
            return conn
        except Exception as e:
            logger.error(f"Erro ao obter conexão do pool: {str(e)}")
            raise
    
    def release_connection(self, conn):
        """Devolve uma conexão ao pool.
        
        Args:
            conn: Conexão PostgreSQL a ser devolvida.
        """
        try:
            self.pool.putconn(conn)
            self.active_connections -= 1
            logger.debug(f"Conexão devolvida ao pool. Conexões ativas: {self.active_connections}")
        except Exception as e:
            logger.error(f"Erro ao devolver conexão ao pool: {str(e)}")
    
    @asynccontextmanager
    async def connection(self):
        """Context manager assíncrono para obter e liberar conexões.
        
        Yields:
            Conexão PostgreSQL.
        """
        conn = None
        try:
            conn = self.get_connection()
            yield conn
        finally:
            if conn:
                self.release_connection(conn)
    
    @asynccontextmanager
    async def cursor(self):
        """Context manager assíncrono para obter e liberar cursores.
        
        Yields:
            Cursor PostgreSQL.
        """
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            yield cursor
        finally:
            if cursor:
                cursor.close()
            if conn:
                self.release_connection(conn)
    
    async def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Executa uma consulta SQL e retorna os resultados.
        
        Args:
            query: Consulta SQL a ser executada.
            params: Parâmetros para a consulta.
            
        Returns:
            Lista de dicionários com os resultados da consulta.
        """
        start_time = time.time()
        async with self.cursor() as cursor:
            try:
                cursor.execute(query, params or {})
                results = cursor.fetchall()
                elapsed_time = time.time() - start_time
                logger.debug(f"Query executada em {elapsed_time:.3f}s: {query}")
                return results
            except Exception as e:
                elapsed_time = time.time() - start_time
                logger.error(f"Erro ao executar query ({elapsed_time:.3f}s): {query}")
                logger.error(f"Erro: {str(e)}")
                raise
    
    async def execute_transaction(self, queries: List[Dict[str, Any]]) -> bool:
        """Executa múltiplas consultas em uma transação.
        
        Args:
            queries: Lista de dicionários com as consultas e parâmetros.
                Cada dicionário deve ter as chaves 'query' e 'params'.
                
        Returns:
            True se a transação foi concluída com sucesso, False caso contrário.
        """
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Iniciar transação
            cursor.execute("BEGIN")
            
            # Executar cada consulta
            for query_data in queries:
                query = query_data.get("query")
                params = query_data.get("params", {})
                cursor.execute(query, params)
            
            # Commit da transação
            conn.commit()
            return True
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Erro ao executar transação: {str(e)}")
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                self.release_connection(conn)
    
    def close(self):
        """Fecha o pool de conexões."""
        if self.pool:
            self.pool.closeall()
            logger.info("Pool de conexões PostgreSQL fechado")


# Instância global do pool de conexões PostgreSQL
pg_pool = PostgreSQLPool.get_instance()