"""
Embedding generation system for vector store.
Handles converting text chunks to vector embeddings with caching and batch processing.
"""

from typing import List, Dict, Optional, Union, Any
import numpy as np
from pathlib import Path
import json
import hashlib
from datetime import datetime
import torch
from transformers import AutoTokenizer, AutoModel
from loguru import logger
from .chunking import TextChunk

class EmbeddingCache:
    """Simple cache for embeddings to avoid regeneration."""
    
    def __init__(self, cache_dir: str = "cache/embeddings"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def _get_cache_key(self, text: str) -> str:
        """Generate a cache key for a text string."""
        return hashlib.md5(text.encode()).hexdigest()
    
    def get(self, text: str) -> Optional[np.ndarray]:
        """Retrieve embedding from cache if it exists."""
        cache_key = self._get_cache_key(text)
        cache_file = self.cache_dir / f"{cache_key}.npy"
        
        if cache_file.exists():
            try:
                return np.load(str(cache_file))
            except Exception as e:
                logger.warning(f"Failed to load cached embedding: {str(e)}")
                return None
        return None
    
    def store(self, text: str, embedding: np.ndarray) -> None:
        """Store embedding in cache."""
        try:
            cache_key = self._get_cache_key(text)
            cache_file = self.cache_dir / f"{cache_key}.npy"
            np.save(str(cache_file), embedding)
        except Exception as e:
            logger.warning(f"Failed to cache embedding: {str(e)}")

class EmbeddingGenerator:
    """Generates embeddings from text using transformer models."""
    
    def __init__(self, 
                 model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
                 device: Optional[str] = None,
                 use_cache: bool = True,
                 batch_size: int = 8):
        """
        Initialize the embedding generator.
        
        Args:
            model_name: Name of the transformer model to use
            device: Device to run model on ('cuda' or 'cpu')
            use_cache: Whether to use embedding cache
            batch_size: Size of batches for processing
        """
        self.model_name = model_name
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.batch_size = batch_size
        self.cache = EmbeddingCache() if use_cache else None
        
        logger.info(f"Initializing embedding model {model_name} on {self.device}")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name).to(self.device)
        self.model.eval()
        
    def _mean_pooling(self, model_output: Any, attention_mask: torch.Tensor) -> torch.Tensor:
        """Perform mean pooling on transformer output."""
        token_embeddings = model_output[0]
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)
    
    def _batch_encode(self, texts: List[str]) -> Dict[str, torch.Tensor]:
        """Encode a batch of texts using the tokenizer."""
        return self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors='pt'
        ).to(self.device)
    
    def _generate_batch(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for a batch of texts."""
        encoded = self._batch_encode(texts)
        
        with torch.no_grad():
            model_output = self.model(**encoded)
            embeddings = self._mean_pooling(model_output, encoded['attention_mask'])
            embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)
            
        return embeddings.cpu().numpy()
    
    def generate(self, chunks: Union[List[TextChunk], List[str]]) -> List[np.ndarray]:
        """
        Generate embeddings for text chunks.
        
        Args:
            chunks: List of TextChunks or strings to generate embeddings for
            
        Returns:
            List of numpy arrays containing embeddings
        """
        if not chunks:
            return []
            
        # Convert TextChunks to strings if needed
        texts = [chunk.text if isinstance(chunk, TextChunk) else chunk for chunk in chunks]
        embeddings = []
        
        for i in range(0, len(texts), self.batch_size):
            batch_texts = texts[i:i + self.batch_size]
            batch_embeddings = []
            
            # Check cache for each text in batch
            for text in batch_texts:
                if self.cache:
                    cached_embedding = self.cache.get(text)
                    if cached_embedding is not None:
                        batch_embeddings.append(cached_embedding)
                        continue
                        
                batch_embeddings.append(None)
            
            # Generate embeddings for texts not in cache
            texts_to_generate = [text for text, emb in zip(batch_texts, batch_embeddings) if emb is None]
            if texts_to_generate:
                generated = self._generate_batch(texts_to_generate)
                gen_idx = 0
                
                # Merge cached and generated embeddings
                for j, embedding in enumerate(batch_embeddings):
                    if embedding is None:
                        embedding = generated[gen_idx]
                        batch_embeddings[j] = embedding
                        if self.cache:
                            self.cache.store(batch_texts[j], embedding)
                        gen_idx += 1
            
            embeddings.extend(batch_embeddings)
        
        return embeddings
    
    def generate_single(self, text: str) -> np.ndarray:
        """Generate embedding for a single text string."""
        return self.generate([text])[0]
