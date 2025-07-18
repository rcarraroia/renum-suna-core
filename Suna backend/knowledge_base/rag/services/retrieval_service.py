"""
Retrieval service for the RAG module.

This module provides functionality for retrieving relevant chunks
based on a query.
"""

import json
from typing import List, Dict, Any, Optional, Union, Tuple
import asyncio
import redis.asyncio as redis

from utils.logger import logger
from services.supabase import DBConnection
from knowledge_base.rag.services.embedding_service import EmbeddingService


class RetrievalService:
    """Service for retrieving relevant chunks."""

    def __init__(
        self,
        embedding_service: EmbeddingService = None,
        db_connection: DBConnection = None,
        redis_client: redis.Redis = None,
        cache_ttl: int = 600  # 10 minutes
    ):
        """Initialize the retrieval service.
        
        Args:
            embedding_service: Embedding service for generating query embeddings.
            db_connection: Database connection.
            redis_client: Redis client for caching.
            cache_ttl: Time-to-live for cache entries in seconds.
        """
        self.embedding_service = embedding_service or EmbeddingService()
        self.db = db_connection or DBConnection()
        self.redis_client = redis_client
        self.cache_ttl = cache_ttl

    async def retrieve_relevant_chunks(
        self,
        query: str,
        collection_ids: List[str] = None,
        top_k: int = 5,
        filters: Dict[str, Any] = None,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """Retrieve chunks relevant to the query.
        
        Args:
            query: Query text.
            collection_ids: List of collection IDs to search in.
            top_k: Number of chunks to retrieve.
            filters: Additional filters to apply.
            use_cache: Whether to use cache.
            
        Returns:
            List of relevant chunks with metadata.
        """
        if not query:
            return []
        
        # Check cache if enabled
        if use_cache and self.redis_client:
            cache_key = self._get_cache_key(query, collection_ids, top_k, filters)
            cached_result = await self._get_from_cache(cache_key)
            if cached_result:
                logger.debug(f"Cache hit for query: {query}")
                return cached_result
        
        # Generate embedding for the query
        query_embedding = await self.embedding_service.generate_embeddings([query])
        if not query_embedding:
            logger.error("Failed to generate embedding for query")
            return []
        
        # Retrieve relevant chunks
        try:
            client = await self.db.client
            
            # Prepare filters
            filter_params = {}
            if collection_ids:
                filter_params['p_collection_ids'] = collection_ids
            if filters:
                filter_params['p_filters'] = json.dumps(filters)
            
            # Call the vector search function
            result = await client.rpc(
                'search_embeddings',
                {
                    'p_query_embedding': query_embedding[0],
                    'p_top_k': top_k,
                    **filter_params
                }
            ).execute()
            
            if not result.data:
                return []
            
            # Process results
            chunks = []
            for item in result.data:
                chunk = {
                    'id': item['chunk_id'],
                    'document_id': item['document_id'],
                    'content': item['content'],
                    'chunk_index': item['chunk_index'],
                    'metadata': item['metadata'],
                    'similarity': item['similarity'],
                    'created_at': item['created_at'],
                    'document': {
                        'id': item['document_id'],
                        'name': item['document_name'],
                        'source_type': item['source_type'],
                        'collection_id': item['collection_id'],
                        'collection_name': item['collection_name']
                    }
                }
                chunks.append(chunk)
            
            # Cache the result if enabled
            if use_cache and self.redis_client:
                await self._store_in_cache(cache_key, chunks)
            
            return chunks
        except Exception as e:
            logger.error(f"Error retrieving relevant chunks: {str(e)}")
            return []

    async def retrieve_by_filters(
        self,
        filters: Dict[str, Any],
        collection_ids: List[str] = None,
        top_k: int = 5,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """Retrieve chunks based on filters.
        
        Args:
            filters: Filters to apply.
            collection_ids: List of collection IDs to search in.
            top_k: Number of chunks to retrieve.
            use_cache: Whether to use cache.
            
        Returns:
            List of chunks matching the filters.
        """
        if not filters:
            return []
        
        # Check cache if enabled
        if use_cache and self.redis_client:
            cache_key = self._get_cache_key(None, collection_ids, top_k, filters)
            cached_result = await self._get_from_cache(cache_key)
            if cached_result:
                logger.debug(f"Cache hit for filters: {filters}")
                return cached_result
        
        try:
            client = await self.db.client
            
            # Prepare filters
            filter_params = {'p_filters': json.dumps(filters)}
            if collection_ids:
                filter_params['p_collection_ids'] = collection_ids
            
            # Call the filter search function
            result = await client.rpc(
                'filter_chunks',
                {
                    'p_top_k': top_k,
                    **filter_params
                }
            ).execute()
            
            if not result.data:
                return []
            
            # Process results
            chunks = []
            for item in result.data:
                chunk = {
                    'id': item['chunk_id'],
                    'document_id': item['document_id'],
                    'content': item['content'],
                    'chunk_index': item['chunk_index'],
                    'metadata': item['metadata'],
                    'created_at': item['created_at'],
                    'document': {
                        'id': item['document_id'],
                        'name': item['document_name'],
                        'source_type': item['source_type'],
                        'collection_id': item['collection_id'],
                        'collection_name': item['collection_name']
                    }
                }
                chunks.append(chunk)
            
            # Cache the result if enabled
            if use_cache and self.redis_client:
                await self._store_in_cache(cache_key, chunks)
            
            return chunks
        except Exception as e:
            logger.error(f"Error retrieving chunks by filters: {str(e)}")
            return []

    async def track_chunk_usage(
        self,
        chunk_ids: List[str],
        agent_id: str,
        client_id: str
    ) -> bool:
        """Track usage of chunks.
        
        Args:
            chunk_ids: List of chunk IDs.
            agent_id: ID of the agent using the chunks.
            client_id: ID of the client.
            
        Returns:
            True if successful, False otherwise.
        """
        if not chunk_ids:
            return True
        
        try:
            client = await self.db.client
            
            # Update usage statistics
            for chunk_id in chunk_ids:
                await client.rpc(
                    'track_chunk_usage',
                    {
                        'p_chunk_id': chunk_id,
                        'p_agent_id': agent_id,
                        'p_client_id': client_id
                    }
                ).execute()
            
            return True
        except Exception as e:
            logger.error(f"Error tracking chunk usage: {str(e)}")
            return False

    async def _get_from_cache(self, cache_key: str) -> Optional[List[Dict[str, Any]]]:
        """Get result from cache.
        
        Args:
            cache_key: Cache key.
            
        Returns:
            Cached result or None if not found.
        """
        if not self.redis_client:
            return None
        
        try:
            cached_data = await self.redis_client.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
            return None
        except Exception as e:
            logger.error(f"Error getting from cache: {str(e)}")
            return None

    async def _store_in_cache(self, cache_key: str, data: List[Dict[str, Any]]) -> bool:
        """Store result in cache.
        
        Args:
            cache_key: Cache key.
            data: Data to store.
            
        Returns:
            True if successful, False otherwise.
        """
        if not self.redis_client:
            return False
        
        try:
            await self.redis_client.setex(
                cache_key,
                self.cache_ttl,
                json.dumps(data)
            )
            return True
        except Exception as e:
            logger.error(f"Error storing in cache: {str(e)}")
            return False

    def _get_cache_key(
        self,
        query: Optional[str],
        collection_ids: Optional[List[str]],
        top_k: int,
        filters: Optional[Dict[str, Any]]
    ) -> str:
        """Generate a cache key.
        
        Args:
            query: Query text.
            collection_ids: List of collection IDs.
            top_k: Number of chunks to retrieve.
            filters: Additional filters.
            
        Returns:
            Cache key.
        """
        key_parts = ["rag"]
        
        if query:
            key_parts.append(f"q:{query}")
        
        if collection_ids:
            key_parts.append(f"c:{','.join(sorted(collection_ids))}")
        
        key_parts.append(f"k:{top_k}")
        
        if filters:
            # Sort filter keys for consistent cache keys
            sorted_filters = json.dumps(filters, sort_keys=True)
            key_parts.append(f"f:{sorted_filters}")
        
        return ":".join(key_parts)