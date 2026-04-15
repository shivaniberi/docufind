#!/usr/bin/env python3
"""
Comprehensive Test Suite for Phase 4-5 Implementation

Tests all new components:
- Summarizer Agent with reflection pattern
- Orchestrator Agent with ReAct loop
- Session Manager with memory
- RAG Pipeline integration
- FastAPI server with RAG endpoints

Run with: python test_phase4_5.py
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment
def load_env():
    """Load .env file."""
    env_path = Path(".env")
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    key, val = line.strip().split("=", 1)
                    os.environ[key] = val


class TestResults:
    """Track test results."""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []
    
    def add_pass(self, test_name: str, message: str = ""):
        self.passed += 1
        self.tests.append(("PASS", test_name, message))
        logger.info(f"[PASS] {test_name}: {message}")
    
    def add_fail(self, test_name: str, error: str):
        self.failed += 1
        self.tests.append(("FAIL", test_name, error))
        logger.error(f"[FAIL] {test_name}: {error}")
    
    def summary(self):
        total = self.passed + self.failed
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Total:  {total}")
        print(f"Success Rate: {(self.passed/total*100):.1f}%" if total > 0 else "N/A")
        print("="*70)


# Test 1: Session Manager

def test_session_manager(results: TestResults):
    """Test session and memory management."""
    print("\n" + "="*70)
    print("TEST 1: Session Manager")
    print("="*70)
    
    try:
        from memory.session_manager import (
            InMemorySessionService,
            Session,
            SessionState,
            ContextManager
        )
        
        # Test 1a: Create session service
        service = InMemorySessionService()
        results.add_pass("SessionService Creation", "Service initialized")
        
        # Test 1b: Create session
        session = service.create_session("Test Session")
        assert session.session_id is not None
        results.add_pass("Session Creation", f"Session ID: {session.session_id[:8]}...")
        
        # Test 1c: Add messages
        session.add_message("user", "Hello, what is AI?")
        session.add_message("assistant", "AI is artificial intelligence...")
        assert len(session.messages) == 2
        results.add_pass("Message Addition", "2 messages added")
        
        # Test 1d: Get conversation history
        history = session.get_conversation_history()
        assert len(history) == 2
        results.add_pass("Conversation History", "History retrieved correctly")
        
        # Test 1e: Context management
        session.set_context("model", "gemini-2.0-flash")
        assert session.get_context("model") == "gemini-2.0-flash"
        results.add_pass("Context Management", "Context stored and retrieved")
        
        # Test 1f: List sessions
        sessions = service.list_sessions()
        assert len(sessions) >= 1
        results.add_pass("List Sessions", f"{len(sessions)} session(s) found")
        
        # Test 1g: Context Manager
        ctx_mgr = ContextManager()
        ctx_mgr.set_global("api_key", "test_key")
        assert ctx_mgr.get_global("api_key") == "test_key"
        results.add_pass("Context Manager", "Global context working")
        
        # Test 1h: Session statistics
        stats = service.get_statistics()
        assert "total_sessions" in stats
        results.add_pass("Session Statistics", f"Total sessions: {stats['total_sessions']}")
        
    except Exception as e:
        results.add_fail("Session Manager Tests", str(e))


# Test 2: RAG Pipeline Components

def test_rag_pipeline(results: TestResults):
    """Test RAG pipeline components."""
    print("\n" + "="*70)
    print("TEST 2: RAG Pipeline")
    print("="*70)
    
    try:
        from rag import (
            RAGPipeline,
            RAGConfig,
            GenerativeAIModel,
            GenerationConfig,
            DocumentLoader,
            VectorStore,
            Retriever
        )
        
        # Test 2a: Configuration classes
        gen_config = GenerationConfig(temperature=0.7, max_output_tokens=1024)
        assert gen_config.temperature == 0.7
        results.add_pass("GenerationConfig", "Configuration created")
        
        rag_config = RAGConfig(k=4, llm_model="gemini-2.0-flash")
        assert rag_config.k == 4
        results.add_pass("RAGConfig", "RAG configuration created")
        
        # Test 2b: Document Loader
        loader = DocumentLoader()
        assert loader is not None
        results.add_pass("DocumentLoader", "Loader initialized")
        
        # Test 2c: Vector Store
        store = VectorStore()
        assert store is not None
        results.add_pass("VectorStore", "Store initialized")
        
        # Test 2d: Retriever
        retriever = Retriever(store, k=4)
        assert retriever is not None
        results.add_pass("Retriever", "Retriever initialized")
        
        # Test 2e: RAG Pipeline initialization
        pipeline = RAGPipeline(config=rag_config)
        assert pipeline is not None
        results.add_pass("RAGPipeline", "Pipeline initialized")
        
        # Test 2f: Pipeline status
        status = pipeline.get_status()
        assert "config" in status
        results.add_pass("Pipeline Status", f"Status retrieved: {status['pipeline_status']}")
        
        # Test 2g: LLM Model structure
        llm = GenerativeAIModel(model_name="gemini-2.0-flash")
        assert llm is not None
        info = llm.get_model_info()
        assert info["model_name"] == "gemini-2.0-flash"
        results.add_pass("GenerativeAIModel", f"Model: {info['model_name']}")
        
    except Exception as e:
        results.add_fail("RAG Pipeline Tests", str(e))


# Test 3: Agent Components

def test_agents(results: TestResults):
    """Test agent components."""
    print("\n" + "="*70)
    print("TEST 3: Agent Components")
    print("="*70)
    
    try:
        from agents.summarizer_agent import (
            SummarizerAgent,
            SummarizerConfig,
            SummaryResult,
            SummaryQuality
        )
        
        # Test 3a: Summarizer Configuration
        config = SummarizerConfig(
            model_name="claude-3-5-sonnet-20241022",
            enable_reflection=True,
            max_reflection_iterations=2
        )
        assert config.enable_reflection is True
        results.add_pass("SummarizerConfig", "Configuration created")
        
        # Test 3b: Summarizer Agent initialization
        agent = SummarizerAgent(config=config)
        assert agent is not None
        results.add_pass("SummarizerAgent", "Agent initialized")
        
        # Test 3c: SummaryResult model
        result = SummaryResult(
            summary="Test summary",
            original_length=100,
            summary_length=20,
            compression_ratio=0.2,
            key_points=["Point 1", "Point 2"],
            quality_score=0.8,
            quality_level=SummaryQuality.GOOD
        )
        assert result.summary == "Test summary"
        results.add_pass("SummaryResult", "Result model created")
        
    except Exception as e:
        results.add_fail("Agent Components Tests", str(e))


def test_orchestrator(results: TestResults):
    """Test orchestrator agent."""
    print("\n" + "="*70)
    print("TEST 4: Orchestrator Agent")
    print("="*70)
    
    try:
        from agents.orchestrator import (
            OrchestratorAgent,
            OrchestratorConfig,
            MCPToolset,
            ActionResult
        )
        
        # Test 4a: MCP Toolset
        toolset = MCPToolset(server_url="http://127.0.0.1:8000")
        assert toolset is not None
        results.add_pass("MCPToolset", "Toolset initialized")
        
        # Test 4b: Orchestrator Configuration
        config = OrchestratorConfig(
            model_name="claude-3-5-sonnet-20241022",
            mcp_server_url="http://127.0.0.1:8000"
        )
        assert config.model_name == "claude-3-5-sonnet-20241022"
        results.add_pass("OrchestratorConfig", "Configuration created")
        
        # Test 4c: Orchestrator Agent
        orchestrator = OrchestratorAgent(config=config)
        assert orchestrator is not None
        results.add_pass("OrchestratorAgent", "Agent initialized")
        
        # Test 4d: Agent status
        status = orchestrator.get_status()
        assert "agent_type" in status
        results.add_pass("Agent Status", f"Status: {status['status']}")
        
        # Test 4e: Action Result model
        action = ActionResult(
            action="test_action",
            success=True,
            result={"data": "test"}
        )
        assert action.success is True
        results.add_pass("ActionResult", "Action result model created")
        
    except Exception as e:
        results.add_fail("Orchestrator Agent Tests", str(e))


# Test 5: File Structure

def test_file_structure(results: TestResults):
    """Test that all required files exist."""
    print("\n" + "="*70)
    print("TEST 5: File Structure")
    print("="*70)
    
    required_files = {
        "agents/summarizer_agent.py": "Summarizer agent module",
        "agents/orchestrator.py": "Orchestrator agent module",
        "agents/graph.py": "LangGraph multi-agent graph",
        "agents/reflection_agent.py": "Reflection critique agent",
        "agents/__init__.py": "Agents package init",
        "memory/session_manager.py": "Session manager module",
        "memory/__init__.py": "Memory package init",
        "rag/llm.py": "LLM integration module",
        "rag/pipeline.py": "RAG pipeline module",
        "rag/bm25_retriever.py": "BM25 sparse retriever",
        "rag/rrf.py": "Reciprocal rank fusion module",
        "run.py": "Unified FastAPI server with RAG",
        "ui/streamlit_app.py": "Primary Streamlit UI",
        "rag_pipeline_examples.py": "RAG pipeline examples",
    }
    
    for filepath, description in required_files.items():
        full_path = Path(filepath)
        if full_path.exists():
            size = full_path.stat().st_size
            results.add_pass(f"File: {filepath}", f"{description} ({size} bytes)")
        else:
            results.add_fail(f"File: {filepath}", f"Missing: {description}")


# Test 6: Imports and Dependencies

def test_dependencies(results: TestResults):
    """Test that all dependencies are available."""
    print("\n" + "="*70)
    print("TEST 6: Dependencies")
    print("="*70)
    
    dependencies = {
        "anthropic": "Anthropic Claude API",
        "pydantic": "Data validation",
        "langchain_core": "LangChain core",
        "langchain_community": "LangChain community",
        "langchain_google_genai": "Google Generative AI",
        "fastapi": "FastAPI framework",
        "uvicorn": "ASGI server",
        "google.generativeai": "Google Generative AI SDK",
    }
    
    for module_name, description in dependencies.items():
        try:
            __import__(module_name)
            results.add_pass(f"Import: {module_name}", description)
        except ImportError as e:
            results.add_fail(f"Import: {module_name}", f"{description} - {str(e)}")


# Test 7: Configuration and Environment

def test_environment(results: TestResults):
    """Test environment configuration."""
    print("\n" + "="*70)
    print("TEST 7: Environment Configuration")
    print("="*70)
    
    # Test .env file
    env_path = Path(".env")
    if env_path.exists():
        results.add_pass(".env file", "Found")
        
        # Test API key
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            results.add_pass("GOOGLE_API_KEY", f"Set ({len(api_key)} chars)")
        else:
            results.add_fail("GOOGLE_API_KEY", "Not set in .env")
        
        # Test PROJECT_ID
        project_id = os.getenv("PROJECT_ID")
        if project_id:
            results.add_pass("PROJECT_ID", f"Set ({project_id})")
        else:
            results.add_fail("PROJECT_ID", "Not set in .env")
    else:
        results.add_fail(".env file", "Not found")


# Main Test Runner

def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("PHASE 4-5 COMPREHENSIVE TEST SUITE")
    print("="*70)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load environment
    load_env()
    
    # Create results tracker
    results = TestResults()
    
    # Run all tests
    test_session_manager(results)
    test_rag_pipeline(results)
    test_agents(results)
    test_orchestrator(results)
    test_file_structure(results)
    test_dependencies(results)
    test_environment(results)
    
    # Print summary
    results.summary()
    
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Exit with appropriate code
    sys.exit(0 if results.failed == 0 else 1)


if __name__ == "__main__":
    main()
