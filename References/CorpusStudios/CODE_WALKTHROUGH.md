# Code Walkthrough: Paper Retrieval Process

This document provides a detailed walkthrough of the code, highlighting the exact sections involved in retrieving and using papers from the dataset.

## File Structure

```
corpusstudio/src/corpusstudio/
├── retriever.py          # Main retrieval logic
├── stores.py             # Database access layer
├── embedding_helper.py   # Embedding generation
├── shared/models.py      # Data models
└── splitter.py           # Sentence splitting (pre-processing)

server/
└── main.py               # API server (if implemented)

notebooks/
└── create_dataset_from_html.ipynb  # Data ingestion pipeline
```

---

## Step-by-Step Code Walkthrough

### Step 1: Query Entry Point

**File**: `corpusstudio/src/corpusstudio/retriever.py`  
**Lines**: 24-62  
**Class**: `SentenceRetriever`

```python
async def query(self, query: str, **kwargs) -> List[Dict[str, Document]]:
```

This is the main entry point for querying papers. It orchestrates the entire retrieval process.

**Key Sections:**

1. **Lines 25-28**: Query preprocessing
   ```python
   offset = kwargs.get("offset", 0)
   title = kwargs.get("title", "")  # Optional - typically empty
   computed_query = f"{title} {query}" if title else query
   ```
   - User types in a sentence (the `query` parameter)
   - Optional `title` parameter can add context, but is usually not provided
   - Optional `offset` parameter for context window adjustment

2. **Line 29**: Query embedding
   ```python
   embedded_query = self.embedding_model.embed(computed_query)
   ```
   - Converts text query to embedding vector
   - Calls `EmbeddingModel.embed()` (see Step 2)

3. **Line 32**: Vector similarity search
   ```python
   targets = self.sentence_store.search(embedded_query, **kwargs)
   ```
   - Searches database for similar sentences
   - Calls `SupabaseSentenceStore.search()` (see Step 3)

4. **Lines 35-38**: Get target sentences with offset
   ```python
   target_sentences = await asyncio.gather(*[
       asyncio.to_thread(self.sentence_store.get_offset, doc.id, offset) 
       for doc in targets
   ])
   ```
   - Retrieves target sentences (with optional offset)
   - Uses async concurrent execution for performance
   - Calls `SupabaseSentenceStore.get_offset()` (see Step 4)

5. **Lines 43-49**: Get context (next/previous sentences)
   ```python
   results = await asyncio.gather(*[
       asyncio.gather(
           asyncio.to_thread(self.sentence_store.get_next_sentence, target_sentence.id),
           asyncio.to_thread(self.sentence_store.get_previous_sentence, target_sentence.id)
       )
       for target_sentence in target_sentences
   ])
   ```
   - Retrieves adjacent sentences for context
   - Executes next/previous queries in parallel
   - Calls `get_next_sentence()` and `get_previous_sentence()` (see Step 5)

6. **Lines 53-60**: Result assembly
   ```python
   res = [
       {
           "target_sentence": target_sentence,
           "next_sentence": next_sentence,
           "previous_sentence": prev_sentence,
       }
       for target_sentence, (next_sentence, prev_sentence) in zip(target_sentences, results)
   ]
   ```
   - Combines target sentence with its context
   - Returns structured results

---

### Step 2: Embedding Generation

**File**: `corpusstudio/src/corpusstudio/embedding_helper.py`  
**Lines**: 8-21  
**Class**: `EmbeddingModel`

```python
class EmbeddingModel:
    def __init__(self, model_name: str, api_key: str) -> None:
        self.model_name = model_name
        self.api_key = api_key

    def embed(self, sentence: str) -> List[float]:
        response = embedding(
            model=self.model_name, input=[sentence], api_key=self.api_key
        )
        return response.data[0]["embedding"]
```

**What it does:**
- Converts text to embedding vector using LiteLLM
- Uses the same model that was used to embed stored sentences
- Returns a list of floats (e.g., 1024 dimensions for Voyage-3-large)

**Called from:**
- `retriever.py:29` - When embedding user queries

---

### Step 3: Vector Similarity Search

**File**: `corpusstudio/src/corpusstudio/stores.py`  
**Lines**: 41-54  
**Class**: `SupabaseSentenceStore`

```python
def search(self, embedding_vector: List[float], **kwargs) -> List[Document]:
    n_results = kwargs.get("n_results", 10)
    match_threshold = kwargs.get("match_threshold", 0.9)

    results = self.supabase.rpc(
        "match_documents",
        {
            "query_embedding": embedding_vector,
            "similarity_threshold": match_threshold,
            "max_results": n_results,
        },
    ).execute()

    return [Document(**r) for r in results.data]
```

**What it does:**
- Calls Supabase RPC function `match_documents`
- Performs vector similarity search using PostgreSQL's pgvector extension
- Filters results by similarity threshold
- Limits results to `max_results` (default: 10)
- Returns list of `Document` objects

**Parameters:**
- `embedding_vector`: Query embedding (from Step 2)
- `similarity_threshold`: Minimum similarity score (0.0-1.0)
- `max_results`: Maximum number of results to return

**Called from:**
- `retriever.py:32` - When searching for similar sentences

**Database Function:**
The `match_documents` RPC function is a PostgreSQL stored procedure (not in this codebase) that:
- Takes query embedding, similarity threshold, and max results
- Uses vector similarity operators (`<=>`) to find similar documents
- Returns documents sorted by similarity
- Filters by similarity threshold

---

### Step 4: Retrieving Target Sentences

**File**: `corpusstudio/src/corpusstudio/stores.py`  
**Lines**: 56-92  
**Class**: `SupabaseSentenceStore`

```python
def get_offset(self, id: int, offset: int) -> Document:
    res = self.supabase.table("Document").select("*").eq("id", id).execute()

    if len(res.data) == 0:
        raise ValueError(f"Document with id {id} not found")

    # Get the current sentence index
    current_sentence_index = res.data[0]["sentence_index"]

    # Calculate the new index with offset
    new_index = current_sentence_index + offset

    # Query for the document with the new sentence index
    res = (
        self.supabase.table("Document")
        .select("*")
        .eq("doc_id", res.data[0]["doc_id"])
        .eq("section_title", res.data[0]["section_title"])
        .eq("sentence_index", new_index)
        .execute()
    )

    if not res.data:
        return EmptyDocument()

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
```

**What it does:**
1. **Lines 57-60**: Retrieves the current sentence by ID
2. **Line 63**: Gets the current sentence's index within its section
3. **Line 66**: Calculates the new index with offset (e.g., +1 for next, -1 for previous)
4. **Lines 69-75**: Queries for the sentence at the new index
   - **Same paper**: `eq("doc_id", ...)`
   - **Same section**: `eq("section_title", ...)`
   - **Offset index**: `eq("sentence_index", new_index)`
5. **Lines 78-79**: Returns `EmptyDocument` if sentence doesn't exist (e.g., at section boundary)
6. **Lines 84-92**: Constructs and returns `Document` object

**Helper Methods:**
- `get_next_sentence(id)`: Calls `get_offset(id, 1)` (line 15-16)
- `get_previous_sentence(id)`: Calls `get_offset(id, -1)` (line 18-19)

**Called from:**
- `retriever.py:36` - When getting target sentences with offset
- `retriever.py:45-46` - When getting next/previous sentences

**Key Design Decision:**
Context retrieval respects section boundaries. Sentences are only retrieved within the same section (`section_title`) and paper (`doc_id`). This ensures semantic coherence.

---

### Step 5: Data Models

**File**: `corpusstudio/src/corpusstudio/shared/models.py`  
**Lines**: 3-31  
**Classes**: `Document`, `EmptyDocument`

```python
class Document(BaseModel):
    id: int
    doc_id: str
    text: str
    section_title: str
    section_number: str
    sentence_index: int
    global_index: int

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

**What it does:**
- Defines the structure of documents returned by the system
- `Document`: Represents a sentence from a paper
- `EmptyDocument`: Represents a missing sentence (e.g., at section boundary)

**Fields:**
- `id`: Unique sentence ID in database
- `doc_id`: Paper identifier (UUID)
- `text`: Sentence text
- `section_title`: Section name (e.g., "Introduction", "Methods")
- `section_number`: Section number (e.g., "1.1", "2.3")
- `sentence_index`: Index within the section
- `global_index`: Index within the entire paper

---

## Data Ingestion Pipeline

### Step 6: Sentence Splitting

**File**: `corpusstudio/src/corpusstudio/splitter.py`  
**Lines**: 23-56  
**Class**: `LLMSentenceSplitter`

```python
class LLMSentenceSplitter(SentenceSplitter):
    def __init__(
        self,
        text: str,
        api_key: str = os.getenv("OPENAI_API_KEY"),
        model_name: str = "openai/gpt-4o-mini",
    ):
        super().__init__(text)
        self.model_name = model_name
        self.api_key = api_key

    def split(self):
        prompt = (
            f"""Split the following text into sentences. Separate each sentence with [EOS] token. Only output the final text with [EOS] tokens and nothing else."""
            f"""Text: {self.text}"""
        )

        response = completion(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.0,
            caching=True,
            api_key=self.api_key,
        )

        return response.choices[0].message.content
```

**What it does:**
- Splits text paragraphs into sentences using LLM
- Uses `[EOS]` token as sentence separator
- Returns text with sentences separated by `[EOS]`

**Used in:**
- `notebooks/create_dataset_from_html.ipynb` - When processing papers
- `scripts/split_sentences.py` - For batch processing

---

### Step 7: Data Storage (Notebook)

**File**: `notebooks/create_dataset_from_html.ipynb`  
**Lines**: ~850-1000 (approximate, based on notebook structure)

**Key Sections:**

1. **Sentence Extraction** (after splitting):
   ```python
   sentences_df = documents_df.explode('sentences')[['docid', 'sentences', 'section_number', 'section_title', 'extra.idx', 'TYPE']]
   sentences_df['paragraph_sentence_index'] = sentences_df.groupby(['docid', 'grp']).cumcount()
   ```
   - Expands sentences from paragraphs
   - Creates sentence indices within sections

2. **Embedding Generation**:
   ```python
   embedding_model = EmbeddingModel(model_name="voyage/voyage-3-large", api_key=API_KEY)
   sentences_df['embedding'] = sentences_df.apply(
       lambda row: embedding_model.embed(f"{row['section_title']} {row['sentences']}" if pd.notna(row['section_title']) else row['sentences']) 
       if pd.notna(row['sentences']) else [], 
       axis=1
   )
   ```
   - Creates embeddings for each sentence
   - Combines section title with sentence for better context

3. **Database Insertion**:
   ```python
   for _, row in sentences_df.iterrows():
       if pd.notna(row['sentences']) and len(row['embedding']) > 0:
           record = {
               "doc_id": row['docid'],
               "text": row['sentences'],
               "section_title": row['section_title'],
               "section_number": row['section_number'],
               "sentence_index": row['paragraph_sentence_index'],
               "global_index": row['paper_global_index'],
               "embedding": row['embedding']
           }
           records.append(record)
   
   # Upload in batches
   for i in range(0, total_records, batch_size):
       batch = records[i:i+batch_size]
       response = supabase.table("Document").insert(batch).execute()
   ```
   - Creates records for each sentence
   - Uploads to Supabase in batches of 100

---

## Complete Call Flow

```
User Query
    ↓
retriever.py:24 (SentenceRetriever.query)
    ├─→ embedding_helper.py:17 (EmbeddingModel.embed) ──→ Query Embedding
    │
    ├─→ stores.py:41 (SupabaseSentenceStore.search) ──→ Vector Search
    │   └─→ Supabase RPC: match_documents ──→ Similar Sentences
    │
    ├─→ stores.py:56 (SupabaseSentenceStore.get_offset) ──→ Target Sentences
    │
    ├─→ stores.py:15 (get_next_sentence)
    │   └─→ stores.py:56 (get_offset with +1) ──→ Next Sentences
    │
    └─→ stores.py:18 (get_previous_sentence)
        └─→ stores.py:56 (get_offset with -1) ──→ Previous Sentences
    ↓
retriever.py:53-60 (Result Assembly)
    ↓
List[Dict[str, Document]] (Results)
```

---

## Key Code Locations Summary

| Step | File | Lines | Function/Class |
|------|------|-------|----------------|
| Query Entry | `retriever.py` | 24-62 | `SentenceRetriever.query()` |
| Embedding | `embedding_helper.py` | 17-21 | `EmbeddingModel.embed()` |
| Vector Search | `stores.py` | 41-54 | `SupabaseSentenceStore.search()` |
| Context Retrieval | `stores.py` | 56-92 | `SupabaseSentenceStore.get_offset()` |
| Data Models | `shared/models.py` | 3-31 | `Document`, `EmptyDocument` |
| Sentence Splitting | `splitter.py` | 36-56 | `LLMSentenceSplitter.split()` |
| Data Ingestion | `notebooks/create_dataset_from_html.ipynb` | ~850-1000 | Notebook cells |

---

## Testing the Flow

Example from the notebook (`create_dataset_from_html.ipynb:1047-1059`):

```python
from corpusstudio.retriever import SentenceRetriever
from corpusstudio.stores import SupabaseSentenceStore
from corpusstudio.embedding_helper import EmbeddingModel

embedding_model = EmbeddingModel(model_name="voyage/voyage-3-large", api_key=API_KEY)
sentence_store = SupabaseSentenceStore(supabase)
retriever = SentenceRetriever(embedding_model, sentence_store)

query = "Figure 2(c) shows the wrist extensor being stimulated by EMS..."
results = await retriever.query(query, n_results=25, match_threshold=0.78)

for i, doc in enumerate(results):
    print(f"Result {i+1}:")
    print(f"Text: {doc['target_sentence'].text}")
    print(f"Section: {doc['target_sentence'].section_title}")
    print(f"Doc ID: {doc['target_sentence'].doc_id}")
    print()
```

This demonstrates the complete flow:
1. Initialize components
2. Execute query
3. Process results
4. Display matches with context

---

## Important Notes

1. **Database Dependency**: The system requires a Supabase database with:
   - `Document` table with embeddings
   - `match_documents` RPC function for vector similarity search
   - PostgreSQL with pgvector extension

2. **Embedding Model**: Must use the same embedding model for:
   - Storing sentences (during ingestion)
   - Querying sentences (during retrieval)

3. **Section Boundaries**: Context retrieval respects section boundaries. Sentences are only retrieved within the same section to maintain semantic coherence.

4. **Async Processing**: The retrieval process uses async/await for concurrent database queries, improving performance.

5. **Error Handling**: Returns `EmptyDocument` when adjacent sentences don't exist (e.g., at section boundaries).

