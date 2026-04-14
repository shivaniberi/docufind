"""
LangChain RAG (Retrieval-Augmented Generation) Module

This package provides document loading, embedding, and retrieval capabilities
for the docufind system using LangChain and FAISS.

Components:
- loader.py: Document loading and text splitting (PyPDFLoader + RecursiveCharacterTextSplitter)
- embedder.py: Vector embeddings and storage (FAISS + Google Generative AI embeddings)
- retriever.py: Semantic search and similarity matching
- llm.py: Generative AI models (Gemini) for answer generation
- pipeline.py: Complete RAG pipeline orchestration
"""

from rag.loader import DocumentLoader
from rag.embedder import VectorStore
from rag.retriever import Retriever
from rag.llm import GenerativeAIModel, GenerationConfig
from rag.pipeline import RAGPipeline, RAGConfig

__all__ = [
    'DocumentLoader',
    'VectorStore',
    'Retriever',
    'GenerativeAIModel',
    'GenerationConfig',
    'RAGPipeline',
    'RAGConfig'
]
