"""
Chunking service for the RAG module.

This module provides functionality for splitting documents into chunks
using different strategies.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from utils.logger import logger


class ChunkingService:
    """Service for splitting documents into chunks."""

    def __init__(
        self,
        default_chunk_size: int = 1000,
        default_chunk_overlap: int = 200,
        default_strategy: str = "fixed_size"
    ):
        """Initialize the chunking service.
        
        Args:
            default_chunk_size: Default size of chunks in characters.
            default_chunk_overlap: Default overlap between chunks in characters.
            default_strategy: Default chunking strategy.
        """
        self.default_chunk_size = default_chunk_size
        self.default_chunk_overlap = default_chunk_overlap
        self.default_strategy = default_strategy

    def chunk_text(
        self,
        text: str,
        strategy: str = None,
        chunk_size: int = None,
        chunk_overlap: int = None,
        metadata: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Split text into chunks using the specified strategy.
        
        Args:
            text: Text to split into chunks.
            strategy: Chunking strategy to use.
            chunk_size: Size of chunks in characters.
            chunk_overlap: Overlap between chunks in characters.
            metadata: Metadata to include with each chunk.
            
        Returns:
            List of dictionaries containing chunk content and metadata.
        """
        if not text or not text.strip():
            return []

        strategy = strategy or self.default_strategy
        chunk_size = chunk_size or self.default_chunk_size
        chunk_overlap = chunk_overlap or self.default_chunk_overlap
        metadata = metadata or {}

        if strategy == "fixed_size":
            chunks = self._chunk_by_fixed_size(text, chunk_size, chunk_overlap)
        elif strategy == "paragraph":
            chunks = self._chunk_by_paragraph(text, chunk_size, chunk_overlap)
        elif strategy == "semantic":
            chunks = self._chunk_by_semantic(text, chunk_size, chunk_overlap)
        else:
            logger.warning(f"Unknown chunking strategy: {strategy}. Using fixed_size instead.")
            chunks = self._chunk_by_fixed_size(text, chunk_size, chunk_overlap)

        # Add metadata to chunks
        result = []
        for i, chunk in enumerate(chunks):
            result.append({
                "content": chunk,
                "chunk_index": i,
                "metadata": {
                    **metadata,
                    "strategy": strategy,
                    "chunk_size": chunk_size,
                    "chunk_overlap": chunk_overlap,
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                }
            })

        return result

    def _chunk_by_fixed_size(
        self, text: str, chunk_size: int, chunk_overlap: int
    ) -> List[str]:
        """Split text into chunks of fixed size with overlap.
        
        Args:
            text: Text to split into chunks.
            chunk_size: Size of chunks in characters.
            chunk_overlap: Overlap between chunks in characters.
            
        Returns:
            List of text chunks.
        """
        if chunk_size <= 0:
            raise ValueError("Chunk size must be positive")
        if chunk_overlap < 0:
            raise ValueError("Chunk overlap must be non-negative")
        if chunk_overlap >= chunk_size:
            raise ValueError("Chunk overlap must be less than chunk size")

        text = text.strip()
        if not text:
            return []

        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = min(start + chunk_size, text_length)
            
            # If this is not the first chunk and we're not at the end,
            # try to find a good break point
            if start > 0 and end < text_length:
                # Look for a newline or period to break on
                break_point = self._find_break_point(text, end)
                if break_point > start:  # Only use if it's after the start
                    end = break_point

            chunks.append(text[start:end])
            start = end - chunk_overlap

        return chunks

    def _chunk_by_paragraph(
        self, text: str, max_chunk_size: int, chunk_overlap: int
    ) -> List[str]:
        """Split text into chunks by paragraphs.
        
        Args:
            text: Text to split into chunks.
            max_chunk_size: Maximum size of chunks in characters.
            chunk_overlap: Overlap between chunks in characters.
            
        Returns:
            List of text chunks.
        """
        # Split text into paragraphs
        paragraphs = re.split(r'\n\s*\n', text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        if not paragraphs:
            return []

        chunks = []
        current_chunk = []
        current_size = 0

        for paragraph in paragraphs:
            paragraph_size = len(paragraph)
            
            # If adding this paragraph would exceed max_chunk_size,
            # finalize the current chunk and start a new one
            if current_size + paragraph_size > max_chunk_size and current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                
                # Start new chunk with overlap
                overlap_size = 0
                overlap_chunks = []
                
                # Add paragraphs from the end of the previous chunk for overlap
                for p in reversed(current_chunk):
                    if overlap_size + len(p) <= chunk_overlap:
                        overlap_chunks.insert(0, p)
                        overlap_size += len(p)
                    else:
                        break
                
                current_chunk = overlap_chunks
                current_size = overlap_size
            
            current_chunk.append(paragraph)
            current_size += paragraph_size
        
        # Add the last chunk if it's not empty
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        
        return chunks

    def _chunk_by_semantic(
        self, text: str, max_chunk_size: int, chunk_overlap: int
    ) -> List[str]:
        """Split text into chunks by semantic units.
        
        This is a simplified implementation that tries to keep sentences together.
        For a more sophisticated semantic chunking, you would need to use
        a language model to identify semantic boundaries.
        
        Args:
            text: Text to split into chunks.
            max_chunk_size: Maximum size of chunks in characters.
            chunk_overlap: Overlap between chunks in characters.
            
        Returns:
            List of text chunks.
        """
        # Split text into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return []

        chunks = []
        current_chunk = []
        current_size = 0

        for sentence in sentences:
            sentence_size = len(sentence)
            
            # If this sentence alone exceeds max_chunk_size, split it further
            if sentence_size > max_chunk_size:
                # Finalize current chunk if not empty
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                    current_chunk = []
                    current_size = 0
                
                # Split the long sentence using fixed size chunking
                sentence_chunks = self._chunk_by_fixed_size(
                    sentence, max_chunk_size, chunk_overlap
                )
                chunks.extend(sentence_chunks)
                continue
            
            # If adding this sentence would exceed max_chunk_size,
            # finalize the current chunk and start a new one
            if current_size + sentence_size > max_chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                
                # Start new chunk with overlap
                overlap_size = 0
                overlap_sentences = []
                
                # Add sentences from the end of the previous chunk for overlap
                for s in reversed(current_chunk):
                    if overlap_size + len(s) <= chunk_overlap:
                        overlap_sentences.insert(0, s)
                        overlap_size += len(s)
                    else:
                        break
                
                current_chunk = overlap_sentences
                current_size = overlap_size
            
            current_chunk.append(sentence)
            current_size += sentence_size
        
        # Add the last chunk if it's not empty
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks

    def _find_break_point(self, text: str, position: int) -> int:
        """Find a good break point near the specified position.
        
        Looks for a newline, period, or space near the position.
        
        Args:
            text: Text to search in.
            position: Position to find a break point near.
            
        Returns:
            Position of the break point.
        """
        # Look for a newline before the position
        newline_pos = text.rfind('\n', position - 100, position)
        if newline_pos != -1:
            return newline_pos + 1  # +1 to start after the newline
        
        # Look for a period followed by a space before the position
        period_pos = text.rfind('. ', position - 100, position)
        if period_pos != -1:
            return period_pos + 2  # +2 to start after the period and space
        
        # Look for a space before the position
        space_pos = text.rfind(' ', position - 50, position)
        if space_pos != -1:
            return space_pos + 1  # +1 to start after the space
        
        # If no good break point found, just use the original position
        return position