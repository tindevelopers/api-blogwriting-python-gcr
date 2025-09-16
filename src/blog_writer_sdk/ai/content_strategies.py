"""
Content Generation Strategies

This module implements the Strategy pattern for different content generation
approaches, allowing for flexible and extensible content creation methods.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass

from .base_provider import AIRequest, AIResponse, ContentType, AIGenerationConfig
from .blog_writer_abstraction import ContentStrategy, BlogGenerationRequest, BlogGenerationResult
from ..models.blog_models import ContentTone, ContentLength


logger = logging.getLogger(__name__)


@dataclass
class ContentStructure:
    """Content structure definition."""
    sections: List[str]
    section_descriptions: Dict[str, str]
    recommended_lengths: Dict[str, int]
    required_elements: List[str]
    optional_elements: List[str]


class ContentGenerationStrategy(ABC):
    """Abstract base class for content generation strategies."""
    
    @abstractmethod
    async def generate_content_structure(
        self, 
        topic: str, 
        keywords: List[str],
        target_length: ContentLength
    ) -> ContentStructure:
        """Generate content structure for the topic."""
        pass
    
    @abstractmethod
    async def create_section_prompts(
        self, 
        structure: ContentStructure,
        topic: str,
        keywords: List[str],
        tone: ContentTone,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """Create prompts for each content section."""
        pass
    
    @abstractmethod
    async def optimize_content_flow(
        self, 
        sections: Dict[str, str],
        structure: ContentStructure
    ) -> Dict[str, str]:
        """Optimize content flow between sections."""
        pass
    
    @abstractmethod
    def get_strategy_metadata(self) -> Dict[str, Any]:
        """Get strategy-specific metadata."""
        pass


class SEOContentStrategy(ContentGenerationStrategy):
    """SEO-optimized content generation strategy."""
    
    async def generate_content_structure(
        self, 
        topic: str, 
        keywords: List[str],
        target_length: ContentLength
    ) -> ContentStructure:
        """Generate SEO-optimized content structure."""
        primary_keyword = keywords[0] if keywords else topic.lower()
        
        # Define SEO-optimized structure
        sections = [
            "introduction",
            "main_content_section_1",
            "main_content_section_2", 
            "main_content_section_3",
            "conclusion",
            "faq_section"
        ]
        
        section_descriptions = {
            "introduction": f"Engaging introduction that hooks readers and includes primary keyword '{primary_keyword}'",
            "main_content_section_1": f"First main section covering key aspects of {topic} with keyword integration",
            "main_content_section_2": f"Second main section with detailed insights about {topic}",
            "main_content_section_3": f"Third main section providing actionable advice related to {topic}",
            "conclusion": f"Strong conclusion that summarizes key points and includes call-to-action",
            "faq_section": f"FAQ section addressing common questions about {topic}"
        }
        
        # Calculate section lengths based on target length
        total_words = self._get_target_word_count(target_length)
        section_lengths = {
            "introduction": int(total_words * 0.15),
            "main_content_section_1": int(total_words * 0.25),
            "main_content_section_2": int(total_words * 0.25),
            "main_content_section_3": int(total_words * 0.20),
            "conclusion": int(total_words * 0.10),
            "faq_section": int(total_words * 0.05)
        }
        
        return ContentStructure(
            sections=sections,
            section_descriptions=section_descriptions,
            recommended_lengths=section_lengths,
            required_elements=["h1", "h2", "h3", "meta_description", "internal_links"],
            optional_elements=["images", "videos", "infographics", "external_links"]
        )
    
    async def create_section_prompts(
        self, 
        structure: ContentStructure,
        topic: str,
        keywords: List[str],
        tone: ContentTone,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """Create SEO-optimized prompts for each section."""
        prompts = {}
        primary_keyword = keywords[0] if keywords else topic.lower()
        
        for section in structure.sections:
            if section == "introduction":
                prompts[section] = f"""Write an engaging, SEO-optimized introduction for a blog post about "{topic}".

Requirements:
- Start with a compelling hook that grabs attention
- Include the primary keyword "{primary_keyword}" naturally in the first paragraph
- Target length: {structure.recommended_lengths[section]} words
- Tone: {tone.value}
- Clearly establish what readers will learn
- Create curiosity to encourage continued reading
- Include secondary keywords: {', '.join(keywords[1:3]) if len(keywords) > 1 else 'N/A'}

Make it engaging and informative while maintaining SEO best practices."""

            elif section.startswith("main_content_section"):
                section_num = section.split("_")[-1]
                prompts[section] = f"""Write the {section_num} main content section for a blog post about "{topic}".

Requirements:
- Target length: {structure.recommended_lengths[section]} words
- Tone: {tone.value}
- Include primary keyword "{primary_keyword}" naturally
- Provide valuable, actionable information
- Use proper heading structure (H2, H3)
- Include relevant examples or case studies
- Make it scannable with bullet points or numbered lists
- Include internal linking opportunities
- Focus on depth and value for readers

Section description: {structure.section_descriptions[section]}"""

            elif section == "conclusion":
                prompts[section] = f"""Write a strong, SEO-optimized conclusion for a blog post about "{topic}".

Requirements:
- Target length: {structure.recommended_lengths[section]} words
- Tone: {tone.value}
- Summarize key points covered in the article
- Include primary keyword "{primary_keyword}" naturally
- Provide actionable next steps for readers
- End with a compelling call-to-action
- Reinforce the value provided to readers
- Encourage engagement (comments, shares, etc.)

Make it memorable and motivating while maintaining SEO value."""

            elif section == "faq_section":
                prompts[section] = f"""Create a comprehensive FAQ section for a blog post about "{topic}".

Requirements:
- Target length: {structure.recommended_lengths[section]} words
- Generate 5-7 relevant questions and detailed answers
- Include primary keyword "{primary_keyword}" in questions naturally
- Address common concerns and misconceptions
- Use conversational, helpful tone
- Format as proper Q&A with clear headings
- Provide valuable, actionable information
- Include long-tail keyword variations

Focus on questions that real readers would actually ask about this topic."""

        return prompts
    
    async def optimize_content_flow(
        self, 
        sections: Dict[str, str],
        structure: ContentStructure
    ) -> Dict[str, str]:
        """Optimize content flow for SEO."""
        optimized_sections = sections.copy()
        
        # Add transition sentences between sections
        # Ensure keyword distribution is optimal
        # Add internal linking suggestions
        # Optimize heading structure
        
        return optimized_sections
    
    def get_strategy_metadata(self) -> Dict[str, Any]:
        """Get SEO strategy metadata."""
        return {
            "strategy_type": "seo_optimized",
            "focus_areas": ["keyword_optimization", "content_structure", "user_experience"],
            "seo_elements": ["meta_tags", "heading_structure", "internal_linking", "keyword_density"],
            "content_flow": "logical_progression",
            "optimization_level": "high"
        }
    
    def _get_target_word_count(self, length: ContentLength) -> int:
        """Get target word count based on content length."""
        targets = {
            ContentLength.SHORT: 800,
            ContentLength.MEDIUM: 1500,
            ContentLength.LONG: 2500,
            ContentLength.EXTENDED: 4000
        }
        return targets.get(length, 1500)


class EngagementContentStrategy(ContentGenerationStrategy):
    """Engagement-focused content generation strategy."""
    
    async def generate_content_structure(
        self, 
        topic: str, 
        keywords: List[str],
        target_length: ContentLength
    ) -> ContentStructure:
        """Generate engagement-focused content structure."""
        sections = [
            "hook_introduction",
            "story_section",
            "value_proposition",
            "interactive_section",
            "social_proof",
            "call_to_action"
        ]
        
        section_descriptions = {
            "hook_introduction": f"Compelling hook that immediately grabs attention and creates emotional connection",
            "story_section": f"Personal story or case study related to {topic} that readers can relate to",
            "value_proposition": f"Clear value proposition explaining what readers will gain from {topic}",
            "interactive_section": f"Interactive element that encourages reader participation and engagement",
            "social_proof": f"Social proof elements showing others' success with {topic}",
            "call_to_action": f"Strong call-to-action that motivates readers to take the next step"
        }
        
        total_words = self._get_target_word_count(target_length)
        section_lengths = {
            "hook_introduction": int(total_words * 0.20),
            "story_section": int(total_words * 0.30),
            "value_proposition": int(total_words * 0.20),
            "interactive_section": int(total_words * 0.15),
            "social_proof": int(total_words * 0.10),
            "call_to_action": int(total_words * 0.05)
        }
        
        return ContentStructure(
            sections=sections,
            section_descriptions=section_descriptions,
            recommended_lengths=section_lengths,
            required_elements=["emotional_hooks", "storytelling", "interactive_elements"],
            optional_elements=["polls", "quizzes", "videos", "user_generated_content"]
        )
    
    async def create_section_prompts(
        self, 
        structure: ContentStructure,
        topic: str,
        keywords: List[str],
        tone: ContentTone,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """Create engagement-focused prompts for each section."""
        prompts = {}
        
        for section in structure.sections:
            if section == "hook_introduction":
                prompts[section] = f"""Write a compelling, emotionally engaging introduction for a blog post about "{topic}".

Requirements:
- Start with a powerful hook that creates immediate emotional connection
- Target length: {structure.recommended_lengths[section]} words
- Tone: {tone.value}
- Use storytelling elements or surprising statistics
- Create curiosity and emotional investment
- Make readers feel understood and connected
- Include keywords naturally: {', '.join(keywords[:3])}

Focus on emotional resonance and immediate engagement."""

            elif section == "story_section":
                prompts[section] = f"""Write a compelling story section for a blog post about "{topic}".

Requirements:
- Target length: {structure.recommended_lengths[section]} words
- Tone: {tone.value}
- Tell a relatable story or case study
- Make it personal and authentic
- Include specific details and emotions
- Show transformation or journey
- Connect the story to the main topic
- Use vivid descriptions and dialogue

Make readers feel like they're part of the story."""

            elif section == "value_proposition":
                prompts[section] = f"""Write a clear value proposition section for a blog post about "{topic}".

Requirements:
- Target length: {structure.recommended_lengths[section]} words
- Tone: {tone.value}
- Clearly explain what readers will gain
- Use benefit-focused language
- Include specific outcomes and results
- Address reader pain points
- Make it compelling and actionable
- Use "you" language to connect with readers

Focus on the transformation readers will experience."""

            elif section == "interactive_section":
                prompts[section] = f"""Create an interactive section for a blog post about "{topic}".

Requirements:
- Target length: {structure.recommended_lengths[section]} words
- Tone: {tone.value}
- Include questions for readers to reflect on
- Add interactive elements (polls, quizzes, exercises)
- Encourage reader participation
- Make it engaging and fun
- Provide immediate value
- Create community feeling

Make readers want to participate and engage."""

            elif section == "social_proof":
                prompts[section] = f"""Write a social proof section for a blog post about "{topic}".

Requirements:
- Target length: {structure.recommended_lengths[section]} words
- Tone: {tone.value}
- Include testimonials or success stories
- Show numbers and statistics
- Highlight community or user achievements
- Build trust and credibility
- Use specific examples
- Make it relatable and inspiring

Show readers that others have succeeded with this approach."""

            elif section == "call_to_action":
                prompts[section] = f"""Write a compelling call-to-action for a blog post about "{topic}".

Requirements:
- Target length: {structure.recommended_lengths[section]} words
- Tone: {tone.value}
- Create urgency and motivation
- Be specific about the next step
- Make it easy to take action
- Use action-oriented language
- Create excitement and anticipation
- End with energy and momentum

Make readers excited to take the next step."""

        return prompts
    
    async def optimize_content_flow(
        self, 
        sections: Dict[str, str],
        structure: ContentStructure
    ) -> Dict[str, str]:
        """Optimize content flow for engagement."""
        optimized_sections = sections.copy()
        
        # Add emotional transitions between sections
        # Ensure emotional arc is maintained
        # Add engagement triggers throughout
        # Optimize for social sharing
        
        return optimized_sections
    
    def get_strategy_metadata(self) -> Dict[str, Any]:
        """Get engagement strategy metadata."""
        return {
            "strategy_type": "engagement_focused",
            "focus_areas": ["emotional_connection", "storytelling", "interaction"],
            "engagement_elements": ["hooks", "stories", "polls", "social_proof"],
            "content_flow": "emotional_journey",
            "optimization_level": "high"
        }
    
    def _get_target_word_count(self, length: ContentLength) -> int:
        """Get target word count based on content length."""
        targets = {
            ContentLength.SHORT: 600,
            ContentLength.MEDIUM: 1200,
            ContentLength.LONG: 2000,
            ContentLength.EXTENDED: 3000
        }
        return targets.get(length, 1200)


class ConversionContentStrategy(ContentGenerationStrategy):
    """Conversion-optimized content generation strategy."""
    
    async def generate_content_structure(
        self, 
        topic: str, 
        keywords: List[str],
        target_length: ContentLength
    ) -> ContentStructure:
        """Generate conversion-optimized content structure."""
        sections = [
            "problem_identification",
            "solution_presentation",
            "benefits_highlight",
            "objection_handling",
            "urgency_creation",
            "conversion_cta"
        ]
        
        section_descriptions = {
            "problem_identification": f"Clearly identify and amplify the problem that {topic} solves",
            "solution_presentation": f"Present {topic} as the ideal solution with clear value proposition",
            "benefits_highlight": f"Highlight specific benefits and outcomes of using {topic}",
            "objection_handling": f"Address common objections and concerns about {topic}",
            "urgency_creation": f"Create urgency and scarcity around {topic}",
            "conversion_cta": f"Strong conversion-focused call-to-action for {topic}"
        }
        
        total_words = self._get_target_word_count(target_length)
        section_lengths = {
            "problem_identification": int(total_words * 0.20),
            "solution_presentation": int(total_words * 0.25),
            "benefits_highlight": int(total_words * 0.25),
            "objection_handling": int(total_words * 0.15),
            "urgency_creation": int(total_words * 0.10),
            "conversion_cta": int(total_words * 0.05)
        }
        
        return ContentStructure(
            sections=sections,
            section_descriptions=section_descriptions,
            recommended_lengths=section_lengths,
            required_elements=["problem_solution", "benefits", "cta", "urgency"],
            optional_elements=["testimonials", "guarantees", "bonuses", "scarcity"]
        )
    
    async def create_section_prompts(
        self, 
        structure: ContentStructure,
        topic: str,
        keywords: List[str],
        tone: ContentTone,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """Create conversion-optimized prompts for each section."""
        prompts = {}
        
        for section in structure.sections:
            if section == "problem_identification":
                prompts[section] = f"""Write a problem identification section for a blog post about "{topic}".

Requirements:
- Target length: {structure.recommended_lengths[section]} words
- Tone: {tone.value}
- Clearly identify the problem your audience faces
- Make the problem feel urgent and painful
- Use specific examples and scenarios
- Connect with reader emotions
- Show the cost of not solving the problem
- Include keywords naturally: {', '.join(keywords[:3])}

Make readers feel the pain of the problem deeply."""

            elif section == "solution_presentation":
                prompts[section] = f"""Write a solution presentation section for a blog post about "{topic}".

Requirements:
- Target length: {structure.recommended_lengths[section]} words
- Tone: {tone.value}
- Present {topic} as the ideal solution
- Show how it directly addresses the problem
- Use clear, benefit-focused language
- Include specific features and capabilities
- Make it feel like the obvious choice
- Build confidence in the solution

Position the solution as the perfect answer to their problem."""

            elif section == "benefits_highlight":
                prompts[section] = f"""Write a benefits highlight section for a blog post about "{topic}".

Requirements:
- Target length: {structure.recommended_lengths[section]} words
- Tone: {tone.value}
- Focus on specific benefits and outcomes
- Use "you will" language
- Include quantifiable results when possible
- Show transformation and improvement
- Make benefits feel personal and relevant
- Use emotional and logical appeals

Make readers excited about the benefits they'll receive."""

            elif section == "objection_handling":
                prompts[section] = f"""Write an objection handling section for a blog post about "{topic}".

Requirements:
- Target length: {structure.recommended_lengths[section]} words
- Tone: {tone.value}
- Address common objections and concerns
- Provide reassuring answers
- Include guarantees or risk reversals
- Show social proof and testimonials
- Address cost, time, and effort concerns
- Build trust and credibility

Remove barriers and objections to taking action."""

            elif section == "urgency_creation":
                prompts[section] = f"""Write an urgency creation section for a blog post about "{topic}".

Requirements:
- Target length: {structure.recommended_lengths[section]} words
- Tone: {tone.value}
- Create legitimate urgency and scarcity
- Show limited time or availability
- Highlight what they'll miss if they don't act
- Use time-sensitive language
- Create FOMO (fear of missing out)
- Make action feel necessary now

Create compelling reasons to act immediately."""

            elif section == "conversion_cta":
                prompts[section] = f"""Write a conversion-focused call-to-action for a blog post about "{topic}".

Requirements:
- Target length: {structure.recommended_lengths[section]} words
- Tone: {tone.value}
- Clear, specific action to take
- Remove friction and barriers
- Create excitement and motivation
- Use action-oriented language
- Make it feel like the natural next step
- End with momentum and energy

Make taking action feel irresistible."""

        return prompts
    
    async def optimize_content_flow(
        self, 
        sections: Dict[str, str],
        structure: ContentStructure
    ) -> Dict[str, str]:
        """Optimize content flow for conversions."""
        optimized_sections = sections.copy()
        
        # Ensure logical progression from problem to solution
        # Add conversion triggers throughout
        # Optimize for decision-making psychology
        # Add trust-building elements
        
        return optimized_sections
    
    def get_strategy_metadata(self) -> Dict[str, Any]:
        """Get conversion strategy metadata."""
        return {
            "strategy_type": "conversion_optimized",
            "focus_areas": ["problem_solution", "benefits", "objection_handling"],
            "conversion_elements": ["cta", "urgency", "scarcity", "social_proof"],
            "content_flow": "persuasion_funnel",
            "optimization_level": "high"
        }
    
    def _get_target_word_count(self, length: ContentLength) -> int:
        """Get target word count based on content length."""
        targets = {
            ContentLength.SHORT: 700,
            ContentLength.MEDIUM: 1400,
            ContentLength.LONG: 2200,
            ContentLength.EXTENDED: 3500
        }
        return targets.get(length, 1400)


class StrategyFactory:
    """Factory for creating content generation strategies."""
    
    @staticmethod
    def create_strategy(strategy_type: ContentStrategy) -> ContentGenerationStrategy:
        """Create a content generation strategy."""
        strategies = {
            ContentStrategy.SEO_OPTIMIZED: SEOOptimizedStrategy(),
            ContentStrategy.ENGAGEMENT_FOCUSED: EngagementFocusedStrategy(),
            ContentStrategy.CONVERSION_OPTIMIZED: ConversionOptimizedStrategy(),
            ContentStrategy.EDUCATIONAL: SEOOptimizedStrategy(),  # Use SEO for educational
            ContentStrategy.PROMOTIONAL: ConversionOptimizedStrategy(),  # Use conversion for promotional
            ContentStrategy.TECHNICAL: SEOOptimizedStrategy(),  # Use SEO for technical
            ContentStrategy.CREATIVE: EngagementFocusedStrategy()  # Use engagement for creative
        }
        
        strategy = strategies.get(strategy_type)
        if not strategy:
            raise ValueError(f"Unknown strategy type: {strategy_type}")
        
        return strategy
