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
# Look for .env in the backend directory
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Add parent directory to path to import gptsm_lite
sys.path.append(str(Path(__file__).parent.parent))
from src.gptsm_lite import summarize_text

# --- CONFIGURATION ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY environment variables must be set")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable must be set")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

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
