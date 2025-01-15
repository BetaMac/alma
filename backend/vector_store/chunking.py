"""
Text chunking system for vector store.
Handles splitting text into semantically meaningful segments while maintaining context.
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
import re
from loguru import logger

@dataclass
class ChunkMetadata:
    """Metadata for a text chunk."""
    index: int
    char_start: int
    char_end: int
    token_count: Optional[int] = None
    source: Optional[str] = None
    context: Optional[Dict[str, str]] = None

@dataclass
class TextChunk:
    """Represents a chunk of text with its metadata."""
    text: str
    metadata: ChunkMetadata

class ChunkingStrategy:
    """Base class for text chunking strategies."""
    
    def __init__(self, 
                 chunk_size: int = 512,
                 chunk_overlap: int = 50,
                 respect_boundaries: bool = True):
        """
        Initialize chunking strategy.
        
        Args:
            chunk_size: Target size for each chunk in characters
            chunk_overlap: Number of characters to overlap between chunks
            respect_boundaries: Whether to respect sentence/paragraph boundaries
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.respect_boundaries = respect_boundaries
        
        # Common sentence boundary patterns
        self.sentence_endings = r'[.!?][\s]{1,2}'
        self.paragraph_breaks = r'\n\s*\n'
        
    def _find_boundary(self, text: str, position: int, forward: bool = True) -> int:
        """Find the nearest semantic boundary (sentence/paragraph) from position."""
        if not self.respect_boundaries:
            return position
            
        # Search window (larger for forward search to find complete sentences)
        window = 100 if forward else 50
        search_text = text[position:position + window] if forward else text[max(0, position - window):position]
        
        # Find sentence boundaries in search window
        boundaries = list(re.finditer(self.sentence_endings, search_text))
        if not boundaries:
            # Fall back to any punctuation or space
            boundaries = list(re.finditer(r'[,;:\s]', search_text))
        
        if boundaries:
            # Get the nearest boundary
            boundary = boundaries[0] if forward else boundaries[-1]
            offset = boundary.end() if forward else boundary.start()
            return position + offset if forward else position - (len(search_text) - offset)
            
        return position
    
    def create_chunks(self, text: str, source: Optional[str] = None) -> List[TextChunk]:
        """
        Split text into chunks with metadata.
        
        Args:
            text: Input text to chunk
            source: Optional source identifier for the text
            
        Returns:
            List of TextChunk objects
        """
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(text):
            # Find end position for current chunk
            end = start + self.chunk_size
            
            if end < len(text):
                # Find nearest semantic boundary
                end = self._find_boundary(text, end)
            else:
                end = len(text)
            
            # Create chunk with metadata
            chunk_text = text[start:end].strip()
            if chunk_text:  # Only create non-empty chunks
                metadata = ChunkMetadata(
                    index=chunk_index,
                    char_start=start,
                    char_end=end,
                    source=source,
                    context={
                        "prev_context": text[max(0, start-100):start].strip(),
                        "next_context": text[end:min(len(text), end+100)].strip()
                    }
                )
                chunks.append(TextChunk(text=chunk_text, metadata=metadata))
                chunk_index += 1
            
            # Move start position for next chunk, considering overlap
            start = end - self.chunk_overlap
            
            # Ensure we make progress
            if start >= end:
                start = end + 1
        
        return chunks

class TextChunker:
    """Main chunking interface with support for different strategies."""
    
    def __init__(self):
        self.default_strategy = ChunkingStrategy()
        self.strategies: Dict[str, ChunkingStrategy] = {}
    
    def add_strategy(self, name: str, strategy: ChunkingStrategy) -> None:
        """Add a new chunking strategy."""
        self.strategies[name] = strategy
    
    def process(self, 
                text: str, 
                strategy_name: Optional[str] = None, 
                source: Optional[str] = None) -> List[TextChunk]:
        """
        Process text using specified strategy or default.
        
        Args:
            text: Input text to chunk
            strategy_name: Name of strategy to use (uses default if None)
            source: Optional source identifier
            
        Returns:
            List of TextChunk objects
        """
        if not text.strip():
            return []
            
        try:
            strategy = self.strategies.get(strategy_name, self.default_strategy)
            chunks = strategy.create_chunks(text, source)
            logger.debug(f"Created {len(chunks)} chunks from text of length {len(text)}")
            return chunks
        except Exception as e:
            logger.error(f"Error chunking text: {str(e)}")
            raise
