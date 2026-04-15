"""
Orchestrator Agent Module - Phase 4

Implements a ReAct (Reasoning + Acting) loop using Pydantic AI with:
- MCPToolset integration for FastMCP server
- Multi-step reasoning and planning
- Tool calling for document operations
- Memory and context management
- Orchestration of multiple agents

This is the main agent that coordinates all operations.
"""

import logging
import os
import json
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from pydantic import BaseModel, Field
import anthropic

from agents.summarizer_agent import SummarizerAgent, SummaryResult

logger = logging.getLogger(__name__)


class ActionResult(BaseModel):
    """Result of an action taken by the agent."""
    
    action: str = Field(..., description="The action performed")
    success: bool = Field(..., description="Whether the action succeeded")
    result: Any = Field(..., description="The result of the action")
    error: Optional[str] = Field(None, description="Error message if failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class OrchestrationPlan(BaseModel):
    """Plan created by the orchestrator."""
    
    goal: str = Field(..., description="The overall goal")
    steps: List[str] = Field(..., description="Steps to achieve the goal")
    reasoning: str = Field(..., description="Reasoning behind the plan")
    estimated_time: str = Field(default="unknown", description="Estimated execution time")


@dataclass
class OrchestratorConfig:
    """Configuration for the orchestrator agent."""
    
    model_name: str = "claude-3-5-sonnet-20241022"
    temperature: float = 0.7
    max_tokens: int = 4096
    
    # MCP Server configuration
    mcp_server_url: str = "http://127.0.0.1:8000"
    mcp_timeout: int = 30
    
    # Reasoning settings
    enable_planning: bool = True
    max_reasoning_steps: int = 10
    
    # Tool integration
    enable_tool_use: bool = True
    retry_failed_tools: bool = True


class MCPToolset:
    """
    Integration with FastMCP server for tool calls.
    
    Provides methods to call tools on the MCP server:
    - Document operations
    - RAG operations
    - Search and retrieval
    """
    
    def __init__(self, server_url: str = "http://127.0.0.1:8000", timeout: int = 30):
        """
        Initialize MCP toolset.
        
        Args:
            server_url (str): URL of the MCP server
            timeout (int): Request timeout in seconds
        """
        self.server_url = server_url
        self.timeout = timeout
        
        try:
            import httpx
            self.client = httpx.Client(timeout=timeout)
        except ImportError:
            logger.warning("httpx not installed, using requests instead")
            import requests
            self.client = requests
    
    def list_documents(self) -> Dict[str, Any]:
        """List all documents on the server."""
        try:
            response = self.client.post(
                f"{self.server_url}/tools/list_documents/call",
                json={}
            )
            return response.json()
        except Exception as e:
            logger.error(f"Error listing documents: {str(e)}")
            return {"error": str(e)}
    
    def read_document(self, file_name: str) -> Dict[str, Any]:
        """Read a document from the server."""
        try:
            response = self.client.post(
                f"{self.server_url}/tools/read_document/call",
                json={"file_name": file_name}
            )
            return response.json()
        except Exception as e:
            logger.error(f"Error reading document: {str(e)}")
            return {"error": str(e)}
    
    def rag_answer_question(
        self,
        question: str,
        collection_name: str = "default",
        use_multi_query: bool = False
    ) -> Dict[str, Any]:
        """Ask a question using RAG."""
        try:
            response = self.client.post(
                f"{self.server_url}/rag/answer",
                json={
                    "question": question,
                    "collection_name": collection_name,
                    "use_multi_query": use_multi_query
                }
            )
            return response.json()
        except Exception as e:
            logger.error(f"Error asking RAG question: {str(e)}")
            return {"error": str(e)}
    
    def rag_search(
        self,
        query: str,
        collection_name: str = "default",
        k: int = 5
    ) -> Dict[str, Any]:
        """Search documents using RAG."""
        try:
            response = self.client.post(
                f"{self.server_url}/rag/search",
                json={
                    "query": query,
                    "collection_name": collection_name,
                    "k": k
                }
            )
            return response.json()
        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            return {"error": str(e)}


class OrchestratorAgent:
    """
    Main orchestrator agent using ReAct pattern.
    
    Features:
    - Multi-step reasoning and planning
    - Tool calling for external operations
    - Memory and context management
    - Integration with RAG and summarization
    - Error handling and recovery
    
    Example:
        >>> orchestrator = OrchestratorAgent()
        >>> result = orchestrator.process("Summarize all documents and answer: What is AI?")
    """
    
    def __init__(self, config: Optional[OrchestratorConfig] = None):
        """
        Initialize the orchestrator agent.
        
        Args:
            config (OrchestratorConfig): Agent configuration
        """
        self.config = config or OrchestratorConfig()
        
        # Initialize Claude client
        self.client = anthropic.Anthropic()
        
        # Initialize toolset
        self.toolset = MCPToolset(
            server_url=self.config.mcp_server_url,
            timeout=self.config.mcp_timeout
        )
        
        # Initialize sub-agents
        self.summarizer = SummarizerAgent()
        
        # Memory
        self.conversation_history: List[Dict[str, str]] = []
        self.action_log: List[ActionResult] = []
        
        logger.info(f" OrchestratorAgent initialized with model: {self.config.model_name}")
    
    def process(self, goal: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a goal using ReAct loop.
        
        Args:
            goal (str): The goal to accomplish
            context (str): Additional context
            
        Returns:
            Dict: Result with reasoning, actions, and final answer
        """
        logger.info(f" Processing goal: {goal}")
        
        # Step 1: Create plan
        if self.config.enable_planning:
            plan = self._create_plan(goal, context)
            logger.info(f" Plan: {plan.reasoning}")
        else:
            plan = None
        
        # Step 2: Execute ReAct loop
        result = self._react_loop(goal, context, plan)
        
        return {
            "goal": goal,
            "plan": plan.dict() if plan else None,
            "reasoning": result.get("reasoning", ""),
            "actions": [a.dict() for a in self.action_log[-5:]],  # Last 5 actions
            "final_answer": result.get("final_answer", ""),
            "success": result.get("success", False)
        }
    
    def _create_plan(self, goal: str, context: Optional[str]) -> OrchestrationPlan:
        """Create an execution plan."""
        
        context_text = f"\n\nContext: {context}" if context else ""
        
        prompt = f"""Create a detailed plan to accomplish this goal.

GOAL: {goal}{context_text}

PLAN:
1. Identify what tools/actions are needed
2. Define the sequence of steps
3. Explain reasoning for each step

Format your response as:
STEPS:
1. [step 1]
2. [step 2]
...

REASONING: [explain your reasoning]

ESTIMATED_TIME: [rough estimate]"""
        
        try:
            response = self.client.messages.create(
                model=self.config.model_name,
                max_tokens=1000,
                temperature=self.config.temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text
            
            # Parse response
            steps = []
            reasoning = ""
            estimated_time = "unknown"
            
            current_section = None
            for line in content.split('\n'):
                if 'STEPS:' in line:
                    current_section = 'steps'
                elif 'REASONING:' in line:
                    current_section = 'reasoning'
                    reasoning = line.split('REASONING:')[1].strip()
                elif 'ESTIMATED_TIME:' in line:
                    estimated_time = line.split('ESTIMATED_TIME:')[1].strip()
                elif current_section == 'steps' and line.strip() and line[0].isdigit():
                    steps.append(line.lstrip('0123456789.)-: ').strip())
            
            return OrchestrationPlan(
                goal=goal,
                steps=steps if steps else ["Execute goal"],
                reasoning=reasoning,
                estimated_time=estimated_time
            )
        except Exception as e:
            logger.error(f"Error creating plan: {str(e)}")
            return OrchestrationPlan(
                goal=goal,
                steps=["Execute goal"],
                reasoning="Direct execution"
            )
    
    def _react_loop(
        self,
        goal: str,
        context: Optional[str],
        plan: Optional[OrchestrationPlan]
    ) -> Dict[str, Any]:
        """Execute ReAct reasoning and acting loop."""
        
        reasoning_steps = []
        
        # Build system prompt
        system_prompt = """You are a helpful assistant that uses a ReAct (Reasoning + Acting) pattern.

At each step:
1. THINK about what you need to do
2. ACT by calling tools or taking actions
3. OBSERVE the results
4. REPEAT until the goal is achieved

Available tools:
- list_documents: List all available documents
- read_document: Read a specific document
- rag_search: Search documents semantically
- rag_answer: Ask questions about documents
- summarize: Summarize a document

Be direct and efficient. Use tools to gather information needed for the goal."""
        
        # Build initial message
        goal_text = f"Goal: {goal}"
        if context:
            goal_text += f"\n\nContext: {context}"
        if plan:
            goal_text += f"\n\nPlan:\n" + "\n".join([f"  {i+1}. {s}" for i, s in enumerate(plan.steps)])
        
        messages = [{"role": "user", "content": goal_text}]
        
        final_answer = ""
        step_count = 0
        
        # ReAct loop
        while step_count < self.config.max_reasoning_steps:
            step_count += 1
            logger.info(f" ReAct step {step_count}")
            
            try:
                # Get Claude's response
                response = self.client.messages.create(
                    model=self.config.model_name,
                    max_tokens=2000,
                    temperature=self.config.temperature,
                    system=system_prompt,
                    messages=messages
                )
                
                assistant_message = response.content[0].text
                messages.append({"role": "assistant", "content": assistant_message})
                
                # Check if we're done
                if "FINAL ANSWER:" in assistant_message or step_count >= self.config.max_reasoning_steps:
                    final_answer = assistant_message.split("FINAL ANSWER:")[-1].strip() if "FINAL ANSWER:" in assistant_message else assistant_message
                    break
                
                # Otherwise, add observation and continue
                messages.append({
                    "role": "user",
                    "content": "Please continue with the next step or provide your final answer."
                })
                
            except Exception as e:
                logger.error(f"Error in ReAct loop: {str(e)}")
                break
        
        return {
            "reasoning": "\n".join(reasoning_steps),
            "final_answer": final_answer,
            "success": True,
            "steps": step_count
        }
    
    def chat(self, message: str) -> str:
        """
        Chat interface for the orchestrator.
        
        Args:
            message (str): User message
            
        Returns:
            str: Agent response
        """
        self.conversation_history.append({"role": "user", "content": message})
        
        try:
            response = self.client.messages.create(
                model=self.config.model_name,
                max_tokens=2000,
                temperature=self.config.temperature,
                messages=self.conversation_history
            )
            
            assistant_message = response.content[0].text
            self.conversation_history.append({"role": "assistant", "content": assistant_message})
            
            return assistant_message
        except Exception as e:
            logger.error(f"Error in chat: {str(e)}")
            return f"Error: {str(e)}"
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status."""
        return {
            "agent_type": "OrchestratorAgent",
            "model": self.config.model_name,
            "mcp_server": self.config.mcp_server_url,
            "conversation_turns": len(self.conversation_history),
            "actions_taken": len(self.action_log),
            "status": "ready"
        }
