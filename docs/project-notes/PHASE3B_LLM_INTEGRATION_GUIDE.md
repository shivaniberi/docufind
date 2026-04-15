# Phase 3B: LLM Integration Guide

This guide explains how to integrate the RAG system with Google Generative AI (Gemini) for generating answers.

---

## Overview

The RAG system you now have can retrieve relevant context from documents. The next step is to integrate it with an LLM to generate answers based on the retrieved context.

**Architecture**:
```
User Query → Retriever → Context → LLM → Generated Answer
                ↑                   ↑
              FAISS             Gemini API
```

---

## What You Need for Phase 3B

✅ Already have:
- DocumentLoader: Loads and chunks documents
- VectorStore: Creates embeddings and stores them
- Retriever: Retrieves relevant context
- Google API Key: In `.env` file
- All dependencies: Installed

🔄 Still need to add:
- LLM integration with google-generativeai
- RAG pipeline that combines retrieval + generation
- Error handling for LLM responses
- Streaming response support (optional)

---

## Implementation Steps

### Step 1: Create LLM Module (`rag/llm.py`)

```python
"""LLM Integration Module"""
import os
import logging
from typing import Optional, Iterator
import google.generativeai as genai

logger = logging.getLogger(__name__)

class GenerativeAIModel:
    """Wrapper for Google Generative AI models"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemini-2.0-flash",
        temperature: float = 0.7
    ):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model_name)
        self.temperature = temperature
    
    def generate(self, prompt: str) -> str:
        """Generate text response"""
        response = self.model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=self.temperature
            )
        )
        return response.text
    
    def generate_stream(self, prompt: str) -> Iterator[str]:
        """Generate text response with streaming"""
        response = self.model.generate_content(
            prompt,
            stream=True,
            generation_config=genai.types.GenerationConfig(
                temperature=self.temperature
            )
        )
        for chunk in response:
            if chunk.text:
                yield chunk.text
```

### Step 2: Create RAG Pipeline (`rag/pipeline.py`)

```python
"""Complete RAG Pipeline"""
from rag.loader import DocumentLoader
from rag.embedder import VectorStore
from rag.retriever import Retriever
from rag.llm import GenerativeAIModel
from typing import Dict, Optional

class RAGPipeline:
    """Complete RAG pipeline from documents to answers"""
    
    def __init__(self, embeddings_collection: str = "documents"):
        self.loader = DocumentLoader()
        self.vector_store = VectorStore()
        self.retriever = Retriever(self.vector_store, k=4)
        self.llm = GenerativeAIModel()
        self.collection = embeddings_collection
        
        # Try to load existing embeddings
        if not self.vector_store.load_from_disk(embeddings_collection):
            logger.info("No embeddings found, will create on first use")
    
    def initialize_embeddings(self):
        """Load or create embeddings"""
        if self.vector_store.faiss_store is None:
            docs = self.loader.load_all_documents()
            for file_name, chunks in docs.items():
                self.vector_store.add_documents(chunks, self.collection)
            self.vector_store.save_to_disk(self.collection)
    
    def answer_question(self, question: str) -> Dict:
        """Answer a question using RAG"""
        # 1. Retrieve context
        results = self.retriever.retrieve(question, k=4)
        
        # 2. Assemble context
        context = self.retriever.assemble_context(results)
        
        # 3. Build prompt
        prompt = self._build_prompt(question, context)
        
        # 4. Generate answer
        answer = self.llm.generate(prompt)
        
        return {
            "question": question,
            "answer": answer,
            "sources": [doc.metadata.get("source") for doc, _ in results],
            "relevance_scores": [score for _, score in results]
        }
    
    def _build_prompt(self, question: str, context: str) -> str:
        return f"""Use the following context to answer the question. 
If the context doesn't contain relevant information, say so.

Context:
{context}

Question: {question}

Answer:"""
```

### Step 3: Create API Endpoints (`run_server_rag.py`)

Add new endpoints to your FastAPI server:

```python
@app.post("/api/rag/query")
async def rag_query(request: {"question": str}):
    """Query using RAG pipeline"""
    pipeline = RAGPipeline()
    result = pipeline.answer_question(request.question)
    return result

@app.post("/api/rag/stream")
async def rag_stream(request: {"question": str}):
    """Stream answer using RAG"""
    pipeline = RAGPipeline()
    # Stream implementation here
    pass
```

### Step 4: Update Tools in Document Server

```python
@mcp.tool()
def answer_question_with_rag(question: str) -> dict:
    """Answer a question using RAG with document context"""
    pipeline = RAGPipeline()
    result = pipeline.answer_question(question)
    return result
```

---

## Testing the Integration

### Basic Test
```python
from rag.pipeline import RAGPipeline

pipeline = RAGPipeline()
pipeline.initialize_embeddings()

result = pipeline.answer_question("What is machine learning?")
print(result)
# Output:
# {
#     "question": "What is machine learning?",
#     "answer": "Machine learning is...",
#     "sources": ["ml_basics.txt"],
#     "relevance_scores": [0.92]
# }
```

### Test with Multiple Queries
```python
questions = [
    "What is machine learning?",
    "How does deep learning work?",
    "What are neural networks?"
]

for q in questions:
    result = pipeline.answer_question(q)
    print(f"Q: {q}")
    print(f"A: {result['answer'][:100]}...")
    print()
```

---

## Available LLM Models

Google Generative AI offers several models:

```python
# Fastest, most efficient
model = GenerativeAIModel(model_name="gemini-2.0-flash")

# More capable, slightly slower
model = GenerativeAIModel(model_name="gemini-1.5-pro")

# Balanced
model = GenerativeAIModel(model_name="gemini-1.5-flash")
```

---

## Prompt Engineering Tips

### For Better Answers
```python
prompt = """You are a helpful assistant. Use the provided context to answer questions accurately.

Rules:
1. Only use information from the context
2. If not found in context, say "I don't have this information"
3. Be concise but complete
4. Include relevant details

Context:
{context}

Question: {question}

Answer:"""
```

### For Source Citations
```python
prompt = """Answer the question using the context. Include citations.

Format: "Answer text [Source: filename]"

Context:
{context}

Question: {question}

Answer:"""
```

---

## Performance Optimization

### Caching
```python
from functools import lru_cache

class RAGPipeline:
    @lru_cache(maxsize=100)
    def answer_question(self, question: str) -> str:
        # Cache answers to same question
        pass
```

### Parallel Processing
```python
import asyncio

async def answer_multiple_questions(questions: list):
    tasks = [
        pipeline.answer_question(q) 
        for q in questions
    ]
    return await asyncio.gather(*tasks)
```

### Streaming for Long Responses
```python
def stream_answer(question: str):
    results = self.retriever.retrieve(question)
    context = self.retriever.assemble_context(results)
    prompt = self._build_prompt(question, context)
    
    for chunk in self.llm.generate_stream(prompt):
        yield chunk
```

---

## Error Handling

```python
class RAGPipeline:
    def answer_question(self, question: str) -> Dict:
        try:
            # Validation
            if not question or len(question) < 3:
                return {"error": "Question too short"}
            
            # Initialize if needed
            self.initialize_embeddings()
            
            # Retrieve
            results = self.retriever.retrieve(question)
            if not results:
                return {"answer": "No relevant context found"}
            
            # Generate
            context = self.retriever.assemble_context(results)
            prompt = self._build_prompt(question, context)
            answer = self.llm.generate(prompt)
            
            return {"question": question, "answer": answer}
        
        except Exception as e:
            logger.error(f"RAG error: {str(e)}")
            return {"error": str(e)}
```

---

## Integration Checklist

- [ ] Create `rag/llm.py` with GenerativeAIModel
- [ ] Create `rag/pipeline.py` with RAGPipeline
- [ ] Update `mcp_server/document_server.py` with RAG tools
- [ ] Update `run_server_fixed.py` with RAG endpoints
- [ ] Update `test_ui.html` with new UI elements
- [ ] Create `test_rag.py` for testing
- [ ] Update documentation
- [ ] Commit to git

---

## File Structure After Phase 3B

```
rag/
├── __init__.py
├── loader.py          (Existing)
├── embedder.py        (Existing)
├── retriever.py       (Existing)
├── llm.py             (New)
└── pipeline.py        (New)

run_server_fixed.py    (Updated with RAG endpoints)
mcp_server/
└── document_server.py (Updated with RAG tools)

test_ui.html           (Updated with RAG UI)
test_rag.py            (New - tests)
```

---

## Expected Results

After Phase 3B:
- ✅ RAG system fully integrated
- ✅ Ask questions about documents
- ✅ Get answers with source citations
- ✅ Streaming responses optional
- ✅ Web UI for testing
- ✅ FastMCP tools for integration

---

## Example Workflow

```
User: "What is machine learning?"
  ↓
Retriever finds 4 relevant chunks about ML
  ↓
Context assembled with 3000 token limit
  ↓
Prompt sent to Gemini API
  ↓
LLM generates: "Machine learning is a subset of AI that..."
  ↓
Response returned with sources and scores
```

---

## Next Steps After Phase 3B

- Phase 4: Web UI enhancement (Gradio)
- Phase 5: Production deployment
- Phase 6: Advanced features (summarization, QA)

---

**Ready to build Phase 3B? Use this guide as your roadmap!**

For detailed implementation, see:
- RAG_DOCUMENTATION.md (existing RAG system)
- Phase 3B Implementation Guide (coming next)
