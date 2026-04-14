"""
FastMCP Server for Document Management
Provides tools for listing, reading, and summarizing documents
"""

import os
import json
from pathlib import Path
from typing import Optional
from fastmcp import FastMCP
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP app
mcp = FastMCP("DocumentServer")

# Define documents directory
DOCUMENTS_DIR = Path(os.getenv("DOCUMENTS_DIR", "./documents"))
DOCUMENTS_DIR.mkdir(exist_ok=True)

SUMMARIES_DIR = Path(os.getenv("SUMMARIES_DIR", "./summaries"))
SUMMARIES_DIR.mkdir(exist_ok=True)


@mcp.tool()
def list_documents() -> dict:
    """
    List all documents in the documents directory.
    
    Returns:
        dict: A dictionary containing the list of documents and their metadata
    """
    try:
        documents = []
        if not DOCUMENTS_DIR.exists():
            return {
                "status": "success",
                "count": 0,
                "documents": [],
                "message": "Documents directory is empty"
            }
        
        for file_path in DOCUMENTS_DIR.glob("*"):
            if file_path.is_file():
                stat_info = file_path.stat()
                documents.append({
                    "name": file_path.name,
                    "path": str(file_path),
                    "size": stat_info.st_size,
                    "type": file_path.suffix.lower(),
                    "created": stat_info.st_ctime,
                    "modified": stat_info.st_mtime
                })
        
        # Sort by modification time (newest first)
        documents.sort(key=lambda x: x["modified"], reverse=True)
        
        logger.info(f"Listed {len(documents)} documents")
        
        return {
            "status": "success",
            "count": len(documents),
            "documents": documents,
            "message": f"Found {len(documents)} document(s)"
        }
    
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to list documents"
        }


@mcp.tool()
def read_document(file_name: str) -> dict:
    """
    Read the content of a document.
    
    Args:
        file_name: The name of the file to read
    
    Returns:
        dict: The document content and metadata
    """
    try:
        file_path = DOCUMENTS_DIR / file_name
        
        # Security check - prevent directory traversal
        if not str(file_path.resolve()).startswith(str(DOCUMENTS_DIR.resolve())):
            raise ValueError("Access denied: Invalid file path")
        
        if not file_path.exists():
            return {
                "status": "error",
                "error": f"File not found: {file_name}",
                "message": "The specified document does not exist"
            }
        
        # Read file content
        if file_path.suffix.lower() == ".pdf":
            content = f"[PDF File] {file_path.name} - Use PDF reader to extract content"
        elif file_path.suffix.lower() in [".txt", ".md", ".json"]:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        else:
            content = f"[Binary File] {file_path.name} - Content cannot be displayed as text"
        
        stat_info = file_path.stat()
        
        logger.info(f"Read document: {file_name}")
        
        return {
            "status": "success",
            "file_name": file_name,
            "file_type": file_path.suffix.lower(),
            "file_size": stat_info.st_size,
            "content": content,
            "message": "Document read successfully"
        }
    
    except Exception as e:
        logger.error(f"Error reading document {file_name}: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to read document"
        }


@mcp.tool()
def save_summary(file_name: str, summary: str, metadata: Optional[dict] = None) -> dict:
    """
    Save a summary of a document.
    
    Args:
        file_name: The name of the document being summarized
        summary: The summary text
        metadata: Optional metadata to include (e.g., key_points, word_count)
    
    Returns:
        dict: Status of the save operation
    """
    try:
        # Create summary filename
        base_name = Path(file_name).stem
        summary_file = SUMMARIES_DIR / f"{base_name}_summary.json"
        
        # Prepare summary data
        summary_data = {
            "source_document": file_name,
            "summary": summary,
            "metadata": metadata or {},
            "created_timestamp": os.popen("date -u +%Y-%m-%dT%H:%M:%SZ").read().strip()
        }
        
        # Save to JSON
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)
        
        stat_info = summary_file.stat()
        
        logger.info(f"Saved summary for: {file_name}")
        
        return {
            "status": "success",
            "summary_file": summary_file.name,
            "summary_path": str(summary_file),
            "file_size": stat_info.st_size,
            "message": f"Summary saved successfully to {summary_file.name}"
        }
    
    except Exception as e:
        logger.error(f"Error saving summary for {file_name}: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to save summary"
        }


@mcp.tool()
def get_summary(file_name: str) -> dict:
    """
    Retrieve a previously saved summary for a document.
    
    Args:
        file_name: The name of the document
    
    Returns:
        dict: The summary data or error message
    """
    try:
        base_name = Path(file_name).stem
        summary_file = SUMMARIES_DIR / f"{base_name}_summary.json"
        
        if not summary_file.exists():
            return {
                "status": "error",
                "error": f"No summary found for: {file_name}",
                "message": "Summary does not exist for this document"
            }
        
        with open(summary_file, 'r', encoding='utf-8') as f:
            summary_data = json.load(f)
        
        logger.info(f"Retrieved summary for: {file_name}")
        
        return {
            "status": "success",
            "file_name": file_name,
            "summary_file": summary_file.name,
            "data": summary_data,
            "message": "Summary retrieved successfully"
        }
    
    except Exception as e:
        logger.error(f"Error retrieving summary for {file_name}: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to retrieve summary"
        }


@mcp.tool()
def delete_document(file_name: str) -> dict:
    """
    Delete a document from the documents directory.
    
    Args:
        file_name: The name of the file to delete
    
    Returns:
        dict: Status of the delete operation
    """
    try:
        file_path = DOCUMENTS_DIR / file_name
        
        # Security check
        if not str(file_path.resolve()).startswith(str(DOCUMENTS_DIR.resolve())):
            raise ValueError("Access denied: Invalid file path")
        
        if not file_path.exists():
            return {
                "status": "error",
                "error": f"File not found: {file_name}",
                "message": "Cannot delete non-existent document"
            }
        
        file_path.unlink()
        
        logger.info(f"Deleted document: {file_name}")
        
        return {
            "status": "success",
            "file_name": file_name,
            "message": f"Document {file_name} deleted successfully"
        }
    
    except Exception as e:
        logger.error(f"Error deleting document {file_name}: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to delete document"
        }


if __name__ == "__main__":
    # This will be run by: fastmcp dev mcp_server/document_server.py
    logger.info("FastMCP Document Server initialized")
    logger.info(f"Documents directory: {DOCUMENTS_DIR}")
    logger.info(f"Summaries directory: {SUMMARIES_DIR}")
