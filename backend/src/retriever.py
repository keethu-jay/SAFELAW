"""
CorpusStudio Implementation Pipeline

Main pipeline module for implementing CorpusStudio functionality with court judgment datasets.
This module provides the retriever interface and example usage patterns.
"""

import asyncio
import logging
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os

from src.embedding_helper import EmbeddingModel
from src.stores import SentenceStore, SupabaseSentenceStore

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
        # Original:
        # targets = await asyncio.to_thread(self.sentence_store.search, embedded_query, **kwargs)
        # Use 0.0 to show all results regardless of similarity (mini corpus testing).
        # Change back to 0.2 to filter out low-similarity results when using full corpus.
        match_threshold = kwargs.pop("match_threshold", 0.0)
        targets = await asyncio.to_thread(self.sentence_store.search, embedded_query, match_threshold=match_threshold, **kwargs)

        # Preserve similarity from search results before fetching offset sentences.
        # Original code below fetched offsets without preserving similarity.
        # similarity_by_id = {doc.id: (doc.similarity or 0.0) for doc in targets}
        similarity_by_id = {doc.id: (doc.similarity or 0.0) for doc in targets}

        # Use asyncio.gather to execute get_offset concurrently
        # Original:
        # target_sentences = await asyncio.gather(*[
        #     asyncio.to_thread(self.sentence_store.get_offset, doc.id, offset)
        #     for doc in targets
        # ])
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
        # Include similarity in API response for Writer semantic scores.
        # Use targets[i].id (matched doc id) not target_sentence.id - when offset != 0,
        # target_sentence is the context doc; similarity belongs to the match.
        res = [
            {
                "target_sentence": target_sentence,
                "next_sentence": next_sentence,
                "previous_sentence": prev_sentence,
                "similarity": similarity_by_id.get(targets[i].id, 0.0),
            }
            for i, (target_sentence, (next_sentence, prev_sentence)) in enumerate(zip(target_sentences, results))
        ]

        return res

# ============================================================================
# API Setup
# ============================================================================

# Initialize FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request model
class RetrieveRequest(BaseModel):
    query: str
    court: str = "supreme"

# Global variable to hold the retriever instance
global_retriever = None

@app.on_event("startup")
async def startup_event():
    global global_retriever
    # Initialize components on startup
    try:
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

        from supabase import create_client
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_KEY")
        
        if supabase_url and supabase_key:
            supabase = create_client(supabase_url, supabase_key)
            embedding_model = EmbeddingModel(model_name="kanon-2-embedder")
            sentence_store = SupabaseSentenceStore(supabase)
            global_retriever = SentenceRetriever(embedding_model, sentence_store)
            logger.info("✅ Retriever API initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize retriever: {e}")

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "SafeLaw Retriever API is running"}

@app.post("/api/retrieve")
async def retrieve_endpoint(request: RetrieveRequest):
    """Endpoint to retrieve similar sentences."""
    if not global_retriever:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    logger.info(f"Processing query: {request.query[:50]}...")
    results = await global_retriever.query(request.query, n_results=10)
    return results

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
    # Run the server
    uvicorn.run(app, host="0.0.0.0", port=8000)
