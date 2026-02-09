from abc import ABC, abstractmethod
from typing import List
import logging
from pydantic import BaseModel
# Added Optional for new similarity field; original import had no Optional.
# from typing import Optional
from typing import Optional

# Configure logging
logger = logging.getLogger(__name__)

class Document(BaseModel):
    """
    A class that represents a document.
    
    Attributes:
        id: Unique identifier for the document
        doc_id: Document ID from the source
        text: The text content of the document
        section_title: Title of the section
        section_number: Number of the section
        sentence_index: Index of the sentence within the document
        global_index: Global index across all documents
        court: Court type (UKSC for Supreme Court or UKUT for Upper Tribunal)
        decision: Decision type (majority, dissenting, or concurring)
        similarity: Similarity score from vector search (0..1), if provided
    """
    id: int
    doc_id: str
    text: str
    section_title: str
    section_number: str
    sentence_index: int
    global_index: int
    court: str
    decision: str
    # New: carry similarity from vector search if present; keep optional to preserve existing schemas.
    # similarity: Optional[float] = None
    similarity: Optional[float] = None


class EmptyDocument(Document):
    """
    A class that represents an empty document placeholder.
    Used when a document is not found or doesn't exist.
    """
    def __init__(self):
        super().__init__(
            id=-1,
            doc_id="",
            text="",
            section_title="",
            section_number="",
            sentence_index=0,
            global_index=0,
            court="",
            decision="",
        )

class SentenceStore(ABC):
    """
    Abstract base class for storing and retrieving documents.
    """

    def search(self, embedding_vector: List[float], **kwargs) -> List[Document]:
        """Search for documents similar to the embedding vector."""
        return []

    def get_next_sentence(self, id: int) -> Document:
        """Get the next sentence after the given ID."""
        return self.get_offset(id, 1)

    def get_previous_sentence(self, id: int) -> Document:
        """Get the previous sentence before the given ID."""
        return self.get_offset(id, -1)

    def get_offset(self, id: int, offset: int) -> Document:
        """Get a sentence at an offset from the given ID."""
        return Document(
            id=id,
            doc_id="",
            text="",
            section_title="",
            section_number="",
            sentence_index=0,
            global_index=0,
            court="",
            decision="",
        )


# RAG corpus: main | mini_paragraphs | mini_sentences (which data)
# RAG_MATCH_FN: cosine | knn (which RPC - cosine uses <=>, knn uses <#>)
RAG_CORPUS_RPC = {
    "main": "match_corpus_documents",
    "mini_paragraphs": "match_corpus_mini_paragraphs",
    "mini_sentences": "match_corpus_mini_sentences",
}
RAG_CORPUS_RPC_KNN = {
    "main": "match_corpus_documents",
    "mini_paragraphs": "match_corpus_mini_paragraphs_knn",
    "mini_sentences": "match_corpus_mini_sentences_knn",
}
RAG_CORPUS_TABLE = {
    "main": "corpus_documents",
    "mini_paragraphs": "corpus_documents_mini_paragraphs",
    "mini_sentences": "corpus_documents_mini_sentences",
}


class SupabaseSentenceStore(SentenceStore):
    """
    A class that stores and retrieves sentences from a Supabase database.
    Works with corpus_documents by default; can switch to mini tables via RAG_CORPUS env.
    """

    def __init__(self, supabase, corpus: str | None = None) -> None:
        """
        Initialize the Supabase sentence store.
        
        Args:
            supabase: A Supabase client instance
            corpus: Override corpus source: main | mini_paragraphs | mini_sentences.
                    If None, uses RAG_CORPUS env var (default: main).
        """
        import os
        self.supabase = supabase
        raw = (corpus or os.environ.get("RAG_CORPUS", "main")).strip().lower()
        # Accept legacy combined values: mini_paragraphs_knn -> mini_paragraphs + knn
        use_knn_override = False
        if raw == "mini_paragraphs_knn":
            raw, use_knn_override = "mini_paragraphs", True
        elif raw == "mini_sentences_knn":
            raw, use_knn_override = "mini_sentences", True
        self._corpus = raw if raw in RAG_CORPUS_TABLE else "main"
        use_knn = use_knn_override or (os.environ.get("RAG_MATCH_FN", "cosine") or "cosine").strip().lower() == "knn"
        rpc_map = RAG_CORPUS_RPC_KNN if use_knn else RAG_CORPUS_RPC
        self._rpc = rpc_map.get(self._corpus, RAG_CORPUS_RPC[self._corpus])
        self._table = RAG_CORPUS_TABLE[self._corpus]
        logger.info(f"RAG corpus: {self._corpus} (table={self._table}, rpc={self._rpc})")

    def search(self, embedding_vector: List[float], **kwargs) -> List[Document]:
        """
        Search for documents similar to the embedding vector.
        
        Args:
            embedding_vector: The embedding vector to search for
            **kwargs: Additional search parameters (n_results, match_threshold)
            
        Returns:
            List[Document]: The matching documents
        """
        n_results = kwargs.get("n_results", 10)
        match_threshold = kwargs.get("match_threshold", 0.9)

        try:
            results = self.supabase.rpc(
                self._rpc,
                {
                    "query_embedding": embedding_vector,
                    "similarity_threshold": match_threshold,
                    "max_results": n_results,
                },
            ).execute()

            return [Document(**r) for r in results.data]
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []

    def get_offset(self, id: int, offset: int) -> Document:
        """
        Get a sentence at an offset from the given ID.
        
        Args:
            id: The document ID
            offset: The offset to apply
            
        Returns:
            Document: The document at the offset, or EmptyDocument if not found
        """
        try:
            res = self.supabase.table(self._table).select("*").eq("id", id).execute()

            if len(res.data) == 0:
                return EmptyDocument()

            # Get the current sentence index
            current_sentence_index = res.data[0]["sentence_index"]

            # Calculate the new index with offset
            new_index = current_sentence_index + offset

            # Query for the document with the new sentence index
            res = (
                self.supabase.table(self._table)
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
                court=doc.get("court", ""),
                decision=doc.get("decision", ""),
            )
        except Exception as e:
            logger.error(f"Error getting offset document: {e}")
            return EmptyDocument()
