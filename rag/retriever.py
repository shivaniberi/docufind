"""
Retriever Module

Handles semantic search and retrieval of relevant documents
for RAG applications.

Features:
- Semantic search using embeddings
- Multi-query retrieval
- Reranking and scoring
- Context assembly for LLM prompts
"""

import logging
from typing import List, Dict, Optional, Tuple

from langchain_core.documents import Document

logger = logging.getLogger(__name__)


class Retriever:
    """
    Retrieves relevant documents for a given query using semantic search.
    
    Features:
    - Single and multi-query search
    - Score-based filtering
    - Context assembly for LLM prompts
    - Result ranking and reranking
    """
    
    def __init__(
        self,
        vector_store,
        k: int = 4,
        score_threshold: float = 0.0
    ):
        """
        Initialize the Retriever.
        
        Args:
            vector_store: VectorStore instance for similarity search
            k (int): Default number of results to return. Default: 4
            score_threshold (float): Minimum similarity score. Default: 0.0
        """
        self.vector_store = vector_store
        self.k = k
        self.score_threshold = score_threshold
        
        logger.info(f"Retriever initialized with k={k}, threshold={score_threshold}")
    
    def retrieve(
        self,
        query: str,
        k: Optional[int] = None,
        score_threshold: Optional[float] = None
    ) -> List[Tuple[Document, float]]:
        """
        Retrieve relevant documents for a query.
        
        Args:
            query (str): Search query
            k (int): Number of results. If None, uses default
            score_threshold (float): Minimum score. If None, uses default
            
        Returns:
            List[Tuple[Document, float]]: List of (document, score) tuples
        """
        k = k or self.k
        score_threshold = score_threshold if score_threshold is not None else self.score_threshold
        
        logger.info(f"Retrieving documents for query: '{query}'")
        
        results = self.vector_store.similarity_search(
            query=query,
            k=k,
            score_threshold=score_threshold
        )
        
        logger.info(f"Retrieved {len(results)} documents")
        return results
    
    def retrieve_multi_query(
        self,
        queries: List[str],
        k: Optional[int] = None,
        deduplicate: bool = True
    ) -> List[Tuple[Document, float, List[str]]]:
        """
        Retrieve documents for multiple queries and combine results.
        
        This technique (Multi-query RAG) improves retrieval by searching
        with multiple reformulations of the original query.
        
        Args:
            queries (List[str]): List of queries to search
            k (int): Number of results per query. If None, uses default
            deduplicate (bool): Remove duplicate documents. Default: True
            
        Returns:
            List[Tuple[Document, float, List[str]]]: List of (document, score, matching_queries) tuples
        """
        k = k or self.k
        all_results = {}  # doc_id -> (doc, max_score, queries_matched)
        
        logger.info(f"Multi-query retrieval with {len(queries)} queries")
        
        for query in queries:
            try:
                results = self.vector_store.similarity_search(query=query, k=k)
                
                for doc, score in results:
                    doc_id = self._get_doc_id(doc)
                    
                    if doc_id not in all_results:
                        all_results[doc_id] = (doc, score, [query])
                    else:
                        # Update with higher score and add query to list
                        existing_doc, existing_score, queries_list = all_results[doc_id]
                        all_results[doc_id] = (
                            doc,
                            max(score, existing_score),
                            queries_list + [query]
                        )
            
            except Exception as e:
                logger.warning(f"Error retrieving for query '{query}': {str(e)}")
                continue
        
        # Convert to sorted list by score
        results = sorted(
            all_results.values(),
            key=lambda x: x[1],
            reverse=True
        )
        
        logger.info(f"Multi-query retrieval returned {len(results)} unique documents")
        return results
    
    def assemble_context(
        self,
        results: List[Tuple[Document, float]],
        max_tokens: int = 3000,
        include_metadata: bool = True
    ) -> str:
        """
        Assemble retrieved documents into context for LLM prompt.
        
        Args:
            results (List[Tuple[Document, float]]): Retrieved documents
            max_tokens (int): Maximum tokens in context. Default: 3000
            include_metadata (bool): Include metadata. Default: True
            
        Returns:
            str: Formatted context string
        """
        context_parts = []
        token_count = 0
        
        for i, (doc, score) in enumerate(results, 1):
            # Format document chunk
            chunk_text = doc.page_content.strip()
            
            if include_metadata:
                source = doc.metadata.get("source", "unknown")
                chunk_idx = doc.metadata.get("chunk_index", "?")
                chunk_str = f"[Document {i}: {source} (chunk {chunk_idx}), similarity: {score:.2f}]\n{chunk_text}\n"
            else:
                chunk_str = f"[Document {i}]\n{chunk_text}\n"
            
            # Estimate tokens (rough: 1 token ≈ 4 characters)
            chunk_tokens = len(chunk_str) // 4
            
            if token_count + chunk_tokens <= max_tokens:
                context_parts.append(chunk_str)
                token_count += chunk_tokens
            else:
                logger.info(f"Stopping context assembly at {len(context_parts)} documents (token limit)")
                break
        
        context = "\n".join(context_parts)
        logger.info(f"Assembled context: {len(context_parts)} documents, ~{token_count} tokens")
        
        return context
    
    def assemble_context_with_queries(
        self,
        results: List[Tuple[Document, float, List[str]]],
        max_tokens: int = 3000,
        include_metadata: bool = True
    ) -> str:
        """
        Assemble multi-query results into context for LLM prompt.
        
        Args:
            results (List[Tuple[Document, float, List[str]]]): Multi-query results
            max_tokens (int): Maximum tokens in context. Default: 3000
            include_metadata (bool): Include metadata. Default: True
            
        Returns:
            str: Formatted context string
        """
        context_parts = []
        token_count = 0
        
        for i, (doc, score, queries) in enumerate(results, 1):
            chunk_text = doc.page_content.strip()
            
            if include_metadata:
                source = doc.metadata.get("source", "unknown")
                chunk_idx = doc.metadata.get("chunk_index", "?")
                queries_str = ", ".join([f"'{q}'" for q in queries[:2]])  # Show first 2 queries
                chunk_str = f"[Document {i}: {source} (chunk {chunk_idx}), similarity: {score:.2f}, matched: {queries_str}]\n{chunk_text}\n"
            else:
                chunk_str = f"[Document {i}]\n{chunk_text}\n"
            
            chunk_tokens = len(chunk_str) // 4
            
            if token_count + chunk_tokens <= max_tokens:
                context_parts.append(chunk_str)
                token_count += chunk_tokens
            else:
                logger.info(f"Stopping context assembly at {len(context_parts)} documents")
                break
        
        context = "\n".join(context_parts)
        logger.info(f"Assembled multi-query context: {len(context_parts)} documents")
        
        return context
    
    def get_summary(self, results: List[Tuple[Document, float]]) -> Dict:
        """
        Get a summary of retrieval results.
        
        Args:
            results (List[Tuple[Document, float]]): Retrieved documents
            
        Returns:
            Dict: Summary information
        """
        unique_sources = set()
        avg_score = 0
        
        for doc, score in results:
            unique_sources.add(doc.metadata.get("source", "unknown"))
            avg_score += score
        
        avg_score = avg_score / len(results) if results else 0
        
        return {
            "total_documents": len(results),
            "unique_sources": len(unique_sources),
            "sources": list(unique_sources),
            "average_score": round(avg_score, 4),
            "scores": [score for _, score in results]
        }
    
    @staticmethod
    def _get_doc_id(doc: Document) -> str:
        """
        Generate unique ID for a document.
        
        Args:
            doc (Document): Document object
            
        Returns:
            str: Unique ID
        """
        source = doc.metadata.get("source", "unknown")
        chunk_idx = doc.metadata.get("chunk_index", 0)
        return f"{source}_{chunk_idx}"
    
    def rerank_results(
        self,
        results: List[Tuple[Document, float]],
        query: str,
        method: str = "similarity"
    ) -> List[Tuple[Document, float]]:
        """
        Rerank results using different methods.
        
        Args:
            results (List[Tuple[Document, float]]): Original results
            query (str): Original query (used for reranking)
            method (str): Reranking method: 'similarity', 'relevance', 'length'. Default: 'similarity'
            
        Returns:
            List[Tuple[Document, float]]: Reranked results
        """
        if method == "similarity":
            # Already sorted by similarity
            return results
        
        elif method == "relevance":
            # Prefer documents with higher query term overlap
            def relevance_score(doc_score_tuple):
                doc, score = doc_score_tuple
                query_terms = set(query.lower().split())
                doc_terms = set(doc.page_content.lower().split())
                overlap = len(query_terms & doc_terms)
                return score * (1 + overlap / len(query_terms))
            
            return sorted(results, key=relevance_score, reverse=True)
        
        elif method == "length":
            # Prefer shorter, more focused documents
            def length_score(doc_score_tuple):
                doc, score = doc_score_tuple
                length_penalty = 1 / (1 + len(doc.page_content) / 500)
                return score * length_penalty
            
            return sorted(results, key=length_score, reverse=True)
        
        else:
            logger.warning(f"Unknown reranking method: {method}")
            return results
