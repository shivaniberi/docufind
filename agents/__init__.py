"""
Agents Package - Phase 4

Contains agent implementations:
- summarizer_agent: Document summarization with reflection pattern
- orchestrator: Main agent with ReAct loop and tool integration
- adk_agent: Google ADK wrapper for LangGraph run_graph
- reflection_agent: Dedicated reflection critique/rewrite agent
"""

from agents.summarizer_agent import SummarizerAgent, SummaryResult, SummarizerConfig
from agents.orchestrator import OrchestratorAgent, MCPToolset, OrchestratorConfig
from agents.adk_agent import ADKGraphAgent, run_with_adk
from agents.reflection_agent import ReflectionAgent, ReflectionResult

__all__ = [
    "SummarizerAgent",
    "SummaryResult",
    "SummarizerConfig",
    "OrchestratorAgent",
    "MCPToolset",
    "OrchestratorConfig",
    "ADKGraphAgent",
    "run_with_adk",
    "ReflectionAgent",
    "ReflectionResult",
]
