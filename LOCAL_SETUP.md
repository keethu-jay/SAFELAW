# Running SafeLaw on Your Own Machine

If you've just cloned the repo or downloaded the zip from GitHub, here's everything you need to get it running on your machine.

---

## What You'll Need

- **Python 3.10+** (for the backend)
- **Node.js 18+** (for the frontend)
- **A Supabase project** (free tier works)
- **API keys**: OpenAI, Isaacus (for embeddings)

---

## 1. Database Setup (Supabase)

You'll need a Supabase project (free tier is fine). Go to [supabase.com](https://supabase.com), create one, then head to the SQL Editor and run these in order.

### Tables for the app (required)

**text_highlights** – stores highlighted text and summaries from the Reader:

```sql
CREATE TABLE IF NOT EXISTS text_highlights (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    original_text TEXT,
    highlighted_text TEXT NOT NULL,
    summarization TEXT,
    sent_at TIMESTAMPTZ DEFAULT NOW(),
    summarized_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_text_highlights_user_id ON text_highlights(user_id);
```

**profiles** – user profiles (created on first login if missing):

```sql
CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name TEXT,
    role TEXT DEFAULT 'Legal User'
);
```

### Tables for RAG retrieval (optional)

If you want the Writer's "get suggestions" feature to work, you need the corpus tables. The full SQL is in `backend/small_corpus/README.md` – run the Schema, Classification Migration, and Context Migration sections in order. You'll also need to run the ingestion scripts to populate the data (details are in that README).

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

Create a file `backend/.env` with:

```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key
OPENAI_API_KEY=sk-your-openai-key
ISAACUS_API_KEY=your-isaacus-key
```

- **SUPABASE_URL**: Project URL from Supabase Dashboard → Settings → API
- **SUPABASE_KEY**: Use the **service role key** (not anon) for the backend
- **OPENAI_API_KEY**: From [platform.openai.com](https://platform.openai.com) – used for summarization
- **ISAACUS_API_KEY**: From Isaacus – used for embeddings. If you don’t have it, retrieval won’t work but the app will still start

Optional: `RAG_CORPUS=mini_paragraphs` or `main` to switch corpus. Default is `main`.

---

## 3. Frontend Setup

### Install dependencies

```bash
cd frontend
npm install
```

### Create `frontend/.env`

Create `frontend/.env` with:

```
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
VITE_API_URL=http://localhost:8000
```

- **VITE_SUPABASE_URL**: Same as backend
- **VITE_SUPABASE_ANON_KEY**: The **anon/public** key (not service role) – safe for the browser
- **VITE_API_URL**: Backend URL. `http://localhost:8000` is fine for local dev.

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
Change the port in `server/server.py` (last line) or stop whatever’s using 8000.
