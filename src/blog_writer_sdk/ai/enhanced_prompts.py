"""
Enhanced Prompt Templates for High-Quality Blog Content Generation

This module provides domain-specific prompt templates that guide LLMs
to produce higher-quality, more authoritative content.
"""

from typing import Dict, List, Optional, Any, Union
from enum import Enum
from ..models.blog_models import ContentTone, ContentLength


def _safe_enum_to_str(value) -> str:
    """
    Safely convert an enum or string to a string value.
    
    Args:
        value: Either an Enum instance or a string
        
    Returns:
        String representation of the value
    """
    if isinstance(value, Enum):
        return value.value
    elif isinstance(value, str):
        return value
    else:
        # Try to get .value attribute, fallback to str()
        try:
            return value.value
        except AttributeError:
            return str(value)


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
            if context.get("gsc_opportunities"):
                opportunities = context['gsc_opportunities']
                prompt += f"\n\nGOOGLE SEARCH CONSOLE - CONTENT OPPORTUNITIES:\n"
                prompt += "These keywords have high impressions but low CTR (opportunity to improve):\n"
                for opp in opportunities[:5]:
                    keyword = opp.get('keyword', '')
                    impressions = opp.get('impressions', 0)
                    position = opp.get('position', 0)
                    ctr = opp.get('ctr', 0)
                    prompt += f"- '{keyword}': {impressions} impressions, position {position:.1f}, CTR {ctr:.2%}\n"
                prompt += "\nConsider optimizing content to target these high-opportunity keywords."
            if context.get("gsc_content_gaps"):
                gaps = context['gsc_content_gaps']
                gap_list = gaps.get('gaps', [])
                if gap_list:
                    prompt += f"\n\nGOOGLE SEARCH CONSOLE - CONTENT GAPS:\n"
                    prompt += "These target keywords are not ranking or ranking low:\n"
                    for gap in gap_list[:5]:
                        keyword = gap.get('keyword', '')
                        status = gap.get('status', '')
                        recommendation = gap.get('recommendation', '')
                        prompt += f"- '{keyword}': {status} - {recommendation}\n"
                    prompt += "\nFocus on creating content that addresses these gaps."
            if context.get("brand_recommendations"):
                brand_data = context['brand_recommendations']
                brands_list = ", ".join(brand_data.get("brands", [])[:10])
                prompt += f"\n\nPRODUCT BRAND RECOMMENDATIONS:\nThe following brands/models are frequently mentioned in top-ranking content:\n{brands_list}\n\nIMPORTANT: Include specific brand recommendations and comparisons in your outline. Create sections that compare different brands, highlight top-rated products, and provide detailed brand-specific information. Include pros/cons for each major brand."
        
            # Priority 1: AI Citation Pattern Optimization
            if context.get("citation_patterns"):
                citation_patterns = context['citation_patterns']
                prompt += "\n\nAI CITATION PATTERN ANALYSIS (CRITICAL FOR AI SEARCH OPTIMIZATION):"
                prompt += "\nThe following content structures are frequently cited by AI agents (ChatGPT, Claude, Gemini, Perplexity):"
                
                top_pages = citation_patterns.get("top_cited_pages", [])
                if top_pages:
                    prompt += f"\n\nTop-Cited Pages (Study these patterns):"
                    for i, page in enumerate(top_pages[:5], 1):
                        title = page.get("title", "")
                        domain = page.get("domain", "")
                        mentions = page.get("mentions", 0)
                        prompt += f"\n{i}. {title} ({domain}) - Cited {mentions} times by AI agents"
                
                common_domains = citation_patterns.get("common_domains", [])
                if common_domains:
                    prompt += f"\n\nMost-Cited Domains (Prioritize similar structure):"
                    for domain, count in common_domains[:5]:
                        prompt += f"\n- {domain} (cited {count} times)"
                
                structure_insights = citation_patterns.get("content_structure_insights", [])
                if structure_insights:
                    prompt += f"\n\nContent Structure Patterns Found in Top-Cited Pages:"
                    for insight in structure_insights:
                        prompt += f"\n- {insight}"
                
                prompt += "\n\nCRITICAL INSTRUCTIONS:"
                prompt += "\n1. Match the content structure of top-cited pages"
                prompt += "\n2. Use question-based headings if top-cited pages use them"
                prompt += "\n3. Add concise summaries after each section (AI agents cite summaries)"
                prompt += "\n4. Use modular, scannable format (easy for AI to extract)"
                prompt += "\n5. Include structured data elements (FAQ, HowTo schemas)"
            
            # Priority 3: LLM Response Insights
            if context.get("llm_responses"):
                llm_responses = context['llm_responses']
                extracted_points = llm_responses.get("extracted_key_points", [])
                if extracted_points:
                    prompt += "\n\nAI AGENT RESEARCH INSIGHTS (From ChatGPT & Claude):"
                    prompt += "\nThe following key points were identified by querying AI agents about this topic:"
                    for point in extracted_points[:10]:
                        prompt += f"\n- {point}"
                    prompt += "\n\nIMPORTANT: Incorporate these insights into your outline. Match how AI agents structure their responses to this topic."
        
        return prompt
    
    @staticmethod
    def build_draft_prompt(
        topic: str,
        outline: str,
        keywords: List[str],
        tone: Union[ContentTone, str],
        length: Union[ContentLength, str],
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
        
        # Add freshness signals
        from datetime import datetime
        current_year = datetime.now().year
        current_date = datetime.now().strftime("%B %Y")
        
        prompt = f"""You are an expert content writer specializing in creating high-quality, authoritative blog posts that rank well in search engines and provide genuine value to readers.

TOPIC: {topic}
PRIMARY KEYWORD: {primary_keyword}
TONE: {_safe_enum_to_str(tone)}
TARGET LENGTH: {word_count_target} words (MANDATORY - content must reach this word count)
CURRENT DATE: {current_date}
CURRENT YEAR: {current_year}

CONTENT OUTLINE:
{outline}

{template_instructions}

CRITICAL LENGTH REQUIREMENT:
- You MUST generate at least {word_count_target} words of content
- This is a hard requirement, not a suggestion
- If your initial draft is shorter, expand sections with more detail, examples, and explanations
- Each H2 section should contribute 400-600 words toward the total
- Do not stop writing until you reach the target word count

WRITING REQUIREMENTS:
1. Write for human readers first, SEO optimization second
2. Use the primary keyword naturally throughout (aim for 1-2% density)
3. Integrate related keywords naturally without keyword stuffing
4. Write in a {_safe_enum_to_str(tone)} tone that matches the target audience
5. Provide specific examples, data points, and actionable insights
6. Use clear, scannable formatting with proper headings (H2, H3)
7. Keep paragraphs to 3-4 sentences maximum
8. Use bullet points and numbered lists where appropriate
9. Include natural transitions between sections
10. End each section with a clear takeaway or summary point

ENGAGEMENT REQUIREMENTS (CRITICAL):
- Include 3-5 rhetorical questions throughout the content to engage readers
- Add compelling call-to-action phrases: "Learn more", "Get started", "Discover", "Try this", "Explore"
- Include 5+ examples using "for example", "such as", "like", "for instance"
- Use storytelling elements and personal anecdotes where appropriate
- Add interactive elements: "Try this", "Consider this", "Imagine", "Think about"
- Include thought-provoking statements that encourage reader engagement
- End sections with questions or prompts that encourage reflection

ENGAGEMENT EXAMPLES:
✅ Good: "Have you ever wondered why Python is so popular among developers?"
✅ Good: "Try this simple exercise to see the difference..."
✅ Good: "For example, when building a web application, Python's simplicity..."
✅ Good: "Consider this: What if you could automate your entire workflow?"
✅ Good: "Imagine being able to build complex applications in just a few lines..."

ACCESSIBILITY REQUIREMENTS (CRITICAL):
- Use proper heading hierarchy: H1 (title only), H2 (main sections), H3 (subsections)
- Ensure no skipped heading levels (H1 → H2 → H3, not H1 → H3)
- For content over 1500 words, include a table of contents section
- Use descriptive link text (not "click here" or "read more")
- When mentioning images, include descriptive alt text suggestions
- Use lists (bulleted or numbered) for scannability (at least one per H2 section)
- Ensure sufficient white space between sections

READABILITY REQUIREMENTS (CRITICAL):
- Target Flesch Reading Ease: 60-70 (8th-9th grade level)
- Use short sentences (average 15-20 words per sentence)
- Replace complex words with simpler alternatives when possible
- Break up long paragraphs (3-4 sentences maximum)
- Use active voice instead of passive voice
- Avoid jargon unless necessary - explain technical terms
- Keep sentences clear and direct

READABILITY EXAMPLES:
❌ Complex: "The implementation of comprehensive optimization strategies necessitates..."
✅ Simple: "We optimize content using proven strategies that..."

❌ Complex: "It is imperative that one considers the multifaceted aspects..."
✅ Simple: "You should consider these important factors..."

❌ Complex: "The utilization of advanced methodologies enables..."
✅ Simple: "Using advanced methods helps..."

E-E-A-T REQUIREMENTS (CRITICAL):
- Add first-hand experience indicators where appropriate (2-3 per 1000 words)
- Use phrases like "In my experience...", "I've found that...", "Based on my work..."
- Include personal anecdotes or case studies when relevant
- Balance first-person experience with third-person authority
- Don't overuse - keep it natural and authentic

EXPERIENCE INDICATOR EXAMPLES:
✅ Good: "In my experience running a dog grooming business, I've found that..."
✅ Good: "Based on my research, I've noticed that..."
✅ Good: "When I started my business, I learned that..."
✅ Good: "I've worked with many clients who..."
✅ Good: "From my own experience, I can say that..."

CONTENT QUALITY STANDARDS:
- Provide unique insights, not just rehashed information
- Include specific examples, case studies, or real-world applications
- Cite sources naturally within the content
- Use active voice and clear, concise language
- Ensure factual accuracy and avoid speculation
- Create content that demonstrates expertise and authority
- Include current information from {current_year} where relevant
- Reference recent developments or trends when applicable
- Add temporal context to show content is up-to-date

STRUCTURE REQUIREMENTS (MANDATORY):
1. Content MUST start with exactly ONE H1 heading: # [Title]
   - This is the main title of the blog post
   - Only one H1 should exist in the entire content
   
2. After H1, write 2-3 introduction paragraphs (3-4 sentences each)
   - Hook the reader with a compelling opening
   - Introduce the topic and what readers will learn
   
3. Main sections MUST use H2 headings: ## [Section Title]
   - Minimum 3-5 H2 sections required
   - Each H2 section should have 3-5 paragraphs
   - Use descriptive, keyword-rich H2 headings
   
4. Subsections MUST use H3 headings: ### [Subsection Title]
   - Use H3 for detailed points within H2 sections
   - Maintain proper hierarchy (H1 > H2 > H3)
   
5. Use proper markdown formatting:
   - H1: # Title (only one, at the start)
   - H2: ## Section Title
   - H3: ### Subsection Title
   - H4-H6: Only for deeper nesting if needed
   
6. Include at least one list (bulleted or numbered) per H2 section
   - Use lists for key points, steps, or features
   - Keep list items concise but informative
   
7. End with H2 Conclusion section: ## Conclusion
   - Summarize key points
   - Provide actionable next steps
   - Include a call-to-action if appropriate

LINKING REQUIREMENTS:
1. Include 3-5 internal links using markdown format: [descriptive anchor text](/related-topic)
   - Links should be natural and contextual within paragraphs
   - Use descriptive anchor text (not "click here" or "read more")
   - Place links where they add value to the reader
   
2. Include 2-3 external authoritative links: [source name](https://authoritative-url.com)
   - Link to reputable sources, studies, or expert content
   - Use descriptive anchor text that indicates the source
   - Place external links naturally within relevant paragraphs
   
3. Links should enhance content, not distract
   - Don't over-link (maximum 1-2 links per paragraph)
   - Ensure links are relevant to the surrounding content

IMAGE PLACEMENT:
1. Add image placeholder after H1 and introduction: ![Featured image description](image-url)
   - Use descriptive alt text for SEO
   - Place after first paragraph following H1
   
2. Add image placeholders before major H2 sections: ![Section image description](image-url)
   - Use relevant images that enhance understanding
   - Include descriptive alt text
   - Place before H2 heading, not after

Generate comprehensive, well-researched content that readers will find valuable and search engines will recognize as authoritative."""
        
        if context:
            if context.get("sources"):
                prompt += f"\n\nAVAILABLE SOURCES:\n{chr(10).join(f'- {s}' for s in context['sources'][:5])}"
            if context.get("recent_info"):
                prompt += f"\n\nRECENT INFORMATION TO INCLUDE:\n{context['recent_info']}"
            if context.get("serp_features"):
                prompt += f"\n\nTARGET SERP FEATURES:\n{chr(10).join(f'- {f}' for f in context['serp_features'])}"
            if context.get("few_shot_examples"):
                prompt += f"\n\n{context['few_shot_examples']}"
            if context.get("search_intent"):
                intent = context.get("search_intent")
                recommendations = context.get("intent_recommendations", [])
                prompt += f"\n\nSEARCH INTENT: {intent}"
                if recommendations:
                    prompt += f"\nINTENT-BASED RECOMMENDATIONS:\n{chr(10).join(f'- {r}' for r in recommendations[:3])}"
            if context.get("adjusted_word_count"):
                prompt += f"\n\nADJUSTED TARGET LENGTH: {context['adjusted_word_count']} words (optimized based on competition)"
            if context.get("brand_recommendations"):
                brand_data = context['brand_recommendations']
                brands_list = brand_data.get("brands", [])
                if brands_list:
                    prompt += f"\n\nPRODUCT BRAND RECOMMENDATIONS:\nInclude detailed information about these brands/models: {', '.join(brands_list[:10])}\n\nFor each brand, include:\n- Key features and specifications\n- Pros and cons\n- Best use cases\n- Price range (if available)\n- User ratings/reviews summary\n- Where to buy\n\nCreate a dedicated comparison section or integrate brand recommendations throughout relevant sections."
            if context.get("custom_instructions"):
                prompt += f"\n\nADDITIONAL INSTRUCTIONS:\n{context['custom_instructions']}"
            
            # Priority 1: Apply citation patterns to draft generation
            if context.get("citation_patterns"):
                citation_patterns = context['citation_patterns']
                structure_insights = citation_patterns.get("content_structure_insights", [])
                if structure_insights:
                    prompt += "\n\nAI OPTIMIZATION REQUIREMENTS (Based on Top-Cited Pages):"
                    if "Question-based headings" in structure_insights:
                        prompt += "\n- Use question-based H2 headings (e.g., 'How to Start a Dog Grooming Business?')"
                    if "Concise titles" in structure_insights:
                        prompt += "\n- Keep headings concise (under 10 words)"
                    prompt += "\n- Add 2-3 sentence summaries after each H2 section (AI agents cite summaries)"
                    prompt += "\n- Use modular format with clear section boundaries"
                    prompt += "\n- Make content easy for AI agents to extract and cite"
            
            # Priority 3: Apply LLM response patterns
            if context.get("llm_responses"):
                llm_responses = context['llm_responses']
                extracted_points = llm_responses.get("extracted_key_points", [])
                if extracted_points:
                    prompt += "\n\nMATCH AI RESPONSE PATTERNS:"
                    prompt += "\nStructure your content similar to how AI agents answer questions about this topic."
                    prompt += "\n- Answer questions directly in the first paragraph"
                    prompt += "\n- Use clear, conversational language"
                    prompt += "\n- Include key points early in each section"
            
            if context.get("product_research_requirements"):
                req = context['product_research_requirements']
                prompt += f"\n\nPRODUCT RESEARCH REQUIREMENTS:\n"
                if req.get("include_brands"):
                    prompt += "- Include specific brand names and recommendations\n"
                if req.get("include_models"):
                    prompt += "- Include specific product model names\n"
                if req.get("include_prices"):
                    prompt += "- Include current pricing information where available\n"
                if req.get("include_features"):
                    prompt += "- Include detailed features and specifications\n"
                if req.get("include_reviews"):
                    prompt += "- Include review summaries and user ratings\n"
                if req.get("include_pros_cons"):
                    prompt += "- Include pros and cons for each recommended product\n"
                if req.get("include_product_table"):
                    prompt += "\nCONTENT STRUCTURE:\n- Create a product comparison table with key specifications\n"
                if req.get("include_comparison_section"):
                    prompt += "- Include a detailed comparison section\n"
                if req.get("include_buying_guide"):
                    prompt += "- Include a buying guide section with key considerations\n"
                if req.get("include_faq_section"):
                    prompt += "- Include an FAQ section addressing common questions\n"
        
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

ENGAGEMENT REQUIREMENTS (CRITICAL):
- Ensure content includes 3-5 rhetorical questions throughout to engage readers
- Add compelling call-to-action phrases: "Learn more", "Get started", "Discover", "Try this", "Explore"
- Include 5+ examples using "for example", "such as", "like", "for instance"
- Use storytelling elements and personal anecdotes where appropriate
- Add interactive elements: "Try this", "Consider this", "Imagine", "Think about"
- Include thought-provoking statements that encourage reader engagement
- End sections with questions or prompts that encourage reflection

ENGAGEMENT EXAMPLES:
✅ Good: "Have you ever wondered why Python is so popular among developers?"
✅ Good: "Try this simple exercise to see the difference..."
✅ Good: "For example, when building a web application, Python's simplicity..."
✅ Good: "Consider this: What if you could automate your entire workflow?"
✅ Good: "Imagine being able to build complex applications in just a few lines..."

ACCESSIBILITY REQUIREMENTS (CRITICAL):
- Verify proper heading hierarchy: H1 (title only), H2 (main sections), H3 (subsections)
- Ensure no skipped heading levels (H1 → H2 → H3, not H1 → H3)
- For content over 1500 words, add a table of contents section at the beginning
- Use descriptive link text (not "click here" or "read more")
- When mentioning images, include descriptive alt text suggestions
- Use lists (bulleted or numbered) for scannability (at least one per H2 section)
- Ensure sufficient white space between sections
- Check that all images have descriptive alt text placeholders

READABILITY REQUIREMENTS (CRITICAL - MUST TARGET 60-70):
- Target Flesch Reading Ease: 60-70 (8th-9th grade level) - THIS IS MANDATORY
- Simplify complex sentences - break long sentences into shorter ones (15-20 words average)
- Replace complex words with simpler alternatives:
  * "utilize" → "use"
  * "facilitate" → "help"
  * "implement" → "do" or "use"
  * "necessitate" → "need"
  * "comprehensive" → "complete" or "thorough"
- Use active voice instead of passive voice
- Keep paragraphs short (3-4 sentences maximum)
- Avoid jargon - explain technical terms in simple language
- Make sentences clear and direct

READABILITY EXAMPLES:
❌ Complex: "The implementation of comprehensive optimization strategies necessitates careful consideration..."
✅ Simple: "We optimize content using proven strategies. This requires careful planning..."

❌ Complex: "It is imperative that one considers the multifaceted aspects of the situation..."
✅ Simple: "You should consider these important factors..."

❌ Complex: "The utilization of advanced methodologies enables organizations to achieve..."
✅ Simple: "Using advanced methods helps businesses achieve..."

E-E-A-T REQUIREMENTS (CRITICAL):
- Add first-hand experience indicators where appropriate (2-3 per 1000 words)
- Use natural first-person phrases: "In my experience...", "I've found that...", "Based on my work..."
- Include personal anecdotes or case studies when relevant
- Balance first-person experience with third-person authority
- Don't overuse - keep it natural and authentic (not every paragraph needs first-person)

EXPERIENCE INDICATOR EXAMPLES:
✅ Good: "In my experience running a dog grooming business, I've found that..."
✅ Good: "Based on my research, I've noticed that..."
✅ Good: "When I started my business, I learned that..."
✅ Good: "I've worked with many clients who..."
✅ Good: "From my own experience, I can say that..."

OUTPUT REQUIREMENTS:
- Return the enhanced version of the content
- Maintain the original structure and length
- Preserve all factual information
- Improve without changing the core message
- Add citations or source references where appropriate
- Ensure the content reads naturally and flows well
- CRITICAL: Reading ease MUST be 60-70 after enhancement
- CRITICAL: Include 2-3 first-hand experience indicators per 1000 words

Focus on making the content more authoritative, engaging, and valuable while maintaining accuracy and readability. Prioritize readability improvements - content must be easy to read (60-70 reading ease)."""
        
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
Provide your response in the following exact format:

Meta Title: [Your SEO-optimized title here - 50-60 characters, include primary keyword]
Meta Description: [Your compelling meta description here - 150-160 characters with call-to-action]

Internal Link Suggestions:
Internal Link: [anchor text] -> /related-topic-url
Internal Link: [anchor text] -> /related-topic-url
Internal Link: [anchor text] -> /related-topic-url
[Provide 3-5 internal link suggestions with descriptive anchor text and URL paths]

Image Alt Text Suggestions:
1. [Descriptive alt text for featured image]
2. [Alt text for section image]
3. [Alt text for section image]
[Provide 3-5 image alt text suggestions]

Schema Markup Recommendations:
[Brief recommendations for structured data]

URL Slug: [seo-friendly-url-slug]

IMPORTANT:
- Meta Title MUST be a proper title string, NOT "**" or placeholder text
- Meta Title should be 50-60 characters and include the primary keyword
- Internal links should use descriptive anchor text, not generic phrases
- All output should be clear, specific, and actionable

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
    def _get_word_count(length: Union[ContentLength, str]) -> int:
        """Get target word count for content length."""
        # Normalize to string for comparison
        length_str = _safe_enum_to_str(length)
        
        word_counts = {
            ContentLength.SHORT.value: 800,
            ContentLength.MEDIUM.value: 1500,
            ContentLength.LONG.value: 2500,
            ContentLength.EXTENDED.value: 4000
        }
        return word_counts.get(length_str, 1500)

