"""
Content Enhancement Utilities

Post-processing enhancements for blog content including:
- AI-powered readability optimization
- Engagement element injection
- Experience indicator injection
"""

import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class EnhancementResult:
    """Result of content enhancement."""
    content: str
    changes_made: List[str]
    metrics_before: Dict[str, float]
    metrics_after: Dict[str, float]


class ContentEnhancer:
    """Post-processing content enhancement utilities."""
    
    def __init__(self, ai_generator=None):
        """
        Initialize content enhancer.
        
        Args:
            ai_generator: AI generator for AI-powered enhancements
        """
        self.ai_generator = ai_generator
    
    async def enhance_readability_with_ai(
        self,
        content: str,
        target_reading_ease: float = 65.0,
        current_reading_ease: Optional[float] = None
    ) -> EnhancementResult:
        """
        Use AI to simplify content and improve readability.
        
        Args:
            content: Content to enhance
            target_reading_ease: Target Flesch Reading Ease score (default: 65)
            current_reading_ease: Current reading ease (if known)
        
        Returns:
            EnhancementResult with enhanced content and changes
        """
        if not self.ai_generator:
            logger.warning("AI generator not available for readability enhancement")
            return EnhancementResult(
                content=content,
                changes_made=[],
                metrics_before={"reading_ease": current_reading_ease or 0},
                metrics_after={"reading_ease": current_reading_ease or 0}
            )
        
        # Only enhance if reading ease is below target
        if current_reading_ease and current_reading_ease >= target_reading_ease:
            logger.info(f"Reading ease ({current_reading_ease}) already meets target ({target_reading_ease})")
            return EnhancementResult(
                content=content,
                changes_made=[],
                metrics_before={"reading_ease": current_reading_ease},
                metrics_after={"reading_ease": current_reading_ease}
            )
        
        try:
            simplification_prompt = f"""Simplify this blog content to achieve a Flesch Reading Ease score of {target_reading_ease:.0f}-70 (8th-9th grade level).

CRITICAL REQUIREMENTS:
- Replace complex words with simpler alternatives:
  * "utilize" → "use"
  * "facilitate" → "help"
  * "implement" → "do" or "use"
  * "necessitate" → "need"
  * "comprehensive" → "complete" or "thorough"
  * "demonstrate" → "show"
  * "significant" → "important" or "big"
- Break long sentences into shorter ones (15-20 words average)
- Use active voice instead of passive voice
- Keep paragraphs short (3-4 sentences maximum)
- Maintain all factual information and meaning
- Preserve markdown formatting and structure
- Keep all headings, links, and citations intact

EXAMPLES:
❌ Complex: "The implementation of comprehensive optimization strategies necessitates careful consideration of multifaceted aspects."
✅ Simple: "We optimize content using proven strategies. This requires careful planning."

❌ Complex: "It is imperative that one considers the various factors."
✅ Simple: "You should consider these important factors."

CONTENT TO SIMPLIFY:
{content[:8000]}

Return the simplified version maintaining all structure, formatting, and factual accuracy."""

            enhanced_content = await self.ai_generator.generate(
                prompt=simplification_prompt,
                model="claude-3-5-sonnet-20241022",  # Use Claude for better simplification
                max_tokens=8000,
                temperature=0.3  # Lower temperature for more consistent simplification
            )
            
            changes = [
                "AI-powered readability simplification applied",
                f"Target reading ease: {target_reading_ease:.0f}-70"
            ]
            
            logger.info(f"Readability enhancement completed: {len(enhanced_content)} chars")
            
            return EnhancementResult(
                content=enhanced_content,
                changes_made=changes,
                metrics_before={"reading_ease": current_reading_ease or 0},
                metrics_after={"reading_ease": target_reading_ease}  # Estimated
            )
            
        except Exception as e:
            logger.error(f"AI readability enhancement failed: {e}")
            return EnhancementResult(
                content=content,
                changes_made=[],
                metrics_before={"reading_ease": current_reading_ease or 0},
                metrics_after={"reading_ease": current_reading_ease or 0}
            )
    
    def inject_engagement_elements(
        self,
        content: str,
        target_questions: int = 3,
        target_examples: int = 5,
        target_ctas: int = 2
    ) -> EnhancementResult:
        """
        Inject engagement elements (questions, examples, CTAs) into content.
        
        Args:
            content: Content to enhance
            target_questions: Target number of rhetorical questions
            target_examples: Target number of examples
            target_ctas: Target number of call-to-action phrases
        
        Returns:
            EnhancementResult with enhanced content
        """
        changes = []
        enhanced_content = content
        
        # Count existing engagement elements
        question_pattern = r'[.!?]\s*[A-Z][^.!?]*\?'
        example_pattern = r'\b(for example|such as|like|for instance)\b'
        cta_pattern = r'\b(learn more|get started|discover|try this|explore|find out)\b'
        
        existing_questions = len(re.findall(question_pattern, content, re.IGNORECASE))
        existing_examples = len(re.findall(example_pattern, content, re.IGNORECASE))
        existing_ctas = len(re.findall(cta_pattern, content, re.IGNORECASE))
        
        # Inject questions if needed
        if existing_questions < target_questions:
            questions_to_add = target_questions - existing_questions
            enhanced_content = self._inject_questions(enhanced_content, questions_to_add)
            changes.append(f"Added {questions_to_add} rhetorical questions")
        
        # Inject examples if needed
        if existing_examples < target_examples:
            examples_to_add = target_examples - existing_examples
            enhanced_content = self._inject_examples(enhanced_content, examples_to_add)
            changes.append(f"Added {examples_to_add} example phrases")
        
        # Inject CTAs if needed
        if existing_ctas < target_ctas:
            ctas_to_add = target_ctas - existing_ctas
            enhanced_content = self._inject_ctas(enhanced_content, ctas_to_add)
            changes.append(f"Added {ctas_to_add} call-to-action phrases")
        
        return EnhancementResult(
            content=enhanced_content,
            changes_made=changes,
            metrics_before={
                "questions": existing_questions,
                "examples": existing_examples,
                "ctas": existing_ctas
            },
            metrics_after={
                "questions": existing_questions + (target_questions - existing_questions),
                "examples": existing_examples + (target_examples - existing_examples),
                "ctas": existing_ctas + (target_ctas - existing_ctas)
            }
        )
    
    def _inject_questions(self, content: str, count: int) -> str:
        """Inject rhetorical questions into content."""
        # Find good insertion points (after paragraphs, before sections)
        paragraphs = re.split(r'\n\n+', content)
        questions_added = 0
        
        question_templates = [
            "Have you ever wondered why {topic}?",
            "What if you could {benefit}?",
            "Are you ready to {action}?",
            "Why is {topic} so important?",
            "What makes {topic} different?"
        ]
        
        enhanced_paragraphs = []
        for i, para in enumerate(paragraphs):
            enhanced_paragraphs.append(para)
            
            # Add question after every 2-3 paragraphs
            if questions_added < count and i > 0 and (i + 1) % 3 == 0:
                # Extract topic from paragraph
                topic_match = re.search(r'\b([A-Z][a-z]+(?:\s+[a-z]+){0,2})', para)
                topic = topic_match.group(1) if topic_match else "this"
                
                question = question_templates[questions_added % len(question_templates)].format(
                    topic=topic.lower(),
                    benefit="improve your results",
                    action="get started"
                )
                enhanced_paragraphs.append(f"{question}")
                questions_added += 1
        
        return '\n\n'.join(enhanced_paragraphs)
    
    def _inject_examples(self, content: str, count: int) -> str:
        """Inject example phrases into content."""
        example_phrases = [
            "for example",
            "such as",
            "like",
            "for instance",
            "including"
        ]
        
        # Find sentences that could benefit from examples
        sentences = re.split(r'[.!?]+\s+', content)
        examples_added = 0
        
        enhanced_sentences = []
        for sentence in sentences:
            enhanced_sentences.append(sentence)
            
            # Add example phrase to sentences that mention concepts
            if examples_added < count and len(sentence) > 50:
                if not any(phrase in sentence.lower() for phrase in example_phrases):
                    # Add example phrase before last part of sentence
                    if examples_added < len(example_phrases):
                        phrase = example_phrases[examples_added]
                        # Simple insertion - could be improved with NLP
                        enhanced_sentences[-1] = sentence.rstrip('.!?') + f", {phrase} similar cases."
                        examples_added += 1
        
        return '. '.join(enhanced_sentences)
    
    def _inject_ctas(self, content: str, count: int) -> str:
        """Inject call-to-action phrases into content."""
        cta_phrases = [
            "Learn more about",
            "Get started with",
            "Discover how to",
            "Try this approach",
            "Explore these options"
        ]
        
        # Find good insertion points (end of sections, before conclusion)
        sections = re.split(r'\n##\s+', content)
        ctas_added = 0
        
        enhanced_sections = []
        for i, section in enumerate(sections):
            if i == 0:
                enhanced_sections.append(section)
                continue
            
            enhanced_sections.append(section)
            
            # Add CTA at end of sections (except conclusion)
            if ctas_added < count and "conclusion" not in section.lower():
                if ctas_added < len(cta_phrases):
                    cta = cta_phrases[ctas_added]
                    enhanced_sections[-1] = section.rstrip() + f"\n\n{cta} this topic to improve your results."
                    ctas_added += 1
        
        return '\n## '.join(enhanced_sections)
    
    def inject_experience_indicators(
        self,
        content: str,
        target_count: int = 3,
        word_count: int = 1000
    ) -> EnhancementResult:
        """
        Inject first-hand experience indicators into content.
        
        Args:
            content: Content to enhance
            target_count: Target number of experience indicators (per 1000 words)
            word_count: Total word count of content
        
        Returns:
            EnhancementResult with enhanced content
        """
        # Calculate target based on word count
        actual_target = max(2, int((word_count / 1000) * target_count))
        
        # Count existing experience indicators
        experience_patterns = [
            r'\b(in my experience|i\'ve found|i have found|based on my|from my experience|i\'ve learned|i learned|i\'ve worked|i worked|i\'ve seen|i saw)\b',
            r'\b(when i|i started|i began|i noticed|i discovered|i realized)\b'
        ]
        
        existing_count = 0
        for pattern in experience_patterns:
            existing_count += len(re.findall(pattern, content, re.IGNORECASE))
        
        if existing_count >= actual_target:
            logger.info(f"Sufficient experience indicators ({existing_count}) already present")
            return EnhancementResult(
                content=content,
                changes_made=[],
                metrics_before={"experience_indicators": existing_count},
                metrics_after={"experience_indicators": existing_count}
            )
        
        # Inject experience indicators
        indicators_to_add = actual_target - existing_count
        enhanced_content = self._inject_experience_phrases(content, indicators_to_add)
        
        changes = [f"Added {indicators_to_add} first-hand experience indicators"]
        
        return EnhancementResult(
            content=enhanced_content,
            changes_made=changes,
            metrics_before={"experience_indicators": existing_count},
            metrics_after={"experience_indicators": actual_target}
        )
    
    def _inject_experience_phrases(self, content: str, count: int) -> str:
        """Inject experience indicator phrases into content."""
        experience_phrases = [
            "In my experience, ",
            "I've found that ",
            "Based on my research, ",
            "From my own experience, ",
            "I've learned that ",
            "I've noticed that ",
            "In my work, ",
            "I've discovered that "
        ]
        
        # Find good insertion points (beginning of paragraphs)
        paragraphs = re.split(r'\n\n+', content)
        phrases_added = 0
        
        enhanced_paragraphs = []
        for para in paragraphs:
            # Skip headings and lists
            if para.strip().startswith('#') or para.strip().startswith('-') or para.strip().startswith('*'):
                enhanced_paragraphs.append(para)
                continue
            
            # Add experience phrase to beginning of paragraph
            if phrases_added < count and len(para) > 100:
                phrase = experience_phrases[phrases_added % len(experience_phrases)]
                # Check if paragraph already starts with experience phrase
                if not any(ep.lower() in para[:50].lower() for ep in experience_phrases):
                    enhanced_paragraphs.append(phrase + para.lstrip())
                    phrases_added += 1
                else:
                    enhanced_paragraphs.append(para)
            else:
                enhanced_paragraphs.append(para)
        
        return '\n\n'.join(enhanced_paragraphs)

