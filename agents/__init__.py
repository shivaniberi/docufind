"""
Agents Package - Phase 4

Contains agent implementations:
- summarizer_agent: Document summarization with reflection pattern
- orchestrator: Main agent with ReAct loop and tool integration
"""

from agents.summarizer_agent import SummarizerAgent, SummaryResult, SummarizerConfig
from agents.orchestrator import OrchestratorAgent, MCPToolset, OrchestratorConfig

__all__ = [
    "SummarizerAgent",
    "SummaryResult",
    "SummarizerConfig",
    "OrchestratorAgent",
    "MCPToolset",
    "OrchestratorConfig"
]
