"""
Reflection agent for summary quality checks.

This module provides a dedicated Reflection agentic pattern component:
- Critiques a draft answer for groundedness, completeness, and clarity.
- Returns PASS when no rewrite is needed, otherwise returns an improved answer.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate


@dataclass
class ReflectionResult:
    verdict: str
    issues: str
    improved_answer: str

    @property
    def passed(self) -> bool:
        return self.verdict.upper() == "PASS"


class ReflectionAgent:
    """Dedicated reflection agent that critiques and optionally rewrites."""

    def __init__(self, backend: str | None = None):
        self.backend = (backend or os.getenv("LLM_BACKEND", "gemini")).lower()

    def _build_llm(self, temperature: float = 0.2):
        if self.backend == "openai":
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model="gpt-4o-mini",
                temperature=temperature,
                api_key=os.getenv("OPENAI_API_KEY"),
            )
        if self.backend == "cohere":
            from langchain_cohere import ChatCohere
            return ChatCohere(
                model=os.getenv("COHERE_MODEL", "command-r-08-2024"),
                temperature=temperature,
                cohere_api_key=os.getenv("COHERE_API_KEY"),
            )
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=temperature,
            google_api_key=os.getenv("GOOGLE_API_KEY"),
        )

    def critique(
        self,
        query: str,
        draft_answer: str,
        document_context: str,
    ) -> ReflectionResult:
        llm = self._build_llm(temperature=0.2)

        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are a strict quality reviewer for AI-generated document summaries.

Evaluate the DRAFT ANSWER against the DOCUMENT CONTEXT on:
1. Groundedness: every claim must be supported by context.
2. Completeness: all parts of the query should be addressed.
3. Clarity: structure and readability.

Respond in this EXACT format:
VERDICT: <PASS|FAIL>
ISSUES: <brief issues text, or "None">
IMPROVED_ANSWER: <rewritten answer if FAIL, or "PASS">"""),
            HumanMessage(content=f"""DOCUMENT CONTEXT (excerpt):
{document_context[:2000]}

ORIGINAL QUERY: {query}

DRAFT ANSWER:
{draft_answer}"""),
        ])

        response = llm.invoke(prompt.format_messages())
        text = response.content.strip()

        verdict = "PASS"
        issues = "None"
        improved = "PASS"

        for line in text.splitlines():
            if line.startswith("VERDICT:"):
                verdict = line.split(":", 1)[1].strip().upper()
            elif line.startswith("ISSUES:"):
                issues = line.split(":", 1)[1].strip()
            elif line.startswith("IMPROVED_ANSWER:"):
                improved = line.split(":", 1)[1].strip()

        if "IMPROVED_ANSWER:" in text:
            improved = text.split("IMPROVED_ANSWER:", 1)[1].strip()

        if verdict == "PASS" or improved.upper() == "PASS":
            improved = draft_answer

        return ReflectionResult(
            verdict=verdict,
            issues=issues,
            improved_answer=improved,
        )
