"""
HTTP Server with CORS support for FastMCP Document Server
"""

import sys
from pathlib import Path

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from mcp_server.document_server import mcp
from fastapi.middleware.cors import CORSMiddleware

if __name__ == "__main__":
    import uvicorn
    
    # Get the HTTP app and add CORS middleware
    app = mcp.http_app()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    print("🚀 Starting FastMCP Document Server with CORS...")
    print("📍 Server will be available at: http://127.0.0.1:8000")
    print("📝 Open: http://127.0.0.1:8001/test_ui.html to test")
    print("\nAvailable tools:")
    print("  - list_documents()")
    print("  - read_document(file_name)")
    print("  - save_summary(file_name, summary, metadata)")
    print("  - get_summary(file_name)")
    print("  - delete_document(file_name)")
    print("\nPress Ctrl+C to stop the server\n")
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info"
    )
