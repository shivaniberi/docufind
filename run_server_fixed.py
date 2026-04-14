"""
Fixed HTTP server for FastMCP Document Server with proper REST endpoints
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import sys
from pathlib import Path
import json

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from mcp_server.document_server import (
    list_documents,
    read_document,
    save_summary,
    get_summary,
    delete_document
)

# Request models
class FileNameRequest(BaseModel):
    file_name: str

class SaveSummaryRequest(BaseModel):
    file_name: str
    summary: str
    metadata: dict = None

# Create FastAPI app
app = FastAPI(
    title="FastMCP Document Server",
    description="REST API for document management with FastMCP",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint - health check"""
    return {
        "status": "running",
        "service": "FastMCP Document Server",
        "version": "1.0.0"
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

if __name__ == "__main__":
    print("🚀 Starting FastMCP Document Server (Fixed)...")
    print("📍 Server will be available at: http://127.0.0.1:8000")
    print("📝 Open: http://127.0.0.1:8000/docs for API docs")
    print("\nAvailable endpoints:")
    print("  POST /tools/list_documents/call")
    print("  POST /tools/read_document/call?file_name=...")
    print("  POST /tools/save_summary/call")
    print("  POST /tools/get_summary/call?file_name=...")
    print("  POST /tools/delete_document/call?file_name=...")
    print("\nPress Ctrl+C to stop the server\n")
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        reload=False,
        log_level="info"
    )
