# Storage Locations Guide

Complete reference for where all data is stored in the DocuFind system.

## 📁 Directory Structure & Storage Locations

### 1. **Documents Directory** (Source Files)
```
/Users/vallabhnaik/Desktop/docufind/documents/
```

**What's stored here:**
- Original uploaded documents
- `.txt` files
- `.pdf` files
- `.md` files

**Current files:**
```
documents/
├── ai_future.txt        (1.1 KB)
└── ml_basics.txt        (814 B)
```

**How to add files:**
```bash
cp /your/file.txt /Users/vallabhnaik/Desktop/docufind/documents/
```

---

### 2. **Embeddings Directory** (Vector Data)
```
/Users/vallabhnaik/Desktop/docufind/embeddings/
```

**What's stored here:**
- FAISS vector indexes (`.faiss` files)
- Metadata for each collection
- Embedding pickle files

**Directory structure:**
```
embeddings/
├── default_faiss/               # Default collection
│   ├── index.faiss             # Vector index
│   ├── index.pkl               # Pickle dump
│   └── metadata.json           # Collection metadata
├── my_docs_faiss/              # Custom collection
│   ├── index.faiss
│   ├── index.pkl
│   └── metadata.json
└── another_collection_faiss/
    └── ...
```

**Created automatically when indexing:**
```bash
python << 'EOF'
from rag import RAGPipeline

pipeline = RAGPipeline()
# This creates embeddings in the embeddings/ directory
result = pipeline.index_documents(collection_name="my_docs")
EOF
```

---

### 3. **Session Data** (Memory Storage)
```
/Users/vallabhnaik/Desktop/docufind/sessions/
```

**What's stored here:**
- Session state files (JSON)
- Conversation history
- Session metadata

**Directory structure:**
```
sessions/
├── session_abc123.json
├── session_def456.json
└── ...
```

**Session file format:**
```json
{
  "session_id": "abc123",
  "title": "My Session",
  "created_at": "2026-04-13T21:33:09",
  "state": "active",
  "messages": [
    {
      "role": "user",
      "content": "Hello",
      "timestamp": "2026-04-13T21:33:09"
    }
  ],
  "context": {}
}
```

**Save/load sessions:**
```bash
python << 'EOF'
from memory.session_manager import InMemorySessionService

service = InMemorySessionService()

# Create session
session = service.create_session("My Session")
session.add_message("user", "Hello")

# Save to disk
service.save_session_state(session.session_id, "sessions/my_session.json")

# Load from disk
loaded_session = service.load_session_state("sessions/my_session.json")
EOF
```

---

### 4. **Environment Configuration**
```
/Users/vallabhnaik/Desktop/docufind/.env
```

**What's stored here:**
- API keys (sensitive!)
- Configuration parameters
- Environment variables

**Contents:**
```
GOOGLE_API_KEY=AIza...
PROJECT_ID=projects/...
```

**⚠️ Important:** Never commit `.env` to git!

---

### 5. **Temporary Cache**
```
/Users/vallabhnaik/Desktop/docufind/.cache/
```

**What might be stored here:**
- FAISS cache files
- Embedding model cache
- Google API cache

**Clear cache:**
```bash
rm -rf /Users/vallabhnaik/Desktop/docufind/.cache/
```

---

### 6. **Database Files** (if using SQLite)
```
/Users/vallabhnaik/Desktop/docufind/*.db
```

**Currently:** No SQLite databases (in-memory storage only)

---

## 📊 Storage Hierarchy

```
docufind/
│
├── documents/                  # SOURCE DOCUMENTS
│   ├── ai_future.txt
│   └── ml_basics.txt
│
├── embeddings/                 # VECTOR INDEXES (AUTO-GENERATED)
│   ├── default_faiss/
│   │   ├── index.faiss
│   │   ├── index.pkl
│   │   └── metadata.json
│   └── my_docs_faiss/
│       ├── index.faiss
│       ├── index.pkl
│       └── metadata.json
│
├── sessions/                   # SESSION DATA
│   ├── session_*.json
│   └── ...
│
├── .env                        # CONFIGURATION (SECRET)
├── .cache/                     # TEMPORARY CACHE
│
└── venv/                       # NOT COUNTED (virtual environment)
```

---

## 🔄 Data Flow

### Adding a Document

```
File on disk
    ↓
/documents/my_file.txt
    ↓
DocumentLoader reads file
    ↓
Text splits into chunks
    ↓
GoogleGenerativeAIEmbeddings creates vectors
    ↓
FAISS indexes vectors
    ↓
/embeddings/{collection}_faiss/
    ├── index.faiss
    ├── index.pkl
    └── metadata.json
```

### Using Stored Data

```
User asks question
    ↓
RAGPipeline loads /embeddings/{collection}_faiss/
    ↓
FAISS similarity search
    ↓
Retrieve relevant documents
    ↓
Send to Gemini LLM with context
    ↓
Return answer with sources
```

---

## 💾 Storage Limits & Performance

### File Size Guidelines

| Item | Limit | Performance |
|------|-------|-------------|
| Single TXT file | Unlimited | Fast |
| Single PDF file | ~100 MB | Slow on large files |
| Documents folder | Unlimited | Depends on total |
| Embeddings folder | Limited by RAM | Slower as grows |
| Session files | No limit | Depends on message count |

### Embedding File Size

**Calculation:**
- Each embedding: ~768 dimensions × 4 bytes = 3 KB
- 1000 documents (chunks) = ~3 MB FAISS index
- Plus metadata: +10-20%

**Example:**
```
10 documents (100 chunks) → ~300 KB
100 documents (1000 chunks) → ~3 MB
1000 documents (10000 chunks) → ~30 MB
```

---

## 🔍 Checking Storage

### View documents
```bash
ls -lah /Users/vallabhnaik/Desktop/docufind/documents/
```

### Check embeddings directory
```bash
du -sh /Users/vallabhnaik/Desktop/docufind/embeddings/
ls -lah /Users/vallabhnaik/Desktop/docufind/embeddings/
```

### List collections
```bash
ls -la /Users/vallabhnaik/Desktop/docufind/embeddings/ | grep _faiss
```

### Check session files
```bash
ls -lah /Users/vallabhnaik/Desktop/docufind/sessions/
```

### Total storage used
```bash
du -sh /Users/vallabhnaik/Desktop/docufind/
```

---

## 🧹 Cleanup & Maintenance

### Clear old embeddings
```bash
# Remove a specific collection
rm -rf /Users/vallabhnaik/Desktop/docufind/embeddings/my_docs_faiss/

# Clear all embeddings
rm -rf /Users/vallabhnaik/Desktop/docufind/embeddings/*
```

### Clear old sessions
```bash
# Remove a specific session
rm /Users/vallabhnaik/Desktop/docufind/sessions/session_abc123.json

# Clear all sessions
rm /Users/vallabhnaik/Desktop/docufind/sessions/*
```

### Clear cache
```bash
rm -rf /Users/vallabhnaik/Desktop/docufind/.cache/
```

### Re-index documents
```bash
python << 'EOF'
from rag import RAGPipeline

# Clear all embeddings first
import shutil
shutil.rmtree("/Users/vallabhnaik/Desktop/docufind/embeddings")

# Re-index
pipeline = RAGPipeline()
result = pipeline.index_documents(collection_name="fresh_index")
print(f"Re-indexed {result['documents_indexed']} documents")
EOF
```

---

## 🔐 Security Notes

### Sensitive Data Storage

**API Keys (.env):**
- ⚠️ Never share this file
- ⚠️ Never commit to git
- ✅ Add to `.gitignore`

**Session Files:**
- May contain user queries (not sensitive by default)
- Consider encrypting if storing production data

**Embeddings:**
- Generated from documents
- Can reconstruct document content
- Store securely

### Backup Important Data

```bash
# Backup documents
cp -r /Users/vallabhnaik/Desktop/docufind/documents ~/backup/

# Backup embeddings (large!)
cp -r /Users/vallabhnaik/Desktop/docufind/embeddings ~/backup/

# Backup sessions
cp -r /Users/vallabhnaik/Desktop/docufind/sessions ~/backup/

# Backup configuration
cp /Users/vallabhnaik/Desktop/docufind/.env ~/backup/
```

---

## 📝 Python API for Storage

### Access document directory
```python
from rag import DocumentLoader
from pathlib import Path

loader = DocumentLoader()
documents_dir = loader.documents_dir
print(f"Documents stored in: {documents_dir}")
print(f"Files: {list(documents_dir.glob('*'))}")
```

### Access embeddings directory
```python
from rag import VectorStore

store = VectorStore()
embeddings_dir = store.embeddings_dir
print(f"Embeddings stored in: {embeddings_dir}")
```

### Access sessions directory
```python
from memory.session_manager import InMemorySessionService
from pathlib import Path

service = InMemorySessionService()
sessions_dir = Path("sessions")
print(f"Sessions stored in: {sessions_dir}")
if sessions_dir.exists():
    print(f"Session files: {list(sessions_dir.glob('*.json'))}")
```

---

## 🚀 Storage Configuration

### Change storage locations (optional)

**In your code:**
```python
from rag import DocumentLoader, VectorStore
from memory.session_manager import InMemorySessionService

# Use custom directories
loader = DocumentLoader(documents_dir="/custom/docs/path")
store = VectorStore(embeddings_dir="/custom/embeddings/path")
```

**Via environment variables:**
```bash
export DOCUMENTS_DIR="/custom/docs"
export EMBEDDINGS_DIR="/custom/embeddings"
export SESSIONS_DIR="/custom/sessions"
```

**In .env file:**
```
GOOGLE_API_KEY=AIza...
PROJECT_ID=projects/...
DOCUMENTS_DIR=/Users/vallabhnaik/Desktop/docufind/documents
EMBEDDINGS_DIR=/Users/vallabhnaik/Desktop/docufind/embeddings
SESSIONS_DIR=/Users/vallabhnaik/Desktop/docufind/sessions
```

---

## 📊 Storage Summary

| Location | Type | Size | Auto-created | Editable |
|----------|------|------|-------------|----------|
| `/documents/` | Source | Variable | Yes | Yes |
| `/embeddings/` | Vectors | MB-GB | Yes | No |
| `/sessions/` | JSON | KB-MB | Yes | Yes |
| `/.env` | Config | <1 KB | No | Yes |
| `/.cache/` | Temp | MB | Yes | No |

**Pro Tips:**
- ✅ Add documents to `/documents/`
- ✅ Embeddings auto-generate in `/embeddings/`
- ✅ Sessions auto-save to `/sessions/`
- ✅ Regularly back up important data
- ⚠️ Keep `.env` secret and secure
