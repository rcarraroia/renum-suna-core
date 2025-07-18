"""
Módulo que implementa os repositórios para o módulo RAG da Plataforma Renum.

Este módulo contém as implementações específicas do padrão Repository para as
entidades do módulo RAG, como bases de conhecimento, coleções, documentos e chunks.
"""

import logging
from typing import Optional, Dict, Any, List, Union
from uuid import UUID

from app.core.supabase_client import supabase
from app.db.pg_pool import pg_pool
from app.models.rag import (
    KnowledgeBase,
    KnowledgeCollection,
    Document,
    DocumentChunk,
    DocumentVersion,
    DocumentUsageStats,
    RetrievalFeedback,
    ProcessingJob
)
from app.repositories.base import SupabaseRepository, PaginatedResult

# Configurar logger
logger = logging.getLogger(__name__)


class KnowledgeBaseRepository(SupabaseRepository[KnowledgeBase]):
    """Repositório para bases de conhecimento."""
    
    def __init__(self):
        """Inicializa o repositório."""
        super().__init__(supabase, "knowledge_bases")
    
    def _map_to_entity(self, data: Dict[str, Any]) -> KnowledgeBase:
        """Converte um dicionário de dados em uma entidade KnowledgeBase.
        
        Args:
            data: Dicionário com os dados da base de conhecimento.
            
        Returns:
            Entidade KnowledgeBase correspondente aos dados.
        """
        return KnowledgeBase(**data)
    
    def _map_to_dict(self, entity: KnowledgeBase) -> Dict[str, Any]:
        """Converte uma entidade KnowledgeBase em um dicionário de dados.
        
        Args:
            entity: Entidade KnowledgeBase a ser convertida.
            
        Returns:
            Dicionário com os dados da base de conhecimento.
        """
        return entity.model_dump(exclude_unset=True)
    
    async def get_by_client_id(self, client_id: Union[str, UUID], limit: int = 100, offset: int = 0) -> List[KnowledgeBase]:
        """Recupera bases de conhecimento de um cliente específico.
        
        Args:
            client_id: ID do cliente.
            limit: Número máximo de bases a serem retornadas.
            offset: Número de bases a serem puladas.
            
        Returns:
            Lista de bases de conhecimento do cliente.
        """
        result = await self.supabase.from_(self.table_name).select("*").eq("client_id", str(client_id)).limit(limit).offset(offset).execute()
        return [self._map_to_entity(item) for item in result.data]
    
    async def count_by_client_id(self, client_id: Union[str, UUID]) -> int:
        """Conta o número de bases de conhecimento de um cliente específico.
        
        Args:
            client_id: ID do cliente.
            
        Returns:
            Número de bases de conhecimento do cliente.
        """
        result = await self.supabase.from_(self.table_name).select("id", count="exact").eq("client_id", str(client_id)).execute()
        return result.count if hasattr(result, "count") else 0
    
    async def get_paginated_by_client_id(
        self, 
        client_id: Union[str, UUID], 
        page: int = 1, 
        page_size: int = 10
    ) -> PaginatedResult[KnowledgeBase]:
        """Recupera bases de conhecimento de um cliente específico com paginação.
        
        Args:
            client_id: ID do cliente.
            page: Número da página (começando em 1).
            page_size: Tamanho da página.
            
        Returns:
            Resultado paginado com bases de conhecimento do cliente.
        """
        offset = (page - 1) * page_size
        items = await self.get_by_client_id(client_id, limit=page_size, offset=offset)
        total = await self.count_by_client_id(client_id)
        return PaginatedResult(items=items, total=total, page=page, page_size=page_size)


class KnowledgeCollectionRepository(SupabaseRepository[KnowledgeCollection]):
    """Repositório para coleções de conhecimento."""
    
    def __init__(self):
        """Inicializa o repositório."""
        super().__init__(supabase, "knowledge_collections")
    
    def _map_to_entity(self, data: Dict[str, Any]) -> KnowledgeCollection:
        """Converte um dicionário de dados em uma entidade KnowledgeCollection.
        
        Args:
            data: Dicionário com os dados da coleção.
            
        Returns:
            Entidade KnowledgeCollection correspondente aos dados.
        """
        return KnowledgeCollection(**data)
    
    def _map_to_dict(self, entity: KnowledgeCollection) -> Dict[str, Any]:
        """Converte uma entidade KnowledgeCollection em um dicionário de dados.
        
        Args:
            entity: Entidade KnowledgeCollection a ser convertida.
            
        Returns:
            Dicionário com os dados da coleção.
        """
        return entity.model_dump(exclude_unset=True)
    
    async def get_by_knowledge_base_id(
        self, 
        knowledge_base_id: Union[str, UUID], 
        limit: int = 100, 
        offset: int = 0
    ) -> List[KnowledgeCollection]:
        """Recupera coleções de uma base de conhecimento específica.
        
        Args:
            knowledge_base_id: ID da base de conhecimento.
            limit: Número máximo de coleções a serem retornadas.
            offset: Número de coleções a serem puladas.
            
        Returns:
            Lista de coleções da base de conhecimento.
        """
        result = await self.supabase.from_(self.table_name).select("*").eq("knowledge_base_id", str(knowledge_base_id)).limit(limit).offset(offset).execute()
        return [self._map_to_entity(item) for item in result.data]
    
    async def count_by_knowledge_base_id(self, knowledge_base_id: Union[str, UUID]) -> int:
        """Conta o número de coleções de uma base de conhecimento específica.
        
        Args:
            knowledge_base_id: ID da base de conhecimento.
            
        Returns:
            Número de coleções da base de conhecimento.
        """
        result = await self.supabase.from_(self.table_name).select("id", count="exact").eq("knowledge_base_id", str(knowledge_base_id)).execute()
        return result.count if hasattr(result, "count") else 0


class DocumentRepository(SupabaseRepository[Document]):
    """Repositório para documentos."""
    
    def __init__(self):
        """Inicializa o repositório."""
        super().__init__(supabase, "documents")
    
    def _map_to_entity(self, data: Dict[str, Any]) -> Document:
        """Converte um dicionário de dados em uma entidade Document.
        
        Args:
            data: Dicionário com os dados do documento.
            
        Returns:
            Entidade Document correspondente aos dados.
        """
        return Document(**data)
    
    def _map_to_dict(self, entity: Document) -> Dict[str, Any]:
        """Converte uma entidade Document em um dicionário de dados.
        
        Args:
            entity: Entidade Document a ser convertida.
            
        Returns:
            Dicionário com os dados do documento.
        """
        return entity.model_dump(exclude_unset=True)
    
    async def get_by_collection_id(
        self, 
        collection_id: Union[str, UUID], 
        limit: int = 100, 
        offset: int = 0
    ) -> List[Document]:
        """Recupera documentos de uma coleção específica.
        
        Args:
            collection_id: ID da coleção.
            limit: Número máximo de documentos a serem retornados.
            offset: Número de documentos a serem pulados.
            
        Returns:
            Lista de documentos da coleção.
        """
        result = await self.supabase.from_(self.table_name).select("*").eq("collection_id", str(collection_id)).limit(limit).offset(offset).execute()
        return [self._map_to_entity(item) for item in result.data]
    
    async def count_by_collection_id(self, collection_id: Union[str, UUID]) -> int:
        """Conta o número de documentos de uma coleção específica.
        
        Args:
            collection_id: ID da coleção.
            
        Returns:
            Número de documentos da coleção.
        """
        result = await self.supabase.from_(self.table_name).select("id", count="exact").eq("collection_id", str(collection_id)).execute()
        return result.count if hasattr(result, "count") else 0
    
    async def update_status(self, document_id: Union[str, UUID], status: str) -> Document:
        """Atualiza o status de um documento.
        
        Args:
            document_id: ID do documento.
            status: Novo status do documento.
            
        Returns:
            Documento atualizado.
        """
        result = await self.supabase.from_(self.table_name).update({"status": status}).eq("id", str(document_id)).execute()
        if result.data and len(result.data) > 0:
            return self._map_to_entity(result.data[0])
        raise ValueError(f"Falha ao atualizar status do documento com ID {document_id}")


class DocumentChunkRepository(SupabaseRepository[DocumentChunk]):
    """Repositório para chunks de documentos."""
    
    def __init__(self):
        """Inicializa o repositório."""
        super().__init__(supabase, "document_chunks")
    
    def _map_to_entity(self, data: Dict[str, Any]) -> DocumentChunk:
        """Converte um dicionário de dados em uma entidade DocumentChunk.
        
        Args:
            data: Dicionário com os dados do chunk.
            
        Returns:
            Entidade DocumentChunk correspondente aos dados.
        """
        return DocumentChunk(**data)
    
    def _map_to_dict(self, entity: DocumentChunk) -> Dict[str, Any]:
        """Converte uma entidade DocumentChunk em um dicionário de dados.
        
        Args:
            entity: Entidade DocumentChunk a ser convertida.
            
        Returns:
            Dicionário com os dados do chunk.
        """
        return entity.model_dump(exclude_unset=True)
    
    async def get_by_document_id(
        self, 
        document_id: Union[str, UUID], 
        limit: int = 100, 
        offset: int = 0
    ) -> List[DocumentChunk]:
        """Recupera chunks de um documento específico.
        
        Args:
            document_id: ID do documento.
            limit: Número máximo de chunks a serem retornados.
            offset: Número de chunks a serem pulados.
            
        Returns:
            Lista de chunks do documento.
        """
        result = await self.supabase.from_(self.table_name).select("*").eq("document_id", str(document_id)).limit(limit).offset(offset).execute()
        return [self._map_to_entity(item) for item in result.data]
    
    async def count_by_document_id(self, document_id: Union[str, UUID]) -> int:
        """Conta o número de chunks de um documento específico.
        
        Args:
            document_id: ID do documento.
            
        Returns:
            Número de chunks do documento.
        """
        result = await self.supabase.from_(self.table_name).select("id", count="exact").eq("document_id", str(document_id)).execute()
        return result.count if hasattr(result, "count") else 0
    
    async def create_batch(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """Cria múltiplos chunks em lote.
        
        Args:
            chunks: Lista de chunks a serem criados.
            
        Returns:
            Lista de chunks criados.
        """
        data = [self._map_to_dict(chunk) for chunk in chunks]
        result = await self.supabase.from_(self.table_name).insert(data).execute()
        if result.data:
            return [self._map_to_entity(item) for item in result.data]
        raise ValueError("Falha ao criar chunks em lote")
    
    async def search_by_similarity(
        self,
        query_embedding: List[float],
        collection_ids: Optional[List[Union[str, UUID]]] = None,
        limit: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Busca chunks por similaridade de embedding.
        
        Args:
            query_embedding: Vetor de embedding da consulta.
            collection_ids: Lista de IDs de coleções para filtrar a busca.
            limit: Número máximo de resultados.
            similarity_threshold: Limiar mínimo de similaridade (0-1).
            
        Returns:
            Lista de chunks ordenados por similaridade.
        """
        # Esta função requer uma função SQL personalizada no Supabase
        # que implementa a busca por similaridade usando a extensão pgvector
        try:
            async with pg_pool.cursor() as cursor:
                query = """
                SELECT c.*, d.name as document_name, d.collection_id,
                       1 - (c.embedding <=> %s::vector) as similarity
                FROM document_chunks c
                JOIN documents d ON c.document_id = d.id
                """
                
                params = [query_embedding]
                
                if collection_ids:
                    collection_ids_str = ",".join([f"'{str(cid)}'" for cid in collection_ids])
                    query += f" WHERE d.collection_id IN ({collection_ids_str})"
                
                query += f" WHERE 1 - (c.embedding <=> %s::vector) > {similarity_threshold}"
                query += " ORDER BY similarity DESC"
                query += f" LIMIT {limit}"
                
                await cursor.execute(query, params)
                results = await cursor.fetchall()
                return results
        except Exception as e:
            logger.error(f"Erro ao buscar chunks por similaridade: {str(e)}")
            raise


# Instâncias globais dos repositórios
knowledge_base_repository = KnowledgeBaseRepository()
knowledge_collection_repository = KnowledgeCollectionRepository()
document_repository = DocumentRepository()
document_chunk_repository = DocumentChunkRepository()