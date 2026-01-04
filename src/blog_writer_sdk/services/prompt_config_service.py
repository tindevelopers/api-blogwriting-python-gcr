"""
Service for managing prompt configurations and writing styles.

This service loads, merges, and manages writing configurations from Firestore,
combining global templates with organization-specific overrides and per-blog customizations.
"""

import logging
from typing import Dict, Any, Optional
from ..integrations.firebase_config_client import get_firebase_config_client, FirebaseConfigClient
from ..models.prompt_config_models import (
    PromptTemplate,
    OrganizationWritingConfig,
    BlogOverrideConfig,
    MergedWritingConfig,
    PromptTemplateSettings,
    WritingConfigOverrides
)

logger = logging.getLogger(__name__)


class PromptConfigService:
    """
    Service for managing prompt configurations.
    
    This service handles:
    - Loading prompt templates from Firestore
    - Loading organization writing configurations
    - Loading per-blog overrides
    - Merging configurations with proper priority
    - Converting configurations to instruction text
    """
    
    def __init__(self, firebase_client: Optional[FirebaseConfigClient] = None):
        """
        Initialize prompt config service.
        
        Args:
            firebase_client: Firebase client instance (uses singleton if not provided)
        """
        self.firebase_client = firebase_client or get_firebase_config_client()
        self._default_template: Optional[PromptTemplate] = None
    
    def _get_default_template(self) -> PromptTemplate:
        """
        Get or create default prompt template.
        
        Returns:
            Default prompt template
        """
        if self._default_template is not None:
            return self._default_template
        
        # Try to load default template from Firestore
        templates = self.firebase_client.list_prompt_templates(active_only=True)
        
        if templates:
            # Use the first active template as default
            template_data = templates[0]
            self._default_template = PromptTemplate(
                id=template_data.get('id'),
                name=template_data.get('name', 'Default'),
                description=template_data.get('description', ''),
                category=template_data.get('category', 'tone'),
                settings=PromptTemplateSettings(**template_data.get('settings', {})),
                instruction_text=template_data.get('instruction_text', ''),
                is_active=template_data.get('is_active', True),
                created_by=template_data.get('created_by', 'system')
            )
            logger.info(f"Loaded default template: {self._default_template.name}")
        else:
            # Create a fallback default template
            self._default_template = PromptTemplate(
                name="Natural Conversational (Fallback)",
                description="Default natural conversational writing style",
                category="tone",
                settings=PromptTemplateSettings(),
                instruction_text="Write naturally and conversationally, avoiding obvious AI transitions.",
                is_active=True,
                created_by="system"
            )
            logger.warning("No templates found in Firestore, using fallback default template")
        
        return self._default_template
    
    def get_template_by_id(self, template_id: str) -> Optional[PromptTemplate]:
        """
        Get a specific prompt template by ID.
        
        Args:
            template_id: Template document ID
            
        Returns:
            Prompt template or None if not found
        """
        try:
            template_data = self.firebase_client.get_prompt_template(template_id)
            
            if not template_data:
                logger.warning(f"Template not found: {template_id}")
                return None
            
            return PromptTemplate(
                id=template_data.get('id'),
                name=template_data.get('name', 'Unknown'),
                description=template_data.get('description', ''),
                category=template_data.get('category', 'tone'),
                settings=PromptTemplateSettings(**template_data.get('settings', {})),
                instruction_text=template_data.get('instruction_text', ''),
                is_active=template_data.get('is_active', True),
                created_by=template_data.get('created_by', 'system')
            )
        except Exception as e:
            logger.error(f"Error loading template {template_id}: {e}")
            return None
    
    def get_org_config(self, org_id: str) -> Optional[OrganizationWritingConfig]:
        """
        Get organization writing configuration.
        
        Args:
            org_id: Organization ID
            
        Returns:
            Organization writing config or None if not found
        """
        try:
            config_data = self.firebase_client.get_org_writing_config(org_id)
            
            if not config_data:
                logger.info(f"No org config found for {org_id}, will use default")
                return None
            
            # Parse custom overrides
            custom_overrides_data = config_data.get('custom_overrides', {})
            custom_overrides = WritingConfigOverrides(**custom_overrides_data)
            
            return OrganizationWritingConfig(
                id=config_data.get('id'),
                org_id=config_data.get('org_id'),
                template_id=config_data.get('template_id'),
                custom_overrides=custom_overrides,
                tone_style=config_data.get('tone_style'),
                transition_words=config_data.get('transition_words'),
                formality_level=config_data.get('formality_level'),
                example_style=config_data.get('example_style'),
                updated_by=config_data.get('updated_by', 'system')
            )
        except Exception as e:
            logger.error(f"Error loading org config for {org_id}: {e}")
            return None
    
    def get_blog_override(self, blog_id: str) -> Optional[BlogOverrideConfig]:
        """
        Get per-blog configuration override.
        
        Args:
            blog_id: Blog generation job ID
            
        Returns:
            Blog override config or None if not found
        """
        try:
            override_data = self.firebase_client.get_blog_override(blog_id)
            
            if not override_data:
                return None
            
            # Parse config overrides
            config_overrides_data = override_data.get('config_overrides', {})
            config_overrides = WritingConfigOverrides(**config_overrides_data)
            
            return BlogOverrideConfig(
                id=override_data.get('id'),
                org_id=override_data.get('org_id'),
                config_overrides=config_overrides
            )
        except Exception as e:
            logger.error(f"Error loading blog override for {blog_id}: {e}")
            return None
    
    def merge_configs(
        self,
        template: PromptTemplate,
        org_config: Optional[OrganizationWritingConfig] = None,
        blog_override: Optional[BlogOverrideConfig] = None
    ) -> MergedWritingConfig:
        """
        Merge configurations with proper priority.
        
        Priority (highest to lowest):
        1. Blog override
        2. Organization config
        3. Template settings
        
        Args:
            template: Base template
            org_config: Organization config (optional)
            blog_override: Per-blog override (optional)
            
        Returns:
            Merged writing configuration
        """
        # Start with template settings
        merged = MergedWritingConfig(
            formality_level=template.settings.formality_level,
            use_contractions=template.settings.use_contractions,
            avoid_obvious_transitions=template.settings.avoid_obvious_transitions,
            transition_blocklist=template.settings.transition_blocklist.copy(),
            preferred_transitions=template.settings.preferred_transitions.copy(),
            sentence_variety=template.settings.sentence_variety,
            conclusion_style=template.settings.conclusion_style,
            engagement_style=template.settings.engagement_style,
            use_first_person=template.settings.use_first_person,
            personality=template.settings.personality,
            heading_style=template.settings.heading_style,
            example_style=template.settings.example_style,
            custom_instructions=template.settings.custom_instructions
        )
        
        # Apply organization config overrides
        if org_config:
            overrides = org_config.custom_overrides
            if overrides.formality_level is not None:
                merged.formality_level = overrides.formality_level
            if overrides.use_contractions is not None:
                merged.use_contractions = overrides.use_contractions
            if overrides.avoid_obvious_transitions is not None:
                merged.avoid_obvious_transitions = overrides.avoid_obvious_transitions
            if overrides.transition_blocklist is not None:
                merged.transition_blocklist = overrides.transition_blocklist
            if overrides.preferred_transitions is not None:
                merged.preferred_transitions = overrides.preferred_transitions
            if overrides.sentence_variety is not None:
                merged.sentence_variety = overrides.sentence_variety
            if overrides.conclusion_style is not None:
                merged.conclusion_style = overrides.conclusion_style
            if overrides.engagement_style is not None:
                merged.engagement_style = overrides.engagement_style
            if overrides.use_first_person is not None:
                merged.use_first_person = overrides.use_first_person
            if overrides.personality is not None:
                merged.personality = overrides.personality
            if overrides.heading_style is not None:
                merged.heading_style = overrides.heading_style
            if overrides.example_style is not None:
                merged.example_style = overrides.example_style
            if overrides.custom_instructions is not None:
                merged.custom_instructions = overrides.custom_instructions
        
        # Apply per-blog overrides (highest priority)
        if blog_override:
            overrides = blog_override.config_overrides
            if overrides.formality_level is not None:
                merged.formality_level = overrides.formality_level
            if overrides.use_contractions is not None:
                merged.use_contractions = overrides.use_contractions
            if overrides.avoid_obvious_transitions is not None:
                merged.avoid_obvious_transitions = overrides.avoid_obvious_transitions
            if overrides.transition_blocklist is not None:
                merged.transition_blocklist = overrides.transition_blocklist
            if overrides.preferred_transitions is not None:
                merged.preferred_transitions = overrides.preferred_transitions
            if overrides.sentence_variety is not None:
                merged.sentence_variety = overrides.sentence_variety
            if overrides.conclusion_style is not None:
                merged.conclusion_style = overrides.conclusion_style
            if overrides.engagement_style is not None:
                merged.engagement_style = overrides.engagement_style
            if overrides.use_first_person is not None:
                merged.use_first_person = overrides.use_first_person
            if overrides.personality is not None:
                merged.personality = overrides.personality
            if overrides.heading_style is not None:
                merged.heading_style = overrides.heading_style
            if overrides.example_style is not None:
                merged.example_style = overrides.example_style
            if overrides.custom_instructions is not None:
                # Append blog-specific custom instructions
                if merged.custom_instructions:
                    merged.custom_instructions += f"\n\n{overrides.custom_instructions}"
                else:
                    merged.custom_instructions = overrides.custom_instructions
        
        return merged
    
    def get_writing_config(
        self,
        org_id: Optional[str] = None,
        blog_id: Optional[str] = None,
        template_id: Optional[str] = None
    ) -> MergedWritingConfig:
        """
        Get merged writing configuration for blog generation.
        
        This method loads and merges configurations in the following priority:
        1. Blog-specific override (highest)
        2. Organization config
        3. Template settings (lowest)
        
        Args:
            org_id: Organization ID
            blog_id: Blog generation job ID
            template_id: Specific template ID to use (optional)
            
        Returns:
            Merged writing configuration
        """
        # Load base template
        if template_id:
            template = self.get_template_by_id(template_id)
            if not template:
                logger.warning(f"Template {template_id} not found, using default")
                template = self._get_default_template()
        else:
            # Load org config to see if it references a template
            org_config = self.get_org_config(org_id) if org_id else None
            
            if org_config and org_config.template_id:
                template = self.get_template_by_id(org_config.template_id)
                if not template:
                    logger.warning(f"Org template {org_config.template_id} not found, using default")
                    template = self._get_default_template()
            else:
                template = self._get_default_template()
        
        # Load organization config
        org_config = self.get_org_config(org_id) if org_id else None
        
        # Load blog override
        blog_override = self.get_blog_override(blog_id) if blog_id else None
        
        # Merge configurations
        merged_config = self.merge_configs(template, org_config, blog_override)
        
        logger.info(f"Merged writing config for org={org_id}, blog={blog_id}, template={template.name}")
        return merged_config
    
    def get_instruction_text(
        self,
        org_id: Optional[str] = None,
        blog_id: Optional[str] = None,
        template_id: Optional[str] = None
    ) -> str:
        """
        Get formatted instruction text for blog generation.
        
        Args:
            org_id: Organization ID
            blog_id: Blog generation job ID
            template_id: Specific template ID to use (optional)
            
        Returns:
            Formatted instruction text ready for prompt injection
        """
        merged_config = self.get_writing_config(org_id, blog_id, template_id)
        return merged_config.to_instruction_text()


# Singleton instance
_config_service: Optional[PromptConfigService] = None


def get_prompt_config_service() -> PromptConfigService:
    """Get singleton prompt config service instance."""
    global _config_service
    if _config_service is None:
        _config_service = PromptConfigService()
    return _config_service


def initialize_prompt_config_service(
    firebase_client: Optional[FirebaseConfigClient] = None
) -> PromptConfigService:
    """
    Initialize prompt config service with custom settings.
    
    Args:
        firebase_client: Firebase client instance
        
    Returns:
        Initialized prompt config service
    """
    global _config_service
    _config_service = PromptConfigService(firebase_client)
    return _config_service




