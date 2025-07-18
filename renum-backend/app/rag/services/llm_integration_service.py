"""
LLM integration service for the RAG module.

This module provides functionality for integrating retrieved context
with LLM prompts.
"""

import json
import re
from typing import List, Dict, Any, Optional, Union, Tuple

from app.core.logger import logger


class LLMIntegrationService:
    """Service for integrating retrieved context with LLM prompts."""

    def __init__(
        self,
        max_context_length: int = 4000,
        context_template: str = None
    ):
        """Initialize the LLM integration service.
        
        Args:
            max_context_length: Maximum length of context in tokens.
            context_template: Template for formatting context.
        """
        self.max_context_length = max_context_length
        self.context_template = context_template or self._default_context_template()

    async def enrich_prompt(
        self,
        original_prompt: str,
        relevant_chunks: List[Dict[str, Any]],
        max_tokens: int = None
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """Enrich the prompt with relevant chunks.
        
        Args:
            original_prompt: Original prompt.
            relevant_chunks: List of relevant chunks.
            max_tokens: Maximum number of tokens to use for context.
            
        Returns:
            Tuple of enriched prompt and list of used chunks.
        """
        if not relevant_chunks:
            return original_prompt, []
        
        max_tokens = max_tokens or self.max_context_length
        
        # Sort chunks by similarity (highest first)
        sorted_chunks = sorted(
            relevant_chunks,
            key=lambda x: x.get('similarity', 0),
            reverse=True
        )
        
        # Prepare context
        context_parts = []
        used_chunks = []
        current_tokens = 0
        
        for chunk in sorted_chunks:
            # Estimate tokens (rough approximation: 1 token ≈ 4 characters)
            chunk_tokens = len(chunk['content']) // 4
            
            if current_tokens + chunk_tokens > max_tokens:
                # Skip this chunk if it would exceed the token limit
                continue
            
            # Format chunk with source information
            source_info = f"{chunk['document']['name']}"
            if chunk['document'].get('source_type') == 'url':
                source_info += f" ({chunk['document'].get('source_url', '')})"
            
            context_parts.append(f"[Source: {source_info}]\n{chunk['content']}")
            used_chunks.append(chunk)
            current_tokens += chunk_tokens
            
            if current_tokens >= max_tokens:
                break
        
        if not context_parts:
            return original_prompt, []
        
        # Format context using template
        context_text = "\n\n".join(context_parts)
        formatted_context = self.context_template.format(context=context_text)
        
        # Combine with original prompt
        enriched_prompt = f"{formatted_context}\n\n{original_prompt}"
        
        return enriched_prompt, used_chunks

    async def format_response_with_sources(
        self,
        response: str,
        used_chunks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Format the response with source information.
        
        Args:
            response: Response from the LLM.
            used_chunks: List of chunks used for the response.
            
        Returns:
            Dictionary with formatted response and sources.
        """
        if not used_chunks:
            return {
                'response': response,
                'sources': []
            }
        
        # Extract sources
        sources = []
        for chunk in used_chunks:
            source = {
                'chunk_id': chunk['id'],
                'document_id': chunk['document_id'],
                'document_name': chunk['document']['name'],
                'source_type': chunk['document']['source_type'],
                'collection_id': chunk['document']['collection_id'],
                'collection_name': chunk['document']['collection_name'],
                'similarity': chunk.get('similarity', 0)
            }
            
            if chunk['document'].get('source_type') == 'url':
                source['source_url'] = chunk['document'].get('source_url', '')
            
            sources.append(source)
        
        # Check if the response already contains source citations
        has_citations = bool(re.search(r'\[\d+\]', response))
        
        # If no citations, just return the response and sources
        if not has_citations:
            return {
                'response': response,
                'sources': sources
            }
        
        # If there are citations, try to match them with sources
        try:
            # Extract citation numbers
            citation_numbers = set(int(m.group(1)) for m in re.finditer(r'\[(\d+)\]', response))
            
            # Map citation numbers to sources
            citation_map = {}
            for num in citation_numbers:
                if 1 <= num <= len(sources):
                    citation_map[num] = sources[num - 1]
            
            # Replace citations with source information
            def replace_citation(match):
                num = int(match.group(1))
                if num in citation_map:
                    source = citation_map[num]
                    return f"[{source['document_name']}]"
                return match.group(0)
            
            formatted_response = re.sub(r'\[(\d+)\]', replace_citation, response)
            
            return {
                'response': formatted_response,
                'sources': sources
            }
        except Exception as e:
            logger.error(f"Error formatting response with sources: {str(e)}")
            return {
                'response': response,
                'sources': sources
            }

    def _default_context_template(self) -> str:
        """Get the default context template.
        
        Returns:
            Default context template.
        """
        return (
            "I'll provide you with some relevant information to help answer the user's question.\n"
            "Please use this information to inform your response, and cite the sources when appropriate.\n\n"
            "Relevant Information:\n"
            "{context}\n\n"
            "Based on the information above, please respond to the user's question. "
            "If the information doesn't contain the answer, you can use your general knowledge, "
            "but make it clear what information comes from the provided context and what doesn't."
        )