"""
Reciprocal Rank Fusion (RRF) Module

Combines results from BM25 (sparse/keyword) and FAISS (dense/semantic)
retrievers into a single ranked list. Neither retriever dominates  both
contribute based on rank position, not raw scores.

Formula: RRF_score(doc) = sum(1 / (k + rank_i)) for each retriever i
where k=60 is a constant that dampens the impact of high ranks.

Usage:
    from rag.rrf import reciprocal_rank_fusion

    bm25_results  = [(doc1, 0.9), (doc2, 0.6), (doc3, 0.3)]
    faiss_results = [(doc2, 0.95), (doc4, 0.7), (doc1, 0.4)]
    merged = reciprocal_rank_fusion(bm25_results, faiss_results)
"""

import logging
from typing import List, Tuple, Dict
from langchain_core.documents import Document

logger = logging.getLogger(__name__)


def reciprocal_rank_fusion(
    *result_lists: List[Tuple[Document, float]],
    k: int = 60,
    top_n: int = 10
) -> List[Tuple[Document, float]]:
    """
    Merge multiple ranked result lists using Reciprocal Rank Fusion.

    Args:
        *result_lists: Any number of (Document, score) lists, each already
                       sorted best-first. Typically two: BM25 + FAISS.
        k (int):       RRF constant. k=60 is the standard default from the
                       original Cormack et al. paper. Higher k  more weight
                       to lower-ranked docs; lower k  top ranks dominate more.
        top_n (int):   How many results to return after fusion.

    Returns:
        List of (Document, rrf_score) tuples, sorted best-first.
        rrf_score is the fused score (not a similarity  just used for ranking).
    """
    # doc_id  (Document, cumulative_rrf_score)
    fused: Dict[str, Tuple[Document, float]] = {}

    for result_list in result_lists:
        for rank, (doc, _original_score) in enumerate(result_list):
            doc_id = _doc_id(doc)
            rrf_contribution = 1.0 / (k + rank + 1)  # rank is 0-indexed

            if doc_id in fused:
                existing_doc, existing_score = fused[doc_id]
                fused[doc_id] = (existing_doc, existing_score + rrf_contribution)
            else:
                fused[doc_id] = (doc, rrf_contribution)

    # Sort by fused score, descending
    sorted_results = sorted(fused.values(), key=lambda x: x[1], reverse=True)

    logger.info(
        f"RRF fusion: {sum(len(r) for r in result_lists)} total results "
        f"from {len(result_lists)} retrievers  {len(sorted_results)} unique  "
        f"returning top {min(top_n, len(sorted_results))}"
    )

    return sorted_results[:top_n]


def _doc_id(doc: Document) -> str:
    """
    Stable unique ID for a document chunk.
    Uses source path + chunk_index from metadata so the same chunk from
    two different retrievers maps to the same key.
    """
    source = doc.metadata.get("source", "unknown")
    chunk = doc.metadata.get("chunk_index", doc.page_content[:40])
    return f"{source}::{chunk}"
