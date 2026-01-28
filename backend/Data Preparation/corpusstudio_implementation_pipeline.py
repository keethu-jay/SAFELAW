"""
CorpusStudio Implementation Pipeline

Main pipeline module for implementing CorpusStudio functionality with court judgment datasets.
This module provides the retriever interface and example usage patterns.
"""

import asyncio
import logging
import os
from typing import List, Dict, Any

from corpus_studio_initialization import (
    Document,
    EmbeddingModel,
    SentenceStore,
    SupabaseSentenceStore,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SentenceRetriever:
    """
    A class that retrieves sentences from a corpus.
    """

    def __init__(
        self, embedding_model: EmbeddingModel, sentence_store: SentenceStore
    ) -> None:
        self.embedding_model = embedding_model
        self.sentence_store = sentence_store

    async def query(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        offset = kwargs.get("offset", 0)
        title = kwargs.get("title", "")

        computed_query = f"{title} {query}" if title else query
        
        # Run embedding in a thread to avoid blocking the event loop
        embedded_query = await asyncio.to_thread(self.embedding_model.embed, computed_query)

        # Get target documents from search
        targets = await asyncio.to_thread(self.sentence_store.search, embedded_query, **kwargs)

        # Use asyncio.gather to execute get_offset concurrently
        target_sentences = await asyncio.gather(*[
            asyncio.to_thread(self.sentence_store.get_offset, doc.id, offset) 
            for doc in targets
        ])

        # Use asyncio.gather to get next and previous sentences concurrently
        results = await asyncio.gather(*[
            asyncio.gather(
                asyncio.to_thread(self.sentence_store.get_next_sentence, target_sentence.id),
                asyncio.to_thread(self.sentence_store.get_previous_sentence, target_sentence.id)
            )
            for target_sentence in target_sentences
        ])

        # Combine results
        res = [
            {
                "target_sentence": target_sentence,
                "next_sentence": next_sentence,
                "previous_sentence": prev_sentence,
            }
            for target_sentence, (next_sentence, prev_sentence) in zip(target_sentences, results)
        ]

        return res

async def main():
    """Example usage of the pipeline."""
    # Load environment variables
    from pathlib import Path
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    try:
                        key, value = line.split("=", 1)
                        os.environ[key] = value
                    except ValueError:
                        pass

    try:
        from supabase import create_client
        
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            logger.error("Missing SUPABASE_URL or SUPABASE_KEY")
            return

        supabase = create_client(supabase_url, supabase_key)
        
        # Initialize components
        embedding_model = EmbeddingModel(model_name="kanon-2-embedder")
        sentence_store = SupabaseSentenceStore(supabase)
        
        retriever = SentenceRetriever(
            embedding_model=embedding_model,
            sentence_store=sentence_store
        )
        
        # Example query
        query_text = "breach of contract"
        print(f"Querying for: '{query_text}'...")
        results = await retriever.query(query_text, n_results=3)
        
        for i, res in enumerate(results):
            target = res["target_sentence"]
            print(f"\nResult {i+1}:")
            print(f"  Target: {target.text[:100]}...")
            print(f"  Doc ID: {target.doc_id}")
            
    except Exception as e:
        logger.error(f"Error in pipeline: {e}")

if __name__ == "__main__":
    asyncio.run(main())
