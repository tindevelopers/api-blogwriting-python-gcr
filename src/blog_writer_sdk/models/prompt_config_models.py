"""
Pydantic models for prompt templates and writing configurations.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class PromptTemplateSettings(BaseModel):
    """Settings for a prompt template."""
    formality_level: int = Field(default=6, ge=1, le=10, description="Writing formality (1=casual, 10=formal)")
    use_contractions: bool = Field(default=True, description="Allow contractions (it's, don't)")
    avoid_obvious_transitions: bool = Field(default=True, description="Block AI-obvious transition words")
    transition_blocklist: List[str] = Field(
        default_factory=lambda: [
            "In conclusion",
            "Moreover",
            "Furthermore",
            "Additionally",
            "In summary"
        ],
        description="Phrases to avoid"
    )
    preferred_transitions: List[str] = Field(
        default_factory=lambda: [
            "Here's the thing",
            "So",
            "Now",
            "The bottom line",
            "What this means"
        ],
        description="Recommended transitions"
    )
    sentence_variety: bool = Field(default=True, description="Mix short and long sentences")
    conclusion_style: str = Field(default="natural_wrap_up", description="How to end blog")
    engagement_style: str = Field(default="conversational", description="Reader engagement approach")
    use_first_person: bool = Field(default=False, description="Use first-person voice")
    personality: str = Field(default="friendly", description="Writing personality")
    heading_style: str = Field(default="statements", description="H2 heading format")
    example_style: str = Field(default="mixed", description="Example specificity")
    custom_instructions: str = Field(default="", description="Additional instructions")


class PromptTemplate(BaseModel):
    """A prompt template document."""
    id: Optional[str] = None
    name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template description")
    category: str = Field(..., description="Category (tone, structure, style)")
    settings: PromptTemplateSettings = Field(..., description="Template settings")
    instruction_text: str = Field(..., description="Compiled instruction text")
    is_active: bool = Field(default=True, description="Whether template is active")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: str = Field(default="system", description="User who created the template")


class WritingConfigOverrides(BaseModel):
    """Organization or blog-specific configuration overrides."""
    formality_level: Optional[int] = Field(None, ge=1, le=10)
    use_contractions: Optional[bool] = None
    avoid_obvious_transitions: Optional[bool] = None
    transition_blocklist: Optional[List[str]] = None
    preferred_transitions: Optional[List[str]] = None
    sentence_variety: Optional[bool] = None
    conclusion_style: Optional[str] = None
    engagement_style: Optional[str] = None
    use_first_person: Optional[bool] = None
    personality: Optional[str] = None
    heading_style: Optional[str] = None
    example_style: Optional[str] = None
    custom_instructions: Optional[str] = None


class OrganizationWritingConfig(BaseModel):
    """Organization-specific writing configuration."""
    id: Optional[str] = None
    org_id: Optional[str] = None
    template_id: Optional[str] = Field(None, description="Reference to prompt_templates")
    custom_overrides: WritingConfigOverrides = Field(
        default_factory=WritingConfigOverrides,
        description="Overrides to apply"
    )
    tone_style: Optional[str] = Field(None, description="Organization tone preference")
    transition_words: Optional[List[str]] = Field(None, description="Custom transition words")
    formality_level: Optional[int] = Field(None, ge=1, le=10)
    example_style: Optional[str] = None
    updated_at: Optional[datetime] = None
    updated_by: str = Field(default="system", description="User who updated the config")


class BlogOverrideConfig(BaseModel):
    """Per-blog configuration overrides."""
    id: Optional[str] = None
    org_id: str = Field(..., description="Organization ID")
    config_overrides: WritingConfigOverrides = Field(
        default_factory=WritingConfigOverrides,
        description="Configuration overrides"
    )
    created_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class MergedWritingConfig(BaseModel):
    """Merged writing configuration after applying all overrides."""
    formality_level: int = 6
    use_contractions: bool = True
    avoid_obvious_transitions: bool = True
    transition_blocklist: List[str] = Field(default_factory=list)
    preferred_transitions: List[str] = Field(default_factory=list)
    sentence_variety: bool = True
    conclusion_style: str = "natural_wrap_up"
    engagement_style: str = "conversational"
    use_first_person: bool = False
    personality: str = "friendly"
    heading_style: str = "statements"
    example_style: str = "mixed"
    custom_instructions: str = ""
    
    def to_instruction_text(self) -> str:
        """
        Convert merged config to instruction text that can be injected into prompts.
        
        Returns:
            Formatted instruction text
        """
        instructions = []
        
        # Formality
        if self.formality_level <= 3:
            instructions.append("Write in a very casual, conversational tone.")
        elif self.formality_level <= 6:
            instructions.append("Write in a balanced, professional yet friendly tone.")
        else:
            instructions.append("Write in a formal, authoritative tone.")
        
        # Contractions
        if self.use_contractions:
            instructions.append("Use contractions naturally (it's, don't, we'll, can't, won't).")
        else:
            instructions.append("Avoid contractions. Use full forms (it is, do not, we will).")
        
        # Transitions
        if self.avoid_obvious_transitions:
            instructions.append(
                f"AVOID these obvious AI transition words: {', '.join(self.transition_blocklist)}"
            )
            if self.preferred_transitions:
                instructions.append(
                    f"Instead, use natural transitions: {', '.join(self.preferred_transitions)}"
                )
        
        # Sentence variety
        if self.sentence_variety:
            instructions.append("Vary sentence length - mix short punchy sentences with longer explanatory ones.")
        
        # Conclusion style
        conclusion_styles = {
            "natural_wrap_up": "End with a natural wrap-up, not formulaic conclusion phrases.",
            "summary": "End with a summary of key points.",
            "call_to_action": "End with a strong call-to-action.",
            "open_ended": "End with an open-ended question or thought."
        }
        if self.conclusion_style in conclusion_styles:
            instructions.append(conclusion_styles[self.conclusion_style])
        
        # Engagement style
        engagement_styles = {
            "conversational": "Write like you're explaining to a friend over coffee.",
            "professional": "Maintain a professional yet friendly tone throughout.",
            "authoritative": "Write with expert authority and confidence.",
            "analytical": "Use a data-driven, analytical approach."
        }
        if self.engagement_style in engagement_styles:
            instructions.append(engagement_styles[self.engagement_style])
        
        # First person
        if self.use_first_person:
            instructions.append("Use first-person voice (I, we) naturally where appropriate.")
        else:
            instructions.append("Avoid first-person voice. Use second-person (you) or third-person.")
        
        # Personality
        personality_styles = {
            "friendly": "Write in a warm, approachable manner.",
            "authoritative": "Demonstrate expertise and authority.",
            "analytical": "Use logical, structured reasoning.",
            "conversational": "Keep it casual and relatable."
        }
        if self.personality in personality_styles:
            instructions.append(personality_styles[self.personality])
        
        # Custom instructions
        if self.custom_instructions:
            instructions.append(f"\nADDITIONAL INSTRUCTIONS:\n{self.custom_instructions}")
        
        return "\n".join(instructions)


class PromptConfigRequest(BaseModel):
    """Request model for creating/updating prompt configurations."""
    name: str
    description: str
    category: str
    settings: Dict[str, Any]
    instruction_text: Optional[str] = None


class WritingStyleUpdateRequest(BaseModel):
    """Request model for updating organization writing style."""
    template_id: Optional[str] = None
    custom_overrides: Optional[Dict[str, Any]] = None
    tone_style: Optional[str] = None
    transition_words: Optional[List[str]] = None
    formality_level: Optional[int] = Field(None, ge=1, le=10)
    example_style: Optional[str] = None




