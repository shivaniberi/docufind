"""
Example Usage of FastMCP Document Server API
This script demonstrates how to use the FastMCP server programmatically
"""

import requests
import json
from typing import Dict, Any, List

class DocumentServerClient:
    """Client for interacting with FastMCP Document Server"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
    
    def _call_tool(self, tool_name: str, **params) -> Dict[str, Any]:
        """Make a request to the FastMCP server"""
        url = f"{self.base_url}/tools/{tool_name}/call"
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json=params
        )
        return response.json()
    
    def list_documents(self) -> List[Dict]:
        """List all documents"""
        result = self._call_tool("list_documents")
        if result.get("status") == "success":
            return result.get("documents", [])
        raise Exception(f"Error listing documents: {result.get('error')}")
    
    def read_document(self, file_name: str) -> str:
        """Read a document's content"""
        result = self._call_tool("read_document", file_name=file_name)
        if result.get("status") == "success":
            return result.get("content", "")
        raise Exception(f"Error reading document: {result.get('error')}")
    
    def save_summary(self, file_name: str, summary: str, 
                    metadata: Dict = None) -> str:
        """Save a summary for a document"""
        result = self._call_tool(
            "save_summary",
            file_name=file_name,
            summary=summary,
            metadata=metadata or {}
        )
        if result.get("status") == "success":
            return result.get("summary_file", "")
        raise Exception(f"Error saving summary: {result.get('error')}")
    
    def get_summary(self, file_name: str) -> Dict:
        """Retrieve a saved summary"""
        result = self._call_tool("get_summary", file_name=file_name)
        if result.get("status") == "success":
            return result.get("data", {})
        raise Exception(f"Error retrieving summary: {result.get('error')}")
    
    def delete_document(self, file_name: str) -> bool:
        """Delete a document"""
        result = self._call_tool("delete_document", file_name=file_name)
        return result.get("status") == "success"


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

def main():
    print("🚀 FastMCP Document Server - Usage Examples\n")
    print("="*60)
    
    # Initialize client
    client = DocumentServerClient()
    
    # Example 1: List documents
    print("\n📋 Example 1: Listing Documents")
    print("-" * 60)
    try:
        documents = client.list_documents()
        print(f"Found {len(documents)} document(s):")
        for doc in documents:
            print(f"  - {doc['name']} ({doc['size']} bytes)")
    except Exception as e:
        print(f"Error: {e}")
    
    # Example 2: Read a document
    print("\n📖 Example 2: Reading Document Content")
    print("-" * 60)
    try:
        if documents:
            file_name = documents[0]['name']
            content = client.read_document(file_name)
            print(f"Reading: {file_name}")
            print(f"Content preview (first 200 chars):")
            print(content[:200] + "..." if len(content) > 200 else content)
    except Exception as e:
        print(f"Error: {e}")
    
    # Example 3: Save a summary
    print("\n💾 Example 3: Saving a Summary")
    print("-" * 60)
    try:
        if documents:
            file_name = documents[0]['name']
            summary_text = "This is an AI-generated summary of the document content..."
            
            metadata = {
                "tags": ["AI", "summary", "automated"],
                "word_count": 150,
                "reading_time_minutes": 2,
                "confidence": 0.95
            }
            
            summary_file = client.save_summary(
                file_name,
                summary_text,
                metadata
            )
            print(f"✅ Summary saved: {summary_file}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Example 4: Retrieve a summary
    print("\n🔍 Example 4: Retrieving a Summary")
    print("-" * 60)
    try:
        if documents:
            file_name = documents[0]['name']
            summary_data = client.get_summary(file_name)
            print(f"Summary for {file_name}:")
            print(json.dumps(summary_data, indent=2))
    except Exception as e:
        print(f"Error: {e}")
    
    # Example 5: Integration with AI
    print("\n🤖 Example 5: AI Integration Pattern")
    print("-" * 60)
    print("""
    Here's how to integrate with Google Gemini API:
    
    from google.generativeai import GenerativeModel
    from document_client import DocumentServerClient
    
    client = DocumentServerClient()
    model = GenerativeModel('gemini-pro')
    
    # 1. List documents
    documents = client.list_documents()
    
    # 2. Read a document
    content = client.read_document(documents[0]['name'])
    
    # 3. Generate summary with AI
    response = model.generate_content(
        f"Summarize this document: {content}"
    )
    
    # 4. Save the AI-generated summary
    client.save_summary(
        documents[0]['name'],
        response.text,
        metadata={"source": "gemini-pro"}
    )
    """)
    
    print("\n" + "="*60)
    print("✅ Examples complete!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
