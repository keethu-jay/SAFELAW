# Retraining CorpusStudio on Legal Documents

## You're Correct! No Model Training Required

**CorpusStudio does NOT train an AI model.** Instead, it's a **database lookup system** that uses **pre-trained embedding models** to find semantically similar sentences.

---

## How It Actually Works

### 1. Pre-trained Embedding Model (No Training Needed)

The system uses a **pre-trained embedding model** (like Voyage AI, OpenAI, etc.) that's already been trained on massive text datasets. You don't train this - you just use it via API.

**Code Location**: `corpusstudio/src/corpusstudio/embedding_helper.py`

```python
class EmbeddingModel:
    def embed(self, sentence: str) -> List[float]:
        response = embedding(
            model=self.model_name,  # e.g., "voyage/voyage-3-large"
            input=[sentence], 
            api_key=self.api_key
        )
        return response.data[0]["embedding"]  # Returns vector like [0.123, -0.456, ...]
```

**What this does:**
- Calls an API to convert text → embedding vector
- The embedding model is already trained (by Voyage/OpenAI/etc.)
- You just use it - no training required

---

### 2. Data Processing (Not Training)

To "retrain" on legal documents, you're actually just:

1. **Processing documents** (splitting into sentences)
2. **Generating embeddings** (using the pre-trained model)
3. **Storing in database** (for fast lookup)

**No model training happens here!**

---

## What You'd Do to Switch to Legal Documents

### Step 1: Process Legal Documents

Instead of processing research papers, you'd process legal documents:

```python
# Parse legal documents (contracts, case law, statutes, etc.)
legal_docs = parse_legal_documents(your_legal_files)

# Split into sentences (same as with papers)
sentences = split_into_sentences(legal_docs)
```

**Code Location**: `notebooks/create_dataset_from_html.ipynb` (adapt for legal docs)

---

### Step 2: Generate Embeddings (Using Pre-trained Model)

Use the **same pre-trained embedding model** to generate embeddings for legal sentences:

```python
embedding_model = EmbeddingModel(
    model_name="voyage/voyage-3-large",  # Same model - no retraining!
    api_key=API_KEY
)

# Generate embeddings for each sentence
sentences_df['embedding'] = sentences_df.apply(
    lambda row: embedding_model.embed(row['sentences']), 
    axis=1
)
```

**Key Point**: You're using the same pre-trained model. It works on legal text because it was trained on diverse text including legal content.

---

### Step 3: Store in Database

Store the legal document sentences with their embeddings:

```python
records = []
for _, row in sentences_df.iterrows():
    record = {
        "doc_id": row['docid'],           # Legal document ID
        "text": row['sentences'],          # Sentence text
        "section_title": row['section_title'],  # e.g., "Article 1", "Clause 3"
        "section_number": row['section_number'],
        "sentence_index": row['sentence_index'],
        "global_index": row['global_index'],
        "embedding": row['embedding']      # Pre-computed embedding vector
    }
    records.append(record)

# Upload to database
supabase.table("Document").insert(records).execute()
```

**Code Location**: `notebooks/create_dataset_from_html.ipynb` (lines ~850-1000)

---

### Step 4: Query (Database Lookup)

When users query, it's just a **database lookup** using vector similarity:

```python
# User types: "The party shall indemnify..."
query_embedding = embedding_model.embed("The party shall indemnify...")

# Database lookup - finds similar sentences
results = supabase.rpc(
    "match_documents",
    {
        "query_embedding": query_embedding,  # Vector to search for
        "similarity_threshold": 0.78,
        "max_results": 25
    }
).execute()
```

**Code Location**: `corpusstudio/src/corpusstudio/stores.py` (lines 41-54)

**What happens:**
- Converts query to embedding (using pre-trained model)
- Searches database for similar embeddings (vector similarity search)
- Returns matching sentences from legal documents

**No training involved - just database lookup!**

---

## The Complete Picture

```
┌─────────────────────────────────────────────────────────────┐
│  PRE-TRAINED EMBEDDING MODEL (Voyage AI, OpenAI, etc.)     │
│  - Already trained on massive text corpus                   │
│  - Works on any domain (papers, legal docs, etc.)          │
│  - You just use it via API - NO TRAINING                    │
└─────────────────────────────────────────────────────────────┘
                        │
                        │ (used for both)
                        │
        ┌───────────────┴───────────────┐
        │                               │
        ▼                               ▼
┌──────────────────┐          ┌──────────────────┐
│  DATA PROCESSING │          │   QUERY TIME      │
│                  │          │                   │
│ Legal Documents  │          │ User Query        │
│   → Sentences    │          │   → Embedding     │
│   → Embeddings   │          │   → DB Search     │
│   → Database    │          │   → Results       │
└──────────────────┘          └──────────────────┘
```

---

## Key Points

### ✅ What You DO:
1. **Process documents** - Split legal docs into sentences
2. **Generate embeddings** - Use pre-trained model to create vectors
3. **Store in database** - Save sentences + embeddings
4. **Query database** - Use vector similarity search

### ❌ What You DON'T Do:
1. **Train a model** - The embedding model is pre-trained
2. **Fine-tune anything** - No fine-tuning needed
3. **Retrain embeddings** - Same model works for all domains

---

## Why This Works

The pre-trained embedding models (like Voyage-3-large) were trained on:
- Diverse text from the internet
- Academic papers
- Legal documents
- News articles
- Books
- And more...

So they already understand legal language! You just:
- Use the model to generate embeddings for your legal documents
- Store them in a database
- Search using vector similarity

---

## Example: Switching to Legal Documents

```python
# 1. Process legal documents
legal_docs = load_legal_documents("contracts/", "case_law/", "statutes/")

# 2. Split into sentences (same process as papers)
sentences = split_legal_docs_into_sentences(legal_docs)

# 3. Generate embeddings (using SAME pre-trained model)
embedding_model = EmbeddingModel("voyage/voyage-3-large", API_KEY)
embeddings = [embedding_model.embed(s) for s in sentences]

# 4. Store in database
for sentence, embedding in zip(sentences, embeddings):
    supabase.table("Document").insert({
        "doc_id": doc_id,
        "text": sentence,
        "embedding": embedding,
        # ... other metadata
    }).execute()

# 5. Query (same as before - just database lookup!)
query = "The party shall indemnify..."
results = retriever.query(query)  # Finds similar legal sentences
```

---

## Database vs. Model Training

| Aspect | Model Training | CorpusStudio Approach |
|--------|---------------|------------------------|
| **What it does** | Trains neural network weights | Stores embeddings in database |
| **Time required** | Days/weeks | Hours (just processing) |
| **Computational cost** | High (GPUs, training time) | Low (API calls, database storage) |
| **Domain adaptation** | Requires retraining | Just process new documents |
| **Query speed** | Model inference | Fast database lookup |
| **Storage** | Model weights (GBs) | Embeddings + text (MBs/GBs) |

---

## Summary

**To "retrain" CorpusStudio on legal documents:**

1. ✅ Process legal documents (split into sentences)
2. ✅ Generate embeddings using pre-trained model (no training!)
3. ✅ Store in database
4. ✅ Query using vector similarity search

**You're NOT training a model - you're just:**
- Processing new documents
- Using a pre-trained embedding model
- Storing results in a database
- Doing fast database lookups

**It's a database lookup system, not a trained model!**

---

## Technical Details

### Vector Similarity Search

The database uses **PostgreSQL with pgvector extension** for fast similarity search:

```sql
-- Example of what happens in the database
SELECT * FROM "Document"
WHERE 1 - (embedding <=> query_embedding) > similarity_threshold
ORDER BY embedding <=> query_embedding
LIMIT max_results;
```

This is just a **database query** - no model inference, no training, just fast vector math!

### Embedding Model Options

You can use any pre-trained embedding model:
- `voyage/voyage-3-large` (1024 dimensions)
- `text-embedding-3-large` (OpenAI, 3072 dimensions)
- `text-embedding-ada-002` (OpenAI, 1536 dimensions)
- Any other embedding API

**All are pre-trained - you just use them!**

---

## Conclusion

CorpusStudio is essentially a **semantic search database**:
- Uses pre-trained embedding models (no training)
- Stores sentence embeddings in a database
- Performs fast vector similarity searches
- Returns semantically similar sentences

To switch domains (papers → legal docs), you just process new documents and store them. No model training required!


