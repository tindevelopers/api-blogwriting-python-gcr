"""
AI-powered content generator that integrates with the BlogWriter SDK.

This module provides enhanced content generation capabilities using
multiple AI providers with intelligent fallback and optimization.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from enum import Enum

from .base_provider import (
    AIProviderManager, 
    AIRequest, 
    AIResponse, 
    ContentType, 
    AIGenerationConfig,
    AIProviderError
)
from .openai_provider import OpenAIProvider, AzureOpenAIProvider
from .anthropic_provider import AnthropicProvider
from ..models.blog_models import ContentTone, ContentLength


logger = logging.getLogger(__name__)


class ContentTemplate(str, Enum):
    """Predefined content templates."""
    HOW_TO_GUIDE = "how_to_guide"
    LISTICLE = "listicle"
    REVIEW = "review"
    COMPARISON = "comparison"
    NEWS_ARTICLE = "news_article"
    TUTORIAL = "tutorial"
    CASE_STUDY = "case_study"
    OPINION_PIECE = "opinion_piece"
    INTERVIEW = "interview"
    ROUNDUP = "roundup"


class AIContentGenerator:
    """
    AI-powered content generator with multi-provider support.
    
    This class provides intelligent content generation using multiple AI providers
    with automatic fallback, cost optimization, and quality assurance.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the AI content generator.
        
        Args:
            config: Configuration dictionary for AI providers and settings
        """
        self.config = config or {}
        self.provider_manager = AIProviderManager()
        self.content_templates = self._load_content_templates()
        self.generation_stats = {
            "total_requests": 0,
            "successful_generations": 0,
            "failed_generations": 0,
            "total_tokens_used": 0,
            "total_cost": 0.0,
            "provider_usage": {}
        }
        
        # Initialize providers based on config
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize AI providers based on configuration."""
        providers_config = self.config.get('providers', {})
        
        # Initialize OpenAI if configured
        if 'openai' in providers_config:
            openai_config = providers_config['openai']
            if openai_config.get('api_key'):
                try:
                    provider = OpenAIProvider(
                        api_key=openai_config['api_key'],
                        organization=openai_config.get('organization'),
                        max_retries=openai_config.get('max_retries', 3),
                        timeout=openai_config.get('timeout', 30)
                    )
                    
                    from .base_provider import AIProviderConfig, AIProviderType
                    config = AIProviderConfig(
                        provider_type=AIProviderType.OPENAI,
                        api_key=openai_config['api_key'],
                        default_model=openai_config.get('default_model', 'gpt-4o-mini'),
                        enabled=openai_config.get('enabled', True),
                        priority=openai_config.get('priority', 1)
                    )
                    
                    self.provider_manager.add_provider('openai', provider, config)
                    logger.info("OpenAI provider initialized successfully")
                    
                except Exception as e:
                    logger.error(f"Failed to initialize OpenAI provider: {e}")
        
        # Initialize Azure OpenAI if configured
        if 'azure_openai' in providers_config:
            azure_config = providers_config['azure_openai']
            if azure_config.get('api_key') and azure_config.get('azure_endpoint'):
                try:
                    provider = AzureOpenAIProvider(
                        api_key=azure_config['api_key'],
                        azure_endpoint=azure_config['azure_endpoint'],
                        api_version=azure_config.get('api_version', '2024-02-15-preview'),
                        max_retries=azure_config.get('max_retries', 3),
                        timeout=azure_config.get('timeout', 30)
                    )
                    
                    from .base_provider import AIProviderConfig, AIProviderType
                    config = AIProviderConfig(
                        provider_type=AIProviderType.AZURE_OPENAI,
                        api_key=azure_config['api_key'],
                        default_model=azure_config.get('default_model', 'gpt-4o-mini'),
                        enabled=azure_config.get('enabled', True),
                        priority=azure_config.get('priority', 2)
                    )
                    
                    self.provider_manager.add_provider('azure_openai', provider, config)
                    logger.info("Azure OpenAI provider initialized successfully")
                    
                except Exception as e:
                    logger.error(f"Failed to initialize Azure OpenAI provider: {e}")
        
        # Initialize Anthropic if configured
        if 'anthropic' in providers_config:
            anthropic_config = providers_config['anthropic']
            if anthropic_config.get('api_key'):
                try:
                    provider = AnthropicProvider(
                        api_key=anthropic_config['api_key'],
                        max_retries=anthropic_config.get('max_retries', 3),
                        timeout=anthropic_config.get('timeout', 30)
                    )
                    
                    from .base_provider import AIProviderConfig, AIProviderType
                    config = AIProviderConfig(
                        provider_type=AIProviderType.ANTHROPIC,
                        api_key=anthropic_config['api_key'],
                        default_model=anthropic_config.get('default_model', 'claude-3-5-haiku-20241022'),
                        enabled=anthropic_config.get('enabled', True),
                        priority=anthropic_config.get('priority', 3)
                    )
                    
                    self.provider_manager.add_provider('anthropic', provider, config)
                    logger.info("Anthropic provider initialized successfully")
                    
                except Exception as e:
                    logger.error(f"Failed to initialize Anthropic provider: {e}")
    
    async def generate_blog_content(
        self,
        topic: str,
        keywords: List[str],
        tone: ContentTone = ContentTone.PROFESSIONAL,
        length: ContentLength = ContentLength.MEDIUM,
        template: Optional[ContentTemplate] = None,
        additional_context: Optional[Dict[str, Any]] = None,
        preferred_provider: Optional[str] = None
    ) -> AIResponse:
        """
        Generate complete blog post content.
        
        Args:
            topic: Main topic for the blog post
            keywords: Target keywords for SEO
            tone: Writing tone
            length: Target content length
            template: Content template to use
            additional_context: Additional context for generation
            preferred_provider: Preferred AI provider
            
        Returns:
            AI response with generated content
        """
        self.generation_stats["total_requests"] += 1
        
        try:
            # Prepare context
            context = {
                "keywords": keywords,
                "tone": tone.value,
                "target_length": self._get_word_count_target(length),
                "template": template.value if template else "blog_post"
            }
            
            if additional_context:
                context.update(additional_context)
            
            # Create prompt based on template
            prompt = self._create_blog_prompt(topic, template, context)
            
            # Configure generation parameters
            config = AIGenerationConfig(
                max_tokens=self._get_max_tokens(length),
                temperature=self._get_temperature(tone),
                top_p=0.9,
                frequency_penalty=0.1,
                presence_penalty=0.1
            )
            
            # Create AI request
            request = AIRequest(
                prompt=prompt,
                content_type=ContentType.BLOG_POST,
                config=config,
                context=context
            )
            
            # Generate content
            response = await self.provider_manager.generate_content(
                request=request,
                preferred_provider=preferred_provider
            )
            
            # Update statistics
            self._update_stats(response, success=True)
            
            return response
            
        except Exception as e:
            self.generation_stats["failed_generations"] += 1
            logger.error(f"Blog content generation failed: {e}")
            raise AIProviderError(f"Failed to generate blog content: {str(e)}", "ai_generator")
    
    async def generate_title(
        self,
        topic: str,
        content: str,
        keywords: List[str],
        tone: ContentTone = ContentTone.PROFESSIONAL,
        preferred_provider: Optional[str] = None
    ) -> AIResponse:
        """Generate SEO-optimized blog title."""
        self.generation_stats["total_requests"] += 1
        
        try:
            context = {
                "keywords": keywords,
                "tone": tone.value,
                "content_preview": content[:500]  # First 500 chars for context
            }
            
            prompt = self._create_title_prompt(topic, content, keywords)
            
            config = AIGenerationConfig(
                max_tokens=100,
                temperature=self._get_temperature(tone),
                top_p=0.9
            )
            
            request = AIRequest(
                prompt=prompt,
                content_type=ContentType.TITLE,
                config=config,
                context=context
            )
            
            response = await self.provider_manager.generate_content(
                request=request,
                preferred_provider=preferred_provider
            )
            
            self._update_stats(response, success=True)
            return response
            
        except Exception as e:
            self.generation_stats["failed_generations"] += 1
            logger.error(f"Title generation failed: {e}")
            raise AIProviderError(f"Failed to generate title: {str(e)}", "ai_generator")
    
    async def generate_meta_description(
        self,
        title: str,
        content: str,
        keywords: List[str],
        preferred_provider: Optional[str] = None
    ) -> AIResponse:
        """Generate SEO meta description."""
        self.generation_stats["total_requests"] += 1
        
        try:
            context = {
                "keywords": keywords,
                "title": title,
                "content_preview": content[:300]
            }
            
            prompt = self._create_meta_description_prompt(title, content, keywords)
            
            config = AIGenerationConfig(
                max_tokens=80,  # ~160 characters
                temperature=0.7,
                top_p=0.9
            )
            
            request = AIRequest(
                prompt=prompt,
                content_type=ContentType.META_DESCRIPTION,
                config=config,
                context=context
            )
            
            response = await self.provider_manager.generate_content(
                request=request,
                preferred_provider=preferred_provider
            )
            
            self._update_stats(response, success=True)
            return response
            
        except Exception as e:
            self.generation_stats["failed_generations"] += 1
            logger.error(f"Meta description generation failed: {e}")
            raise AIProviderError(f"Failed to generate meta description: {str(e)}", "ai_generator")
    
    async def generate_introduction(
        self,
        topic: str,
        keywords: List[str],
        tone: ContentTone = ContentTone.PROFESSIONAL,
        preferred_provider: Optional[str] = None
    ) -> AIResponse:
        """Generate engaging blog introduction."""
        self.generation_stats["total_requests"] += 1
        
        try:
            context = {
                "keywords": keywords,
                "tone": tone.value,
                "target_length": "150-250 words"
            }
            
            prompt = self._create_introduction_prompt(topic, keywords, tone)
            
            config = AIGenerationConfig(
                max_tokens=400,
                temperature=self._get_temperature(tone),
                top_p=0.9
            )
            
            request = AIRequest(
                prompt=prompt,
                content_type=ContentType.INTRODUCTION,
                config=config,
                context=context
            )
            
            response = await self.provider_manager.generate_content(
                request=request,
                preferred_provider=preferred_provider
            )
            
            self._update_stats(response, success=True)
            return response
            
        except Exception as e:
            self.generation_stats["failed_generations"] += 1
            logger.error(f"Introduction generation failed: {e}")
            raise AIProviderError(f"Failed to generate introduction: {str(e)}", "ai_generator")
    
    async def generate_conclusion(
        self,
        topic: str,
        key_points: List[str],
        tone: ContentTone = ContentTone.PROFESSIONAL,
        preferred_provider: Optional[str] = None
    ) -> AIResponse:
        """Generate effective blog conclusion."""
        self.generation_stats["total_requests"] += 1
        
        try:
            context = {
                "key_points": key_points,
                "tone": tone.value,
                "target_length": "100-200 words"
            }
            
            prompt = self._create_conclusion_prompt(topic, key_points, tone)
            
            config = AIGenerationConfig(
                max_tokens=300,
                temperature=self._get_temperature(tone),
                top_p=0.9
            )
            
            request = AIRequest(
                prompt=prompt,
                content_type=ContentType.CONCLUSION,
                config=config,
                context=context
            )
            
            response = await self.provider_manager.generate_content(
                request=request,
                preferred_provider=preferred_provider
            )
            
            self._update_stats(response, success=True)
            return response
            
        except Exception as e:
            self.generation_stats["failed_generations"] += 1
            logger.error(f"Conclusion generation failed: {e}")
            raise AIProviderError(f"Failed to generate conclusion: {str(e)}", "ai_generator")
    
    async def generate_faq_section(
        self,
        topic: str,
        keywords: List[str],
        num_questions: int = 5,
        preferred_provider: Optional[str] = None
    ) -> AIResponse:
        """Generate FAQ section for the blog post."""
        self.generation_stats["total_requests"] += 1
        
        try:
            context = {
                "keywords": keywords,
                "num_questions": num_questions,
                "topic": topic
            }
            
            prompt = self._create_faq_prompt(topic, keywords, num_questions)
            
            config = AIGenerationConfig(
                max_tokens=800,
                temperature=0.7,
                top_p=0.9
            )
            
            request = AIRequest(
                prompt=prompt,
                content_type=ContentType.FAQ,
                config=config,
                context=context
            )
            
            response = await self.provider_manager.generate_content(
                request=request,
                preferred_provider=preferred_provider
            )
            
            self._update_stats(response, success=True)
            return response
            
        except Exception as e:
            self.generation_stats["failed_generations"] += 1
            logger.error(f"FAQ generation failed: {e}")
            raise AIProviderError(f"Failed to generate FAQ: {str(e)}", "ai_generator")
    
    def _get_word_count_target(self, length: ContentLength) -> int:
        """Get target word count based on content length."""
        targets = {
            ContentLength.SHORT: 500,
            ContentLength.MEDIUM: 1000,
            ContentLength.LONG: 2000,
            ContentLength.EXTENDED: 3500
        }
        return targets.get(length, 1000)
    
    def _get_max_tokens(self, length: ContentLength) -> int:
        """Get max tokens based on content length."""
        # Roughly 4 characters per token
        word_count = self._get_word_count_target(length)
        return int(word_count * 1.5)  # Add buffer for formatting
    
    def _get_temperature(self, tone: ContentTone) -> float:
        """Get temperature based on content tone."""
        temperatures = {
            ContentTone.PROFESSIONAL: 0.7,
            ContentTone.CASUAL: 0.8,
            ContentTone.FRIENDLY: 0.8,
            ContentTone.AUTHORITATIVE: 0.6,
            ContentTone.CONVERSATIONAL: 0.9,
            ContentTone.TECHNICAL: 0.6,
            ContentTone.CREATIVE: 0.9
        }
        return temperatures.get(tone, 0.7)
    
    def _load_content_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load content templates for different blog types."""
        return {
            ContentTemplate.HOW_TO_GUIDE.value: {
                "structure": ["introduction", "materials_needed", "step_by_step", "tips", "conclusion"],
                "keywords_density": 0.02,
                "tone_preference": ContentTone.INSTRUCTIONAL
            },
            ContentTemplate.LISTICLE.value: {
                "structure": ["introduction", "numbered_items", "conclusion"],
                "keywords_density": 0.015,
                "tone_preference": ContentTone.ENGAGING
            },
            ContentTemplate.REVIEW.value: {
                "structure": ["introduction", "pros_cons", "detailed_analysis", "verdict"],
                "keywords_density": 0.02,
                "tone_preference": ContentTone.ANALYTICAL
            },
            ContentTemplate.COMPARISON.value: {
                "structure": ["introduction", "comparison_table", "detailed_comparison", "recommendation"],
                "keywords_density": 0.025,
                "tone_preference": ContentTone.OBJECTIVE
            }
        }
    
    def _create_blog_prompt(
        self, 
        topic: str, 
        template: Optional[ContentTemplate], 
        context: Dict[str, Any]
    ) -> str:
        """Create comprehensive blog post prompt."""
        base_prompt = f"""Write a comprehensive, SEO-optimized blog post about: {topic}

Requirements:
- Target word count: {context.get('target_length', 1000)} words
- Writing tone: {context.get('tone', 'professional')}
- Target keywords to incorporate naturally: {', '.join(context.get('keywords', []))}
- Use proper heading structure (H2, H3, etc.)
- Include engaging introduction and strong conclusion
- Provide actionable insights and valuable information
- Ensure content is original and well-researched
"""
        
        if template:
            template_info = self.content_templates.get(template.value, {})
            structure = template_info.get('structure', [])
            if structure:
                base_prompt += f"\n- Follow this content structure: {' → '.join(structure)}"
        
        if context.get('audience'):
            base_prompt += f"\n- Target audience: {context['audience']}"
        
        if context.get('brand_voice'):
            base_prompt += f"\n- Brand voice: {context['brand_voice']}"
        
        if context.get('additional_instructions'):
            base_prompt += f"\n- Additional instructions: {context['additional_instructions']}"
        
        return base_prompt
    
    def _create_title_prompt(self, topic: str, content: str, keywords: List[str]) -> str:
        """Create title generation prompt."""
        return f"""Create 5 compelling, SEO-optimized blog titles for a post about: {topic}

Requirements:
- Include primary keyword: {keywords[0] if keywords else topic}
- Keep under 60 characters for SEO
- Make them click-worthy and engaging
- Accurately represent the content
- Use power words and emotional triggers

Content preview: {content[:200]}...

Format as a numbered list."""
    
    def _create_meta_description_prompt(self, title: str, content: str, keywords: List[str]) -> str:
        """Create meta description prompt."""
        return f"""Write a compelling SEO meta description for this blog post:

Title: {title}
Keywords: {', '.join(keywords)}
Content preview: {content[:300]}...

Requirements:
- Exactly 150-160 characters
- Include primary keyword naturally
- Compelling call-to-action
- Accurately summarize the content
- Encourage clicks from search results"""
    
    def _create_introduction_prompt(self, topic: str, keywords: List[str], tone: ContentTone) -> str:
        """Create introduction prompt."""
        return f"""Write an engaging blog post introduction about: {topic}

Requirements:
- Hook readers immediately with an interesting opening
- Clearly establish what readers will learn
- Include primary keyword: {keywords[0] if keywords else topic}
- Writing tone: {tone.value}
- Length: 150-250 words
- Create curiosity and encourage continued reading
- Establish credibility and expertise"""
    
    def _create_conclusion_prompt(self, topic: str, key_points: List[str], tone: ContentTone) -> str:
        """Create conclusion prompt."""
        key_points_text = '\n'.join(f"- {point}" for point in key_points)
        
        return f"""Write a strong conclusion for a blog post about: {topic}

Key points covered in the article:
{key_points_text}

Requirements:
- Summarize the main insights
- Provide actionable next steps
- Writing tone: {tone.value}
- Length: 100-200 words
- End with a compelling call-to-action
- Reinforce the value provided to readers"""
    
    def _create_faq_prompt(self, topic: str, keywords: List[str], num_questions: int) -> str:
        """Create FAQ section prompt."""
        return f"""Create a comprehensive FAQ section for a blog post about: {topic}

Requirements:
- Generate {num_questions} relevant questions and detailed answers
- Include keywords naturally: {', '.join(keywords)}
- Address common concerns and misconceptions
- Provide valuable, actionable information
- Use clear, conversational language
- Format as Q&A pairs with proper headings

Focus on questions that real readers would actually ask about this topic."""
    
    def _update_stats(self, response: AIResponse, success: bool):
        """Update generation statistics."""
        if success:
            self.generation_stats["successful_generations"] += 1
            if response.tokens_used:
                self.generation_stats["total_tokens_used"] += response.tokens_used
            if response.cost:
                self.generation_stats["total_cost"] += response.cost
            
            provider = response.provider
            if provider not in self.generation_stats["provider_usage"]:
                self.generation_stats["provider_usage"][provider] = 0
            self.generation_stats["provider_usage"][provider] += 1
    
    async def get_provider_health(self) -> Dict[str, Dict[str, Any]]:
        """Get health status of all providers."""
        return await self.provider_manager.health_check_all()
    
    def get_generation_stats(self) -> Dict[str, Any]:
        """Get generation statistics."""
        stats = self.generation_stats.copy()
        if stats["total_requests"] > 0:
            stats["success_rate"] = stats["successful_generations"] / stats["total_requests"]
            stats["average_cost_per_request"] = stats["total_cost"] / stats["total_requests"]
        else:
            stats["success_rate"] = 0.0
            stats["average_cost_per_request"] = 0.0
        
        return stats
