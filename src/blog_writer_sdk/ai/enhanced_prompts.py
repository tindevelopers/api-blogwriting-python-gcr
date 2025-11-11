"""
Enhanced Prompt Templates for High-Quality Blog Content Generation

This module provides domain-specific prompt templates that guide LLMs
to produce higher-quality, more authoritative content.
"""

from typing import Dict, List, Optional, Any
from enum import Enum
from ..models.blog_models import ContentTone, ContentLength


class PromptTemplate(str, Enum):
    """Available prompt template types."""
    EXPERT_AUTHORITY = "expert_authority"
    HOW_TO_GUIDE = "how_to_guide"
    COMPARISON = "comparison"
    CASE_STUDY = "case_study"
    NEWS_UPDATE = "news_update"
    TUTORIAL = "tutorial"
    LISTICLE = "listicle"
    REVIEW = "review"


class EnhancedPromptBuilder:
    """Builder for enhanced, domain-specific prompts."""
    
    @staticmethod
    def build_research_prompt(
        topic: str,
        keywords: List[str],
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Build prompt for research and outline generation (Stage 1).
        Optimized for Claude 3.5 Sonnet's reasoning capabilities.
        """
        primary_keyword = keywords[0] if keywords else topic.lower()
        related_keywords = ", ".join(keywords[1:6]) if len(keywords) > 1 else ""
        
        prompt = f"""You are an expert content researcher and strategist. Your task is to conduct comprehensive research and create a detailed outline for a high-quality blog post.

TOPIC: {topic}
PRIMARY KEYWORD: {primary_keyword}
RELATED KEYWORDS: {related_keywords}

RESEARCH REQUIREMENTS:
1. Identify the core questions readers have about this topic
2. Determine what information is missing from existing top-ranking content
3. Find unique angles or insights that haven't been covered extensively
4. Identify authoritative sources and recent data points
5. Analyze what makes top-ranking content successful for this topic

OUTLINE REQUIREMENTS:
1. Create a comprehensive outline with 5-7 main sections
2. Each section should address a specific aspect or question
3. Include subsections with specific points to cover
4. Prioritize sections by importance and search intent
5. Identify content gaps and opportunities for unique value
6. Suggest specific examples, case studies, or data points for each section

OUTPUT FORMAT:
Provide a structured outline with:
- Section titles (H2 headings)
- Subsection points (H3 headings)
- Key points to cover in each section
- Suggested examples or data points
- Estimated word count per section

Focus on creating content that provides genuine value, unique insights, and actionable information. Prioritize depth and authority over surface-level coverage."""
        
        if context:
            if context.get("search_intent"):
                prompt += f"\n\nSEARCH INTENT: {context['search_intent']}"
            if context.get("target_audience"):
                prompt += f"\nTARGET AUDIENCE: {context['target_audience']}"
            if context.get("competitor_analysis"):
                prompt += f"\n\nCOMPETITOR INSIGHTS:\n{context['competitor_analysis']}"
        
        return prompt
    
    @staticmethod
    def build_draft_prompt(
        topic: str,
        outline: str,
        keywords: List[str],
        tone: ContentTone,
        length: ContentLength,
        template: Optional[PromptTemplate] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Build prompt for draft generation (Stage 2).
        Optimized for GPT-4o's comprehensive generation capabilities.
        """
        primary_keyword = keywords[0] if keywords else topic.lower()
        word_count_target = EnhancedPromptBuilder._get_word_count(length)
        
        # Select template-specific instructions
        template_instructions = EnhancedPromptBuilder._get_template_instructions(
            template or PromptTemplate.EXPERT_AUTHORITY,
            topic,
            keywords
        )
        
        prompt = f"""You are an expert content writer specializing in creating high-quality, authoritative blog posts that rank well in search engines and provide genuine value to readers.

TOPIC: {topic}
PRIMARY KEYWORD: {primary_keyword}
TONE: {tone.value}
TARGET LENGTH: {word_count_target} words

CONTENT OUTLINE:
{outline}

{template_instructions}

WRITING REQUIREMENTS:
1. Write for human readers first, SEO optimization second
2. Use the primary keyword naturally throughout (aim for 1-2% density)
3. Integrate related keywords naturally without keyword stuffing
4. Write in a {tone.value} tone that matches the target audience
5. Provide specific examples, data points, and actionable insights
6. Use clear, scannable formatting with proper headings (H2, H3)
7. Keep paragraphs to 3-4 sentences maximum
8. Use bullet points and numbered lists where appropriate
9. Include natural transitions between sections
10. End each section with a clear takeaway or summary point

CONTENT QUALITY STANDARDS:
- Provide unique insights, not just rehashed information
- Include specific examples, case studies, or real-world applications
- Cite sources naturally within the content
- Use active voice and clear, concise language
- Ensure factual accuracy and avoid speculation
- Create content that demonstrates expertise and authority

STRUCTURE REQUIREMENTS:
- Start with a compelling introduction that hooks the reader
- Use proper heading hierarchy (H1 for title, H2 for main sections, H3 for subsections)
- Include at least one list (bulleted or numbered) per main section
- Add internal linking opportunities naturally
- End with a strong conclusion that summarizes key points

Generate comprehensive, well-researched content that readers will find valuable and search engines will recognize as authoritative."""
        
        if context:
            if context.get("sources"):
                prompt += f"\n\nAVAILABLE SOURCES:\n{chr(10).join(f'- {s}' for s in context['sources'][:5])}"
            if context.get("recent_info"):
                prompt += f"\n\nRECENT INFORMATION TO INCLUDE:\n{context['recent_info']}"
            if context.get("serp_features"):
                prompt += f"\n\nTARGET SERP FEATURES:\n{chr(10).join(f'- {f}' for f in context['serp_features'])}"
        
        return prompt
    
    @staticmethod
    def build_enhancement_prompt(
        draft_content: str,
        topic: str,
        keywords: List[str],
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Build prompt for content enhancement (Stage 3).
        Optimized for Claude 3.5 Sonnet's refinement capabilities.
        """
        primary_keyword = keywords[0] if keywords else topic.lower()
        
        prompt = f"""You are an expert content editor specializing in enhancing blog posts for maximum quality, readability, and SEO performance.

TOPIC: {topic}
PRIMARY KEYWORD: {primary_keyword}

CURRENT DRAFT:
{draft_content[:3000]}...

ENHANCEMENT TASKS:
1. Improve readability and flow - ensure smooth transitions between paragraphs and sections
2. Enhance clarity - simplify complex concepts without dumbing down
3. Add natural keyword integration - ensure primary keyword appears naturally (1-2% density)
4. Strengthen examples - replace generic examples with specific, concrete ones
5. Improve structure - optimize heading hierarchy and paragraph length
6. Add value - identify areas where more depth or unique insights can be added
7. Fact-check - verify any factual claims and suggest corrections if needed
8. Enhance engagement - add rhetorical questions, compelling statements, or thought-provoking points
9. Optimize for featured snippets - ensure key sections can serve as featured snippet answers
10. Improve conclusion - make it more actionable and memorable

OUTPUT REQUIREMENTS:
- Return the enhanced version of the content
- Maintain the original structure and length
- Preserve all factual information
- Improve without changing the core message
- Add citations or source references where appropriate
- Ensure the content reads naturally and flows well

Focus on making the content more authoritative, engaging, and valuable while maintaining accuracy and readability."""
        
        if context:
            if context.get("readability_issues"):
                prompt += f"\n\nREADABILITY ISSUES TO ADDRESS:\n{chr(10).join(f'- {issue}' for issue in context['readability_issues'])}"
            if context.get("fact_check_results"):
                prompt += f"\n\nFACT-CHECK RESULTS:\n{context['fact_check_results']}"
        
        return prompt
    
    @staticmethod
    def build_seo_polish_prompt(
        content: str,
        topic: str,
        keywords: List[str],
        meta_requirements: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Build prompt for SEO polish (Stage 4).
        Optimized for GPT-4o-mini's efficient optimization capabilities.
        """
        primary_keyword = keywords[0] if keywords else topic.lower()
        
        prompt = f"""You are an SEO specialist optimizing blog content for maximum search engine visibility while maintaining quality and readability.

TOPIC: {topic}
PRIMARY KEYWORD: {primary_keyword}

CONTENT TO OPTIMIZE:
{content[:2000]}...

SEO OPTIMIZATION TASKS:
1. Meta Title Generation - Create an SEO-optimized title (50-60 characters) that includes the primary keyword
2. Meta Description - Write a compelling meta description (150-160 characters) with primary keyword and call-to-action
3. Heading Optimization - Ensure H1, H2, and H3 headings include relevant keywords naturally
4. Keyword Density Check - Verify primary keyword appears 1-2% of the time, related keywords integrated naturally
5. Internal Linking - Suggest 3-5 internal linking opportunities with anchor text
6. Image Alt Text Suggestions - Recommend alt text for potential images
7. Schema Markup Suggestions - Identify opportunities for structured data (FAQ, HowTo, Article)
8. Featured Snippet Optimization - Ensure key sections can serve as featured snippet answers
9. Readability Check - Verify content is scannable with proper formatting
10. URL Slug Suggestion - Create an SEO-friendly URL slug

OUTPUT FORMAT:
Provide:
1. Optimized meta title
2. Meta description
3. List of internal linking suggestions (with anchor text and target topics)
4. Image alt text suggestions (3-5 suggestions)
5. Schema markup recommendations
6. URL slug suggestion
7. Any content adjustments needed for SEO (minimal changes only)

Focus on SEO optimization that enhances rather than detracts from content quality."""
        
        if meta_requirements:
            if meta_requirements.get("title_length"):
                prompt += f"\n\nTITLE LENGTH REQUIREMENT: {meta_requirements['title_length']} characters"
            if meta_requirements.get("description_length"):
                prompt += f"\nDESCRIPTION LENGTH REQUIREMENT: {meta_requirements['description_length']} characters"
        
        return prompt
    
    @staticmethod
    def _get_template_instructions(
        template: PromptTemplate,
        topic: str,
        keywords: List[str]
    ) -> str:
        """Get template-specific instructions."""
        primary_keyword = keywords[0] if keywords else topic.lower()
        
        templates = {
            PromptTemplate.EXPERT_AUTHORITY: f"""
EXPERT AUTHORITY TEMPLATE:
- Position yourself as a domain expert with deep knowledge
- Provide insights that demonstrate expertise and authority
- Include data-driven analysis and evidence-based conclusions
- Use professional terminology appropriately
- Reference industry standards, best practices, or research
- Offer unique perspectives that go beyond surface-level information""",
            
            PromptTemplate.HOW_TO_GUIDE: f"""
HOW-TO GUIDE TEMPLATE:
- Provide clear, step-by-step instructions
- Include prerequisites or requirements upfront
- Break complex processes into manageable steps
- Add troubleshooting tips and common pitfalls
- Include visual descriptions or examples for each step
- End with a summary checklist of key steps
- Use action-oriented language and imperative mood""",
            
            PromptTemplate.COMPARISON: f"""
COMPARISON TEMPLATE:
- Create a structured comparison format
- Use clear criteria for comparison
- Present pros and cons objectively
- Include specific examples for each option
- Provide a recommendation based on use cases
- Use tables or lists for easy comparison
- Address common misconceptions""",
            
            PromptTemplate.CASE_STUDY: f"""
CASE STUDY TEMPLATE:
- Start with context and background
- Describe the challenge or problem
- Explain the solution or approach
- Present results and outcomes with data
- Extract key lessons and takeaways
- Provide actionable insights readers can apply
- Use real-world examples and specific details""",
            
            PromptTemplate.NEWS_UPDATE: f"""
NEWS/UPDATE TEMPLATE:
- Lead with the most important information
- Provide context and background
- Explain implications and significance
- Include expert opinions or quotes
- Reference recent developments or data
- Add analysis of what this means for readers
- Include relevant dates and timestamps""",
            
            PromptTemplate.TUTORIAL: f"""
TUTORIAL TEMPLATE:
- Start with learning objectives
- Provide prerequisite knowledge requirements
- Break content into logical learning modules
- Include practice exercises or examples
- Add progress checkpoints
- Summarize key concepts at the end
- Provide next steps or advanced topics""",
            
            PromptTemplate.LISTICLE: f"""
LISTICLE TEMPLATE:
- Use numbered or bulleted list format
- Each item should be substantial (not just a sentence)
- Include explanations and context for each item
- Add images or visual descriptions
- Use engaging, descriptive headings for each item
- Maintain consistent format throughout
- End with a summary or conclusion""",
            
            PromptTemplate.REVIEW: f"""
REVIEW TEMPLATE:
- Provide comprehensive evaluation criteria
- Test or evaluate multiple aspects
- Include pros and cons
- Add real-world usage examples
- Provide rating or scoring system
- Compare with alternatives
- Give clear recommendation with reasoning"""
        }
        
        return templates.get(template, templates[PromptTemplate.EXPERT_AUTHORITY])
    
    @staticmethod
    def _get_word_count(length: ContentLength) -> int:
        """Get target word count for content length."""
        word_counts = {
            ContentLength.SHORT: 800,
            ContentLength.MEDIUM: 1500,
            ContentLength.LONG: 2500,
            ContentLength.VERY_LONG: 4000
        }
        return word_counts.get(length, 1500)

