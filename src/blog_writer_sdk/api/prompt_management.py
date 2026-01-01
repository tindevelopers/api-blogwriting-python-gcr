"""
API endpoints for prompt template and writing configuration management.

These endpoints allow dashboard administrators to:
- Create, read, update prompt templates
- Manage organization writing configurations
- Save per-blog configuration overrides
"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, Field

from ..services.prompt_config_service import get_prompt_config_service, PromptConfigService
from ..integrations.firebase_config_client import get_firebase_config_client, FirebaseConfigClient
from ..models.prompt_config_models import (
    PromptTemplate,
    PromptTemplateSettings,
    OrganizationWritingConfig,
    WritingConfigOverrides,
    PromptConfigRequest,
    WritingStyleUpdateRequest,
    MergedWritingConfig
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/prompts", tags=["Prompt Management"])


# Dependency to get services
def get_config_service() -> PromptConfigService:
    """Dependency to get prompt config service."""
    return get_prompt_config_service()


def get_firebase_client() -> FirebaseConfigClient:
    """Dependency to get Firebase client."""
    return get_firebase_config_client()


# ======================================================================
# PROMPT TEMPLATES
# ======================================================================

@router.get("/templates", response_model=List[Dict[str, Any]])
async def list_prompt_templates(
    active_only: bool = True,
    category: Optional[str] = None,
    firebase_client: FirebaseConfigClient = Depends(get_firebase_client)
):
    """
    List all prompt templates.
    
    Args:
        active_only: Only return active templates
        category: Filter by category (tone, structure, style)
        
    Returns:
        List of prompt templates
    """
    try:
        templates = firebase_client.list_prompt_templates(
            active_only=active_only,
            category=category
        )
        
        logger.info(f"Retrieved {len(templates)} prompt templates")
        return templates
    except Exception as e:
        logger.error(f"Error listing prompt templates: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list templates: {str(e)}")


@router.get("/templates/{template_id}", response_model=Dict[str, Any])
async def get_prompt_template(
    template_id: str,
    firebase_client: FirebaseConfigClient = Depends(get_firebase_client)
):
    """
    Get a specific prompt template by ID.
    
    Args:
        template_id: Template document ID
        
    Returns:
        Prompt template document
    """
    try:
        template = firebase_client.get_prompt_template(template_id)
        
        if not template:
            raise HTTPException(status_code=404, detail=f"Template not found: {template_id}")
        
        logger.info(f"Retrieved template: {template_id}")
        return template
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving template {template_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve template: {str(e)}")


@router.post("/templates", response_model=Dict[str, str])
async def create_prompt_template(
    request: PromptConfigRequest,
    firebase_client: FirebaseConfigClient = Depends(get_firebase_client),
    # TODO: Add authentication and admin check
    # current_user: str = Depends(get_current_user)
):
    """
    Create a new prompt template (admin only).
    
    Args:
        request: Template creation request
        
    Returns:
        Created template ID
    """
    try:
        # Generate instruction text if not provided
        instruction_text = request.instruction_text
        if not instruction_text:
            # Convert settings to instruction text
            settings = PromptTemplateSettings(**request.settings)
            merged_config = MergedWritingConfig(
                formality_level=settings.formality_level,
                use_contractions=settings.use_contractions,
                avoid_obvious_transitions=settings.avoid_obvious_transitions,
                transition_blocklist=settings.transition_blocklist,
                preferred_transitions=settings.preferred_transitions,
                sentence_variety=settings.sentence_variety,
                conclusion_style=settings.conclusion_style,
                engagement_style=settings.engagement_style,
                use_first_person=settings.use_first_person,
                personality=settings.personality,
                heading_style=settings.heading_style,
                example_style=settings.example_style,
                custom_instructions=settings.custom_instructions
            )
            instruction_text = merged_config.to_instruction_text()
        
        template_id = firebase_client.create_prompt_template(
            name=request.name,
            description=request.description,
            category=request.category,
            settings=request.settings,
            instruction_text=instruction_text,
            created_by="admin"  # TODO: Use actual user from auth
        )
        
        if not template_id:
            raise HTTPException(status_code=500, detail="Failed to create template")
        
        logger.info(f"Created template: {template_id}")
        return {"template_id": template_id, "message": "Template created successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating template: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create template: {str(e)}")


@router.put("/templates/{template_id}", response_model=Dict[str, str])
async def update_prompt_template(
    template_id: str,
    updates: Dict[str, Any],
    firebase_client: FirebaseConfigClient = Depends(get_firebase_client),
    # TODO: Add authentication and admin check
    # current_user: str = Depends(get_current_user)
):
    """
    Update an existing prompt template (admin only).
    
    Args:
        template_id: Template document ID
        updates: Fields to update
        
    Returns:
        Success message
    """
    try:
        # If settings are updated, regenerate instruction text
        if 'settings' in updates and 'instruction_text' not in updates:
            settings = PromptTemplateSettings(**updates['settings'])
            merged_config = MergedWritingConfig(
                formality_level=settings.formality_level,
                use_contractions=settings.use_contractions,
                avoid_obvious_transitions=settings.avoid_obvious_transitions,
                transition_blocklist=settings.transition_blocklist,
                preferred_transitions=settings.preferred_transitions,
                sentence_variety=settings.sentence_variety,
                conclusion_style=settings.conclusion_style,
                engagement_style=settings.engagement_style,
                use_first_person=settings.use_first_person,
                personality=settings.personality,
                heading_style=settings.heading_style,
                example_style=settings.example_style,
                custom_instructions=settings.custom_instructions
            )
            updates['instruction_text'] = merged_config.to_instruction_text()
        
        success = firebase_client.update_prompt_template(template_id, updates)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update template")
        
        logger.info(f"Updated template: {template_id}")
        return {"message": "Template updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating template {template_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update template: {str(e)}")


# ======================================================================
# ORGANIZATION WRITING CONFIGURATION
# ======================================================================

@router.get("/config/writing-style/{org_id}", response_model=Dict[str, Any])
async def get_organization_writing_config(
    org_id: str,
    config_service: PromptConfigService = Depends(get_config_service)
):
    """
    Get organization writing configuration.
    
    Args:
        org_id: Organization ID
        
    Returns:
        Organization writing configuration
    """
    try:
        org_config = config_service.get_org_config(org_id)
        
        if not org_config:
            # Return default configuration
            default_template = config_service._get_default_template()
            return {
                "org_id": org_id,
                "template_id": default_template.id,
                "custom_overrides": {},
                "message": "Using default configuration"
            }
        
        logger.info(f"Retrieved writing config for org: {org_id}")
        return org_config.model_dump()
    except Exception as e:
        logger.error(f"Error retrieving org config for {org_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve config: {str(e)}")


@router.put("/config/writing-style/{org_id}", response_model=Dict[str, str])
async def update_organization_writing_config(
    org_id: str,
    request: WritingStyleUpdateRequest,
    firebase_client: FirebaseConfigClient = Depends(get_firebase_client),
    # TODO: Add authentication and org membership check
    # current_user: str = Depends(get_current_user)
):
    """
    Update organization writing configuration.
    
    Args:
        org_id: Organization ID
        request: Writing style update request
        
    Returns:
        Success message
    """
    try:
        # Prepare config data
        config_data = {}
        
        if request.template_id:
            config_data['template_id'] = request.template_id
        
        if request.custom_overrides:
            config_data['custom_overrides'] = request.custom_overrides
        
        if request.tone_style:
            config_data['tone_style'] = request.tone_style
        
        if request.transition_words:
            config_data['transition_words'] = request.transition_words
        
        if request.formality_level:
            config_data['formality_level'] = request.formality_level
        
        if request.example_style:
            config_data['example_style'] = request.example_style
        
        success = firebase_client.save_org_writing_config(
            org_id=org_id,
            config=config_data,
            updated_by="admin"  # TODO: Use actual user from auth
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update config")
        
        logger.info(f"Updated writing config for org: {org_id}")
        return {"message": "Writing config updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating org config for {org_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update config: {str(e)}")


# ======================================================================
# MERGED CONFIGURATION (FOR BLOG GENERATION)
# ======================================================================

@router.get("/config/merged", response_model=Dict[str, Any])
async def get_merged_writing_config(
    org_id: Optional[str] = None,
    blog_id: Optional[str] = None,
    template_id: Optional[str] = None,
    config_service: PromptConfigService = Depends(get_config_service)
):
    """
    Get merged writing configuration for blog generation.
    
    This endpoint returns the final configuration after merging:
    - Base template
    - Organization overrides
    - Blog-specific overrides
    
    Args:
        org_id: Organization ID
        blog_id: Blog generation job ID
        template_id: Specific template ID to use
        
    Returns:
        Merged writing configuration
    """
    try:
        merged_config = config_service.get_writing_config(
            org_id=org_id,
            blog_id=blog_id,
            template_id=template_id
        )
        
        logger.info(f"Retrieved merged config for org={org_id}, blog={blog_id}")
        return merged_config.model_dump()
    except Exception as e:
        logger.error(f"Error retrieving merged config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve merged config: {str(e)}")


@router.get("/config/instruction-text", response_model=Dict[str, str])
async def get_instruction_text(
    org_id: Optional[str] = None,
    blog_id: Optional[str] = None,
    template_id: Optional[str] = None,
    config_service: PromptConfigService = Depends(get_config_service)
):
    """
    Get formatted instruction text for blog generation.
    
    Args:
        org_id: Organization ID
        blog_id: Blog generation job ID
        template_id: Specific template ID to use
        
    Returns:
        Formatted instruction text
    """
    try:
        instruction_text = config_service.get_instruction_text(
            org_id=org_id,
            blog_id=blog_id,
            template_id=template_id
        )
        
        logger.info(f"Generated instruction text for org={org_id}, blog={blog_id}")
        return {"instruction_text": instruction_text}
    except Exception as e:
        logger.error(f"Error generating instruction text: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate instruction text: {str(e)}")


# ======================================================================
# BLOG-SPECIFIC OVERRIDES
# ======================================================================

class BlogOverrideRequest(BaseModel):
    """Request model for saving blog-specific overrides."""
    org_id: str = Field(..., description="Organization ID")
    config_overrides: Dict[str, Any] = Field(..., description="Configuration overrides")
    ttl_days: int = Field(default=7, ge=1, le=30, description="Days until expiration")


@router.post("/config/blog-override/{blog_id}", response_model=Dict[str, str])
async def save_blog_override(
    blog_id: str,
    request: BlogOverrideRequest,
    firebase_client: FirebaseConfigClient = Depends(get_firebase_client)
):
    """
    Save per-blog configuration override.
    
    Args:
        blog_id: Blog generation job ID
        request: Blog override request
        
    Returns:
        Success message
    """
    try:
        success = firebase_client.save_blog_override(
            blog_id=blog_id,
            org_id=request.org_id,
            config_overrides=request.config_overrides,
            ttl_days=request.ttl_days
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save blog override")
        
        logger.info(f"Saved blog override for blog: {blog_id}")
        return {"message": "Blog override saved successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving blog override for {blog_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save blog override: {str(e)}")


@router.delete("/config/blog-override/{blog_id}", response_model=Dict[str, str])
async def delete_blog_override(
    blog_id: str,
    firebase_client: FirebaseConfigClient = Depends(get_firebase_client)
):
    """
    Delete per-blog configuration override.
    
    Args:
        blog_id: Blog generation job ID
        
    Returns:
        Success message
    """
    try:
        success = firebase_client.delete_blog_override(blog_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete blog override")
        
        logger.info(f"Deleted blog override for blog: {blog_id}")
        return {"message": "Blog override deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting blog override for {blog_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete blog override: {str(e)}")

