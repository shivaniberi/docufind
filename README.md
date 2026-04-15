# DocuFind - Your document summarizer and insight assistant.

DocuFind is an LLM-powered document intelligence system built using LangChain and LangGraph, enabling users to upload, index, search, and chat over their data using a hybrid Retrieval-Augmented Generation (RAG) pipeline and agent-based workflows.

It includes:

1. FastAPI backend for scalable document processing and RAG APIs
2. Streamlit frontend for interactive upload, semantic search, and chat
3. LangChain + LangGraph for LLM orchestration, multi-agent workflows, and stateful reasoning
4. Hybrid retrieval using BM25 + FAISS (vector embeddings) + Reciprocal Rank Fusion (RRF)
5. Context-aware memory for maintaining conversation history and improving response relevance
6. Model Context Protocol (MCP) integration for efficient tool usage and fast context exchange between components
7. Semantic search over document embeddings for accurate, context-grounded responses

<img width="1302" height="767" alt="Screenshot 2026-04-15 at 1 12 49 AM (1)" src="https://github.com/user-attachments/assets/ac51f347-af02-47ac-933a-537bd169cff5" />


## Features

- Multi-format ingestion: `PDF`, `TXT`, `MD`  
- Semantic chunking with metadata-aware indexing  

- Hybrid retrieval combining lexical and vector search:
  - BM25 for keyword-based matching  
  - FAISS for semantic similarity search  
  - Reciprocal Rank Fusion (RRF) for ranking optimization  

- Context-aware conversational memory for improved multi-turn interactions  

- Multi-agent reasoning pipeline (LangChain + LangGraph):
  - Classifier Node → routes simple vs complex queries  
  - Retrieval Node → gathers relevant context  
  - Generation Node → produces grounded responses  
  - Reflection Node → validates and refines outputs  

- ADK (Agent Development Kit) integration for flexible agent execution and optional runtime orchestration  

- Support for local embeddings to reduce dependency on external APIs and avoid rate limits  

- Extensible architecture for integrating multiple LLM providers and tools  

## Requirements

- Python `3.12`
- Virtual environment: `venv/`

## Quick Start

```bash
cd /Users/vallabhnaik/Desktop/docufind
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Terminal 1:

```bash
python run.py
```

Terminal 2:

```bash
streamlit run ui/streamlit_app.py --server.port 8501
```

Open:
- UI: `http://localhost:8501`
- API docs: `http://127.0.0.1:8000/docs`

## Environment Variables

Create a local `.env` file in the repo root (do not commit it). Example:

```env
LLM_BACKEND=cohere
COHERE_API_KEY=your_key_here
COHERE_MODEL=command-r-08-2024

EMBEDDING_BACKEND=local
LOCAL_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

Optional:

```env
GOOGLE_API_KEY=...
OPENAI_API_KEY=...
ADK_MODEL=gemini-2.0-flash
```

Notes:
- Local embeddings avoid remote embedding quota failures.
- ADK integration is optional and safely falls back to direct graph execution.

## Main Endpoints

- `POST /rag/index`
- `POST /rag/answer`
- `POST /rag/search`
- `GET /rag/status`
- `GET /health`

## Typical Workflow

1. Upload documents in the Streamlit UI
2. Trigger indexing to build BM25 + FAISS indexes
3. Use Search for retrieval-only results
4. Use Chat/Answer for grounded responses powered by the agent graph + hybrid retrieval

## Project Structure

```text
docufind/
  agents/
  rag/
  ui/
  mcp_server/
  documents/
  embeddings/
  run.py
  README.md
```

## Notes

- Keep `venv/` active when running API and Streamlit.
- If you change embedding model/backend, re-index so vectors match the configured embedder.
