"""
Enhanced FastAPI Server with RAG Pipeline Integration

Adds RAG capabilities to the document server:
- answer_question_with_rag: Ask questions about documents with source citations
- search_documents_rag: Semantic search across documents
- index_documents_rag: Index documents for RAG
"""

import os
import sys
from pathlib import Path
from typing import Optional, List

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from mcp_server.document_server import (
    list_documents,
    read_document,
    save_summary,
    get_summary,
    delete_document
)

from rag import RAGPipeline, RAGConfig

# Request/Response models
class FileNameRequest(BaseModel):
    file_name: str

class SaveSummaryRequest(BaseModel):
    file_name: str
    summary: str
    metadata: Optional[dict] = None

class QuestionRequest(BaseModel):
    question: str
    collection_name: str = "default"
    use_multi_query: bool = False
    include_sources: bool = True

class SearchRequest(BaseModel):
    query: str
    collection_name: str = "default"
    k: int = 5

class IndexRequest(BaseModel):
    collection_name: str = "default"

# Initialize FastAPI app
app = FastAPI(
    title="FastMCP Document Server with RAG",
    description="REST API for document management and RAG question answering",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global RAG pipeline (lazy loaded)
rag_pipeline = None

def get_rag_pipeline():
    """Get or initialize RAG pipeline."""
    global rag_pipeline
    if rag_pipeline is None:
        try:
            config = RAGConfig(
                k=4,
                llm_model="gemini-2.0-flash",
                temperature=0.7,
                include_sources=True
            )
            rag_pipeline = RAGPipeline(config=config)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to initialize RAG pipeline: {str(e)}")
    return rag_pipeline

# ============================================================================
# Original Document Management Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint - health check"""
    return {
        "status": "running",
        "service": "FastMCP Document Server with RAG",
        "version": "2.0.0",
        "features": [
            "Document management",
            "RAG question answering",
            "Semantic search",
            "Document indexing"
        ]
    }

@app.post("/tools/list_documents/call")
async def api_list_documents():
    """List all documents"""
    try:
        result = list_documents()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tools/read_document/call")
async def api_read_document(request: FileNameRequest):
    """Read a specific document"""
    try:
        result = read_document(request.file_name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tools/save_summary/call")
async def api_save_summary(request: SaveSummaryRequest):
    """Save a summary for a document"""
    try:
        result = save_summary(request.file_name, request.summary, request.metadata or {})
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tools/get_summary/call")
async def api_get_summary(request: FileNameRequest):
    """Get a previously saved summary"""
    try:
        result = get_summary(request.file_name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tools/delete_document/call")
async def api_delete_document(request: FileNameRequest):
    """Delete a document"""
    try:
        result = delete_document(request.file_name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# New RAG Endpoints (Phase 3B)
# ============================================================================

@app.post("/rag/index")
async def rag_index_documents(request: IndexRequest):
    """
    Index documents for RAG system.
    
    Call this before asking questions to prepare the document collection.
    """
    try:
        pipeline = get_rag_pipeline()
        result = pipeline.index_documents(collection_name=request.collection_name)
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rag/answer")
async def rag_answer_question(request: QuestionRequest):
    """
    Answer a question using RAG (Retrieval-Augmented Generation).
    
    Steps:
    1. Retrieves relevant documents using semantic search
    2. Generates an answer using Gemini with the retrieved context
    3. Includes source citations and confidence scores
    """
    try:
        pipeline = get_rag_pipeline()
        result = pipeline.answer_question(
            question=request.question,
            collection_name=request.collection_name,
            use_multi_query=request.use_multi_query
        )
        return {
            "status": result.get("status", "error"),
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rag/search")
async def rag_search_documents(request: SearchRequest):
    """
    Search documents using semantic similarity (no generation).
    
    Useful for exploring relevant documents before asking questions.
    """
    try:
        pipeline = get_rag_pipeline()
        results = pipeline.search(
            query=request.query,
            collection_name=request.collection_name,
            k=request.k
        )
        return {
            "status": "success",
            "data": {
                "query": request.query,
                "results": results,
                "count": len(results)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/rag/status")
async def rag_status():
    """Get RAG pipeline status."""
    try:
        pipeline = get_rag_pipeline()
        status = pipeline.get_status()
        return {
            "status": "success",
            "data": status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Health checks and diagnostics
# ============================================================================

@app.get("/health")
async def health_check():
    """Complete health check including RAG pipeline."""
    try:
        # Check basic health
        docs = list_documents()
        
        # Check RAG pipeline
        pipeline = get_rag_pipeline()
        rag_status = pipeline.get_status()
        
        return {
            "status": "healthy",
            "components": {
                "document_server": "online",
                "rag_pipeline": "online",
                "documents_available": len(docs.get("documents", [])) if isinstance(docs, dict) else 0
            }
        }
    except Exception as e:
        return {
            "status": "degraded",
            "error": str(e)
        }

@app.get("/docs-custom")
async def custom_docs():
    """Custom API documentation."""
    return {
        "service": "FastMCP Document Server with RAG",
        "endpoints": {
            "document_management": {
                "/tools/list_documents/call": "List all documents",
                "/tools/read_document/call": "Read document content",
                "/tools/save_summary/call": "Save document summary",
                "/tools/get_summary/call": "Get saved summary",
                "/tools/delete_document/call": "Delete document"
            },
            "rag": {
                "/rag/index": "Index documents for RAG",
                "/rag/answer": "Answer question with RAG",
                "/rag/search": "Search documents semantically",
                "/rag/status": "Get RAG pipeline status"
            },
            "health": {
                "/health": "Complete health check",
                "/": "Root endpoint"
            }
        }
    }

if __name__ == "__main__":
    # Load environment
    env_path = Path(".env")
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    key, val = line.strip().split("=", 1)
                    os.environ[key] = val
    
    # Run server
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info"
    )
