# Running SafeLaw on Your Own Machine

If you've just cloned the repo or downloaded the zip from GitHub, here's everything you need to get it running on your machine. For a walkthrough of the directory structure, see [STRUCTURE.md](STRUCTURE.md).

---

## What You'll Need

- **Python 3.10+** (for the backend)
- **Node.js 18+** (for the frontend)
- **A Supabase project** (free tier works)
- **API keys**: OpenAI, Isaacus (for embeddings)

---

## 1. Database Setup (Supabase)

You'll need a Supabase project (free tier is fine). Go to [supabase.com](https://supabase.com), create one, then head to the SQL Editor.

**All required SQL is in [SUPABASE_SQL.md](SUPABASE_SQL.md).** Run sections 1–4 in order:

1. **App tables** – text_highlights, profiles (Reader, auth)
2. **Corpus schema** – mini paragraphs, sentences, KNN match functions
3. **Classification migration** – classification columns, indiv_class table
4. **Context migration** – context_tag, case_summary tables (for sentence comparison v2–v4)

After running the SQL, populate the corpus tables by running the ingestion scripts (see `backend/small_corpus/README.md`).

---

## 2. Backend Setup

### Create a virtual environment

```bash
cd backend
python -m venv .venv
```

**Windows:**
```powershell
.venv\Scripts\activate
```

**Mac/Linux:**
```bash
source .venv/bin/activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Create `backend/.env`

Create a file `backend/.env` with (replace placeholders with your values):

```
# Required
SUPABASE_URL=https://YOUR_PROJECT_ID.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
OPENAI_API_KEY=sk-proj-...
ISAACUS_API_KEY=your-isaacus-key

# Optional – corpus for RAG retrieval (default: main)
# RAG_CORPUS=mini_paragraphs
# RAG_CORPUS=mini_sentences
# RAG_CORPUS=main
```

| Variable | Where to get it |
|----------|-----------------|
| **SUPABASE_URL** | Supabase Dashboard → Settings → API → Project URL |
| **SUPABASE_KEY** | Supabase Dashboard → Settings → API → **service role key** (not anon) |
| **OPENAI_API_KEY** | [platform.openai.com](https://platform.openai.com) – used for summarization |
| **ISAACUS_API_KEY** | Isaacus – used for embeddings. Without it, retrieval fails but the app starts |


---

## 3. Frontend Setup

### Install dependencies

```bash
cd frontend
npm install
```

### Create `frontend/.env`

Create `frontend/.env` with (replace placeholders with your values):

```
VITE_SUPABASE_URL=https://YOUR_PROJECT_ID.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
VITE_API_URL=http://localhost:8000
```

| Variable | Where to get it |
|----------|-----------------|
| **VITE_SUPABASE_URL** | Same as backend SUPABASE_URL |
| **VITE_SUPABASE_ANON_KEY** | Supabase Dashboard → Settings → API → **anon/public** key (not service role) |
| **VITE_API_URL** | Backend URL; `http://localhost:8000` for local dev |

---

## 4. Run Both

You need **two terminals** – backend and frontend run separately.

### Terminal 1: Backend

```bash
cd backend
.venv\Scripts\activate   # Windows
# or: source .venv/bin/activate   # Mac/Linux
python server/server.py
```

You should see something like `Uvicorn running on http://0.0.0.0:8000`. Leave this running.

### Terminal 2: Frontend

```bash
cd frontend
npm run dev
```

You should see `Local: http://localhost:5173/`. Open that in your browser.

---

## 5. Create a User (Auth)

Supabase Auth is email/password. In the Supabase Dashboard:

1. Go to **Authentication** → **Users**
2. Click **Add user** → **Create new user**
3. Enter email and password

Use those credentials on the Login page.

---

## Troubleshooting

**"Module not found" in backend**  
Make sure the venv is activated and you ran `pip install -r requirements.txt` inside it.

**Frontend can't reach backend**  
Check that the backend is running on port 8000 and `VITE_API_URL` is `http://localhost:8000`.

**"Failed to store highlight in database"**  
Run the `text_highlights` and `profiles` SQL in Supabase. Make sure you’re using the service role key in the backend `.env`.

**"OPENAI_API_KEY environment variable must be set"**  
Add it to `backend/.env` and restart the backend.

**Retrieval returns nothing or errors**  
You need the corpus tables and data. See `backend/small_corpus/README.md`. You also need `ISAACUS_API_KEY` set.

**Port 8000 already in use**  
Change the port in `server/server.py` (last line) or stop whatever's using 8000.

---

## Adding Your Own Vector Database (e.g. Weaviate)

The retrieval layer uses a **store abstraction** (`SentenceStore` in `backend/src/stores.py`). You can plug in Weaviate, Pinecone, Qdrant, or any other vector DB by implementing this interface.

### 1. Implement the `SentenceStore` interface

Create a new class that subclasses `SentenceStore` and implements:

| Method | Purpose |
|--------|---------|
| `search(embedding_vector, n_results=10, match_threshold=0.0)` | Return a list of `Document` objects (id, doc_id, text, section_title, section_number, sentence_index, global_index, court, decision, similarity) ordered by similarity |
| `get_offset(id, offset)` | Return the `Document` at `sentence_index + offset` within the same doc_id/section_title, or `EmptyDocument()` if not found |

The `Document` model has: `id`, `doc_id`, `text`, `section_title`, `section_number`, `sentence_index`, `global_index`, `court`, `decision`, `similarity`.

### 2. Example: Weaviate store

Create `backend/src/weaviate_store.py`:

```python
from weaviate import Client
from src.stores import SentenceStore, Document, EmptyDocument

class WeaviateSentenceStore(SentenceStore):
    def __init__(self, client: Client, collection: str = "CorpusDocument"):
        self.client = client
        self.collection = collection

    def search(self, embedding_vector, n_results=10, match_threshold=0.0, **kwargs):
        result = self.client.query.get(self.collection, ["doc_id", "text", "section_title", ...]) \
            .with_near_vector({"vector": embedding_vector}) \
            .with_limit(n_results) \
            .do()
        return [Document(id=r["id"], doc_id=r["doc_id"], ..., similarity=r["_additional"]["distance"]) for r in result["data"]["Get"][self.collection]]

    def get_offset(self, id: int, offset: int):
        # Fetch doc by id, then query for doc_id + section_title + (sentence_index + offset)
        ...
```

### 3. Wire it in the server

In `backend/server/server.py`, replace the Supabase store with your store:

```python
# Instead of:
from src.stores import SupabaseSentenceStore
sentence_store = SupabaseSentenceStore(supabase, corpus=rag_corpus)

# Use:
from src.weaviate_store import WeaviateSentenceStore
from weaviate import Client
weaviate_client = Client(os.getenv("WEAVIATE_URL"))
sentence_store = WeaviateSentenceStore(weaviate_client)
```

### 4. Add env vars and ingestion

- Add your DB URL/API key to `backend/.env` (e.g. `WEAVIATE_URL`, `WEAVIATE_API_KEY`).
- You'll need an ingestion script to populate your DB from the classified corpus (paragraphs/sentences with embeddings). The existing ingestion scripts write to Supabase; adapt them or write a new one that inserts into Weaviate.

### 5. Embedding dimension

Embeddings use **1792 dimensions** (kanon-2-embedder). Configure your vector DB schema to match.
