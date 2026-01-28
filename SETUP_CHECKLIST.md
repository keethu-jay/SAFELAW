# Setup Checklist for Text Summarization Feature

Follow these steps to get the text summarization feature working:

## ✅ Step 1: Create Database Table

You **MUST** run the SQL schema in Supabase to create the `text_highlights` table:

1. Go to your Supabase project dashboard
2. Navigate to **SQL Editor**
3. Copy and paste the contents of `backend/text_highlights_schema.sql`
4. Click **Run** to execute the SQL

**File location:** `backend/text_highlights_schema.sql`

This creates:
- `text_highlights` table
- Row-level security policies
- Indexes for performance

## ✅ Step 2: Set Up Backend Environment Variables

Create a `.env` file in the `backend/` directory with:

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key
OPENAI_API_KEY=sk-your-openai-api-key
```

**Important:** Use the **Service Role Key** (not the anon key) for `SUPABASE_KEY` in the backend.

## ✅ Step 3: Install Backend Dependencies

Navigate to the backend directory and install Python packages:

```bash
cd backend
pip install -r requirements.txt
```

## ✅ Step 4: Start the Backend Server

Run the FastAPI server:

```bash
cd backend
python server/server.py
```

Or if you're in the backend directory:

```bash
python -m server.server
```

The server should start on `http://localhost:8000`

You should see output like:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## ✅ Step 5: Verify Backend is Running

Test the health endpoint:

```bash
curl http://localhost:8000/api/health
```

Or open in browser: `http://localhost:8000/api/health`

You should see: `{"status":"ok"}`

## ✅ Step 6: Start Frontend (if not already running)

In a separate terminal:

```bash
cd frontend
npm run dev
```

## ✅ Step 7: Test the Feature

1. Go to the Reader page in your app
2. Paste some text in the text box
3. Highlight a portion of text
4. Click "Summarize Highlighted Text"
5. Wait for the summarization (may take a few seconds)

## 🔍 Troubleshooting

### Error: "Failed to store highlight in database"

**Cause:** The `text_highlights` table doesn't exist or RLS policies are blocking access.

**Solution:**
- Make sure you ran the SQL schema (Step 1)
- Check that the table exists in Supabase: Go to **Table Editor** → Look for `text_highlights`
- Verify RLS policies are set correctly

### Error: "Connection refused" or "Failed to fetch"

**Cause:** Backend server is not running or frontend can't reach it.

**Solution:**
- Make sure the backend server is running (Step 4)
- Check that it's running on port 8000
- Verify `VITE_API_URL` in frontend `.env` matches your backend URL (default: `http://localhost:8000`)

### Error: "OPENAI_API_KEY environment variable must be set"

**Cause:** Backend can't find the OpenAI API key.

**Solution:**
- Check your `.env` file in the `backend/` directory
- Make sure `OPENAI_API_KEY` is set correctly
- Restart the backend server after adding/changing environment variables

### Error: "Summarization failed: ..."

**Cause:** OpenAI API call is failing.

**Solution:**
- Verify your OpenAI API key is valid
- Check that you have credits/quota in your OpenAI account
- Check the backend console for detailed error messages

### Error: "SUPABASE_URL and SUPABASE_KEY environment variables must be set"

**Cause:** Backend can't find Supabase credentials.

**Solution:**
- Check your `.env` file in the `backend/` directory
- Make sure both `SUPABASE_URL` and `SUPABASE_KEY` are set
- Restart the backend server after adding/changing environment variables

## 📝 Quick Verification Commands

```bash
# Check if backend is running
curl http://localhost:8000/api/health

# Check backend logs for errors
# (Look at the terminal where you started the server)

# Check browser console for frontend errors
# (Open DevTools → Console tab)
```

## 🎯 Common Issues

1. **Table doesn't exist** → Run the SQL schema
2. **Backend not running** → Start the server (Step 4)
3. **Wrong API key** → Check your `.env` file
4. **CORS errors** → Backend CORS is already configured, but make sure backend is running
5. **Port already in use** → Change port in `server.py` or kill the process using port 8000

