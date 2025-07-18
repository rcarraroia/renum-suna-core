"""
Chunking service for the RAG module.

This module provides functionality for chunking text into smaller pieces.
"""

from typing import List, Dict, Any, Optional
import re

from app.core.logger import logger


class ChunkingService:
    """Service for chunking text."""

    def chunk_text(
        self,
        text: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        chunking_strategy: str = "fixed_size",
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Chunk text into smaller pieces.
        
        Args:
            text: Text to chunk.
            chunk_size: Size of each chunk in characters.
            chunk_overlap: Overlap between chunks in characters.
            chunking_strategy: Strategy to use for chunking.
            metadata: Optional metadata to include with each chunk.
            
        Returns:
            List of chunks with content, chunk index, and metadata.
            
        Raises:
            ValueError: If the chunking strategy is not supported.
        """
        if not text:
            return []
        
        if chunking_strategy == "fixed_size":
            return self._chunk_fixed_size(text, chunk_size, chunk_overlap, metadata)
        elif chunking_strategy == "paragraph":
            return self._chunk_paragraph(text, chunk_size, chunk_overlap, metadata)
        elif chunking_strategy == "sentence":
            return self._chunk_sentence(text, chunk_size, chunk_overlap, metadata)
        else:
            raise ValueError(f"Unsupported chunking strategy: {chunking_strategy}")

    def _chunk_fixed_size(
        self,
        text: str,
        chunk_size: int,
        chunk_overlap: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Chunk text into fixed-size chunks.
        
        Args:
            text: Text to chunk.
            chunk_size: Size of each chunk in characters.
            chunk_overlap: Overlap between chunks in characters.
            metadata: Optional metadata to include with each chunk.
            
        Returns:
            List of chunks with content, chunk index, and metadata.
        """
        if not text:
            return []
        
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(text):
            # Calculate end position
            end = min(start + chunk_size, len(text))
            
            # If this is not the first chunk and we're not at the end of the text,
            # try to find a good breaking point (whitespace)
            if start > 0 and end < len(text):
                # Look for whitespace to break at
                whitespace_match = re.search(r'\s', text[end-20:end])
                if whitespace_match:
                    end = end - 20 + whitespace_match.start() + 1
            
            # Extract chunk
            chunk_text = text[start:end].strip()
            
            # Only add non-empty chunks
            if chunk_text:
                # Create chunk with metadata
                chunk = {
                    'content': chunk_text,
                    'chunk_index': chunk_index,
                    'metadata': {
                        'start_char': start,
                        'end_char': end
                    }
                }
                
                # Add additional metadata if provided
                if metadata:
                    chunk['metadata'].update(metadata)
                
                chunks.append(chunk)
                chunk_index += 1
            
            # Move start position for next chunk
            start = end - chunk_overlap
            
            # Ensure we're making progress
            if start >= end:
                start = end
        
        return chunks

    def _chunk_paragraph(
        self,
        text: str,
        chunk_size: int,
        chunk_overlap: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Chunk text by paragraphs.
        
        Args:
            text: Text to chunk.
            chunk_size: Maximum size of each chunk in characters.
            chunk_overlap: Not used in this strategy.
            metadata: Optional metadata to include with each chunk.
            
        Returns:
            List of chunks with content, chunk index, and metadata.
        """
        if not text:
            return []
        
        # Split text into paragraphs
        paragraphs = re.split(r'\n\s*\n', text)
        
        chunks = []
        current_chunk = ""
        current_start = 0
        chunk_index = 0
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            # If adding this paragraph would exceed the chunk size, start a new chunk
            if current_chunk and len(current_chunk) + len(paragraph) + 2 > chunk_size:
                # Create chunk with metadata
                chunk = {
                    'content': current_chunk.strip(),
                    'chunk_index': chunk_index,
                    'metadata': {
                        'start_char': current_start,
                        'end_char': current_start + len(current_chunk)
                    }
                }
                
                # Add additional metadata if provided
                if metadata:
                    chunk['metadata'].update(metadata)
                
                chunks.append(chunk)
                chunk_index += 1
                
                # Start a new chunk
                current_chunk = paragraph
                current_start = text.find(paragraph, current_start + len(current_chunk))
            else:
                # Add paragraph to current chunk
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
                    current_start = text.find(paragraph)
        
        # Add the last chunk if there's anything left
        if current_chunk:
            # Create chunk with metadata
            chunk = {
                'content': current_chunk.strip(),
                'chunk_index': chunk_index,
                'metadata': {
                    'start_char': current_start,
                    'end_char': current_start + len(current_chunk)
                }
            }
            
            # Add additional metadata if provided
            if metadata:
                chunk['metadata'].update(metadata)
            
            chunks.append(chunk)
        
        return chunks

    def _chunk_sentence(
        self,
        text: str,
        chunk_size: int,
        chunk_overlap: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Chunk text by sentences.
        
        Args:
            text: Text to chunk.
            chunk_size: Maximum size of each chunk in characters.
            chunk_overlap: Not used in this strategy.
            metadata: Optional metadata to include with each chunk.
            
        Returns:
            List of chunks with content, chunk index, and metadata.
        """
        if not text:
            return []
        
        # Split text into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        chunks = []
        current_chunk = ""
        current_start = 0
        chunk_index = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # If adding this sentence would exceed the chunk size, start a new chunk
            if current_chunk and len(current_chunk) + len(sentence) + 1 > chunk_size:
                # Create chunk with metadata
                chunk = {
                    'content': current_chunk.strip(),
                    'chunk_index': chunk_index,
                    'metadata': {
                        'start_char': current_start,
                        'end_char': current_start + len(current_chunk)
                    }
                }
                
                # Add additional metadata if provided
                if metadata:
                    chunk['metadata'].update(metadata)
                
                chunks.append(chunk)
                chunk_index += 1
                
                # Start a new chunk
                current_chunk = sentence
                current_start = text.find(sentence, current_start + len(current_chunk))
            else:
                # Add sentence to current chunk
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
                    current_start = text.find(sentence)
        
        # Add the last chunk if there's anything left
        if current_chunk:
            # Create chunk with metadata
            chunk = {
                'content': current_chunk.strip(),
                'chunk_index': chunk_index,
                'metadata': {
                    'start_char': current_start,
                    'end_char': current_start + len(current_chunk)
                }
            }
            
            # Add additional metadata if provided
            if metadata:
                chunk['metadata'].update(metadata)
            
            chunks.append(chunk)
        
        return chunks