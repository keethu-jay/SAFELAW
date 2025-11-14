# How CorpusStudio Retrieves and Uses Papers from the Dataset

This document explains the complete flow of how CorpusStudio takes a paper from the dataset and uses it for retrieval and querying.

## Overview

The system uses a semantic search approach where:
1. Papers are pre-processed and stored in a Supabase database with embeddings
2. User queries are converted to embeddings
3. Similar sentences are found using vector similarity search
4. Context (adjacent sentences) is retrieved for each match
5. Results are returned with target sentences and their context

---

## Step 1: Data Storage (Pre-processing)

Papers are stored in Supabase database with the following structure. Each sentence from a paper is stored as a separate document with its embedding.

### Location: `notebooks/create_dataset_from_html.ipynb`

**Key Code Section: Storing Papers in Database**

```python
# Create a list of records to insert into Supabase
records = []

for _, row in sentences_df.iterrows():
    if pd.notna(row['sentences']) and len(row['embedding']) > 0:
        record = {
            "doc_id": row['docid'],                    # Paper identifier
            "text": row['sentences'],                  # Sentence text
            "section_title": row['section_title'],     # Section title (e.g., "Introduction")
            "section_number": row['section_number'],   # Section number (e.g., "1.1")
            "sentence_index": row['paragraph_sentence_index'],  # Index within section
            "global_index": row['paper_global_index'], # Index within entire paper
            "embedding": row['embedding']              # Vector embedding for semantic search
        }
        records.append(record)

# Upload records to Supabase in batches
batch_size = 100
for i in range(0, total_records, batch_size):
    batch = records[i:i+batch_size]
    response = supabase.table("Document").insert(batch).execute()
```

**What happens:**
- Each sentence from a paper is stored as a separate row in the `Document` table
- Each sentence includes its embedding vector (created using Voyage AI model)
- Sentences are linked to their paper via `doc_id`
- Section information is preserved for context

---

## Step 2: Query Processing

When a user submits a query, the system processes it through the `SentenceRetriever` class.

### Location: `corpusstudio/src/corpusstudio/retriever.py`

**Key Code Section: Query Method**

```python
async def query(self, query: str, **kwargs) -> List[Dict[str, Document]]:
    offset = kwargs.get("offset", 0)
    title = kwargs.get("title", "")

    # STEP 2a: Embed the user's sentence query
    # (Title is optional - if provided, it's combined with query for context)
    computed_query = f"{title} {query}" if title else query
    embedded_query = self.embedding_model.embed(computed_query)

    # STEP 2b: Search for similar documents using vector similarity
    targets = self.sentence_store.search(embedded_query, **kwargs)

    # STEP 2c: Get target sentences with offset (for context window)
    target_sentences = await asyncio.gather(*[
        asyncio.to_thread(self.sentence_store.get_offset, doc.id, offset) 
        for doc in targets
    ])
    
    # STEP 2d: Get next and previous sentences for context
    results = await asyncio.gather(*[
        asyncio.gather(
            asyncio.to_thread(self.sentence_store.get_next_sentence, target_sentence.id),
            asyncio.to_thread(self.sentence_store.get_previous_sentence, target_sentence.id)
        )
        for target_sentence in target_sentences
    ])
    
    # STEP 2e: Combine results
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

**What happens:**
1. **Query Embedding**: The user's sentence query is converted to an embedding vector. If an optional paper title is provided, it's combined with the query for additional context, but typically users just type a sentence.
2. **Vector Search**: The embedding is used to search the database for similar sentences from other papers in the dataset
3. **Context Retrieval**: For each matching sentence, the system retrieves the previous and next sentences from the same paper/section to provide context
4. **Result Assembly**: Results are packaged with target sentence and its surrounding context

---

## Step 3: Embedding Creation

The query is converted to an embedding vector using the same model that was used to embed the stored sentences.

### Location: `corpusstudio/src/corpusstudio/embedding_helper.py`

**Key Code Section: Embedding Model**

```python
class EmbeddingModel:
    """
    A class that embeds sentences.
    """

    def __init__(self, model_name: str, api_key: str) -> None:
        self.model_name = model_name
        self.api_key = api_key

    def embed(self, sentence: str) -> List[float]:
        response = embedding(
            model=self.model_name, input=[sentence], api_key=self.api_key
        )
        return response.data[0]["embedding"]
```

**What happens:**
- Uses LiteLLM to call the embedding API (e.g., Voyage AI)
- Converts the text query into a high-dimensional vector (e.g., 1024 dimensions)
- This vector represents the semantic meaning of the query

---

## Step 4: Vector Similarity Search

The embedded query is used to search the database for similar sentences using Supabase's vector similarity search.

### Location: `corpusstudio/src/corpusstudio/stores.py`

**Key Code Section: Supabase Search**

```python
class SupabaseSentenceStore(SentenceStore):
    def __init__(self, supabase: Client) -> None:
        self.supabase = supabase

    def search(self, embedding_vector: List[float], **kwargs) -> List[Document]:
        n_results = kwargs.get("n_results", 10)
        match_threshold = kwargs.get("match_threshold", 0.9)

        # Call Supabase RPC function for vector similarity search
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

**What happens:**
- Calls the `match_documents` RPC function in Supabase
- This function uses PostgreSQL's vector similarity operators (likely `pgvector`)
- Finds documents whose embeddings are similar to the query embedding
- Returns documents that exceed the similarity threshold
- Results are limited by `max_results` parameter

**Note**: The `match_documents` function is a database function (stored procedure) that performs the vector similarity search. It's not shown in this codebase but would look something like:

```sql
CREATE OR REPLACE FUNCTION match_documents(
  query_embedding vector(1024),
  similarity_threshold float,
  max_results int
)
RETURNS TABLE (
  id int,
  doc_id text,
  text text,
  section_title text,
  section_number text,
  sentence_index int,
  global_index int
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT 
    d.id,
    d.doc_id,
    d.text,
    d.section_title,
    d.section_number,
    d.sentence_index,
    d.global_index
  FROM "Document" d
  WHERE 1 - (d.embedding <=> query_embedding) > similarity_threshold
  ORDER BY d.embedding <=> query_embedding
  LIMIT max_results;
END;
$$;
```

---

## Step 5: Context Retrieval

For each matched sentence, the system retrieves adjacent sentences to provide context.

### Location: `corpusstudio/src/corpusstudio/stores.py`

**Key Code Section: Getting Adjacent Sentences**

```python
def get_offset(self, id: int, offset: int) -> Document:
    # Get the current sentence
    res = self.supabase.table("Document").select("*").eq("id", id).execute()

    if len(res.data) == 0:
        raise ValueError(f"Document with id {id} not found")

    # Get the current sentence index
    current_sentence_index = res.data[0]["sentence_index"]

    # Calculate the new index with offset
    new_index = current_sentence_index + offset

    # Query for the document with the new sentence index
    # (within the same document and section)
    res = (
        self.supabase.table("Document")
        .select("*")
        .eq("doc_id", res.data[0]["doc_id"])           # Same paper
        .eq("section_title", res.data[0]["section_title"])  # Same section
        .eq("sentence_index", new_index)               # Offset sentence index
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

def get_next_sentence(self, id: int) -> Document:
    return self.get_offset(id, 1)

def get_previous_sentence(self, id: int) -> Document:
    return self.get_offset(id, -1)
```

**What happens:**
1. **Get Current Sentence**: Retrieves the matched sentence from the database
2. **Calculate Offset**: Determines the index of the adjacent sentence (current_index ± 1)
3. **Query Adjacent Sentence**: Finds the sentence with the calculated index within the same paper and section
4. **Return Context**: Returns the adjacent sentence, or an EmptyDocument if it doesn't exist (e.g., at section boundaries)

**Important**: Context is retrieved within the same section (`section_title`) and paper (`doc_id`). This ensures that context is semantically coherent.

---

## Step 6: Result Assembly

The final step combines all the retrieved information into a structured response.

### Location: `corpusstudio/src/corpusstudio/retriever.py`

**Key Code Section: Result Assembly**

```python
# Combine results
res = [
    {
        "target_sentence": target_sentence,      # The matched sentence
        "next_sentence": next_sentence,          # Sentence that comes after
        "previous_sentence": prev_sentence,      # Sentence that comes before
    }
    for target_sentence, (next_sentence, prev_sentence) in zip(target_sentences, results)
]

return res
```

**What happens:**
- Each result contains:
  - **target_sentence**: The sentence that matched the query (with similarity above threshold)
  - **next_sentence**: The sentence immediately following the target (for context)
  - **previous_sentence**: The sentence immediately preceding the target (for context)
- All three sentences are from the same paper and section
- Results are returned as a list, allowing multiple matches from different papers

---

## Complete Flow Diagram

```
User Query
    ↓
[EmbeddingModel.embed()]
    ↓
Embedding Vector
    ↓
[SentenceStore.search()]
    ↓
Supabase RPC: match_documents
    ↓
Similar Sentences (Documents)
    ↓
[For each document:]
    ├─→ get_offset(id, offset) → Target Sentence
    ├─→ get_next_sentence(id) → Next Sentence
    └─→ get_previous_sentence(id) → Previous Sentence
    ↓
Result: List of {
    target_sentence: Document,
    next_sentence: Document,
    previous_sentence: Document
}
```

---

## Data Model

### Document Structure

```python
class Document(BaseModel):
    id: int                    # Unique sentence ID in database
    doc_id: str               # Paper identifier (UUID)
    text: str                 # Sentence text
    section_title: str        # Section title (e.g., "Introduction", "Methods")
    section_number: str       # Section number (e.g., "1.1", "2.3")
    sentence_index: int       # Index within the section
    global_index: int         # Index within the entire paper
```

### Database Schema

- **Document Table**: Stores individual sentences with embeddings
  - `id`: Primary key
  - `doc_id`: Foreign key to paper
  - `text`: Sentence text
  - `section_title`: Section name
  - `section_number`: Section number
  - `sentence_index`: Position within section
  - `global_index`: Position within paper
  - `embedding`: Vector embedding (for similarity search)

- **Source Table**: Stores paper metadata
  - `doc_id`: Paper identifier
  - `title`: Paper title
  - `abstract`: Paper abstract
  - `authors`: Paper authors
  - `doi_link`: DOI link
  - `venue_name`: Publication venue

---

## Example Usage

From the notebook (`create_dataset_from_html.ipynb`):

```python
from corpusstudio.retriever import SentenceRetriever
from corpusstudio.stores import SupabaseSentenceStore
from corpusstudio.embedding_helper import EmbeddingModel

# Initialize components
embedding_model = EmbeddingModel(
    model_name="voyage/voyage-3-large", 
    api_key=API_KEY
)
sentence_store = SupabaseSentenceStore(supabase)
retriever = SentenceRetriever(embedding_model, sentence_store)

# Query the corpus
query = "Figure 2(c) shows the wrist extensor being stimulated by EMS..."
results = await retriever.query(
    query, 
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
    print()
```

---

## Key Design Decisions

1. **Sentence-Level Granularity**: Papers are split into individual sentences, allowing fine-grained retrieval
2. **Section-Aware Context**: Context retrieval respects section boundaries, maintaining semantic coherence
3. **Vector Similarity Search**: Uses embeddings for semantic matching, not just keyword matching
4. **Async Processing**: Uses asyncio for concurrent database queries, improving performance
5. **Batch Processing**: Database inserts are done in batches to handle large datasets efficiently

---

## Performance Considerations

- **Embedding Caching**: LiteLLM uses disk caching for embeddings to avoid redundant API calls
- **Concurrent Queries**: Uses `asyncio.gather()` to execute multiple database queries in parallel
- **Batch Uploads**: Sentences are uploaded to the database in batches of 100 to avoid request size limits
- **Vector Indexing**: Supabase/PostgreSQL uses vector indexes (pgvector) for fast similarity search

---

## Summary

CorpusStudio retrieves papers from the dataset through a semantic search pipeline:

1. **Storage**: Papers are pre-processed into sentences with embeddings and stored in Supabase
2. **Query**: User queries are embedded using the same model
3. **Search**: Vector similarity search finds matching sentences
4. **Context**: Adjacent sentences are retrieved for each match
5. **Results**: Matches are returned with their context for the user

The system maintains paper structure (sections, sentence order) while enabling semantic search across the entire corpus.

