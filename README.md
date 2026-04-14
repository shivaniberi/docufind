# 📚 Documind - Document Intelligence Platform

A modern document management and AI summarization platform built with **FastMCP**, **PydanticAI**, **LangChain**, and **Google Gemini**.

![Status](https://img.shields.io/badge/Status-Phase%202%20Complete-brightgreen)
![Python](https://img.shields.io/badge/Python-3.11+-blue)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 🎯 Project Goals

- ✅ Phase 1: Environment Setup (COMPLETE)
- ✅ Phase 2: FastMCP Server (COMPLETE)
- 🔄 Phase 3: AI Integration (NEXT)
- ⏳ Phase 4: Gradio Web UI
- ⏳ Phase 5: Deployment

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- macOS/Linux/Windows (tested on macOS)
- Virtual environment (venv)

### Installation

```bash
# Navigate to project
cd /Users/vallabhnaik/Desktop/docufind

# Activate virtual environment
source venv/bin/activate

# All dependencies already installed from Phase 1 ✅
```

### Running the Servers

**Terminal 1: Start FastMCP Server**
```bash
python run_server.py
# Runs on http://127.0.0.1:8000
```

**Terminal 2: Start Test UI**
```bash
python serve_test_ui.py
# Opens at http://127.0.0.1:8001/test_ui.html
```

---

## 📊 Architecture Overview

```
┌────────────────────────────────────────────────────────┐
│              Web UI (Gradio) - Phase 4                │
│        Beautiful interface for end users               │
└──────────────────┬─────────────────────────────────────┘
                   │
┌──────────────────▼─────────────────────────────────────┐
│           AI Processing Layer - Phase 3                │
│  - Google Gemini API Integration                       │
│  - PydanticAI for structured outputs                   │
│  - LangChain for document processing                   │
└──────────────────┬─────────────────────────────────────┘
                   │
┌──────────────────▼─────────────────────────────────────┐
│          FastMCP Server (HTTP API)                     │
│  - 5 Core Tools (list, read, save, get, delete)        │
│  - Interactive Test UI                                 │
│  - Error handling & Logging                            │
└──────────────────┬─────────────────────────────────────┘
                   │
┌──────────────────▼─────────────────────────────────────┐
│            Document Storage Layer                      │
│  - /documents/ - Input documents                       │
│  - /summaries/ - JSON summaries                        │
│  - /embeddings/ - FAISS vectors (Phase 3)              │
└────────────────────────────────────────────────────────┘
```

---

## 🛠️ Technology Stack

### Phase 1 & 2 (Complete)
- **FastMCP** - MCP server framework
- **Uvicorn** - ASGI server
- **Python 3.12** - Core language

### Phase 3 (Next)
- **Google Generative AI** - Gemini API
- **PydanticAI** - Structured AI outputs
- **LangChain** - Document processing
- **FAISS** - Vector similarity search

### Phase 4 (Future)
- **Gradio** - Web UI framework
- **PyPDF** - PDF handling

---

## 📚 Available Tools

### 1. List Documents
**Endpoint:** `POST /tools/list_documents/call`

Lists all documents with metadata (name, size, type, timestamps).

```json
{
  "status": "success",
  "count": 2,
  "documents": [
    {
      "name": "ai_future.txt",
      "path": "/Users/.../documents/ai_future.txt",
      "size": 1024,
      "type": ".txt",
      "created": 1712000000.0,
      "modified": 1712000000.0
    }
  ]
}
```

### 2. Read Document
**Endpoint:** `POST /tools/read_document/call`

Reads and returns the content of a specific document.

**Parameters:**
- `file_name` (string) - Name of the file to read

```json
{
  "status": "success",
  "file_name": "ai_future.txt",
  "file_type": ".txt",
  "file_size": 1024,
  "content": "The Future of Artificial Intelligence...",
  "message": "Document read successfully"
}
```

### 3. Save Summary
**Endpoint:** `POST /tools/save_summary/call`

Saves a summary for a document with optional metadata.

**Parameters:**
- `file_name` (string) - Document being summarized
- `summary` (string) - Summary text
- `metadata` (object, optional) - Additional metadata

### 4. Get Summary
**Endpoint:** `POST /tools/get_summary/call`

Retrieves a previously saved summary.

**Parameters:**
- `file_name` (string) - Document name

### 5. Delete Document
**Endpoint:** `POST /tools/delete_document/call`

Safely deletes a document from the system.

**Parameters:**
- `file_name` (string) - Document to delete

---

## 🧪 Testing

### Interactive Web UI (Recommended)
```bash
# Both servers running
# Visit: http://127.0.0.1:8001/test_ui.html
# Click buttons to test each tool
```

### Python Script
```bash
source venv/bin/activate
python example_usage.py
```

### With cURL
```bash
# List documents
curl -X POST http://127.0.0.1:8000/tools/list_documents/call \
  -H "Content-Type: application/json" \
  -d '{}'
```

---

## 📁 Project Structure

```
docufind/
├── .env                           # Environment variables (API keys)
├── venv/                          # Python virtual environment
├── mcp_server/
│   └── document_server.py         # FastMCP server implementation
├── documents/                     # Sample documents
│   ├── ai_future.txt
│   └── ml_basics.txt
├── summaries/                     # Saved summaries (JSON)
├── run_server.py                  # Start FastMCP server
├── serve_test_ui.py               # Start test UI server
├── test_ui.html                   # Interactive web tester
├── test_server.py                 # Python test script
├── example_usage.py               # Usage examples
├── PHASE2_COMPLETE.md             # Phase 2 documentation
└── README.md                      # This file
```

---

## 🔧 Configuration

### Environment Variables (in `.env`)
```env
GOOGLE_API_KEY=your_api_key_here
PROJECT_ID=your_project_id_here
DOCUMENTS_DIR=./documents
SUMMARIES_DIR=./summaries
```

---

## 🎬 Portfolio Recording Guide

Perfect for demonstrating your skills:

1. **Record your screen** (Cmd+Shift+5 on Mac)
2. **Open test UI** at http://127.0.0.1:8001
3. **Demo each tool**:
   - Click "List Documents" → show available files
   - Click "Read Document" → display content
   - Click "Save Summary" → save a new summary
   - Click "Get Summary" → retrieve it
   - Show JSON responses and error handling
4. **Narrate** what you're doing:
   - Explain FastMCP architecture
   - Show code structure
   - Discuss security features
5. **Show the API** at http://127.0.0.1:8000/docs

---

## 🚀 Next Steps (Phase 3)

### AI Integration with Google Gemini

```python
from google.generativeai import GenerativeModel
from document_server_client import DocumentServerClient

client = DocumentServerClient()
model = GenerativeModel('gemini-pro')

# Get document
content = client.read_document('ai_future.txt')

# Generate summary with AI
response = model.generate_content(
    f"Summarize this in 3 key points: {content}"
)

# Save AI summary
client.save_summary('ai_future.txt', response.text)
```

### Coming Soon
- ✨ Intelligent summarization
- 🔍 Semantic search with FAISS
- 🎨 Beautiful Gradio UI
- 📊 Document analytics
- 🔐 User authentication
- ☁️ Cloud deployment

---

## 📝 Notes

- All sample documents are in `/documents` - add your own!
- Summaries are saved as JSON in `/summaries`
- The server logs all operations to console
- CORS is enabled for cross-origin requests
- Security features prevent directory traversal attacks

---

## 🤝 Contributing

This is a learning project. Feel free to extend it!

Ideas for enhancement:
- Add PDF text extraction
- Implement batch processing
- Add document versioning
- Create user authentication
- Add webhooks for automation

---

## 📄 License

MIT License - Feel free to use for learning and projects

---

## 🎓 Learning Resources

- [FastMCP Docs](https://fastmcp.dev)
- [Google Gemini API](https://ai.google.dev)
- [LangChain Documentation](https://python.langchain.com)
- [PydanticAI](https://ai.pydantic.dev)

---

## ✅ Status

- **Phase 1:** ✅ Complete - Environment & dependencies
- **Phase 2:** ✅ Complete - FastMCP server with 5 tools
- **Phase 3:** 🔄 In Progress - AI integration
- **Phase 4:** ⏳ Planned - Gradio web UI
- **Phase 5:** ⏳ Planned - Deployment & scaling

---

Made with ❤️ by Your AI Assistant | April 2026
