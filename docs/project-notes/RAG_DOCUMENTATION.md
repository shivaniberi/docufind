# LangChain RAG System Documentation

## Overview

The RAG (Retrieval-Augmented Generation) system is a powerful module that combines document retrieval with LLM capabilities for enhanced question-answering. This system enables semantic search, multi-query retrieval, and context assembly for LLM prompts.

**Components:**
- **DocumentLoader** (`rag/loader.py`): Loads and splits documents into manageable chunks
- **VectorStore** (`rag/embedder.py`): Creates and manages vector embeddings using FAISS
- **Retriever** (`rag/retriever.py`): Performs semantic search and context assembly

---

## Architecture

```
Documents (PDF, TXT, MD)
         ↓
   DocumentLoader
    (split chunks)
         ↓
   Vector Embeddings
  (Google Generative AI)
         ↓
    FAISS Store
(Similarity Search)
         ↓
    Retriever
 (Context Assembly)
         ↓
  LLM Prompt Ready
```

---

## 1. DocumentLoader (`rag/loader.py`)

### Purpose
Loads various document formats and intelligently splits them into chunks for semantic search.

### Supported Formats
- **PDF** (`.pdf`) - Using PyPDFLoader
- **Text** (`.txt`, `.md`) - Using TextLoader

### Key Methods

#### `__init__` - Initialize Loader
```python
loader = DocumentLoader(
    chunk_size=1000,        # Characters per chunk
    chunk_overlap=200,      # Overlap between chunks
    documents_dir="./documents"
)
```

**Parameters:**
- `chunk_size`: Size of text chunks (default: 1000 chars)
- `chunk_overlap`: Overlap between consecutive chunks (default: 200 chars)
- `documents_dir`: Path to documents directory (default: ./documents)

#### `load_document` - Load Single Document
```python
chunks = loader.load_document("file.pdf")
# Returns: List[Document]
```

**Features:**
- Security: Validates file is within documents directory
- Metadata: Adds source, chunk_index, loaded_at timestamp
- Error handling: Comprehensive logging and error messages

#### `load_all_documents` - Load All Documents
```python
all_docs = loader.load_all_documents()
# Returns: Dict[str, List[Document]]
# Example: {"file1.pdf": [chunks], "file2.txt": [chunks]}
```

#### `get_document_info` - Get Document Metadata
```python
info = loader.get_document_info("file.pdf")
# Returns: {
#     "name": "file.pdf",
#     "size": 12345,
#     "type": ".pdf",
#     "estimated_tokens": 3000
# }
```

### Text Splitting Strategy

Uses `RecursiveCharacterTextSplitter` with hierarchical separators:
1. Double newlines (paragraphs)
2. Single newlines (lines)
3. Sentences
4. Words
5. Characters

This preserves semantic meaning while keeping chunks manageable.

### Example Usage

```python
from rag.loader import DocumentLoader

# Initialize
loader = DocumentLoader(chunk_size=1000, chunk_overlap=200)

# Load single document
chunks = loader.load_document("ml_basics.txt")
print(f"Loaded {len(chunks)} chunks")

# Load all documents
all_docs = loader.load_all_documents()
for file_name, chunks in all_docs.items():
    print(f"{file_name}: {len(chunks)} chunks")
```

---

## 2. VectorStore (`rag/embedder.py`)

### Purpose
Creates vector embeddings and manages them in a FAISS index for efficient similarity search.

### Embedding Model
- **Model**: Google Generative AI (models/embedding-001)
- **Dimensions**: 768 (from Google's embeddings)
- **Cost**: Free tier included with GOOGLE_API_KEY

### Key Methods

#### `__init__` - Initialize Vector Store
```python
vector_store = VectorStore(
    api_key=None,              # Uses GOOGLE_API_KEY env var if None
    embeddings_dir="./embeddings",
    model_name="models/embedding-001"
)
```

#### `add_documents` - Add Documents to Store
```python
success = vector_store.add_documents(
    documents=[chunk1, chunk2, ...],
    collection_name="documents"
)
```

**Process:**
1. Creates FAISS index (or updates existing)
2. Generates embeddings for each document
3. Stores metadata (source, chunk index, etc.)
4. Returns success status

#### `similarity_search` - Search Similar Documents
```python
results = vector_store.similarity_search(
    query="machine learning",
    k=4,                       # Number of results
    score_threshold=0.0        # Minimum similarity (0-1)
)
# Returns: List[Tuple[Document, float]]
```

#### `save_to_disk` - Persist Embeddings
```python
vector_store.save_to_disk("documents")
# Saves to: ./embeddings/documents/
# Creates: index, metadata.json
```

#### `load_from_disk` - Load Saved Embeddings
```python
success = vector_store.load_from_disk("documents")
if success:
    print("Embeddings loaded!")
```

#### `get_store_info` - Get Store Statistics
```python
info = vector_store.get_store_info()
# Returns: {
#     "status": "ready",
#     "model": "models/embedding-001",
#     "documents": 5,
#     "collections": ["documents"]
# }
```

#### `list_collections` - List All Saved Collections
```python
collections = vector_store.list_collections()
# Returns: ["documents", "archive", ...]
```

### Workflow Example

```python
from rag.loader import DocumentLoader
from rag.embedder import VectorStore

# Load documents
loader = DocumentLoader()
all_docs = loader.load_all_documents()

# Create vector store
vs = VectorStore()

# Add documents
for file_name, chunks in all_docs.items():
    vs.add_documents(chunks, collection_name="documents")

# Save for future use
vs.save_to_disk("documents")
```

---

## 3. Retriever (`rag/retriever.py`)

### Purpose
Performs semantic search and assembles context for LLM prompts.

### Key Methods

#### `__init__` - Initialize Retriever
```python
retriever = Retriever(
    vector_store=vs,           # VectorStore instance
    k=4,                       # Default number of results
    score_threshold=0.0        # Default score threshold
)
```

#### `retrieve` - Basic Semantic Search
```python
results = retriever.retrieve(
    query="How does gradient descent work?",
    k=4,
    score_threshold=0.0
)
# Returns: List[Tuple[Document, float]]
```

Each result tuple contains:
- `Document`: Document chunk with metadata
- `float`: Similarity score (0-1)

#### `retrieve_multi_query` - Multi-Query RAG
```python
queries = [
    "How does gradient descent work?",
    "What is gradient descent algorithm?",
    "Gradient descent optimization"
]

results = retriever.retrieve_multi_query(
    queries=queries,
    k=3,                       # Per query
    deduplicate=True          # Remove duplicates
)
# Returns: List[Tuple[Document, float, List[str]]]
```

Returns tuples of:
- `Document`: Document chunk
- `float`: Best similarity score
- `List[str]`: Queries that matched this document

**Benefits:**
- Multiple query reformulations improve retrieval
- Captures different ways people ask the same question
- Deduplication prevents redundant documents

#### `assemble_context` - Format Context for LLM
```python
context = retriever.assemble_context(
    results=results,
    max_tokens=3000,           # Limit context size
    include_metadata=True      # Show source/chunk info
)
# Returns: str (formatted context)
```

**Output Format:**
```
[Document 1: file.pdf (chunk 0), similarity: 0.95]
Document content here...

[Document 2: file.pdf (chunk 1), similarity: 0.92]
Document content here...
```

#### `assemble_context_with_queries` - Format Multi-Query Context
```python
context = retriever.assemble_context_with_queries(
    results=multi_query_results,
    max_tokens=3000,
    include_metadata=True
)
```

Shows which queries matched each result for transparency.

#### `get_summary` - Get Retrieval Statistics
```python
summary = retriever.get_summary(results)
# Returns: {
#     "total_documents": 4,
#     "unique_sources": 2,
#     "sources": ["file1.pdf", "file2.txt"],
#     "average_score": 0.92,
#     "scores": [0.95, 0.92, 0.88, 0.85]
# }
```

#### `rerank_results` - Rerank Retrieved Results
```python
reranked = retriever.rerank_results(
    results=results,
    query="machine learning",
    method="relevance"  # Options: similarity, relevance, length
)
```

**Methods:**
- `similarity`: Already sorted by similarity (default)
- `relevance`: Prefer documents with query term overlap
- `length`: Prefer shorter, more focused documents

### Complete RAG Pipeline Example

```python
from rag.loader import DocumentLoader
from rag.embedder import VectorStore
from rag.retriever import Retriever

# 1. Load documents
loader = DocumentLoader()
all_docs = loader.load_all_documents()

# 2. Create embeddings
vs = VectorStore()
for file_name, chunks in all_docs.items():
    vs.add_documents(chunks, collection_name="documents")

# 3. Save embeddings
vs.save_to_disk("documents")

# 4. Retrieve documents
retriever = Retriever(vs, k=4)
user_query = "What is machine learning?"
results = retriever.retrieve(user_query)

# 5. Assemble context
context = retriever.assemble_context(results, max_tokens=2000)

# 6. Format LLM prompt
llm_prompt = f"""Use the following context to answer the question.

Context:
{context}

Question: {user_query}

Answer:"""

# 7. Send to LLM (next phase)
# response = llm.generate(llm_prompt)
```

---

## Usage Guide

### Quick Start

1. **Place documents** in `./documents/` directory
2. **Run example script**:
   ```bash
   cd /Users/vallabhnaik/Desktop/docufind
   source venv/bin/activate
   python rag_examples.py --auto
   ```

### Run Individual Examples

```bash
python rag_examples.py
```

Then select:
- `1`: Load and split documents
- `2`: Create and store embeddings
- `3`: Semantic search
- `4`: Multi-query RAG
- `5`: Complete RAG pipeline

### Integrate into Your Code

```python
from rag.loader import DocumentLoader
from rag.embedder import VectorStore
from rag.retriever import Retriever

# Your custom integration
```

---

## Performance Tips

1. **Chunk Size**: Balance between context and specificity
   - Smaller chunks: More specific but may lose context
   - Larger chunks: More context but less precise
   - Sweet spot: 800-1200 characters

2. **Chunk Overlap**: Prevents losing information at boundaries
   - Typical: 10-25% of chunk size
   - Our default: 200 chars (20% of 1000)

3. **Score Threshold**: Filter low-quality results
   - 0.0: All results
   - 0.5: Moderate filtering
   - 0.8: Strict filtering

4. **Multi-Query**: Use when first query doesn't retrieve well
   - Generate 3-5 reformulations
   - Combine results
   - Deduplicates automatically

5. **Context Limit**: Balance context quality and token costs
   - 2000 tokens: Quick, focused context
   - 4000 tokens: More comprehensive
   - Use `max_tokens` parameter

---

## Troubleshooting

### Issue: "GOOGLE_API_KEY not found"
**Solution**: Ensure `.env` file has `GOOGLE_API_KEY` set

### Issue: "No documents found"
**Solution**: Place PDF/TXT/MD files in `./documents/` directory

### Issue: "FAISS store is empty"
**Solution**: Run `rag_examples.py` example 2 first to create embeddings

### Issue: "Poor search results"
**Solution**:
1. Try multi-query retrieval
2. Adjust chunk size
3. Check document quality
4. Use reranking methods

---

## Next Steps

### Phase 3B: LLM Integration
- Integrate Google Generative AI (Gemini) for generation
- Build RAG question-answering pipeline
- Add streaming responses

### Phase 4: Advanced Features
- Document summarization
- Answer confidence scoring
- Source citations
- Query refinement

---

## File Structure

```
docufind/
├── rag/
│   ├── __init__.py           # Package exports
│   ├── loader.py             # DocumentLoader class
│   ├── embedder.py           # VectorStore class
│   └── retriever.py          # Retriever class
├── rag_examples.py           # Usage examples and tests
├── embeddings/               # Saved FAISS indexes
│   └── documents/
│       ├── index files
│       └── documents_metadata.json
└── documents/                # Source documents
    ├── ml_basics.txt
    ├── neural_networks.pdf
    └── ...
```

---

## API Reference

### DocumentLoader
- `load_document(file_name)` → List[Document]
- `load_all_documents()` → Dict[str, List[Document]]
- `get_document_info(file_name)` → Dict
- `estimate_tokens(text)` → int

### VectorStore
- `add_documents(documents, collection_name)` → bool
- `similarity_search(query, k, score_threshold)` → List[Tuple]
- `save_to_disk(collection_name)` → bool
- `load_from_disk(collection_name)` → bool
- `get_store_info()` → Dict
- `list_collections()` → List[str]
- `delete_collection(collection_name)` → bool
- `clear_store()` → bool

### Retriever
- `retrieve(query, k, score_threshold)` → List[Tuple[Document, float]]
- `retrieve_multi_query(queries, k, deduplicate)` → List[Tuple[Document, float, List]]
- `assemble_context(results, max_tokens, include_metadata)` → str
- `assemble_context_with_queries(results, max_tokens, include_metadata)` → str
- `get_summary(results)` → Dict
- `rerank_results(results, query, method)` → List[Tuple]

---

## Dependencies

All dependencies are pre-installed:
```
langchain==1.2.15
langchain-core==1.2.28
langchain-community==0.4.1
langchain-google-genai==4.2.1
langchain-text-splitters==1.1.1
faiss-cpu==1.13.2
pypdf==6.10.0
google-generativeai==0.3.1
```

---

## License & Credits

- **LangChain**: LangChain Framework
- **FAISS**: Facebook AI Similarity Search
- **Google Generative AI**: Google Cloud Platform
- **PyPDF**: PDF processing library

---

**Status**: ✅ Phase 7 Complete - RAG System Implemented
**Next**: Phase 3B - LLM Integration for generation
