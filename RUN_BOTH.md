# Running Frontend and Backend

## Important: You Need to Run BOTH Separately

The backend server (`server.py`) and frontend (React app) are **separate applications** that need to run in **different terminals**.

## Setup

### Terminal 1: Backend Server

```bash
# Navigate to backend directory
cd backend

# Make sure virtual environment is activated (if using one)
# On Windows:
.venv\Scripts\activate

# Install dependencies (if not already done)
pip install -r requirements.txt

# Start the backend server
python server/server.py
```

You should see:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Keep this terminal open!** The server needs to keep running.

### Terminal 2: Frontend (React App)

Open a **NEW terminal window**:

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies (if not already done)
npm install

# Start the frontend development server
npm run dev
```

You should see:
```
VITE v7.x.x  ready in xxx ms

➜  Local:   http://localhost:5173/
```

## How They Work Together

1. **Frontend** (React app on port 5173) - The user interface you see in the browser
2. **Backend** (FastAPI server on port 8000) - Handles API requests, database operations, and AI summarization

When you click "Summarize" in the frontend:
- Frontend sends a request to `http://localhost:8000/api/summarize-highlight`
- Backend processes the request, calls OpenAI API, saves to Supabase
- Backend sends response back to frontend
- Frontend displays the result

## Quick Start Scripts

### Windows (PowerShell)

**Backend:**
```powershell
cd backend
.venv\Scripts\activate
python server/server.py
```

**Frontend (new terminal):**
```powershell
cd frontend
npm run dev
```

### Mac/Linux

**Backend:**
```bash
cd backend
source .venv/bin/activate  # if using venv
python server/server.py
```

**Frontend (new terminal):**
```bash
cd frontend
npm run dev
```

## Troubleshooting

### "Module not found" in backend
- Make sure virtual environment is activated
- Run: `pip install -r requirements.txt` **while venv is active**

### Frontend can't connect to backend
- Make sure backend is running on port 8000
- Check browser console for CORS errors
- Verify `VITE_API_URL` in frontend `.env` is `http://localhost:8000`

### Port already in use
- Backend: Change port in `server/server.py` (line 119)
- Frontend: Vite will automatically use next available port

