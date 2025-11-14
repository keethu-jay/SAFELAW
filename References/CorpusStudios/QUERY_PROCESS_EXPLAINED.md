# How CorpusStudio Processes User Queries

## Simple Explanation

When a user types in a sentence, CorpusStudio finds similar sentences from other papers in the dataset. Here's exactly how it works:

---

## The Process

### Step 1: User Types a Sentence

**Example**: User types: `"Figure 2(c) shows the wrist extensor being stimulated by EMS..."`

This is just a regular sentence - no paper title needed.

---

### Step 2: Sentence Gets Converted to an Embedding

**Code Location**: `corpusstudio/src/corpusstudio/retriever.py` (lines 28-29)

```python
computed_query = f"{title} {query}" if title else query
embedded_query = self.embedding_model.embed(computed_query)
```

**What happens:**
- The user's sentence is converted from text into a mathematical vector (embedding)
- This vector represents the semantic meaning of the sentence
- If a title is provided (optional), it's combined with the query, but **typically users just type a sentence**

**Example:**
- Input: `"Figure 2(c) shows the wrist extensor..."`
- Output: `[0.123, -0.456, 0.789, ...]` (a 1024-dimensional vector)

---

### Step 3: Search Database for Similar Sentences

**Code Location**: `corpusstudio/src/corpusstudio/stores.py` (lines 41-54)

```python
def search(self, embedding_vector: List[float], **kwargs) -> List[Document]:
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
- The embedding vector is used to search the database
- The database contains embeddings of all sentences from all papers in the dataset
- It finds sentences whose embeddings are similar to the query embedding
- Returns the most similar sentences from other papers

**Example:**
- Query embedding searches through all stored sentence embeddings
- Finds sentences like:
  - `"The wrist extensor was activated using EMS stimulation..."` (from Paper A)
  - `"EMS was used to stimulate the wrist extensor muscle..."` (from Paper B)
  - `"Figure 2 demonstrates EMS activation of wrist extensors..."` (from Paper C)

---

### Step 4: Get Context (Adjacent Sentences)

**Code Location**: `corpusstudio/src/corpusstudio/stores.py` (lines 56-92)

For each matching sentence found, the system retrieves:
- The sentence before it (previous sentence)
- The sentence after it (next sentence)

This provides context so users can see what the paper was discussing around that sentence.

---

### Step 5: Return Results

**Code Location**: `corpusstudio/src/corpusstudio/retriever.py` (lines 53-60)

```python
res = [
    {
        "target_sentence": target_sentence,      # The matched sentence
        "next_sentence": next_sentence,          # Sentence after it
        "previous_sentence": prev_sentence,      # Sentence before it
    }
    for target_sentence, (next_sentence, prev_sentence) in zip(target_sentences, results)
]
```

**What happens:**
- Returns a list of results
- Each result contains:
  - The matching sentence from another paper
  - The sentence before it (for context)
  - The sentence after it (for context)
  - Information about which paper and section it came from

---

## Visual Flow

```
User Types Sentence
    ↓
"Figure 2(c) shows the wrist extensor..."
    ↓
[Convert to Embedding Vector]
    ↓
[0.123, -0.456, 0.789, ...]
    ↓
[Search Database for Similar Embeddings]
    ↓
Finds Similar Sentences from Other Papers:
    ├─→ "The wrist extensor was activated..." (Paper A, Section 3.2)
    ├─→ "EMS was used to stimulate..." (Paper B, Section 2.1)
    └─→ "Figure 2 demonstrates EMS..." (Paper C, Section 4.3)
    ↓
[Get Context for Each Match]
    ├─→ Previous sentence
    ├─→ Target sentence (the match)
    └─→ Next sentence
    ↓
Return Results to User
```

---

## Key Points

1. **User just types a sentence** - No paper title needed (it's optional)
2. **Sentence gets embedded** - Converted to a vector representation
3. **Database search** - Finds similar sentences from other papers using vector similarity
4. **Context included** - Returns the matching sentence plus sentences before/after it
5. **Results from multiple papers** - Can find similar sentences across the entire dataset

---

## About the "Title" Parameter

Looking at the code:

```python
title = kwargs.get("title", "")  # Line 26
computed_query = f"{title} {query}" if title else query  # Line 28
```

- The `title` parameter is **optional** (defaults to empty string)
- If provided, it's combined with the query for additional context
- **In typical usage, users just type a sentence** - no title needed
- The title feature is there if you want to narrow the search to a specific topic area

**Example with title (optional):**
```python
# If you want to add context
results = await retriever.query(
    "wrist extensor stimulation",
    title="Electromyography and Muscle Control"  # Optional context
)
```

**Typical usage (no title):**
```python
# Just type a sentence
results = await retriever.query("Figure 2(c) shows the wrist extensor...")
```

---

## Complete Example

```python
from corpusstudio.retriever import SentenceRetriever
from corpusstudio.stores import SupabaseSentenceStore
from corpusstudio.embedding_helper import EmbeddingModel

# Initialize
embedding_model = EmbeddingModel(model_name="voyage/voyage-3-large", api_key=API_KEY)
sentence_store = SupabaseSentenceStore(supabase)
retriever = SentenceRetriever(embedding_model, sentence_store)

# User types a sentence
user_sentence = "Figure 2(c) shows the wrist extensor being stimulated by EMS"

# Search for similar sentences
results = await retriever.query(
    user_sentence,           # The sentence the user typed
    n_results=25,            # How many results to return
    match_threshold=0.78     # Minimum similarity score
)

# Results contain similar sentences from other papers
for result in results:
    print(f"Found in: {result['target_sentence'].doc_id}")
    print(f"Section: {result['target_sentence'].section_title}")
    print(f"Match: {result['target_sentence'].text}")
    print(f"Context before: {result['previous_sentence'].text}")
    print(f"Context after: {result['next_sentence'].text}")
    print()
```

---

## Summary

**The main workflow:**
1. User types a sentence → `"Figure 2(c) shows the wrist extensor..."`
2. Sentence is embedded → `[0.123, -0.456, ...]`
3. Database is searched → Finds similar sentences from other papers
4. Context is retrieved → Gets sentences before/after each match
5. Results are returned → List of matching sentences with context

**The title parameter:**
- Optional feature
- Can add context to the query
- Typically not used - users just type sentences
- If provided, it's combined with the query before embedding

The core functionality is: **Type a sentence → Find similar sentences from other papers in the dataset**.

