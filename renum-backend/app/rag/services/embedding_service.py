"""
Embedding service for the RAG module.

This module provides functionality for generating and managing embeddings.
"""

from typing import List, Dict, Any, Optional, Union
import numpy as np

from app.core.logger import logger
from app.core.config import get_settings


class EmbeddingService:
    """Service for generating and managing embeddings."""

    def __init__(self, model_name: str = None):
        """Initialize the embedding service.
        
        Args:
            model_name: Name of the embedding model to use.
        """
        self.model_name = model_name or get_settings().default_embedding_model
        self._initialize_client()

    def _initialize_client(self):
        """Initialize the embedding client based on the model name."""
        try:
            if "openai" in self.model_name.lower():
                from openai import OpenAI
                self.client = OpenAI(api_key=get_settings().openai_api_key)
                self.client_type = "openai"
            elif "cohere" in self.model_name.lower():
                import cohere
                self.client = cohere.Client(get_settings().cohere_api_key)
                self.client_type = "cohere"
            else:
                # Default to OpenAI
                from openai import OpenAI
                self.client = OpenAI(api_key=get_settings().openai_api_key)
                self.client_type = "openai"
                self.model_name = "text-embedding-ada-002"
        except Exception as e:
            logger.error(f"Error initializing embedding client: {str(e)}")
            self.client = None
            self.client_type = None

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts.
        
        Args:
            texts: List of texts to generate embeddings for.
            
        Returns:
            List of embeddings.
        """
        if not texts:
            return []
        
        if not self.client:
            logger.error("Embedding client not initialized")
            return []
        
        try:
            if self.client_type == "openai":
                response = self.client.embeddings.create(
                    model=self.model_name,
                    input=texts
                )
                return [item.embedding for item in response.data]
            elif self.client_type == "cohere":
                response = self.client.embed(
                    texts=texts,
                    model=self.model_name
                )
                return response.embeddings
            else:
                logger.error(f"Unsupported client type: {self.client_type}")
                return []
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            return []

    async def store_embeddings(
        self,
        chunk_ids: List[str],
        embeddings: List[List[float]]
    ) -> bool:
        """Store embeddings in the vector database.
        
        Args:
            chunk_ids: List of chunk IDs.
            embeddings: List of embeddings.
            
        Returns:
            True if successful, False otherwise.
        """
        if len(chunk_ids) != len(embeddings):
            logger.error("Number of chunk IDs and embeddings must match")
            return False
        
        try:
            from app.core.database import get_db_client
            client = await get_db_client()
            
            # Store embeddings in batches
            batch_size = 100
            for i in range(0, len(chunk_ids), batch_size):
                batch_chunk_ids = chunk_ids[i:i+batch_size]
                batch_embeddings = embeddings[i:i+batch_size]
                
                # Update chunks with embeddings
                for j, (chunk_id, embedding) in enumerate(zip(batch_chunk_ids, batch_embeddings)):
                    await client.rpc(
                        'update_chunk_embedding',
                        {
                            'p_chunk_id': chunk_id,
                            'p_embedding': embedding
                        }
                    ).execute()
            
            return True
        except Exception as e:
            logger.error(f"Error storing embeddings: {str(e)}")
            return False

    async def delete_embeddings(self, chunk_ids: List[str]) -> bool:
        """Delete embeddings from the vector database.
        
        Args:
            chunk_ids: List of chunk IDs.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            from app.core.database import get_db_client
            client = await get_db_client()
            
            # Delete embeddings in batches
            batch_size = 100
            for i in range(0, len(chunk_ids), batch_size):
                batch_chunk_ids = chunk_ids[i:i+batch_size]
                
                # Delete embeddings
                await client.rpc(
                    'delete_chunk_embeddings',
                    {
                        'p_chunk_ids': batch_chunk_ids
                    }
                ).execute()
            
            return True
        except Exception as e:
            logger.error(f"Error deleting embeddings: {str(e)}")
            return False