"""
Vector store implementation using FAISS for efficient similarity search.
Integrates with chunking and embedding systems for end-to-end vector storage and retrieval.
"""

from typing import List, Dict, Optional, Union, Tuple
import numpy as np
import faiss
import json
from pathlib import Path
from datetime import datetime
from loguru import logger

from .chunking import TextChunk
from .embeddings import EmbeddingGenerator

class VectorStore:
    """Manages storage and retrieval of vector embeddings using FAISS."""
    
    def __init__(self, 
                 embedding_dim: int = 384,  # Default for all-MiniLM-L6-v2
                 index_type: str = "L2",
                 store_dir: str = "data/vector_store"):
        """
        Initialize the vector store.
        
        Args:
            embedding_dim: Dimension of embeddings
            index_type: Type of FAISS index ('L2' or 'IP' for inner product)
            store_dir: Directory to store index and metadata
        """
        self.embedding_dim = embedding_dim
        self.store_dir = Path(store_dir)
        self.store_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize FAISS index
        if index_type == "L2":
            self.index = faiss.IndexFlatL2(embedding_dim)
        elif index_type == "IP":
            self.index = faiss.IndexFlatIP(embedding_dim)
        else:
            raise ValueError(f"Unsupported index type: {index_type}")
            
        # Metadata storage
        self.metadata: Dict[int, Dict] = {}
        self._load_metadata()
        
        self.embedding_generator = EmbeddingGenerator()
        
    def _load_metadata(self) -> None:
        """Load metadata from disk if it exists."""
        metadata_file = self.store_dir / "metadata.json"
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r') as f:
                    # Convert string keys back to integers
                    self.metadata = {int(k): v for k, v in json.load(f).items()}
            except Exception as e:
                logger.error(f"Failed to load metadata: {str(e)}")
                self.metadata = {}
                
    def _save_metadata(self) -> None:
        """Save metadata to disk."""
        try:
            metadata_file = self.store_dir / "metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(self.metadata, f)
        except Exception as e:
            logger.error(f"Failed to save metadata: {str(e)}")
            
    def add(self, chunks: List[TextChunk]) -> List[int]:
        """
        Add text chunks to the vector store.
        
        Args:
            chunks: List of TextChunks to add
            
        Returns:
            List of IDs assigned to the chunks
        """
        if not chunks:
            return []
            
        # Generate embeddings
        embeddings = self.embedding_generator.generate(chunks)
        embeddings_array = np.array(embeddings).astype('float32')
        
        # Add to FAISS index
        start_idx = self.index.ntotal
        self.index.add(embeddings_array)
        
        # Store metadata
        chunk_ids = []
        for i, chunk in enumerate(chunks):
            chunk_id = start_idx + i
            self.metadata[chunk_id] = {
                "text": chunk.text,
                "metadata": chunk.metadata,
                "timestamp": datetime.now().isoformat()
            }
            chunk_ids.append(chunk_id)
            
        self._save_metadata()
        return chunk_ids
        
    def search(self, 
               query: Union[str, np.ndarray],
               k: int = 5,
               threshold: Optional[float] = None) -> List[Tuple[int, float, Dict]]:
        """
        Search for similar vectors.
        
        Args:
            query: Query text or vector
            k: Number of results to return
            threshold: Optional similarity threshold
            
        Returns:
            List of tuples (id, similarity_score, metadata)
        """
        # Convert query to vector if needed
        if isinstance(query, str):
            query_vector = self.embedding_generator.generate_single(query)
        else:
            query_vector = query
            
        query_vector = np.array([query_vector]).astype('float32')
        
        # Search index
        distances, indices = self.index.search(query_vector, k)
        
        # Format results
        results = []
        for distance, idx in zip(distances[0], indices[0]):
            if idx != -1:  # Valid index
                if threshold is None or distance <= threshold:
                    results.append((
                        int(idx),
                        float(distance),
                        self.metadata.get(int(idx), {})
                    ))
                    
        return results
        
    def delete(self, chunk_ids: List[int]) -> None:
        """
        Delete chunks from the store.
        
        Args:
            chunk_ids: List of chunk IDs to delete
        """
        # FAISS doesn't support deletion, so we need to rebuild the index
        if not chunk_ids:
            return
            
        # Get all vectors except those to delete
        all_vectors = []
        keep_metadata = {}
        total = self.index.ntotal
        
        for i in range(total):
            if i not in chunk_ids:
                vector = self.index.reconstruct(i)
                all_vectors.append(vector)
                if i in self.metadata:
                    keep_metadata[len(all_vectors)-1] = self.metadata[i]
                    
        # Rebuild index
        self.index.reset()
        if all_vectors:
            self.index.add(np.array(all_vectors).astype('float32'))
            
        # Update metadata
        self.metadata = keep_metadata
        self._save_metadata()
        
    def save(self, path: Optional[str] = None) -> None:
        """
        Save the vector store to disk.
        
        Args:
            path: Optional path to save to, defaults to store_dir
        """
        save_dir = Path(path) if path else self.store_dir
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, str(save_dir / "index.faiss"))
        
        # Save metadata
        with open(save_dir / "metadata.json", 'w') as f:
            json.dump(self.metadata, f)
            
    @classmethod
    def load(cls, path: str) -> 'VectorStore':
        """
        Load a vector store from disk.
        
        Args:
            path: Path to load from
            
        Returns:
            Loaded VectorStore instance
        """
        store = cls(store_dir=path)
        
        # Load FAISS index
        index_path = Path(path) / "index.faiss"
        if index_path.exists():
            store.index = faiss.read_index(str(index_path))
            
        return store
