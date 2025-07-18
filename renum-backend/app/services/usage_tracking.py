"""
Módulo que implementa o serviço de rastreamento de uso para o módulo RAG da Plataforma Renum.

Este módulo fornece funcionalidades para registrar o uso de documentos e chunks,
bem como coletar feedback sobre a relevância dos resultados de busca.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from uuid import UUID

from app.db.pg_pool import pg_pool
from app.models.rag import DocumentUsageStats, RetrievalFeedback

# Configurar logger
logger = logging.getLogger(__name__)

class UsageTrackingService:
    """Serviço para rastreamento de uso no módulo RAG."""
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """Implementação de Singleton para o serviço de rastreamento de uso."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        """Inicializa o serviço de rastreamento de uso."""
        logger.info("Serviço de rastreamento de uso inicializado")
    
    async def track_document_usage(
        self,
        document_id: Union[str, UUID],
        client_id: Union[str, UUID],
        chunk_id: Optional[Union[str, UUID]] = None,
        agent_id: Optional[Union[str, UUID]] = None
    ) -> None:
        """Registra o uso de um documento ou chunk.
        
        Args:
            document_id: ID do documento.
            client_id: ID do cliente.
            chunk_id: ID do chunk (opcional).
            agent_id: ID do agente que utilizou o documento (opcional).
        """
        try:
            # Converter IDs para strings
            document_id_str = str(document_id)
            client_id_str = str(client_id)
            chunk_id_str = str(chunk_id) if chunk_id else None
            agent_id_str = str(agent_id) if agent_id else None
            
            # Verificar se já existe um registro para esta combinação
            async with pg_pool.cursor() as cursor:
                query = """
                SELECT id, usage_count
                FROM document_usage_stats
                WHERE document_id = %s
                AND client_id = %s
                """
                params = [document_id_str, client_id_str]
                
                if chunk_id:
                    query += " AND chunk_id = %s"
                    params.append(chunk_id_str)
                else:
                    query += " AND chunk_id IS NULL"
                
                if agent_id:
                    query += " AND agent_id = %s"
                    params.append(agent_id_str)
                else:
                    query += " AND agent_id IS NULL"
                
                await cursor.execute(query, params)
                result = await cursor.fetchone()
                
                now = datetime.now().isoformat()
                
                if result:
                    # Atualizar registro existente
                    usage_id = result["id"]
                    usage_count = result["usage_count"] + 1
                    
                    update_query = """
                    UPDATE document_usage_stats
                    SET usage_count = %s, last_used_at = %s
                    WHERE id = %s
                    """
                    await cursor.execute(update_query, [usage_count, now, usage_id])
                else:
                    # Criar novo registro
                    insert_query = """
                    INSERT INTO document_usage_stats
                    (document_id, chunk_id, agent_id, client_id, usage_count, last_used_at, first_used_at)
                    VALUES (%s, %s, %s, %s, 1, %s, %s)
                    """
                    await cursor.execute(insert_query, [
                        document_id_str, chunk_id_str, agent_id_str, client_id_str, now, now
                    ])
                
                # Commit da transação
                await cursor.execute("COMMIT")
                
                logger.debug(f"Uso registrado para documento {document_id_str}")
        except Exception as e:
            logger.error(f"Erro ao registrar uso de documento: {str(e)}")
            # Não propagar a exceção para não interromper o fluxo principal
    
    async def track_multiple_documents_usage(
        self,
        document_ids: List[Union[str, UUID]],
        client_id: Union[str, UUID],
        chunk_ids: Optional[List[Union[str, UUID]]] = None,
        agent_id: Optional[Union[str, UUID]] = None
    ) -> None:
        """Registra o uso de múltiplos documentos ou chunks.
        
        Args:
            document_ids: Lista de IDs de documentos.
            client_id: ID do cliente.
            chunk_ids: Lista de IDs de chunks (opcional).
            agent_id: ID do agente que utilizou os documentos (opcional).
        """
        try:
            # Verificar se chunk_ids tem o mesmo tamanho que document_ids
            if chunk_ids and len(chunk_ids) != len(document_ids):
                raise ValueError("chunk_ids deve ter o mesmo tamanho que document_ids")
            
            # Registrar uso para cada documento
            for i, doc_id in enumerate(document_ids):
                chunk_id = chunk_ids[i] if chunk_ids else None
                await self.track_document_usage(doc_id, client_id, chunk_id, agent_id)
        except Exception as e:
            logger.error(f"Erro ao registrar uso de múltiplos documentos: {str(e)}")
    
    async def record_retrieval_feedback(
        self,
        document_id: Union[str, UUID],
        chunk_id: Union[str, UUID],
        client_id: Union[str, UUID],
        query: str,
        relevance_score: float,
        agent_id: Optional[Union[str, UUID]] = None,
        feedback_source: str = "user"
    ) -> None:
        """Registra feedback sobre a relevância de um resultado de busca.
        
        Args:
            document_id: ID do documento.
            chunk_id: ID do chunk.
            client_id: ID do cliente.
            query: Consulta que gerou o resultado.
            relevance_score: Pontuação de relevância (0-1).
            agent_id: ID do agente que utilizou o documento (opcional).
            feedback_source: Fonte do feedback (user, system, agent).
        """
        try:
            # Validar pontuação de relevância
            if relevance_score < 0 or relevance_score > 1:
                raise ValueError("Pontuação de relevância deve estar entre 0 e 1")
            
            # Converter IDs para strings
            document_id_str = str(document_id)
            chunk_id_str = str(chunk_id)
            client_id_str = str(client_id)
            agent_id_str = str(agent_id) if agent_id else None
            
            # Criar registro de feedback
            async with pg_pool.cursor() as cursor:
                insert_query = """
                INSERT INTO retrieval_feedback
                (document_id, chunk_id, client_id, agent_id, query, relevance_score, feedback_source, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                now = datetime.now().isoformat()
                await cursor.execute(insert_query, [
                    document_id_str, chunk_id_str, client_id_str, agent_id_str,
                    query, relevance_score, feedback_source, now
                ])
                
                # Commit da transação
                await cursor.execute("COMMIT")
                
                logger.debug(f"Feedback registrado para chunk {chunk_id_str}")
        except Exception as e:
            logger.error(f"Erro ao registrar feedback de recuperação: {str(e)}")
    
    async def get_document_usage_stats(
        self,
        document_id: Union[str, UUID]
    ) -> Dict[str, Any]:
        """Obtém estatísticas de uso de um documento.
        
        Args:
            document_id: ID do documento.
            
        Returns:
            Dicionário com estatísticas de uso.
        """
        try:
            document_id_str = str(document_id)
            
            async with pg_pool.cursor() as cursor:
                # Estatísticas gerais do documento
                query = """
                SELECT SUM(usage_count) as total_usage,
                       MIN(first_used_at) as first_used_at,
                       MAX(last_used_at) as last_used_at,
                       COUNT(DISTINCT client_id) as unique_clients,
                       COUNT(DISTINCT agent_id) as unique_agents
                FROM document_usage_stats
                WHERE document_id = %s
                """
                await cursor.execute(query, [document_id_str])
                general_stats = await cursor.fetchone()
                
                # Estatísticas por chunk
                chunk_query = """
                SELECT chunk_id, SUM(usage_count) as usage_count
                FROM document_usage_stats
                WHERE document_id = %s AND chunk_id IS NOT NULL
                GROUP BY chunk_id
                ORDER BY usage_count DESC
                LIMIT 10
                """
                await cursor.execute(chunk_query, [document_id_str])
                chunk_stats = await cursor.fetchall()
                
                # Estatísticas por cliente
                client_query = """
                SELECT client_id, SUM(usage_count) as usage_count
                FROM document_usage_stats
                WHERE document_id = %s
                GROUP BY client_id
                ORDER BY usage_count DESC
                LIMIT 10
                """
                await cursor.execute(client_query, [document_id_str])
                client_stats = await cursor.fetchall()
                
                return {
                    "document_id": document_id_str,
                    "general_stats": dict(general_stats) if general_stats else {},
                    "chunk_stats": [dict(stat) for stat in chunk_stats],
                    "client_stats": [dict(stat) for stat in client_stats]
                }
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas de uso do documento: {str(e)}")
            return {
                "document_id": str(document_id),
                "error": str(e)
            }
    
    async def get_client_usage_stats(
        self,
        client_id: Union[str, UUID]
    ) -> Dict[str, Any]:
        """Obtém estatísticas de uso de um cliente.
        
        Args:
            client_id: ID do cliente.
            
        Returns:
            Dicionário com estatísticas de uso.
        """
        try:
            client_id_str = str(client_id)
            
            async with pg_pool.cursor() as cursor:
                # Estatísticas gerais do cliente
                query = """
                SELECT SUM(usage_count) as total_usage,
                       MIN(first_used_at) as first_used_at,
                       MAX(last_used_at) as last_used_at,
                       COUNT(DISTINCT document_id) as unique_documents,
                       COUNT(DISTINCT agent_id) as unique_agents
                FROM document_usage_stats
                WHERE client_id = %s
                """
                await cursor.execute(query, [client_id_str])
                general_stats = await cursor.fetchone()
                
                # Documentos mais usados
                doc_query = """
                SELECT document_id, SUM(usage_count) as usage_count
                FROM document_usage_stats
                WHERE client_id = %s
                GROUP BY document_id
                ORDER BY usage_count DESC
                LIMIT 10
                """
                await cursor.execute(doc_query, [client_id_str])
                doc_stats = await cursor.fetchall()
                
                # Agentes mais ativos
                agent_query = """
                SELECT agent_id, SUM(usage_count) as usage_count
                FROM document_usage_stats
                WHERE client_id = %s AND agent_id IS NOT NULL
                GROUP BY agent_id
                ORDER BY usage_count DESC
                LIMIT 10
                """
                await cursor.execute(agent_query, [client_id_str])
                agent_stats = await cursor.fetchall()
                
                return {
                    "client_id": client_id_str,
                    "general_stats": dict(general_stats) if general_stats else {},
                    "document_stats": [dict(stat) for stat in doc_stats],
                    "agent_stats": [dict(stat) for stat in agent_stats]
                }
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas de uso do cliente: {str(e)}")
            return {
                "client_id": str(client_id),
                "error": str(e)
            }


# Instância global do serviço de rastreamento de uso
usage_tracking_service = UsageTrackingService.get_instance()