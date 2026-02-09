import uvicorn
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client
import sys
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables from .env file
# Look for .env in the backend directory; override=True so .env wins over shell
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

# Add parent directory to path to import gptsm_lite
sys.path.append(str(Path(__file__).parent.parent))
from src.gptsm_lite import summarize_text
from src.retriever import SentenceRetriever
from src.stores import SupabaseSentenceStore
from src.embedding_helper import EmbeddingModel

# --- CONFIGURATION ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY environment variables must be set")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable must be set")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Initialize Retrieval Components
# Using OPENAI_API_KEY as fallback if VOYAGE_API_KEY is not set, assuming the EmbeddingModel can handle it or user configures it.
# Original:
# embedding_model = EmbeddingModel(model_name="voyage/voyage-3-large", api_key=os.getenv("VOYAGE_API_KEY", OPENAI_API_KEY))
# Updated: EmbeddingModel uses Isaacus; wire ISAACUS_API_KEY and canonical model name.
embedding_model = EmbeddingModel(model_name="kanon-2-embedder", api_key=os.getenv("ISAACUS_API_KEY"))
# Read RAG_CORPUS: prefer .env file (IDE run configs may override os.getenv)
rag_corpus = ""
if env_path.exists():
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            if line.strip().startswith("RAG_CORPUS="):
                rag_corpus = line.split("=", 1)[1].strip().strip('"').strip("'").lower()
                break
rag_corpus = rag_corpus or os.getenv("RAG_CORPUS", "main").strip().lower() or "main"
print(f"[RAG] env_path={env_path}, exists={env_path.exists()}, RAG_CORPUS={rag_corpus!r}")
sentence_store = SupabaseSentenceStore(supabase, corpus=rag_corpus)
retriever = SentenceRetriever(embedding_model, sentence_store)

app = FastAPI()

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- REQUEST/RESPONSE MODELS ---
class SummarizeRequest(BaseModel):
    text: str
    user_id: str
    original_text: str  # Full text context

class SummarizeResponse(BaseModel):
    summarization: str
    processing_time: float
    original_length: int
    summarized_length: int

class RetrieveRequest(BaseModel):
    query: str
    court: str | None = None

def _safe_float(val):
    """Convert to JSON-serializable float (replace NaN/Inf with 0.0)."""
    if val is None:
        return 0.0
    try:
        f = float(val)
        if f != f or f == float('inf') or f == float('-inf'):  # NaN or Inf
            return 0.0
        return f
    except (TypeError, ValueError):
        return 0.0


# --- ENDPOINT: RETRIEVAL ---
@app.post("/api/retrieve")
async def retrieve_suggestions(request: RetrieveRequest):
    """
    Retrieve similar sentences/paragraphs based on semantic score.
    """
    try:
        # Query the retriever for top 10 results
        results = await retriever.query(request.query, n_results=10)
        
        # Format response for Writer.tsx
        formatted_results = []
        for item in results:
            target = item['target_sentence']
            similarity = item.get("similarity", getattr(target, 'similarity', 0))
            similarity = _safe_float(similarity)
            
            formatted_results.append({
                "target_sentence": {
                    "text": target.text,
                    "doc_id": target.doc_id,
                    "decision": "majority" # Defaulting as decision might not be in Document model
                },
                "similarity": similarity,
                "previous_sentence": {"text": item['previous_sentence'].text} if item['previous_sentence'] else None,
                "next_sentence": {"text": item['next_sentence'].text} if item['next_sentence'] else None
            })
            
        return formatted_results
    except Exception as e:
        print(f"Retrieval error: {e}")
        raise HTTPException(status_code=500, detail=f"Retrieval failed: {str(e)}")

# --- ENDPOINT: TEXT HIGHLIGHT SUMMARIZATION ---
@app.post("/api/summarize-highlight", response_model=SummarizeResponse)
async def summarize_highlight(request: SummarizeRequest):
    """
    Summarize highlighted text using GP-TSM lite and store in database.
    """
    try:
        # Validate input
        if not request.text or not request.text.strip():
            raise HTTPException(status_code=400, detail="Highlighted text cannot be empty")
        
        if not request.user_id:
            raise HTTPException(status_code=400, detail="User ID is required")
        
        # 0. Ensure user profile exists (create if it doesn't)
        try:
            profile_check = supabase.table("profiles").select("id").eq("id", request.user_id).execute()
            if not profile_check.data:
                # Profile doesn't exist, create it
                supabase.table("profiles").insert({
                    "id": request.user_id,
                    "full_name": None,
                    "role": "Legal User"
                }).execute()
        except Exception as profile_error:
            # If profile creation fails, log but continue (might already exist)
            print(f"Note: Profile check/creation issue: {profile_error}")
        
        # 1. Store the highlight request in database (before summarization)
        sent_at = datetime.now(timezone.utc).isoformat()
        highlight_entry = {
            "user_id": request.user_id,
            "original_text": request.original_text,
            "highlighted_text": request.text,
            "summarization": None,  # Will be updated after summarization
            "sent_at": sent_at,
        }
        
        insert_result = supabase.table("text_highlights").insert(highlight_entry).execute()
        
        if not insert_result.data:
            raise HTTPException(status_code=500, detail="Failed to store highlight in database")
        
        highlight_id = insert_result.data[0]["id"]
        
        # 2. Run GP-TSM lite summarization
        try:
            result = summarize_text(request.text, OPENAI_API_KEY)
            summarization = result["summarization"]
            processing_time = result["processing_time"]
        except Exception as e:
            # Update database with error
            supabase.table("text_highlights").update({
                "summarization": f"Error: {str(e)}"
            }).eq("id", highlight_id).execute()
            raise HTTPException(status_code=500, detail=f"Summarization failed: {str(e)}")
        
        # 3. Update database with summarization result
        summarized_at = datetime.now(timezone.utc).isoformat()
        supabase.table("text_highlights").update({
            "summarization": summarization,
            "summarized_at": summarized_at
        }).eq("id", highlight_id).execute()
        
        return SummarizeResponse(
            summarization=summarization,
            processing_time=processing_time,
            original_length=result["original_length"],
            summarized_length=result["summarized_length"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# --- HEALTH CHECK ---
@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
