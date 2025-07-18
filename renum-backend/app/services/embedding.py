"""
Módulo que implementa o serviço de embeddings para o módulo RAG da Plataforma Renum.

Este módulo fornece funcionalidades para gerar embeddings de texto usando
diferentes modelos e armazená-los no banco de dados vetorial do Supabase.
"""

import logging
import os
from typing import List, Dict, Any, Optional, Union
from uuid import UUID

import openai
import numpy as np
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.models.rag import DocumentChunk
from app.repositories.rag import document_chunk_repository

# Configurar logger
logger = logging.getLogger(__name__)

class EmbeddingService:
    """Serviço para gerenciar embeddings no módulo RAG."""
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """Implementação de Singleton para o serviço de embeddings."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        """Inicializa o serviço de embeddings."""
        self.model = settings.EMBEDDING_MODEL or "text-embedding-ada-002"
        self.openai_api_key = settings.OPENAI_API_KEY
        
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
        else:
            logger.warning("OPENAI_API_KEY não configurada. O serviço de embeddings pode não funcionar corretamente.")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate_embedding(self, text: str) -> List[float]:
        """Gera um embedding para o texto usando o modelo configurado.
        
        Args:
            text: Texto para gerar o embedding.
            
        Returns:
            Vetor de embedding.
            
        Raises:
            Exception: Se ocorrer um erro ao gerar o embedding.
        """
        try:
            # Limitar o tamanho do texto para evitar erros com tokens muito longos
            # A maioria dos modelos de embedding tem um limite de 8192 tokens
            max_tokens = 8000
            if len(text) > max_tokens * 4:  # Estimativa aproximada de 4 caracteres por token
                text = text[:max_tokens * 4]
                logger.warning(f"Texto truncado para {max_tokens * 4} caracteres")
            
            # Gerar embedding usando OpenAI
            response = await openai.Embedding.acreate(
                input=text,
                model=self.model
            )
            
            # Extrair o vetor de embedding
            embedding = response["data"][0]["embedding"]
            
            return embedding
        except Exception as e:
            logger.error(f"Erro ao gerar embedding: {str(e)}")
            raise
    
    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Gera embeddings para uma lista de textos.
        
        Args:
            texts: Lista de textos para gerar embeddings.
            
        Returns:
            Lista de vetores de embedding.
            
        Raises:
            Exception: Se ocorrer um erro ao gerar os embeddings.
        """
        try:
            # Limitar o tamanho dos textos
            max_tokens = 8000
            truncated_texts = []
            for text in texts:
                if len(text) > max_tokens * 4:
                    truncated_texts.append(text[:max_tokens * 4])
                    logger.warning(f"Texto truncado para {max_tokens * 4} caracteres")
                else:
                    truncated_texts.append(text)
            
            # Gerar embeddings em lote
            response = await openai.Embedding.acreate(
                input=truncated_texts,
                model=self.model
            )
            
            # Extrair os vetores de embedding
            embeddings = [item["embedding"] for item in response["data"]]
            
            return embeddings
        except Exception as e:
            logger.error(f"Erro ao gerar embeddings em lote: {str(e)}")
            raise
    
    async def create_document_chunks_with_embeddings(
        self, 
        document_id: Union[str, UUID], 
        chunks: List[Dict[str, Any]]
    ) -> List[DocumentChunk]:
        """Cria chunks de documento com embeddings.
        
        Args:
            document_id: ID do documento.
            chunks: Lista de dicionários com os dados dos chunks.
                Cada dicionário deve ter as chaves 'content', 'chunk_index' e opcionalmente 'metadata'.
                
        Returns:
            Lista de chunks criados.
            
        Raises:
            Exception: Se ocorrer um erro ao criar os chunks.
        """
        try:
            # Extrair os textos dos chunks
            texts = [chunk["content"] for chunk in chunks]
            
            # Gerar embeddings em lote
            embeddings = await self.generate_embeddings_batch(texts)
            
            # Criar objetos DocumentChunk
            document_chunks = []
            for i, chunk in enumerate(chunks):
                document_chunk = DocumentChunk(
                    document_id=document_id,
                    content=chunk["content"],
                    chunk_index=chunk["chunk_index"],
                    metadata=chunk.get("metadata", {}),
                    embedding=embeddings[i]
                )
                document_chunks.append(document_chunk)
            
            # Salvar os chunks no banco de dados
            created_chunks = await document_chunk_repository.create_batch(document_chunks)
            
            return created_chunks
        except Exception as e:
            logger.error(f"Erro ao criar chunks com embeddings: {str(e)}")
            raise
    
    async def update_chunk_embedding(self, chunk_id: Union[str, UUID], content: str) -> DocumentChunk:
        """Atualiza o embedding de um chunk.
        
        Args:
            chunk_id: ID do chunk.
            content: Novo conteúdo do chunk.
            
        Returns:
            Chunk atualizado.
            
        Raises:
            Exception: Se ocorrer um erro ao atualizar o embedding.
        """
        try:
            # Gerar novo embedding
            embedding = await self.generate_embedding(content)
            
            # Atualizar o chunk
            chunk = await document_chunk_repository.get_by_id(chunk_id)
            if not chunk:
                raise ValueError(f"Chunk com ID {chunk_id} não encontrado")
            
            chunk.content = content
            chunk.embedding = embedding
            
            updated_chunk = await document_chunk_repository.update(chunk_id, chunk)
            
            return updated_chunk
        except Exception as e:
            logger.error(f"Erro ao atualizar embedding do chunk: {str(e)}")
            raise
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calcula a similaridade entre dois embeddings usando similaridade de cosseno.
        
        Args:
            embedding1: Primeiro vetor de embedding.
            embedding2: Segundo vetor de embedding.
            
        Returns:
            Valor de similaridade entre 0 e 1, onde 1 é mais similar.
        """
        # Converter para arrays numpy
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        # Normalizar os vetores
        vec1 = vec1 / np.linalg.norm(vec1)
        vec2 = vec2 / np.linalg.norm(vec2)
        
        # Calcular similaridade de cosseno
        similarity = np.dot(vec1, vec2)
        
        return float(similarity)


# Instância global do serviço de embeddings
embedding_service = EmbeddingService.get_instance()