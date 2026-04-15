# Document Management Guide

## Document Directory Location

All documents should be added to:
```
/Users/vallabhnaik/Desktop/docufind/documents/
```

## Current Documents

The `documents/` folder currently contains:
- `ai_future.txt` - Sample AI document
- `ml_basics.txt` - Sample machine learning document

## How to Add Documents Manually

### Method 1: Copy Files to Documents Folder

**Supported File Formats:**
- `.txt` - Plain text files
- `.pdf` - PDF documents
- `.md` - Markdown files

**Steps:**

1. **For Text Files (.txt or .md):**
   ```bash
   # Copy your file to the documents folder
   cp /path/to/your/file.txt /Users/vallabhnaik/Desktop/docufind/documents/
   cp /path/to/your/file.md /Users/vallabhnaik/Desktop/docufind/documents/
   ```

2. **For PDF Files (.pdf):**
   ```bash
   # Copy your PDF to the documents folder
   cp /path/to/your/file.pdf /Users/vallabhnaik/Desktop/docufind/documents/
   ```

3. **Verify Files Added:**
   ```bash
   ls -la /Users/vallabhnaik/Desktop/docufind/documents/
   ```

### Method 2: Using the API

**Start the server:**
```bash
cd /Users/vallabhnaik/Desktop/docufind
source venv/bin/activate
python run_server_with_rag.py
```

**Upload documents via API:**
```bash
# Upload a text file
curl -X POST http://127.0.0.1:8000/tools/save_document/call \
  -H "Content-Type: application/json" \
  -d '{
    "file_name": "my_document.txt",
    "content": "Your document content here..."
  }'

# Or upload a PDF (requires fastmcp integration)
curl -X POST http://127.0.0.1:8000/documents/upload \
  -F "file=@/path/to/file.pdf"
```

### Method 3: Using Python

**Programmatically add documents:**
```python
from rag import DocumentLoader
from pathlib import Path

# Initialize loader
loader = DocumentLoader()

# Load documents from folder
documents = loader.load_from_directory("/Users/vallabhnaik/Desktop/docufind/documents")

# Or load a specific file
documents = loader.load_documents(["/Users/vallabhnaik/Desktop/docufind/documents/my_file.txt"])

print(f"Loaded {len(documents)} documents")
```

## Document Organization Tips

### Create Subdirectories (Optional)

```bash
cd /Users/vallabhnaik/Desktop/docufind/documents

# Create categories
mkdir -p ai
mkdir -p ml
mkdir -p data_science
mkdir -p general

# Add files to categories
cp ai_book.pdf ai/
cp ml_paper.pdf ml/
cp data_handbook.txt data_science/
```

### Naming Convention

Use clear, descriptive filenames:

❌ Bad:
```
doc1.txt
file_2024.pdf
untitled.md
```

✅ Good:
```
ai_future_trends_2024.txt
machine_learning_basics.pdf
data_science_handbook.md
```

## RAG Pipeline Document Processing

### Automatic Indexing

Once documents are in the `/documents` folder:

```bash
# Index all documents
python << 'EOF'
from rag import RAGPipeline, RAGConfig

config = RAGConfig(k=4, llm_model="gemini-2.0-flash")
pipeline = RAGPipeline(config=config)

# Index documents
result = pipeline.index_documents(collection_name="my_docs")
print(f"Indexed {result['documents_indexed']} documents")
EOF
```

### Query Indexed Documents

```python
from rag import RAGPipeline, RAGConfig

config = RAGConfig(k=4, llm_model="gemini-2.0-flash")
pipeline = RAGPipeline(config=config)

# Answer question based on documents
result = pipeline.answer_question(
    question="What is machine learning?",
    collection="my_docs"
)
print(result['answer'])
```

## File Size Considerations

**Recommended sizes:**
- Small files: < 5 MB (instant processing)
- Medium files: 5-50 MB (few seconds)
- Large files: > 50 MB (may take time)

**Max supported:**
- Text files: Unlimited
- PDF files: Limited by available memory
- Chunk size: 1000 characters (default, configurable)

## Document Structure

### Text File Format (.txt)

```
Title of Document

Introduction paragraph...

Section 1: Main Topic
Content for section 1...

Section 2: Another Topic
Content for section 2...

Conclusion...
```

### Markdown Format (.md)

```markdown
# Document Title

## Introduction
Intro text...

## Section 1
Content...

## Section 2
Content...

## Conclusion
Final thoughts...
```

### PDF Format (.pdf)

PDFs are automatically extracted and processed. Any PDF with text content works.

## Checking Indexed Documents

```bash
# List all documents in a collection
python << 'EOF'
from rag import RAGPipeline

pipeline = RAGPipeline()
status = pipeline.get_status()
print(f"Indexed collections: {status['indexed_collections']}")
EOF
```

## Troubleshooting

### Documents Not Found

**Issue:** Documents folder empty or files not loading

**Solution:**
```bash
# Check documents folder exists
ls -la /Users/vallabhnaik/Desktop/docufind/documents/

# Check file permissions
chmod 644 /Users/vallabhnaik/Desktop/docufind/documents/*

# Verify file format is supported
file /Users/vallabhnaik/Desktop/docufind/documents/your_file.txt
```

### Files Not Indexing

**Issue:** Documents not appearing in search results

**Solution:**
```bash
# Re-index collection
python << 'EOF'
from rag import RAGPipeline

pipeline = RAGPipeline()
pipeline.clear_cache()  # Clear old index
result = pipeline.index_documents(collection_name="my_docs")
print(f"Re-indexed: {result}")
EOF
```

### Memory Error for Large Files

**Issue:** Out of memory when processing large PDFs

**Solution:**
```python
# Process files in chunks
from rag import DocumentLoader

loader = DocumentLoader(chunk_size=500)  # Reduce chunk size
documents = loader.load_documents(["large_file.pdf"])
```

## Batch Adding Documents

### Script to Add Multiple Files

Create a script `add_documents.sh`:

```bash
#!/bin/bash

SOURCE_DIR="$1"
DEST_DIR="/Users/vallabhnaik/Desktop/docufind/documents"

if [ -z "$SOURCE_DIR" ]; then
    echo "Usage: ./add_documents.sh /path/to/source/folder"
    exit 1
fi

echo "Copying documents from $SOURCE_DIR to $DEST_DIR..."

# Copy all supported files
cp "$SOURCE_DIR"/*.txt "$DEST_DIR/" 2>/dev/null
cp "$SOURCE_DIR"/*.pdf "$DEST_DIR/" 2>/dev/null
cp "$SOURCE_DIR"/*.md "$DEST_DIR/" 2>/dev/null

# Count files
COUNT=$(ls -1 "$DEST_DIR" | wc -l)
echo "Total documents in folder: $COUNT"

echo "Done! Files are ready for indexing."
```

**Usage:**
```bash
chmod +x add_documents.sh
./add_documents.sh /path/to/your/documents
```

## Programmatic Document Addition

### Python Script Example

```python
#!/usr/bin/env python3
"""Add documents to the RAG system."""

import os
from pathlib import Path
from rag import RAGPipeline, RAGConfig

def add_documents_from_folder(folder_path: str, collection_name: str = "documents"):
    """Add all documents from a folder to RAG system."""
    
    docs_folder = Path("/Users/vallabhnaik/Desktop/docufind/documents")
    
    # Copy files
    source = Path(folder_path)
    if not source.exists():
        print(f"Error: Source folder {folder_path} not found")
        return
    
    print(f"Copying documents from {source}...")
    for file_path in source.glob("*"):
        if file_path.suffix in [".txt", ".pdf", ".md"]:
            target = docs_folder / file_path.name
            os.system(f"cp {file_path} {target}")
            print(f"  ✓ {file_path.name}")
    
    # Index documents
    print(f"\nIndexing documents...")
    config = RAGConfig(k=4, llm_model="gemini-2.0-flash")
    pipeline = RAGPipeline(config=config)
    result = pipeline.index_documents(collection_name=collection_name)
    
    print(f"✓ Indexed {result['documents_indexed']} documents")
    print(f"✓ Collection: {collection_name}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python add_documents.py /path/to/source/folder [collection_name]")
        sys.exit(1)
    
    folder = sys.argv[1]
    collection = sys.argv[2] if len(sys.argv) > 2 else "documents"
    
    add_documents_from_folder(folder, collection)
```

**Usage:**
```bash
source venv/bin/activate
python add_documents.py /path/to/your/documents my_collection
```

## Summary

| Method | Use Case | Command |
|--------|----------|---------|
| **Manual Copy** | Adding 1-2 files | `cp file.txt documents/` |
| **API Upload** | Programmatic addition | `curl -X POST .../save_document` |
| **Batch Script** | Adding many files | `./add_documents.sh /source` |
| **Python Script** | Automation | `python add_documents.py /source` |

## Quick Reference

```bash
# Location to add documents
cd /Users/vallabhnaik/Desktop/docufind/documents

# Supported formats
# - .txt (text files)
# - .pdf (PDF documents)
# - .md (Markdown files)

# View current documents
ls -lh

# Add a file
cp ~/Downloads/my_document.txt .

# Index for RAG
python << 'EOF'
from rag import RAGPipeline
pipeline = RAGPipeline()
pipeline.index_documents(collection_name="my_docs")
EOF

# Query documents
python << 'EOF'
from rag import RAGPipeline
pipeline = RAGPipeline()
result = pipeline.answer_question(
    question="Your question here",
    collection="my_docs"
)
print(result['answer'])
EOF
```

## Notes

- Documents are automatically processed and chunked
- The RAG system uses semantic search to find relevant content
- Embedding generation may take a few seconds for large documents
- API key must be configured in `.env` file
- Free tier has rate limits - use wisely
