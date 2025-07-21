"""
Embedding service for the RAG module.

This module provides functionality for generating embeddings for text chunks
using different embedding models.
"""

import os
import json
import asyncio
from typing import List, Dict, Any, Optional, Union, Tuple
import numpy as np

from utils.logger import logger
from services.supabase import DBConnection


class EmbeddingService:
    """Service for generating and managing embeddings."""

    def __init__(
        self,
        model_name: str = "openai",
        model_kwargs: Dict[str, Any] = None,
        cache_dir: str = None,
        db_connection: DBConnection = None
    ):
        """Initialize the embedding service.
        
        Args:
            model_name: Name of the embedding model to use.
            model_kwargs: Additional arguments for the embedding model.
            cache_dir: Directory to cache embeddings.
            db_connection: Database connection.
        """
        self.model_name = model_name
        self.model_kwargs = model_kwargs or {}
        self.cache_dir = cache_dir
        self.db = db_connection or DBConnection()
        self._model = None
        self._client = None

    async def initialize(self):
        """Initialize the embedding service."""
        if self.model_name == "openai":
            await self._initialize_openai()
        elif self.model_name == "sentence-transformers":
            await self._initialize_sentence_transformers()
        else:
            raise ValueError(f"Unsupported embedding model: {self.model_name}")

    async def _initialize_openai(self):
        """Initialize the OpenAI embedding model."""
        try:
            from openai import AsyncOpenAI
            
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            
            self._client = AsyncOpenAI(api_key=api_key)
            logger.info("OpenAI embedding model initialized")
        except ImportError:
            raise ImportError("OpenAI package not installed. Install it with 'pip install openai'")
        except Exception as e:
            logger.error(f"Error initializing OpenAI embedding model: {str(e)}")
            raise

    async def _initialize_sentence_transformers(self):
        """Initialize the Sentence Transformers embedding model."""
        try:
            from sentence_transformers import SentenceTransformer
            
            model_name = self.model_kwargs.get("model_name", "all-MiniLM-L6-v2")
            
            # Run in a thread to avoid blocking the event loop
            loop = asyncio.get_event_loop()
            self._model = await loop.run_in_executor(
                None, lambda: SentenceTransformer(model_name)
            )
            
            logger.info(f"Sentence Transformers model '{model_name}' initialized")
        except ImportError:
            raise ImportError(
                "Sentence Transformers package not installed. "
                "Install it with 'pip install sentence-transformers'"
            )
        except Exception as e:
            logger.error(f"Error initializing Sentence Transformers model: {str(e)}")
            raise

    async def generate_embeddings(
        self, texts: List[str]
    ) -> List[List[float]]:
        """Generate embeddings for a list of texts.
        
        Args:
            texts: List of texts to generate embeddings for.
            
        Returns:
            List of embeddings, where each embedding is a list of floats.
        """
        if not texts:
            return []
        
        if not self._model and not self._client:
            await self.initialize()
        
        if self.model_name == "openai":
            return await self._generate_openai_embeddings(texts)
        elif self.model_name == "sentence-transformers":
            return await self._generate_sentence_transformers_embeddings(texts)
        else:
            raise ValueError(f"Unsupported embedding model: {self.model_name}")

    async def _generate_openai_embeddings(
        self, texts: List[str]
    ) -> List[List[float]]:
        """Generate embeddings using OpenAI API.
        
        Args:
            texts: List of texts to generate embeddings for.
            
        Returns:
            List of embeddings, where each embedding is a list of floats.
        """
        try:
            model = self.model_kwargs.get("model", "text-embedding-ada-002")
            
            # OpenAI has a rate limit, so we need to batch the requests
            batch_size = 100
            embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i+batch_size]
                
                response = await self._client.embeddings.create(
                    model=model,
                    input=batch_texts
                )
                
                batch_embeddings = [item.embedding for item in response.data]
                embeddings.extend(batch_embeddings)
            
            return embeddings
        except Exception as e:
            logger.error(f"Error generating OpenAI embeddings: {str(e)}")
            raise

    async def _generate_sentence_transformers_embeddings(
        self, texts: List[str]
    ) -> List[List[float]]:
        """Generate embeddings using Sentence Transformers.
        
        Args:
            texts: List of texts to generate embeddings for.
            
        Returns:
            List of embeddings, where each embedding is a list of floats.
        """
        try:
            # Run in a thread to avoid blocking the event loop
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None, lambda: self._model.encode(texts)
            )
            
            # Convert numpy arrays to lists
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Error generating Sentence Transformers embeddings: {str(e)}")
            raise

    async def store_embeddings(
        self, chunk_ids: List[str], embeddings: List[List[float]]
    ) -> List[str]:
        """Store embeddings in the vector database.
        
        Args:
            chunk_ids: List of chunk IDs.
            embeddings: List of embeddings.
            
        Returns:
            List of embedding IDs.
        """
        if len(chunk_ids) != len(embeddings):
            raise ValueError("Number of chunk IDs must match number of embeddings")
        
        try:
            client = await self.db.client
            
            embedding_ids = []
            for i, (chunk_id, embedding) in enumerate(zip(chunk_ids, embeddings)):
                # Store embedding in pgvector
                result = await client.rpc(
                    'store_embedding',
                    {
                        'p_chunk_id': chunk_id,
                        'p_embedding': embedding,
                        'p_model': self.model_name
                    }
                ).execute()
                
                if not result.data:
                    logger.error(f"Failed to store embedding for chunk {chunk_id}")
                    continue
                
                embedding_id = result.data[0]['id']
                embedding_ids.append(embedding_id)
                
                # Update the document_chunks table with the embedding ID
                await client.table('document_chunks').update(
                    {'embedding_id': embedding_id}
                ).eq('id', chunk_id).execute()
            
            return embedding_ids
        except Exception as e:
            logger.error(f"Error storing embeddings: {str(e)}")
            raise

    async def delete_embeddings(self, chunk_ids: List[str]) -> bool:
        """Delete embeddings from the vector database.
        
        Args:
            chunk_ids: List of chunk IDs.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            client = await self.db.client
            
            # Get embedding IDs for the chunks
            result = await client.table('document_chunks').select(
                'embedding_id'
            ).in_('id', chunk_ids).execute()
            
            if not result.data:
                return True  # No embeddings to delete
            
            embedding_ids = [row['embedding_id'] for row in result.data if row['embedding_id']]
            
            if not embedding_ids:
                return True  # No embeddings to delete
            
            # Delete embeddings from pgvector
            await client.rpc(
                'delete_embeddings',
                {'p_embedding_ids': embedding_ids}
            ).execute()
            
            # Update document_chunks to remove embedding_id references
            await client.table('document_chunks').update(
                {'embedding_id': None}
            ).in_('id', chunk_ids).execute()
            
            return True
        except Exception as e:
            logger.error(f"Error deleting embeddings: {str(e)}")
            return False

    async def update_embeddings(
        self, chunk_ids: List[str], texts: List[str]
    ) -> List[str]:
        """Update embeddings for chunks.
        
        Args:
            chunk_ids: List of chunk IDs.
            texts: List of texts to generate embeddings for.
            
        Returns:
            List of embedding IDs.
        """
        # Delete existing embeddings
        await self.delete_embeddings(chunk_ids)
        
        # Generate new embeddings
        embeddings = await self.generate_embeddings(texts)
        
        # Store new embeddings
        return await self.store_embeddings(chunk_ids, embeddings)