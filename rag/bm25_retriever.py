"""
BM25 Retriever Module

Sparse keyword-based retrieval using the BM25 algorithm (Best Match 25).
Complements FAISS semantic search  BM25 is strong on exact keyword matches
and rare terms; FAISS is strong on semantic/conceptual similarity.

Together (fused via RRF) they cover both cases.

Requires: pip install rank-bm25 nltk

Usage:
    from rag.bm25_retriever import BM25Retriever

    retriever = BM25Retriever()
    retriever.index(documents)                          # list of LangChain Documents
    results = retriever.retrieve("machine learning", k=5)
    #  List[Tuple[Document, float]]  (same interface as rag/retriever.py)
"""

import logging
import math
from typing import List, Tuple, Optional

from langchain_core.documents import Document

logger = logging.getLogger(__name__)


def _simple_tokenize(text: str) -> List[str]:
    """
    Lightweight tokenizer  avoids NLTK download requirement.
    Lowercases, splits on whitespace/punctuation, removes short tokens.
    """
    import re
    tokens = re.findall(r'\b[a-zA-Z0-9]+\b', text.lower())
    return [t for t in tokens if len(t) > 1]


class BM25Retriever:
    """
    BM25 keyword retriever with the same (Document, score) interface
    as the existing FAISS-based Retriever in rag/retriever.py.

    BM25 parameters (standard defaults):
        k1=1.5   term frequency saturation. Higher  more weight on TF.
        b=0.75   length normalisation. 1.0 = full normalisation by doc length.

    Example:
        >>> from rag.bm25_retriever import BM25Retriever
        >>> bm25 = BM25Retriever()
        >>> bm25.index(chunks)
        >>> results = bm25.retrieve("neural networks", k=5)
        >>> for doc, score in results:
        ...     print(score, doc.page_content[:60])
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b

        self._docs: List[Document] = []
        self._tokenized_corpus: List[List[str]] = []
        self._bm25 = None          # rank_bm25.BM25Okapi instance (lazy import)
        self._indexed = False

    # Indexing

    def index(self, documents: List[Document]) -> None:
        """
        Build a BM25 index from a list of LangChain Document chunks.

        Args:
            documents: List of Document objects (same chunks used for FAISS).
        """
        if not documents:
            logger.warning("BM25Retriever.index() called with empty document list.")
            return

        self._docs = documents
        self._tokenized_corpus = [
            _simple_tokenize(doc.page_content) for doc in documents
        ]

        try:
            from rank_bm25 import BM25Okapi
            self._bm25 = BM25Okapi(
                self._tokenized_corpus,
                k1=self.k1,
                b=self.b
            )
            self._indexed = True
            logger.info(f"BM25 index built: {len(documents)} chunks")
        except ImportError:
            logger.error(
                "rank-bm25 not installed. Run: pip install rank-bm25"
            )
            raise

    def add_documents(self, documents: List[Document]) -> None:
        """
        Add more documents and rebuild the index.
        For large corpora consider batching; BM25 rebuild is O(n).
        """
        self._docs.extend(documents)
        self.index(self._docs)

    # Retrieval

    def retrieve(
        self,
        query: str,
        k: int = 5,
        score_threshold: float = 0.0
    ) -> List[Tuple[Document, float]]:
        """
        Retrieve the top-k most relevant documents for a query.

        Args:
            query:           Natural-language search query.
            k:               Number of results to return.
            score_threshold: Minimum BM25 score (0.0 = return all top-k).

        Returns:
            List of (Document, normalised_score) tuples, sorted best-first.
            Scores are normalised to [0, 1] so they are comparable with
            FAISS cosine scores when passed to RRF.
        """
        if not self._indexed:
            raise RuntimeError(
                "BM25Retriever has not been indexed yet. Call .index(documents) first."
            )

        query_tokens = _simple_tokenize(query)
        if not query_tokens:
            logger.warning("BM25 query produced no tokens after tokenisation.")
            return []

        raw_scores = self._bm25.get_scores(query_tokens)

        # Pair each doc with its score and sort
        scored = sorted(
            zip(self._docs, raw_scores),
            key=lambda x: x[1],
            reverse=True
        )

        # Normalise scores to [0, 1] based on the max score in this query
        max_score = scored[0][1] if scored and scored[0][1] > 0 else 1.0
        normalised = [
            (doc, score / max_score)
            for doc, score in scored
            if score / max_score >= score_threshold
        ]

        results = normalised[:k]
        logger.info(f"BM25 retrieved {len(results)} docs for query: '{query[:60]}'")
        return results

    # Helpers

    def is_indexed(self) -> bool:
        return self._indexed

    def corpus_size(self) -> int:
        return len(self._docs)

    def clear(self) -> None:
        """Reset the index."""
        self._docs = []
        self._tokenized_corpus = []
        self._bm25 = None
        self._indexed = False
        logger.info("BM25 index cleared.")
