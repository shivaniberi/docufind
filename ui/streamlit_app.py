"""
DocuFind  Streamlit UI  (ui/streamlit_app.py)

Run:
    cd docufind
    streamlit run ui/streamlit_app.py

Environment variables needed (.env):
    GOOGLE_API_KEY=...      (for Gemini LLM + embeddings)
    # or
    OPENAI_API_KEY=...      (set LLM_BACKEND=openai in .env)
"""

import os
import sys
import logging
import time
import html
from pathlib import Path
from typing import Optional

import streamlit as st

#  path setup 
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

env_path = ROOT / ".env"
if env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(env_path)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#  page config (must be first Streamlit call) 
st.set_page_config(
    page_title="DocuFind",
    layout="wide",
    initial_sidebar_state="expanded",
)

#  custom CSS 
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
}

::view-transition-group(*),
::view-transition-old(*),
::view-transition-new(*) {
    animation-duration: 0.25s;
    animation-timing-function: cubic-bezier(0.19, 1, 0.22, 1);
}

/* Page background */
.stApp { background: #0d0f12; color: #e2e8f0; }

/* Top chrome strip */
header[data-testid="stHeader"] {
    background: #111318 !important;
    border-bottom: 1px solid #1e2330 !important;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #111318 !important;
    border-right: 1px solid #1e2330;
}

/* Cards */
.doc-card {
    background: #161b24;
    border: 1px solid #1e2330;
    border-radius: 8px;
    padding: 16px 20px;
    margin-bottom: 10px;
}
.doc-card:hover { border-color: #3b82f6; transition: border-color 0.2s; }

/* Trace steps */
.trace-step {
    background: #0d1117;
    border-left: 3px solid #3b82f6;
    border-radius: 0 6px 6px 0;
    padding: 8px 14px;
    margin-bottom: 6px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 12px;
    color: #7dd3fc;
}
.trace-step.reflection { border-left-color: #f59e0b; color: #fcd34d; }
.trace-step.classify   { border-left-color: #a78bfa; color: #c4b5fd; }
.trace-step.retrieval  { border-left-color: #34d399; color: #6ee7b7; }
.trace-step.summary    { border-left-color: #f472b6; color: #f9a8d4; }

/* Answer box */
.answer-box {
    background: #0f1923;
    border: 1px solid #1e3a5f;
    border-radius: 10px;
    padding: 20px 24px;
    line-height: 1.75;
    font-size: 15px;
}

/* Badge */
.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 500;
    font-family: 'IBM Plex Mono', monospace;
}
.badge-simple    { background:#1a2a1a; color:#4ade80; border:1px solid #166534; }
.badge-complex   { background:#1a1a2e; color:#818cf8; border:1px solid #3730a3; }
.badge-super     { background:#2a1a10; color:#fb923c; border:1px solid #92400e; }
.badge-pass      { background:#1a2a1a; color:#4ade80; border:1px solid #166534; }
.badge-fail      { background:#2a1010; color:#f87171; border:1px solid #7f1d1d; }

/* Headings */
h1, h2, h3 { font-family: 'IBM Plex Sans', sans-serif; }

/* Input overrides */
.stTextArea textarea, .stTextInput input {
    background: #161b24 !important;
    border: 1px solid #1e2330 !important;
    color: #e2e8f0 !important;
    border-radius: 6px !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
}
.stTextArea textarea:focus, .stTextInput input:focus {
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 2px rgba(59,130,246,0.15) !important;
}

/* Button */
.stButton > button {
    background: #1d4ed8 !important;
    color: #fff !important;
    border: none !important;
    border-radius: 6px !important;
    font-weight: 500 !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
    transition: background 0.15s !important;
}
.stButton > button:hover { background: #2563eb !important; }

/* Chat messages */
.chat-user {
    background: #1e293b;
    border-radius: 10px 10px 3px 10px;
    padding: 12px 16px;
    margin: 8px 0;
    font-size: 14px;
    max-width: 80%;
    margin-left: auto;
    text-align: right;
}
.chat-ai {
    background: #0f1923;
    border: 1px solid #1e3a5f;
    border-radius: 3px 10px 10px 10px;
    padding: 12px 16px;
    margin: 8px 0;
    font-size: 14px;
    max-width: 90%;
}

.report h4 {
    margin: 10px 0 6px 0;
    font-size: 13px;
    color: #cbd5e1;
    letter-spacing: 0.2px;
}
.report p {
    margin: 0 0 10px 0;
    line-height: 1.6;
}
.report ul {
    margin: 0 0 10px 18px;
    padding: 0;
}
.report li {
    margin: 0 0 6px 0;
}
.report .citations {
    color: #93c5fd;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 12px;
}
</style>
""", unsafe_allow_html=True)


#  session state init 
def _init_state():
    defaults = {
        "indexed": False,
        "chat_history": [],   # LangChain messages
        "chat_display": [],   # (role, text) for UI
        "rag_pipeline": None,
        "bm25": None,
        "use_adk": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()


def _render_report_html(text: str) -> str:
    """
    Convert LLM answer text into a clean report-style HTML block.
    Keeps behavior unchanged while improving readability.
    """
    lines = [ln.rstrip() for ln in (text or "").splitlines()]
    out = []
    in_list = False

    def close_list():
        nonlocal in_list
        if in_list:
            out.append("</ul>")
            in_list = False

    for raw in lines:
        line = raw.strip()
        if not line:
            close_list()
            continue

        # Section-style headings, e.g. "Summary:", "Key Points:", "Citations Used:"
        if line.endswith(":") and len(line) < 60:
            close_list()
            out.append(f"<h4>{html.escape(line[:-1])}</h4>")
            continue

        # Bullet points
        if line.startswith("- "):
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{html.escape(line[2:])}</li>")
            continue

        close_list()
        cls = " class='citations'" if "chunk" in line.lower() and "[" in line else ""
        out.append(f"<p{cls}>{html.escape(line)}</p>")

    close_list()
    return "<div class='report'>" + "".join(out) + "</div>"


#  lazy component init 
@st.cache_resource(show_spinner=False)
def _get_pipeline():
    from rag.pipeline import RAGPipeline, RAGConfig
    cfg = RAGConfig(k=5)
    return RAGPipeline(config=cfg)

@st.cache_resource(show_spinner=False)
def _get_bm25():
    from rag.bm25_retriever import BM25Retriever
    return BM25Retriever()


#  sidebar 
with st.sidebar:
    sidebar_logo_path = ROOT / "assets" / "logo" / "docufind-logo.png"
    if sidebar_logo_path.exists():
        st.image(str(sidebar_logo_path), width=92)
    st.markdown(
        "<h2 style='color:#ffffff;font-weight:800;font-size:28px;margin:0 0 2px 0;'>DocuFind</h2>"
        "<p style='color:#94a3b8;font-size:13px;margin-top:0;'>"
        "Your document summarizer and insight assistant."
        "</p>",
        unsafe_allow_html=True,
    )
    st.divider()

    # Document upload
    st.markdown("#### Upload Documents")
    uploaded = st.file_uploader(
        "Drop PDFs or text files",
        type=["pdf", "txt", "md"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    if uploaded and st.button("Index Documents", use_container_width=True):
        docs_dir = ROOT / "documents"
        docs_dir.mkdir(exist_ok=True)

        with st.spinner("Saving files..."):
            for f in uploaded:
                (docs_dir / f.name).write_bytes(f.read())

        with st.spinner("Building BM25 + FAISS indexes..."):
            try:
                pipeline = _get_pipeline()
                stats = pipeline.index_documents(collection_name="docufind")

                # Build BM25 over same chunks
                bm25 = _get_bm25()
                from rag.loader import DocumentLoader
                loader = DocumentLoader()
                all_docs_dict = loader.load_all_documents()
                all_chunks = [c for chunks in all_docs_dict.values() for c in chunks]
                bm25.index(all_chunks)

                # Register with graph
                from agents.graph import set_retrievers
                set_retrievers(bm25, pipeline.vector_store)

                st.session_state["indexed"] = True
                st.session_state["bm25"] = bm25
                st.success(
                    f"Indexed {stats['documents_loaded']} doc(s), "
                    f"{stats['chunks_created']} chunks"
                )
            except Exception as e:
                st.error(f"Indexing failed: {e}")

    st.divider()

    st.markdown("#### Agent Runtime")
    from agents.adk_agent import ADKGraphAgent
    adk_available = ADKGraphAgent.is_available()
    use_adk = st.checkbox(
        "Use Google ADK LlmAgent",
        value=st.session_state.get("use_adk", False),
        disabled=not adk_available,
        help="Routes chat through agents/adk_agent.py (run_graph wrapped by ADK).",
    )
    st.session_state["use_adk"] = use_adk
    if not adk_available:
        st.caption("ADK not installed. Install requirements to enable this mode.")

    st.divider()

    if st.button("Clear Chat", use_container_width=True):
        st.session_state["chat_display"] = []
        st.session_state["chat_history"] = []
        st.rerun()


#  main layout 
st.markdown(
    "<div style='height:8px;'></div>",
    unsafe_allow_html=True,
)

# Centered chat layout
left_spacer, col_chat, right_spacer = st.columns([1.3, 3.4, 1.3], gap="large")


#  CHAT COLUMN 
with col_chat:
    st.markdown(
        "<h3 style='text-align:center;color:#e2e8f0;margin:0 0 10px 0;'>Chat</h3>",
        unsafe_allow_html=True,
    )

    # Render conversation
    chat_container = st.container(height=420)
    with chat_container:
        for role, text in st.session_state["chat_display"]:
            if role == "user":
                st.markdown(f'<div class="chat-user">{text}</div>', unsafe_allow_html=True)
            else:
                formatted = _render_report_html(text)
                st.markdown(f'<div class="chat-ai">{formatted}</div>', unsafe_allow_html=True)

    # Input row
    with st.form("chat_form", clear_on_submit=True):
        c1, c2 = st.columns([5, 1])
        with c1:
            user_input = st.text_input(
                "Message",
                placeholder="Ask a question or request a summary...",
                label_visibility="collapsed",
            )
        with c2:
            submitted = st.form_submit_button("Send", use_container_width=True)

    if submitted and user_input.strip():
        if not st.session_state["indexed"]:
            st.warning("Please upload and index documents first (sidebar).")
        else:
            query = user_input.strip()
            st.session_state["chat_display"].append(("user", query))

            with st.spinner("Processing request..."):
                try:
                    if st.session_state.get("use_adk"):
                        from agents.adk_agent import run_with_adk
                        result = run_with_adk(
                            query=query,
                            chat_history=st.session_state["chat_history"],
                        )
                    else:
                        from agents.graph import run_graph
                        result = run_graph(
                            query=query,
                            chat_history=st.session_state["chat_history"],
                        )

                    answer = result["final_answer"]

                    # Update LangChain memory list
                    from langchain_core.messages import HumanMessage, AIMessage
                    st.session_state["chat_history"].append(HumanMessage(content=query))
                    st.session_state["chat_history"].append(AIMessage(content=answer))

                    st.session_state["chat_display"].append(("ai", answer))

                except Exception as e:
                    err = f"Error: {e}"
                    st.session_state["chat_display"].append(("ai", err))
                    logger.exception(e)

            st.rerun()


#  bottom tabs: RAG search + MCP status 
st.divider()
tab_search, tab_mcp, tab_about = st.tabs(["RAG Search", "MCP Server", "About"])

with tab_search:
    st.markdown("Direct hybrid search  bypasses the agent, returns raw chunks.")
    sc1, sc2 = st.columns([4, 1])
    with sc1:
        search_q = st.text_input("Search query", placeholder="Enter keywords or a sentence...", label_visibility="collapsed")
    with sc2:
        do_search = st.button("Search", use_container_width=True)

    if do_search and search_q:
        if not st.session_state["indexed"]:
            st.warning("Index documents first.")
        else:
            with st.spinner("Searching..."):
                try:
                    pipeline = _get_pipeline()
                    faiss_results = pipeline.search(search_q, collection_name="docufind", k=5)
                    bm25 = st.session_state.get("bm25")
                    bm25_results = bm25.retrieve(search_q, k=5) if bm25 and bm25.is_indexed() else []

                    from rag.rrf import reciprocal_rank_fusion
                    from langchain_core.documents import Document

                    # Convert pipeline search results to (Document, score) for RRF
                    faiss_docs = [
                        (Document(page_content=r["content"], metadata={"source": r["file"]}), r["score"])
                        for r in faiss_results
                    ]
                    fused = reciprocal_rank_fusion(bm25_results, faiss_docs, top_n=6) if bm25_results else faiss_docs

                    st.markdown(f"**{len(fused)} results** (BM25 + FAISS  RRF fusion)")
                    for i, (doc, score) in enumerate(fused, 1):
                        src = doc.metadata.get("source", "unknown")
                        with st.expander(f"#{i}  {src}  (rrf={score:.4f})"):
                            st.text(doc.page_content[:600])
                except Exception as e:
                    st.error(f"Search error: {e}")

with tab_mcp:
    st.markdown("**MCP Server**  tools exposed via FastMCP (`mcp_server/document_server.py`)")
    st.code("""# Start the MCP server
cd docufind
python run_server.py          # default: http://127.0.0.1:8000

# Tools available:
#   list_documents()
#   read_document(file_name)
#   rag_answer_question(question, collection_name, use_multi_query)
#   rag_search(query, collection_name, k)
""", language="bash")
    st.markdown("The `MCPToolset` class in `agents/orchestrator.py` calls these tools from the agent graph.")

with tab_about:
    st.markdown("""
**DocuFind**  portfolio project demonstrating:

| Requirement | Implementation |
|---|---|
| Multi-agent (LangChain + LangGraph) | `agents/graph.py`  StateGraph with 4 nodes |
| ReAct pattern | `classify_node` reasons before routing |
| Reflection pattern | `reflection_node` critiques & rewrites answers |
| Google ADK | `agents/adk_agent.py` wraps `run_graph()` inside `LlmAgent` |
| MCP | `mcp_server/document_server.py` via FastMCP |
| RAG | `rag/pipeline.py`  FAISS semantic search |
| Hybrid RAG | `rag/bm25_retriever.py` + `rag/rrf.py` (BM25 + FAISS + RRF) |
| Memory | LangChain `ConversationSummaryMemory` in `agents/graph.py` |

**Stack:** LangChain  LangGraph  FastMCP  Streamlit  Gemini/OpenAI  FAISS  BM25
""")
