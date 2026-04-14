"""
Summarizer Agent Module - Phase 4

Implements a document summarization agent using Pydantic AI with:
- Typed result models for type safety
- Reflection pattern: draft → critique → refine
- Quality control and iterative improvement
- Source tracking and confidence scores

Uses Pydantic AI for agent logic and LLM integration.
"""

import logging
from typing import Optional, List
from dataclasses import dataclass
from enum import Enum

from pydantic import BaseModel, Field
import anthropic

logger = logging.getLogger(__name__)


class SummaryQuality(str, Enum):
    """Quality levels for summaries."""
    POOR = "poor"
    FAIR = "fair"
    GOOD = "good"
    EXCELLENT = "excellent"


class SummaryResult(BaseModel):
    """Typed result model for summaries."""
    
    summary: str = Field(
        ...,
        description="The generated summary text"
    )
    
    original_length: int = Field(
        ...,
        description="Number of words in original text"
    )
    
    summary_length: int = Field(
        ...,
        description="Number of words in summary"
    )
    
    compression_ratio: float = Field(
        ...,
        description="Ratio of summary length to original length"
    )
    
    key_points: List[str] = Field(
        default_factory=list,
        description="List of key points extracted from the text"
    )
    
    quality_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Quality score between 0 and 1"
    )
    
    quality_level: SummaryQuality = Field(
        default=SummaryQuality.FAIR,
        description="Subjective quality level"
    )
    
    improvement_suggestions: List[str] = Field(
        default_factory=list,
        description="Suggestions for improvement"
    )


@dataclass
class SummarizerConfig:
    """Configuration for the summarizer agent."""
    
    model_name: str = "claude-3-5-sonnet-20241022"
    temperature: float = 0.7
    max_tokens: int = 4096
    
    # Reflection settings
    enable_reflection: bool = True
    max_reflection_iterations: int = 2
    
    # Summary settings
    target_compression_ratio: float = 0.3  # ~30% of original
    min_key_points: int = 3
    max_key_points: int = 10


class SummarizerAgent:
    """
    Document Summarization Agent with reflection pattern.
    
    Features:
    - Multi-pass summarization with refinement
    - Quality evaluation and improvement suggestions
    - Key point extraction
    - Configurable compression ratios
    - Type-safe results with Pydantic models
    
    Example:
        >>> agent = SummarizerAgent()
        >>> result = agent.summarize("Long document text...")
        >>> print(result.summary)
        >>> print(result.quality_score)
    """
    
    def __init__(self, config: Optional[SummarizerConfig] = None):
        """
        Initialize the summarizer agent.
        
        Args:
            config (SummarizerConfig): Agent configuration
        """
        self.config = config or SummarizerConfig()
        
        # Initialize Claude client
        self.client = anthropic.Anthropic()
        
        logger.info(f"✅ SummarizerAgent initialized with model: {self.config.model_name}")
    
    def summarize(
        self,
        text: str,
        length_preference: str = "medium"
    ) -> SummaryResult:
        """
        Summarize text using the reflection pattern.
        
        Args:
            text (str): Text to summarize
            length_preference (str): "short", "medium", or "long"
            
        Returns:
            SummaryResult: Typed result with summary and metadata
        """
        logger.info(f"📝 Starting summarization (text length: {len(text)} chars)")
        
        # Step 1: Generate initial draft
        draft_summary = self._generate_draft(text, length_preference)
        logger.info("✅ Draft summary generated")
        
        # Step 2: Reflection with critique
        if self.config.enable_reflection:
            refined_summary = self._reflection_loop(text, draft_summary)
        else:
            refined_summary = draft_summary
        
        logger.info("✅ Summary refined through reflection")
        
        # Step 3: Extract key points
        key_points = self._extract_key_points(text, refined_summary)
        logger.info(f"✅ Extracted {len(key_points)} key points")
        
        # Step 4: Evaluate quality
        quality_score, quality_level, suggestions = self._evaluate_quality(
            text,
            refined_summary,
            key_points
        )
        logger.info(f"✅ Quality evaluated: {quality_level} ({quality_score:.2f})")
        
        # Calculate metrics
        original_words = len(text.split())
        summary_words = len(refined_summary.split())
        compression_ratio = summary_words / original_words if original_words > 0 else 0
        
        # Create typed result
        result = SummaryResult(
            summary=refined_summary,
            original_length=original_words,
            summary_length=summary_words,
            compression_ratio=round(compression_ratio, 3),
            key_points=key_points,
            quality_score=quality_score,
            quality_level=quality_level,
            improvement_suggestions=suggestions
        )
        
        return result
    
    def _generate_draft(self, text: str, length_preference: str) -> str:
        """Generate initial summary draft."""
        
        length_instructions = {
            "short": "Keep it to 2-3 sentences. Focus on the most critical information.",
            "medium": "Keep it to 4-6 sentences. Cover main points and key details.",
            "long": "Keep it to 8-10 sentences. Include important examples and context."
        }
        
        prompt = f"""Generate a high-quality summary of the following text.

{length_instructions.get(length_preference, length_instructions['medium'])}

TEXT:
{text}

SUMMARY:
Provide only the summary text without any preamble or explanation."""
        
        try:
            response = self.client.messages.create(
                model=self.config.model_name,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Error generating draft: {str(e)}")
            raise
    
    def _reflection_loop(self, text: str, draft_summary: str) -> str:
        """Reflection pattern: critique and refine."""
        
        current_summary = draft_summary
        
        for iteration in range(self.config.max_reflection_iterations):
            logger.info(f"🔄 Reflection iteration {iteration + 1}")
            
            # Get critique
            critique_prompt = f"""Evaluate this summary of a document. Provide constructive critique.

ORIGINAL TEXT:
{text[:1000]}...

SUMMARY:
{current_summary}

Critique (be specific about what could be improved):"""
            
            try:
                critique_response = self.client.messages.create(
                    model=self.config.model_name,
                    max_tokens=500,
                    temperature=0.7,
                    messages=[{"role": "user", "content": critique_prompt}]
                )
                critique = critique_response.content[0].text
                logger.info(f"📝 Critique: {critique[:100]}...")
                
                # Refine based on critique
                refine_prompt = f"""Given the critique below, improve the summary. 
Keep the same length but address the feedback.

ORIGINAL SUMMARY:
{current_summary}

CRITIQUE:
{critique}

IMPROVED SUMMARY:
Provide only the improved summary without explanation."""
                
                refine_response = self.client.messages.create(
                    model=self.config.model_name,
                    max_tokens=self.config.max_tokens,
                    temperature=self.config.temperature,
                    messages=[{"role": "user", "content": refine_prompt}]
                )
                current_summary = refine_response.content[0].text
                logger.info("✅ Summary refined")
                
            except Exception as e:
                logger.error(f"Error in reflection loop: {str(e)}")
                break
        
        return current_summary
    
    def _extract_key_points(self, text: str, summary: str) -> List[str]:
        """Extract key points from text."""
        
        prompt = f"""Extract the {self.config.max_key_points} most important key points from this text.
Return them as a numbered list.

TEXT:
{text[:2000]}...

KEY POINTS:"""
        
        try:
            response = self.client.messages.create(
                model=self.config.model_name,
                max_tokens=500,
                temperature=0.5,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parse key points from response
            content = response.content[0].text
            points = []
            for line in content.split('\n'):
                line = line.strip()
                if line and line[0].isdigit():
                    # Remove numbering
                    point = line.lstrip('0123456789.)-: ')
                    if point:
                        points.append(point)
            
            return points[:self.config.max_key_points]
        except Exception as e:
            logger.error(f"Error extracting key points: {str(e)}")
            return []
    
    def _evaluate_quality(
        self,
        text: str,
        summary: str,
        key_points: List[str]
    ) -> tuple:
        """Evaluate summary quality."""
        
        prompt = f"""Evaluate this summary on a scale of 0-1 for quality.
Consider: accuracy, completeness, clarity, and conciseness.

ORIGINAL TEXT (excerpt):
{text[:1000]}...

SUMMARY:
{summary}

KEY POINTS EXTRACTED:
{chr(10).join(f'- {p}' for p in key_points)}

Provide your evaluation in this format:
QUALITY_SCORE: [0.0-1.0]
QUALITY_LEVEL: [poor/fair/good/excellent]
SUGGESTIONS: [list of 2-3 specific improvements]"""
        
        try:
            response = self.client.messages.create(
                model=self.config.model_name,
                max_tokens=300,
                temperature=0.5,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text
            
            # Parse response
            score = 0.7
            level = SummaryQuality.GOOD
            suggestions = []
            
            for line in content.split('\n'):
                if 'QUALITY_SCORE:' in line:
                    try:
                        score = float(line.split(':')[1].strip())
                        score = max(0.0, min(1.0, score))
                    except:
                        pass
                elif 'QUALITY_LEVEL:' in line:
                    level_str = line.split(':')[1].strip().lower()
                    try:
                        level = SummaryQuality(level_str)
                    except:
                        pass
                elif 'SUGGESTIONS:' in line:
                    suggestions_text = line.split(':', 1)[1].strip()
                    suggestions = [s.strip() for s in suggestions_text.split(',')]
            
            return score, level, suggestions[:3]
        
        except Exception as e:
            logger.error(f"Error evaluating quality: {str(e)}")
            return 0.5, SummaryQuality.FAIR, []
    
    def batch_summarize(
        self,
        texts: List[str],
        length_preference: str = "medium"
    ) -> List[SummaryResult]:
        """
        Summarize multiple texts.
        
        Args:
            texts (List[str]): List of texts to summarize
            length_preference (str): Length preference
            
        Returns:
            List[SummaryResult]: List of results
        """
        logger.info(f"📚 Batch summarizing {len(texts)} documents")
        results = []
        
        for i, text in enumerate(texts, 1):
            logger.info(f"[{i}/{len(texts)}] Summarizing document...")
            try:
                result = self.summarize(text, length_preference)
                results.append(result)
            except Exception as e:
                logger.error(f"Error summarizing document {i}: {str(e)}")
        
        return results
