#!/usr/bin/env python3
"""
Gradio UI for DocuFind - Phase 5

Complete web interface featuring:
- Document management (upload, list, read, delete)
- RAG question answering with source citations
- Semantic document search
- AI-powered summarization
- Agent orchestration interface
- Session management and history

Run with: python ui/app.py
Open at: http://localhost:7860
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Tuple, Optional

import gradio as gr
import pandas as pd

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                key, val = line.strip().split("=", 1)
                os.environ[key] = val

from rag import RAGPipeline, RAGConfig
from agents import SummarizerAgent, OrchestratorAgent
from memory import InMemorySessionService, ContextManager

# Initialize components
rag_pipeline = None
summarizer = None
orchestrator = None
session_service = InMemorySessionService()
context_manager = ContextManager()

def init_components():
    """Initialize AI components."""
    global rag_pipeline, summarizer, orchestrator
    
    try:
        # Initialize RAG pipeline
        rag_config = RAGConfig(k=4, llm_model="gemini-2.0-flash")
        rag_pipeline = RAGPipeline(config=rag_config)
        logger.info("✅ RAG Pipeline initialized")
        
        # Initialize summarizer
        summarizer = SummarizerAgent()
        logger.info("✅ Summarizer Agent initialized")
        
        # Initialize orchestrator
        orchestrator = OrchestratorAgent()
        logger.info("✅ Orchestrator Agent initialized")
        
        return True
    except Exception as e:
        logger.error(f"Error initializing components: {str(e)}")
        return False

# ============================================================================
# RAG Tab Functions
# ============================================================================

def index_documents_ui(progress=gr.Progress()):
    """Index documents for RAG."""
    progress(0, desc="Starting indexing...")
    
    try:
        progress(0.5, desc="Indexing documents...")
        result = rag_pipeline.index_documents(collection_name="demo")
        
        progress(1.0, desc="Complete!")
        
        return f"""
✅ **Documents Indexed Successfully**

- Documents loaded: {result['documents_loaded']}
- Chunks created: {result['chunks_created']}
- Collection: {result['collection_name']}
- Status: {result['status']}
        """
    except Exception as e:
        return f"❌ Error: {str(e)}"

def rag_search_ui(query: str, k: int = 5) -> str:
    """Search documents using RAG."""
    if not query:
        return "Please enter a search query."
    
    try:
        results = rag_pipeline.search(query, collection_name="demo", k=k)
        
        if not results:
            return "No results found."
        
        output = f"**Search Results for: '{query}'**\n\n"
        for i, result in enumerate(results, 1):
            output += f"**{i}. {result['file']}** (Score: {result['score']})\n"
            output += f"   {result['content']}\n\n"
        
        return output
    except Exception as e:
        return f"❌ Error: {str(e)}"

def rag_answer_ui(question: str, use_multi_query: bool = False) -> Tuple[str, str]:
    """Answer a question using RAG."""
    if not question:
        return "Please enter a question.", ""
    
    try:
        result = rag_pipeline.answer_question(
            question,
            collection_name="demo",
            use_multi_query=use_multi_query
        )
        
        if result["status"] == "success":
            answer = result["answer"]
            
            sources = "**Sources:**\n"
            for i, source in enumerate(result.get("sources", []), 1):
                sources += f"{i}. {source['file']} (Score: {source['score']})\n"
            
            return answer, sources
        else:
            return f"❌ Error: {result.get('error', 'Unknown error')}", ""
    except Exception as e:
        return f"❌ Error: {str(e)}", ""

# ============================================================================
# Summarization Tab Functions
# ============================================================================

def summarize_text_ui(text: str, length_pref: str = "medium") -> str:
    """Summarize text."""
    if not text:
        return "Please enter text to summarize."
    
    try:
        result = summarizer.summarize(text, length_preference=length_pref)
        
        output = f"""
**Summary Result**

**Summary:**
{result.summary}

**Metrics:**
- Original length: {result.original_length} words
- Summary length: {result.summary_length} words
- Compression ratio: {result.compression_ratio}
- Quality score: {result.quality_score:.2f}/1.0
- Quality level: {result.quality_level.value}

**Key Points:**
{chr(10).join(f'- {p}' for p in result.key_points)}

**Improvement Suggestions:**
{chr(10).join(f'- {s}' for s in result.improvement_suggestions)}
        """
        return output
    except Exception as e:
        return f"❌ Error: {str(e)}"

# ============================================================================
# Agent Tab Functions
# ============================================================================

def agent_process_ui(goal: str, context: str = "") -> Tuple[str, str]:
    """Process a goal using the orchestrator agent."""
    if not goal:
        return "Please enter a goal.", ""
    
    try:
        result = orchestrator.process(goal, context if context else None)
        
        goal_result = f"""
**Goal:** {result['goal']}

**Success:** {result['success']}

**Final Answer:**
{result['final_answer']}
        """
        
        actions = "**Recent Actions:**\n"
        for i, action in enumerate(result.get('actions', []), 1):
            actions += f"{i}. {action['action']}: {'✅' if action['success'] else '❌'}\n"
        
        return goal_result, actions
    except Exception as e:
        return f"❌ Error: {str(e)}", ""

def agent_chat_ui(message: str, history: List[List[str]]) -> List[List[str]]:
    """Chat with the orchestrator agent."""
    try:
        response = orchestrator.chat(message)
        history.append([message, response])
        return history
    except Exception as e:
        return history

# ============================================================================
# Session Tab Functions
# ============================================================================

def get_sessions_list() -> pd.DataFrame:
    """Get list of all sessions."""
    sessions = session_service.list_sessions()
    
    data = []
    for session in sessions:
        data.append({
            "Session ID": session["session_id"][:8] + "...",
            "Title": session["title"],
            "State": session["state"],
            "Messages": session["message_count"],
            "Created": session["created_at"][:10]
        })
    
    return pd.DataFrame(data)

def create_session_ui(title: str) -> str:
    """Create a new session."""
    if not title:
        return "Please enter a session title."
    
    session = session_service.create_session(title)
    return f"✅ Created session: {title}\nSession ID: {session.session_id}"

def get_session_stats() -> str:
    """Get session statistics."""
    stats = session_service.get_statistics()
    
    return f"""
**Session Statistics**

- Total sessions: {stats['total_sessions']}
- Active sessions: {stats['active_sessions']}
- Total messages: {stats['total_messages']}
- Avg messages/session: {stats['average_messages_per_session']:.1f}
    """

# ============================================================================
# Build Gradio Interface
# ============================================================================

def build_interface():
    """Build the Gradio interface."""
    
    with gr.Blocks(title="DocuFind - AI Document Assistant", theme=gr.themes.Soft()) as demo:
        gr.Markdown("""
# 🎯 DocuFind - AI Document Assistant
        
Complete document management and question-answering system with RAG, summarization, and intelligent agents.
        """)
        
        # ====================================================================
        # RAG Tab
        # ====================================================================
        with gr.Tab("📚 RAG Question Answering"):
            gr.Markdown("### Retrieve information from your documents and get answers with source citations")
            
            with gr.Row():
                with gr.Column(scale=2):
                    rag_question = gr.Textbox(
                        label="Question",
                        placeholder="Ask a question about your documents...",
                        lines=3
                    )
                    with gr.Row():
                        use_multi = gr.Checkbox(label="Use multi-query expansion", value=False)
                        rag_submit = gr.Button("🔍 Answer Question", variant="primary")
                
                with gr.Column(scale=1):
                    index_btn = gr.Button("📖 Index Documents", size="lg")
                    gr.Textbox(label="Status", value="Ready", interactive=False)
            
            with gr.Row():
                rag_answer = gr.Textbox(label="Answer", lines=6, interactive=False)
                rag_sources = gr.Textbox(label="Sources", lines=6, interactive=False)
            
            with gr.Row():
                gr.Markdown("### Document Search")
                search_query = gr.Textbox(label="Search Query", placeholder="Search documents...")
                search_k = gr.Slider(1, 10, value=5, label="Number of Results")
                search_btn = gr.Button("🔎 Search")
                search_results = gr.Textbox(label="Results", lines=8, interactive=False)
            
            # Event handlers
            index_btn.click(index_documents_ui, outputs="")
            rag_submit.click(
                rag_answer_ui,
                inputs=[rag_question, use_multi],
                outputs=[rag_answer, rag_sources]
            )
            search_btn.click(
                rag_search_ui,
                inputs=[search_query, search_k],
                outputs=search_results
            )
        
        # ====================================================================
        # Summarization Tab
        # ====================================================================
        with gr.Tab("✨ Document Summarization"):
            gr.Markdown("### Generate concise summaries with quality evaluation")
            
            with gr.Row():
                with gr.Column():
                    sum_text = gr.Textbox(
                        label="Text to Summarize",
                        placeholder="Paste text here...",
                        lines=8
                    )
                    sum_length = gr.Radio(
                        ["short", "medium", "long"],
                        value="medium",
                        label="Summary Length"
                    )
                    sum_btn = gr.Button("📝 Summarize", variant="primary")
                
                with gr.Column():
                    sum_result = gr.Textbox(
                        label="Summary Result",
                        lines=15,
                        interactive=False
                    )
            
            sum_btn.click(summarize_text_ui, inputs=[sum_text, sum_length], outputs=sum_result)
        
        # ====================================================================
        # Agent Tab
        # ====================================================================
        with gr.Tab("🤖 AI Agents"):
            gr.Markdown("### Use intelligent agents to process complex tasks")
            
            with gr.Tab("Orchestrator"):
                gr.Markdown("#### Process goals with the orchestrator agent")
                
                with gr.Row():
                    with gr.Column():
                        agent_goal = gr.Textbox(
                            label="Goal",
                            placeholder="What would you like the agent to do?",
                            lines=3
                        )
                        agent_context = gr.Textbox(
                            label="Context (optional)",
                            placeholder="Additional context...",
                            lines=2
                        )
                        agent_submit = gr.Button("🚀 Process Goal", variant="primary")
                    
                    with gr.Column():
                        agent_result = gr.Textbox(label="Result", lines=6, interactive=False)
                        agent_actions = gr.Textbox(label="Actions", lines=6, interactive=False)
                
                agent_submit.click(
                    agent_process_ui,
                    inputs=[agent_goal, agent_context],
                    outputs=[agent_result, agent_actions]
                )
            
            with gr.Tab("Agent Chat"):
                gr.Markdown("#### Chat with the agent")
                
                chatbot = gr.Chatbot(label="Agent Chat")
                user_msg = gr.Textbox(label="Message", placeholder="Type your message...")
                send_btn = gr.Button("Send")
                
                send_btn.click(agent_chat_ui, inputs=[user_msg, chatbot], outputs=chatbot)
        
        # ====================================================================
        # Session Tab
        # ====================================================================
        with gr.Tab("💾 Sessions"):
            gr.Markdown("### Manage conversation sessions and memory")
            
            with gr.Row():
                with gr.Column():
                    session_title = gr.Textbox(label="Session Title", placeholder="New session...")
                    create_session_btn = gr.Button("+ Create Session")
                    session_msg = gr.Textbox(interactive=False)
                
                with gr.Column():
                    sessions_df = gr.Dataframe(label="All Sessions", interactive=False)
                    refresh_btn = gr.Button("🔄 Refresh")
                    stats_txt = gr.Textbox(label="Statistics", interactive=False)
            
            create_session_btn.click(create_session_ui, inputs=session_title, outputs=session_msg)
            refresh_btn.click(get_sessions_list, outputs=sessions_df)
            refresh_btn.click(get_session_stats, outputs=stats_txt)
        
        # ====================================================================
        # Info Tab
        # ====================================================================
        with gr.Tab("ℹ️ About"):
            gr.Markdown("""
## DocuFind - AI Document Assistant

### Features
- **RAG (Retrieval-Augmented Generation)**: Answer questions about your documents with source citations
- **Summarization**: Generate summaries with quality evaluation and key points
- **AI Agents**: Use intelligent agents to process complex tasks
- **Session Management**: Keep track of conversations and context
- **Semantic Search**: Find relevant documents using AI understanding

### Technology Stack
- **LangChain**: Document processing and embeddings
- **FAISS**: Vector similarity search
- **Claude AI**: Intelligence and reasoning
- **Gradio**: Web interface
- **FastMCP**: Server integration

### Getting Started
1. Upload your documents
2. Index them for RAG using the "📚 RAG" tab
3. Ask questions or request summaries
4. Use agents for complex tasks

### Tips
- Use multi-query expansion for better RAG results
- Adjust summary length based on your needs
- Create sessions to keep track of conversations
- Check the orchestrator agent for complex multi-step tasks

### Support
For issues or questions, refer to the documentation in the project root.
            """)
    
    return demo

# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    print("🚀 Starting DocuFind UI...\n")
    
    # Initialize components
    print("⚙️  Initializing components...")
    if not init_components():
        print("⚠️  Some components failed to initialize")
        print("   You can still use non-AI features")
    
    # Build and launch interface
    print("🎨 Building Gradio interface...")
    demo = build_interface()
    
    print("\n" + "="*70)
    print("✅ DocuFind UI is running!")
    print("📍 Open http://localhost:7860 in your browser")
    print("="*70 + "\n")
    
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        show_error=True
    )
