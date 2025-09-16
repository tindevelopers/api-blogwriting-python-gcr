"""
Blog Writer Factory

This module provides factory patterns for creating Blog Writer instances
with different configurations, strategies, and provider setups.
"""

import os
import logging
from typing import Dict, List, Optional, Any, Type
from enum import Enum

from .blog_writer_abstraction import (
    BlogWriterAbstraction,
    ContentStrategy,
    ContentQuality
)
from .ai_content_generator import AIContentGenerator
from ..seo.enhanced_keyword_analyzer import EnhancedKeywordAnalyzer
from ..core.content_analyzer import ContentAnalyzer
from .base_provider import AIProviderType, AIProviderConfig


logger = logging.getLogger(__name__)


class BlogWriterPreset(str, Enum):
    """Predefined blog writer configurations."""
    SEO_FOCUSED = "seo_focused"
    ENGAGEMENT_FOCUSED = "engagement_focused"
    CONVERSION_FOCUSED = "conversion_focused"
    TECHNICAL_WRITER = "technical_writer"
    CREATIVE_WRITER = "creative_writer"
    ENTERPRISE_WRITER = "enterprise_writer"
    STARTUP_WRITER = "startup_writer"
    MINIMAL_WRITER = "minimal_writer"


class BlogWriterFactory:
    """
    Factory class for creating Blog Writer instances with different configurations.
    """
    
    @staticmethod
    def create_blog_writer(
        preset: Optional[BlogWriterPreset] = None,
        custom_config: Optional[Dict[str, Any]] = None,
        providers: Optional[List[str]] = None
    ) -> BlogWriterAbstraction:
        """
        Create a Blog Writer instance with specified configuration.
        
        Args:
            preset: Predefined configuration preset
            custom_config: Custom configuration overrides
            providers: List of AI providers to enable
            
        Returns:
            Configured Blog Writer instance
        """
        # Start with base configuration
        config = BlogWriterFactory._get_base_config()
        
        # Apply preset configuration
        if preset:
            preset_config = BlogWriterFactory._get_preset_config(preset)
            config = BlogWriterFactory._merge_configs(config, preset_config)
        
        # Apply custom configuration
        if custom_config:
            config = BlogWriterFactory._merge_configs(config, custom_config)
        
        # Filter providers if specified
        if providers:
            config = BlogWriterFactory._filter_providers(config, providers)
        
        # Create components
        ai_generator = BlogWriterFactory._create_ai_generator(config)
        keyword_analyzer = BlogWriterFactory._create_keyword_analyzer(config)
        content_analyzer = BlogWriterFactory._create_content_analyzer(config)
        
        # Create and return Blog Writer instance
        return BlogWriterAbstraction(
            ai_generator=ai_generator,
            keyword_analyzer=keyword_analyzer,
            content_analyzer=content_analyzer,
            config=config
        )
    
    @staticmethod
    def create_seo_focused_writer(
        dataforseo_config: Optional[Dict[str, Any]] = None
    ) -> BlogWriterAbstraction:
        """Create an SEO-focused blog writer."""
        config = {
            "default_strategy": ContentStrategy.SEO_OPTIMIZED,
            "default_quality": ContentQuality.EXCELLENT,
            "enable_keyword_analysis": True,
            "enable_content_optimization": True,
            "dataforseo": dataforseo_config or {}
        }
        
        return BlogWriterFactory.create_blog_writer(
            preset=BlogWriterPreset.SEO_FOCUSED,
            custom_config=config
        )
    
    @staticmethod
    def create_engagement_focused_writer() -> BlogWriterAbstraction:
        """Create an engagement-focused blog writer."""
        config = {
            "default_strategy": ContentStrategy.ENGAGEMENT_FOCUSED,
            "default_quality": ContentQuality.GOOD,
            "enable_storytelling": True,
            "enable_emotional_triggers": True
        }
        
        return BlogWriterFactory.create_blog_writer(
            preset=BlogWriterPreset.ENGAGEMENT_FOCUSED,
            custom_config=config
        )
    
    @staticmethod
    def create_conversion_focused_writer() -> BlogWriterAbstraction:
        """Create a conversion-focused blog writer."""
        config = {
            "default_strategy": ContentStrategy.CONVERSION_OPTIMIZED,
            "default_quality": ContentQuality.EXCELLENT,
            "enable_cta_optimization": True,
            "enable_urgency_elements": True
        }
        
        return BlogWriterFactory.create_blog_writer(
            preset=BlogWriterPreset.CONVERSION_FOCUSED,
            custom_config=config
        )
    
    @staticmethod
    def create_technical_writer() -> BlogWriterAbstraction:
        """Create a technical blog writer."""
        config = {
            "default_strategy": ContentStrategy.TECHNICAL,
            "default_quality": ContentQuality.EXCELLENT,
            "enable_code_examples": True,
            "enable_diagrams": True,
            "technical_depth": "advanced"
        }
        
        return BlogWriterFactory.create_blog_writer(
            preset=BlogWriterPreset.TECHNICAL_WRITER,
            custom_config=config
        )
    
    @staticmethod
    def create_creative_writer() -> BlogWriterAbstraction:
        """Create a creative blog writer."""
        config = {
            "default_strategy": ContentStrategy.CREATIVE,
            "default_quality": ContentQuality.GOOD,
            "enable_creative_elements": True,
            "enable_storytelling": True,
            "allow_experimental_content": True
        }
        
        return BlogWriterFactory.create_blog_writer(
            preset=BlogWriterPreset.CREATIVE_WRITER,
            custom_config=config
        )
    
    @staticmethod
    def create_enterprise_writer() -> BlogWriterAbstraction:
        """Create an enterprise-grade blog writer."""
        config = {
            "default_strategy": ContentStrategy.SEO_OPTIMIZED,
            "default_quality": ContentQuality.PUBLICATION_READY,
            "enable_enterprise_features": True,
            "enable_brand_consistency": True,
            "enable_compliance_checking": True,
            "enable_approval_workflow": True
        }
        
        return BlogWriterFactory.create_blog_writer(
            preset=BlogWriterPreset.ENTERPRISE_WRITER,
            custom_config=config
        )
    
    @staticmethod
    def create_startup_writer() -> BlogWriterAbstraction:
        """Create a startup-focused blog writer."""
        config = {
            "default_strategy": ContentStrategy.ENGAGEMENT_FOCUSED,
            "default_quality": ContentQuality.GOOD,
            "enable_cost_optimization": True,
            "enable_rapid_generation": True,
            "enable_mvp_content": True
        }
        
        return BlogWriterFactory.create_blog_writer(
            preset=BlogWriterPreset.STARTUP_WRITER,
            custom_config=config
        )
    
    @staticmethod
    def create_minimal_writer() -> BlogWriterAbstraction:
        """Create a minimal blog writer with basic features."""
        config = {
            "default_strategy": ContentStrategy.SEO_OPTIMIZED,
            "default_quality": ContentQuality.DRAFT,
            "enable_basic_features_only": True,
            "disable_advanced_optimization": True
        }
        
        return BlogWriterFactory.create_blog_writer(
            preset=BlogWriterPreset.MINIMAL_WRITER,
            custom_config=config
        )
    
    @staticmethod
    def create_custom_writer(
        providers: List[str],
        strategy: ContentStrategy,
        quality: ContentQuality,
        features: Optional[Dict[str, bool]] = None
    ) -> BlogWriterAbstraction:
        """Create a custom blog writer with specific configuration."""
        config = {
            "default_strategy": strategy,
            "default_quality": quality,
            "enabled_features": features or {},
            "providers": {
                provider: {"enabled": True, "priority": i + 1}
                for i, provider in enumerate(providers)
            }
        }
        
        return BlogWriterFactory.create_blog_writer(
            custom_config=config,
            providers=providers
        )
    
    @staticmethod
    def _get_base_config() -> Dict[str, Any]:
        """Get base configuration for all blog writers."""
        return {
            "providers": {
                "openai": {
                    "api_key": os.getenv("OPENAI_API_KEY"),
                    "default_model": "gpt-4o-mini",
                    "enabled": bool(os.getenv("OPENAI_API_KEY")),
                    "priority": 1,
                    "max_retries": 3,
                    "timeout": 30
                },
                "anthropic": {
                    "api_key": os.getenv("ANTHROPIC_API_KEY"),
                    "default_model": "claude-3-5-haiku-20241022",
                    "enabled": bool(os.getenv("ANTHROPIC_API_KEY")),
                    "priority": 2,
                    "max_retries": 3,
                    "timeout": 30
                },
                "azure_openai": {
                    "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
                    "azure_endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
                    "api_version": os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
                    "default_model": "gpt-4o-mini",
                    "enabled": bool(os.getenv("AZURE_OPENAI_API_KEY")),
                    "priority": 3,
                    "max_retries": 3,
                    "timeout": 30
                }
            },
            "default_strategy": ContentStrategy.SEO_OPTIMIZED,
            "default_quality": ContentQuality.GOOD,
            "enable_keyword_analysis": True,
            "enable_content_optimization": True,
            "enable_quality_assurance": True,
            "max_concurrent_generations": 3,
            "cache_enabled": True,
            "logging_level": "INFO"
        }
    
    @staticmethod
    def _get_preset_config(preset: BlogWriterPreset) -> Dict[str, Any]:
        """Get configuration for specific presets."""
        preset_configs = {
            BlogWriterPreset.SEO_FOCUSED: {
                "default_strategy": ContentStrategy.SEO_OPTIMIZED,
                "default_quality": ContentQuality.EXCELLENT,
                "enable_keyword_analysis": True,
                "enable_seo_optimization": True,
                "enable_meta_generation": True,
                "seo_requirements": {
                    "keyword_density": 0.02,
                    "heading_structure": True,
                    "internal_linking": True,
                    "meta_tags": True
                }
            },
            BlogWriterPreset.ENGAGEMENT_FOCUSED: {
                "default_strategy": ContentStrategy.ENGAGEMENT_FOCUSED,
                "default_quality": ContentQuality.GOOD,
                "enable_storytelling": True,
                "enable_emotional_triggers": True,
                "enable_interactive_elements": True,
                "engagement_features": {
                    "hook_optimization": True,
                    "storytelling": True,
                    "emotional_appeal": True,
                    "social_proof": True
                }
            },
            BlogWriterPreset.CONVERSION_FOCUSED: {
                "default_strategy": ContentStrategy.CONVERSION_OPTIMIZED,
                "default_quality": ContentQuality.EXCELLENT,
                "enable_cta_optimization": True,
                "enable_urgency_elements": True,
                "enable_trust_signals": True,
                "conversion_features": {
                    "cta_placement": "optimal",
                    "urgency_creation": True,
                    "benefit_focus": True,
                    "trust_building": True
                }
            },
            BlogWriterPreset.TECHNICAL_WRITER: {
                "default_strategy": ContentStrategy.TECHNICAL,
                "default_quality": ContentQuality.EXCELLENT,
                "enable_code_examples": True,
                "enable_diagrams": True,
                "enable_technical_depth": True,
                "technical_features": {
                    "code_syntax_highlighting": True,
                    "diagram_generation": True,
                    "technical_accuracy": True,
                    "step_by_step_guides": True
                }
            },
            BlogWriterPreset.CREATIVE_WRITER: {
                "default_strategy": ContentStrategy.CREATIVE,
                "default_quality": ContentQuality.GOOD,
                "enable_creative_elements": True,
                "enable_experimental_content": True,
                "enable_artistic_expression": True,
                "creative_features": {
                    "unconventional_structures": True,
                    "artistic_language": True,
                    "experimental_formats": True,
                    "creative_metaphors": True
                }
            },
            BlogWriterPreset.ENTERPRISE_WRITER: {
                "default_strategy": ContentStrategy.SEO_OPTIMIZED,
                "default_quality": ContentQuality.PUBLICATION_READY,
                "enable_enterprise_features": True,
                "enable_brand_consistency": True,
                "enable_compliance_checking": True,
                "enterprise_features": {
                    "brand_guidelines": True,
                    "compliance_checking": True,
                    "approval_workflow": True,
                    "multi_language_support": True,
                    "enterprise_security": True
                }
            },
            BlogWriterPreset.STARTUP_WRITER: {
                "default_strategy": ContentStrategy.ENGAGEMENT_FOCUSED,
                "default_quality": ContentQuality.GOOD,
                "enable_cost_optimization": True,
                "enable_rapid_generation": True,
                "enable_mvp_content": True,
                "startup_features": {
                    "cost_optimization": True,
                    "rapid_prototyping": True,
                    "mvp_focus": True,
                    "lean_content": True
                }
            },
            BlogWriterPreset.MINIMAL_WRITER: {
                "default_strategy": ContentStrategy.SEO_OPTIMIZED,
                "default_quality": ContentQuality.DRAFT,
                "enable_basic_features_only": True,
                "disable_advanced_optimization": True,
                "minimal_features": {
                    "basic_generation": True,
                    "simple_optimization": True,
                    "minimal_analysis": True
                }
            }
        }
        
        return preset_configs.get(preset, {})
    
    @staticmethod
    def _merge_configs(base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge configuration dictionaries recursively."""
        merged = base_config.copy()
        
        for key, value in override_config.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = BlogWriterFactory._merge_configs(merged[key], value)
            else:
                merged[key] = value
        
        return merged
    
    @staticmethod
    def _filter_providers(config: Dict[str, Any], providers: List[str]) -> Dict[str, Any]:
        """Filter configuration to only include specified providers."""
        if "providers" not in config:
            return config
        
        filtered_providers = {}
        for provider in providers:
            if provider in config["providers"]:
                filtered_providers[provider] = config["providers"][provider]
        
        config["providers"] = filtered_providers
        return config
    
    @staticmethod
    def _create_ai_generator(config: Dict[str, Any]) -> AIContentGenerator:
        """Create AI content generator with configuration."""
        return AIContentGenerator(config)
    
    @staticmethod
    def _create_keyword_analyzer(config: Dict[str, Any]) -> Optional[EnhancedKeywordAnalyzer]:
        """Create keyword analyzer if enabled in configuration."""
        if not config.get("enable_keyword_analysis", False):
            return None
        
        try:
            dataforseo_config = config.get("dataforseo", {})
            return EnhancedKeywordAnalyzer(dataforseo_config)
        except Exception as e:
            logger.warning(f"Failed to create keyword analyzer: {e}")
            return None
    
    @staticmethod
    def _create_content_analyzer(config: Dict[str, Any]) -> Optional[ContentAnalyzer]:
        """Create content analyzer if enabled in configuration."""
        if not config.get("enable_quality_assurance", False):
            return None
        
        try:
            return ContentAnalyzer()
        except Exception as e:
            logger.warning(f"Failed to create content analyzer: {e}")
            return None


class BlogWriterBuilder:
    """
    Builder pattern for creating Blog Writer instances with fluent interface.
    """
    
    def __init__(self):
        self.config = BlogWriterFactory._get_base_config()
        self.providers = []
    
    def with_preset(self, preset: BlogWriterPreset) -> 'BlogWriterBuilder':
        """Set configuration preset."""
        preset_config = BlogWriterFactory._get_preset_config(preset)
        self.config = BlogWriterFactory._merge_configs(self.config, preset_config)
        return self
    
    def with_providers(self, *providers: str) -> 'BlogWriterBuilder':
        """Set AI providers to use."""
        self.providers = list(providers)
        return self
    
    def with_strategy(self, strategy: ContentStrategy) -> 'BlogWriterBuilder':
        """Set default content strategy."""
        self.config["default_strategy"] = strategy
        return self
    
    def with_quality(self, quality: ContentQuality) -> 'BlogWriterBuilder':
        """Set default content quality."""
        self.config["default_quality"] = quality
        return self
    
    def with_keyword_analysis(self, enabled: bool = True) -> 'BlogWriterBuilder':
        """Enable or disable keyword analysis."""
        self.config["enable_keyword_analysis"] = enabled
        return self
    
    def with_content_optimization(self, enabled: bool = True) -> 'BlogWriterBuilder':
        """Enable or disable content optimization."""
        self.config["enable_content_optimization"] = enabled
        return self
    
    def with_quality_assurance(self, enabled: bool = True) -> 'BlogWriterBuilder':
        """Enable or disable quality assurance."""
        self.config["enable_quality_assurance"] = enabled
        return self
    
    def with_dataforseo(self, config: Dict[str, Any]) -> 'BlogWriterBuilder':
        """Configure DataForSEO integration."""
        self.config["dataforseo"] = config
        return self
    
    def with_custom_config(self, config: Dict[str, Any]) -> 'BlogWriterBuilder':
        """Add custom configuration."""
        self.config = BlogWriterFactory._merge_configs(self.config, config)
        return self
    
    def build(self) -> BlogWriterAbstraction:
        """Build the Blog Writer instance."""
        return BlogWriterFactory.create_blog_writer(
            custom_config=self.config,
            providers=self.providers if self.providers else None
        )
