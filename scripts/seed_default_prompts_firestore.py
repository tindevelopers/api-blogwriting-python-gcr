#!/usr/bin/env python3
"""
Seed default prompt templates in Firestore.

This script creates the default "Natural Conversational" prompt template
in Firestore for the Blog Writer system.

Usage:
    python scripts/seed_default_prompts_firestore.py

Environment Variables:
    FIREBASE_PROJECT_ID or GOOGLE_CLOUD_PROJECT - Google Cloud project ID
    FIREBASE_CREDENTIALS_JSON (optional) - Service account JSON
    GOOGLE_APPLICATION_CREDENTIALS (optional) - Path to service account JSON file
"""

import os
import sys
import logging

# Add parent directory to path to import SDK modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.blog_writer_sdk.integrations.firebase_config_client import FirebaseConfigClient
from src.blog_writer_sdk.models.prompt_config_models import MergedWritingConfig

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_default_template(firebase_client: FirebaseConfigClient) -> str:
    """
    Create the default "Natural Conversational" prompt template.
    
    Args:
        firebase_client: Initialized Firebase config client
        
    Returns:
        Template document ID
    """
    # Default template settings
    settings = {
        "formality_level": 6,
        "use_contractions": True,
        "avoid_obvious_transitions": True,
        "transition_blocklist": [
            "In conclusion",
            "Moreover",
            "Furthermore",
            "Additionally",
            "In summary",
            "It is important to note that",
            "It should be mentioned that",
            "Last but not least",
            "To sum up",
            "In closing"
        ],
        "preferred_transitions": [
            "Here's the thing",
            "So",
            "Now",
            "The bottom line",
            "What this means",
            "Think about it",
            "Let's be honest"
        ],
        "sentence_variety": True,
        "conclusion_style": "natural_wrap_up",
        "engagement_style": "conversational",
        "use_first_person": False,
        "personality": "friendly",
        "heading_style": "statements",
        "example_style": "mixed",
        "custom_instructions": ""
    }
    
    # Generate instruction text
    merged_config = MergedWritingConfig(**settings)
    instruction_text = merged_config.to_instruction_text()
    
    # Create template in Firestore
    template_id = firebase_client.create_prompt_template(
        name="Natural Conversational (Default)",
        description=(
            "Default writing style that produces natural, human-sounding content. "
            "Avoids obvious AI transitions and writes conversationally. "
            "Perfect for most blog content."
        ),
        category="tone",
        settings=settings,
        instruction_text=instruction_text,
        created_by="system"
    )
    
    if template_id:
        logger.info(f"✅ Created default template with ID: {template_id}")
        logger.info(f"   Name: Natural Conversational (Default)")
        logger.info(f"   Category: tone")
        logger.info(f"   Settings: {len(settings)} configuration options")
    else:
        logger.error("❌ Failed to create default template")
    
    return template_id


def create_formal_template(firebase_client: FirebaseConfigClient) -> str:
    """
    Create a "Formal Professional" prompt template.
    
    Args:
        firebase_client: Initialized Firebase config client
        
    Returns:
        Template document ID
    """
    settings = {
        "formality_level": 9,
        "use_contractions": False,
        "avoid_obvious_transitions": False,
        "transition_blocklist": [],
        "preferred_transitions": [
            "Moreover",
            "Furthermore",
            "Additionally",
            "Therefore",
            "Consequently"
        ],
        "sentence_variety": True,
        "conclusion_style": "summary",
        "engagement_style": "professional",
        "use_first_person": False,
        "personality": "authoritative",
        "heading_style": "statements",
        "example_style": "specific_brands",
        "custom_instructions": ""
    }
    
    merged_config = MergedWritingConfig(**settings)
    instruction_text = merged_config.to_instruction_text()
    
    template_id = firebase_client.create_prompt_template(
        name="Formal Professional",
        description=(
            "Formal, authoritative writing style for business and enterprise content. "
            "Uses complete sentences without contractions. "
            "Ideal for white papers, case studies, and professional reports."
        ),
        category="tone",
        settings=settings,
        instruction_text=instruction_text,
        created_by="system"
    )
    
    if template_id:
        logger.info(f"✅ Created formal template with ID: {template_id}")
    else:
        logger.error("❌ Failed to create formal template")
    
    return template_id


def create_casual_template(firebase_client: FirebaseConfigClient) -> str:
    """
    Create a "Casual Friendly" prompt template.
    
    Args:
        firebase_client: Initialized Firebase config client
        
    Returns:
        Template document ID
    """
    settings = {
        "formality_level": 3,
        "use_contractions": True,
        "avoid_obvious_transitions": True,
        "transition_blocklist": [
            "In conclusion",
            "Moreover",
            "Furthermore",
            "Additionally",
            "In summary",
            "Nevertheless",
            "Notwithstanding"
        ],
        "preferred_transitions": [
            "So",
            "Now",
            "Here's the deal",
            "Look",
            "Honestly",
            "Real talk"
        ],
        "sentence_variety": True,
        "conclusion_style": "natural_wrap_up",
        "engagement_style": "conversational",
        "use_first_person": True,
        "personality": "friendly",
        "heading_style": "statements",
        "example_style": "mixed",
        "custom_instructions": ""
    }
    
    merged_config = MergedWritingConfig(**settings)
    instruction_text = merged_config.to_instruction_text()
    
    template_id = firebase_client.create_prompt_template(
        name="Casual Friendly",
        description=(
            "Very casual, approachable writing style with first-person voice. "
            "Feels like talking to a friend. "
            "Great for lifestyle blogs, personal stories, and community content."
        ),
        category="tone",
        settings=settings,
        instruction_text=instruction_text,
        created_by="system"
    )
    
    if template_id:
        logger.info(f"✅ Created casual template with ID: {template_id}")
    else:
        logger.error("❌ Failed to create casual template")
    
    return template_id


def main():
    """Main function to seed default prompt templates."""
    logger.info("🌱 Starting Firestore prompt template seeding...")
    
    # Get project ID
    project_id = os.getenv("FIREBASE_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        logger.error("❌ FIREBASE_PROJECT_ID or GOOGLE_CLOUD_PROJECT environment variable required")
        sys.exit(1)
    
    logger.info(f"📦 Using Firebase project: {project_id}")
    
    # Initialize Firebase client
    try:
        firebase_client = FirebaseConfigClient(project_id=project_id)
        logger.info("✅ Firebase client initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Firebase client: {e}")
        sys.exit(1)
    
    # Check existing templates
    existing_templates = firebase_client.list_prompt_templates(active_only=False)
    logger.info(f"📊 Found {len(existing_templates)} existing templates")
    
    # Create default templates
    templates_created = []
    
    logger.info("\n📝 Creating default templates...")
    
    # 1. Natural Conversational (Default)
    template_id = create_default_template(firebase_client)
    if template_id:
        templates_created.append(("Natural Conversational", template_id))
    
    # 2. Formal Professional
    template_id = create_formal_template(firebase_client)
    if template_id:
        templates_created.append(("Formal Professional", template_id))
    
    # 3. Casual Friendly
    template_id = create_casual_template(firebase_client)
    if template_id:
        templates_created.append(("Casual Friendly", template_id))
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("✅ Seeding completed!")
    logger.info(f"   Templates created: {len(templates_created)}")
    for name, tid in templates_created:
        logger.info(f"   - {name}: {tid}")
    logger.info("="*60)
    
    # Verify
    all_templates = firebase_client.list_prompt_templates(active_only=True)
    logger.info(f"\n📊 Total active templates in Firestore: {len(all_templates)}")
    
    return len(templates_created)


if __name__ == "__main__":
    try:
        count = main()
        sys.exit(0 if count > 0 else 1)
    except Exception as e:
        logger.error(f"❌ Script failed: {e}", exc_info=True)
        sys.exit(1)




