# Visual Flow: How CorpusStudio Uses Papers from Dataset

## 🎯 Overview

This document provides a visual guide to the code sections involved in retrieving and using papers from the dataset.

---

## 📊 Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER QUERY                                   │
│              "Find sentences about X"                           │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  📁 retriever.py:24-29                                         │
│  SentenceRetriever.query()                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ # User types a sentence (title is optional)             │  │
│  │ computed_query = f"{title} {query}" if title else query│  │
│  │ embedded_query = embedding_model.embed(computed_query)   │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  📁 embedding_helper.py:17-21                                   │
│  EmbeddingModel.embed()                                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ response = embedding(                                    │  │
│  │     model=self.model_name,                               │  │
│  │     input=[sentence],                                    │  │
│  │     api_key=self.api_key                                 │  │
│  │ )                                                        │  │
│  │ return response.data[0]["embedding"]                     │  │
│  └──────────────────────────────────────────────────────────┘  │
│  Returns: [0.123, -0.456, 0.789, ...] (1024 dimensions)        │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  📁 retriever.py:32                                            │
│  targets = sentence_store.search(embedded_query, **kwargs)     │
│  └──────────────────────────────────────────────────────────┘  │
│                            │                                    │
│                            ▼                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  📁 stores.py:41-54                                      │  │
│  │  SupabaseSentenceStore.search()                          │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │ results = supabase.rpc(                           │  │  │
│  │  │     "match_documents",                            │  │  │
│  │  │     {                                             │  │  │
│  │  │         "query_embedding": embedding_vector,      │  │  │
│  │  │         "similarity_threshold": match_threshold,  │  │  │
│  │  │         "max_results": n_results,                 │  │  │
│  │  │     },                                            │  │  │
│  │  │ ).execute()                                       │  │  │
│  │  │                                                    │  │  │
│  │  │ return [Document(**r) for r in results.data]     │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
│  Returns: List[Document] (similar sentences from papers)        │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  📁 retriever.py:35-38                                         │
│  Get target sentences with offset                              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ target_sentences = await asyncio.gather(*[              │  │
│  │     asyncio.to_thread(                                  │  │
│  │         sentence_store.get_offset, doc.id, offset       │  │
│  │     )                                                   │  │
│  │     for doc in targets                                  │  │
│  │ ])                                                      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                            │                                    │
│                            ▼                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  📁 stores.py:56-92                                      │  │
│  │  SupabaseSentenceStore.get_offset()                     │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │ # Get current sentence                             │  │  │
│  │  │ res = supabase.table("Document")                   │  │  │
│  │  │     .select("*").eq("id", id).execute()            │  │  │
│  │  │                                                     │  │  │
│  │  │ # Calculate offset                                 │  │  │
│  │  │ new_index = current_sentence_index + offset        │  │  │
│  │  │                                                     │  │  │
│  │  │ # Get sentence at offset                           │  │  │
│  │  │ res = supabase.table("Document")                   │  │  │
│  │  │     .select("*")                                   │  │  │
│  │  │     .eq("doc_id", ...)      # Same paper          │  │  │
│  │  │     .eq("section_title", ...) # Same section      │  │  │
│  │  │     .eq("sentence_index", new_index)               │  │  │
│  │  │     .execute()                                     │  │  │
│  │  │                                                     │  │  │
│  │  │ return Document(...)                               │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  📁 retriever.py:43-49                                         │
│  Get context (next/previous sentences)                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ results = await asyncio.gather(*[                       │  │
│  │     asyncio.gather(                                     │  │
│  │         get_next_sentence(target_sentence.id),         │  │
│  │         get_previous_sentence(target_sentence.id)      │  │
│  │     )                                                   │  │
│  │     for target_sentence in target_sentences            │  │
│  │ ])                                                      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                            │                                    │
│                            ├──────────────────┐                 │
│                            ▼                  ▼                 │
│  ┌──────────────────────────────┐  ┌──────────────────────────┐│
│  │ 📁 stores.py:15-16           │  │ 📁 stores.py:18-19       ││
│  │ get_next_sentence(id)        │  │ get_previous_sentence(id)││
│  │   return get_offset(id, 1)   │  │   return get_offset(id,-1)││
│  └──────────────────────────────┘  └──────────────────────────┘│
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  📁 retriever.py:53-60                                         │
│  Combine results                                               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ res = [                                                   │  │
│  │     {                                                     │  │
│  │         "target_sentence": target_sentence,              │  │
│  │         "next_sentence": next_sentence,                  │  │
│  │         "previous_sentence": prev_sentence,              │  │
│  │     }                                                     │  │
│  │     for target_sentence, (next_sentence, prev_sentence)  │  │
│  │     in zip(target_sentences, results)                    │  │
│  │ ]                                                         │  │
│  │                                                           │  │
│  │ return res                                                │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FINAL RESULTS                                │
│  List[Dict[str, Document]]                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ [                                                         │  │
│  │   {                                                       │  │
│  │     "target_sentence": Document(...),                    │  │
│  │     "next_sentence": Document(...),                      │  │
│  │     "previous_sentence": Document(...)                   │  │
│  │   },                                                      │  │
│  │   ...                                                     │  │
│  │ ]                                                         │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔍 Key Code Sections Highlighted

### 1. Main Query Entry Point

**File**: `corpusstudio/src/corpusstudio/retriever.py`

```python
# ═══════════════════════════════════════════════════════════════
# LINE 24-29: Query Processing and Embedding
# ═══════════════════════════════════════════════════════════════
async def query(self, query: str, **kwargs) -> List[Dict[str, Document]]:
    offset = kwargs.get("offset", 0)
    title = kwargs.get("title", "")  # Optional - typically empty

    # User types a sentence, which gets embedded
    computed_query = f"{title} {query}" if title else query
    embedded_query = self.embedding_model.embed(computed_query)  # ← EMBEDDING STEP

    # ═══════════════════════════════════════════════════════════════
    # LINE 32: Vector Similarity Search
    # ═══════════════════════════════════════════════════════════════
    targets = self.sentence_store.search(embedded_query, **kwargs)  # ← SEARCH STEP

    # ═══════════════════════════════════════════════════════════════
    # LINE 35-38: Get Target Sentences
    # ═══════════════════════════════════════════════════════════════
    target_sentences = await asyncio.gather(*[
        asyncio.to_thread(self.sentence_store.get_offset, doc.id, offset)  # ← TARGET RETRIEVAL
        for doc in targets
    ])

    # ═══════════════════════════════════════════════════════════════
    # LINE 43-49: Get Context (Next/Previous Sentences)
    # ═══════════════════════════════════════════════════════════════
    results = await asyncio.gather(*[
        asyncio.gather(
            asyncio.to_thread(self.sentence_store.get_next_sentence, target_sentence.id),      # ← NEXT SENTENCE
            asyncio.to_thread(self.sentence_store.get_previous_sentence, target_sentence.id)   # ← PREVIOUS SENTENCE
        )
        for target_sentence in target_sentences
    ])

    # ═══════════════════════════════════════════════════════════════
    # LINE 53-60: Result Assembly
    # ═══════════════════════════════════════════════════════════════
    res = [
        {
            "target_sentence": target_sentence,
            "next_sentence": next_sentence,
            "previous_sentence": prev_sentence,
        }
        for target_sentence, (next_sentence, prev_sentence) in zip(target_sentences, results)
    ]

    return res
```

---

### 2. Embedding Generation

**File**: `corpusstudio/src/corpusstudio/embedding_helper.py`

```python
# ═══════════════════════════════════════════════════════════════
# LINE 17-21: Convert Text to Embedding Vector
# ═══════════════════════════════════════════════════════════════
def embed(self, sentence: str) -> List[float]:
    response = embedding(
        model=self.model_name,        # e.g., "voyage/voyage-3-large"
        input=[sentence],             # Query text
        api_key=self.api_key
    )
    return response.data[0]["embedding"]  # ← Returns 1024-dim vector
```

**What happens:**
- Text query → Embedding API → Vector representation
- Same model used for storing and querying ensures compatibility

---

### 3. Vector Similarity Search

**File**: `corpusstudio/src/corpusstudio/stores.py`

```python
# ═══════════════════════════════════════════════════════════════
# LINE 41-54: Search Database for Similar Sentences
# ═══════════════════════════════════════════════════════════════
def search(self, embedding_vector: List[float], **kwargs) -> List[Document]:
    n_results = kwargs.get("n_results", 10)
    match_threshold = kwargs.get("match_threshold", 0.9)

    # ═══════════════════════════════════════════════════════════════
    # LINE 45-52: Call Supabase RPC Function
    # ═══════════════════════════════════════════════════════════════
    results = self.supabase.rpc(
        "match_documents",                    # ← Database function for vector search
        {
            "query_embedding": embedding_vector,      # ← Query embedding
            "similarity_threshold": match_threshold,  # ← Minimum similarity (0.0-1.0)
            "max_results": n_results,                 # ← Max results to return
        },
    ).execute()

    # ═══════════════════════════════════════════════════════════════
    # LINE 54: Convert to Document Objects
    # ═══════════════════════════════════════════════════════════════
    return [Document(**r) for r in results.data]  # ← Returns list of matching sentences
```

**What happens:**
- Calls PostgreSQL function `match_documents` (uses pgvector extension)
- Performs cosine similarity search on embeddings
- Returns documents with similarity above threshold
- Results are sorted by similarity (most similar first)

---

### 4. Context Retrieval

**File**: `corpusstudio/src/corpusstudio/stores.py`

```python
# ═══════════════════════════════════════════════════════════════
# LINE 56-92: Get Sentence with Offset (for context)
# ═══════════════════════════════════════════════════════════════
def get_offset(self, id: int, offset: int) -> Document:
    # ═══════════════════════════════════════════════════════════════
    # LINE 57: Get Current Sentence
    # ═══════════════════════════════════════════════════════════════
    res = self.supabase.table("Document").select("*").eq("id", id).execute()

    if len(res.data) == 0:
        raise ValueError(f"Document with id {id} not found")

    # ═══════════════════════════════════════════════════════════════
    # LINE 63-66: Calculate Offset Index
    # ═══════════════════════════════════════════════════════════════
    current_sentence_index = res.data[0]["sentence_index"]
    new_index = current_sentence_index + offset  # ← +1 for next, -1 for previous

    # ═══════════════════════════════════════════════════════════════
    # LINE 69-75: Query for Sentence at Offset
    # ═══════════════════════════════════════════════════════════════
    res = (
        self.supabase.table("Document")
        .select("*")
        .eq("doc_id", res.data[0]["doc_id"])           # ← Same paper
        .eq("section_title", res.data[0]["section_title"])  # ← Same section
        .eq("sentence_index", new_index)               # ← Offset sentence index
        .execute()
    )

    if not res.data:
        return EmptyDocument()  # ← No sentence at offset (e.g., section boundary)

    # ═══════════════════════════════════════════════════════════════
    # LINE 84-92: Return Document Object
    # ═══════════════════════════════════════════════════════════════
    doc = res.data[0]
    return Document(
        id=doc["id"],
        doc_id=doc["doc_id"],
        text=doc["text"],
        section_title=doc["section_title"],
        section_number=doc["section_number"],
        sentence_index=doc["sentence_index"],
        global_index=doc["global_index"],
    )

# ═══════════════════════════════════════════════════════════════
# LINE 15-16: Get Next Sentence
# ═══════════════════════════════════════════════════════════════
def get_next_sentence(self, id: int) -> Document:
    return self.get_offset(id, 1)  # ← Offset = +1

# ═══════════════════════════════════════════════════════════════
# LINE 18-19: Get Previous Sentence
# ═══════════════════════════════════════════════════════════════
def get_previous_sentence(self, id: int) -> Document:
    return self.get_offset(id, -1)  # ← Offset = -1
```

**Key Design Points:**
- **Same Paper**: `eq("doc_id", ...)` ensures context is from the same paper
- **Same Section**: `eq("section_title", ...)` ensures context is from the same section
- **Sequential Index**: `eq("sentence_index", new_index)` gets the sentence at the offset position
- **Boundary Handling**: Returns `EmptyDocument` if sentence doesn't exist (e.g., at section start/end)

---

## 📦 Data Model

**File**: `corpusstudio/src/corpusstudio/shared/models.py`

```python
# ═══════════════════════════════════════════════════════════════
# LINE 3-14: Document Structure
# ═══════════════════════════════════════════════════════════════
class Document(BaseModel):
    id: int                    # Unique sentence ID in database
    doc_id: str               # Paper identifier (UUID)
    text: str                 # Sentence text
    section_title: str        # Section title (e.g., "Introduction")
    section_number: str       # Section number (e.g., "1.1")
    sentence_index: int       # Index within the section
    global_index: int         # Index within the entire paper

# ═══════════════════════════════════════════════════════════════
# LINE 17-31: Empty Document (for missing sentences)
# ═══════════════════════════════════════════════════════════════
class EmptyDocument(Document):
    def __init__(self):
        super().__init__(
            id=-1,
            doc_id="",
            text="",
            section_title="",
            section_number="",
            sentence_index=0,
            global_index=0,
        )
```

---

## 🔄 Complete Data Flow

### Pre-processing (Data Ingestion)

```
Paper (HTML/PDF)
    ↓
[Parse into sections and paragraphs]
    ↓
[Split into sentences using LLM]
    ↓
[Create embeddings for each sentence]
    ↓
[Store in Supabase Database]
    ├─→ Document table (sentences with embeddings)
    └─→ Source table (paper metadata)
```

### Query Processing (Retrieval)

```
User Query
    ↓
[Embed query] → embedding_helper.py:17-21
    ↓
[Search database] → stores.py:41-54
    ↓
[Get target sentences] → stores.py:56-92
    ↓
[Get context] → stores.py:15-19
    ├─→ Next sentence
    └─→ Previous sentence
    ↓
[Combine results] → retriever.py:53-60
    ↓
Return: List[Dict[str, Document]]
```

---

## 🎯 Key Code Locations Summary

| Step | File | Lines | Description |
|------|------|-------|-------------|
| **1. Query Entry** | `retriever.py` | 24-29 | Main query method, combines title+query, embeds query |
| **2. Embedding** | `embedding_helper.py` | 17-21 | Converts text to embedding vector |
| **3. Vector Search** | `stores.py` | 41-54 | Searches database for similar sentences |
| **4. Target Retrieval** | `stores.py` | 56-92 | Gets target sentences with offset |
| **5. Context Retrieval** | `stores.py` | 15-19 | Gets next/previous sentences |
| **6. Result Assembly** | `retriever.py` | 53-60 | Combines results into final format |
| **7. Data Models** | `shared/models.py` | 3-31 | Document structure definition |

---

## 🧪 Example Usage

```python
from corpusstudio.retriever import SentenceRetriever
from corpusstudio.stores import SupabaseSentenceStore
from corpusstudio.embedding_helper import EmbeddingModel

# Initialize
embedding_model = EmbeddingModel(
    model_name="voyage/voyage-3-large", 
    api_key=API_KEY
)
sentence_store = SupabaseSentenceStore(supabase)
retriever = SentenceRetriever(embedding_model, sentence_store)

# Query
results = await retriever.query(
    "Figure 2(c) shows the wrist extensor...",
    n_results=25,
    match_threshold=0.78
)

# Process results
for result in results:
    print(f"Target: {result['target_sentence'].text}")
    print(f"Previous: {result['previous_sentence'].text}")
    print(f"Next: {result['next_sentence'].text}")
    print(f"Section: {result['target_sentence'].section_title}")
    print(f"Paper: {result['target_sentence'].doc_id}")
```

---

## 📝 Notes

1. **Async Processing**: Uses `asyncio.gather()` for concurrent database queries
2. **Section Boundaries**: Context retrieval respects section boundaries for semantic coherence
3. **Vector Search**: Uses PostgreSQL pgvector extension for fast similarity search
4. **Embedding Consistency**: Same embedding model must be used for storage and retrieval
5. **Error Handling**: Returns `EmptyDocument` when sentences don't exist (e.g., at boundaries)

---

## 🗂️ Database Schema

### Document Table
- `id`: Primary key (sentence ID)
- `doc_id`: Paper identifier (UUID)
- `text`: Sentence text
- `section_title`: Section name
- `section_number`: Section number
- `sentence_index`: Index within section
- `global_index`: Index within paper
- `embedding`: Vector embedding (for similarity search)

### Source Table
- `doc_id`: Paper identifier (UUID)
- `title`: Paper title
- `abstract`: Paper abstract
- `authors`: Paper authors
- `doi_link`: DOI link
- `venue_name`: Publication venue

---

## 🔗 Related Files

- **Main Retrieval**: `corpusstudio/src/corpusstudio/retriever.py`
- **Database Access**: `corpusstudio/src/corpusstudio/stores.py`
- **Embedding Generation**: `corpusstudio/src/corpusstudio/embedding_helper.py`
- **Data Models**: `corpusstudio/src/corpusstudio/shared/models.py`
- **Sentence Splitting**: `corpusstudio/src/corpusstudio/splitter.py`
- **Data Ingestion**: `notebooks/create_dataset_from_html.ipynb`

