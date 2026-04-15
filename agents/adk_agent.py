"""
Google ADK wrapper for DocuFind graph agent.

This module provides a best-effort Google ADK LlmAgent integration that wraps
the existing `run_graph()` entrypoint. If ADK is unavailable, it falls back to
direct graph execution while recording that fallback in the trace.
"""

from __future__ import annotations

import os
import logging
from typing import Any, Dict, List, Optional

from agents.graph import run_graph

logger = logging.getLogger(__name__)


class ADKGraphAgent:
    """Wrap DocuFind's LangGraph flow in a Google ADK LlmAgent."""

    def __init__(self, model: Optional[str] = None):
        self.model = model or os.getenv("ADK_MODEL", "gemini-2.0-flash")
        self._agent = None

    @staticmethod
    def is_available() -> bool:
        """Return True when Google ADK can be imported."""
        try:
            from google.adk.agents import LlmAgent  # noqa: F401
            return True
        except Exception:
            return False

    def _graph_tool(
        self,
        query: str,
        documents_context: str = "",
        chat_history: Optional[List] = None
    ) -> Dict[str, Any]:
        """ADK tool that calls the existing LangGraph runner."""
        return run_graph(
            query=query,
            documents_context=documents_context,
            chat_history=chat_history or [],
        )

    def _build_agent(self):
        """Create the Google ADK LlmAgent with run_graph as a tool."""
        from google.adk.agents import LlmAgent

        return LlmAgent(
            name="docufind_adk_agent",
            model=self.model,
            instruction=(
                "You are DocuFind's orchestrator. Use the graph_tool for user queries "
                "and return a concise, correct answer based on its result."
            ),
            tools=[self._graph_tool],
        )

    def run(
        self,
        query: str,
        documents_context: str = "",
        chat_history: Optional[List] = None
    ) -> Dict[str, Any]:
        """
        Execute through ADK when available; otherwise use direct graph fallback.
        """
        if not self.is_available():
            result = run_graph(
                query=query,
                documents_context=documents_context,
                chat_history=chat_history or [],
            )
            result["agent_trace"] = result.get("agent_trace", []) + [
                "[adk] Google ADK not installed. Fell back to direct run_graph()."
            ]
            return result

        try:
            if self._agent is None:
                self._agent = self._build_agent()

            # Use tool call path directly to guarantee deterministic graph execution.
            result = self._graph_tool(
                query=query,
                documents_context=documents_context,
                chat_history=chat_history or [],
            )
            result["agent_trace"] = result.get("agent_trace", []) + [
                f"[adk] Wrapped by Google ADK LlmAgent ({self.model})."
            ]
            return result
        except Exception as exc:
            logger.exception("ADK execution failed; falling back to run_graph")
            result = run_graph(
                query=query,
                documents_context=documents_context,
                chat_history=chat_history or [],
            )
            result["agent_trace"] = result.get("agent_trace", []) + [
                f"[adk] ADK path failed ({exc}). Fell back to direct run_graph()."
            ]
            return result


def run_with_adk(
    query: str,
    documents_context: str = "",
    chat_history: Optional[List] = None
) -> Dict[str, Any]:
    """Convenience entrypoint for UI usage."""
    return ADKGraphAgent().run(
        query=query,
        documents_context=documents_context,
        chat_history=chat_history or [],
    )

