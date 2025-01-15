"""
Memory management system for the manager agent.
Integrates vector store for long-term memory and context management.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from loguru import logger

from vector_store.store import VectorStore
from vector_store.chunking import TextChunk, ChunkingStrategy

class MemoryManager:
    """Manages agent memory using vector store for context and history."""
    
    def __init__(self, 
                 store_dir: str = "data/agent_memory",
                 max_context_items: int = 10):
        """
        Initialize the memory manager.
        
        Args:
            store_dir: Directory for storing vector data
            max_context_items: Maximum number of context items to return
        """
        self.vector_store = VectorStore(store_dir=store_dir)
        self.chunking_strategy = ChunkingStrategy()
        self.max_context_items = max_context_items
        
    async def add_interaction(self, 
                            prompt: str, 
                            response: str,
                            task_id: str,
                            metadata: Optional[Dict[str, Any]] = None) -> List[str]:
        """
        Add a prompt-response interaction to memory.
        
        Args:
            prompt: User's prompt
            response: Agent's response
            task_id: Associated task ID
            metadata: Additional metadata
            
        Returns:
            List of chunk IDs created
        """
        # Create chunks for both prompt and response
        chunks = []
        
        # Add prompt chunk
        prompt_chunk = TextChunk(
            text=prompt,
            metadata={
                "type": "prompt",
                "task_id": task_id,
                "timestamp": datetime.now().isoformat(),
                **(metadata or {})
            }
        )
        chunks.append(prompt_chunk)
        
        # Add response chunk
        response_chunk = TextChunk(
            text=response,
            metadata={
                "type": "response",
                "task_id": task_id,
                "timestamp": datetime.now().isoformat(),
                **(metadata or {})
            }
        )
        chunks.append(response_chunk)
        
        # Store in vector store
        chunk_ids = self.vector_store.add(chunks)
        logger.debug(f"Added interaction to memory with chunk IDs: {chunk_ids}")
        return chunk_ids
        
    async def get_relevant_context(self, 
                                 query: str,
                                 k: Optional[int] = None,
                                 threshold: Optional[float] = 0.7) -> List[Dict[str, Any]]:
        """
        Retrieve relevant context for a query.
        
        Args:
            query: The query to find context for
            k: Number of results to return (defaults to max_context_items)
            threshold: Similarity threshold
            
        Returns:
            List of relevant context items with metadata
        """
        k = k or self.max_context_items
        results = self.vector_store.search(query, k=k, threshold=threshold)
        
        context_items = []
        for _, score, metadata in results:
            context_items.append({
                "text": metadata["text"],
                "type": metadata.get("type"),
                "task_id": metadata.get("task_id"),
                "timestamp": metadata.get("timestamp"),
                "relevance_score": score
            })
            
        return context_items
        
    async def get_task_history(self, task_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve all interactions for a specific task.
        
        Args:
            task_id: The task ID to get history for
            
        Returns:
            List of interactions in chronological order
        """
        # We'll implement a metadata-based search in the future
        # For now, we'll retrieve recent items and filter
        results = await self.get_relevant_context("", k=100)
        
        task_history = [
            item for item in results
            if item.get("task_id") == task_id
        ]
        
        # Sort by timestamp
        task_history.sort(key=lambda x: x.get("timestamp", ""))
        return task_history
        
    async def clear_task_memory(self, task_id: str) -> None:
        """
        Remove all memory entries for a specific task.
        
        Args:
            task_id: The task ID to clear memory for
        """
        # This is a placeholder until we implement metadata-based deletion
        logger.warning("clear_task_memory is not yet implemented")
        pass
        
    async def summarize_context(self, context_items: List[Dict[str, Any]]) -> str:
        """
        Create a summary of context items for injection into prompts.
        
        Args:
            context_items: List of context items to summarize
            
        Returns:
            Formatted context summary
        """
        if not context_items:
            return ""
            
        summary = "Previous relevant context:\n\n"
        for item in context_items:
            item_type = item.get("type", "interaction")
            timestamp = item.get("timestamp", "")
            text = item.get("text", "")
            
            summary += f"[{item_type.upper()}] {timestamp}\n{text}\n\n"
            
        return summary.strip() 