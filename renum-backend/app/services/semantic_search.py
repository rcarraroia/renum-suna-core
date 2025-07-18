"""
Módulo que implementa o serviço de busca semântica para o módulo RAG da Plataforma Renum.

Este módulo fornece funcionalidades para realizar buscas semânticas em documentos
usando embeddings e o banco de dados vetorial do Supabase.
"""

import logging
from typing import List, Dict, Any, Optional, Union, Tuple
from uuid import UUID

from app.db.pg_pool import pg_pool
from app.models.rag import DocumentChunk, Document
from app.repositories.rag import document_chunk_repository, document_repository
from app.services.embedding import embedding_service

# Configurar logger
logger = logging.getLogger(__name__)

class SemanticSearchService:
    """Serviço para realizar buscas semânticas no módulo RAG."""
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """Implementação de Singleton para o serviço de busca semântica."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        """Inicializa o serviço de busca semântica."""
        self.default_similarity_threshold = 0.7
        self.default_max_results = 5
    
    async def search_chunks(
        self,
        query: str,
        collection_ids: Optional[List[Union[str, UUID]]] = None,
        similarity_threshold: float = None,
        max_results: int = None
    ) -> List[Dict[str, Any]]:
        """Busca chunks relevantes para uma consulta.
        
        Args:
            query: Texto da consulta.
            collection_ids: Lista de IDs de coleções para filtrar a busca.
            similarity_threshold: Limiar mínimo de similaridade (0-1).
            max_results: Número máximo de resultados.
            
        Returns:
            Lista de chunks relevantes com metadados e pontuação de similaridade.
        """
        try:
            # Usar valores padrão se não fornecidos
            similarity_threshold = similarity_threshold or self.default_similarity_threshold
            max_results = max_results or self.default_max_results
            
            # Gerar embedding para a consulta
            query_embedding = await embedding_service.generate_embedding(query)
            
            # Converter collection_ids para strings se fornecido
            if collection_ids:
                collection_ids = [str(cid) for cid in collection_ids]
            
            # Executar a busca usando a função SQL personalizada
            async with pg_pool.cursor() as cursor:
                sql = """
                SELECT * FROM search_embeddings($1, $2, $3, $4)
                """
                await cursor.execute(sql, (query_embedding, similarity_threshold, max_results, collection_ids))
                results = await cursor.fetchall()
            
            # Processar os resultados
            processed_results = []
            for result in results:
                processed_result = dict(result)
                # Adicionar informações adicionais se necessário
                processed_results.append(processed_result)
            
            return processed_results
        except Exception as e:
            logger.error(f"Erro ao buscar chunks: {str(e)}")
            raise
    
    async def search_documents(
        self,
        query: str,
        collection_ids: Optional[List[Union[str, UUID]]] = None,
        similarity_threshold: float = None,
        max_results: int = None
    ) -> List[Dict[str, Any]]:
        """Busca documentos relevantes para uma consulta.
        
        Args:
            query: Texto da consulta.
            collection_ids: Lista de IDs de coleções para filtrar a busca.
            similarity_threshold: Limiar mínimo de similaridade (0-1).
            max_results: Número máximo de resultados.
            
        Returns:
            Lista de documentos relevantes com pontuação de similaridade média.
        """
        try:
            # Usar valores padrão se não fornecidos
            similarity_threshold = similarity_threshold or self.default_similarity_threshold
            max_results = max_results or self.default_max_results
            
            # Gerar embedding para a consulta
            query_embedding = await embedding_service.generate_embedding(query)
            
            # Converter collection_ids para strings se fornecido
            if collection_ids:
                collection_ids = [str(cid) for cid in collection_ids]
            
            # Executar a busca usando a função SQL personalizada
            async with pg_pool.cursor() as cursor:
                sql = """
                SELECT * FROM search_similar_documents($1, $2, $3, $4)
                """
                await cursor.execute(sql, (query_embedding, similarity_threshold, max_results, collection_ids))
                results = await cursor.fetchall()
            
            # Processar os resultados
            processed_results = []
            for result in results:
                processed_result = dict(result)
                # Adicionar informações adicionais se necessário
                processed_results.append(processed_result)
            
            return processed_results
        except Exception as e:
            logger.error(f"Erro ao buscar documentos: {str(e)}")
            raise
    
    async def generate_context(
        self,
        query: str,
        collection_ids: Optional[List[Union[str, UUID]]] = None,
        max_tokens: int = 1500,
        similarity_threshold: float = None
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """Gera um contexto para uma consulta combinando chunks relevantes.
        
        Args:
            query: Texto da consulta.
            collection_ids: Lista de IDs de coleções para filtrar a busca.
            max_tokens: Número máximo de tokens no contexto.
            similarity_threshold: Limiar mínimo de similaridade (0-1).
            
        Returns:
            Tupla com o contexto gerado e a lista de chunks usados.
        """
        try:
            # Usar valor padrão se não fornecido
            similarity_threshold = similarity_threshold or self.default_similarity_threshold
            
            # Buscar chunks relevantes
            chunks = await self.search_chunks(
                query=query,
                collection_ids=collection_ids,
                similarity_threshold=similarity_threshold,
                max_results=10  # Buscar mais chunks do que o necessário para ter opções
            )
            
            # Ordenar por similaridade (do mais similar para o menos similar)
            chunks.sort(key=lambda x: x["similarity"], reverse=True)
            
            # Estimar o número de tokens (aproximadamente 4 caracteres por token)
            context_chunks = []
            context_text = ""
            total_tokens = 0
            
            for chunk in chunks:
                # Estimar tokens no chunk
                chunk_tokens = len(chunk["content"]) // 4
                
                # Se adicionar este chunk exceder o limite, parar
                if total_tokens + chunk_tokens > max_tokens:
                    break
                
                # Adicionar chunk ao contexto
                if context_text:
                    context_text += "\n\n"
                context_text += chunk["content"]
                total_tokens += chunk_tokens
                context_chunks.append(chunk)
            
            return context_text, context_chunks
        except Exception as e:
            logger.error(f"Erro ao gerar contexto: {str(e)}")
            raise
    
    async def track_usage(
        self,
        document_id: Union[str, UUID],
        chunk_id: Optional[Union[str, UUID]] = None,
        agent_id: Optional[Union[str, UUID]] = None,
        client_id: Union[str, UUID] = None
    ) -> None:
        """Registra o uso de um documento ou chunk.
        
        Args:
            document_id: ID do documento.
            chunk_id: ID do chunk (opcional).
            agent_id: ID do agente que utilizou o documento (opcional).
            client_id: ID do cliente.
        """
        try:
            # Implementar o registro de uso
            # Esta funcionalidade será implementada posteriormente
            pass
        except Exception as e:
            logger.error(f"Erro ao registrar uso: {str(e)}")
            # Não propagar a exceção para não interromper o fluxo principal


# Instância global do serviço de busca semântica
semantic_search_service = SemanticSearchService.get_instance()