"""
Test script for the vector store system.
Demonstrates and validates the complete pipeline: chunking -> embedding -> storage -> retrieval.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from vector_store.chunking import TextChunk, ChunkingStrategy
from vector_store.embeddings import EmbeddingGenerator
from vector_store.store import VectorStore
from loguru import logger

def test_full_pipeline():
    """Test the complete vector store pipeline."""
    
    # Test data
    documents = [
        "The quick brown fox jumps over the lazy dog. This is a simple test sentence.",
        "Machine learning is a subset of artificial intelligence that focuses on data and algorithms.",
        "Python is a high-level programming language known for its simplicity and readability.",
        "Neural networks are computing systems inspired by biological neural networks.",
        "The lazy dog sleeps while the quick brown fox continues jumping."
    ]
    
    # Initialize components
    logger.info("Initializing vector store components...")
    chunking_strategy = ChunkingStrategy()
    vector_store = VectorStore(store_dir="test_vector_store")
    
    # Create chunks
    logger.info("Creating text chunks...")
    chunks = []
    for i, doc in enumerate(documents):
        chunk = TextChunk(
            text=doc,
            metadata={"doc_id": i, "source": "test_data"}
        )
        chunks.append(chunk)
    
    # Add to vector store
    logger.info("Adding chunks to vector store...")
    chunk_ids = vector_store.add(chunks)
    logger.info(f"Added {len(chunk_ids)} chunks to store")
    
    # Test similarity search
    logger.info("\nTesting similarity search...")
    
    # Test case 1: Search for fox-related content
    query = "Tell me about the fox"
    results = vector_store.search(query, k=2)
    logger.info(f"\nQuery: {query}")
    for idx, score, metadata in results:
        logger.info(f"Score: {score:.4f}")
        logger.info(f"Text: {metadata['text']}")
        logger.info("---")
    
    # Test case 2: Search for AI-related content
    query = "What is artificial intelligence and machine learning?"
    results = vector_store.search(query, k=2)
    logger.info(f"\nQuery: {query}")
    for idx, score, metadata in results:
        logger.info(f"Score: {score:.4f}")
        logger.info(f"Text: {metadata['text']}")
        logger.info("---")
    
    # Test case 3: Search for programming-related content
    query = "Tell me about programming languages"
    results = vector_store.search(query, k=2)
    logger.info(f"\nQuery: {query}")
    for idx, score, metadata in results:
        logger.info(f"Score: {score:.4f}")
        logger.info(f"Text: {metadata['text']}")
        logger.info("---")
    
    # Test persistence
    logger.info("\nTesting persistence...")
    vector_store.save()
    
    # Load and verify
    loaded_store = VectorStore.load("test_vector_store")
    results = loaded_store.search("fox", k=1)
    logger.info("Loaded store search result:")
    if results:
        logger.info(f"Text: {results[0][2]['text']}")
    
    logger.info("\nAll tests completed successfully!")

if __name__ == "__main__":
    test_full_pipeline() 