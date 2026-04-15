# DocuFind

DocuFind is a document intelligence app with:
- FastAPI backend for document and RAG APIs
- Streamlit frontend for upload, indexing, search, and chat
- LangGraph multi-agent flow for classify, retrieval, summary, and reflection
- Hybrid retrieval using BM25 + FAISS + RRF

## Requirements

- Python 3.12
- Virtual environment at `venv/`

## Quick Start

```bash
cd /Users/vallabhnaik/Desktop/docufind
source venv/bin/activate
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

Set these in `.env`:

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

## Main Endpoints

- `POST /rag/index`
- `POST /rag/answer`
- `POST /rag/search`
- `GET /rag/status`
- `GET /health`

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

- Local embeddings avoid remote embedding quota failures.
- ADK integration is optional and safely falls back to direct graph execution.
- Keep `venv/` active when running API and Streamlit.
