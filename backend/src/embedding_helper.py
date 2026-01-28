import os
import logging
from typing import List

# Isaacus legal embedder - using kanon-2-embedder for legal documents
try:
    from isaacus import Isaacus
except ImportError:
    Isaacus = None

# Configure logging
logger = logging.getLogger(__name__)

class EmbeddingModel:
    """
    A class that generates vector embeddings for text sentences.
    Uses Isaacus kanon-2-embedder for legal document embeddings.
    """

    def __init__(self, model_name: str = "kanon-2-embedder", api_key: str = None) -> None:
        """
        Initialize the embedding model.
        
        Args:
            model_name: The embedding model to use (default: kanon-2-embedder for legal documents)
            api_key: Isaacus API key (defaults to ISAACUS_API_KEY env var)
        """
        self.model_name = model_name
        self.api_key = api_key or os.getenv("ISAACUS_API_KEY")
        
        # Switched from OpenAI to Isaacus kanon-2-embedder for legal domain specificity
        if Isaacus is None:
            logger.error("Isaacus SDK not installed. Install with: pip install isaacus")
            self.client = None
        else:
            self.client = Isaacus(api_key=self.api_key)

    def embed(self, sentence: str) -> List[float]:
        """
        Generate an embedding vector for a sentence using Isaacus legal embedder.
        
        Args:
            sentence: The sentence to embed
            
        Returns:
            List[float]: The embedding vector
        """
        if not self.client:
            logger.error("Isaacus client not initialized")
            return [0.0] * 1792  # Isaacus kanon-2 uses 1792 dimensions
        
        try:
            # Using kanon-2-embedder: legal-domain embedder optimized for court documents
            # task="retrieval/document" since we're embedding document chunks/paragraphs
            response = self.client.embeddings.create(
                model=self.model_name,
                texts=[sentence],
                task="retrieval/document"  # Task type for embedding documents (not queries)
            )
            # Extract embedding from response
            return response.embeddings[0].embedding
        except Exception as e:
            logger.error(f"Error generating embedding with Isaacus: {e}")
            # Fallback to zero vector if API fails
            return [0.0] * 1792  # Isaacus kanon-2 uses 1792 dimensions