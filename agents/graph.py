"""
LangGraph multi-agent graph.

Pipeline:
1. classify_node -> detect query complexity
2. retrieval_node -> BM25 + FAISS + RRF (for complex queries)
3. summary_node -> generate answer from retrieved context
4. reflection_node -> critique/rewrite when needed

Supports multiple LLM backends via environment variables.
"""

import logging
import os
from enum import Enum
from typing import TypedDict, List, Annotated, Optional
import operator
import re
import time

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_classic.memory import ConversationSummaryMemory
from langgraph.graph import StateGraph, END

logger = logging.getLogger(__name__)

# Backoff window when provider quota is exhausted.
_LLM_BACKOFF_UNTIL = 0.0
_LLM_BACKOFF_REASON = ""

# LLM Backend  swap here if you want OpenAI instead of Gemini

def _build_llm(temperature: float = 0.3):
    """
    Build the LangChain chat LLM.
    Reads env vars: LLM_BACKEND, GOOGLE_API_KEY, OPENAI_API_KEY, or COHERE_API_KEY.
    """
    backend = os.getenv("LLM_BACKEND", "gemini").lower()
    max_retries = int(os.getenv("LLM_MAX_RETRIES", "1"))
    timeout = float(os.getenv("LLM_TIMEOUT_SECONDS", "30"))
    if backend == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model="gpt-4o-mini",
            temperature=temperature,
            api_key=os.getenv("OPENAI_API_KEY"),
            max_retries=max_retries,
            timeout=timeout,
        )
    elif backend == "cohere":
        from langchain_cohere import ChatCohere
        return ChatCohere(
            model=os.getenv("COHERE_MODEL", "command-r-08-2024"),
            temperature=temperature,
            cohere_api_key=os.getenv("COHERE_API_KEY"),
            max_retries=max_retries,
            timeout=timeout,
        )
    else:
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=temperature,
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            max_retries=max_retries,
            timeout=timeout,
        )


def _is_quota_error(exc: Exception) -> bool:
    text = str(exc).upper()
    return (
        "RESOURCE_EXHAUSTED" in text
        or "QUOTA EXCEEDED" in text
        or "429" in text
        or "RATE_LIMIT" in text
    )


def _set_quota_backoff(exc: Exception) -> None:
    global _LLM_BACKOFF_UNTIL, _LLM_BACKOFF_REASON
    text = str(exc)
    wait_seconds = 60.0
    match = re.search(r"retry in\s+([0-9]+(?:\.[0-9]+)?)s", text, re.IGNORECASE)
    if match:
        wait_seconds = max(30.0, float(match.group(1)))
    _LLM_BACKOFF_UNTIL = time.time() + wait_seconds
    _LLM_BACKOFF_REASON = f"LLM quota exhausted; temporary fallback enabled ({int(wait_seconds)}s)."
    logger.warning(_LLM_BACKOFF_REASON)


def _llm_temporarily_blocked() -> bool:
    return time.time() < _LLM_BACKOFF_UNTIL


def _heuristic_classify(query: str) -> tuple["QueryComplexity", list[str], str]:
    q = query.lower()
    if any(k in q for k in ["compare", "difference", "analyze", "analyse", "why", "how"]):
        return QueryComplexity.COMPLEX, [query], "Heuristic classify (LLM unavailable)."
    if any(k in q for k in ["step by step", "cause", "consequence", "timeline"]):
        return QueryComplexity.SUPER_COMPLEX, [query], "Heuristic classify (LLM unavailable)."
    return QueryComplexity.SIMPLE, [query], "Heuristic classify (LLM unavailable)."


def _extractive_fallback_answer(query: str, context: str) -> str:
    if not context or not context.strip():
        return (
            "I couldn't call the language model due to quota limits and no context was available. "
            "Please retry later or switch to a key/project with available quota."
        )

    # Prefer first few chunk blocks if present; otherwise first 1200 chars.
    chunks = re.split(r"\n(?=\[Chunk\s+\d+)", context)
    picked = [c.strip() for c in chunks if c.strip()][:3]
    snippet = "\n\n".join(picked) if picked else context[:1200].strip()
    return (
        "Gemini quota is currently exhausted, so this is an extractive fallback from retrieved context.\n\n"
        f"Query: {query}\n\n"
        f"{snippet}\n\n"
        "Retry after quota reset, or use a billed/alternate model key for generated summaries."
    )


# Shared State  flows between every node in the graph

class QueryComplexity(str, Enum):
    SIMPLE = "simple"            # single-hop, answer is directly in docs
    COMPLEX = "complex"          # needs multi-query retrieval + synthesis
    SUPER_COMPLEX = "super_complex"  # multi-hop, several sub-questions


class AgentState(TypedDict):
    """
    The state object that flows through every node.

    Use Annotated[list, operator.add] for fields that nodes *append to*
    (LangGraph will merge them automatically).
    """
    # Input
    query: str
    documents_context: str          # raw text of uploaded / indexed docs

    # Routing
    complexity: QueryComplexity

    # Retrieval
    retrieved_chunks: str           # assembled context from retriever(s)
    retrieval_queries: List[str]    # sub-queries generated for complex cases

    # Generation
    draft_answer: str
    final_answer: str

    # Reflection
    reflection_critique: str
    reflection_passed: bool

    # Memory / trace
    chat_history: Annotated[List, operator.add]   # appended by each node
    agent_trace: Annotated[List[str], operator.add]  # human-readable log


# Helper: build memory object (shared, injected into nodes)

def build_memory(llm=None) -> ConversationSummaryMemory:
    """
    LangChain ConversationSummaryMemory.

    After N messages it automatically summarises older turns so the context
    window stays bounded  this is the 'good memory' from sougaaat's approach.
    """
    _llm = llm or _build_llm(temperature=0.0)
    return ConversationSummaryMemory(
        llm=_llm,
        memory_key="chat_history",
        return_messages=True,
        max_token_limit=1000       # summarise when history exceeds ~1000 tokens
    )


# Node 1  classify_node (ReAct: Reason before Acting)

def classify_node(state: AgentState) -> AgentState:
    """
    ReAct reasoning step.

    Looks at the query + any available document context and decides:
       simple         go straight to summary_node
       complex        generate retrieval sub-queries  retrieval_node
       super_complex  multi-hop sub-queries  retrieval_node

    This is what makes the graph 'agentic'  it doesn't blindly run every step;
    it reasons first about what is needed.
    """
    logger.info("[classify_node] Analysing query complexity...")

    if _llm_temporarily_blocked():
        complexity, sub_queries, reasoning = _heuristic_classify(state["query"])
        return {
            **state,
            "complexity": complexity,
            "retrieval_queries": sub_queries,
            "agent_trace": [
                f"[classify] {reasoning} "
                f"Complexity='{complexity.value}'. Sub-queries: {sub_queries}"
            ],
        }

    llm = _build_llm(temperature=0.0)

    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content="""You are a query complexity classifier for a document Q&A system.

Classify the user's query into exactly one of these three levels:

SIMPLE        The answer is a single fact or short explanation that can be
               found directly in one document passage. No synthesis needed.
               Examples: "What is the document about?", "Who wrote this?"

COMPLEX       The answer requires retrieving from multiple passages and
               synthesising them. The user wants analysis, comparison, or
               a summary of several ideas.
               Examples: "Summarise the main arguments", "Compare X and Y"

SUPER_COMPLEX  The answer requires multi-hop reasoning: finding A, then using
               A to find B, then combining both. Often involves causal chains
               or step-by-step derivations across many document sections.
               Examples: "How did X lead to Y and what were the consequences?"

Respond ONLY in this exact format (no extra text):
COMPLEXITY: <simple|complex|super_complex>
REASONING: <one sentence explaining why>
SUB_QUERIES: <comma-separated list of 1-3 retrieval queries, or NONE for simple>"""),
        HumanMessage(content=f"Query: {state['query']}")
    ])

    try:
        response = llm.invoke(prompt.format_messages())
        text = response.content.strip()
    except Exception as exc:
        if _is_quota_error(exc):
            _set_quota_backoff(exc)
            complexity, sub_queries, reasoning = _heuristic_classify(state["query"])
            return {
                **state,
                "complexity": complexity,
                "retrieval_queries": sub_queries,
                "agent_trace": [
                    f"[classify] {reasoning} "
                    f"Complexity='{complexity.value}'. Sub-queries: {sub_queries}",
                    f"[quota] {_LLM_BACKOFF_REASON}",
                ],
            }
        raise

    # Parse
    complexity = QueryComplexity.SIMPLE
    sub_queries = []
    reasoning = ""

    for line in text.splitlines():
        if line.startswith("COMPLEXITY:"):
            val = line.split(":", 1)[1].strip().lower()
            if val in QueryComplexity._value2member_map_:
                complexity = QueryComplexity(val)
        elif line.startswith("REASONING:"):
            reasoning = line.split(":", 1)[1].strip()
        elif line.startswith("SUB_QUERIES:"):
            raw = line.split(":", 1)[1].strip()
            if raw.upper() != "NONE":
                sub_queries = [q.strip() for q in raw.split(",") if q.strip()]

    logger.info(f"   Complexity: {complexity.value} | Reason: {reasoning}")

    return {
        **state,
        "complexity": complexity,
        "retrieval_queries": sub_queries or [state["query"]],
        "agent_trace": [
            f"[classify] Query classified as '{complexity.value}'. "
            f"Reason: {reasoning}. "
            f"Sub-queries: {sub_queries or ['(none)']}"
        ],
    }


# Node 2  retrieval_node

def retrieval_node(state: AgentState) -> AgentState:
    """
    Hybrid retrieval: BM25 + FAISS fused with RRF.

    For COMPLEX queries uses multi-query retrieval (one retrieval pass per
    sub-query, then RRF merges them).
    For SUPER_COMPLEX queries does the same but the sub-queries are ordered
    as a chain: context from query N feeds query N+1 (multi-hop).

    Falls back gracefully if the vector store is not initialised  uses the
    raw documents_context string passed in the state.
    """
    logger.info(f"[retrieval_node] Running {'multi-hop' if state['complexity'] == QueryComplexity.SUPER_COMPLEX else 'multi-query'} retrieval...")

    # --- Try hybrid retrieval if the pipeline is available ---
    try:
        from rag.bm25_retriever import BM25Retriever
        from rag.rrf import reciprocal_rank_fusion
        from rag.embedder import VectorStore

        # These are module-level singletons set by the UI / pipeline
        bm25: Optional[BM25Retriever] = _GLOBAL_BM25
        vs: Optional[VectorStore] = _GLOBAL_VECTOR_STORE

        if bm25 and bm25.is_indexed() and vs:
            all_bm25, all_faiss = [], []

            queries = state["retrieval_queries"]
            hop_context = ""   # for super_complex: accumulate context between hops

            for i, q in enumerate(queries):
                if state["complexity"] == QueryComplexity.SUPER_COMPLEX and hop_context:
                    q = f"{q}\n\nContext so far: {hop_context[:400]}"

                bm25_results = bm25.retrieve(q, k=6)
                faiss_results = vs.similarity_search(q, k=6)
                fused = reciprocal_rank_fusion(bm25_results, faiss_results, top_n=5)

                all_bm25.extend(bm25_results)
                all_faiss.extend(faiss_results)

                # Accumulate hop context
                hop_context += "\n".join(doc.page_content[:200] for doc, _ in fused[:3])

            # Final global fusion of everything collected
            final_fused = reciprocal_rank_fusion(all_bm25, all_faiss, top_n=8)
            retrieved_text = _assemble_context(final_fused)

            logger.info(f"   Hybrid retrieval: {len(final_fused)} chunks after RRF fusion")

            return {
                **state,
                "retrieved_chunks": retrieved_text,
                "agent_trace": [
                    f"[retrieval] Hybrid BM25+FAISS with RRF. "
                    f"Queries: {queries}. "
                    f"Chunks after fusion: {len(final_fused)}"
                ],
            }

    except Exception as exc:
        logger.warning(f"   Hybrid retrieval failed ({exc}), falling back to documents_context")

    # --- Fallback: use raw context already in state ---
    return {
        **state,
        "retrieved_chunks": state.get("documents_context", "No document context available."),
        "agent_trace": ["[retrieval] Used raw documents_context (hybrid retrieval not available)"],
    }


def _assemble_context(fused_results, max_chars: int = 4000) -> str:
    """Turn a list of (Document, score) into a context string for the LLM."""
    parts = []
    total = 0
    for i, (doc, score) in enumerate(fused_results, 1):
        source = doc.metadata.get("source", "doc")
        chunk = doc.page_content.strip()
        entry = f"[Chunk {i} | {source} | rrf={score:.4f}]\n{chunk}\n"
        if total + len(entry) > max_chars:
            break
        parts.append(entry)
        total += len(entry)
    return "\n".join(parts)


# Node 3  summary_node

def summary_node(state: AgentState) -> AgentState:
    """
    Generates the answer / summary from the retrieved context.

    Uses:
    - The retrieved_chunks (from retrieval_node) OR documents_context
      (for simple queries that skip retrieval)
    - ConversationSummaryMemory (via chat_history in state) so multi-turn
      conversations stay coherent
    """
    logger.info("[summary_node] Generating answer...")

    context = state.get("retrieved_chunks") or state.get("documents_context", "")
    if _llm_temporarily_blocked():
        fallback = _extractive_fallback_answer(state["query"], context)
        return {
            **state,
            "draft_answer": fallback,
            "agent_trace": [
                "[summary] LLM temporarily unavailable. Returned extractive fallback answer.",
                f"[quota] {_LLM_BACKOFF_REASON}",
            ],
        }

    llm = _build_llm(temperature=0.5)

    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content="""You are a precise document assistant.
Answer the user's query using ONLY the provided document context.
- Be concise but complete.
- Cite which chunk(s) you drew from using the [Chunk N] labels.
- If the context does not contain enough information, say so clearly.
- For summarisation tasks, use this exact structure:
  1) Summary: 2-4 clear sentences
  2) Key Points: 3-6 short bullet points
  3) Citations Used: list chunk labels like [Chunk 2], [Chunk 5]
- Avoid repeating the same point in different wording.
- Keep language simple and professional."""),
        MessagesPlaceholder(variable_name="chat_history"),
        HumanMessage(content=f"""DOCUMENT CONTEXT:
{context}

QUERY: {state['query']}

Provide your answer:""")
    ])

    messages = prompt.format_messages(
        chat_history=state.get("chat_history", [])
    )
    try:
        response = llm.invoke(messages)
        draft = response.content.strip()
    except Exception as exc:
        if _is_quota_error(exc):
            _set_quota_backoff(exc)
            draft = _extractive_fallback_answer(state["query"], context)
            return {
                **state,
                "draft_answer": draft,
                "agent_trace": [
                    "[summary] Quota exceeded. Returned extractive fallback answer.",
                    f"[quota] {_LLM_BACKOFF_REASON}",
                ],
            }
        raise

    logger.info(f"   Draft answer: {draft[:80]}...")

    return {
        **state,
        "draft_answer": draft,
        "agent_trace": [f"[summary] Draft answer generated ({len(draft)} chars)"],
    }


# Node 4  reflection_node

def reflection_node(state: AgentState) -> AgentState:
    """
    Reflection agentic pattern.

    Critiques the draft answer on three dimensions:
      1. Groundedness  is every claim supported by the retrieved context?
      2. Completeness  does it address all parts of the query?
      3. Clarity       is it well-structured and easy to read?

    If quality is PASS, sets final_answer = draft_answer.
    If quality is FAIL, rewrites the answer and sets reflection_passed = False
    so the trace shows what changed.
    """
    logger.info("[reflection_node] Critiquing draft answer...")

    from agents.reflection_agent import ReflectionAgent

    if _llm_temporarily_blocked():
        return {
            **state,
            "reflection_critique": "Skipped reflection due to temporary LLM quota backoff.",
            "reflection_passed": True,
            "final_answer": state["draft_answer"],
            "agent_trace": [
                "[reflection] Skipped due to temporary LLM quota backoff."
            ],
        }

    try:
        reflection = ReflectionAgent().critique(
            query=state["query"],
            draft_answer=state["draft_answer"],
            document_context=state.get("retrieved_chunks", state.get("documents_context", "")),
        )
    except Exception as exc:
        if _is_quota_error(exc):
            _set_quota_backoff(exc)
            return {
                **state,
                "reflection_critique": "Skipped reflection due to quota exhaustion.",
                "reflection_passed": True,
                "final_answer": state["draft_answer"],
                "agent_trace": [
                    "[reflection] Quota exceeded. Returned draft answer without critique.",
                    f"[quota] {_LLM_BACKOFF_REASON}",
                ],
            }
        raise

    verdict = reflection.verdict
    issues = reflection.issues
    passed = reflection.passed
    final = state["draft_answer"] if passed else reflection.improved_answer

    logger.info(f"   Reflection verdict: {verdict} | Issues: {issues[:80]}")

    return {
        **state,
        "reflection_critique": issues,
        "reflection_passed": passed,
        "final_answer": final,
        "agent_trace": [
            f"[reflection] Verdict: {verdict}. "
            f"Issues: {issues[:120]}. "
            f"Answer {'unchanged' if passed else 'rewritten'}."
        ],
    }


# Terminal node  packages the final answer for simple queries

def finalise_node(state: AgentState) -> AgentState:
    """Promote draft  final for paths that skip reflection."""
    return {
        **state,
        "final_answer": state.get("final_answer") or state.get("draft_answer", ""),
        "agent_trace": ["[finalise] Answer ready (no reflection needed for simple query)"],
    }


# Routing logic (conditional edges)

def route_after_classify(state: AgentState) -> str:
    """
    Called by LangGraph after classify_node.
    Returns the name of the next node.
    """
    c = state.get("complexity", QueryComplexity.SIMPLE)
    if c == QueryComplexity.SIMPLE:
        return "summary_node"
    else:
        return "retrieval_node"   # both COMPLEX and SUPER_COMPLEX go here


def route_after_summary(state: AgentState) -> str:
    """
    After summary_node, reflect only for complex/super_complex queries.
    Simple queries go straight to finalise.
    """
    c = state.get("complexity", QueryComplexity.SIMPLE)
    if c == QueryComplexity.SIMPLE:
        return "finalise_node"
    else:
        return "reflection_node"


# Build the graph

def build_graph() -> StateGraph:
    """
    Assemble and compile the LangGraph StateGraph.

    Returns a compiled graph you can call with:
        result = graph.invoke(initial_state)
    """
    graph = StateGraph(AgentState)

    # Register nodes
    graph.add_node("classify_node", classify_node)
    graph.add_node("retrieval_node", retrieval_node)
    graph.add_node("summary_node", summary_node)
    graph.add_node("reflection_node", reflection_node)
    graph.add_node("finalise_node", finalise_node)

    # Entry point
    graph.set_entry_point("classify_node")

    # Conditional edge after classify
    graph.add_conditional_edges(
        "classify_node",
        route_after_classify,
        {
            "summary_node": "summary_node",
            "retrieval_node": "retrieval_node",
        }
    )

    # retrieval always feeds into summary
    graph.add_edge("retrieval_node", "summary_node")

    # Conditional edge after summary
    graph.add_conditional_edges(
        "summary_node",
        route_after_summary,
        {
            "reflection_node": "reflection_node",
            "finalise_node": "finalise_node",
        }
    )

    # Both terminal nodes end the graph
    graph.add_edge("reflection_node", END)
    graph.add_edge("finalise_node", END)

    compiled = graph.compile()
    logger.info("LangGraph multi-agent graph compiled successfully")
    return compiled


# Module-level singletons (set by pipeline / UI before first run)
_GLOBAL_BM25 = None          # BM25Retriever instance
_GLOBAL_VECTOR_STORE = None  # VectorStore instance


def set_retrievers(bm25_retriever, vector_store) -> None:
    """
    Call this once after indexing documents so the graph nodes can use
    the live retrieval indexes.

        from agents.graph import set_retrievers
        set_retrievers(bm25, vs)
    """
    global _GLOBAL_BM25, _GLOBAL_VECTOR_STORE
    _GLOBAL_BM25 = bm25_retriever
    _GLOBAL_VECTOR_STORE = vector_store
    logger.info("Graph retrievers registered (BM25 + VectorStore)")


# Convenience runner

def run_graph(
    query: str,
    documents_context: str = "",
    chat_history: Optional[List] = None
) -> dict:
    """
    High-level entry point.

    Args:
        query:             User's question or summarisation request.
        documents_context: Raw document text (fallback if retrievers not set).
        chat_history:      Previous LangChain messages for memory continuity.

    Returns:
        dict with keys: final_answer, complexity, agent_trace, reflection_passed
    """
    graph = build_graph()

    initial_state: AgentState = {
        "query": query,
        "documents_context": documents_context,
        "complexity": QueryComplexity.SIMPLE,
        "retrieved_chunks": "",
        "retrieval_queries": [query],
        "draft_answer": "",
        "final_answer": "",
        "reflection_critique": "",
        "reflection_passed": True,
        "chat_history": chat_history or [],
        "agent_trace": [],
    }

    try:
        result = graph.invoke(initial_state)
    except Exception as exc:
        if _is_quota_error(exc):
            _set_quota_backoff(exc)
            fallback = _extractive_fallback_answer(query, documents_context)
            return {
                "final_answer": fallback,
                "complexity": QueryComplexity.SIMPLE.value,
                "agent_trace": [f"[quota] {_LLM_BACKOFF_REASON}"],
                "reflection_passed": True,
                "reflection_critique": "Graph fallback due to LLM quota exhaustion.",
                "retrieved_chunks_preview": (documents_context or "")[:300],
            }
        raise

    return {
        "final_answer": result.get("final_answer", ""),
        "complexity": result.get("complexity", QueryComplexity.SIMPLE).value,
        "agent_trace": result.get("agent_trace", []),
        "reflection_passed": result.get("reflection_passed", True),
        "reflection_critique": result.get("reflection_critique", ""),
        "retrieved_chunks_preview": result.get("retrieved_chunks", "")[:300],
    }
