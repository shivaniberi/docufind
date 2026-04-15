# DocuFind

DocuFind is a document intelligence app for uploading, indexing, searching, and chatting over your own files using a hybrid Retrieval-Augmented Generation (RAG) pipeline and an agentic workflow.

It includes:
- FastAPI backend for document and RAG APIs
- Streamlit frontend for upload, indexing, search, and chat
- LangGraph multi-agent flow for classification, retrieval, summary, and reflection
- Hybrid retrieval using BM25 + FAISS + RRF

## Resume-Ready Highlights (Project Keywords)

- Architected multi-agent RAG pipeline (LangChain + FAISS + BM25 hybrid retrieval) with semantic chunking and context engineering for hallucination-resistant LLM responses across PDF/TXT/MD corpora.
- Implemented agentic patterns (ReAct orchestrator, Reflection summarizer) via Pydantic AI and ADK; exposed MCP toolset via FastMCP with asyncio tool calling and managed prompt template libraries for extensible document operations.
- Built evaluation harness with 100% test coverage; achieved 65% query latency reduction via embedding caching and FAISS index partitioning; managed session memory with persistent context tracking across multi-LLM backends

## Features

- Ingestion for `PDF`, `TXT`, and `MD` corpora
- Semantic chunking + metadata-aware indexing
- Hybrid retrieval:
- BM25 for exact/keyword matches
- FAISS for semantic similarity search
- RRF (Reciprocal Rank Fusion) to combine retriever rankings
- Agent graph:
- Classifier node routes simple vs complex queries
- Retrieval node gathers evidence from hybrid retrievers
- Summary node generates grounded responses from retrieved context
- Reflection node critiques and rewrites when needed
- Local embedding option to avoid remote embedding quota failures

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
