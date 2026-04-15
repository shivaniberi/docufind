"""
RAG Pipeline Module

Combines retrieval (BM25/FAISS side) and generation into a unified interface.
"""

import os
import logging
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass

from langchain_core.documents import Document

from rag.loader import DocumentLoader
from rag.embedder import VectorStore
from rag.retriever import Retriever
from rag.llm import GenerativeAIModel, GenerationConfig

logger = logging.getLogger(__name__)


@dataclass
class RAGConfig:
    """Configuration for RAG Pipeline."""
    # Retrieval settings
    k: int = 4  # Number of documents to retrieve
    score_threshold: float = 0.0  # Minimum similarity score
    
    # Embedding settings
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Generation settings
    llm_model: str = "gemini-2.0-flash"
    temperature: float = 0.7
    max_output_tokens: int = 2048
    
    # Features
    include_sources: bool = True
    deduplicate_results: bool = True


class RAGPipeline:
    """
    Complete RAG (Retrieval-Augmented Generation) Pipeline.
    
    Orchestrates:
    - Document loading and indexing
    - Semantic search for context
    - LLM-based answer generation
    - Source tracking and citations
    
    Example:
        >>> pipeline = RAGPipeline()
        >>> answer = pipeline.answer_question("What is AI?")
        >>> print(answer)
    """
    
    def __init__(self, config: Optional[RAGConfig] = None, api_key: Optional[str] = None):
        """
        Initialize the RAG Pipeline.
        
        Args:
            config (RAGConfig): Pipeline configuration
            api_key (str): Optional Google API key used only for Gemini generation.
        """
        self.config = config or RAGConfig()
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.embedding_backend = os.getenv("EMBEDDING_BACKEND", "local").lower()
        if self.embedding_backend == "hf":
            self.embedding_backend = "local"
        self.llm = None  # Lazily initialized only when answer generation is called.
        
        # Initialize components
        logger.info("Initializing RAG pipeline...")
        
        try:
            # 1. Document Loader
            self.loader = DocumentLoader()
            logger.info("DocumentLoader initialized")
            
            # 2. Vector Store (Embeddings)
            self.vector_store = VectorStore(
                api_key=self.api_key,
                model_name=self.config.embedding_model,
                backend=self.embedding_backend,
            )
            logger.info("VectorStore initialized")
            
            # 3. Retriever (Search)
            self.retriever = Retriever(
                vector_store=self.vector_store,
                k=self.config.k,
                score_threshold=self.config.score_threshold
            )
            logger.info("Retriever initialized")
            
            logger.info("RAG pipeline fully initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG pipeline: {str(e)}")
            raise

    def _get_llm(self) -> GenerativeAIModel:
        """Initialize generation model only when needed."""
        if self.llm is not None:
            return self.llm

        if not self.api_key:
            raise ValueError(
                "GOOGLE_API_KEY is required for pipeline.answer_question(). "
                "Index/search will still work with local embeddings."
            )

        gen_config = GenerationConfig(
            temperature=self.config.temperature,
            max_output_tokens=self.config.max_output_tokens
        )
        self.llm = GenerativeAIModel(
            api_key=self.api_key,
            model_name=self.config.llm_model,
            generation_config=gen_config
        )
        logger.info("GenerativeAIModel initialized")
        return self.llm
    
    def index_documents(self, collection_name: str = "default") -> Dict:
        """
        Load and index all documents.
        
        Args:
            collection_name (str): Name for this document collection
            
        Returns:
            Dict: Indexing statistics
        """
        logger.info(f"Indexing documents into collection: {collection_name}")
        
        try:
            # Load all documents
            documents_dict = self.loader.load_all_documents()
            total_docs = 0
            total_chunks = 0
            
            for file_name, chunks in documents_dict.items():
                total_docs += 1
                total_chunks += len(chunks)
                logger.info(f"  {file_name}: {len(chunks)} chunks")
            
            # Combine all chunks
            all_chunks = []
            for chunks in documents_dict.values():
                all_chunks.extend(chunks)
            
            # Add to vector store
            if all_chunks:
                self.vector_store.add_documents(all_chunks, collection_name)
                logger.info(f"Added {len(all_chunks)} chunks to vector store")
            
            return {
                "documents_loaded": total_docs,
                "chunks_created": total_chunks,
                "collection_name": collection_name,
                "status": "success"
            }
        
        except Exception as e:
            logger.error(f"Error indexing documents: {str(e)}")
            raise
    
    def answer_question(
        self,
        question: str,
        collection_name: str = "default",
        use_multi_query: bool = False,
        stream: bool = False
    ) -> Dict:
        """
        Answer a question using the RAG pipeline.
        
        Args:
            question (str): The user's question
            collection_name (str): Collection to search in
            use_multi_query (bool): Use multi-query expansion
            stream (bool): Stream the response (not yet implemented)
            
        Returns:
            Dict: Answer with metadata and sources
        """
        logger.info(f"Answering question: {question}")
        
        try:
            # 1. Load the vector store collection
            self.vector_store.load_from_disk(collection_name)
            
            # 2. Retrieve relevant documents
            if use_multi_query:
                # Use multi-query expansion for better retrieval
                logger.info("Using multi-query expansion...")
                results = self.retriever.retrieve_multi_query(
                    [question],
                    k=self.config.k,
                    deduplicate=self.config.deduplicate_results
                )
            else:
                # Simple single-query retrieval
                results = self.retriever.retrieve(
                    question,
                    k=self.config.k,
                    score_threshold=self.config.score_threshold
                )
            
            logger.info(f"Retrieved {len(results)} documents")
            
            # 3. Assemble context from retrieved documents
            context = self.retriever.assemble_context(
                results,
                max_tokens=2000,
                include_metadata=True
            )
            
            # 4. Generate answer using LLM
            logger.info("Generating answer with model...")
            llm = self._get_llm()
            answer = llm.answer_question(
                question=question,
                context=context,
                include_sources=self.config.include_sources,
                sources=results
            )
            
            # 5. Get retrieval summary
            summary = self.retriever.get_summary(results)
            
            logger.info("Answer generated successfully")
            
            return {
                "question": question,
                "answer": answer,
                "documents_retrieved": len(results),
                "retrieval_summary": summary,
                "sources": [
                    {
                        "file": doc.metadata.get("source", "Unknown"),
                        "page": doc.metadata.get("page", "Unknown"),
                        "score": round(score, 3)
                    }
                    for doc, score in results
                ],
                "status": "success"
            }
        
        except Exception as e:
            logger.error(f"Error answering question: {str(e)}")
            return {
                "question": question,
                "error": str(e),
                "status": "error"
            }
    
    def search(self, query: str, collection_name: str = "default", k: int = 5) -> List[Dict]:
        """
        Search for documents without generating an answer.
        
        Args:
            query (str): Search query
            collection_name (str): Collection to search in
            k (int): Number of results to return
            
        Returns:
            List[Dict]: Search results with metadata and scores
        """
        try:
            self.vector_store.load_from_disk(collection_name)
            results = self.vector_store.similarity_search(query, k=k)
            
            return [
                {
                    "content": doc.page_content[:200] + "...",
                    "file": doc.metadata.get("source", "Unknown"),
                    "score": round(score, 3)
                }
                for doc, score in results
            ]
        except Exception as e:
            logger.error(f"Error searching: {str(e)}")
            return []
    
    def summarize_document(self, file_name: str) -> str:
        """
        Summarize a specific document.
        
        Args:
            file_name (str): Document filename
            
        Returns:
            str: Document summary
        """
        try:
            # Load the document
            docs = self.loader.load_document(file_name)
            text = " ".join([doc.page_content for doc in docs])
            
            # Summarize
            summary = self.llm.summarize(text)
            return summary
        except Exception as e:
            logger.error(f"Error summarizing document: {str(e)}")
            raise
    
    def get_status(self) -> Dict:
        """
        Get the status of the RAG pipeline.
        
        Returns:
            Dict: Status information
        """
        return {
            "pipeline_status": "active",
            "config": {
                "k": self.config.k,
                "embedding_model": self.config.embedding_model,
                "llm_model": self.config.llm_model,
                "temperature": self.config.temperature
            },
            "vector_store_status": "ready",
            "llm_status": "ready"
        }
    
    def clear_cache(self):
        """Clear vector store cache."""
        try:
            self.vector_store.clear_store()
            logger.info("Cache cleared")
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
