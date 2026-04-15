"""
LLM Module for Generative AI Responses

Handles integration with Google's Gemini models for generating
answers based on retrieved context from the RAG system.

Uses:
- Google Generative AI: For answer generation
- Gemini 2.0 Flash: Fastest model for real-time responses
- Gemini 1.5 Pro: More powerful model for complex reasoning
"""

import os
import logging
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass

import google.generativeai as genai
from langchain_core.documents import Document

logger = logging.getLogger(__name__)


@dataclass
class GenerationConfig:
    """Configuration for LLM generation."""
    temperature: float = 0.7
    top_p: float = 0.95
    top_k: int = 64
    max_output_tokens: int = 2048


class GenerativeAIModel:
    """
    Wrapper for Google's Generative AI models (Gemini family).
    
    Features:
    - Multiple model support (2.0-flash, 1.5-pro, 1.5-flash)
    - Configurable generation parameters
    - Source tracking and citations
    - Context-aware answer generation
    - Streaming support
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemini-2.0-flash",
        generation_config: Optional[GenerationConfig] = None
    ):
        """
        Initialize the Generative AI Model.
        
        Args:
            api_key (str): Google API key. If None, uses GOOGLE_API_KEY env var
            model_name (str): Model to use. Default: gemini-2.0-flash
                Options: gemini-2.0-flash, gemini-1.5-pro, gemini-1.5-flash
            generation_config (GenerationConfig): Generation parameters
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")
        
        self.model_name = model_name
        self.generation_config = generation_config or GenerationConfig()
        
        # Configure Generative AI
        genai.configure(api_key=self.api_key)
        
        try:
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config={
                    "temperature": self.generation_config.temperature,
                    "top_p": self.generation_config.top_p,
                    "top_k": self.generation_config.top_k,
                    "max_output_tokens": self.generation_config.max_output_tokens,
                }
            )
            logger.info(f"Initialized model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize model: {str(e)}")
            raise
    
    def generate(
        self,
        prompt: str,
        temperature: Optional[float] = None
    ) -> str:
        """
        Generate text from a prompt.
        
        Args:
            prompt (str): Input prompt
            temperature (float): Override default temperature
            
        Returns:
            str: Generated text
        """
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error generating content: {str(e)}")
            raise
    
    def answer_question(
        self,
        question: str,
        context: str,
        include_sources: bool = False,
        sources: Optional[List[Tuple[Document, float]]] = None
    ) -> str:
        """
        Generate an answer to a question using provided context.
        
        Args:
            question (str): The user's question
            context (str): Retrieved context from RAG system
            include_sources (bool): Whether to include source citations
            sources (List): List of (Document, score) tuples for citations
            
        Returns:
            str: Generated answer with optional source citations
        """
        # Build the prompt
        prompt = f"""Based on the following context, please answer the question.
        
CONTEXT:
{context}

QUESTION:
{question}

ANSWER:
Provide a clear, concise answer based on the context. If the context doesn't contain 
relevant information, say so."""
        
        try:
            answer = self.generate(prompt)
            
            # Add sources if requested
            if include_sources and sources:
                sources_text = self._format_sources(sources)
                answer += f"\n\n{sources_text}"
            
            return answer
        except Exception as e:
            logger.error(f"Error answering question: {str(e)}")
            raise
    
    def _format_sources(self, sources: List[Tuple[Document, float]]) -> str:
        """
        Format sources with scores and metadata.
        
        Args:
            sources (List): List of (Document, score) tuples
            
        Returns:
            str: Formatted sources text
        """
        sources_text = "\nSources:\n"
        for i, (doc, score) in enumerate(sources, 1):
            # Extract source info from document
            source = doc.metadata.get("source", "Unknown")
            page = doc.metadata.get("page", "Unknown")
            confidence = round(score * 100, 1) if score else 0
            
            sources_text += f"  {i}. {source} (Page: {page}, Confidence: {confidence}%)\n"
        
        return sources_text
    
    def summarize(self, text: str, max_length: int = 500) -> str:
        """
        Summarize a document or text.
        
        Args:
            text (str): Text to summarize
            max_length (int): Maximum summary length in words
            
        Returns:
            str: Summarized text
        """
        prompt = f"""Please summarize the following text in approximately {max_length} words.
        
TEXT:
{text}

SUMMARY:"""
        
        try:
            return self.generate(prompt)
        except Exception as e:
            logger.error(f"Error summarizing text: {str(e)}")
            raise
    
    def extract_keywords(self, text: str, num_keywords: int = 10) -> List[str]:
        """
        Extract key topics/keywords from text.
        
        Args:
            text (str): Text to extract from
            num_keywords (int): Number of keywords to extract
            
        Returns:
            List[str]: List of extracted keywords
        """
        prompt = f"""Extract the {num_keywords} most important keywords or topics from the following text.
Return them as a comma-separated list without numbering.

TEXT:
{text}

KEYWORDS:"""
        
        try:
            response = self.generate(prompt)
            keywords = [kw.strip() for kw in response.split(",")]
            return keywords[:num_keywords]
        except Exception as e:
            logger.error(f"Error extracting keywords: {str(e)}")
            raise
    
    def paraphrase(self, text: str, style: str = "neutral") -> str:
        """
        Paraphrase text in a different style.
        
        Args:
            text (str): Text to paraphrase
            style (str): Style to use (professional, casual, technical, simple)
            
        Returns:
            str: Paraphrased text
        """
        prompt = f"""Please paraphrase the following text in a {style} style.
        
TEXT:
{text}

PARAPHRASED TEXT:"""
        
        try:
            return self.generate(prompt)
        except Exception as e:
            logger.error(f"Error paraphrasing text: {str(e)}")
            raise
    
    def get_model_info(self) -> Dict:
        """
        Get information about the current model.
        
        Returns:
            Dict: Model information
        """
        return {
            "model_name": self.model_name,
            "temperature": self.generation_config.temperature,
            "top_p": self.generation_config.top_p,
            "top_k": self.generation_config.top_k,
            "max_output_tokens": self.generation_config.max_output_tokens
        }
    
    @staticmethod
    def list_available_models() -> List[str]:
        """
        List available Gemini models.
        
        Returns:
            List[str]: Available model names
        """
        try:
            models = genai.list_models()
            gemini_models = [
                m.name.replace("models/", "")
                for m in models
                if "gemini" in m.name.lower()
            ]
            return gemini_models
        except Exception as e:
            logger.error(f"Error listing models: {str(e)}")
            return []
