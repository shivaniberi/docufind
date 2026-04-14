# Phase 4-5 Testing Guide

Comprehensive guide for testing all Phase 4-5 components.

## Quick Test (5 minutes)

### Run All Tests at Once
```bash
cd /Users/vallabhnaik/Desktop/docufind
source venv/bin/activate
python test_phase4_5.py
```

**Expected Output:**
```
✅ Passed: 44
❌ Failed: 0
📊 Total:  44
📈 Success Rate: 100.0%
```

## Component-Level Testing

### 1. Session Manager Testing
```bash
python << 'EOF'
from memory.session_manager import InMemorySessionService

# Create service
service = InMemorySessionService()

# Create session
session = service.create_session("Test")

# Add messages
session.add_message("user", "Hello!")
session.add_message("assistant", "Hi!")

# Check results
assert len(session.messages) == 2
print("✅ Session Manager working!")
EOF
```

### 2. RAG Pipeline Testing
```bash
python << 'EOF'
from rag import RAGPipeline, RAGConfig

# Create pipeline
config = RAGConfig(k=4, llm_model="gemini-2.0-flash")
pipeline = RAGPipeline(config=config)

# Get status
status = pipeline.get_status()
print("✅ RAG Pipeline Status:", status['pipeline_status'])
EOF
```

### 3. Agent Testing
```bash
python << 'EOF'
from agents.summarizer_agent import SummarizerAgent
from agents.orchestrator import OrchestratorAgent

# Test Summarizer
summarizer = SummarizerAgent()
print("✅ SummarizerAgent initialized")

# Test Orchestrator
orchestrator = OrchestratorAgent()
print("✅ OrchestratorAgent initialized")
print("   Status:", orchestrator.get_status()['status'])
EOF
```

## Integration Testing

### Full System Integration Test
```bash
python << 'EOF'
import os
from pathlib import Path

# Load environment
with open(".env") as f:
    for line in f:
        if "=" in line and not line.startswith("#"):
            key, val = line.strip().split("=", 1)
            os.environ[key] = val

# Import all components
from memory.session_manager import InMemorySessionService
from agents.summarizer_agent import SummarizerAgent
from agents.orchestrator import OrchestratorAgent
from rag.pipeline import RAGPipeline

# Initialize
session_service = InMemorySessionService()
summarizer = SummarizerAgent()
orchestrator = OrchestratorAgent()
pipeline = RAGPipeline()

# Test session
session = session_service.create_session("Integration Test")
session.add_message("user", "Test message")

print("✅ All components initialized successfully!")
print("✅ System ready for Phase 5 UI deployment!")
EOF
```

## Server Testing

### Test FastAPI Server with RAG

**Terminal 1 - Start Server:**
```bash
cd /Users/vallabhnaik/Desktop/docufind
source venv/bin/activate
python run_server_with_rag.py
```

**Terminal 2 - Test Endpoints:**
```bash
# Test health check
curl http://127.0.0.1:8000/health

# List documents
curl -X POST http://127.0.0.1:8000/tools/list_documents/call \
  -H "Content-Type: application/json" \
  -d '{}'

# Index documents for RAG
curl -X POST http://127.0.0.1:8000/rag/index \
  -H "Content-Type: application/json" \
  -d '{"collection_name": "demo"}'

# Search documents
curl -X POST http://127.0.0.1:8000/rag/search \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "collection_name": "demo"}'

# Get RAG status
curl http://127.0.0.1:8000/rag/status
```

## File Structure Verification

Verify all required files exist:

```bash
# Check Phase 4-5 files
ls -lh agents/summarizer_agent.py    # ~12KB
ls -lh agents/orchestrator.py        # ~13KB
ls -lh agents/__init__.py            # ~500B

ls -lh memory/session_manager.py     # ~11KB
ls -lh memory/__init__.py            # ~400B

ls -lh rag/llm.py                    # ~8KB
ls -lh rag/pipeline.py               # ~10KB

ls -lh run_server_with_rag.py        # ~9KB
ls -lh rag_pipeline_examples.py      # ~9KB
ls -lh test_phase4_5.py              # ~12KB
```

## Dependency Verification

Check all required packages:

```bash
source venv/bin/activate
pip list | grep -E "anthropic|pydantic|langchain|google|fastapi|uvicorn"
```

Expected packages:
- ✅ anthropic >= 0.7.0
- ✅ pydantic >= 2.0
- ✅ langchain >= 0.1.0
- ✅ langchain-community >= 0.0.1
- ✅ langchain-google-genai >= 0.0.1
- ✅ google-generativeai >= 0.3.0
- ✅ fastapi >= 0.100.0
- ✅ uvicorn >= 0.23.0

## Environment Configuration

Verify `.env` file:

```bash
cat .env
```

Should contain:
```
GOOGLE_API_KEY=AIza...
PROJECT_ID=projects/...
```

## Test Results Summary

### All Tests Passing ✅
- 44/44 tests passed
- 100% success rate

### Component Status
| Component | Status | Details |
|-----------|--------|---------|
| Session Manager | ✅ | 8/8 tests passed |
| RAG Pipeline | ✅ | 7/7 tests passed |
| Agents | ✅ | 4/4 tests passed |
| Orchestrator | ✅ | 5/5 tests passed |
| File Structure | ✅ | 9/9 files present |
| Dependencies | ✅ | 8/8 packages available |
| Environment | ✅ | 3/3 config items set |

## Troubleshooting

### ImportError: No module named 'anthropic'
```bash
source venv/bin/activate
pip install anthropic
```

### ImportError: No module named 'agents'
Make sure `agents/__init__.py` exists:
```bash
ls agents/__init__.py
```

### API Key Error
Check `.env` file:
```bash
grep GOOGLE_API_KEY .env
```

### Port Already in Use
Kill existing server:
```bash
pkill -f "python run_server_with_rag.py"
sleep 2
python run_server_with_rag.py
```

## Next Steps

1. ✅ All tests passing - Phase 4-5 complete
2. Start FastAPI server: `python run_server_with_rag.py`
3. Build Gradio UI (Phase 5): `python ui/app.py`
4. Access UI at: `http://localhost:7860`

## Performance Metrics

### Test Execution Time
- Total test time: ~3 seconds
- Average per test: ~70ms
- All tests sequential

### Component Initialization Time
- Session Manager: ~1ms
- RAG Pipeline: ~2.0 seconds
- Agents: ~100ms each
- Total: ~2.2 seconds

## Notes

- Free tier rate limits may apply to Claude/Gemini calls
- Ensure API keys are properly configured
- Use `.env` file for sensitive configuration
- Always activate virtual environment before testing

## Getting Help

If tests fail:
1. Check `.env` file configuration
2. Verify all dependencies installed: `pip list`
3. Check virtual environment active: `which python`
4. Run individual component tests for debugging
5. Check error messages in test output
