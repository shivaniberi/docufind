"""
Simple HTTP server runner for FastMCP Document Server
"""

import sys
from pathlib import Path

# Add the parent directory to the path so we can import mcp_server
sys.path.insert(0, str(Path(__file__).parent))

from mcp_server.document_server import mcp

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting FastMCP Document Server...")
    print("📍 Server will be available at: http://127.0.0.1:8000")
    print("📝 Open: http://127.0.0.1:8000/docs for API docs")
    print("\nAvailable tools:")
    print("  - list_documents()")
    print("  - read_document(file_name)")
    print("  - save_summary(file_name, summary, metadata)")
    print("  - get_summary(file_name)")
    print("  - delete_document(file_name)")
    print("\nPress Ctrl+C to stop the server\n")
    
    # Get the FastAPI app from FastMCP
    app = mcp.http_app()
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        reload=False,
        log_level="info"
    )
