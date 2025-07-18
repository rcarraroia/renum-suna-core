"""
Módulo que implementa os endpoints REST para o módulo RAG da Plataforma Renum.

Este módulo contém os endpoints para gerenciar bases de conhecimento, coleções,
documentos e realizar buscas semânticas.
"""

import logging
import time
from typing import List, Dict, Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status

from app.api.schemas.rag import (
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
    KnowledgeBaseResponse,
    KnowledgeCollectionCreate,
    KnowledgeCollectionUpdate,
    KnowledgeCollectionResponse,
    DocumentCreate,
    DocumentUpdate,
    DocumentResponse,
    DocumentChunkResponse,
    SemanticSearchRequest,
    SemanticSearchResponse,
    ContextGenerationRequest,
    ContextGenerationResponse,
    ProcessDocumentRequest,
    ProcessDocumentResponse,
    UsageStatsResponse,
    PaginatedResponse
)
from app.models.rag import (
    KnowledgeBase,
    KnowledgeCollection,
    Document,
    DocumentChunk
)
from app.repositories.rag import (
    knowledge_base_repository,
    knowledge_collection_repository,
    document_repository,
    document_chunk_repository
)
from app.services.semantic_search import semantic_search_service
from app.services.embedding import embedding_service
from app.services.usage_tracking import usage_tracking_service

# Configurar logger
logger = logging.getLogger(__name__)

# Criar router
router = APIRouter(
    prefix="/rag",
    tags=["RAG"],
    responses={404: {"description": "Item não encontrado"}}
)


# Endpoints para KnowledgeBase

@router.post("/knowledge-bases", response_model=KnowledgeBaseResponse, status_code=status.HTTP_201_CREATED)
async def create_knowledge_base(knowledge_base: KnowledgeBaseCreate):
    """Cria uma nova base de conhecimento."""
    try:
        # Criar objeto KnowledgeBase
        kb = KnowledgeBase(
            name=knowledge_base.name,
            description=knowledge_base.description,
            client_id=knowledge_base.client_id
        )
        
        # Salvar no repositório
        created_kb = await knowledge_base_repository.create(kb)
        
        return created_kb
    except Exception as e:
        logger.error(f"Erro ao criar base de conhecimento: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar base de conhecimento: {str(e)}"
        )


@router.get("/knowledge-bases", response_model=List[KnowledgeBaseResponse])
async def list_knowledge_bases(
    client_id: Optional[UUID] = Query(None, description="Filtrar por ID do cliente"),
    limit: int = Query(100, description="Número máximo de resultados"),
    offset: int = Query(0, description="Número de resultados a pular")
):
    """Lista bases de conhecimento."""
    try:
        # Filtrar por client_id se fornecido
        filters = {}
        if client_id:
            filters["client_id"] = client_id
        
        # Buscar no repositório
        knowledge_bases = await knowledge_base_repository.list(filters=filters, limit=limit, offset=offset)
        
        return knowledge_bases
    except Exception as e:
        logger.error(f"Erro ao listar bases de conhecimento: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao listar bases de conhecimento: {str(e)}"
        )


@router.get("/knowledge-bases/{knowledge_base_id}", response_model=KnowledgeBaseResponse)
async def get_knowledge_base(
    knowledge_base_id: UUID = Path(..., description="ID da base de conhecimento")
):
    """Obtém uma base de conhecimento pelo ID."""
    try:
        # Buscar no repositório
        knowledge_base = await knowledge_base_repository.get_by_id(knowledge_base_id)
        
        if not knowledge_base:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Base de conhecimento com ID {knowledge_base_id} não encontrada"
            )
        
        return knowledge_base
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter base de conhecimento: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao obter base de conhecimento: {str(e)}"
        )


@router.put("/knowledge-bases/{knowledge_base_id}", response_model=KnowledgeBaseResponse)
async def update_knowledge_base(
    knowledge_base_id: UUID = Path(..., description="ID da base de conhecimento"),
    knowledge_base: KnowledgeBaseUpdate = Body(...)
):
    """Atualiza uma base de conhecimento."""
    try:
        # Verificar se a base de conhecimento existe
        existing_kb = await knowledge_base_repository.get_by_id(knowledge_base_id)
        
        if not existing_kb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Base de conhecimento com ID {knowledge_base_id} não encontrada"
            )
        
        # Atualizar campos
        if knowledge_base.name is not None:
            existing_kb.name = knowledge_base.name
        
        if knowledge_base.description is not None:
            existing_kb.description = knowledge_base.description
        
        # Salvar no repositório
        updated_kb = await knowledge_base_repository.update(knowledge_base_id, existing_kb)
        
        return updated_kb
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar base de conhecimento: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao atualizar base de conhecimento: {str(e)}"
        )


@router.delete("/knowledge-bases/{knowledge_base_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge_base(
    knowledge_base_id: UUID = Path(..., description="ID da base de conhecimento")
):
    """Exclui uma base de conhecimento."""
    try:
        # Verificar se a base de conhecimento existe
        existing_kb = await knowledge_base_repository.get_by_id(knowledge_base_id)
        
        if not existing_kb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Base de conhecimento com ID {knowledge_base_id} não encontrada"
            )
        
        # Excluir do repositório
        await knowledge_base_repository.delete(knowledge_base_id)
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao excluir base de conhecimento: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao excluir base de conhecimento: {str(e)}"
        )


# Endpoints para KnowledgeCollection

@router.post("/collections", response_model=KnowledgeCollectionResponse, status_code=status.HTTP_201_CREATED)
async def create_collection(collection: KnowledgeCollectionCreate):
    """Cria uma nova coleção."""
    try:
        # Verificar se a base de conhecimento existe
        kb = await knowledge_base_repository.get_by_id(collection.knowledge_base_id)
        
        if not kb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Base de conhecimento com ID {collection.knowledge_base_id} não encontrada"
            )
        
        # Criar objeto KnowledgeCollection
        kc = KnowledgeCollection(
            name=collection.name,
            description=collection.description,
            knowledge_base_id=collection.knowledge_base_id
        )
        
        # Salvar no repositório
        created_kc = await knowledge_collection_repository.create(kc)
        
        return created_kc
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao criar coleção: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar coleção: {str(e)}"
        )


@router.get("/collections", response_model=List[KnowledgeCollectionResponse])
async def list_collections(
    knowledge_base_id: Optional[UUID] = Query(None, description="Filtrar por ID da base de conhecimento"),
    limit: int = Query(100, description="Número máximo de resultados"),
    offset: int = Query(0, description="Número de resultados a pular")
):
    """Lista coleções."""
    try:
        # Filtrar por knowledge_base_id se fornecido
        filters = {}
        if knowledge_base_id:
            filters["knowledge_base_id"] = knowledge_base_id
        
        # Buscar no repositório
        collections = await knowledge_collection_repository.list(filters=filters, limit=limit, offset=offset)
        
        return collections
    except Exception as e:
        logger.error(f"Erro ao listar coleções: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao listar coleções: {str(e)}"
        )


@router.get("/collections/{collection_id}", response_model=KnowledgeCollectionResponse)
async def get_collection(
    collection_id: UUID = Path(..., description="ID da coleção")
):
    """Obtém uma coleção pelo ID."""
    try:
        # Buscar no repositório
        collection = await knowledge_collection_repository.get_by_id(collection_id)
        
        if not collection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Coleção com ID {collection_id} não encontrada"
            )
        
        return collection
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter coleção: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao obter coleção: {str(e)}"
        )


@router.put("/collections/{collection_id}", response_model=KnowledgeCollectionResponse)
async def update_collection(
    collection_id: UUID = Path(..., description="ID da coleção"),
    collection: KnowledgeCollectionUpdate = Body(...)
):
    """Atualiza uma coleção."""
    try:
        # Verificar se a coleção existe
        existing_kc = await knowledge_collection_repository.get_by_id(collection_id)
        
        if not existing_kc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Coleção com ID {collection_id} não encontrada"
            )
        
        # Atualizar campos
        if collection.name is not None:
            existing_kc.name = collection.name
        
        if collection.description is not None:
            existing_kc.description = collection.description
        
        # Salvar no repositório
        updated_kc = await knowledge_collection_repository.update(collection_id, existing_kc)
        
        return updated_kc
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar coleção: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao atualizar coleção: {str(e)}"
        )


@router.delete("/collections/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_collection(
    collection_id: UUID = Path(..., description="ID da coleção")
):
    """Exclui uma coleção."""
    try:
        # Verificar se a coleção existe
        existing_kc = await knowledge_collection_repository.get_by_id(collection_id)
        
        if not existing_kc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Coleção com ID {collection_id} não encontrada"
            )
        
        # Excluir do repositório
        await knowledge_collection_repository.delete(collection_id)
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao excluir coleção: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao excluir coleção: {str(e)}"
        )


# Endpoints para Document

@router.post("/documents", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(document: DocumentCreate):
    """Cria um novo documento."""
    try:
        # Verificar se a coleção existe
        collection = await knowledge_collection_repository.get_by_id(document.collection_id)
        
        if not collection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Coleção com ID {document.collection_id} não encontrada"
            )
        
        # Criar objeto Document
        doc = Document(
            name=document.name,
            collection_id=document.collection_id,
            source_type=document.source_type,
            source_url=document.source_url,
            file_type=document.file_type,
            file_size=document.file_size,
            status="pending"
        )
        
        # Salvar no repositório
        created_doc = await document_repository.create(doc)
        
        # Adicionar contagem de chunks
        created_doc_dict = created_doc.model_dump()
        created_doc_dict["chunks_count"] = 0
        
        return created_doc_dict
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao criar documento: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar documento: {str(e)}"
        )


@router.get("/documents", response_model=List[DocumentResponse])
async def list_documents(
    collection_id: Optional[UUID] = Query(None, description="Filtrar por ID da coleção"),
    limit: int = Query(100, description="Número máximo de resultados"),
    offset: int = Query(0, description="Número de resultados a pular")
):
    """Lista documentos."""
    try:
        # Filtrar por collection_id se fornecido
        filters = {}
        if collection_id:
            filters["collection_id"] = collection_id
        
        # Buscar no repositório
        documents = await document_repository.list(filters=filters, limit=limit, offset=offset)
        
        # Adicionar contagem de chunks para cada documento
        result = []
        for doc in documents:
            doc_dict = doc.model_dump()
            # Contar chunks (em produção, isso seria otimizado com JOIN)
            chunks_count = await document_chunk_repository.count_by_document_id(doc.id)
            doc_dict["chunks_count"] = chunks_count
            result.append(doc_dict)
        
        return result
    except Exception as e:
        logger.error(f"Erro ao listar documentos: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao listar documentos: {str(e)}"
        )


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID = Path(..., description="ID do documento")
):
    """Obtém um documento pelo ID."""
    try:
        # Buscar no repositório
        document = await document_repository.get_by_id(document_id)
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Documento com ID {document_id} não encontrado"
            )
        
        # Adicionar contagem de chunks
        doc_dict = document.model_dump()
        chunks_count = await document_chunk_repository.count_by_document_id(document_id)
        doc_dict["chunks_count"] = chunks_count
        
        return doc_dict
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter documento: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao obter documento: {str(e)}"
        )


@router.put("/documents/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: UUID = Path(..., description="ID do documento"),
    document: DocumentUpdate = Body(...)
):
    """Atualiza um documento."""
    try:
        # Verificar se o documento existe
        existing_doc = await document_repository.get_by_id(document_id)
        
        if not existing_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Documento com ID {document_id} não encontrado"
            )
        
        # Atualizar campos
        if document.name is not None:
            existing_doc.name = document.name
        
        if document.status is not None:
            existing_doc.status = document.status
        
        # Salvar no repositório
        updated_doc = await document_repository.update(document_id, existing_doc)
        
        # Adicionar contagem de chunks
        doc_dict = updated_doc.model_dump()
        chunks_count = await document_chunk_repository.count_by_document_id(document_id)
        doc_dict["chunks_count"] = chunks_count
        
        return doc_dict
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar documento: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao atualizar documento: {str(e)}"
        )


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID = Path(..., description="ID do documento")
):
    """Exclui um documento."""
    try:
        # Verificar se o documento existe
        existing_doc = await document_repository.get_by_id(document_id)
        
        if not existing_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Documento com ID {document_id} não encontrado"
            )
        
        # Excluir do repositório
        await document_repository.delete(document_id)
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao excluir documento: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao excluir documento: {str(e)}"
        )


# Endpoints para DocumentChunk

@router.get("/documents/{document_id}/chunks", response_model=List[DocumentChunkResponse])
async def list_document_chunks(
    document_id: UUID = Path(..., description="ID do documento"),
    limit: int = Query(100, description="Número máximo de resultados"),
    offset: int = Query(0, description="Número de resultados a pular")
):
    """Lista chunks de um documento."""
    try:
        # Verificar se o documento existe
        document = await document_repository.get_by_id(document_id)
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Documento com ID {document_id} não encontrado"
            )
        
        # Buscar chunks no repositório
        chunks = await document_chunk_repository.get_by_document_id(document_id, limit=limit, offset=offset)
        
        return chunks
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao listar chunks do documento: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao listar chunks do documento: {str(e)}"
        )


@router.get("/chunks/{chunk_id}", response_model=DocumentChunkResponse)
async def get_chunk(
    chunk_id: UUID = Path(..., description="ID do chunk")
):
    """Obtém um chunk pelo ID."""
    try:
        # Buscar no repositório
        chunk = await document_chunk_repository.get_by_id(chunk_id)
        
        if not chunk:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chunk com ID {chunk_id} não encontrado"
            )
        
        return chunk
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter chunk: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao obter chunk: {str(e)}"
        )


# Endpoints para busca semântica

@router.post("/search", response_model=SemanticSearchResponse)
async def search(search_request: SemanticSearchRequest):
    """Realiza uma busca semântica."""
    try:
        start_time = time.time()
        
        # Realizar busca semântica
        results = await semantic_search_service.search_chunks(
            query=search_request.query,
            collection_ids=search_request.collection_ids,
            similarity_threshold=search_request.similarity_threshold,
            max_results=search_request.max_results
        )
        
        # Calcular tempo de execução
        execution_time_ms = (time.time() - start_time) * 1000
        
        # Formatar resposta
        response = {
            "results": results,
            "query": search_request.query,
            "total_results": len(results),
            "execution_time_ms": execution_time_ms
        }
        
        return response
    except Exception as e:
        logger.error(f"Erro ao realizar busca semântica: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao realizar busca semântica: {str(e)}"
        )


@router.post("/generate-context", response_model=ContextGenerationResponse)
async def generate_context(context_request: ContextGenerationRequest):
    """Gera um contexto para uma consulta."""
    try:
        start_time = time.time()
        
        # Gerar contexto
        context, chunks_used = await semantic_search_service.generate_context(
            query=context_request.query,
            collection_ids=context_request.collection_ids,
            max_tokens=context_request.max_tokens,
            similarity_threshold=context_request.similarity_threshold
        )
        
        # Calcular tempo de execução
        execution_time_ms = (time.time() - start_time) * 1000
        
        # Calcular similaridade média
        avg_similarity = sum(chunk["similarity"] for chunk in chunks_used) / len(chunks_used) if chunks_used else 0
        
        # Formatar resposta
        response = {
            "context": context,
            "chunks_used": chunks_used,
            "total_chunks": len(chunks_used),
            "context_length": len(context),
            "average_similarity": avg_similarity,
            "execution_time_ms": execution_time_ms
        }
        
        return response
    except Exception as e:
        logger.error(f"Erro ao gerar contexto: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao gerar contexto: {str(e)}"
        )


# Endpoints para processamento de documentos

@router.post("/documents/{document_id}/process", response_model=ProcessDocumentResponse)
async def process_document(
    document_id: UUID = Path(..., description="ID do documento")
):
    """Processa um documento (chunking e embedding)."""
    try:
        # Verificar se o documento existe
        document = await document_repository.get_by_id(document_id)
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Documento com ID {document_id} não encontrado"
            )
        
        # Verificar se o documento já está sendo processado
        if document.status == "processing":
            return {
                "document_id": document_id,
                "status": "processing",
                "message": "Documento já está sendo processado"
            }
        
        # Atualizar status para "processing"
        document.status = "processing"
        await document_repository.update(document_id, document)
        
        # Em uma implementação real, o processamento seria feito de forma assíncrona
        # Aqui, vamos simular um processamento simples para fins de demonstração
        
        # Simular chunks
        chunks = [
            {
                "content": f"Este é um chunk de teste para o documento {document_id}. Chunk 1.",
                "chunk_index": 1,
                "metadata": {"page": 1, "position": "top"}
            },
            {
                "content": f"Este é um chunk de teste para o documento {document_id}. Chunk 2.",
                "chunk_index": 2,
                "metadata": {"page": 1, "position": "middle"}
            },
            {
                "content": f"Este é um chunk de teste para o documento {document_id}. Chunk 3.",
                "chunk_index": 3,
                "metadata": {"page": 1, "position": "bottom"}
            }
        ]
        
        # Criar chunks com embeddings
        await embedding_service.create_document_chunks_with_embeddings(document_id, chunks)
        
        # Atualizar status para "completed"
        document.status = "completed"
        await document_repository.update(document_id, document)
        
        return {
            "document_id": document_id,
            "status": "completed",
            "message": f"Documento processado com sucesso. {len(chunks)} chunks criados."
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao processar documento: {str(e)}")
        
        # Atualizar status para "failed"
        try:
            document = await document_repository.get_by_id(document_id)
            if document:
                document.status = "failed"
                await document_repository.update(document_id, document)
        except Exception:
            pass
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar documento: {str(e)}"
        )


# Endpoints para estatísticas de uso

@router.get("/documents/{document_id}/usage-stats", response_model=UsageStatsResponse)
async def get_document_usage_stats(
    document_id: UUID = Path(..., description="ID do documento")
):
    """Obtém estatísticas de uso de um documento."""
    try:
        # Verificar se o documento existe
        document = await document_repository.get_by_id(document_id)
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Documento com ID {document_id} não encontrado"
            )
        
        # Obter estatísticas de uso
        stats = await usage_tracking_service.get_document_usage_stats(document_id)
        
        return stats
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas de uso do documento: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao obter estatísticas de uso do documento: {str(e)}"
        )