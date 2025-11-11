"""
Multi-Model Consensus Generation

Generates content with multiple LLMs and synthesizes the best elements
to produce higher-quality, more balanced content.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from .ai_content_generator import AIContentGenerator
from .base_provider import AIRequest, AIGenerationConfig, ContentType
from .enhanced_prompts import EnhancedPromptBuilder

logger = logging.getLogger(__name__)


@dataclass
class ConsensusResult:
    """Result from consensus generation."""
    final_content: str
    draft_variations: List[Dict[str, Any]]
    synthesis_metadata: Dict[str, Any]
    best_sections: Dict[str, str]  # section_name -> best_content
    total_tokens: int
    total_cost: float


class ConsensusGenerator:
    """Generates content using multi-model consensus approach."""
    
    def __init__(self, ai_generator: AIContentGenerator):
        """
        Initialize consensus generator.
        
        Args:
            ai_generator: AI content generator instance
        """
        self.ai_generator = ai_generator
        self.prompt_builder = EnhancedPromptBuilder()
    
    async def generate_with_consensus(
        self,
        topic: str,
        outline: str,
        keywords: List[str],
        tone: str = "professional",
        length: str = "medium",
        additional_context: Optional[Dict[str, Any]] = None
    ) -> ConsensusResult:
        """
        Generate content using multi-model consensus.
        
        Args:
            topic: Blog topic
            outline: Content outline
            keywords: Target keywords
            tone: Content tone
            length: Content length
            additional_context: Additional context
        
        Returns:
            ConsensusResult with synthesized content
        """
        # Step 1: Generate draft with GPT-4o
        logger.info("Generating draft with GPT-4o")
        gpt_draft = await self._generate_draft(
            topic, outline, keywords, tone, length,
            provider="openai",
            model_preference="gpt-4o",
            additional_context=additional_context
        )
        
        # Step 2: Generate alternative draft with Claude 3.5 Sonnet
        logger.info("Generating alternative draft with Claude 3.5 Sonnet")
        claude_draft = await self._generate_draft(
            topic, outline, keywords, tone, length,
            provider="anthropic",
            model_preference="claude-3-5-sonnet-20241022",
            additional_context=additional_context
        )
        
        # Step 3: Use GPT-4o-mini to compare and extract best sections
        logger.info("Synthesizing best sections")
        synthesis_result = await self._synthesize_best_sections(
            gpt_draft["content"],
            claude_draft["content"],
            topic,
            keywords
        )
        
        # Step 4: Use Claude for final coherence check
        logger.info("Final coherence check with Claude")
        final_content = await self._final_coherence_check(
            synthesis_result["synthesized_content"],
            topic,
            keywords
        )
        
        # Calculate totals
        total_tokens = (
            gpt_draft["tokens_used"] +
            claude_draft["tokens_used"] +
            synthesis_result["tokens_used"] +
            final_content["tokens_used"]
        )
        total_cost = (
            gpt_draft.get("cost", 0) +
            claude_draft.get("cost", 0) +
            synthesis_result.get("cost", 0) +
            final_content.get("cost", 0)
        )
        
        return ConsensusResult(
            final_content=final_content["content"],
            draft_variations=[
                {
                    "provider": "openai",
                    "content": gpt_draft["content"],
                    "tokens": gpt_draft["tokens_used"],
                    "cost": gpt_draft.get("cost", 0)
                },
                {
                    "provider": "anthropic",
                    "content": claude_draft["content"],
                    "tokens": claude_draft["tokens_used"],
                    "cost": claude_draft.get("cost", 0)
                }
            ],
            synthesis_metadata=synthesis_result.get("metadata", {}),
            best_sections=synthesis_result.get("best_sections", {}),
            total_tokens=total_tokens,
            total_cost=total_cost
        )
    
    async def _generate_draft(
        self,
        topic: str,
        outline: str,
        keywords: List[str],
        tone: str,
        length: str,
        provider: str,
        model_preference: Optional[str] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate a draft with specified provider."""
        prompt = self.prompt_builder.build_draft_prompt(
            topic=topic,
            outline=outline,
            keywords=keywords,
            tone=tone,
            length=length,
            template=None,
            context=additional_context
        )
        
        # Add provider-specific instructions
        if provider == "openai":
            prompt += "\n\nFocus on comprehensive coverage and detailed explanations."
        elif provider == "anthropic":
            prompt += "\n\nFocus on clarity, reasoning, and unique insights."
        
        request = AIRequest(
            prompt=prompt,
            content_type=ContentType.BLOG_POST,
            config=AIGenerationConfig(
                max_tokens=3000,
                temperature=0.8,
                top_p=0.9
            )
        )
        
        response = await self.ai_generator.provider_manager.generate_content(
            request=request,
            preferred_provider=provider
        )
        
        return {
            "content": response.content,
            "tokens_used": response.tokens_used,
            "cost": response.cost or 0.0,
            "provider": response.provider
        }
    
    async def _synthesize_best_sections(
        self,
        draft1: str,
        draft2: str,
        topic: str,
        keywords: List[str]
    ) -> Dict[str, Any]:
        """Synthesize best sections from both drafts."""
        prompt = f"""You are an expert content editor. Your task is to compare two drafts of the same blog post and synthesize the best elements from each.

TOPIC: {topic}
KEYWORDS: {', '.join(keywords)}

DRAFT 1 (GPT-4o):
{draft1[:2000]}

DRAFT 2 (Claude):
{draft2[:2000]}

TASK:
1. Identify the strongest sections from each draft
2. Extract the best content from Draft 1 (comprehensive coverage, details)
3. Extract the best content from Draft 2 (clarity, insights, reasoning)
4. Synthesize a final version that combines the strengths of both
5. Ensure smooth transitions and coherence

OUTPUT:
Provide the synthesized content that combines the best elements from both drafts.
Focus on:
- Best explanations and details from Draft 1
- Best insights and clarity from Draft 2
- Natural flow and coherence
- No repetition or redundancy
"""
        
        request = AIRequest(
            prompt=prompt,
            content_type=ContentType.BLOG_POST,
            config=AIGenerationConfig(
                max_tokens=4000,
                temperature=0.7,
                top_p=0.9
            )
        )
        
        response = await self.ai_generator.provider_manager.generate_content(
            request=request,
            preferred_provider="openai"  # Use GPT-4o-mini for cost efficiency
        )
        
        return {
            "synthesized_content": response.content,
            "tokens_used": response.tokens_used,
            "cost": response.cost or 0.0,
            "best_sections": {},  # Could be enhanced to extract specific sections
            "metadata": {
                "synthesis_method": "multi_draft_comparison",
                "drafts_compared": 2
            }
        }
    
    async def _final_coherence_check(
        self,
        content: str,
        topic: str,
        keywords: List[str]
    ) -> Dict[str, Any]:
        """Perform final coherence check with Claude."""
        prompt = f"""You are an expert content editor performing a final coherence check.

TOPIC: {topic}
KEYWORDS: {', '.join(keywords)}

CONTENT TO REVIEW:
{content[:3000]}

TASK:
Review the content and ensure:
1. Smooth transitions between sections
2. Consistent tone throughout
3. Logical flow and coherence
4. No contradictions or inconsistencies
5. Natural keyword integration
6. Clear, engaging narrative

Make minimal edits - only improve flow and coherence. Return the refined content.
"""
        
        request = AIRequest(
            prompt=prompt,
            content_type=ContentType.BLOG_POST,
            config=AIGenerationConfig(
                max_tokens=3500,
                temperature=0.6,
                top_p=0.9
            )
        )
        
        response = await self.ai_generator.provider_manager.generate_content(
            request=request,
            preferred_provider="anthropic"
        )
        
        return {
            "content": response.content,
            "tokens_used": response.tokens_used,
            "cost": response.cost or 0.0
        }

