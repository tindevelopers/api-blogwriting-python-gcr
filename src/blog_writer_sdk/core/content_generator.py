"""
Content generation module for creating blog content.

This module handles the actual content creation logic, focusing on
structure, readability, and SEO-friendly content generation.
"""

import re
from typing import List, Optional
from ..models.blog_models import ContentTone


class ContentGenerator:
    """
    Handles content generation for blog posts.
    
    This class focuses on creating well-structured, readable content
    without relying on external AI services.
    """
    
    def __init__(self):
        """Initialize the content generator."""
        self.tone_templates = {
            ContentTone.PROFESSIONAL: {
                "intro_starters": [
                    "In today's rapidly evolving landscape,",
                    "Understanding the fundamentals of",
                    "As organizations continue to prioritize",
                    "The importance of {topic} cannot be overstated",
                ],
                "transition_phrases": [
                    "Furthermore,", "Additionally,", "Moreover,", "It's important to note that",
                    "Building on this concept,", "From a strategic perspective,",
                ],
                "conclusion_starters": [
                    "In conclusion,", "To summarize,", "Moving forward,",
                    "The key takeaway is that", "As we've explored,",
                ],
            },
            ContentTone.CASUAL: {
                "intro_starters": [
                    "Let's be honest,", "You've probably wondered about",
                    "Here's the thing about", "So, you want to know about",
                ],
                "transition_phrases": [
                    "Now,", "Here's where it gets interesting:", "But wait, there's more:",
                    "On the flip side,", "Let's dive deeper:",
                ],
                "conclusion_starters": [
                    "So there you have it!", "The bottom line?", "To wrap things up,",
                    "At the end of the day,", "Here's what it all comes down to:",
                ],
            },
            ContentTone.FRIENDLY: {
                "intro_starters": [
                    "Welcome! Today we're exploring",
                    "I'm excited to share with you",
                    "Have you ever wondered about",
                    "Let's take a friendly look at",
                ],
                "transition_phrases": [
                    "What's really great is that", "You'll love this part:",
                    "Here's something cool:", "I think you'll find that",
                ],
                "conclusion_starters": [
                    "I hope this has been helpful!", "Thanks for joining me on this journey through",
                    "I'd love to hear your thoughts on", "Feel free to reach out if",
                ],
            },
        }
    
    async def generate_introduction(
        self,
        topic: str,
        tone: ContentTone = ContentTone.PROFESSIONAL,
        keywords: Optional[List[str]] = None,
    ) -> str:
        """
        Generate an engaging introduction for the blog post.
        
        Args:
            topic: Main topic of the blog post
            tone: Writing tone to use
            keywords: Keywords to naturally incorporate
            
        Returns:
            Generated introduction text
        """
        templates = self.tone_templates.get(tone, self.tone_templates[ContentTone.PROFESSIONAL])
        starter = templates["intro_starters"][0].format(topic=topic)
        
        # Create introduction paragraphs
        intro_parts = [
            f"{starter} {topic} has become increasingly important in our modern world.",
            f"This comprehensive guide will explore the key aspects of {topic}, "
            f"providing you with practical insights and actionable strategies.",
        ]
        
        # Add keyword-focused sentence if keywords provided
        if keywords:
            keyword_sentence = self._create_keyword_sentence(keywords, topic, tone)
            intro_parts.append(keyword_sentence)
        
        # Add value proposition
        intro_parts.append(
            f"By the end of this article, you'll have a clear understanding of "
            f"how to effectively implement {topic} in your own context."
        )
        
        return "\n\n".join(intro_parts)
    
    async def generate_section(
        self,
        heading: str,
        topic: str,
        keyword_focus: Optional[str] = None,
        tone: ContentTone = ContentTone.PROFESSIONAL,
        target_words: int = 200,
    ) -> str:
        """
        Generate content for a specific section.
        
        Args:
            heading: Section heading
            topic: Main topic
            keyword_focus: Specific keyword to focus on
            tone: Writing tone
            target_words: Target word count for the section
            
        Returns:
            Generated section content
        """
        templates = self.tone_templates.get(tone, self.tone_templates[ContentTone.PROFESSIONAL])
        
        # Generate opening paragraph
        opening = self._generate_section_opening(heading, topic, keyword_focus, tone)
        
        # Generate main content paragraphs
        content_paragraphs = []
        
        # Add definition/explanation paragraph
        if keyword_focus:
            definition = self._generate_definition_paragraph(keyword_focus, topic, tone)
            content_paragraphs.append(definition)
        
        # Add benefits/importance paragraph
        benefits = self._generate_benefits_paragraph(heading, topic, tone)
        content_paragraphs.append(benefits)
        
        # Add practical examples/tips
        examples = self._generate_examples_paragraph(heading, topic, tone)
        content_paragraphs.append(examples)
        
        # Combine all parts
        section_content = [opening] + content_paragraphs
        full_content = "\n\n".join(section_content)
        
        # Adjust length if needed
        return self._adjust_content_length(full_content, target_words)
    
    async def generate_faq(
        self,
        topic: str,
        keywords: Optional[List[str]] = None,
    ) -> str:
        """
        Generate FAQ section content.
        
        Args:
            topic: Main topic
            keywords: Keywords to create questions around
            
        Returns:
            Generated FAQ content in markdown format
        """
        faq_items = []
        
        # Generate common questions
        common_questions = [
            f"What is {topic}?",
            f"How does {topic} work?",
            f"What are the benefits of {topic}?",
            f"How do I get started with {topic}?",
            f"What are the common challenges with {topic}?",
        ]
        
        # Add keyword-specific questions
        if keywords:
            for keyword in keywords[:3]:  # Limit to 3 keyword questions
                common_questions.append(f"How does {keyword} relate to {topic}?")
        
        # Generate answers for each question
        for question in common_questions[:6]:  # Limit to 6 total questions
            answer = self._generate_faq_answer(question, topic)
            faq_items.append(f"### {question}\n\n{answer}")
        
        return "\n\n".join(faq_items)
    
    async def generate_conclusion(
        self,
        topic: str,
        tone: ContentTone = ContentTone.PROFESSIONAL,
        key_points: Optional[List[str]] = None,
    ) -> str:
        """
        Generate a conclusion for the blog post.
        
        Args:
            topic: Main topic
            tone: Writing tone
            key_points: Key points to summarize
            
        Returns:
            Generated conclusion text
        """
        templates = self.tone_templates.get(tone, self.tone_templates[ContentTone.PROFESSIONAL])
        starter = templates["conclusion_starters"][0]
        
        conclusion_parts = [
            f"{starter} {topic} represents a significant opportunity for growth and improvement.",
        ]
        
        # Summarize key points if provided
        if key_points:
            summary = f"We've explored {', '.join(key_points[:-1])}"
            if len(key_points) > 1:
                summary += f", and {key_points[-1]}"
            summary += f" as they relate to {topic}."
            conclusion_parts.append(summary)
        
        # Add actionable next steps
        conclusion_parts.append(
            f"The next step is to begin implementing these strategies in your own context. "
            f"Start with the fundamentals and gradually build your expertise in {topic}."
        )
        
        # Add call to action based on tone
        if tone == ContentTone.FRIENDLY:
            conclusion_parts.append(
                "I'd love to hear about your experiences and any questions you might have!"
            )
        elif tone == ContentTone.PROFESSIONAL:
            conclusion_parts.append(
                "Consider how these insights can be applied to your specific situation and goals."
            )
        
        return "\n\n".join(conclusion_parts)
    
    async def generate_title(
        self,
        topic: str,
        content: str,
        keywords: Optional[List[str]] = None,
        focus_keyword: Optional[str] = None,
        tone: ContentTone = ContentTone.PROFESSIONAL,
    ) -> str:
        """
        Generate an SEO-optimized title.
        
        Args:
            topic: Main topic
            content: Generated content for context
            keywords: Available keywords
            focus_keyword: Primary keyword to include
            tone: Writing tone
            
        Returns:
            Generated title
        """
        # Use focus keyword if available, otherwise use topic
        primary_term = focus_keyword or topic
        
        # Title templates based on tone
        if tone == ContentTone.PROFESSIONAL:
            templates = [
                f"The Complete Guide to {primary_term}",
                f"Understanding {primary_term}: A Comprehensive Overview",
                f"Essential Strategies for {primary_term}",
                f"Mastering {primary_term}: Best Practices and Insights",
            ]
        elif tone == ContentTone.CASUAL:
            templates = [
                f"Everything You Need to Know About {primary_term}",
                f"The Ultimate {primary_term} Guide for Beginners",
                f"Why {primary_term} Matters (And How to Get Started)",
                f"Your Complete {primary_term} Handbook",
            ]
        else:  # FRIENDLY
            templates = [
                f"A Friendly Guide to {primary_term}",
                f"Getting Started with {primary_term}: A Beginner's Journey",
                f"Exploring {primary_term}: What You Need to Know",
                f"Your Introduction to {primary_term}",
            ]
        
        # Select the most appropriate template
        selected_title = templates[0]
        
        # Ensure title is within SEO limits (50-60 characters)
        if len(selected_title) > 60:
            selected_title = f"Complete Guide to {primary_term}"
        
        return selected_title
    
    def _create_keyword_sentence(
        self, keywords: List[str], topic: str, tone: ContentTone
    ) -> str:
        """Create a natural sentence incorporating keywords."""
        if not keywords:
            return ""
        
        if len(keywords) == 1:
            return f"We'll particularly focus on {keywords[0]} and its relationship to {topic}."
        elif len(keywords) == 2:
            return f"Key areas we'll cover include {keywords[0]} and {keywords[1]}."
        else:
            keyword_list = ", ".join(keywords[:-1]) + f", and {keywords[-1]}"
            return f"This includes exploring {keyword_list} in detail."
    
    def _generate_section_opening(
        self, heading: str, topic: str, keyword_focus: Optional[str], tone: ContentTone
    ) -> str:
        """Generate opening paragraph for a section."""
        if keyword_focus:
            return (
                f"When it comes to {topic}, {keyword_focus} plays a crucial role. "
                f"Understanding this concept is essential for anyone looking to "
                f"make the most of their {topic} strategy."
            )
        else:
            clean_heading = heading.replace("Understanding ", "").replace("Key Aspects of ", "")
            return (
                f"{clean_heading} represents a fundamental aspect of {topic}. "
                f"Let's explore why this matters and how you can apply these concepts effectively."
            )
    
    def _generate_definition_paragraph(
        self, keyword: str, topic: str, tone: ContentTone
    ) -> str:
        """Generate a definition/explanation paragraph."""
        return (
            f"{keyword.title()} refers to the specific approaches and methodologies "
            f"used within the context of {topic}. This encompasses both theoretical "
            f"understanding and practical application, making it a cornerstone of "
            f"effective {topic} implementation."
        )
    
    def _generate_benefits_paragraph(
        self, heading: str, topic: str, tone: ContentTone
    ) -> str:
        """Generate benefits/importance paragraph."""
        return (
            f"The benefits of properly implementing this aspect of {topic} are significant. "
            f"Organizations and individuals who focus on these elements typically see "
            f"improved outcomes, better efficiency, and more sustainable results over time."
        )
    
    def _generate_examples_paragraph(
        self, heading: str, topic: str, tone: ContentTone
    ) -> str:
        """Generate examples/tips paragraph."""
        return (
            f"In practice, this means focusing on clear objectives, consistent execution, "
            f"and regular evaluation of your {topic} efforts. Consider starting with "
            f"small, manageable steps and gradually expanding your approach as you "
            f"gain experience and confidence."
        )
    
    def _generate_faq_answer(self, question: str, topic: str) -> str:
        """Generate answer for FAQ question."""
        if "What is" in question:
            return (
                f"{topic} is a comprehensive approach that involves multiple strategies "
                f"and considerations. It encompasses both foundational principles and "
                f"advanced techniques designed to achieve optimal results."
            )
        elif "How does" in question and "work" in question:
            return (
                f"The process typically involves several key steps: planning, implementation, "
                f"monitoring, and optimization. Each phase builds upon the previous one to "
                f"create a cohesive and effective approach."
            )
        elif "benefits" in question.lower():
            return (
                f"The primary benefits include improved efficiency, better outcomes, "
                f"reduced costs, and enhanced long-term sustainability. Many users also "
                f"report increased satisfaction and confidence in their approach."
            )
        elif "get started" in question.lower():
            return (
                f"Begin by understanding the fundamentals and assessing your current situation. "
                f"Then, develop a clear plan with specific goals and timelines. Start with "
                f"small steps and gradually expand your efforts as you gain experience."
            )
        elif "challenges" in question.lower():
            return (
                f"Common challenges include initial complexity, resource requirements, "
                f"and the need for consistent effort. However, these can be overcome with "
                f"proper planning, patience, and a willingness to learn and adapt."
            )
        else:
            return (
                f"This is an important consideration in {topic}. The key is to maintain "
                f"focus on your objectives while remaining flexible in your approach. "
                f"Regular evaluation and adjustment help ensure continued success."
            )
    
    def _adjust_content_length(self, content: str, target_words: int) -> str:
        """Adjust content length to approximate target word count."""
        current_words = len(content.split())
        
        if current_words < target_words * 0.8:  # Too short
            # Add additional explanatory content
            additional = (
                "\n\nIt's worth noting that successful implementation requires careful "
                "attention to detail and a commitment to continuous improvement. "
                "Regular monitoring and adjustment of your approach will help ensure "
                "that you achieve the best possible results over time."
            )
            content += additional
        
        return content
