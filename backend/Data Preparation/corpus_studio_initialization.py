"""
CorpusStudio Initialization Module

Contains the core split, embed, and store logic for processing court judgments.
This module handles text splitting with LLMs, vector embedding generation,
and database storage/retrieval operations.
"""

from abc import ABC, abstractmethod
from typing import List
import os
import logging

from pydantic import BaseModel

# Isaacus legal embedder - using kanon-2-embedder for legal documents
try:
    from isaacus import Isaacus
except ImportError:
    Isaacus = None

# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

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


# ============================================================================
# Text Splitting [not neccesary sinc he xml files are already sectioned]
# ============================================================================

# class SentenceSplitter(ABC):
#     """Abstract base class for splitting text into sentences."""
#
#     def __init__(self, text: str):
#         """
#         Initialize the sentence splitter.
#         
#         Args:
#             text: The text to split into sentences
#         """
#         self.text = text
#
#     @abstractmethod
#     def split(self):
#         """Split the text into sentences."""
#         pass
#
#
# class LLMSentenceSplitter(SentenceSplitter):
#     """Split a text into sentences using a language model."""
#
#     def __init__(
#         self,
#         text: str,
#         api_key: str = None,
#         model_name: str = "openai/gpt-4o-mini",
#     ):
#         """
#         Initialize the LLM sentence splitter.
#         
#         Args:
#             text: The text to split
#             api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
#             model_name: The model to use for splitting
#         """
#         super().__init__(text)
#         self.model_name = model_name
#         self.api_key = api_key or os.getenv("OPENAI_API_KEY")
#
#     def split(self):
#         """
#         Split the text into sentences using a language model.
#
#         Returns:
#             str: The text with [EOS] tokens separating sentences.
#         """
#         try:
#             # Import litellm only when needed
#             from litellm import completion
#             
#             prompt = (
#                 f"Split the following text into sentences. Separate each sentence with [EOS] token. "
#                 f"Only output the final text with [EOS] tokens and nothing else.\n"
#                 f"Text: {self.text}"
#             )
#
#             response = completion(
#                 model=self.model_name,
#                 messages=[{"role": "user", "content": prompt}],
#                 max_tokens=1000,
#                 temperature=0.0,
#                 api_key=self.api_key,
#             )
#
#             return response.choices[0].message.content
#         except Exception as e:
#             logger.error(f"Error splitting sentences with LLM: {e}")
#             # Fallback: split by period, exclamation mark, or question mark
#             sentences = re.split(r'[.!?]+', self.text)
#             return "[EOS]".join([s.strip() for s in sentences if s.strip()])


# ============================================================================
# Embedding Generation
# ============================================================================

class EmbeddingModel:
    """
    A class that generates vector embeddings for text sentences.
    Uses Isaacus kanon-2-embedder for legal document embeddings.
    """

    def __init__(self, model_name: str = "kanon-2-embedder", api_key: str = None) -> None:
        """
        Initialize the embedding model.
        
        Args:
            model_name: The embedding model to use (default: kanon-2-embedder for legal documents)
            api_key: Isaacus API key (defaults to ISAACUS_API_KEY env var)
        """
        self.model_name = model_name
        self.api_key = api_key or os.getenv("ISAACUS_API_KEY")
        
        # Switched from OpenAI to Isaacus kanon-2-embedder for legal domain specificity
        if Isaacus is None:
            logger.error("Isaacus SDK not installed. Install with: pip install isaacus")
            self.client = None
        else:
            self.client = Isaacus(api_key=self.api_key)

    def embed(self, sentence: str) -> List[float]:
        """
        Generate an embedding vector for a sentence using Isaacus legal embedder.
        
        Args:
            sentence: The sentence to embed
            
        Returns:
            List[float]: The embedding vector
        """
        if not self.client:
            logger.error("Isaacus client not initialized")
            return [0.0] * 1792  # Isaacus kanon-2 uses 1792 dimensions
        
        try:
            # Using kanon-2-embedder: legal-domain embedder optimized for court documents
            # task="retrieval/document" since we're embedding document chunks/paragraphs
            response = self.client.embeddings.create(
                model=self.model_name,
                texts=[sentence],
                task="retrieval/document"  # Task type for embedding documents (not queries)
            )
            # Extract embedding from response
            return response.embeddings[0].embedding
        except Exception as e:
            logger.error(f"Error generating embedding with Isaacus: {e}")
            # Fallback to zero vector if API fails
            return [0.0] * 1792  # Isaacus kanon-2 uses 1792 dimensions


# ============================================================================
# Storage and Retrieval
# ============================================================================

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


class SupabaseSentenceStore(SentenceStore):
    """
    A class that stores and retrieves sentences from a Supabase database.
    Works with the corpus_documents table for legal judgment storage.
    """

    def __init__(self, supabase) -> None:
        """
        Initialize the Supabase sentence store.
        
        Args:
            supabase: A Supabase client instance
        """
        self.supabase = supabase

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
            # Changed from match_documents to match_corpus_documents RPC function
            # to target the corpus_documents table specifically
            results = self.supabase.rpc(
                "match_corpus_documents",
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
            # Changed table name from Document to corpus_documents
            res = self.supabase.table("corpus_documents").select("*").eq("id", id).execute()

            if len(res.data) == 0:
                return EmptyDocument()

            # Get the current sentence index
            current_sentence_index = res.data[0]["sentence_index"]

            # Calculate the new index with offset
            new_index = current_sentence_index + offset

            # Query for the document with the new sentence index
            res = (
                self.supabase.table("corpus_documents")
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
