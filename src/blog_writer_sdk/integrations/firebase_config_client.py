"""
Firebase/Firestore client for managing prompt templates and writing configurations.

This module provides a client for interacting with Firestore to store and retrieve
blog generation configurations, prompt templates, and organization-specific settings.
"""

import os
import json
import base64
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    from google.cloud.firestore_v1.base_query import FieldFilter
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    logging.warning("firebase-admin package not installed. Firebase functionality will be disabled.")

logger = logging.getLogger(__name__)


class FirebaseConfigClient:
    """
    Client for managing blog writing configurations in Firestore.
    
    This client handles:
    - Prompt templates (global instruction sets)
    - Organization writing configs (per-org defaults)
    - Blog generation overrides (per-blog temporary configs)
    """
    
    def __init__(
        self,
        project_id: Optional[str] = None,
        credentials_json: Optional[str] = None,
        credentials_path: Optional[str] = None
    ):
        """
        Initialize Firebase config client.
        
        Args:
            project_id: Google Cloud project ID (defaults to FIREBASE_PROJECT_ID env var)
            credentials_json: Service account JSON as string or base64 encoded
            credentials_path: Path to service account JSON file
        """
        if not FIREBASE_AVAILABLE:
            raise ImportError(
                "firebase-admin package is required. "
                "Install with: pip install firebase-admin"
            )
        
        self.project_id = project_id or os.getenv("FIREBASE_PROJECT_ID")
        self.db = None
        self._initialize_firebase(credentials_json, credentials_path)
    
    def _initialize_firebase(
        self,
        credentials_json: Optional[str] = None,
        credentials_path: Optional[str] = None
    ):
        """Initialize Firebase Admin SDK."""
        try:
            # Check if already initialized
            firebase_admin.get_app()
            logger.info("Firebase already initialized, using existing app")
            self.db = firestore.client()
            return
        except ValueError:
            # Not initialized, proceed with initialization
            pass
        
        cred = None
        
        # Try to load credentials from provided JSON string
        if credentials_json:
            try:
                # Try to decode if base64 encoded
                try:
                    decoded = base64.b64decode(credentials_json)
                    cred_dict = json.loads(decoded)
                except Exception:
                    # Not base64, try as plain JSON
                    cred_dict = json.loads(credentials_json)
                
                cred = credentials.Certificate(cred_dict)
                logger.info("Loaded credentials from JSON string")
            except Exception as e:
                logger.error(f"Failed to load credentials from JSON string: {e}")
        
        # Try to load credentials from file path
        elif credentials_path:
            if os.path.exists(credentials_path):
                cred = credentials.Certificate(credentials_path)
                logger.info(f"Loaded credentials from file: {credentials_path}")
            else:
                logger.error(f"Credentials file not found: {credentials_path}")
        
        # Try environment variable
        elif os.getenv("FIREBASE_CREDENTIALS_JSON"):
            try:
                cred_json = os.getenv("FIREBASE_CREDENTIALS_JSON")
                try:
                    decoded = base64.b64decode(cred_json)
                    cred_dict = json.loads(decoded)
                except Exception:
                    cred_dict = json.loads(cred_json)
                
                cred = credentials.Certificate(cred_dict)
                logger.info("Loaded credentials from FIREBASE_CREDENTIALS_JSON env var")
            except Exception as e:
                logger.error(f"Failed to load credentials from environment: {e}")
        
        elif os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            if os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                logger.info(f"Loaded credentials from GOOGLE_APPLICATION_CREDENTIALS: {cred_path}")
        
        # Initialize with credentials or use default (for GCR with service account)
        if cred:
            firebase_admin.initialize_app(cred, {
                'projectId': self.project_id,
            })
        else:
            # Use default credentials (works on GCR with service account)
            firebase_admin.initialize_app(options={
                'projectId': self.project_id,
            })
            logger.info("Initialized Firebase with default credentials")
        
        self.db = firestore.client()
        logger.info(f"Firebase initialized successfully for project: {self.project_id}")
    
    # ======================================================================
    # PROMPT TEMPLATES
    # ======================================================================
    
    def get_prompt_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific prompt template by ID.
        
        Args:
            template_id: Document ID of the template
            
        Returns:
            Template document as dict, or None if not found
        """
        try:
            doc_ref = self.db.collection('prompt_templates').document(template_id)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                data['id'] = doc.id
                logger.info(f"Retrieved prompt template: {template_id}")
                return data
            else:
                logger.warning(f"Prompt template not found: {template_id}")
                return None
        except Exception as e:
            logger.error(f"Error retrieving prompt template {template_id}: {e}")
            return None
    
    def list_prompt_templates(
        self,
        active_only: bool = True,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List all prompt templates.
        
        Args:
            active_only: Only return active templates
            category: Filter by category (tone, structure, style)
            
        Returns:
            List of template documents
        """
        try:
            query = self.db.collection('prompt_templates')
            
            if active_only:
                query = query.where(filter=FieldFilter('is_active', '==', True))
            
            if category:
                query = query.where(filter=FieldFilter('category', '==', category))
            
            query = query.order_by('created_at', direction=firestore.Query.DESCENDING)
            
            templates = []
            for doc in query.stream():
                data = doc.to_dict()
                data['id'] = doc.id
                templates.append(data)
            
            logger.info(f"Retrieved {len(templates)} prompt templates")
            return templates
        except Exception as e:
            logger.error(f"Error listing prompt templates: {e}")
            return []
    
    def create_prompt_template(
        self,
        name: str,
        description: str,
        category: str,
        settings: Dict[str, Any],
        instruction_text: str,
        created_by: str = "system"
    ) -> Optional[str]:
        """
        Create a new prompt template.
        
        Args:
            name: Template name
            description: Template description
            category: Category (tone, structure, style)
            settings: Template settings dict
            instruction_text: Compiled instruction text
            created_by: User ID who created the template
            
        Returns:
            Document ID of created template, or None on error
        """
        try:
            template_data = {
                'name': name,
                'description': description,
                'category': category,
                'settings': settings,
                'instruction_text': instruction_text,
                'is_active': True,
                'created_at': firestore.SERVER_TIMESTAMP,
                'updated_at': firestore.SERVER_TIMESTAMP,
                'created_by': created_by
            }
            
            doc_ref = self.db.collection('prompt_templates').document()
            doc_ref.set(template_data)
            
            logger.info(f"Created prompt template: {name} (ID: {doc_ref.id})")
            return doc_ref.id
        except Exception as e:
            logger.error(f"Error creating prompt template: {e}")
            return None
    
    def update_prompt_template(
        self,
        template_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        Update an existing prompt template.
        
        Args:
            template_id: Document ID of the template
            updates: Fields to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            doc_ref = self.db.collection('prompt_templates').document(template_id)
            
            # Add updated_at timestamp
            updates['updated_at'] = firestore.SERVER_TIMESTAMP
            
            doc_ref.update(updates)
            logger.info(f"Updated prompt template: {template_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating prompt template {template_id}: {e}")
            return False
    
    # ======================================================================
    # ORGANIZATION WRITING CONFIG
    # ======================================================================
    
    def get_org_writing_config(
        self,
        org_id: str,
        config_id: str = "default"
    ) -> Optional[Dict[str, Any]]:
        """
        Get organization-specific writing configuration.
        
        Args:
            org_id: Organization ID
            config_id: Config document ID (default: "default")
            
        Returns:
            Config document as dict, or None if not found
        """
        try:
            doc_ref = (self.db.collection('organizations')
                      .document(org_id)
                      .collection('writing_config')
                      .document(config_id))
            
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                data['id'] = doc.id
                data['org_id'] = org_id
                logger.info(f"Retrieved writing config for org {org_id}")
                return data
            else:
                logger.info(f"No writing config found for org {org_id}, config {config_id}")
                return None
        except Exception as e:
            logger.error(f"Error retrieving org writing config: {e}")
            return None
    
    def save_org_writing_config(
        self,
        org_id: str,
        config: Dict[str, Any],
        config_id: str = "default",
        updated_by: str = "system"
    ) -> bool:
        """
        Save organization-specific writing configuration.
        
        Args:
            org_id: Organization ID
            config: Configuration data
            config_id: Config document ID (default: "default")
            updated_by: User ID who updated the config
            
        Returns:
            True if successful, False otherwise
        """
        try:
            doc_ref = (self.db.collection('organizations')
                      .document(org_id)
                      .collection('writing_config')
                      .document(config_id))
            
            config_data = {
                **config,
                'updated_at': firestore.SERVER_TIMESTAMP,
                'updated_by': updated_by
            }
            
            doc_ref.set(config_data, merge=True)
            logger.info(f"Saved writing config for org {org_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving org writing config: {e}")
            return False
    
    # ======================================================================
    # BLOG GENERATION OVERRIDES
    # ======================================================================
    
    def save_blog_override(
        self,
        blog_id: str,
        org_id: str,
        config_overrides: Dict[str, Any],
        ttl_days: int = 7
    ) -> bool:
        """
        Save temporary per-blog configuration overrides.
        
        Args:
            blog_id: Blog generation job ID
            org_id: Organization ID
            config_overrides: Configuration overrides
            ttl_days: Days until auto-deletion (default: 7)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            doc_ref = (self.db.collection('blog_generations')
                      .document(blog_id)
                      .collection('config_override')
                      .document(blog_id))
            
            expires_at = datetime.utcnow() + timedelta(days=ttl_days)
            
            override_data = {
                'org_id': org_id,
                'config_overrides': config_overrides,
                'created_at': firestore.SERVER_TIMESTAMP,
                'expires_at': expires_at
            }
            
            doc_ref.set(override_data)
            logger.info(f"Saved blog override for blog {blog_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving blog override: {e}")
            return False
    
    def get_blog_override(self, blog_id: str) -> Optional[Dict[str, Any]]:
        """
        Get per-blog configuration overrides.
        
        Args:
            blog_id: Blog generation job ID
            
        Returns:
            Override document as dict, or None if not found
        """
        try:
            doc_ref = (self.db.collection('blog_generations')
                      .document(blog_id)
                      .collection('config_override')
                      .document(blog_id))
            
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                
                # Check if expired
                if 'expires_at' in data:
                    expires_at = data['expires_at']
                    if isinstance(expires_at, datetime) and expires_at < datetime.utcnow():
                        logger.info(f"Blog override expired for blog {blog_id}")
                        return None
                
                data['id'] = doc.id
                logger.info(f"Retrieved blog override for blog {blog_id}")
                return data
            else:
                logger.info(f"No blog override found for blog {blog_id}")
                return None
        except Exception as e:
            logger.error(f"Error retrieving blog override: {e}")
            return None
    
    def delete_blog_override(self, blog_id: str) -> bool:
        """
        Delete per-blog configuration override.
        
        Args:
            blog_id: Blog generation job ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            doc_ref = (self.db.collection('blog_generations')
                      .document(blog_id)
                      .collection('config_override')
                      .document(blog_id))
            
            doc_ref.delete()
            logger.info(f"Deleted blog override for blog {blog_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting blog override: {e}")
            return False
    
    # ======================================================================
    # CLEANUP UTILITIES
    # ======================================================================
    
    def cleanup_expired_overrides(self) -> int:
        """
        Clean up expired blog generation overrides.
        
        Returns:
            Number of overrides deleted
        """
        try:
            deleted_count = 0
            now = datetime.utcnow()
            
            # Query for expired overrides
            # Note: This requires a composite index on expires_at
            blog_gen_ref = self.db.collection('blog_generations')
            
            # Get all blog generation documents
            for blog_doc in blog_gen_ref.stream():
                override_ref = blog_doc.reference.collection('config_override')
                
                for override_doc in override_ref.stream():
                    data = override_doc.to_dict()
                    if 'expires_at' in data:
                        expires_at = data['expires_at']
                        if isinstance(expires_at, datetime) and expires_at < now:
                            override_doc.reference.delete()
                            deleted_count += 1
            
            logger.info(f"Cleaned up {deleted_count} expired blog overrides")
            return deleted_count
        except Exception as e:
            logger.error(f"Error cleaning up expired overrides: {e}")
            return 0


# Singleton instance
_firebase_client: Optional[FirebaseConfigClient] = None


def get_firebase_config_client() -> FirebaseConfigClient:
    """Get singleton Firebase config client instance."""
    global _firebase_client
    if _firebase_client is None:
        _firebase_client = FirebaseConfigClient()
    return _firebase_client


def initialize_firebase_config_client(
    project_id: Optional[str] = None,
    credentials_json: Optional[str] = None,
    credentials_path: Optional[str] = None
) -> FirebaseConfigClient:
    """
    Initialize Firebase config client with custom settings.
    
    Args:
        project_id: Google Cloud project ID
        credentials_json: Service account JSON
        credentials_path: Path to service account JSON file
        
    Returns:
        Initialized Firebase config client
    """
    global _firebase_client
    _firebase_client = FirebaseConfigClient(
        project_id=project_id,
        credentials_json=credentials_json,
        credentials_path=credentials_path
    )
    return _firebase_client

